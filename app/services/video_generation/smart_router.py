"""
智能视频生成路由服务
根据用户输入自动选择生成链路：
1. 纯文本描述 → 从零生成（Orchestrator）
2. 包含视频URL → 视频二创（Recreation）
3. 包含图片 → 图片参考生成（Orchestrator with images）
"""

import logging
import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.core.config import settings
from app.prompts.style_extraction_prompt import STYLE_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class InputAnalysis:
    """输入分析结果"""
    input_type: str  # "text_only", "with_video_url", "with_images", "with_urls"
    video_urls: List[str]  # 检测到的视频URL
    image_urls: List[str]  # 检测到的图片URL
    web_urls: List[str]  # 检测到的网页URL
    text_content: str  # 纯文本内容
    generation_mode: str  # "from_scratch", "recreation", "reference"


class SmartVideoRouter:
    """智能视频生成路由"""

    # 支持的视频平台域名
    VIDEO_PLATFORMS = [
        'youtube.com', 'youtu.be',
        'bilibili.com', 'b23.tv',
        'tiktok.com',
        'instagram.com',
        'twitter.com', 'x.com',
        'douyin.com',
        'kuaishou.com'
    ]

    # 图片文件扩展名
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']

    def __init__(self):
        self._client = genai.Client(api_key=settings.google_api_key)

    def analyze_input(self, user_input: str) -> InputAnalysis:
        """
        分析用户输入，识别类型和内容

        Args:
            user_input: 用户输入的文本

        Returns:
            InputAnalysis: 输入分析结果
        """
        logger.info(f"分析用户输入: {user_input[:100]}...")

        # 提取所有URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, user_input)

        video_urls = []
        image_urls = []
        web_urls = []

        # 分类URL
        for url in urls:
            if self._is_video_url(url):
                video_urls.append(url)
            elif self._is_image_url(url):
                image_urls.append(url)
            else:
                web_urls.append(url)

        # 移除URL后的纯文本内容
        text_content = user_input
        for url in urls:
            text_content = text_content.replace(url, '').strip()

        # 清理多余空格
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        # 判断输入类型和生成模式
        if video_urls:
            input_type = "with_video_url"
            generation_mode = "recreation"
        elif image_urls:
            input_type = "with_images"
            generation_mode = "reference"
        elif web_urls:
            input_type = "with_urls"
            generation_mode = "reference"  # 从网页提取内容作为参考
        else:
            input_type = "text_only"
            generation_mode = "from_scratch"

        result = InputAnalysis(
            input_type=input_type,
            video_urls=video_urls,
            image_urls=image_urls,
            web_urls=web_urls,
            text_content=text_content,
            generation_mode=generation_mode
        )

        logger.info(f"输入分析结果: {result.input_type}, 模式: {result.generation_mode}")
        if video_urls:
            logger.info(f"  检测到视频URL: {len(video_urls)} 个")
        if image_urls:
            logger.info(f"  检测到图片URL: {len(image_urls)} 个")
        if web_urls:
            logger.info(f"  检测到网页URL: {len(web_urls)} 个")

        return result

    def _is_video_url(self, url: str) -> bool:
        """判断是否为视频URL"""
        url_lower = url.lower()
        return any(platform in url_lower for platform in self.VIDEO_PLATFORMS)

    def _is_image_url(self, url: str) -> bool:
        """判断是否为图片URL"""
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in self.IMAGE_EXTENSIONS)

    async def extract_style_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取风格描述 - 使用 LLM

        Args:
            text: 文本内容

        Returns:
            风格描述（如果找到）
        """
        try:
            style_prompt = STYLE_EXTRACTION_PROMPT.format(text=text)

            response = await self._client.aio.models.generate_content(
                model='gemini-3-flash',
                contents=style_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)
            style = result.get("style")

            if style and style != "null":
                logger.info(f"LLM 检测到风格: {style}")
                return style
            else:
                logger.debug("LLM 未检测到明确风格")
                return None

        except Exception as e:
            logger.error(f"LLM 风格提取失败: {e}")
            return None

    async def build_generation_config(
        self,
        analysis: InputAnalysis,
        default_style: str = "专业"
    ) -> Dict[str, Any]:
        """
        根据分析结果构建生成配置

        Args:
            analysis: 输入分析结果
            default_style: 默认风格

        Returns:
            生成配置字典
        """
        config = {
            "generation_mode": analysis.generation_mode,
            "topic": analysis.text_content or "视频生成",
            "style": default_style
        }

        # 尝试从文本中提取风格（使用 LLM）
        detected_style = await self.extract_style_from_text(analysis.text_content)
        if detected_style:
            config["style"] = detected_style

        # 根据不同模式添加特定配置
        if analysis.generation_mode == "recreation":
            config["video_url"] = analysis.video_urls[0] if analysis.video_urls else None
            config["target_description"] = analysis.text_content

        elif analysis.generation_mode == "reference":
            if analysis.image_urls:
                config["user_images"] = analysis.image_urls
            if analysis.web_urls:
                config["user_urls"] = analysis.web_urls

        return config


# 全局实例
_router = None


def get_smart_router() -> SmartVideoRouter:
    """获取智能路由实例"""
    global _router
    if _router is None:
        _router = SmartVideoRouter()
    return _router
