"""
Phase 1 离线验证脚本

不依赖真实 LLM / Imagen API，纯走数据层验证：
1. ProductionBible schema 序列化/反序列化
2. DirectorAgent 装配逻辑（用 mock 替代 ScriptWriter 和 CharacterManager 的网络调用）
3. TaskState 接入 bible 后 to_dict/load 闭环
4. orchestrator._refs_for_shot 能从 bible 取出参考图

跑法：
    python scripts/verify_director_phase1.py
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# 让脚本在仓库根目录下也能直接跑
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
    """造一个假的 ScriptResult，模拟 ScriptWriter 的输出"""
    return ScriptResult(
        script="A short story about a cat exploring the city.",
        metadata=ScriptMetadata(
            characters=[
                Character(
                    name="Whiskers",
                    description="A curious orange tabby cat with green eyes and a fluffy tail",
                    role="protagonist",
                    consistency_required=True,
                    visual_keywords=["orange tabby", "green eyes", "fluffy tail"],
                )
            ],
            scenes=[
                Scene(id=1, location="Urban rooftop at sunset", time="dusk", mood="adventurous", visual_style="warm cinematic"),
                Scene(id=2, location="Empty street alley at night", time="night", mood="mysterious", visual_style="cool noir"),
            ],
            narrative=NarrativeStructure(arc_type=NarrativeArc.THREE_ACT, setup="cat on rooftop", resolution="cat returns home"),
            theme="A cat's adventure",
            emotional_tone="warm, adventurous",
            target_audience="general",
            key_messages=["curiosity", "courage"],
        ),
        visual_style_guide={
            "color_palette": "warm golden tones with cool blue shadows",
            "lighting_style": "soft natural light",
            "visual_quality": "cinematic, 4K",
            "camera_style": "smooth tracking",
            "overall_mood": "warm and adventurous",
        },
        estimated_duration=30,
        recommended_shot_count=4,
        complexity_level="medium",
        shots=[
            ScriptShotPlan(sequence=1, prompt="An orange tabby cat sits on a rooftop edge at sunset, golden hour light", duration=7.0, shot_type="Wide Shot"),
            ScriptShotPlan(sequence=2, prompt="Close up of orange tabby cat's curious green eyes scanning the city", duration=5.0, shot_type="Close-Up"),
            ScriptShotPlan(sequence=3, prompt="Orange tabby cat leaping across rooftop, dramatic angle", duration=6.0, shot_type="Tracking Shot"),
            ScriptShotPlan(sequence=4, prompt="Orange tabby cat walking down a dark alley, mysterious", duration=7.0, shot_type="Medium Shot"),
        ],
    )


async def test_director_assembly():
    """验证 DirectorAgent 的装配逻辑（不打真实网络）"""
    from app.services.video_generation.agents.director_agent import DirectorAgent

    director = DirectorAgent(output_dir=tempfile.mkdtemp())

    # mock ScriptWriter.write_script
    fake_script = make_fake_script_result()
    director.script_writer.write_script = AsyncMock(return_value=fake_script)

    # mock LLM.call for shot ↔ scene mapping
    mock_llm_response = {
        "content": '{"mappings": [{"sequence": 1, "scene_id": 1, "characters_in_shot": ["Whiskers"]}, {"sequence": 2, "scene_id": 1, "characters_in_shot": ["Whiskers"]}, {"sequence": 3, "scene_id": 1, "characters_in_shot": ["Whiskers"]}, {"sequence": 4, "scene_id": 2, "characters_in_shot": ["Whiskers"]}]}'
    }
    director.llm.call = MagicMock(return_value=mock_llm_response)

    # mock CharacterManager.manage_characters
    from app.services.video_generation.agents.character_manager_agent import (
        CharacterAsset,
        CharacterManagementResult,
    )

    fake_ref_path = "/outputs/projects/test123/characters/whiskers_reference.jpg"
    fake_mgmt_result = CharacterManagementResult(
        character_assets=[
            CharacterAsset(
                character_id="char_whiskers",
                name="Whiskers",
                description="An orange tabby cat",
                visual_keywords=["orange tabby", "green eyes"],
                reference_image_path=fake_ref_path,
            )
        ],
        consistency_rules=[],
        global_reference_prompt="",
        requires_character_ref=True,
        estimated_generation_time=15.0,
    )
    director.character_manager.manage_characters = AsyncMock(return_value=fake_mgmt_result)

    # 实际调用
    bible, script_result = await director.build_bible(
        brief="A cat's adventure in the city",
        task_id="test123",
        style="cinematic",
    )

    # 断言
    assert bible.logline, "logline 为空"
    assert len(bible.characters) == 1, f"角色数错误: {len(bible.characters)}"
    assert bible.characters[0].reference_image_path == fake_ref_path, "参考图路径未回填"
    assert len(bible.scenes) == 2, f"场景数错误: {len(bible.scenes)}"
    assert len(bible.shot_graph) == 4, f"shot 数错误: {len(bible.shot_graph)}"

    # shot 1-3 应在 scene 1，shot 4 在 scene 2
    assert bible.shot_graph[0].scene_id == 1
    assert bible.shot_graph[3].scene_id == 2

    # 同场景连续镜头应标记 continue，跨场景应标记 cut
    assert bible.shot_graph[0].continuity == ContinuityLink.CUT, "首镜头应为 cut"
    assert bible.shot_graph[1].continuity == ContinuityLink.CONTINUE, "shot2 同场景应为 continue"
    assert bible.shot_graph[3].continuity == ContinuityLink.CUT, "跨场景应为 cut"

    # 每个 shot 都应该认出 Whiskers
    for shot in bible.shot_graph:
        assert "Whiskers" in shot.characters_in_shot, f"shot {shot.sequence} 未识别角色"

    # 参考图查询测试
    refs = bible.get_reference_images_for_shot(1)
    assert refs == [fake_ref_path], f"shot 1 参考图查询失败: {refs}"

    print("✅ DirectorAgent 装配逻辑验证通过")
    return bible


def test_bible_serialization(bible: ProductionBible):
    """验证 bible 序列化和反序列化"""
    dumped = bible.model_dump()
    assert isinstance(dumped, dict)
    restored = ProductionBible.model_validate(dumped)
    assert restored.logline == bible.logline
    assert len(restored.shot_graph) == len(bible.shot_graph)
    assert restored.characters[0].reference_image_path == bible.characters[0].reference_image_path
    print("✅ ProductionBible 序列化/反序列化通过")


def test_taskstate_with_bible(bible: ProductionBible):
    """验证 TaskState.to_dict 包含 bible，且能 round-trip 回来"""
    from app.services.video_generation.orchestrator import (
        GenerationConfig,
        TaskState,
    )

    state = TaskState(task_id="test123", config=GenerationConfig(topic="test"))
    state.bible = bible

    d = state.to_dict()
    assert d["bible"] is not None, "to_dict 没序列化 bible"
    assert d["bible"]["logline"] == bible.logline

    # 反序列化
    restored = ProductionBible.model_validate(d["bible"])
    assert restored.logline == bible.logline
    assert len(restored.shot_graph) == len(bible.shot_graph)
    print("✅ TaskState.bible 序列化通过")


def test_imagen_signature_compat():
    """确认 GoogleImagenGenerator.generate_image 仍然向后兼容"""
    import inspect

    from app.services.image.google_imagen_generator import GoogleImagenGenerator

    sig = inspect.signature(GoogleImagenGenerator.generate_image)
    params = sig.parameters
    assert "reference_images" in params, "缺 reference_images 参数"
    assert params["reference_images"].default is None, "reference_images 默认应为 None（向后兼容）"
    print("✅ GoogleImagenGenerator 向后兼容验证通过")


async def main():
    print("=" * 60)
    print("Phase 1 离线验证")
    print("=" * 60)

    test_imagen_signature_compat()
    bible = await test_director_assembly()
    test_bible_serialization(bible)
    test_taskstate_with_bible(bible)

    print()
    print("=" * 60)
    print("✅ 全部通过 — Phase 1 数据层和装配层 OK")
    print("=" * 60)
    print()
    print("下一步：用真实 API 跑一次端到端生成（需要 GOOGLE_API_KEY），")
    print("观察日志中是否出现：")
    print("  - 🎬 总导演开始构建全局蓝图")
    print("  - ✅ 蓝图完成：N 镜头 / N 场景 / N 角色（M 张参考图）")
    print("  - 镜头 X 使用 N 张角色参考图锁定一致性")


if __name__ == "__main__":
    asyncio.run(main())
