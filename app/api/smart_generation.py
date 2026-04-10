"""
统一视频生成 API
智能路由到不同的生成链路
"""

import logging
from fastapi import APIRouter, Form, HTTPException, BackgroundTasks
from typing import Optional

from app.services.video_generation.smart_router import get_smart_router
from app.services.video_generation.orchestrator import get_orchestrator, GenerationConfig
from app.services.video_recreation import get_recreation_service, RecreationConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate", tags=["unified-generation"])


@router.post("/smart")
async def smart_video_generation(
    user_input: str = Form(..., description="用户输入（可以是纯文本、包含视频URL、图片URL等）"),
    shot_count: int = Form(6, description="镜头数量"),
    user_id: int = Form(1),  # TODO: 从认证中获取
    background_tasks: BackgroundTasks = None
):
    """
    智能视频生成 - 根据用户输入自动选择生成链路

    支持的输入类型：
    1. 纯文本描述 → 从零生成
       示例: "制作一个关于人工智能的科普视频"

    2. 包含视频URL → 视频二创
       示例: "将这个视频 https://youtube.com/watch?v=xxx 转换为动漫风格"

    3. 包含图片URL → 图片参考生成
       示例: "基于这张图片 https://example.com/image.jpg 生成视频"

    4. 包含网页URL → 网页内容参考生成
       示例: "根据这个产品页面 https://example.com/product 制作宣传视频"

    Args:
        user_input: 用户输入
        shot_count: 镜头数量
        user_id: 用户ID
        background_tasks: 后台任务

    Returns:
        任务信息
    """
    try:
        logger.info(f"收到智能生成请求: {user_input[:100]}...")

        # 1. 分析用户输入
        router_service = get_smart_router()
        analysis = router_service.analyze_input(user_input)

        logger.info(f"输入类型: {analysis.input_type}, 生成模式: {analysis.generation_mode}")

        # 2. 根据分析结果路由到不同的生成链路
        if analysis.generation_mode == "recreation":
            # 链路1: 视频二创
            return await _handle_recreation(
                analysis=analysis,
                shot_count=shot_count,
                user_id=user_id,
                background_tasks=background_tasks
            )

        elif analysis.generation_mode == "reference":
            # 链路2: 参考生成（图片或网页）
            return await _handle_reference_generation(
                analysis=analysis,
                shot_count=shot_count,
                user_id=user_id,
                background_tasks=background_tasks
            )

        else:
            # 链路3: 从零生成
            return await _handle_from_scratch(
                analysis=analysis,
                shot_count=shot_count,
                user_id=user_id,
                background_tasks=background_tasks
            )

    except Exception as e:
        logger.error(f"智能生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_recreation(
    analysis,
    shot_count: int,
    user_id: int,
    background_tasks: BackgroundTasks
) -> dict:
    """处理视频二创"""
    logger.info("🎬 路由到: 视频二创链路")

    video_url = analysis.video_urls[0] if analysis.video_urls else None
    if not video_url:
        raise HTTPException(status_code=400, detail="未检测到视频URL")

    # 提取风格
    target_style = analysis.text_content or "专业风格"

    # 创建二创配置
    config = RecreationConfig(
        original_video_url=video_url,
        target_style=target_style,
        target_description=analysis.text_content,
        shot_count=shot_count,
        enable_keyframe_reference=True,
        generation_mode="autopilot"
    )

    # 创建任务ID
    import uuid
    task_id = f"smart_recreation_{uuid.uuid4().hex[:8]}"

    # 在后台执行二创
    async def recreation_task():
        try:
            recreation_service = get_recreation_service()
            result = await recreation_service.recreate_video(
                config=config,
                user_id=user_id
            )

            if not result.success:
                logger.error(f"视频二创失败: {result.error}")
                return

            # 继续生成视频
            orchestrator = get_orchestrator()

            from app.services.video_generation.orchestrator import (
                GenerationConfig as OrchestratorConfig,
                TaskState,
                ShotInfo
            )

            gen_config = OrchestratorConfig(
                topic=target_style,
                style=target_style,
                target_duration=sum(shot.get('duration', 5) for shot in result.generated_shots),
                shot_count=len(result.generated_shots),
                generation_mode="autopilot",
                enable_narration=False
            )

            state = TaskState(
                task_id=task_id,
                config=gen_config,
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

            logger.info(f"视频二创完成: {task_id}")

        except Exception as e:
            logger.error(f"视频二创任务失败: {e}")

    if background_tasks:
        background_tasks.add_task(recreation_task)
    else:
        import asyncio
        asyncio.create_task(recreation_task())

    return {
        "success": True,
        "task_id": task_id,
        "generation_mode": "recreation",
        "message": "视频二创任务已启动",
        "video_url": video_url,
        "target_style": target_style,
        "shot_count": shot_count
    }


async def _handle_reference_generation(
    analysis,
    shot_count: int,
    user_id: int,
    background_tasks: BackgroundTasks
) -> dict:
    """处理参考生成（图片或网页）"""
    logger.info("🖼️ 路由到: 参考生成链路")

    # 创建生成配置
    config = GenerationConfig(
        topic=analysis.text_content or "视频生成",
        style=analysis.text_content or "专业",
        shot_count=shot_count,
        generation_mode="autopilot",
        user_images=analysis.image_urls if analysis.image_urls else None,
        user_urls=analysis.web_urls if analysis.web_urls else None,
        enable_narration=False
    )

    # 创建任务ID
    import uuid
    task_id = f"smart_ref_{uuid.uuid4().hex[:8]}"

    # 在后台执行生成
    async def generation_task():
        try:
            orchestrator = get_orchestrator()
            await orchestrator.generate_full_video(
                config=config,
                task_id=task_id,
                user_id=user_id
            )
            logger.info(f"参考生成完成: {task_id}")
        except Exception as e:
            logger.error(f"参考生成任务失败: {e}")

    if background_tasks:
        background_tasks.add_task(generation_task)
    else:
        import asyncio
        asyncio.create_task(generation_task())

    return {
        "success": True,
        "task_id": task_id,
        "generation_mode": "reference",
        "message": "参考生成任务已启动",
        "has_images": bool(analysis.image_urls),
        "has_urls": bool(analysis.web_urls),
        "shot_count": shot_count
    }


async def _handle_from_scratch(
    analysis,
    shot_count: int,
    user_id: int,
    background_tasks: BackgroundTasks
) -> dict:
    """处理从零生成"""
    logger.info("✨ 路由到: 从零生成链路")

    # 创建生成配置
    config = GenerationConfig(
        topic=analysis.text_content or "视频生成",
        style="专业",
        shot_count=shot_count,
        generation_mode="autopilot",
        enable_narration=False
    )

    # 创建任务ID
    import uuid
    task_id = f"smart_scratch_{uuid.uuid4().hex[:8]}"

    # 在后台执行生成
    async def generation_task():
        try:
            orchestrator = get_orchestrator()
            await orchestrator.generate_full_video(
                config=config,
                task_id=task_id,
                user_id=user_id
            )
            logger.info(f"从零生成完成: {task_id}")
        except Exception as e:
            logger.error(f"从零生成任务失败: {e}")

    if background_tasks:
        background_tasks.add_task(generation_task)
    else:
        import asyncio
        asyncio.create_task(generation_task())

    return {
        "success": True,
        "task_id": task_id,
        "generation_mode": "from_scratch",
        "message": "从零生成任务已启动",
        "topic": analysis.text_content,
        "shot_count": shot_count
    }


@router.get("/status/{task_id}")
async def get_generation_status(task_id: str):
    """
    查询生成任务状态（统一接口）

    Args:
        task_id: 任务ID

    Returns:
        任务状态信息
    """
    try:
        orchestrator = get_orchestrator()
        state = orchestrator.load_task_state(task_id)

        if not state:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            "success": True,
            "task_id": task_id,
            "status": state.status.value,
            "progress": state.progress,
            "final_video": state.final_video_path,
            "shots": [
                {
                    "sequence": s.sequence,
                    "status": s.status,
                    "video_path": s.video_path,
                    "quality_score": s.quality_score
                }
                for s in state.shots
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
