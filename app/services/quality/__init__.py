"""
质量检查服务模块

提供视频质量检查、评估和自动重新生成功能
"""

from .models import (
    QualityLevel,
    QualityDimension,
    FrameAnalysis,
    VisualConsistencyResult,
    ContentMatchResult,
    TechnicalQualityResult,
    ShotQualityResult,
    QualityCheckConfig,
    QualityReport,
    RegenerationRequest
)

from .checker import (
    VideoQualityChecker,
    check_video_quality,
    check_project_quality
)

from .regenerator import (
    AutoRegenerator,
    RegenerationResult,
    RegenerationReport,
    auto_regenerate_low_quality
)

__all__ = [
    # 数据模型
    "QualityLevel",
    "QualityDimension",
    "FrameAnalysis",
    "VisualConsistencyResult",
    "ContentMatchResult",
    "TechnicalQualityResult",
    "ShotQualityResult",
    "QualityCheckConfig",
    "QualityReport",
    "RegenerationRequest",

    # 服务类
    "VideoQualityChecker",
    "AutoRegenerator",
    "RegenerationResult",
    "RegenerationReport",

    # 便捷函数
    "check_video_quality",
    "check_project_quality",
    "auto_regenerate_low_quality",
]
