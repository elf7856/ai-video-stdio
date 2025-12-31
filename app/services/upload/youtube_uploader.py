"""
YouTube上传器
使用YouTube Data API v3
"""
import os
import logging
from typing import Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from .base import (
    PlatformUploader,
    PlatformConfig,
    VideoMetadata,
    UploadResult,
    UploadStatus,
    Platform
)

logger = logging.getLogger(__name__)

class YouTubeUploader(PlatformUploader):
    """YouTube上传器"""

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.youtube = None
        self.credentials = None

    async def authenticate(self) -> bool:
        """使用OAuth 2.0认证"""
        try:
            # 尝试从配置中加载凭证
            if self.config.access_token and self.config.refresh_token:
                self.credentials = Credentials(
                    token=self.config.access_token,
                    refresh_token=self.config.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.config.client_id,
                    client_secret=self.config.client_secret,
                    scopes=self.SCOPES
                )

                # 刷新过期的token
                if self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())

            # 如果没有有效凭证，需要重新授权
            if not self.credentials or not self.credentials.valid:
                logger.warning("YouTube credentials invalid or missing. Manual authorization required.")
                return False

            # 构建YouTube服务
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            return True

        except Exception as e:
            logger.error(f"YouTube authentication failed: {e}")
            return False

    async def upload_video(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> UploadResult:
        """上传视频到YouTube"""
        result = UploadResult(
            platform=Platform.YOUTUBE,
            status=UploadStatus.PENDING
        )

        try:
            # 验证认证状态
            if not self.youtube:
                if not await self.authenticate():
                    result.status = UploadStatus.FAILED
                    result.error = "Authentication failed"
                    return result

            # 验证元数据
            if not await self.validate_metadata(metadata):
                result.status = UploadStatus.FAILED
                result.error = "Invalid metadata"
                return result

            # 验证文件存在
            if not os.path.exists(video_path):
                result.status = UploadStatus.FAILED
                result.error = f"Video file not found: {video_path}"
                return result

            # 构建请求体
            body = {
                'snippet': {
                    'title': metadata.title[:100],  # YouTube限制100字符
                    'description': metadata.description[:5000],  # 限制5000字符
                    'tags': metadata.tags[:500],  # 最多500个标签
                    'categoryId': self._get_category_id(metadata.category),
                    'defaultLanguage': metadata.language,
                },
                'status': {
                    'privacyStatus': metadata.privacy,  # public, private, unlisted
                    'selfDeclaredMadeForKids': False,
                }
            }

            # 创建媒体上传对象
            media = MediaFileUpload(
                video_path,
                mimetype='video/*',
                resumable=True,
                chunksize=10 * 1024 * 1024  # 10MB chunks
            )

            # 执行上传
            logger.info(f"Uploading video to YouTube: {metadata.title}")
            result.status = UploadStatus.UPLOADING

            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")

            # 上传成功
            video_id = response.get('id')
            result.status = UploadStatus.SUCCESS
            result.video_id = video_id
            result.video_url = f"https://www.youtube.com/watch?v={video_id}"
            result.uploaded_at = datetime.utcnow().isoformat()

            logger.info(f"Video uploaded successfully: {result.video_url}")

            # 如果有缩略图，上传缩略图
            if metadata.thumbnail_path and os.path.exists(metadata.thumbnail_path):
                await self._upload_thumbnail(video_id, metadata.thumbnail_path)

            return result

        except HttpError as e:
            logger.error(f"YouTube upload failed: {e}")
            result.status = UploadStatus.FAILED
            result.error = str(e)
            return result

        except Exception as e:
            logger.error(f"Unexpected error during YouTube upload: {e}")
            result.status = UploadStatus.FAILED
            result.error = str(e)
            return result

    async def _upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """上传自定义缩略图"""
        try:
            media = MediaFileUpload(thumbnail_path, mimetype='image/*')
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            logger.info(f"Thumbnail uploaded for video: {video_id}")
        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")

    async def check_upload_status(self, video_id: str) -> UploadStatus:
        """检查视频状态"""
        try:
            if not self.youtube:
                if not await self.authenticate():
                    return UploadStatus.FAILED

            response = self.youtube.videos().list(
                part='status,processingDetails',
                id=video_id
            ).execute()

            if not response.get('items'):
                return UploadStatus.FAILED

            video = response['items'][0]
            upload_status = video['status']['uploadStatus']

            # YouTube状态映射
            status_map = {
                'uploaded': UploadStatus.PROCESSING,
                'processed': UploadStatus.SUCCESS,
                'failed': UploadStatus.FAILED,
                'rejected': UploadStatus.FAILED,
                'deleted': UploadStatus.FAILED
            }

            return status_map.get(upload_status, UploadStatus.PROCESSING)

        except Exception as e:
            logger.error(f"Failed to check video status: {e}")
            return UploadStatus.FAILED

    async def delete_video(self, video_id: str) -> bool:
        """删除视频"""
        try:
            if not self.youtube:
                if not await self.authenticate():
                    return False

            self.youtube.videos().delete(id=video_id).execute()
            logger.info(f"Video deleted: {video_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete video: {e}")
            return False

    def _get_category_id(self, category: Optional[str]) -> str:
        """获取YouTube分类ID"""
        # YouTube分类ID映射
        categories = {
            'film': '1',
            'autos': '2',
            'music': '10',
            'pets': '15',
            'sports': '17',
            'travel': '19',
            'gaming': '20',
            'people': '22',
            'comedy': '23',
            'entertainment': '24',
            'news': '25',
            'howto': '26',
            'education': '27',
            'science': '28',
            'nonprofits': '29'
        }

        if category and category.lower() in categories:
            return categories[category.lower()]

        # 默认返回"教育"分类
        return '27'

    async def validate_metadata(self, metadata: VideoMetadata) -> bool:
        """验证元数据"""
        if not await super().validate_metadata(metadata):
            return False

        # YouTube特定验证
        if len(metadata.title) > 100:
            logger.warning(f"Title too long, will be truncated: {metadata.title}")

        if len(metadata.description) > 5000:
            logger.warning(f"Description too long, will be truncated")

        if len(metadata.tags) > 500:
            logger.warning(f"Too many tags, will be limited to 500")

        return True
