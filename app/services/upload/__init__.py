"""
多平台上传服务模块
"""

from .base import (
    Platform,
    PlatformConfig,
    PlatformUploader,
    VideoMetadata,
    UploadResult,
    UploadStatus
)
from .manager import upload_manager, UploadManager, UploadTask
from .youtube_uploader import YouTubeUploader
from .bilibili_uploader import BilibiliUploader
from .douyin_uploader import DouyinUploader

__all__ = [
    # Base classes
    'Platform',
    'PlatformConfig',
    'PlatformUploader',
    'VideoMetadata',
    'UploadResult',
    'UploadStatus',

    # Manager
    'upload_manager',
    'UploadManager',
    'UploadTask',

    # Platform uploaders
    'YouTubeUploader',
    'BilibiliUploader',
    'DouyinUploader',
]
