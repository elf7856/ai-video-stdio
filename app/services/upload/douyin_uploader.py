"""
抖音上传器
使用Playwright进行Web自动化上传
"""
import os
import logging
import asyncio
from typing import Optional
from datetime import datetime

from .base import (
    PlatformUploader,
    PlatformConfig,
    VideoMetadata,
    UploadResult,
    UploadStatus,
    Platform
)

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Douyin uploader will not work.")

class DouyinUploader(PlatformUploader):
    """抖音上传器 - 使用Web自动化"""

    UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"

    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def authenticate(self) -> bool:
        """验证登录状态"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not installed")
            return False

        try:
            # 启动浏览器
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=False)

            # 创建上下文并加载Cookie
            context = await self.browser.new_context()

            if self.config.cookies:
                cookies = [
                    {'name': k, 'value': v, 'domain': '.douyin.com', 'path': '/'}
                    for k, v in self.config.cookies.items()
                ]
                await context.add_cookies(cookies)

            self.page = await context.new_page()

            # 访问创作者平台验证登录状态
            await self.page.goto('https://creator.douyin.com')
            await asyncio.sleep(2)

            # 检查是否需要登录
            if 'login' in self.page.url.lower():
                logger.error("Not logged in to Douyin")
                return False

            logger.info("Douyin authentication successful")
            return True

        except Exception as e:
            logger.error(f"Douyin authentication error: {e}")
            return False

    async def upload_video(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> UploadResult:
        """上传视频到抖音"""
        result = UploadResult(
            platform=Platform.DOUYIN,
            status=UploadStatus.PENDING
        )

        try:
            # 验证认证
            if not self.page:
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

            logger.info(f"Uploading video to Douyin: {metadata.title}")
            result.status = UploadStatus.UPLOADING

            # 访问上传页面
            await self.page.goto(self.UPLOAD_URL)
            await asyncio.sleep(2)

            # 上传视频文件
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
                logger.info("Video file selected")
            else:
                result.status = UploadStatus.FAILED
                result.error = "Upload input not found"
                return result

            # 等待视频上传完成
            await self._wait_for_upload_complete()

            # 填写视频信息
            await self._fill_video_info(metadata)

            # 发布视频
            publish_button = await self.page.query_selector('button:has-text("发布")')
            if publish_button:
                await publish_button.click()
                await asyncio.sleep(3)

                # 获取视频链接
                video_url = await self._get_video_url()

                result.status = UploadStatus.SUCCESS
                result.video_url = video_url
                result.uploaded_at = datetime.utcnow().isoformat()

                logger.info(f"Video uploaded successfully: {video_url}")
            else:
                result.status = UploadStatus.FAILED
                result.error = "Publish button not found"

            return result

        except Exception as e:
            logger.error(f"Douyin upload failed: {e}")
            result.status = UploadStatus.FAILED
            result.error = str(e)
            return result

        finally:
            # 清理浏览器资源
            if self.browser:
                await self.browser.close()

    async def _wait_for_upload_complete(self, timeout: int = 600):
        """等待视频上传完成"""
        try:
            # 等待上传进度条消失或完成提示出现
            await self.page.wait_for_selector(
                'text="上传完成"',
                timeout=timeout * 1000
            )
            logger.info("Video upload completed")
        except Exception as e:
            logger.warning(f"Upload wait timeout or error: {e}")

    async def _fill_video_info(self, metadata: VideoMetadata):
        """填写视频信息"""
        try:
            # 标题
            title_input = await self.page.query_selector('textarea[placeholder*="标题"]')
            if title_input:
                await title_input.fill(metadata.title[:55])  # 抖音标题限制55字符

            # 描述
            desc_input = await self.page.query_selector('textarea[placeholder*="描述"]')
            if desc_input:
                await desc_input.fill(metadata.description[:2000])

            # 话题标签
            if metadata.topic:
                topic_input = await self.page.query_selector('input[placeholder*="话题"]')
                if topic_input:
                    await topic_input.fill(metadata.topic)
                    await asyncio.sleep(1)
                    # 选择第一个推荐话题
                    first_topic = await self.page.query_selector('.topic-item:first-child')
                    if first_topic:
                        await first_topic.click()

            # 封面图（如果提供）
            if metadata.cover_image and os.path.exists(metadata.cover_image):
                cover_input = await self.page.query_selector('input[type="file"][accept*="image"]')
                if cover_input:
                    await cover_input.set_input_files(metadata.cover_image)

            # 允许合拍
            if not metadata.allow_duet:
                duet_switch = await self.page.query_selector('text="允许合拍"')
                if duet_switch:
                    await duet_switch.click()

            # 允许评论
            if not metadata.allow_comment:
                comment_switch = await self.page.query_selector('text="允许评论"')
                if comment_switch:
                    await comment_switch.click()

            logger.info("Video info filled")

        except Exception as e:
            logger.error(f"Failed to fill video info: {e}")

    async def _get_video_url(self) -> Optional[str]:
        """获取发布后的视频URL"""
        try:
            # 等待成功提示
            await self.page.wait_for_selector('text="发布成功"', timeout=10000)

            # 尝试获取视频链接
            link_element = await self.page.query_selector('a[href*="douyin.com/video"]')
            if link_element:
                video_url = await link_element.get_attribute('href')
                return video_url

            return None

        except Exception as e:
            logger.error(f"Failed to get video URL: {e}")
            return None

    async def check_upload_status(self, video_id: str) -> UploadStatus:
        """检查视频状态"""
        # 抖音上传是同步的，发布后立即成功
        return UploadStatus.SUCCESS

    async def delete_video(self, video_id: str) -> bool:
        """删除视频"""
        # 需要实现Web自动化删除
        logger.warning("Delete video not implemented for Douyin")
        return False

    async def validate_metadata(self, metadata: VideoMetadata) -> bool:
        """验证元数据"""
        if not await super().validate_metadata(metadata):
            return False

        # 抖音特定验证
        if len(metadata.title) > 55:
            logger.warning("Title too long for Douyin, will be truncated to 55 chars")

        if len(metadata.description) > 2000:
            logger.warning("Description too long for Douyin, will be truncated")

        return True
