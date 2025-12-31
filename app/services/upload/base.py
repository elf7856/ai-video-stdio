"""
多平台上传基础类
支持视频一键分发到各大平台
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum

class UploadStatus(str, Enum):
    """上传状态"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"  # 平台处理中
    SUCCESS = "success"
    FAILED = "failed"

class Platform(str, Enum):
    """支持的平台"""
    YOUTUBE = "youtube"
    BILIBILI = "bilibili"
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    XIAOHONGSHU = "xiaohongshu"
    WECHAT_CHANNELS = "wechat_channels"
    WEIBO = "weibo"

class VideoMetadata(BaseModel):
    """视频元数据"""
    title: str
    description: str
    tags: List[str] = []
    category: Optional[str] = None
    thumbnail_path: Optional[str] = None
    privacy: str = "public"  # public, private, unlisted
    language: str = "zh-CN"

    # 平台特定字段
    cover_image: Optional[str] = None  # 封面图（抖音、B站等）
    topic: Optional[str] = None  # 话题标签（抖音、小红书）
    allow_comment: bool = True
    allow_download: bool = True
    allow_duet: bool = True  # 允许合拍（抖音）

class UploadResult(BaseModel):
    """上传结果"""
    platform: Platform
    status: UploadStatus
    video_id: Optional[str] = None  # 平台返回的视频ID
    video_url: Optional[str] = None  # 视频链接
    error: Optional[str] = None
    uploaded_at: Optional[str] = None

class PlatformConfig(BaseModel):
    """平台配置"""
    platform: Platform
    enabled: bool = True

    # 认证信息（根据平台不同而不同）
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

    # OAuth配置
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    # Cookie/Session（用于自动化上传）
    cookies: Optional[Dict[str, str]] = None
    session_data: Optional[Dict[str, Any]] = None

class PlatformUploader(ABC):
    """平台上传器基类"""

    def __init__(self, config: PlatformConfig):
        self.config = config
        self.platform = config.platform

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        认证/验证登录状态
        Returns:
            bool: 认证是否成功
        """
        pass

    @abstractmethod
    async def upload_video(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> UploadResult:
        """
        上传视频
        Args:
            video_path: 视频文件路径
            metadata: 视频元数据
        Returns:
            UploadResult: 上传结果
        """
        pass

    @abstractmethod
    async def check_upload_status(self, video_id: str) -> UploadStatus:
        """
        检查上传状态
        Args:
            video_id: 视频ID
        Returns:
            UploadStatus: 上传状态
        """
        pass

    @abstractmethod
    async def delete_video(self, video_id: str) -> bool:
        """
        删除视频
        Args:
            video_id: 视频ID
        Returns:
            bool: 是否删除成功
        """
        pass

    async def validate_metadata(self, metadata: VideoMetadata) -> bool:
        """
        验证元数据是否符合平台要求
        Args:
            metadata: 视频元数据
        Returns:
            bool: 是否有效
        """
        # 子类可以重写此方法添加平台特定验证
        if not metadata.title or len(metadata.title.strip()) == 0:
            return False
        return True

    def get_platform_name(self) -> str:
        """获取平台中文名称"""
        platform_names = {
            Platform.YOUTUBE: "YouTube",
            Platform.BILIBILI: "哔哩哔哩",
            Platform.DOUYIN: "抖音",
            Platform.KUAISHOU: "快手",
            Platform.XIAOHONGSHU: "小红书",
            Platform.WECHAT_CHANNELS: "微信视频号",
            Platform.WEIBO: "微博"
        }
        return platform_names.get(self.platform, str(self.platform))
