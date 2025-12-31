"""
视频编辑器数据库模型
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.utils.database import Base


class ProjectStatusEnum(str, enum.Enum):
    """项目状态枚举"""
    DRAFT = "draft"
    EDITING = "editing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class EditorProjectDB(Base):
    """编辑项目数据库模型"""
    __tablename__ = "editor_projects"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Timeline存储为JSON
    timeline_json = Column(JSON, nullable=True)

    # 状态
    status = Column(SQLEnum(ProjectStatusEnum), default=ProjectStatusEnum.DRAFT, nullable=False)

    # 输出配置
    output_path = Column(String(500), nullable=True)
    output_format = Column(String(10), default="mp4")
    output_quality = Column(String(20), default="high")

    # 渲染进度
    render_progress = Column(Float, default=0.0)
    render_error = Column(Text, nullable=True)

    # 元数据
    created_by = Column(String(100), nullable=True)  # 用户ID
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class SubtitleFileDB(Base):
    """字幕文件数据库模型"""
    __tablename__ = "subtitle_files"

    id = Column(String(100), primary_key=True, index=True)
    project_id = Column(String(100), index=True, nullable=False)

    # 语言
    language = Column(String(10), default="zh-CN")

    # 字幕片段（JSON格式）
    segments_json = Column(JSON, nullable=False)

    # 默认样式
    default_font_size = Column(Integer, default=40)
    default_color = Column(String(20), default="#FFFFFF")
    default_font_family = Column(String(100), default="Arial")
    default_position = Column(String(20), default="bottom")

    # 元数据
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
