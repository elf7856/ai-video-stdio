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
        narration_voice=request.narrationVoice
    )
    
    # 同步初始化状态
    initial_state = TaskState(task_id=task_id, config=config, user_id=current_user.id if current_user else 0)
    orchestrator._save_task_state(initial_state)
    
    # 后台运行
    background_tasks.add_task(orchestrator.generate_full_video, config, task_id, initial_state.user_id)
    
    return TaskResponse(success=True, taskId=task_id, status="pending", progress=0)

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