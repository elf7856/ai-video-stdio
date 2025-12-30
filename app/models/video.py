from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    duration = Column(Float)
    resolution = Column(String(50))
    file_size = Column(Integer)
    format = Column(String(10))
    
    # 分析结果
    analysis = Column(JSON)
    tags = Column(JSON)
    scenes = Column(JSON)
    transcript = Column(Text)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    edits = relationship("VideoEdit", back_populates="video")
    projects = relationship("Project", back_populates="video")

class VideoEdit(Base):
    __tablename__ = "video_edits"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    
    # 编辑信息
    instruction = Column(Text, nullable=False)
    edit_type = Column(String(50))  # insert, replace, delete, style_change
    start_time = Column(Float)
    end_time = Column(Float)
    duration = Column(Float)
    
    # 生成的内容
    generated_content = Column(JSON)
    output_path = Column(String(500))
    
    # 状态
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 关系
    video = relationship("Video", back_populates="edits")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    video_id = Column(Integer, ForeignKey("videos.id"))
    
    # 项目配置
    settings = Column(JSON)
    timeline = Column(JSON)
    
    # 状态
    status = Column(String(20), default="draft")  # draft, active, completed
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    video = relationship("Video", back_populates="projects")

# Pydantic models for API
class VideoCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class VideoResponse(BaseModel):
    id: int
    filename: str
    title: Optional[str]
    description: Optional[str]
    duration: Optional[float]
    resolution: Optional[str]
    file_size: Optional[int]
    format: Optional[str]
    analysis: Optional[dict]
    tags: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class VideoEditCreate(BaseModel):
    instruction: str
    edit_type: Optional[str] = "insert"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None

class VideoEditResponse(BaseModel):
    id: int
    video_id: int
    instruction: str
    edit_type: str
    start_time: Optional[float]
    end_time: Optional[float]
    duration: Optional[float]
    status: str
    progress: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[dict] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    video_id: Optional[int]
    settings: Optional[dict]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 