"""
镜头数据模型
定义视频镜头的核心数据结构和相关枚举
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid


class ShotType(str, Enum):
    """镜头类型枚举"""
    ESTABLISHING = "establishing"    # 全景/建立镜头
    CLOSE_UP = "close_up"           # 特写镜头
    MEDIUM = "medium"               # 中景镜头
    WIDE = "wide"                   # 广角镜头
    TRANSITION = "transition"       # 过渡镜头
    ACTION = "action"               # 动作镜头
    DETAIL = "detail"               # 细节镜头
    CUTAWAY = "cutaway"            # 插切镜头


class ShotStatus(str, Enum):
    """镜头状态枚举"""
    PLANNED = "planned"             # 已规划
    GENERATING = "generating"       # 生成中
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"              # 生成失败
    RETRY = "retry"                # 重试中


class APIProvider(str, Enum):
    """视频生成API提供商枚举"""
    GOOGLE_VEO = "google_veo"
    RUNWAY = "runway"
    OPENAI_SORA = "openai_sora"
    STABLE_VIDEO = "stable_video"


class Shot(BaseModel):
    """镜头模型"""
    
    id: str = Field(default_factory=lambda: f"shot_{str(uuid.uuid4())[:8]}")
    project_id: str = Field(..., description="所属项目ID")
    sequence: int = Field(..., ge=1, description="镜头序号")
    
    # 镜头内容定义
    prompt: str = Field(..., min_length=1, description="生成prompt")
    description: str = Field(default="", description="镜头描述")
    shot_type: ShotType = Field(default=ShotType.MEDIUM)
    
    # 时长和技术参数
    duration: float = Field(..., ge=3.0, le=15.0, description="镜头时长(秒)")
    target_resolution: str = Field(default="1920x1080")
    target_fps: int = Field(default=30)
    
    # 风格参数
    style_params: Dict[str, Any] = Field(default_factory=dict)
    
    # 生成相关
    api_provider: APIProvider = Field(default=APIProvider.GOOGLE_VEO)
    priority: int = Field(default=1, ge=1, le=5, description="优先级1-5，数字越大优先级越高")
    max_retries: int = Field(default=3)
    current_retry: int = Field(default=0)
    
    # 状态和结果
    status: ShotStatus = Field(default=ShotStatus.PLANNED)
    file_path: Optional[str] = Field(default=None, description="生成的视频文件路径")
    thumbnail_path: Optional[str] = Field(default=None, description="缩略图路径")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    generation_started_at: Optional[datetime] = Field(default=None)
    generation_completed_at: Optional[datetime] = Field(default=None)
    
    # 质量和成本信息
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    generation_cost: float = Field(default=0.0, ge=0.0)
    generation_time: float = Field(default=0.0, ge=0.0, description="生成耗时(秒)")
    
    # 错误信息
    error_message: Optional[str] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def update_status(self, new_status: ShotStatus, error_message: Optional[str] = None):
        """更新镜头状态"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == ShotStatus.GENERATING:
            self.generation_started_at = datetime.now()
        elif new_status in [ShotStatus.COMPLETED, ShotStatus.FAILED]:
            self.generation_completed_at = datetime.now()
            if self.generation_started_at:
                self.generation_time = (self.generation_completed_at - self.generation_started_at).total_seconds()
        
        if error_message:
            self.error_message = error_message

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.current_retry < self.max_retries and self.status == ShotStatus.FAILED

    def increment_retry(self):
        """增加重试次数"""
        self.current_retry += 1
        self.status = ShotStatus.RETRY
        self.updated_at = datetime.now()

    def get_filename(self) -> str:
        """生成标准化的文件名"""
        return f"shot_{self.sequence:03d}_{int(self.duration)}s.mp4"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式用于保存"""
        return {
            "id": self.id,
            "sequence": self.sequence,
            "prompt": self.prompt,
            "description": self.description,
            "shot_type": self.shot_type.value,
            "duration": self.duration,
            "api_provider": self.api_provider.value,
            "status": self.status.value,
            "file_path": self.file_path,
            "style_params": self.style_params,
            "priority": self.priority,
            "quality_score": self.quality_score,
            "generation_cost": self.generation_cost,
            "generation_time": self.generation_time,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error_message": self.error_message
        }


class ShotPlan(BaseModel):
    """分镜计划模型"""
    
    id: str = Field(default_factory=lambda: f"plan_{str(uuid.uuid4())[:8]}")
    project_id: str = Field(..., description="所属项目ID")
    shots: List[Shot] = Field(default_factory=list)
    
    # 计划统计
    total_duration: float = Field(default=0.0, description="总时长")
    total_shots: int = Field(default=0, description="总镜头数")
    estimated_cost: float = Field(default=0.0, description="预估成本")
    estimated_time: float = Field(default=0.0, description="预估生成时间(秒)")
    
    # 计划元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    strategy_notes: str = Field(default="", description="策略说明")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_shot(self, shot: Shot):
        """添加镜头到计划"""
        shot.sequence = len(self.shots) + 1
        shot.project_id = self.project_id
        self.shots.append(shot)
        self._recalculate_stats()

    def remove_shot(self, shot_id: str):
        """从计划中移除镜头"""
        self.shots = [s for s in self.shots if s.id != shot_id]
        # 重新排序
        for i, shot in enumerate(self.shots):
            shot.sequence = i + 1
        self._recalculate_stats()

    def get_shot_by_id(self, shot_id: str) -> Optional[Shot]:
        """根据ID获取镜头"""
        for shot in self.shots:
            if shot.id == shot_id:
                return shot
        return None

    def get_shots_by_status(self, status: ShotStatus) -> List[Shot]:
        """根据状态获取镜头列表"""
        return [shot for shot in self.shots if shot.status == status]

    def _recalculate_stats(self):
        """重新计算统计信息"""
        self.total_shots = len(self.shots)
        self.total_duration = sum(shot.duration for shot in self.shots)
        self.estimated_cost = sum(self._estimate_shot_cost(shot) for shot in self.shots)
        self.estimated_time = sum(self._estimate_shot_time(shot) for shot in self.shots)
        self.updated_at = datetime.now()

    def _estimate_shot_cost(self, shot: Shot) -> float:
        """估算单个镜头成本"""
        base_cost_per_second = {
            APIProvider.GOOGLE_VEO: 0.08,
            APIProvider.RUNWAY: 0.12,
            APIProvider.OPENAI_SORA: 0.10,
            APIProvider.STABLE_VIDEO: 0.06
        }
        return shot.duration * base_cost_per_second.get(shot.api_provider, 0.08)

    def _estimate_shot_time(self, shot: Shot) -> float:
        """估算单个镜头生成时间"""
        base_time_per_second = {
            APIProvider.GOOGLE_VEO: 6.0,
            APIProvider.RUNWAY: 8.0,
            APIProvider.OPENAI_SORA: 7.0,
            APIProvider.STABLE_VIDEO: 5.0
        }
        return shot.duration * base_time_per_second.get(shot.api_provider, 6.0)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "total_duration": self.total_duration,
            "total_shots": self.total_shots,
            "estimated_cost": self.estimated_cost,
            "estimated_time": self.estimated_time,
            "strategy_notes": self.strategy_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "shots": [shot.to_dict() for shot in self.shots]
        }