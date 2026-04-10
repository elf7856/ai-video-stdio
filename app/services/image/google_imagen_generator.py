"""
Google Imagen 3 图像生成器
支持 imagen-3.0-generate-001 和 imagen-3.0-fast-generate-001
"""

import os
import time
import logging
import uuid
from typing import Tuple, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# 懒加载Google AI SDK
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None


class GoogleImagenGenerator:
    """Google Imagen 3 图像生成器 (Vertex AI)"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-image-preview"):
        self.api_key = api_key or settings.vertex_api_key or settings.google_api_key
        self.project_id = settings.vertex_project_id
        self.location = settings.vertex_location
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not GENAI_AVAILABLE:
                raise ImportError("google.genai 模块不可用，请安装: pip install google-genai")
            if not self.project_id:
                raise ValueError("VERTEX_PROJECT_ID 未配置")
            try:
                if self.api_key:
                    # Vertex AI Express 模式：只用 api_key
                    self._client = genai.Client(  # type: ignore
                        vertexai=True,
                        api_key=self.api_key,
                    )
                    logger.info("✅ Vertex AI Imagen 客户端初始化完成 (api_key 模式)")
                else:
                    # 标准模式：project + location（需要 ADC）
                    self._client = genai.Client(  # type: ignore
                        vertexai=True,
                        project=self.project_id,
                        location=self.location,
                    )
                    logger.info(f"✅ Vertex AI Imagen 客户端初始化完成 (project={self.project_id})")
            except Exception as e:
                logger.error(f"❌ Vertex AI Imagen 客户端初始化失败: {e}")
                raise
        return self._client

    def is_available(self) -> bool:
        return bool(self.project_id) and GENAI_AVAILABLE

    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: Optional[Tuple[int, int]] = None,
        aspect_ratio: Optional[str] = None,
        resolution: str = "medium",
        **kwargs
    ) -> str:
        if not self.is_available():
            raise Exception("Google Vertex AI Imagen API不可用，请检查 VERTEX_PROJECT_ID 配置")

        try:
            logger.info(f"🎨 开始生成图像 (Vertex AI): {prompt[:50]}...")

            if aspect_ratio is None:
                aspect_ratio = self._size_to_aspect_ratio(size) if size else "1:1"

            final_prompt = prompt
            if negative_prompt:
                final_prompt = f"{prompt}. Avoid: {negative_prompt}"

            aspect_ratio_hint = f"Create a {resolution} resolution image with {aspect_ratio} aspect ratio. "
            enhanced_prompt = aspect_ratio_hint + final_prompt

            response = self.client.models.generate_content(
                model=self.model,
                contents=enhanced_prompt,
                config=genai.types.GenerateContentConfig(  # type: ignore
                    response_modalities=['TEXT', 'IMAGE'],
                )
            )

            if not response or not response.candidates:
                raise Exception("API未返回结果")

            candidate = response.candidates[0]
            image_part = next(
                (part for part in candidate.content.parts
                 if hasattr(part, 'inline_data') and part.inline_data is not None),
                None
            )

            if not image_part:
                raise Exception("响应中未找到图像数据")

            output_dir = os.path.join(settings.output_dir, "images")
            os.makedirs(output_dir, exist_ok=True)

            unique_filename = f"vertex_imagen_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
            output_path = os.path.join(output_dir, unique_filename)

            with open(output_path, 'wb') as f:
                f.write(image_part.inline_data.data)

            logger.info(f"✅ 图像生成成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Vertex AI 图像生成失败: {e}")
            raise

    def _size_to_aspect_ratio(self, size: Tuple[int, int]) -> str:
        width, height = size
        ratio = width / height
        if abs(ratio - 1.0) < 0.1: return "1:1"
        if abs(ratio - 0.75) < 0.1: return "3:4"
        if abs(ratio - 1.333) < 0.1: return "4:3"
        if abs(ratio - 0.5625) < 0.1: return "9:16"
        if abs(ratio - 1.778) < 0.1: return "16:9"
        return "9:16" if ratio < 0.8 else ("1:1" if ratio < 1.2 else "16:9")