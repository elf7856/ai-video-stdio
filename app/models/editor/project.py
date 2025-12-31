"""
编辑项目数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

from .timeline import Timeline


class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"  # 草稿
    EDITING = "editing"  # 编辑中
    RENDERING = "rendering"  # 渲染中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class EditorProject(BaseModel):
    """编辑项目"""
    id: str
    name: str
    description: Optional[str] = None
    timeline: Optional[Timeline] = None
    status: ProjectStatus = ProjectStatus.DRAFT

    # 渲染输出
    output_path: Optional[str] = None
    output_format: str = "mp4"
    output_quality: Literal["low", "medium", "high"] = "high"

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None  # 用户ID

    # 渲染进度
    render_progress: float = 0.0  # 0-100
    render_error: Optional[str] = None

    class Config:
        use_enum_values = True
