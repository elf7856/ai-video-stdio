"""
项目数据模型
定义视频创作项目的核心数据结构
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    CREATED = "created"           # 已创建
    ANALYZING = "analyzing"       # 内容分析中
    PLANNING = "planning"         # 分镜规划中
    GENERATING = "generating"     # 视频生成中
    COMPOSING = "composing"       # 合成中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"       # 已取消


class Project(BaseModel):
    """视频创作项目模型"""
    
    id: str = Field(default_factory=lambda: f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}")
    title: str = Field(..., description="项目标题")
    script: str = Field(..., description="用户原始稿件")
    target_duration: int = Field(..., ge=30, le=300, description="目标总时长(秒)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: ProjectStatus = Field(default=ProjectStatus.CREATED)
    output_dir: str = Field(default="", description="输出目录路径")
    
    # 音频设置
    enable_narration: bool = Field(default=False, description="是否启用专业旁白音频")
    narration_voice: str = Field(default="default", description="旁白语音类型")
    narration_speed: float = Field(default=1.0, description="旁白语速")
    narration_audio_path: Optional[str] = Field(default=None, description="旁白音频文件路径")
    
    # 可选的用户偏好设置
    style_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    quality_requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # 项目统计信息
    total_shots: int = Field(default=0, description="总镜头数")
    completed_shots: int = Field(default=0, description="已完成镜头数")
    failed_shots: int = Field(default=0, description="失败镜头数")
    total_cost: float = Field(default=0.0, description="总成本")
    generation_time: float = Field(default=0.0, description="生成耗时(秒)")
    
    # 结果文件路径
    final_video_path: Optional[str] = Field(default=None)
    thumbnail_path: Optional[str] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def update_status(self, new_status: ProjectStatus):
        """更新项目状态"""
        self.status = new_status
        self.updated_at = datetime.now()

    def get_progress_percentage(self) -> float:
        """获取项目进度百分比"""
        if self.total_shots == 0:
            return 0.0
        return (self.completed_shots / self.total_shots) * 100

    def add_shot_result(self, success: bool, cost: float = 0.0, time: float = 0.0):
        """添加镜头生成结果"""
        if success:
            self.completed_shots += 1
        else:
            self.failed_shots += 1
        
        self.total_cost += cost
        self.generation_time += time
        self.updated_at = datetime.now()

    def to_metadata_dict(self) -> Dict[str, Any]:
        """转换为元数据字典用于保存"""
        return {
            "id": self.id,
            "title": self.title,
            "script": self.script,
            "target_duration": self.target_duration,
            "actual_duration": 0,  # 将在合成后更新
            "total_shots": self.total_shots,
            "completed_shots": self.completed_shots,
            "failed_shots": self.failed_shots,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "total_cost": self.total_cost,
            "generation_time": self.generation_time,
            "style_preferences": self.style_preferences,
            "quality_requirements": self.quality_requirements,
            # 音频设置
            "enable_narration": self.enable_narration,
            "narration_voice": self.narration_voice,
            "narration_speed": self.narration_speed,
            "narration_audio_path": self.narration_audio_path
        }


class ProjectSummary(BaseModel):
    """项目摘要模型，用于列表显示"""
    
    id: str
    title: str
    status: ProjectStatus
    target_duration: int
    total_shots: int
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    final_video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """创建项目的请求模型"""
    
    title: str = Field(..., min_length=1, max_length=100, description="项目标题")
    script: str = Field(..., min_length=10, max_length=5000, description="用户稿件")
    target_duration: int = Field(..., ge=30, le=300, description="目标时长(秒)")
    
    # 音频相关设置
    enable_narration: bool = Field(default=False, description="是否启用专业旁白音频")
    narration_voice: Optional[str] = Field(default="default", description="旁白语音类型")
    narration_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="旁白语速")
    
    # 可选设置
    style_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    quality_requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    """更新项目的请求模型"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    target_duration: Optional[int] = Field(None, ge=30, le=300)
    
    # 音频相关设置
    enable_narration: Optional[bool] = Field(None, description="是否启用专业旁白音频")
    narration_voice: Optional[str] = Field(None, description="旁白语音类型")
    narration_speed: Optional[float] = Field(None, ge=0.5, le=2.0, description="旁白语速")
    
    style_preferences: Optional[Dict[str, Any]] = None
    quality_requirements: Optional[Dict[str, Any]] = None