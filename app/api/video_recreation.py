"""
视频二创 API 端点
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
import shutil

from app.services.video_recreation import (
    get_recreation_service,
    RecreationConfig
)
from app.services.video_generation.orchestrator import get_orchestrator
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recreation", tags=["video-recreation"])


@router.post("/analyze")
async def analyze_video_for_recreation(
    video: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    target_style: str = Form(...),
    target_description: Optional[str] = Form(None),
    shot_count: int = Form(6),
    enable_keyframe_reference: bool = Form(True)
):
    """
    分析上传的视频或视频URL并生成二创方案

    Args:
        video: 上传的视频文件（可选）
        video_url: 视频URL（可选，支持YouTube、B站、TikTok等）
        target_style: 目标风格（如：动漫风格、科幻风格、复古风格等）
        target_description: 目标描述（可选）
        shot_count: 目标镜头数
        enable_keyframe_reference: 是否使用关键帧作为参考

    Returns:
        分析结果和生成的镜头方案
    """
    try:
        # 验证输入：必须提供视频文件或URL之一
        if not video and not video_url:
            raise HTTPException(
                status_code=400,
                detail="必须提供视频文件或视频URL"
            )

        video_path = None

        # 如果提供了视频文件，保存到临时目录
        if video:
            temp_dir = Path(settings.output_dir) / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            video_path = temp_dir / video.filename
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)

            logger.info(f"收到视频文件: {video.filename}, 目标风格: {target_style}")

        # 如果提供了URL
        if video_url:
            logger.info(f"收到视频URL: {video_url}, 目标风格: {target_style}")

        # 创建二创配置
        config = RecreationConfig(
            original_video_path=str(video_path) if video_path else None,
            original_video_url=video_url,
            target_style=target_style,
            target_description=target_description,
            shot_count=shot_count,
            enable_keyframe_reference=enable_keyframe_reference,
            generation_mode="manual"  # 先返回方案，等待用户确认
        )

        # 执行二创分析
        recreation_service = get_recreation_service()
        result = await recreation_service.recreate_video(
            config=config,
            user_id=1  # TODO: 从认证中获取真实用户ID
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        # 返回分析结果和生成的镜头方案
        return {
            "success": True,
            "task_id": result.task_id,
            "analysis": {
                "overall_summary": result.analysis.overall_summary,
                "narrative_structure": result.analysis.narrative_structure,
                "key_elements": result.analysis.key_elements,
                "mood": result.analysis.mood,
                "duration": result.analysis.duration,
                "scenes_count": len(result.analysis.scenes)
            },
            "shots": result.generated_shots,
            "keyframes_count": len([k for k in result.keyframes if k]) if result.keyframes else 0,
            "message": "视频分析完成，请确认生成方案"
        }

    except Exception as e:
        logger.error(f"视频二创分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_recreation_video(
    task_id: str = Form(...),
    user_id: int = Form(1),  # TODO: 从认证中获取
    background_tasks: BackgroundTasks = None
):
    """
    基于分析结果生成二创视频

    Args:
        task_id: 二创任务ID（从 analyze 接口返回）
        user_id: 用户ID
        background_tasks: 后台任务

    Returns:
        生成任务信息
    """
    try:
        # 读取分析结果
        recreation_dir = Path(settings.output_dir) / "recreation" / task_id
        analysis_file = recreation_dir / "analysis.json"

        if not analysis_file.exists():
            raise HTTPException(status_code=404, detail="任务不存在")

        import json
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        shots = analysis_data.get("shots", [])
        config_data = analysis_data.get("config", {})

        logger.info(f"开始生成二创视频，任务ID: {task_id}, 镜头数: {len(shots)}")

        # 调用 Orchestrator 生成视频
        orchestrator = get_orchestrator()

        # 构建 GenerationConfig
        from app.services.video_generation.orchestrator import GenerationConfig

        generation_config = GenerationConfig(
            topic=f"{config_data.get('target_style', '')} 风格视频",
            style=config_data.get('target_style', '专业'),
            target_duration=sum(shot.get('duration', 5) for shot in shots),
            shot_count=len(shots),
            generation_mode="autopilot",  # 自动生成
            enable_narration=False
        )

        # 创建新的任务ID用于生成
        import uuid
        generation_task_id = f"gen_{task_id}_{uuid.uuid4().hex[:6]}"

        # 在后台启动生成任务
        async def generate_task():
            try:
                # 创建任务状态
                from app.services.video_generation.orchestrator import TaskState, ShotInfo

                state = TaskState(
                    task_id=generation_task_id,
                    config=generation_config,
                    user_id=user_id
                )

                # 设置脚本和镜头
                state.script = analysis_data.get("analysis", {}).get("overall_summary", "")
                state.shots = [
                    ShotInfo(
                        sequence=shot.get("sequence", i+1),
                        prompt=shot.get("prompt", ""),
                        duration=shot.get("duration", 5.0),
                        shot_type=shot.get("shot_type", "medium shot"),
                        image_path=shot.get("imagePath")  # 关键帧作为参考
                    )
                    for i, shot in enumerate(shots)
                ]

                # 保存初始状态
                orchestrator._save_task_state(state)

                # 开始生成
                await orchestrator.continue_from_confirmation(
                    state=state,
                    script=state.script,
                    shots=[s.to_dict() for s in state.shots],
                    options=None
                )

                logger.info(f"二创视频生成完成: {generation_task_id}")

            except Exception as e:
                logger.error(f"二创视频生成失败: {e}")

        # 添加到后台任务
        if background_tasks:
            background_tasks.add_task(generate_task)
        else:
            # 如果没有后台任务支持，直接执行
            import asyncio
            asyncio.create_task(generate_task())

        return {
            "success": True,
            "generation_task_id": generation_task_id,
            "message": "视频生成任务已启动",
            "shots_count": len(shots)
        }

    except Exception as e:
        logger.error(f"启动视频生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_recreation_status(task_id: str):
    """
    查询二创任务状态

    Args:
        task_id: 任务ID（可以是分析任务ID或生成任务ID）

    Returns:
        任务状态信息
    """
    try:
        # 先尝试作为生成任务查询
        orchestrator = get_orchestrator()
        state = orchestrator.load_task_state(task_id)

        if state:
            return {
                "success": True,
                "task_type": "generation",
                "status": state.status.value,
                "progress": state.progress,
                "final_video": state.final_video_path,
                "shots": [
                    {
                        "sequence": s.sequence,
                        "status": s.status,
                        "video_path": s.video_path
                    }
                    for s in state.shots
                ]
            }

        # 如果不是生成任务，尝试作为分析任务查询
        recreation_dir = Path(settings.output_dir) / "recreation" / task_id
        analysis_file = recreation_dir / "analysis.json"

        if analysis_file.exists():
            import json
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "success": True,
                "task_type": "analysis",
                "status": "completed",
                "analysis": data.get("analysis"),
                "shots": data.get("shots")
            }

        raise HTTPException(status_code=404, detail="任务不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/one-click")
async def one_click_recreation(
    video: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    target_style: str = Form(...),
    target_description: Optional[str] = Form(None),
    shot_count: int = Form(6),
    enable_keyframe_reference: bool = Form(True),
    user_id: int = Form(1),  # TODO: 从认证中获取
    background_tasks: BackgroundTasks = None
):
    """
    一键式视频二创（分析 + 生成）

    Args:
        video: 上传的视频文件（可选）
        video_url: 视频URL（可选，支持YouTube、B站、TikTok等）
        target_style: 目标风格
        target_description: 目标描述（可选）
        shot_count: 目标镜头数
        enable_keyframe_reference: 是否使用关键帧作为参考
        user_id: 用户ID
        background_tasks: 后台任务

    Returns:
        任务信息
    """
    try:
        # 验证输入
        if not video and not video_url:
            raise HTTPException(
                status_code=400,
                detail="必须提供视频文件或视频URL"
            )

        video_path = None

        # 如果提供了视频文件，保存到临时目录
        if video:
            temp_dir = Path(settings.output_dir) / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            video_path = temp_dir / video.filename
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)

            logger.info(f"收到一键二创请求（文件）: {video.filename}, 目标风格: {target_style}")

        # 如果提供了URL
        if video_url:
            logger.info(f"收到一键二创请求（URL）: {video_url}, 目标风格: {target_style}")

        # 创建二创配置
        config = RecreationConfig(
            original_video_path=str(video_path) if video_path else None,
            original_video_url=video_url,
            target_style=target_style,
            target_description=target_description,
            shot_count=shot_count,
            enable_keyframe_reference=enable_keyframe_reference,
            generation_mode="autopilot"  # 自动生成
        )

        # 创建任务ID
        import uuid
        task_id = f"oneclick_{uuid.uuid4().hex[:8]}"

        # 在后台执行完整流程
        async def full_recreation_task():
            try:
                # 步骤1: 分析视频
                recreation_service = get_recreation_service()
                result = await recreation_service.recreate_video(
                    config=config,
                    user_id=user_id
                )

                if not result.success:
                    logger.error(f"视频分析失败: {result.error}")
                    return

                # 步骤2: 生成视频
                orchestrator = get_orchestrator()

                from app.services.video_generation.orchestrator import (
                    GenerationConfig,
                    TaskState,
                    ShotInfo
                )

                generation_config = GenerationConfig(
                    topic=f"{target_style} 风格视频",
                    style=target_style,
                    target_duration=sum(shot.get('duration', 5) for shot in result.generated_shots),
                    shot_count=len(result.generated_shots),
                    generation_mode="autopilot",
                    enable_narration=False
                )

                state = TaskState(
                    task_id=task_id,
                    config=generation_config,
                    user_id=user_id
                )

                state.script = result.analysis.overall_summary
                state.shots = [
                    ShotInfo(
                        sequence=shot.get("sequence", i+1),
                        prompt=shot.get("prompt", ""),
                        duration=shot.get("duration", 5.0),
                        shot_type=shot.get("shot_type", "medium shot"),
                        image_path=shot.get("imagePath")
                    )
                    for i, shot in enumerate(result.generated_shots)
                ]

                orchestrator._save_task_state(state)

                await orchestrator.continue_from_confirmation(
                    state=state,
                    script=state.script,
                    shots=[s.to_dict() for s in state.shots],
                    options=None
                )

                logger.info(f"一键二创完成: {task_id}")

            except Exception as e:
                logger.error(f"一键二创失败: {e}")

        # 添加到后台任务
        if background_tasks:
            background_tasks.add_task(full_recreation_task)
        else:
            import asyncio
            asyncio.create_task(full_recreation_task())

        return {
            "success": True,
            "task_id": task_id,
            "message": "一键二创任务已启动，请稍后查询状态",
            "target_style": target_style,
            "shot_count": shot_count
        }

    except Exception as e:
        logger.error(f"一键二创启动失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
