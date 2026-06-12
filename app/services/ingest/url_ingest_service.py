"""
URL ingest service.

Turns a user-provided URL into normalized source material that can be shown in
the producer panel and injected into the video generation brief.
"""

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.services.web.content_extractor import WebContentExtractor

logger = logging.getLogger(__name__)


class UrlIngestService:
    """Normalize webpage, image, and video URLs into source material."""

    URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    VIDEO_PLATFORMS = (
        "youtube.com",
        "youtu.be",
        "bilibili.com",
        "b23.tv",
        "tiktok.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "douyin.com",
        "kuaishou.com",
    )
    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or settings.output_dir) / "ingest"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.web_extractor = WebContentExtractor()

    def extract_urls(self, text: str) -> List[str]:
        """Extract and lightly sanitize URLs from natural language input."""
        urls = []
        for match in self.URL_PATTERN.findall(text or ""):
            cleaned = match.rstrip(").,;!?，。；！？")
            if cleaned not in urls:
                urls.append(cleaned)
        return urls

    def strip_urls(self, text: str, urls: List[str]) -> str:
        """Return the user text with URL tokens removed."""
        cleaned = text or ""
        for url in urls:
            cleaned = cleaned.replace(url, " ")
        return re.sub(r"\s+", " ", cleaned).strip()

    def classify_url(self, url: str) -> str:
        """Classify a URL as video, image, or webpage."""
        url_lower = url.lower()
        if any(platform in url_lower for platform in self.VIDEO_PLATFORMS):
            return "video"

        parsed = urlparse(url_lower)
        if parsed.path.endswith(self.IMAGE_EXTENSIONS):
            return "image"

        return "webpage"

    async def ingest(self, url: str) -> Dict[str, Any]:
        """Fetch source metadata and persist a lightweight ingest record."""
        source_type = self.classify_url(url)
        source_id = f"src_{uuid.uuid4().hex[:12]}"
        domain = urlparse(url).netloc

        material: Dict[str, Any] = {
            "sourceId": source_id,
            "type": source_type,
            "url": url,
            "domain": domain,
            "title": domain or url,
            "summary": "",
            "images": [],
            "rawContent": "",
            "metadata": {},
            "status": "ready",
            "error": None,
        }

        try:
            if source_type == "webpage":
                material.update(await self._ingest_webpage(url))
            elif source_type == "image":
                material.update(self._ingest_image(url))
            elif source_type == "video":
                material.update(self._ingest_video(url))
        except Exception as e:
            logger.warning(f"URL ingest failed for {url}: {e}")
            material["status"] = "failed"
            material["error"] = str(e)

        self._persist(material)
        return material

    async def _ingest_webpage(self, url: str) -> Dict[str, Any]:
        content = await self.web_extractor.extract_content_from_url(url, max_images=8)
        if not content:
            return {
                "status": "failed",
                "error": "网页内容拉取失败",
            }

        summary = content.get("description") or self._summarize_text(content.get("main_content", ""))
        title = content.get("title") or urlparse(url).netloc or url

        return {
            "title": title,
            "summary": summary,
            "images": content.get("images", []),
            "rawContent": content.get("main_content", ""),
            "metadata": {
                "ogData": content.get("og_data", {}),
                "productInfo": content.get("product_info", {}),
            },
        }

    def _ingest_image(self, url: str) -> Dict[str, Any]:
        filename = Path(urlparse(url).path).name or "image"
        return {
            "title": filename,
            "summary": "用户提供了一张参考图片，可用于画面风格、主体或构图参考。",
            "images": [{"url": url, "alt": filename}],
            "metadata": {"imageUrl": url},
        }

    def _ingest_video(self, url: str) -> Dict[str, Any]:
        platform = self._video_platform(url)
        return {
            "title": f"{platform} video" if platform else "Video source",
            "summary": "用户提供了一个视频链接。生成任务启动后会在后台下载视频、提取转写和关键帧，并把摘要与风格结构用于二创生成。",
            "metadata": {
                "platform": platform,
                "requiresDeepRecreation": True,
                "analysisStatus": "pending",
            },
        }

    def _video_platform(self, url: str) -> str:
        url_lower = url.lower()
        for platform in self.VIDEO_PLATFORMS:
            if platform in url_lower:
                return platform
        return "general"

    def _summarize_text(self, text: str, limit: int = 360) -> str:
        lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
        summary = " ".join(lines)
        if len(summary) > limit:
            return summary[:limit].rstrip() + "..."
        return summary

    def _persist(self, material: Dict[str, Any]) -> None:
        path = self.output_dir / f"{material['sourceId']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(material, f, ensure_ascii=False, indent=2)
