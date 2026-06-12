"""
视频生成API - 路径对齐稳定版
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from sqlalchemy.orm import Session
from enum import Enum
import logging
import uuid
from pathlib import Path

from app.services.video_generation import (
    get_orchestrator,
    GenerationConfig,
    TaskStatus,
    TaskState
)
from app.services.ingest import UrlIngestService
from app.utils.database import get_db
from app.models.user import User
from app.api.deps import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video-generation", tags=["视频生成"])

# 视频风格枚举
class VideoStyle(str, Enum):
    PROFESSIONAL = "专业"
    CINEMATIC = "电影感"
    DOCUMENTARY = "纪录片"
    COMMERCIAL = "商业广告"
    SOCIAL_MEDIA = "社交媒体"
    EDUCATIONAL = "教育"
    ENTERTAINMENT = "娱乐"

# 旁白声音枚举
class NarrationVoice(str, Enum):
    CHINESE_FEMALE = "chinese_female"
    CHINESE_MALE = "chinese_male"
    ENGLISH_FEMALE = "english_female"
    ENGLISH_MALE = "english_male"

class VideoGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="视频主题")
    style: str = Field(default="专业", description="视频风格")
    targetDuration: Optional[int] = Field(default=60, ge=15, le=180, description="目标时长（秒）")
    shotCount: Optional[int] = Field(default=6, ge=3, le=12, description="镜头数量")
    enableNarration: bool = Field(default=False, description="是否启用旁白")
    narrationVoice: str = Field(default="chinese_female", description="旁白声音")
    generationMode: str = Field(default="manual", description="生成模式：manual | autopilot")
    additionalRequirements: Optional[str] = Field(default=None, description="补充要求")
    sourceMaterial: Optional[Dict[str, Any]] = Field(default=None, description="URL/图片/视频来源材料")

    model_config = {"extra": "ignore"}

    @validator('topic')
    def validate_topic(cls, v):
        if not v or v.strip() == "":
            raise ValueError("主题不能为空")
        return v.strip()

class ShotData(BaseModel):
    sequence: int = Field(..., ge=1, description="镜头序号")
    prompt: str = Field(..., min_length=10, max_length=1000, description="镜头描述")
    duration: float = Field(..., gt=0, le=8.0, description="镜头时长（秒）")
    shotType: str = Field(default="medium shot", description="镜头类型")
    imagePath: Optional[str] = None
    videoPath: Optional[str] = None
    status: str = Field(default="pending", description="状态")
    qualityScore: Optional[float] = Field(default=None, ge=0, le=1, description="质量分数")

class ScriptConfirmRequest(BaseModel):
    script: str = Field(..., min_length=50, description="视频脚本")
    shots: List[ShotData] = Field(..., min_items=1, max_items=12, description="镜头列表")
    options: Optional[Dict[str, Any]] = None

    @validator('shots')
    def validate_shots_sequence(cls, v):
        sequences = [shot.sequence for shot in v]
        if len(sequences) != len(set(sequences)):
            raise ValueError("镜头序号不能重复")
        if sorted(sequences) != list(range(1, len(sequences) + 1)):
            raise ValueError("镜头序号必须从1开始连续")
        return v

class TaskResponse(BaseModel):
    success: bool
    taskId: str
    status: str
    progress: float
    message: str = ""
    data: Optional[Dict[str, Any]] = None

class IntentGenerationRequest(BaseModel):
    userInput: str = Field(..., min_length=2, max_length=3000, description="自然语言输入，可包含 URL")
    style: str = Field(default="专业", description="视频风格")
    targetDuration: Optional[int] = Field(default=60, ge=10, le=300, description="目标时长（秒）")
    shotCount: Optional[int] = Field(default=6, ge=3, le=20, description="镜头数量")
    enableNarration: bool = Field(default=False, description="是否启用旁白")
    narrationVoice: str = Field(default="chinese_female", description="旁白声音")
    generationMode: str = Field(default="manual", description="生成模式：manual | autopilot")
    additionalRequirements: Optional[str] = Field(default=None, description="补充要求")

class IntentGenerationResponse(BaseModel):
    success: bool
    action: Literal["created", "needs_clarification"]
    taskId: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    message: str = ""
    sourceMaterial: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []

@router.post("/create", response_model=TaskResponse)
async def create_video_task(request: VideoGenerationRequest, background_tasks: BackgroundTasks, current_user: Optional[User] = Depends(get_current_user_optional)):
    orchestrator = get_orchestrator()
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    
    config = GenerationConfig(
        topic=request.topic,
        style=request.style,
        target_duration=request.targetDuration,
        shot_count=request.shotCount,
        enable_narration=request.enableNarration,
        narration_voice=request.narrationVoice,
        generation_mode=request.generationMode,
        additional_requirements=request.additionalRequirements or "",
        source_material=request.sourceMaterial
    )
    
    # 同步初始化状态
    initial_state = TaskState(task_id=task_id, config=config, user_id=current_user.id if current_user else 0)
    orchestrator._save_task_state(initial_state)
    
    # 后台运行
    background_tasks.add_task(orchestrator.generate_full_video, config, task_id, initial_state.user_id)
    
    return TaskResponse(success=True, taskId=task_id, status="pending", progress=0)

@router.post("/intent", response_model=IntentGenerationResponse)
async def create_video_from_intent(
    request: IntentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    自然语言生成入口。

    用户可以把 URL 直接写在输入里。系统会先拉取来源内容，并判断意图是否足够明确：
    - 明确：创建视频生成任务
    - 不明确：返回右侧 Producer 面板需要追问的内容
    """
    ingest_service = UrlIngestService()
    urls = ingest_service.extract_urls(request.userInput)
    text_content = ingest_service.strip_urls(request.userInput, urls)

    source_material = None
    if urls:
        source_material = await ingest_service.ingest(urls[0])

    if not _is_intent_clear(request.userInput, text_content, bool(urls)):
        return IntentGenerationResponse(
            success=True,
            action="needs_clarification",
            message=_clarification_message(source_material),
            sourceMaterial=source_material,
            suggestions=_clarification_suggestions(source_material),
        )

    topic = text_content or request.userInput.strip()
    orchestrator = get_orchestrator()
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    config = GenerationConfig(
        topic=topic,
        style=request.style,
        target_duration=request.targetDuration or 60,
        shot_count=request.shotCount or 6,
        enable_narration=request.enableNarration,
        narration_voice=request.narrationVoice,
        generation_mode=request.generationMode,
        additional_requirements=request.additionalRequirements or "",
        source_material=source_material,
    )

    initial_state = TaskState(
        task_id=task_id,
        config=config,
        user_id=current_user.id if current_user else 0,
    )
    if source_material:
        initial_state.add_log(
            f"🔗 已识别输入来源：{source_material.get('type')} | "
            f"{source_material.get('title') or source_material.get('url')}",
            "info",
        )
    orchestrator._save_task_state(initial_state)
    background_tasks.add_task(orchestrator.generate_full_video, config, task_id, initial_state.user_id)

    return IntentGenerationResponse(
        success=True,
        action="created",
        taskId=task_id,
        status="pending",
        progress=0,
        message="已理解输入，正在创建视频生成任务",
        sourceMaterial=source_material,
    )

def _is_intent_clear(user_input: str, text_content: str, has_url: bool) -> bool:
    text = (text_content or "").strip()
    if not has_url:
        return len((user_input or "").strip()) >= 2

    if len(text) >= 12:
        return True

    compact = "".join(text.split())
    return len(compact) >= 4 and any(
        keyword in text
        for keyword in ["做", "生成", "改", "二创", "总结", "推广", "广告", "种草", "解说", "参考"]
    )

def _clarification_message(source_material: Optional[Dict[str, Any]]) -> str:
    if not source_material:
        return "我还需要知道你想生成什么类型的视频。"

    source_type = source_material.get("type")
    if source_type == "video":
        return "我已识别到视频链接。请补充你想做二创改写、风格参考，还是内容总结。"
    if source_type == "image":
        return "我已识别到图片链接。请补充你想参考主体、构图，还是视觉风格。"
    return "我已拉取到网页内容。请补充你想做产品推广、内容总结，还是社媒种草视频。"

def _clarification_suggestions(source_material: Optional[Dict[str, Any]]) -> List[str]:
    source_type = (source_material or {}).get("type")
    if source_type == "video":
        return ["参考结构做二创", "总结成解说视频", "改成科技感版本"]
    if source_type == "image":
        return ["参考这张图生成短片", "保持主体一致做产品视频", "提取视觉风格生成视频"]
    return ["做一个30秒产品推广视频", "总结网页内容做科普视频", "改成小红书种草视频"]

@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    orchestrator = get_orchestrator()
    # 核心修复：直接通过 orchestrator 加载，它知道正确路径
    state = orchestrator.load_task_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return TaskResponse(
        success=True, 
        taskId=state.task_id, 
        status=state.status.value, 
        progress=state.progress, 
        data=state.to_dict()
    )

@router.post("/task/{task_id}/confirm")
async def confirm_and_continue(task_id: str, request: ScriptConfirmRequest, background_tasks: BackgroundTasks):
    orchestrator = get_orchestrator()
    state = orchestrator.load_task_state(task_id)
    if not state: raise HTTPException(status_code=404)
    background_tasks.add_task(orchestrator.continue_from_confirmation, state, request.script, request.shots, request.options)
    return {"success": True}

@router.post("/task/{task_id}/regenerate-shot")
async def regenerate_shot(task_id: str, request: Dict[str, Any], background_tasks: BackgroundTasks):
    orchestrator = get_orchestrator()
    state = orchestrator.load_task_state(task_id)
    if not state: raise HTTPException(status_code=404)
    
    shot = next((s for s in state.shots if s.sequence == request.get("sequence")), None)
    if shot:
        shot.prompt = request.get("prompt", shot.prompt)
        shot.duration = request.get("duration", shot.duration)
        shot.status = "pending"
        orchestrator._save_task_state(state)
        # 简单触发逻辑
        background_tasks.add_task(orchestrator._stage_generate_storyboard_images, state, state.config)
    return {"success": True}
