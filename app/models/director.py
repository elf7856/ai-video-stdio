"""
测试适配层：AI导演相关模型与枚举
满足 tests/test_ai_director.py 的导入与字段访问需求
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class SceneType(str, Enum):
    EXPLANATION = "explanation"
    NARRATIVE = "narrative"
    DEMO = "demo"
    INTERVIEW = "interview"
    CREATIVE = "creative"


class QualityLevel(str, Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"


class ContentStrategy(str, Enum):
    SCRIPTED = "scripted"
    GENERATIVE = "generative"
    HYBRID = "hybrid"


class ShotType(str, Enum):
    ESTABLISHING = "establishing"
    CHARACTER_FOCUS = "character_focus"
    REALISTIC_SCENE = "realistic_scene"
    CAMERA_MOVEMENT = "camera_movement"
    CREATIVE_EFFECT = "creative_effect"


class APIProvider(str, Enum):
    RUNWAY = "runway"
    GOOGLE = "google"
    OPENAI = "openai"


class VideoCreationRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    duration_target: int = 180
    quality_level: QualityLevel = QualityLevel.PROFESSIONAL
    content_strategy: ContentStrategy = ContentStrategy.HYBRID
    style_preferences: Dict[str, Any] = Field(default_factory=dict)
    audio_requirements: Dict[str, Any] = Field(default_factory=dict)


class ContentAnalysis(BaseModel):
    intent: Dict[str, Any] = Field(default_factory=dict)
    scene_type: SceneType = SceneType.EXPLANATION
    style_preferences: Dict[str, Any] = Field(default_factory=dict)
    key_elements: List[str] = Field(default_factory=list)
    narrative_structure: Dict[str, Any] = Field(default_factory=dict)
    source_content: Optional[Dict[str, Any]] = None


class VideoSegment(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: float = 0.0
    duration: float = 0.0


class Shot(BaseModel):
    id: str = Field(default_factory=lambda: f"shot_{uuid.uuid4().hex[:8]}")
    sequence_number: int
    type: ShotType
    prompt: str
    duration: float
    start_time: float = 0.0
    api_provider: APIProvider = APIProvider.GOOGLE


class PlanStructure(BaseModel):
    total_duration: float


class ShotPlan(BaseModel):
    request_id: str
    shots: List[Shot]
    total_duration: float
    transitions: List[str] = Field(default_factory=list)
    estimated_cost: float = 0.0
    audio_plan: Optional["AudioPlan"] = None
    structure: PlanStructure = Field(default_factory=lambda: PlanStructure(total_duration=0.0))


class AudioPlan(BaseModel):
    voice_over: Optional[str] = None
    background_music: Optional[str] = None
