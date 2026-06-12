"""
ProductionBible — 全局制片蓝图

整部片子的"圣经"：DirectorAgent 一次产出，下游所有 agent 严格执行。
解决多镜头视频缺失全局视角的问题：角色一致性、风格一致性、镜头衔接。
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ContinuityLink(str, Enum):
    """镜头衔接意图（导演视角）

    - CUT：硬切，新机位/新构图，是默认且最常用的电影语法
    - MATCH_CUT：匹配剪辑，构图或动作呼应上一镜头，但仍是独立机位
    - CONTINUOUS：动作延续（同一时间流的不同瞬间），未来可选择性启用末帧链接
    """
    CUT = "cut"
    MATCH_CUT = "match_cut"
    CONTINUOUS = "continuous"


class VisualStyle(BaseModel):
    """全片统一的视觉风格"""
    color_palette: str = Field(..., description="色彩基调，英文，例如 'warm golden tones'")
    lighting_style: str = Field(..., description="光影风格，英文")
    visual_quality: str = Field(default="cinematic, high quality")
    camera_style: str = Field(default="stable, smooth")
    overall_mood: str = Field(..., description="整体氛围，可中文")

    def to_prompt_suffix(self) -> str:
        """转成 prompt 末尾可拼接的英文风格描述"""
        parts = [self.color_palette, self.lighting_style, self.visual_quality, self.camera_style]
        return ", ".join(p for p in parts if p)


class CharacterProfile(BaseModel):
    """角色档案（视觉锚点）"""
    character_id: str
    name: str
    description: str = Field(..., description="完整视觉描述，英文，喂给图像模型")
    visual_keywords: List[str] = Field(default_factory=list, description="一致性关键词")
    reference_image_path: Optional[str] = Field(
        default=None,
        description="参考图本地路径，由 CharacterManager 生成。后续每个 shot 生图都喂这张图"
    )
    consistency_required: bool = True
    role: str = Field(default="supporting", description="protagonist | supporting | prop")


class SceneInfo(BaseModel):
    """场景（叙事骨架的一格）

    每个 scene 持有一张"环境参考图"（establishing shot），
    同一 scene 内的所有 shot 生图时都会把它喂给 Imagen，
    使切机位时世界本身保持一致（光线/构造/物件不漂移）。
    """
    scene_id: int
    location: str
    time_of_day: str = Field(default="day", description="day | night | dawn | dusk")
    mood: str
    narrative_purpose: str = Field(default="", description="该场景在叙事中的作用")
    characters_present: List[str] = Field(default_factory=list, description="角色名列表")
    environment_description: str = Field(
        default="",
        description="详细的环境视觉描述（英文），喂给 Imagen 生成场景参考图用"
    )
    reference_image_path: Optional[str] = Field(
        default=None,
        description="场景参考图本地路径，由 DirectorAgent 生成"
    )


class ShotPlan(BaseModel):
    """镜头执行计划——下游 agent 看这个干活"""
    sequence: int
    scene_id: int = Field(..., description="所属场景，用于跨场景/同场景的连贯性决策")

    prompt: str = Field(..., description="英文视频生成 prompt")
    duration: float
    shot_type: str = Field(default="medium shot", description="Wide / Medium / Close-Up / Tracking ...")

    # 角色参考——决定本镜头生图时喂哪些参考图
    characters_in_shot: List[str] = Field(
        default_factory=list,
        description="本镜头出现的角色名（从 CharacterProfile.name 引用）"
    )

    # 连贯性指令
    continuity: ContinuityLink = ContinuityLink.CUT
    inherits_frame_from: Optional[int] = Field(
        default=None,
        description="若 continuity=continue，则承接此 sequence 的末帧；Phase 2 启用"
    )

    # 摄影师指令（可选，未来传给视频 prompt 转换器）
    camera_movement: Optional[str] = None
    action: Optional[str] = None


class ProductionBible(BaseModel):
    """整部片子的圣经——DirectorAgent 的产出，下游执行的依据"""

    # 全局意图层
    logline: str = Field(..., description="一句话核心")
    tone: str = Field(default="", description="情感基调")
    visual_style: VisualStyle

    # 角色档案
    characters: List[CharacterProfile] = Field(default_factory=list)

    # 场景图
    scenes: List[SceneInfo] = Field(default_factory=list)

    # 镜头执行图
    shot_graph: List[ShotPlan] = Field(default_factory=list)

    # 元数据
    estimated_duration: int = 0
    narrative_arc: str = Field(default="three_act")

    # ---------- 便捷访问方法 ----------

    def get_character(self, name: str) -> Optional[CharacterProfile]:
        for c in self.characters:
            if c.name == name:
                return c
        return None

    def get_reference_images_for_shot(self, sequence: int) -> List[str]:
        """返回某镜头需要喂给图像生成器的参考图路径列表。

        组合：本镜头出现的角色参考图 + 本镜头所属场景的环境参考图。
        顺序：场景在前（先锁世界），角色在后（再锁人物）。
        """
        shot = next((s for s in self.shot_graph if s.sequence == sequence), None)
        if not shot:
            return []
        refs: List[str] = []

        scene = self.get_scene(shot.scene_id)
        if scene and scene.reference_image_path:
            refs.append(scene.reference_image_path)

        for char_name in shot.characters_in_shot:
            char = self.get_character(char_name)
            if char and char.reference_image_path:
                refs.append(char.reference_image_path)
        return refs

    def get_reference_breakdown_for_shot(self, sequence: int) -> Dict[str, int]:
        """返回参考图来源拆分（用于日志）：{'scene': 1, 'character': 2}"""
        shot = next((s for s in self.shot_graph if s.sequence == sequence), None)
        if not shot:
            return {"scene": 0, "character": 0}
        scene = self.get_scene(shot.scene_id)
        scene_count = 1 if (scene and scene.reference_image_path) else 0
        char_count = sum(
            1 for n in shot.characters_in_shot
            if (c := self.get_character(n)) and c.reference_image_path
        )
        return {"scene": scene_count, "character": char_count}

    def get_scene(self, scene_id: int) -> Optional[SceneInfo]:
        for sc in self.scenes:
            if sc.scene_id == scene_id:
                return sc
        return None
