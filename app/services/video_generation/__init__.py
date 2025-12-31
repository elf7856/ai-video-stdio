"""
视频生成服务模块

包含:
- 视频生成API客户端 (Google Veo, Runway, OpenAI)
- 视频生成编排器 (Orchestrator)
"""

from .base_client import BaseVideoGenerationClient, VideoGenerationRequest, VideoGenerationResult
from .openai_client import OpenAIVideoClient
from .runway_client import RunwayClient
from .google_robust_client import RobustGoogleVideoClient
from .orchestrator import (
    VideoGenerationOrchestrator,
    GenerationConfig,
    TaskState,
    TaskStatus,
    ShotInfo,
    get_orchestrator
)

__all__ = [
    # 基础类
    'BaseVideoGenerationClient',
    'VideoGenerationRequest',
    'VideoGenerationResult',

    # API客户端
    'RunwayClient',
    'OpenAIVideoClient',
    'RobustGoogleVideoClient',

    # 编排器
    'VideoGenerationOrchestrator',
    'GenerationConfig',
    'TaskState',
    'TaskStatus',
    'ShotInfo',
    'get_orchestrator',
]
