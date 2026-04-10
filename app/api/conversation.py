"""
对话式视频生成API
支持用户与AI进行多轮对话，动态调整脚本和分镜
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.video_generation.conversational_service import ConversationalGenerationService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request Models ====================

class StartConversationRequest(BaseModel):
    """开始对话请求"""
    topic: str = Field(..., description="视频主题")
    style: str = Field(default="专业", description="视频风格")
    shot_count: int = Field(default=6, description="镜头数量")
    target_duration: int = Field(default=60, description="目标时长（秒）")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str = Field(..., description="用户消息")
    conversation_history: List[Dict[str, Any]] = Field(..., description="对话历史")
    current_script: str = Field(..., description="当前脚本")
    current_shots: List[Dict[str, Any]] = Field(..., description="当前分镜")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class ConfirmGenerationRequest(BaseModel):
    """确认生成请求"""
    task_id: str = Field(..., description="任务ID")
    final_script: str = Field(..., description="最终脚本")
    final_shots: List[Dict[str, Any]] = Field(..., description="最终分镜")
    options: Optional[Dict[str, Any]] = Field(default=None, description="生成选项")


# ==================== Response Models ====================

class ConversationResponse(BaseModel):
    """对话响应"""
    success: bool
    conversation_history: Optional[List[Dict[str, Any]]] = None
    script: Optional[str] = None
    shots: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    ai_response: Optional[str] = None
    error: Optional[str] = None


class GenerationResponse(BaseModel):
    """生成响应"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


# ==================== API Endpoints ====================

@router.post("/start", response_model=ConversationResponse)
async def start_conversation(
    request: StartConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    开始一个新的对话式生成会话

    用户提供初始主题，系统生成初始脚本和分镜，并返回对话历史
    """
    try:
        logger.info(f"用户 {current_user.id} 开始对话式生成: {request.topic}")

        service = ConversationalGenerationService()

        result = await service.start_conversation(
            user_id=current_user.id,
            initial_topic=request.topic,
            style=request.style,
            shot_count=request.shot_count,
            target_duration=request.target_duration
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "启动对话失败")
            )

        return ConversationResponse(
            success=True,
            conversation_history=result.get("conversation_history"),
            script=result.get("script"),
            shots=result.get("shots"),
            metadata=result.get("metadata")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动对话失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动对话失败: {str(e)}"
        )


@router.post("/message", response_model=ConversationResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送用户消息并获取AI响应

    用户发送消息，系统分析意图并修改脚本和分镜，返回更新后的对话历史
    """
    try:
        logger.info(f"用户 {current_user.id} 发送消息: {request.message[:50]}...")

        service = ConversationalGenerationService()

        result = await service.process_user_message(
            user_id=current_user.id,
            user_message=request.message,
            conversation_history=request.conversation_history,
            current_script=request.current_script,
            current_shots=request.current_shots,
            metadata=request.metadata
        )

        if not result.get("success"):
            # 即使处理失败，也返回对话历史（包含错误消息）
            return ConversationResponse(
                success=False,
                conversation_history=result.get("conversation_history"),
                script=result.get("script"),
                shots=result.get("shots"),
                error=result.get("error")
            )

        return ConversationResponse(
            success=True,
            conversation_history=result.get("conversation_history"),
            script=result.get("script"),
            shots=result.get("shots"),
            ai_response=result.get("ai_response")
        )

    except Exception as e:
        logger.error(f"处理消息失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理消息失败: {str(e)}"
        )


@router.post("/confirm", response_model=GenerationResponse)
async def confirm_and_generate(
    request: ConfirmGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    确认脚本并开始生成视频

    用户确认最终脚本和分镜，系统开始生成视频
    """
    try:
        logger.info(f"用户 {current_user.id} 确认生成: {request.task_id}")

        service = ConversationalGenerationService()

        result = await service.confirm_and_generate(
            user_id=current_user.id,
            task_id=request.task_id,
            final_script=request.final_script,
            final_shots=request.final_shots,
            options=request.options
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "生成视频失败")
            )

        return GenerationResponse(
            success=True,
            message="视频生成已启动"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认生成失败: {str(e)}"
        )
