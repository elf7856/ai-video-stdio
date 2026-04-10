"""
Shutterstock API Client
支持视频和图片搜索
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class ShutterstockClient:
    """Shutterstock API Client for fetching stock media"""

    BASE_URL = "https://api.shutterstock.com/v2"

    def __init__(self):
        self.api_key = getattr(settings, 'shutterstock_api_key', None)
        self.api_secret = getattr(settings, 'shutterstock_api_secret', None)

        if not self.api_key or not self.api_secret:
            logger.warning("SHUTTERSTOCK_API_KEY or SHUTTERSTOCK_API_SECRET not set. Shutterstock integration will not work.")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头（使用 Basic Auth）"""
        import base64
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

    async def search_videos(
        self,
        query: str,
        per_page: int = 15,
        orientation: str = None,  # "horizontal", "vertical"
        resolution: str = None  # "4k", "1080p", "720p"
    ) -> List[Dict[str, Any]]:
        """
        搜索视频

        Args:
            query: 搜索关键词
            per_page: 每页结果数
            orientation: 视频方向 - "horizontal" (横屏), "vertical" (竖屏)
            resolution: 分辨率 - "4k", "1080p", "720p"

        Returns:
            视频列表
        """
        if not self.api_key or not self.api_secret:
            return []

        # 构建参数
        params = {
            "query": query,
            "per_page": min(per_page, 50),  # Shutterstock 最大 50
            "sort": "popular"  # 按热度排序
        }

        # 添加方向筛选
        if orientation:
            # 映射到 Shutterstock 的方向参数
            orientation_map = {
                "landscape": "horizontal",
                "portrait": "vertical",
                "horizontal": "horizontal",
                "vertical": "vertical"
            }
            mapped_orientation = orientation_map.get(orientation.lower())
            if mapped_orientation:
                params["aspect_ratio"] = mapped_orientation

        # 添加分辨率筛选
        if resolution:
            resolution_map = {
                "large": "4k",
                "medium": "1080p",
                "small": "720p"
            }
            mapped_resolution = resolution_map.get(resolution, resolution)
            params["resolution"] = mapped_resolution

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/videos/search",
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                videos = data.get("data", [])
                if videos:
                    logger.info(
                        f"Shutterstock: Found {len(videos)} videos for '{query}' "
                        f"(orientation={orientation}, resolution={resolution})"
                    )

                return videos

            except httpx.HTTPStatusError as e:
                logger.error(f"Shutterstock API error: {e.response.status_code} - {e.response.text}")
                return []
            except Exception as e:
                logger.error(f"Shutterstock search videos failed: {e}")
                return []

    async def search_images(
        self,
        query: str,
        per_page: int = 15,
        orientation: str = None,  # "horizontal", "vertical"
        image_type: str = "photo"  # "photo", "illustration", "vector"
    ) -> List[Dict[str, Any]]:
        """
        搜索图片

        Args:
            query: 搜索关键词
            per_page: 每页结果数
            orientation: 图片方向 - "horizontal" (横向), "vertical" (纵向)
            image_type: 图片类型 - "photo" (照片), "illustration" (插画), "vector" (矢量图)

        Returns:
            图片列表
        """
        if not self.api_key or not self.api_secret:
            return []

        # 构建参数
        params = {
            "query": query,
            "per_page": min(per_page, 50),
            "sort": "popular",
            "image_type": image_type
        }

        # 添加方向筛选
        if orientation:
            orientation_map = {
                "landscape": "horizontal",
                "portrait": "vertical",
                "horizontal": "horizontal",
                "vertical": "vertical"
            }
            mapped_orientation = orientation_map.get(orientation.lower())
            if mapped_orientation:
                params["orientation"] = mapped_orientation

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/images/search",
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                images = data.get("data", [])
                if images:
                    logger.info(
                        f"Shutterstock: Found {len(images)} images for '{query}' "
                        f"(orientation={orientation}, type={image_type})"
                    )

                return images

            except httpx.HTTPStatusError as e:
                logger.error(f"Shutterstock API error: {e.response.status_code} - {e.response.text}")
                return []
            except Exception as e:
                logger.error(f"Shutterstock search images failed: {e}")
                return []

    async def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """获取视频详情"""
        if not self.api_key or not self.api_secret:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/videos/{video_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

            except Exception as e:
                logger.error(f"Shutterstock get video details failed: {e}")
                return None

    async def get_image_details(self, image_id: str) -> Optional[Dict[str, Any]]:
        """获取图片详情"""
        if not self.api_key or not self.api_secret:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/images/{image_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

            except Exception as e:
                logger.error(f"Shutterstock get image details failed: {e}")
                return None


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        client = ShutterstockClient()

        # 测试视频搜索
        print("\n=== 测试视频搜索 ===")
        videos = await client.search_videos(
            query="sunset beach",
            per_page=5,
            orientation="horizontal",
            resolution="1080p"
        )
        print(f"找到 {len(videos)} 个视频")
        if videos:
            print(f"第一个视频: {videos[0].get('description', 'N/A')}")

        # 测试图片搜索
        print("\n=== 测试图片搜索 ===")
        images = await client.search_images(
            query="mountain landscape",
            per_page=5,
            orientation="horizontal"
        )
        print(f"找到 {len(images)} 张图片")
        if images:
            print(f"第一张图片: {images[0].get('description', 'N/A')}")

    asyncio.run(test())
