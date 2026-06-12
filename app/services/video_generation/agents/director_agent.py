"""
DirectorAgent — 总导演 Agent

整部片子的全局视角持有者：从用户 brief 一次性产出 ProductionBible，
后续所有 agent（图像、视频、TTS、QC）都按 bible 执行，不再各自即兴。

职责：
1. 调用 ScriptWriter 获取叙事骨架（脚本/角色/场景/分镜/风格）
2. 调用 CharacterManager 为每个需要一致性的角色生成参考图
3. 推断每个 shot 所属的 scene 和出现的角色
4. 装配 ProductionBible
"""

import asyncio
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from app.schemas.production_bible import (
    CharacterProfile,
    ContinuityLink,
    ProductionBible,
    SceneInfo,
    ShotPlan,
    VisualStyle,
)
from app.services.image.google_imagen_generator import GoogleImagenGenerator
from app.services.llm.service import LLMService, ProviderType
from app.services.storage import get_storage_service
from app.services.video_generation.agents.character_manager_agent import (
    CharacterManagementResult,
    CharacterManagerAgent,
)
from app.services.video_generation.agents.script_writer_agent import (
    ScriptResult,
    ScriptWriterAgent,
)

logger = logging.getLogger(__name__)


class DirectorAgent:
    """总导演 Agent — 产出全局蓝图 ProductionBible。"""

    def __init__(self, output_dir: Optional[str] = None):
        self.script_writer = ScriptWriterAgent()
        self.character_manager = CharacterManagerAgent(output_dir=output_dir)
        self.image_generator = GoogleImagenGenerator()
        self.storage = get_storage_service()
        self.llm = LLMService(provider=ProviderType.GOOGLE)

    async def build_bible(
        self,
        brief: str,
        task_id: str,
        style: str = "专业",
        target_duration: Optional[int] = None,
        shot_count: Optional[int] = None,
        target_audience: str = "通用",
        additional_context: Optional[Dict[str, Any]] = None,
        generate_character_refs: bool = True,
    ) -> tuple[ProductionBible, ScriptResult]:
        """从用户 brief 构建 ProductionBible。

        Returns:
            (bible, script_result)：bible 给下游执行用，script_result 保留兼容旧字段（state.script）
        """
        logger.info(f"🎬 DirectorAgent 启动，task_id={task_id}")

        # 1. 调 ScriptWriter 拿叙事骨架
        script_result = await self.script_writer.write_script(
            user_input=brief,
            duration=target_duration,
            shot_count=shot_count,
            style=style,
            target_audience=target_audience,
            additional_context=additional_context,
        )
        logger.info(
            f"  ✓ ScriptWriter 完成: {len(script_result.metadata.characters)} 角色, "
            f"{len(script_result.metadata.scenes)} 场景, {len(script_result.shots)} 镜头"
        )

        # 2. 装配 visual_style
        visual_style = self._build_visual_style(script_result.visual_style_guide, style)

        # 3. 装配 characters（参考图先空着，下面再填）
        characters = self._build_characters(script_result)

        # 4. 装配 scenes
        scenes = self._build_scenes(script_result)

        # 5. 推断 shot ↔ scene + shot ↔ characters 的映射
        #    （ScriptWriter 的 shots 不带 scene_id 也不带 characters_in_shot，需要补全）
        shot_mappings = await self._infer_shot_mappings(
            shots=script_result.shots,
            scenes=scenes,
            characters=characters,
        )

        # 6. 装配 shot_graph
        shot_graph = self._build_shot_graph(script_result.shots, shot_mappings)

        # 7. 并行生成角色参考图 + 场景参考图（两者独立，无需串行）
        if generate_character_refs:
            ref_tasks = []
            if characters:
                ref_tasks.append(
                    self._generate_character_references(
                        characters=characters,
                        visual_style_guide=script_result.visual_style_guide,
                        task_id=task_id,
                    )
                )
            if scenes:
                ref_tasks.append(
                    self._generate_scene_references(
                        scenes=scenes,
                        visual_style_guide=script_result.visual_style_guide,
                        task_id=task_id,
                    )
                )
            if ref_tasks:
                await asyncio.gather(*ref_tasks, return_exceptions=True)

        bible = ProductionBible(
            logline=script_result.metadata.theme or brief[:80],
            tone=script_result.metadata.emotional_tone,
            visual_style=visual_style,
            characters=characters,
            scenes=scenes,
            shot_graph=shot_graph,
            estimated_duration=script_result.estimated_duration,
            narrative_arc=script_result.metadata.narrative.arc_type.value,
        )

        char_ref_count = sum(1 for c in bible.characters if c.reference_image_path)
        scene_ref_count = sum(1 for s in bible.scenes if s.reference_image_path)
        logger.info(
            f"✅ ProductionBible 构建完成: "
            f"{len(bible.characters)} 角色（{char_ref_count} 张参考图） "
            f"/ {len(bible.scenes)} 场景（{scene_ref_count} 张参考图） "
            f"/ {len(bible.shot_graph)} 镜头"
        )
        return bible, script_result

    # ---------------- 私有方法 ----------------

    def _build_visual_style(self, vsg: Dict[str, str], fallback_mood: str) -> VisualStyle:
        return VisualStyle(
            color_palette=vsg.get("color_palette") or "natural cinematic tones",
            lighting_style=vsg.get("lighting_style") or "soft natural light",
            visual_quality=vsg.get("visual_quality") or "cinematic, high quality",
            camera_style=vsg.get("camera_style") or "stable, smooth",
            overall_mood=vsg.get("overall_mood") or fallback_mood,
        )

    def _build_characters(self, script_result: ScriptResult) -> List[CharacterProfile]:
        result: List[CharacterProfile] = []
        for c in script_result.metadata.characters:
            char_id = f"char_{c.name.lower().replace(' ', '_')}"
            result.append(
                CharacterProfile(
                    character_id=char_id,
                    name=c.name,
                    description=c.description,
                    visual_keywords=c.visual_keywords or [],
                    consistency_required=c.consistency_required,
                    role=c.role,
                )
            )
        return result

    def _build_scenes(self, script_result: ScriptResult) -> List[SceneInfo]:
        """从 ScriptWriter 的 Scene 装配 SceneInfo，并合成 environment_description。

        environment_description 是喂给 Imagen 生成场景参考图的 prompt，
        合并 location + time + mood + 全片视觉风格，得到一句完整的环境描述。
        """
        vsg = script_result.visual_style_guide or {}
        style_suffix_parts = [
            vsg.get("color_palette", ""),
            vsg.get("lighting_style", ""),
            vsg.get("visual_quality", "cinematic"),
        ]
        style_suffix = ", ".join(p for p in style_suffix_parts if p)

        result: List[SceneInfo] = []
        for s in script_result.metadata.scenes:
            env_parts = [
                s.location,
                s.time if s.time else "",
                s.mood if s.mood else "",
                s.visual_style if s.visual_style else "",
                style_suffix,
                "establishing shot, atmospheric environment, no people, no text, wide composition",
            ]
            env_description = ", ".join(p for p in env_parts if p)

            result.append(
                SceneInfo(
                    scene_id=s.id,
                    location=s.location,
                    time_of_day=s.time or "day",
                    mood=s.mood or "neutral",
                    narrative_purpose=s.visual_style or "",
                    characters_present=[],
                    environment_description=env_description,
                )
            )
        return result

    async def _infer_shot_mappings(
        self,
        shots: List[Any],
        scenes: List[SceneInfo],
        characters: List[CharacterProfile],
    ) -> Dict[int, Dict[str, Any]]:
        """推断每个 shot 的 scene_id、characters_in_shot 和 transition 类型。

        返回: { sequence: { scene_id, characters_in_shot, transition } }
        - transition: "cut" | "match_cut" | "continuous"
          默认 cut。只有真正"动作延续"才标 continuous（为 Phase 4 末帧链接做准备）。
        """
        valid_transitions = {"cut", "match_cut", "continuous"}
        default_scene = scenes[0].scene_id if scenes else 1

        # 退化情形：无场景无角色——所有 shot 都用默认值
        if not scenes and not characters:
            return {
                s.sequence: {"scene_id": default_scene, "characters_in_shot": [], "transition": "cut"}
                for s in shots
            }

        # 单场景 + 无角色：仍走 LLM 也行，但代价不值——直接退化
        if len(scenes) <= 1 and not characters:
            return {
                s.sequence: {"scene_id": default_scene, "characters_in_shot": [], "transition": "cut"}
                for s in shots
            }

        # 通用情形：让 LLM 一次性映射全部
        scene_brief = "\n".join(
            [f"- scene {sc.scene_id}: {sc.location} ({sc.mood})" for sc in scenes]
        ) or "- scene 1: (default)"
        char_brief = "\n".join(
            [f"- {c.name}: {c.description[:80]}" for c in characters]
        ) or "(none)"

        shot_brief = "\n".join(
            [f"- shot {s.sequence}: {s.prompt[:200]}" for s in shots]
        )

        prompt = f"""You are a film script supervisor. For each shot, decide:
1. Which scene it belongs to.
2. Which characters appear in it.
3. The transition relationship to the PREVIOUS shot.

Scenes:
{scene_brief}

Characters:
{char_brief}

Shots (ordered):
{shot_brief}

Output JSON ONLY:
{{
  "mappings": [
    {{"sequence": 1, "scene_id": 1, "characters_in_shot": ["name"], "transition": "cut"}}
  ]
}}

Transition values (be conservative — default to "cut"):
- "cut": clean break — different angle, different moment, or different scene. **This is the default for ~80% of cases.**
- "match_cut": composition or motion deliberately echoes the previous shot across a cut (still a different moment).
- "continuous": this shot continues the EXACT action of the previous shot in real time, like a long take broken into pieces. Rare.

Rules:
- scene_id must be one of the listed scene ids (default to {default_scene} if unclear).
- characters_in_shot must use exact names from the character list (empty list if none).
- The first shot is always "cut" (no previous shot to relate to).
- Pick "continuous" only if the prompts genuinely describe the same continuous action.
- Output ONLY the JSON, no markdown fences, no commentary."""

        try:
            res = await asyncio.to_thread(
                self.llm.call,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            content = res.get("content", "")
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            data = json.loads(json_match.group())
            valid_char_names = {c.name for c in characters}
            valid_scene_ids = {sc.scene_id for sc in scenes} or {default_scene}
            mappings: Dict[int, Dict[str, Any]] = {}
            for m in data.get("mappings", []):
                seq = m.get("sequence")
                if seq is None:
                    continue
                sid = m.get("scene_id", default_scene)
                if sid not in valid_scene_ids:
                    sid = default_scene
                chars = [n for n in m.get("characters_in_shot", []) if n in valid_char_names]
                tr = (m.get("transition") or "cut").lower()
                if tr not in valid_transitions:
                    tr = "cut"
                mappings[seq] = {
                    "scene_id": sid,
                    "characters_in_shot": chars,
                    "transition": tr,
                }

            # 第一个 shot 强制 cut（没有上一个镜头可承接）
            if shots:
                first_seq = shots[0].sequence
                if first_seq in mappings:
                    mappings[first_seq]["transition"] = "cut"

            # 补齐缺失的 shot
            for s in shots:
                if s.sequence not in mappings:
                    mappings[s.sequence] = {
                        "scene_id": default_scene,
                        "characters_in_shot": [],
                        "transition": "cut",
                    }
            return mappings

        except Exception as e:
            logger.warning(f"shot 映射推断失败，退化为默认: {e}")
            return {
                s.sequence: {"scene_id": default_scene, "characters_in_shot": [], "transition": "cut"}
                for s in shots
            }

    def _build_shot_graph(
        self,
        shots: List[Any],
        mappings: Dict[int, Dict[str, Any]],
    ) -> List[ShotPlan]:
        """装配 shot_graph。

        默认 continuity=CUT（cut 是电影最常用的语法，不需要硬接）。
        Task #9 之后，_infer_shot_mappings 会从 LLM 拿到 transition 决定，
        覆盖默认值；只有真正的"动作延续"才标 CONTINUOUS。
        """
        result: List[ShotPlan] = []
        for s in shots:
            mapping = mappings.get(s.sequence, {})
            scene_id = mapping.get("scene_id", 1)
            chars_in_shot = mapping.get("characters_in_shot", [])
            transition_str = mapping.get("transition", "cut")
            try:
                continuity = ContinuityLink(transition_str)
            except ValueError:
                continuity = ContinuityLink.CUT

            # inherits_frame_from 只在 CONTINUOUS 时填入（Phase 4 末帧链接才会用）
            inherits = (s.sequence - 1) if continuity == ContinuityLink.CONTINUOUS else None

            result.append(
                ShotPlan(
                    sequence=s.sequence,
                    scene_id=scene_id,
                    prompt=s.prompt,
                    duration=s.duration,
                    shot_type=s.shot_type,
                    characters_in_shot=chars_in_shot,
                    continuity=continuity,
                    inherits_frame_from=inherits,
                )
            )
        return result

    async def _generate_character_references(
        self,
        characters: List[CharacterProfile],
        visual_style_guide: Dict[str, str],
        task_id: str,
    ) -> None:
        """调用 CharacterManager 为每个需要一致性的角色生成参考图，结果回填到 characters。"""
        chars_for_manager = [
            {
                "name": c.name,
                "description": c.description,
                "visual_keywords": c.visual_keywords,
                "consistency_required": c.consistency_required,
                "role": c.role,
            }
            for c in characters
        ]
        try:
            mgmt: CharacterManagementResult = await self.character_manager.manage_characters(
                characters=chars_for_manager,
                visual_style_guide=visual_style_guide,
                task_id=task_id,
                consistency_level="high",
            )
            # 把参考图路径写回到 CharacterProfile（按 name 匹配）
            ref_by_name = {a.name: a.reference_image_path for a in mgmt.character_assets}
            for c in characters:
                ref_path = ref_by_name.get(c.name)
                if ref_path:
                    c.reference_image_path = ref_path
        except Exception as e:
            logger.warning(f"角色参考图生成失败（流程继续，将退化为纯文本）: {e}")

    async def _generate_scene_references(
        self,
        scenes: List[SceneInfo],
        visual_style_guide: Dict[str, str],
        task_id: str,
    ) -> None:
        """为每个 scene 生成一张环境参考图（establishing shot），结果回填到 SceneInfo。

        同一 scene 内的多个 shot 切机位时，把这张参考图喂给 Imagen，
        保证世界本身（光线、构造、物件、色调）不漂移。
        """
        if not scenes:
            return

        async def _gen_one(scene: SceneInfo) -> None:
            try:
                logger.info(f"      生成场景参考图: scene_{scene.scene_id} ({scene.location[:30]})")
                img_path = await self.image_generator.generate_image(
                    prompt=scene.environment_description or scene.location,
                    aspect_ratio="16:9",  # 场景图用横构图，便于覆盖多个机位
                )
                if not img_path:
                    return
                stored = self.storage.save(
                    img_path,
                    f"projects/{task_id}/scenes/scene_{scene.scene_id}_reference.jpg",
                )
                scene.reference_image_path = stored
                logger.info(f"      ✅ 场景 {scene.scene_id} 参考图已生成: {stored}")
            except Exception as e:
                logger.warning(f"场景 {scene.scene_id} 参考图生成失败（继续）: {e}")

        # 多场景并行生成
        await asyncio.gather(*[_gen_one(s) for s in scenes], return_exceptions=True)
