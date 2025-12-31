"""
B站(哔哩哔哩)上传器
使用B站开放平台API
"""
import os
import json
import logging
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

from .base import (
    PlatformUploader,
    PlatformConfig,
    VideoMetadata,
    UploadResult,
    UploadStatus,
    Platform
)

logger = logging.getLogger(__name__)

class BilibiliUploader(PlatformUploader):
    """B站上传器"""

    # B站API端点
    BASE_URL = "https://member.bilibili.com/x"
    UPLOAD_URL = "https://up.bilibili.com"

    # B站分区ID映射
    CATEGORIES = {
        'douga': 1,      # 动画
        'game': 4,       # 游戏
        'music': 3,      # 音乐
        'dance': 129,    # 舞蹈
        'entertainment': 5,  # 娱乐
        'tech': 188,     # 科技
        'life': 160,     # 生活
        'kichiku': 119,  # 鬼畜
        'fashion': 155,  # 时尚
        'information': 202,  # 资讯
        'ent': 71,       # 影视
        'movie': 181,    # 影视
        'documentary': 177,  # 纪录片
        'car': 223,      # 汽车
        'food': 211,     # 美食
        'animal': 217,   # 动物圈
        'knowledge': 36,  # 知识
        'sports': 234,   # 运动
    }

    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(timeout=300.0)
        self.session_data = config.session_data or {}

    async def authenticate(self) -> bool:
        """验证登录状态"""
        try:
            # B站使用Cookie认证
            if not self.config.cookies:
                logger.error("Bilibili cookies not found")
                return False

            # 验证Cookie有效性
            headers = {
                'Cookie': self._format_cookies(self.config.cookies),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = await self.client.get(
                f"{self.BASE_URL}/web/archive/user/index",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    logger.info("Bilibili authentication successful")
                    return True

            logger.error("Bilibili authentication failed")
            return False

        except Exception as e:
            logger.error(f"Bilibili authentication error: {e}")
            return False

    async def upload_video(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> UploadResult:
        """上传视频到B站"""
        result = UploadResult(
            platform=Platform.BILIBILI,
            status=UploadStatus.PENDING
        )

        try:
            # 验证认证
            if not await self.authenticate():
                result.status = UploadStatus.FAILED
                result.error = "Authentication failed"
                return result

            # 验证元数据
            if not await self.validate_metadata(metadata):
                result.status = UploadStatus.FAILED
                result.error = "Invalid metadata"
                return result

            # 验证文件
            if not os.path.exists(video_path):
                result.status = UploadStatus.FAILED
                result.error = f"Video file not found: {video_path}"
                return result

            logger.info(f"Uploading video to Bilibili: {metadata.title}")
            result.status = UploadStatus.UPLOADING

            # 步骤1: 预上传，获取上传参数
            upload_params = await self._pre_upload(video_path)
            if not upload_params:
                result.status = UploadStatus.FAILED
                result.error = "Failed to get upload parameters"
                return result

            # 步骤2: 分片上传视频文件
            upload_result = await self._upload_chunks(video_path, upload_params)
            if not upload_result:
                result.status = UploadStatus.FAILED
                result.error = "Failed to upload video chunks"
                return result

            # 步骤3: 提交视频信息
            video_id = await self._submit_video(
                upload_result,
                metadata,
                upload_params
            )

            if not video_id:
                result.status = UploadStatus.FAILED
                result.error = "Failed to submit video info"
                return result

            # 上传成功
            result.status = UploadStatus.SUCCESS
            result.video_id = video_id
            result.video_url = f"https://www.bilibili.com/video/{video_id}"
            result.uploaded_at = datetime.utcnow().isoformat()

            logger.info(f"Video uploaded successfully: {result.video_url}")
            return result

        except Exception as e:
            logger.error(f"Bilibili upload failed: {e}")
            result.status = UploadStatus.FAILED
            result.error = str(e)
            return result

    async def _pre_upload(self, video_path: str) -> Optional[Dict[str, Any]]:
        """预上传，获取上传参数"""
        try:
            file_size = os.path.getsize(video_path)
            file_name = os.path.basename(video_path)

            headers = {
                'Cookie': self._format_cookies(self.config.cookies),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # 请求预上传
            data = {
                'name': file_name,
                'size': file_size,
                'r': 'upos',
                'profile': 'ugcupos/bup',
                'ssl': '0',
                'version': '2.10.4',
                'build': '2100400'
            }

            response = await self.client.get(
                f"{self.UPLOAD_URL}/x/vu/web/add",
                params=data,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('OK') == 1:
                    return result

            logger.error(f"Pre-upload failed: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Pre-upload error: {e}")
            return None

    async def _upload_chunks(
        self,
        video_path: str,
        upload_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """分片上传视频"""
        try:
            chunk_size = 4 * 1024 * 1024  # 4MB per chunk
            file_size = os.path.getsize(video_path)

            upload_url = upload_params.get('url')
            if not upload_url:
                logger.error("Upload URL not found in parameters")
                return None

            # 分片上传
            with open(video_path, 'rb') as f:
                chunk_num = 0
                uploaded_parts = []

                while True:
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break

                    # 上传分片
                    headers = {
                        'Content-Type': 'application/octet-stream',
                        'Content-Length': str(len(chunk_data))
                    }

                    response = await self.client.put(
                        f"{upload_url}?partNumber={chunk_num}&uploadId={upload_params.get('upload_id')}",
                        content=chunk_data,
                        headers=headers
                    )

                    if response.status_code != 200:
                        logger.error(f"Failed to upload chunk {chunk_num}")
                        return None

                    uploaded_parts.append({
                        'partNumber': chunk_num,
                        'eTag': response.headers.get('ETag')
                    })

                    chunk_num += 1
                    progress = int((f.tell() / file_size) * 100)
                    logger.info(f"Upload progress: {progress}%")

            return {
                'upload_id': upload_params.get('upload_id'),
                'parts': uploaded_parts,
                'filename': upload_params.get('filename')
            }

        except Exception as e:
            logger.error(f"Chunk upload error: {e}")
            return None

    async def _submit_video(
        self,
        upload_result: Dict[str, Any],
        metadata: VideoMetadata,
        upload_params: Dict[str, Any]
    ) -> Optional[str]:
        """提交视频信息"""
        try:
            headers = {
                'Cookie': self._format_cookies(self.config.cookies),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }

            # 构建投稿信息
            submit_data = {
                'copyright': 1,  # 1=自制 2=转载
                'videos': [{
                    'filename': upload_result['filename'],
                    'title': metadata.title[:80],  # B站限制80字符
                    'desc': ''
                }],
                'source': '',
                'tid': self._get_category_id(metadata.category),
                'cover': metadata.cover_image or '',
                'title': metadata.title[:80],
                'desc_format_id': 0,
                'desc': metadata.description[:250],  # B站限制250字符
                'dynamic': '',  # 动态
                'tag': ','.join(metadata.tags[:12]),  # 最多12个标签
                'open_elec': 1 if metadata.allow_comment else 0,
            }

            response = await self.client.post(
                f"{self.BASE_URL}/web/archive/add",
                json=submit_data,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    bvid = result.get('data', {}).get('bvid')
                    return bvid

            logger.error(f"Submit failed: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Submit error: {e}")
            return None

    async def check_upload_status(self, video_id: str) -> UploadStatus:
        """检查视频状态"""
        try:
            headers = {
                'Cookie': self._format_cookies(self.config.cookies),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = await self.client.get(
                f"{self.BASE_URL}/web/archive/view",
                params={'bvid': video_id},
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    state = data.get('data', {}).get('state')
                    # B站状态: 0=审核中 1=已过审 -1=未过审
                    if state == 1:
                        return UploadStatus.SUCCESS
                    elif state == 0:
                        return UploadStatus.PROCESSING
                    else:
                        return UploadStatus.FAILED

            return UploadStatus.FAILED

        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            return UploadStatus.FAILED

    async def delete_video(self, video_id: str) -> bool:
        """删除视频"""
        try:
            headers = {
                'Cookie': self._format_cookies(self.config.cookies),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = await self.client.post(
                f"{self.BASE_URL}/web/archive/delete",
                json={'bvid': video_id},
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"Video deleted: {video_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete video: {e}")
            return False

    def _get_category_id(self, category: Optional[str]) -> int:
        """获取B站分区ID"""
        if category and category.lower() in self.CATEGORIES:
            return self.CATEGORIES[category.lower()]
        # 默认返回"生活"分区
        return 160

    def _format_cookies(self, cookies: Dict[str, str]) -> str:
        """格式化Cookie字符串"""
        return '; '.join([f"{k}={v}" for k, v in cookies.items()])

    async def validate_metadata(self, metadata: VideoMetadata) -> bool:
        """验证元数据"""
        if not await super().validate_metadata(metadata):
            return False

        # B站特定验证
        if len(metadata.title) > 80:
            logger.warning("Title too long for Bilibili, will be truncated")

        if len(metadata.description) > 250:
            logger.warning("Description too long for Bilibili, will be truncated")

        if len(metadata.tags) > 12:
            logger.warning("Too many tags for Bilibili, will be limited to 12")

        return True
