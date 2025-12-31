"""
自动重新生成服务

根据质量检查结果自动重新生成低质量的视频片段
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .models import (
    QualityReport,
    QualityCheckConfig,
    ShotQualityResult,
    RegenerationRequest,
    QualityLevel
)
from .checker import VideoQualityChecker

from app.services.video_generation.base_client import (
    BaseVideoGenerationClient,
    VideoGenerationRequest,
    VideoGenerationResult
)

logger = logging.getLogger(__name__)


class RegenerationResult:
    """单次重新生成的结果"""

    def __init__(
        self,
        shot_index: int,
        success: bool,
        original_score: float,
        new_score: float,
        improved: bool,
        video_path: Optional[str] = None,
        attempt: int = 1,
        error: Optional[str] = None
    ):
        self.shot_index = shot_index
        self.success = success
        self.original_score = original_score
        self.new_score = new_score
        self.improved = improved
        self.video_path = video_path
        self.attempt = attempt
        self.error = error


class RegenerationReport:
    """重新生成任务的完整报告"""

    def __init__(self):
        self.started_at: datetime = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.total_shots: int = 0
        self.regenerated_shots: int = 0
        self.successful_improvements: int = 0
        self.failed_regenerations: int = 0
        self.results: List[RegenerationResult] = []
        self.final_quality_report: Optional[QualityReport] = None

    def add_result(self, result: RegenerationResult) -> None:
        """添加单次重新生成结果"""
        self.results.append(result)
        self.regenerated_shots += 1
        if result.success and result.improved:
            self.successful_improvements += 1
        elif not result.success:
            self.failed_regenerations += 1

    def complete(self, final_report: QualityReport) -> None:
        """完成重新生成任务"""
        self.completed_at = datetime.now()
        self.final_quality_report = final_report

    @property
    def duration(self) -> float:
        """任务耗时（秒）"""
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()

    @property
    def improvement_rate(self) -> float:
        """改进成功率"""
        if self.regenerated_shots == 0:
            return 0.0
        return self.successful_improvements / self.regenerated_shots

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration,
            "total_shots": self.total_shots,
            "regenerated_shots": self.regenerated_shots,
            "successful_improvements": self.successful_improvements,
            "failed_regenerations": self.failed_regenerations,
            "improvement_rate": self.improvement_rate,
            "results": [
                {
                    "shot_index": r.shot_index,
                    "success": r.success,
                    "original_score": r.original_score,
                    "new_score": r.new_score,
                    "improved": r.improved,
                    "attempt": r.attempt,
                    "error": r.error
                }
                for r in self.results
            ]
        }


class AutoRegenerator:
    """
    自动重新生成器

    自动检测并重新生成低质量的视频片段，具有以下特性：
    1. 智能prompt优化
    2. 多次重试机制
    3. 质量对比验证
    4. 进度回调支持
    """

    def __init__(
        self,
        video_client: BaseVideoGenerationClient,
        quality_checker: Optional[VideoQualityChecker] = None,
        quality_config: Optional[QualityCheckConfig] = None,
        max_retries: int = 3,
        min_improvement: float = 0.1
    ):
        """
        初始化自动重新生成器

        Args:
            video_client: 视频生成客户端
            quality_checker: 质量检查器（可选，会自动创建）
            quality_config: 质量检查配置
            max_retries: 每个镜头最大重试次数
            min_improvement: 最小改进幅度（低于此值不替换）
        """
        self.video_client = video_client
        self.quality_config = quality_config or QualityCheckConfig()
        self.quality_checker = quality_checker or VideoQualityChecker(
            config=self.quality_config
        )
        self.max_retries = max_retries
        self.min_improvement = min_improvement

        logger.info(f"自动重新生成器初始化: max_retries={max_retries}, min_improvement={min_improvement}")

    async def regenerate_from_report(
        self,
        quality_report: QualityReport,
        videos: List[Dict[str, Any]],
        output_dir: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> RegenerationReport:
        """
        根据质量报告自动重新生成低质量片段

        Args:
            quality_report: 质量检查报告
            videos: 原始视频列表 [{path, prompt, shot_index, shot_id}, ...]
            output_dir: 输出目录
            progress_callback: 进度回调函数 (current, total, message)

        Returns:
            RegenerationReport: 重新生成报告
        """
        report = RegenerationReport()
        report.total_shots = len(videos)

        # 获取需要重新生成的镜头
        regeneration_requests = self.quality_checker.get_regeneration_requests(quality_report)

        if not regeneration_requests:
            logger.info("没有需要重新生成的镜头")
            report.complete(quality_report)
            return report

        logger.info(f"需要重新生成 {len(regeneration_requests)} 个镜头")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 逐个重新生成
        for i, request in enumerate(regeneration_requests):
            if progress_callback:
                progress_callback(
                    i + 1,
                    len(regeneration_requests),
                    f"重新生成镜头 {request.shot_index}"
                )

            # 获取原始信息
            original_video = next(
                (v for v in videos if v.get("shot_index") == request.shot_index),
                None
            )
            if not original_video:
                logger.warning(f"找不到镜头 {request.shot_index} 的原始信息")
                continue

            original_shot = next(
                (s for s in quality_report.shots if s.shot_index == request.shot_index),
                None
            )
            original_score = original_shot.overall_score if original_shot else 0

            # 重新生成
            result = await self._regenerate_shot(
                request=request,
                original_video=original_video,
                output_dir=output_dir
            )

            result.original_score = original_score
            report.add_result(result)

            # 如果成功且改进，更新视频列表
            if result.success and result.improved and result.video_path:
                original_video["path"] = result.video_path
                logger.info(
                    f"镜头 {request.shot_index} 改进: "
                    f"{original_score:.2f} -> {result.new_score:.2f}"
                )

        # 重新检查整体质量
        final_report = self.quality_checker.check_multiple_videos(
            videos,
            quality_report.project_id
        )
        report.complete(final_report)

        logger.info(
            f"重新生成完成: {report.successful_improvements}/{report.regenerated_shots} 个镜头改进, "
            f"整体质量: {final_report.overall_score:.2f}"
        )

        return report

    async def _regenerate_shot(
        self,
        request: RegenerationRequest,
        original_video: Dict[str, Any],
        output_dir: str
    ) -> RegenerationResult:
        """重新生成单个镜头"""
        shot_index = request.shot_index
        best_result: Optional[RegenerationResult] = None
        best_score = 0.0

        for attempt in range(1, self.max_retries + 1):
            logger.info(f"镜头 {shot_index} 重新生成尝试 {attempt}/{self.max_retries}")

            try:
                # 使用改进后的prompt
                prompt = request.improved_prompt or request.original_prompt

                # 如果是重试，进一步优化prompt
                if attempt > 1:
                    prompt = self._further_improve_prompt(
                        prompt,
                        request.quality_issues,
                        attempt
                    )

                # 生成视频
                gen_request = VideoGenerationRequest(
                    prompt=prompt,
                    duration=original_video.get("duration", 5.0),
                    resolution=original_video.get("resolution", "1280x720")
                )

                gen_result = await self.video_client.generate_video(gen_request)

                if not gen_result.success:
                    logger.warning(f"镜头 {shot_index} 生成失败: {gen_result.error_message}")
                    continue

                # 检查新视频质量
                new_video_path = gen_result.local_path
                if not new_video_path or not os.path.exists(new_video_path):
                    logger.warning(f"镜头 {shot_index} 视频文件不存在")
                    continue

                quality_result = self.quality_checker.check_video(
                    video_path=new_video_path,
                    prompt=prompt,
                    shot_index=shot_index
                )

                new_score = quality_result.overall_score

                # 检查是否改进
                if new_score > best_score:
                    # 移动到输出目录
                    final_path = os.path.join(
                        output_dir,
                        f"shot_{shot_index}_regen_v{attempt}.mp4"
                    )
                    if new_video_path != final_path:
                        import shutil
                        shutil.copy2(new_video_path, final_path)

                    best_score = new_score
                    best_result = RegenerationResult(
                        shot_index=shot_index,
                        success=True,
                        original_score=0,  # 将在外部设置
                        new_score=new_score,
                        improved=True,  # 暂时设为True
                        video_path=final_path,
                        attempt=attempt
                    )

                    # 如果质量足够好，提前结束
                    if new_score >= self.quality_config.min_acceptable_score:
                        logger.info(f"镜头 {shot_index} 达到可接受质量: {new_score:.2f}")
                        break

            except Exception as e:
                logger.error(f"镜头 {shot_index} 重新生成异常: {e}")

        # 返回最佳结果
        if best_result:
            return best_result
        else:
            return RegenerationResult(
                shot_index=shot_index,
                success=False,
                original_score=0,
                new_score=0,
                improved=False,
                error="所有重试均失败"
            )

    def _further_improve_prompt(
        self,
        prompt: str,
        issues: List[str],
        attempt: int
    ) -> str:
        """根据重试次数进一步改进prompt"""
        # 添加更具体的指令
        improvements = []

        if "视觉一致性" in str(issues):
            improvements.append("保持统一的色调和风格")
        if "内容不匹配" in str(issues):
            improvements.append("严格按照描述生成内容")
        if "技术质量" in str(issues):
            improvements.append("高清晰度，流畅的画面")

        if improvements:
            return f"{prompt}。要求：{'，'.join(improvements)}"

        return prompt

    async def auto_regenerate_until_acceptable(
        self,
        videos: List[Dict[str, Any]],
        project_id: str,
        output_dir: str,
        max_iterations: int = 3,
        target_score: float = 0.7,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> RegenerationReport:
        """
        自动迭代重新生成，直到达到可接受质量

        Args:
            videos: 视频列表
            project_id: 项目ID
            output_dir: 输出目录
            max_iterations: 最大迭代次数
            target_score: 目标质量分数
            progress_callback: 进度回调

        Returns:
            最终的重新生成报告
        """
        final_report = None

        for iteration in range(1, max_iterations + 1):
            logger.info(f"质量优化迭代 {iteration}/{max_iterations}")

            if progress_callback:
                progress_callback(iteration, max_iterations, f"质量优化迭代 {iteration}")

            # 检查当前质量
            quality_report = self.quality_checker.check_multiple_videos(
                videos, project_id
            )

            # 检查是否达到目标
            if quality_report.overall_score >= target_score:
                logger.info(
                    f"达到目标质量 {quality_report.overall_score:.2f} >= {target_score}"
                )
                if final_report:
                    final_report.complete(quality_report)
                else:
                    final_report = RegenerationReport()
                    final_report.total_shots = len(videos)
                    final_report.complete(quality_report)
                break

            # 没有需要重新生成的
            if not quality_report.shots_to_regenerate:
                logger.info("没有需要重新生成的镜头")
                if final_report:
                    final_report.complete(quality_report)
                break

            # 重新生成
            iteration_dir = os.path.join(output_dir, f"iteration_{iteration}")
            report = await self.regenerate_from_report(
                quality_report=quality_report,
                videos=videos,
                output_dir=iteration_dir,
                progress_callback=None
            )

            if final_report is None:
                final_report = report
            else:
                # 合并结果
                final_report.results.extend(report.results)
                final_report.regenerated_shots += report.regenerated_shots
                final_report.successful_improvements += report.successful_improvements
                final_report.failed_regenerations += report.failed_regenerations
                final_report.final_quality_report = report.final_quality_report

            # 检查是否有改进
            if report.successful_improvements == 0:
                logger.info("本轮没有改进，停止迭代")
                break

        if final_report is None:
            final_report = RegenerationReport()
            final_report.total_shots = len(videos)

        return final_report

    def cleanup(self) -> None:
        """清理资源"""
        if self.quality_checker:
            self.quality_checker.cleanup()


# 便捷函数
async def auto_regenerate_low_quality(
    videos: List[Dict[str, Any]],
    video_client: BaseVideoGenerationClient,
    output_dir: str,
    quality_config: Optional[QualityCheckConfig] = None,
    max_retries: int = 3
) -> RegenerationReport:
    """
    自动重新生成低质量视频的便捷函数

    Args:
        videos: 视频列表 [{path, prompt, shot_index}, ...]
        video_client: 视频生成客户端
        output_dir: 输出目录
        quality_config: 质量配置
        max_retries: 最大重试次数

    Returns:
        重新生成报告
    """
    regenerator = AutoRegenerator(
        video_client=video_client,
        quality_config=quality_config,
        max_retries=max_retries
    )

    try:
        # 先检查质量
        quality_report = regenerator.quality_checker.check_multiple_videos(
            videos, project_id="auto"
        )

        # 重新生成
        return await regenerator.regenerate_from_report(
            quality_report=quality_report,
            videos=videos,
            output_dir=output_dir
        )
    finally:
        regenerator.cleanup()
