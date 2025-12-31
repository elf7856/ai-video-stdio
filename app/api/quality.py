"""
质量检查API端点

提供视频质量检查和自动重新生成的HTTP接口
"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.quality import (
    VideoQualityChecker,
    QualityCheckConfig,
    QualityReport,
    ShotQualityResult,
    check_video_quality,
    check_project_quality
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quality", tags=["质量检查"])


# ============================================================
# 请求/响应模型
# ============================================================

class VideoQualityCheckRequest(BaseModel):
    """单个视频质量检查请求"""
    video_path: str = Field(..., description="视频文件路径")
    prompt: str = Field(..., description="生成该视频的提示词")
    shot_index: int = Field(default=0, description="镜头索引")
    shot_id: str = Field(default="", description="镜头ID")


class ProjectQualityCheckRequest(BaseModel):
    """项目质量检查请求"""
    project_id: str = Field(default="", description="项目ID")
    videos: List[VideoQualityCheckRequest] = Field(..., description="视频列表")
    config: Optional[dict] = Field(default=None, description="检查配置")


class QualityCheckResponse(BaseModel):
    """质量检查响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class RegenerationStartRequest(BaseModel):
    """启动重新生成请求"""
    project_id: str = Field(..., description="项目ID")
    quality_report_id: str = Field(default="", description="质量报告ID（可选）")
    target_score: float = Field(default=0.7, ge=0, le=1, description="目标质量分数")
    max_iterations: int = Field(default=3, ge=1, le=10, description="最大迭代次数")


# ============================================================
# 质量检查任务存储（简单内存存储）
# ============================================================

quality_check_tasks = {}
regeneration_tasks = {}


# ============================================================
# API端点
# ============================================================

@router.post("/check/video", response_model=QualityCheckResponse)
async def check_single_video_quality(request: VideoQualityCheckRequest):
    """
    检查单个视频的质量

    返回视觉一致性、内容匹配度、技术质量的综合评分
    """
    try:
        if not os.path.exists(request.video_path):
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {request.video_path}")

        result = check_video_quality(
            video_path=request.video_path,
            prompt=request.prompt
        )

        return QualityCheckResponse(
            success=True,
            message="质量检查完成",
            data={
                "overall_score": result.overall_score,
                "overall_level": result.overall_level.value,
                "visual_consistency": {
                    "score": result.visual_consistency.score,
                    "level": result.visual_consistency.level.value,
                    "color_consistency": result.visual_consistency.color_consistency,
                    "style_consistency": result.visual_consistency.style_consistency,
                    "issues": result.visual_consistency.inconsistencies
                },
                "content_match": {
                    "score": result.content_match.score,
                    "level": result.content_match.level.value,
                    "semantic_match": result.content_match.semantic_match,
                    "visual_match": result.content_match.visual_match,
                    "matched_elements": result.content_match.matched_elements,
                    "missing_elements": result.content_match.missing_elements
                },
                "technical_quality": {
                    "score": result.technical_quality.score,
                    "level": result.technical_quality.level.value,
                    "resolution": result.technical_quality.resolution,
                    "fps": result.technical_quality.fps,
                    "issues": result.technical_quality.issues
                },
                "needs_regeneration": result.needs_regeneration,
                "regeneration_reason": result.regeneration_reason,
                "suggestions": result.regeneration_suggestions
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"质量检查失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"质量检查失败: {str(e)}")


@router.post("/check/project", response_model=QualityCheckResponse)
async def check_project_video_quality(request: ProjectQualityCheckRequest):
    """
    检查整个项目的视频质量

    分析所有镜头并返回综合质量报告
    """
    try:
        # 构建视频列表
        videos = []
        for v in request.videos:
            if not os.path.exists(v.video_path):
                logger.warning(f"视频文件不存在，跳过: {v.video_path}")
                continue
            videos.append({
                "path": v.video_path,
                "prompt": v.prompt,
                "shot_index": v.shot_index,
                "shot_id": v.shot_id
            })

        if not videos:
            raise HTTPException(status_code=400, detail="没有有效的视频文件")

        # 构建配置
        config = None
        if request.config:
            config = QualityCheckConfig(**request.config)

        # 执行检查
        report = check_project_quality(
            videos=videos,
            project_id=request.project_id,
            config=config
        )

        return QualityCheckResponse(
            success=True,
            message="项目质量检查完成",
            data={
                "project_id": report.project_id,
                "overall_score": report.overall_score,
                "overall_level": report.overall_level.value,
                "overall_visual_consistency": report.overall_visual_consistency,
                "overall_content_match": report.overall_content_match,
                "overall_technical_quality": report.overall_technical_quality,
                "total_shots": len(report.shots),
                "shots_to_regenerate": report.shots_to_regenerate,
                "summary": report.summary,
                "recommendations": report.recommendations,
                "shots": [
                    {
                        "shot_index": s.shot_index,
                        "overall_score": s.overall_score,
                        "overall_level": s.overall_level.value,
                        "needs_regeneration": s.needs_regeneration,
                        "regeneration_reason": s.regeneration_reason
                    }
                    for s in report.shots
                ]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"项目质量检查失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"项目质量检查失败: {str(e)}")


@router.post("/check/async", response_model=QualityCheckResponse)
async def start_async_quality_check(
    request: ProjectQualityCheckRequest,
    background_tasks: BackgroundTasks
):
    """
    异步启动项目质量检查

    返回任务ID，可通过状态接口查询进度
    """
    import uuid

    task_id = str(uuid.uuid4())

    # 存储任务
    quality_check_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "message": "等待开始",
        "result": None
    }

    # 添加后台任务
    background_tasks.add_task(
        run_quality_check_task,
        task_id,
        request
    )

    return QualityCheckResponse(
        success=True,
        message="质量检查任务已启动",
        data={"task_id": task_id}
    )


@router.get("/check/status/{task_id}", response_model=QualityCheckResponse)
async def get_quality_check_status(task_id: str):
    """获取质量检查任务状态"""
    if task_id not in quality_check_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = quality_check_tasks[task_id]
    return QualityCheckResponse(
        success=True,
        message=task["message"],
        data={
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "result": task["result"]
        }
    )


@router.get("/config/default", response_model=QualityCheckResponse)
async def get_default_config():
    """获取默认质量检查配置"""
    config = QualityCheckConfig()
    return QualityCheckResponse(
        success=True,
        message="默认配置",
        data={
            "check_visual_consistency": config.check_visual_consistency,
            "check_content_match": config.check_content_match,
            "check_technical_quality": config.check_technical_quality,
            "keyframe_count": config.keyframe_count,
            "min_acceptable_score": config.min_acceptable_score,
            "regeneration_threshold": config.regeneration_threshold,
            "weights": config.weights,
            "use_llm_analysis": config.use_llm_analysis
        }
    )


# ============================================================
# 后台任务函数
# ============================================================

async def run_quality_check_task(task_id: str, request: ProjectQualityCheckRequest):
    """执行质量检查后台任务"""
    try:
        quality_check_tasks[task_id]["status"] = "running"
        quality_check_tasks[task_id]["message"] = "正在检查..."

        # 构建视频列表
        videos = []
        for v in request.videos:
            if os.path.exists(v.video_path):
                videos.append({
                    "path": v.video_path,
                    "prompt": v.prompt,
                    "shot_index": v.shot_index,
                    "shot_id": v.shot_id
                })

        if not videos:
            quality_check_tasks[task_id]["status"] = "failed"
            quality_check_tasks[task_id]["message"] = "没有有效的视频文件"
            return

        # 执行检查
        config = QualityCheckConfig(**request.config) if request.config else None
        checker = VideoQualityChecker(config=config)

        try:
            total = len(videos)
            results = []

            for i, video in enumerate(videos):
                quality_check_tasks[task_id]["progress"] = int((i / total) * 100)
                quality_check_tasks[task_id]["message"] = f"检查镜头 {i+1}/{total}"

                result = checker.check_video(
                    video_path=video["path"],
                    prompt=video["prompt"],
                    shot_index=video["shot_index"],
                    shot_id=video.get("shot_id", "")
                )
                results.append(result)

            # 生成报告
            report = QualityReport(project_id=request.project_id, config=config or QualityCheckConfig())
            report.shots = results
            report.calculate_overall_scores()
            checker._generate_report_summary(report)

            quality_check_tasks[task_id]["status"] = "completed"
            quality_check_tasks[task_id]["progress"] = 100
            quality_check_tasks[task_id]["message"] = "检查完成"
            quality_check_tasks[task_id]["result"] = {
                "overall_score": report.overall_score,
                "overall_level": report.overall_level.value,
                "shots_to_regenerate": report.shots_to_regenerate,
                "summary": report.summary
            }

        finally:
            checker.cleanup()

    except Exception as e:
        logger.error(f"质量检查任务失败: {e}", exc_info=True)
        quality_check_tasks[task_id]["status"] = "failed"
        quality_check_tasks[task_id]["message"] = f"检查失败: {str(e)}"
