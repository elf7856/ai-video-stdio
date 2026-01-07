import httpx
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class PexelsClient:
    """Pexels API Client for fetching stock media"""
    
    BASE_URL = "https://api.pexels.com/v1"
    VIDEO_BASE_URL = "https://api.pexels.com/videos"
    
    def __init__(self):
        self.api_key = settings.pexels_api_key
        if not self.api_key:
            logger.warning("PEXELS_API_KEY not set. Pexels integration will not work.")

    async def search_photos(self, query: str, per_page: int = 15) -> List[Dict[str, Any]]:
        """Search for photos"""
        if not self.api_key:
            return []
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    headers={"Authorization": self.api_key},
                    params={"query": query, "per_page": per_page}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("photos", [])
            except Exception as e:
                logger.error(f"Pexels search photos failed: {e}")
                return []

    async def get_curated_photos(self, per_page: int = 15) -> List[Dict[str, Any]]:
        """Get curated (trending) photos"""
        if not self.api_key:
            return []
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/curated",
                    headers={"Authorization": self.api_key},
                    params={"per_page": per_page}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("photos", [])
            except Exception as e:
                logger.error(f"Pexels curated photos failed: {e}")
                return []

    async def search_videos(self, query: str, per_page: int = 15) -> List[Dict[str, Any]]:
        """Search for videos"""
        if not self.api_key:
            return []
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.VIDEO_BASE_URL}/search",
                    headers={"Authorization": self.api_key},
                    params={"query": query, "per_page": per_page}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("videos", [])
            except Exception as e:
                logger.error(f"Pexels search videos failed: {e}")
                return []
