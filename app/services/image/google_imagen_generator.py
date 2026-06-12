"""
Google Imagen 3 图像生成器
支持 imagen-3.0-generate-001 和 imagen-3.0-fast-generate-001
"""

import os
import time
import logging
import uuid
from typing import Tuple, Optional, Dict, Any, List
from app.core.config import settings
from app.services.google_error_utils import format_google_api_error

logger = logging.getLogger(__name__)

# 懒加载Google AI SDK
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

# 懒加载 PIL（仅在需要参考图时使用）
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    PILImage = None


class GoogleImagenGenerator:
    """Google Imagen 3 图像生成器 (Vertex AI)"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-image"):
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
        return bool(self.project_id) and bool(self.api_key) and GENAI_AVAILABLE

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: Optional[Tuple[int, int]] = None,
        aspect_ratio: Optional[str] = None,
        resolution: str = "medium",
        reference_images: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """生成图像。

        Args:
            reference_images: 参考图路径列表（角色锁定/场景锁定）。利用 Gemini 3 Pro Image
                的多模态能力，把参考图与文本一起作为 contents，使输出与参考保持一致。
        """
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

            # 构建 contents：纯文本 → 字符串；带参考图 → [text, image, image, ...]
            contents: Any = enhanced_prompt
            valid_refs: List[str] = []
            if reference_images:
                if not PIL_AVAILABLE:
                    logger.warning("⚠️ 提供了参考图但 PIL 不可用，将退化为纯文本生成")
                else:
                    for ref_path in reference_images:
                        if not ref_path or not os.path.exists(ref_path):
                            logger.warning(f"⚠️ 参考图不存在，跳过: {ref_path}")
                            continue
                        valid_refs.append(ref_path)

            if valid_refs:
                ref_instruction = (
                    "Use the following reference image(s) to lock the visual identity "
                    "(character appearance, outfit, distinctive features). "
                    "Match faces, body shapes, clothing and styling exactly. "
                    "Then render the scene described below.\n\n"
                )
                pil_images = [PILImage.open(p) for p in valid_refs]
                contents = [ref_instruction + enhanced_prompt, *pil_images]
                logger.info(f"  使用 {len(valid_refs)} 张参考图锁定视觉一致性")

            import asyncio
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=contents,
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
            logger.error(
                "❌ Vertex AI 图像生成失败详情: %s",
                format_google_api_error(
                    e,
                    {
                        "model": self.model,
                        "project_id": self.project_id,
                        "location": self.location,
                        "aspect_ratio": aspect_ratio if "aspect_ratio" in locals() else None,
                        "resolution": resolution,
                        "reference_image_count": len(valid_refs) if "valid_refs" in locals() else 0,
                    },
                ),
            )
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
