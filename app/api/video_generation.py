"""
视频生成API - 路径对齐稳定版
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
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

class VideoGenerationRequest(BaseModel):
    topic: str
    style: str = "专业"
    targetDuration: Optional[int] = 60
    shotCount: Optional[int] = 6
    enableNarration: bool = False
    narrationVoice: str = "chinese_female"

class ScriptConfirmRequest(BaseModel):
    script: str
    shots: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None

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