"""
质量检查数据模型

定义视频质量检查相关的数据结构和评分标准
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class QualityLevel(str, Enum):
    """质量等级"""
    EXCELLENT = "excellent"    # 优秀 (0.9-1.0)
    GOOD = "good"              # 良好 (0.7-0.9)
    ACCEPTABLE = "acceptable"  # 可接受 (0.5-0.7)
    POOR = "poor"              # 较差 (0.3-0.5)
    UNACCEPTABLE = "unacceptable"  # 不可接受 (<0.3)


class QualityDimension(str, Enum):
    """质量维度"""
    VISUAL_CONSISTENCY = "visual_consistency"  # 视觉一致性
    CONTENT_MATCH = "content_match"            # 内容匹配度
    TECHNICAL_QUALITY = "technical_quality"    # 技术质量
    PACING = "pacing"                          # 节奏感
    OVERALL = "overall"                        # 综合质量


class FrameAnalysis(BaseModel):
    """单帧分析结果"""
    frame_index: int = Field(description="帧索引")
    timestamp: float = Field(description="时间戳(秒)")
    frame_path: Optional[str] = Field(default=None, description="帧图像路径")

    # 视觉特征
    dominant_colors: List[str] = Field(default_factory=list, description="主要颜色")
    brightness: float = Field(default=0.5, ge=0, le=1, description="亮度 (0-1)")
    contrast: float = Field(default=0.5, ge=0, le=1, description="对比度 (0-1)")
    sharpness: float = Field(default=0.5, ge=0, le=1, description="清晰度 (0-1)")

    # 内容描述
    scene_description: str = Field(default="", description="场景描述")
    detected_objects: List[str] = Field(default_factory=list, description="检测到的物体")
    style_tags: List[str] = Field(default_factory=list, description="风格标签")

    # 质量问题
    issues: List[str] = Field(default_factory=list, description="发现的问题")


class VisualConsistencyResult(BaseModel):
    """视觉一致性检查结果"""
    score: float = Field(default=0.5, ge=0, le=1, description="一致性分数 (0-1)")
    level: QualityLevel = Field(default=QualityLevel.ACCEPTABLE, description="质量等级")

    # 细分指标
    color_consistency: float = Field(default=0.5, ge=0, le=1, description="色彩一致性")
    style_consistency: float = Field(default=0.5, ge=0, le=1, description="风格一致性")
    lighting_consistency: float = Field(default=0.5, ge=0, le=1, description="光照一致性")

    # 问题描述
    inconsistencies: List[str] = Field(default_factory=list, description="不一致的地方")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")

    # 帧分析
    frame_analyses: List[FrameAnalysis] = Field(default_factory=list, description="帧分析结果")


class ContentMatchResult(BaseModel):
    """内容匹配度检查结果"""
    score: float = Field(default=0.5, ge=0, le=1, description="匹配度分数 (0-1)")
    level: QualityLevel = Field(default=QualityLevel.ACCEPTABLE, description="质量等级")

    # 原始输入
    original_prompt: str = Field(default="", description="原始提示词")

    # 细分指标
    semantic_match: float = Field(default=0.5, ge=0, le=1, description="语义匹配度")
    visual_match: float = Field(default=0.5, ge=0, le=1, description="视觉匹配度")
    style_match: float = Field(default=0.5, ge=0, le=1, description="风格匹配度")

    # 详细分析
    matched_elements: List[str] = Field(default_factory=list, description="匹配的元素")
    missing_elements: List[str] = Field(default_factory=list, description="缺失的元素")
    unexpected_elements: List[str] = Field(default_factory=list, description="意外的元素")

    # 建议
    suggestions: List[str] = Field(default_factory=list, description="改进建议")


class TechnicalQualityResult(BaseModel):
    """技术质量检查结果"""
    score: float = Field(default=0.5, ge=0, le=1, description="技术质量分数 (0-1)")
    level: QualityLevel = Field(default=QualityLevel.ACCEPTABLE, description="质量等级")

    # 视频属性
    resolution: str = Field(default="", description="分辨率")
    fps: float = Field(default=0, description="帧率")
    duration: float = Field(default=0, description="时长(秒)")
    file_size: int = Field(default=0, description="文件大小(bytes)")
    bitrate: float = Field(default=0, description="比特率(kbps)")

    # 质量指标
    clarity_score: float = Field(default=0.5, ge=0, le=1, description="清晰度分数")
    stability_score: float = Field(default=0.5, ge=0, le=1, description="稳定性分数")
    encoding_quality: float = Field(default=0.5, ge=0, le=1, description="编码质量")

    # 问题
    issues: List[str] = Field(default_factory=list, description="技术问题")


class ShotQualityResult(BaseModel):
    """单个镜头的质量检查结果"""
    shot_index: int = Field(description="镜头索引")
    shot_id: str = Field(default="", description="镜头ID")
    video_path: str = Field(default="", description="视频路径")
    prompt: str = Field(default="", description="生成提示词")

    # 各维度质量
    visual_consistency: VisualConsistencyResult = Field(
        default_factory=VisualConsistencyResult,
        description="视觉一致性"
    )
    content_match: ContentMatchResult = Field(
        default_factory=ContentMatchResult,
        description="内容匹配度"
    )
    technical_quality: TechnicalQualityResult = Field(
        default_factory=TechnicalQualityResult,
        description="技术质量"
    )

    # 综合评分
    overall_score: float = Field(default=0.5, ge=0, le=1, description="综合分数")
    overall_level: QualityLevel = Field(default=QualityLevel.ACCEPTABLE, description="综合等级")

    # 是否需要重新生成
    needs_regeneration: bool = Field(default=False, description="是否需要重新生成")
    regeneration_reason: str = Field(default="", description="重新生成原因")
    regeneration_suggestions: List[str] = Field(default_factory=list, description="重新生成建议")


class QualityCheckConfig(BaseModel):
    """质量检查配置"""
    # 启用的检查项
    check_visual_consistency: bool = Field(default=True, description="检查视觉一致性")
    check_content_match: bool = Field(default=True, description="检查内容匹配度")
    check_technical_quality: bool = Field(default=True, description="检查技术质量")

    # 关键帧提取
    keyframe_count: int = Field(default=5, ge=1, le=20, description="提取的关键帧数量")
    keyframe_method: str = Field(default="uniform", description="关键帧提取方法: uniform/scene_change")

    # 质量阈值
    min_acceptable_score: float = Field(default=0.5, ge=0, le=1, description="最低可接受分数")
    regeneration_threshold: float = Field(default=0.4, ge=0, le=1, description="重新生成阈值")

    # 权重配置
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "visual_consistency": 0.3,
            "content_match": 0.4,
            "technical_quality": 0.3
        },
        description="各维度权重"
    )

    # LLM配置
    use_llm_analysis: bool = Field(default=True, description="使用LLM进行分析")
    llm_provider: str = Field(default="google", description="LLM提供商")


class QualityReport(BaseModel):
    """完整的质量检查报告"""
    # 基本信息
    project_id: str = Field(default="", description="项目ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    # 配置
    config: QualityCheckConfig = Field(default_factory=QualityCheckConfig, description="检查配置")

    # 镜头检查结果
    shots: List[ShotQualityResult] = Field(default_factory=list, description="各镜头质量结果")

    # 整体评估
    overall_visual_consistency: float = Field(default=0.5, ge=0, le=1, description="整体视觉一致性")
    overall_content_match: float = Field(default=0.5, ge=0, le=1, description="整体内容匹配度")
    overall_technical_quality: float = Field(default=0.5, ge=0, le=1, description="整体技术质量")
    overall_score: float = Field(default=0.5, ge=0, le=1, description="整体综合分数")
    overall_level: QualityLevel = Field(default=QualityLevel.ACCEPTABLE, description="整体质量等级")

    # 需要重新生成的镜头
    shots_to_regenerate: List[int] = Field(default_factory=list, description="需要重新生成的镜头索引")

    # 总体建议
    summary: str = Field(default="", description="质量总结")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")

    def calculate_overall_scores(self) -> None:
        """计算整体分数"""
        if not self.shots:
            return

        # 计算各维度平均分
        visual_scores = [s.visual_consistency.score for s in self.shots]
        content_scores = [s.content_match.score for s in self.shots]
        technical_scores = [s.technical_quality.score for s in self.shots]

        self.overall_visual_consistency = sum(visual_scores) / len(visual_scores)
        self.overall_content_match = sum(content_scores) / len(content_scores)
        self.overall_technical_quality = sum(technical_scores) / len(technical_scores)

        # 加权计算综合分数
        weights = self.config.weights
        self.overall_score = (
            self.overall_visual_consistency * weights.get("visual_consistency", 0.3) +
            self.overall_content_match * weights.get("content_match", 0.4) +
            self.overall_technical_quality * weights.get("technical_quality", 0.3)
        )

        # 确定质量等级
        self.overall_level = self._score_to_level(self.overall_score)

        # 找出需要重新生成的镜头
        self.shots_to_regenerate = [
            s.shot_index for s in self.shots if s.needs_regeneration
        ]

    @staticmethod
    def _score_to_level(score: float) -> QualityLevel:
        """将分数转换为质量等级"""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE


class RegenerationRequest(BaseModel):
    """重新生成请求"""
    shot_index: int = Field(description="镜头索引")
    original_prompt: str = Field(description="原始提示词")
    improved_prompt: str = Field(default="", description="改进后的提示词")
    quality_issues: List[str] = Field(default_factory=list, description="质量问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    priority: int = Field(default=1, ge=1, le=5, description="优先级 (1最高)")
