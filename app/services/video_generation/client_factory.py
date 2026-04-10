"""
视频生成客户端工厂
根据环境自动选择合适的客户端
"""

import logging
from typing import Optional
from ...core.config import settings
from .base_client import BaseVideoGenerationClient

logger = logging.getLogger(__name__)


def get_video_client(api_key: Optional[str] = None) -> BaseVideoGenerationClient:
    """
    根据环境变量自动选择视频生成客户端

    - ENV=dev: 使用 AI Studio (开发环境，免费配额)
    - ENV=prod: 使用 Vertex AI (生产环境，付费服务)

    Args:
        api_key: 可选的 API Key，如果不提供则从配置读取

    Returns:
        BaseVideoGenerationClient: 视频生成客户端实例
    """
    env = settings.env.lower()

    if env == "prod":
        # 生产环境：使用 Vertex AI
        logger.info("🏭 使用 Vertex AI 客户端 (生产环境)")
        from .google_robust_client import VertexAIVideoClient
        return VertexAIVideoClient(api_key=api_key)
    else:
        # 开发环境：使用 AI Studio
        logger.info("🔧 使用 AI Studio 客户端 (开发环境)")
        from .google_aistudio_client import AIStudioVideoClient
        return AIStudioVideoClient(api_key=api_key)


# 向后兼容：保留原来的类名
def RobustGoogleVideoClient(api_key: Optional[str] = None) -> BaseVideoGenerationClient:
    """
    向后兼容的客户端创建函数
    自动根据环境选择合适的客户端
    """
    return get_video_client(api_key=api_key)
