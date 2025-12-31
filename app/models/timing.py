"""
时长规划数据模型
定义视频时长分配和节奏控制的数据结构
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class PacingStrategy(str, Enum):
    """节奏策略枚举"""
    BALANCED = "balanced"           # 平衡节奏
    FAST_PACED = "fast_paced"      # 快节奏
    SLOW_PACED = "slow_paced"      # 慢节奏
    DYNAMIC = "dynamic"            # 动态节奏（变化丰富）
    CRESCENDO = "crescendo"        # 渐强节奏（逐渐加快）
    DECRESCENDO = "decrescendo"    # 渐弱节奏（逐渐放慢）


class ContentImportance(str, Enum):
    """内容重要性级别"""
    CRITICAL = "critical"          # 关键内容 (权重: 1.5)
    HIGH = "high"                 # 高重要性 (权重: 1.2)
    MEDIUM = "medium"             # 中等重要性 (权重: 1.0)
    LOW = "low"                   # 低重要性 (权重: 0.8)
    FILLER = "filler"             # 填充内容 (权重: 0.6)


class ShotTiming(BaseModel):
    """单个镜头的时长分配"""
    
    shot_id: str = Field(..., description="镜头ID")
    sequence: int = Field(..., description="镜头序号")
    content_segment: str = Field(..., description="对应的内容片段")
    
    # 重要性分析
    importance_level: ContentImportance = Field(default=ContentImportance.MEDIUM)
    importance_weight: float = Field(default=1.0, ge=0.1, le=2.0, description="重要性权重")
    content_density: float = Field(default=0.5, ge=0.0, le=1.0, description="内容密度")
    
    # 时长分配
    base_duration: float = Field(..., ge=3.0, le=15.0, description="基础时长")
    adjusted_duration: float = Field(..., ge=3.0, le=15.0, description="调整后时长")
    min_duration: float = Field(default=3.0, description="最小时长限制")
    max_duration: float = Field(default=15.0, description="最大时长限制")
    
    # 节奏控制
    pacing_factor: float = Field(default=1.0, ge=0.5, le=2.0, description="节奏因子")
    transition_buffer: float = Field(default=0.2, ge=0.0, le=1.0, description="转场缓冲时间")
    
    # 上下文信息
    is_opening: bool = Field(default=False, description="是否为开场镜头")
    is_closing: bool = Field(default=False, description="是否为结尾镜头")
    is_climax: bool = Field(default=False, description="是否为高潮镜头")
    
    # 调整原因记录
    adjustment_reason: Optional[str] = Field(default=None, description="时长调整原因")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def calculate_final_duration(self, global_pacing: float = 1.0) -> float:
        """计算最终时长"""
        # 基于重要性和节奏的时长计算
        duration = self.base_duration * self.importance_weight * self.pacing_factor * global_pacing
        
        # 特殊镜头时长调整
        if self.is_opening or self.is_closing:
            duration *= 1.2  # 开场和结尾稍长
        if self.is_climax:
            duration *= 1.3  # 高潮镜头更长
        
        # 应用约束
        duration = max(self.min_duration, min(self.max_duration, duration))
        
        self.adjusted_duration = round(duration, 1)
        return self.adjusted_duration


class TimingPlan(BaseModel):
    """完整的时长规划模型"""
    
    id: str = Field(default_factory=lambda: f"timing_{str(uuid.uuid4())[:8]}")
    project_id: str = Field(..., description="所属项目ID")
    
    # 目标参数
    target_total_duration: float = Field(..., ge=30.0, le=300.0, description="目标总时长")
    actual_total_duration: float = Field(default=0.0, description="实际总时长")
    duration_tolerance: float = Field(default=2.0, description="时长容差(秒)")
    
    # 节奏策略
    pacing_strategy: PacingStrategy = Field(default=PacingStrategy.BALANCED)
    global_pacing_factor: float = Field(default=1.0, ge=0.5, le=2.0, description="全局节奏因子")
    
    # 镜头时长分配
    shot_timings: List[ShotTiming] = Field(default_factory=list)
    
    # 转场和间隔
    transition_duration: float = Field(default=0.5, ge=0.0, le=2.0, description="转场时长")
    total_transition_time: float = Field(default=0.0, description="总转场时间")
    
    # 质量指标
    pacing_variety_score: float = Field(default=0.0, ge=0.0, le=1.0, description="节奏变化丰富度")
    duration_balance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="时长平衡分")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    optimization_notes: str = Field(default="", description="优化说明")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_shot_timing(self, shot_timing: ShotTiming):
        """添加镜头时长分配"""
        shot_timing.sequence = len(self.shot_timings) + 1
        self.shot_timings.append(shot_timing)
        self._recalculate_totals()

    def optimize_durations(self) -> bool:
        """优化时长分配"""
        if not self.shot_timings:
            return False
        
        # 第一轮：基础时长分配
        self._allocate_base_durations()
        
        # 第二轮：重要性权重调整
        self._apply_importance_weights()
        
        # 第三轮：节奏策略调整
        self._apply_pacing_strategy()
        
        # 第四轮：总时长匹配调整
        self._adjust_to_target_duration()
        
        # 计算质量指标
        self._calculate_quality_metrics()
        
        self.updated_at = datetime.now()
        return True

    def _allocate_base_durations(self):
        """分配基础时长"""
        if not self.shot_timings:
            return
        
        # 平均分配基础时长
        base_duration_per_shot = self.target_total_duration / len(self.shot_timings)
        
        for timing in self.shot_timings:
            timing.base_duration = max(3.0, min(15.0, base_duration_per_shot))

    def _apply_importance_weights(self):
        """应用重要性权重"""
        total_weight = sum(timing.importance_weight for timing in self.shot_timings)
        
        for timing in self.shot_timings:
            weight_ratio = timing.importance_weight / total_weight if total_weight > 0 else 1.0
            timing.adjusted_duration = timing.base_duration * weight_ratio * len(self.shot_timings)
            timing.adjusted_duration = max(timing.min_duration, 
                                         min(timing.max_duration, timing.adjusted_duration))

    def _apply_pacing_strategy(self):
        """应用节奏策略"""
        if not self.shot_timings:
            return
        
        total_shots = len(self.shot_timings)
        
        for i, timing in enumerate(self.shot_timings):
            if self.pacing_strategy == PacingStrategy.CRESCENDO:
                # 渐强：时长逐渐增加
                timing.pacing_factor = 0.8 + 0.4 * (i / (total_shots - 1))
            elif self.pacing_strategy == PacingStrategy.DECRESCENDO:
                # 渐弱：时长逐渐减少
                timing.pacing_factor = 1.2 - 0.4 * (i / (total_shots - 1))
            elif self.pacing_strategy == PacingStrategy.DYNAMIC:
                # 动态：交替变化
                timing.pacing_factor = 1.2 if i % 2 == 0 else 0.8
            elif self.pacing_strategy == PacingStrategy.FAST_PACED:
                timing.pacing_factor = 0.8
            elif self.pacing_strategy == PacingStrategy.SLOW_PACED:
                timing.pacing_factor = 1.2
            else:  # BALANCED
                timing.pacing_factor = 1.0
            
            # 应用节奏因子
            timing.calculate_final_duration(self.global_pacing_factor)

    def _adjust_to_target_duration(self):
        """调整到目标总时长"""
        current_total = sum(timing.adjusted_duration for timing in self.shot_timings)
        
        if abs(current_total - self.target_total_duration) <= self.duration_tolerance:
            return  # 已经在容差范围内
        
        # 计算调整比例
        adjustment_ratio = self.target_total_duration / current_total if current_total > 0 else 1.0
        
        for timing in self.shot_timings:
            new_duration = timing.adjusted_duration * adjustment_ratio
            timing.adjusted_duration = max(timing.min_duration, 
                                         min(timing.max_duration, new_duration))
            timing.adjustment_reason = f"目标时长调整 (比例: {adjustment_ratio:.3f})"
        
        self._recalculate_totals()

    def _calculate_quality_metrics(self):
        """计算质量指标"""
        if not self.shot_timings:
            return
        
        durations = [timing.adjusted_duration for timing in self.shot_timings]
        
        # 节奏变化丰富度 (时长变化的标准差)
        if len(durations) > 1:
            mean_duration = sum(durations) / len(durations)
            variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
            std_dev = variance ** 0.5
            self.pacing_variety_score = min(1.0, std_dev / 3.0)  # 标准化到0-1
        
        # 时长平衡分 (与目标时长的匹配度)
        duration_diff = abs(self.actual_total_duration - self.target_total_duration)
        self.duration_balance_score = max(0.0, 1.0 - duration_diff / self.target_total_duration)

    def _recalculate_totals(self):
        """重新计算总计数据"""
        self.actual_total_duration = sum(timing.adjusted_duration for timing in self.shot_timings)
        self.total_transition_time = max(0, len(self.shot_timings) - 1) * self.transition_duration
        self.updated_at = datetime.now()

    def get_shot_timing_by_id(self, shot_id: str) -> Optional[ShotTiming]:
        """根据镜头ID获取时长分配"""
        for timing in self.shot_timings:
            if timing.shot_id == shot_id:
                return timing
        return None

    def validate_constraints(self) -> List[str]:
        """验证时长约束"""
        violations = []
        
        for timing in self.shot_timings:
            if timing.adjusted_duration < timing.min_duration:
                violations.append(f"镜头{timing.sequence}时长({timing.adjusted_duration}s)低于最小值({timing.min_duration}s)")
            if timing.adjusted_duration > timing.max_duration:
                violations.append(f"镜头{timing.sequence}时长({timing.adjusted_duration}s)超过最大值({timing.max_duration}s)")
        
        total_duration_diff = abs(self.actual_total_duration - self.target_total_duration)
        if total_duration_diff > self.duration_tolerance:
            violations.append(f"总时长差异({total_duration_diff:.1f}s)超出容差({self.duration_tolerance}s)")
        
        return violations

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "target_total_duration": self.target_total_duration,
            "actual_total_duration": self.actual_total_duration,
            "pacing_strategy": self.pacing_strategy.value,
            "global_pacing_factor": self.global_pacing_factor,
            "transition_duration": self.transition_duration,
            "total_transition_time": self.total_transition_time,
            "pacing_variety_score": self.pacing_variety_score,
            "duration_balance_score": self.duration_balance_score,
            "optimization_notes": self.optimization_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "shot_timings": [
                {
                    "shot_id": timing.shot_id,
                    "sequence": timing.sequence,
                    "content_segment": timing.content_segment,
                    "importance_level": timing.importance_level.value,
                    "importance_weight": timing.importance_weight,
                    "base_duration": timing.base_duration,
                    "adjusted_duration": timing.adjusted_duration,
                    "pacing_factor": timing.pacing_factor,
                    "is_opening": timing.is_opening,
                    "is_closing": timing.is_closing,
                    "is_climax": timing.is_climax,
                    "adjustment_reason": timing.adjustment_reason
                }
                for timing in self.shot_timings
            ]
        }