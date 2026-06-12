"""
Phase 2 离线验证脚本

不依赖真实 LLM / Imagen API，纯走数据层验证：
1. SceneInfo 持有 environment_description 和 reference_image_path
2. ContinuityLink 包含 cut / match_cut / continuous（CONTINUE 已重命名为 CONTINUOUS）
3. DirectorAgent 同时生成角色参考图和场景参考图（mock）
4. _infer_shot_mappings 解析 transition 字段
5. get_reference_images_for_shot 返回场景参考图 + 角色参考图（顺序：场景在前）
6. get_reference_breakdown_for_shot 给出来源拆分

跑法：
    python scripts/verify_director_phase2.py
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.production_bible import (
    CharacterProfile,
    ContinuityLink,
    ProductionBible,
    SceneInfo,
    ShotPlan,
    VisualStyle,
)
from app.services.video_generation.agents.script_writer_agent import (
    Character,
    NarrativeArc,
    NarrativeStructure,
    Scene,
    ScriptMetadata,
    ScriptResult,
    ShotPlan as ScriptShotPlan,
)


def make_fake_script_result() -> ScriptResult:
    return ScriptResult(
        script="A short story about a cat exploring the city.",
        metadata=ScriptMetadata(
            characters=[
                Character(
                    name="Whiskers",
                    description="A curious orange tabby cat with green eyes",
                    role="protagonist",
                    consistency_required=True,
                    visual_keywords=["orange tabby", "green eyes"],
                )
            ],
            scenes=[
                Scene(id=1, location="Urban rooftop at sunset", time="dusk", mood="adventurous", visual_style="warm cinematic"),
                Scene(id=2, location="Empty alley at night", time="night", mood="mysterious", visual_style="cool noir"),
            ],
            narrative=NarrativeStructure(arc_type=NarrativeArc.THREE_ACT, setup="cat", resolution="cat returns"),
            theme="A cat's adventure",
            emotional_tone="warm",
            target_audience="general",
            key_messages=["curiosity"],
        ),
        visual_style_guide={
            "color_palette": "warm golden tones",
            "lighting_style": "soft natural light",
            "visual_quality": "cinematic, 4K",
            "camera_style": "smooth tracking",
            "overall_mood": "warm and adventurous",
        },
        estimated_duration=30,
        recommended_shot_count=4,
        complexity_level="medium",
        shots=[
            ScriptShotPlan(sequence=1, prompt="Wide shot of cat on rooftop", duration=7.0, shot_type="Wide Shot"),
            ScriptShotPlan(sequence=2, prompt="Cat leaping mid-air, continuing the previous motion", duration=5.0, shot_type="Tracking Shot"),
            ScriptShotPlan(sequence=3, prompt="Cat lands and walks", duration=6.0, shot_type="Medium Shot"),
            ScriptShotPlan(sequence=4, prompt="Cat in alley at night, looking around", duration=7.0, shot_type="Medium Shot"),
        ],
    )


def test_scene_info_has_new_fields():
    sc = SceneInfo(scene_id=1, location="lab", mood="curious")
    assert hasattr(sc, "environment_description")
    assert hasattr(sc, "reference_image_path")
    assert sc.reference_image_path is None
    assert sc.environment_description == ""
    print("✅ SceneInfo 新字段就位")


def test_continuity_link_values():
    values = {v.value for v in ContinuityLink}
    assert values == {"cut", "match_cut", "continuous"}, f"unexpected values: {values}"
    print("✅ ContinuityLink 值集 = {cut, match_cut, continuous}")


def test_get_refs_breakdown():
    bible = ProductionBible(
        logline="t",
        visual_style=VisualStyle(color_palette="warm", lighting_style="soft", overall_mood="calm"),
        characters=[
            CharacterProfile(character_id="c1", name="A", description="x", reference_image_path="/tmp/a.jpg"),
            CharacterProfile(character_id="c2", name="B", description="y", reference_image_path="/tmp/b.jpg"),
        ],
        scenes=[
            SceneInfo(scene_id=1, location="lab", mood="x", reference_image_path="/tmp/scene.jpg"),
        ],
        shot_graph=[
            ShotPlan(sequence=1, scene_id=1, prompt="p", duration=5.0, characters_in_shot=["A", "B"]),
        ],
    )
    refs = bible.get_reference_images_for_shot(1)
    # 顺序：场景在前
    assert refs[0] == "/tmp/scene.jpg"
    assert "/tmp/a.jpg" in refs and "/tmp/b.jpg" in refs
    breakdown = bible.get_reference_breakdown_for_shot(1)
    assert breakdown == {"scene": 1, "character": 2}
    print("✅ 参考图拼装顺序正确，breakdown 正确")


async def test_director_with_scene_refs():
    """验证 DirectorAgent 同时生成角色参考图和场景参考图"""
    from app.services.video_generation.agents.director_agent import DirectorAgent

    director = DirectorAgent(output_dir=tempfile.mkdtemp())

    # 1. mock ScriptWriter
    fake_script = make_fake_script_result()
    director.script_writer.write_script = AsyncMock(return_value=fake_script)

    # 2. mock LLM 返回带 transition 的映射
    mock_response = {
        "content": """
        {"mappings": [
            {"sequence": 1, "scene_id": 1, "characters_in_shot": ["Whiskers"], "transition": "cut"},
            {"sequence": 2, "scene_id": 1, "characters_in_shot": ["Whiskers"], "transition": "continuous"},
            {"sequence": 3, "scene_id": 1, "characters_in_shot": ["Whiskers"], "transition": "match_cut"},
            {"sequence": 4, "scene_id": 2, "characters_in_shot": ["Whiskers"], "transition": "cut"}
        ]}
        """
    }
    director.llm.call = MagicMock(return_value=mock_response)

    # 3. mock CharacterManager 角色参考图
    from app.services.video_generation.agents.character_manager_agent import (
        CharacterAsset,
        CharacterManagementResult,
    )

    character_ref_path = "/outputs/projects/test/characters/whiskers_reference.jpg"
    director.character_manager.manage_characters = AsyncMock(
        return_value=CharacterManagementResult(
            character_assets=[
                CharacterAsset(
                    character_id="char_whiskers",
                    name="Whiskers",
                    description="x",
                    visual_keywords=["orange"],
                    reference_image_path=character_ref_path,
                )
            ],
            consistency_rules=[],
            global_reference_prompt="",
            requires_character_ref=True,
            estimated_generation_time=15.0,
        )
    )

    # 4. mock 场景参考图：Imagen + Storage
    scene_call_log = []

    async def fake_generate_image(prompt, **kwargs):
        scene_call_log.append(prompt)
        # 用 prompt 第一个词模拟不同场景的产物
        return f"/tmp/fake_scene_{len(scene_call_log)}.png"

    director.image_generator.generate_image = fake_generate_image
    director.storage.save = lambda src, target: f"/outputs/{target}"

    # 5. 实际调用
    bible, _ = await director.build_bible(brief="cat city adventure", task_id="test", style="cinematic")

    # 断言：每个场景都有 reference_image_path
    assert all(s.reference_image_path for s in bible.scenes), "场景参考图未回填"
    assert len(scene_call_log) == 2, f"应该生成 2 张场景参考图，实际 {len(scene_call_log)}"

    # 断言：角色参考图也回填
    assert bible.characters[0].reference_image_path == character_ref_path

    # 断言：transition 被解析
    transitions = [s.continuity for s in bible.shot_graph]
    assert transitions[0] == ContinuityLink.CUT, f"shot 1 应为 cut: {transitions[0]}"
    assert transitions[1] == ContinuityLink.CONTINUOUS, f"shot 2 应为 continuous: {transitions[1]}"
    assert transitions[2] == ContinuityLink.MATCH_CUT, f"shot 3 应为 match_cut: {transitions[2]}"
    assert transitions[3] == ContinuityLink.CUT, f"shot 4 应为 cut: {transitions[3]}"

    # inherits_frame_from 只在 CONTINUOUS 时填入
    assert bible.shot_graph[1].inherits_frame_from == 1
    assert bible.shot_graph[0].inherits_frame_from is None
    assert bible.shot_graph[2].inherits_frame_from is None

    # 参考图组合：每个 shot 应同时拿到场景参考图和角色参考图
    refs = bible.get_reference_images_for_shot(1)
    assert len(refs) == 2, f"shot 1 应有 2 张参考图（1 场景 + 1 角色）: {refs}"

    print("✅ DirectorAgent 同时产出场景 + 角色参考图，transition 解析正确")


async def test_first_shot_forced_cut():
    """即便 LLM 把第一个 shot 标成 continuous，也应被强制改为 cut（没有上一个镜头）"""
    from app.services.video_generation.agents.director_agent import DirectorAgent

    director = DirectorAgent(output_dir=tempfile.mkdtemp())
    fake_script = make_fake_script_result()
    director.script_writer.write_script = AsyncMock(return_value=fake_script)

    # 故意让 LLM 给第一个 shot 标 continuous
    mock_response = {
        "content": """{"mappings": [
            {"sequence": 1, "scene_id": 1, "characters_in_shot": ["Whiskers"], "transition": "continuous"},
            {"sequence": 2, "scene_id": 1, "characters_in_shot": ["Whiskers"], "transition": "cut"},
            {"sequence": 3, "scene_id": 1, "characters_in_shot": ["Whiskers"], "transition": "cut"},
            {"sequence": 4, "scene_id": 2, "characters_in_shot": ["Whiskers"], "transition": "cut"}
        ]}"""
    }
    director.llm.call = MagicMock(return_value=mock_response)

    director.character_manager.manage_characters = AsyncMock(
        return_value=__import__("app.services.video_generation.agents.character_manager_agent", fromlist=["CharacterManagementResult"]).CharacterManagementResult(
            character_assets=[], consistency_rules=[], global_reference_prompt="",
            requires_character_ref=False, estimated_generation_time=0.0,
        )
    )

    async def fake_gen(prompt, **kwargs):
        return None  # 跳过场景图生成

    director.image_generator.generate_image = fake_gen

    bible, _ = await director.build_bible(brief="x", task_id="t", style="x")
    assert bible.shot_graph[0].continuity == ContinuityLink.CUT, "第一个 shot 必须强制为 cut"
    print("✅ 第一个 shot 强制 cut")


async def main():
    print("=" * 60)
    print("Phase 2 离线验证")
    print("=" * 60)

    test_scene_info_has_new_fields()
    test_continuity_link_values()
    test_get_refs_breakdown()
    await test_director_with_scene_refs()
    await test_first_shot_forced_cut()

    print()
    print("=" * 60)
    print("✅ 全部通过 — Phase 2 数据层和装配层 OK")
    print("=" * 60)
    print()
    print("真实端到端验证要点：")
    print("  - 日志包含：✅ 蓝图完成：N 镜头 / N 场景（M 张参考图） / N 角色（M 张参考图）")
    print("  - 日志包含：镜头 X 使用 N 张参考图（场景 1 / 角色 N）锁定一致性")
    print("  - outputs/projects/<task>/scenes/scene_X_reference.jpg 文件存在")
    print("  - 同一场景多个机位的成片，环境/光线/物件保持一致")


if __name__ == "__main__":
    asyncio.run(main())
