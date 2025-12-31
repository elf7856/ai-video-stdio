"""
多平台上传管理器
协调各平台上传器，支持批量上传和重试机制
"""
import logging
import asyncio
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from pydantic import BaseModel

from .base import (
    Platform,
    PlatformConfig,
    PlatformUploader,
    VideoMetadata,
    UploadResult,
    UploadStatus
)
from .youtube_uploader import YouTubeUploader
from .bilibili_uploader import BilibiliUploader
from .douyin_uploader import DouyinUploader

logger = logging.getLogger(__name__)

class UploadTask(BaseModel):
    """上传任务"""
    task_id: str
    video_path: str
    metadata: VideoMetadata
    platforms: List[Platform]
    results: List[UploadResult] = []
    status: str = "pending"  # pending, uploading, completed, failed
    created_at: str
    completed_at: Optional[str] = None

class UploadManager:
    """多平台上传管理器"""

    def __init__(self):
        self.uploaders: Dict[Platform, PlatformUploader] = {}
        self.tasks: Dict[str, UploadTask] = {}
        self.configs: Dict[Platform, PlatformConfig] = {}

    def configure_platform(self, config: PlatformConfig):
        """配置平台"""
        self.configs[config.platform] = config

        # 初始化对应的上传器
        if config.platform == Platform.YOUTUBE:
            self.uploaders[Platform.YOUTUBE] = YouTubeUploader(config)
        elif config.platform == Platform.BILIBILI:
            self.uploaders[Platform.BILIBILI] = BilibiliUploader(config)
        elif config.platform == Platform.DOUYIN:
            self.uploaders[Platform.DOUYIN] = DouyinUploader(config)
        # 可以继续添加其他平台...

        logger.info(f"Platform configured: {config.platform}")

    def get_configured_platforms(self) -> List[Platform]:
        """获取已配置的平台列表"""
        return list(self.configs.keys())

    def is_platform_configured(self, platform: Platform) -> bool:
        """检查平台是否已配置"""
        return platform in self.configs and self.configs[platform].enabled

    async def upload_to_platforms(
        self,
        video_path: str,
        metadata: VideoMetadata,
        platforms: List[Platform],
        on_progress: Optional[Callable[[UploadTask], None]] = None
    ) -> UploadTask:
        """
        上传视频到多个平台

        Args:
            video_path: 视频文件路径
            metadata: 视频元数据
            platforms: 目标平台列表
            on_progress: 进度回调函数

        Returns:
            UploadTask: 上传任务
        """
        # 创建任务
        task_id = f"upload_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(video_path)}"
        task = UploadTask(
            task_id=task_id,
            video_path=video_path,
            metadata=metadata,
            platforms=platforms,
            created_at=datetime.utcnow().isoformat()
        )
        self.tasks[task_id] = task

        # 过滤出已配置的平台
        enabled_platforms = [
            p for p in platforms
            if self.is_platform_configured(p)
        ]

        if not enabled_platforms:
            task.status = "failed"
            logger.error("No platforms configured")
            return task

        # 开始上传
        task.status = "uploading"

        # 并发上传到所有平台
        upload_coroutines = [
            self._upload_to_single_platform(
                platform,
                video_path,
                metadata
            )
            for platform in enabled_platforms
        ]

        # 执行所有上传任务
        results = await asyncio.gather(*upload_coroutines, return_exceptions=True)

        # 处理结果
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Upload exception: {result}")
                # 创建失败结果
                task.results.append(UploadResult(
                    platform=Platform.YOUTUBE,  # 默认
                    status=UploadStatus.FAILED,
                    error=str(result)
                ))
            else:
                task.results.append(result)

            # 触发进度回调
            if on_progress:
                on_progress(task)

        # 更新任务状态
        all_success = all(r.status == UploadStatus.SUCCESS for r in task.results)
        all_failed = all(r.status == UploadStatus.FAILED for r in task.results)

        if all_success:
            task.status = "completed"
        elif all_failed:
            task.status = "failed"
        else:
            task.status = "partial"  # 部分成功

        task.completed_at = datetime.utcnow().isoformat()

        logger.info(f"Upload task completed: {task_id}, status: {task.status}")
        return task

    async def _upload_to_single_platform(
        self,
        platform: Platform,
        video_path: str,
        metadata: VideoMetadata
    ) -> UploadResult:
        """上传到单个平台"""
        try:
            uploader = self.uploaders.get(platform)
            if not uploader:
                return UploadResult(
                    platform=platform,
                    status=UploadStatus.FAILED,
                    error="Platform uploader not found"
                )

            logger.info(f"Starting upload to {platform.value}")
            result = await uploader.upload_video(video_path, metadata)

            return result

        except Exception as e:
            logger.error(f"Upload to {platform.value} failed: {e}")
            return UploadResult(
                platform=platform,
                status=UploadStatus.FAILED,
                error=str(e)
            )

    async def retry_failed_uploads(
        self,
        task_id: str,
        on_progress: Optional[Callable[[UploadTask], None]] = None
    ) -> UploadTask:
        """重试失败的上传"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # 找出失败的平台
        failed_platforms = [
            result.platform
            for result in task.results
            if result.status == UploadStatus.FAILED
        ]

        if not failed_platforms:
            logger.info("No failed uploads to retry")
            return task

        # 重试上传
        logger.info(f"Retrying failed uploads for platforms: {failed_platforms}")

        retry_coroutines = [
            self._upload_to_single_platform(
                platform,
                task.video_path,
                task.metadata
            )
            for platform in failed_platforms
        ]

        retry_results = await asyncio.gather(*retry_coroutines, return_exceptions=True)

        # 更新结果
        for i, result in enumerate(retry_results):
            if isinstance(result, Exception):
                logger.error(f"Retry exception: {result}")
                continue

            # 更新对应平台的结果
            platform = failed_platforms[i]
            for j, old_result in enumerate(task.results):
                if old_result.platform == platform:
                    task.results[j] = result
                    break

            # 触发进度回调
            if on_progress:
                on_progress(task)

        # 更新任务状态
        all_success = all(r.status == UploadStatus.SUCCESS for r in task.results)
        task.status = "completed" if all_success else "partial"

        return task

    def get_task(self, task_id: str) -> Optional[UploadTask]:
        """获取任务信息"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[UploadTask]:
        """获取所有任务"""
        return list(self.tasks.values())

    async def delete_video_from_platforms(
        self,
        video_id: str,
        platforms: List[Platform]
    ) -> Dict[Platform, bool]:
        """从多个平台删除视频"""
        results = {}

        delete_coroutines = []
        for platform in platforms:
            uploader = self.uploaders.get(platform)
            if uploader:
                delete_coroutines.append(uploader.delete_video(video_id))
            else:
                results[platform] = False

        delete_results = await asyncio.gather(*delete_coroutines, return_exceptions=True)

        for i, result in enumerate(delete_results):
            platform = platforms[i]
            if isinstance(result, Exception):
                results[platform] = False
            else:
                results[platform] = result

        return results

    def get_platform_stats(self) -> Dict[str, Any]:
        """获取平台统计信息"""
        stats = {
            'total_tasks': len(self.tasks),
            'configured_platforms': len(self.configs),
            'platform_results': {}
        }

        # 统计各平台的上传情况
        for platform in Platform:
            platform_results = [
                result
                for task in self.tasks.values()
                for result in task.results
                if result.platform == platform
            ]

            if platform_results:
                stats['platform_results'][platform.value] = {
                    'total': len(platform_results),
                    'success': sum(1 for r in platform_results if r.status == UploadStatus.SUCCESS),
                    'failed': sum(1 for r in platform_results if r.status == UploadStatus.FAILED),
                    'processing': sum(1 for r in platform_results if r.status == UploadStatus.PROCESSING)
                }

        return stats

# 全局单例
upload_manager = UploadManager()
