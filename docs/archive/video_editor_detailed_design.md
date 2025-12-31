# 视频编辑模块详细设计文档 v1.0

> **文档类型**: 详细设计文档 (Detailed Design Document)
> **创建日期**: 2025-11-29
> **适用项目**: AI 视频创作平台 - 视频编辑模块
> **技术栈**: Python FastAPI + React + FFmpeg + MoviePy

---

## 📋 目录

1. [设计目标](#1-设计目标)
2. [系统架构](#2-系统架构)
3. [代码组织结构](#3-代码组织结构)
4. [数据模型设计](#4-数据模型设计)
5. [服务层设计](#5-服务层设计)
6. [API接口设计](#6-api接口设计)
7. [类图与时序图](#7-类图与时序图)
8. [数据库设计](#8-数据库设计)
9. [前端集成方案](#9-前端集成方案)
10. [实施计划](#10-实施计划)

---

## 1. 设计目标

### 1.1 功能目标
- ✅ 为 AI 生成的视频提供后期编辑能力
- ✅ 支持多轨道时间轴编辑
- ✅ 支持字幕自动生成和编辑
- ✅ 支持模板库功能
- ✅ 与现有 AI 视频生成模块无缝集成

### 1.2 技术目标
- ✅ 复用现有项目架构（FastAPI + Pydantic + SQLAlchemy）
- ✅ 服务器端渲染（不依赖浏览器）
- ✅ 模块化设计，便于扩展
- ✅ 高性能（支持并发处理）

### 1.3 非功能目标
- ✅ 代码质量：遵循 Python PEP 8 规范
- ✅ 可维护性：清晰的模块划分和文档
- ✅ 可测试性：每个服务都有单元测试
- ✅ 性能：单个视频渲染时间 < 2倍视频时长

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (React + Vite)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Timeline UI  │  │ Preview Panel│  │ Properties   │      │
│  │ (时间轴编辑) │  │ (预览播放器) │  │ (属性编辑)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JSON)
┌────────────────────────▼────────────────────────────────────┐
│                  API 层 (FastAPI Routes)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /api/editor/*  - 编辑器相关接口                      │   │
│  │  - POST   /editor/projects          创建编辑项目      │   │
│  │  - GET    /editor/projects/:id      获取项目         │   │
│  │  - POST   /editor/render            渲染时间轴       │   │
│  │  - POST   /editor/subtitle/generate 生成字幕         │   │
│  │  - GET    /editor/templates         获取模板列表     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   服务层 (Business Logic)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Timeline     │  │ Subtitle     │  │ Template     │      │
│  │ Renderer     │  │ Service      │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ FFmpeg       │  │ Project      │  │ Media        │      │
│  │ Service      │  │ Manager      │  │ Manager      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   数据层 (Data Access)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SQLAlchemy   │  │ File Storage │  │ Cache        │      │
│  │ (项目/模板)  │  │ (媒体文件)   │  │ (Redis可选)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              底层工具层 (Infrastructure)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ FFmpeg       │  │ MoviePy      │  │ Whisper      │      │
│  │ (CLI)        │  │ (视频编辑)   │  │ (ASR)        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Pillow       │  │ pysrt        │                        │
│  │ (图像处理)   │  │ (字幕处理)   │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块依赖关系

```
app/api/routes/editor.py
    ↓ 调用
app/services/editor/
    ├── timeline_renderer.py    (时间轴渲染)
    ├── subtitle_service.py     (字幕服务)
    ├── template_service.py     (模板服务)
    ├── project_manager.py      (项目管理)
    └── media_manager.py        (媒体管理)
    ↓ 使用
app/services/video/
    ├── ffmpeg_service.py       (FFmpeg封装)
    └── moviepy_composer.py     (MoviePy封装)
    ↓ 依赖
app/models/editor/
    ├── timeline.py             (时间轴数据模型)
    ├── project.py              (编辑项目模型)
    └── template.py             (模板模型)
```

---

## 3. 代码组织结构

### 3.1 文件布局

**决策：在现有 `app/` 目录下扩展，不创建新文件夹**

理由：
1. ✅ 与现有项目结构一致
2. ✅ 复用现有的配置、数据库连接
3. ✅ 避免重复代码

```
video_creator_platform/
├── app/
│   ├── models/
│   │   ├── editor/              # 新增：编辑器数据模型
│   │   │   ├── __init__.py
│   │   │   ├── timeline.py      # Timeline, Track, Element
│   │   │   ├── project.py       # EditorProject
│   │   │   ├── template.py      # VideoTemplate
│   │   │   └── subtitle.py      # Subtitle 相关
│   │   ├── project.py           # 现有：AI导演项目
│   │   └── ...
│   │
│   ├── services/
│   │   ├── editor/              # 新增：编辑器业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── timeline_renderer.py   # 时间轴渲染器
│   │   │   ├── subtitle_service.py    # 字幕服务
│   │   │   ├── template_service.py    # 模板服务
│   │   │   ├── project_manager.py     # 编辑项目管理
│   │   │   └── media_manager.py       # 媒体文件管理
│   │   │
│   │   ├── video/               # 现有：扩展视频处理
│   │   │   ├── ffmpeg_service.py      # 新增：FFmpeg 封装
│   │   │   ├── moviepy_composer.py    # 新增：MoviePy 封装
│   │   │   ├── manager.py             # 现有
│   │   │   └── ...
│   │   │
│   │   ├── audio/               # 现有：音频处理
│   │   │   ├── tts_service.py         # 现有：TTS
│   │   │   └── asr_service.py         # 现有：ASR (可用于字幕)
│   │   │
│   │   ├── director/            # 现有：AI导演
│   │   └── ...
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── editor.py        # 新增：编辑器API路由
│   │   │   ├── projects.py      # 现有
│   │   │   └── ...
│   │   └── ...
│   │
│   ├── utils/
│   │   ├── database.py          # 现有
│   │   ├── file_utils.py        # 新增：文件工具
│   │   └── video_utils.py       # 新增：视频工具
│   │
│   └── main.py                  # 现有：主应用
│
├── frontend/
│   └── src/
│       ├── components/
│       │   └── editor/          # 新增：从 OpenCut 提取的组件
│       │       ├── Timeline/
│       │       ├── Preview/
│       │       └── Properties/
│       ├── services/
│       │   └── editor-api.ts    # 新增：编辑器 API 客户端
│       └── ...
│
├── tests/
│   └── test_editor/             # 新增：编辑器测试
│       ├── test_timeline_renderer.py
│       ├── test_subtitle_service.py
│       └── test_ffmpeg_service.py
│
└── requirements.txt             # 添加：pysrt
```

### 3.2 命名规范

- **文件名**: 小写 + 下划线 (`timeline_renderer.py`)
- **类名**: 大驼峰 (`TimelineRenderer`)
- **函数名**: 小写 + 下划线 (`render_timeline()`)
- **常量**: 大写 + 下划线 (`MAX_VIDEO_DURATION`)
- **私有方法**: 单下划线前缀 (`_process_track()`)

---

## 4. 数据模型设计

### 4.1 Pydantic 模型（API 请求/响应）

#### 4.1.1 Timeline 数据模型

```python
# app/models/editor/timeline.py
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union
from datetime import datetime
import uuid

# ==================== 枚举类型 ====================
class TrackType(str):
    """轨道类型"""
    MEDIA = "media"
    TEXT = "text"
    AUDIO = "audio"

class ElementType(str):
    """元素类型"""
    MEDIA = "media"
    TEXT = "text"

# ==================== 基础元素 ====================
class BaseTimelineElement(BaseModel):
    """时间轴元素基类"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="元素名称")
    duration: float = Field(..., ge=0, description="持续时间(秒)")
    start_time: float = Field(..., ge=0, description="开始时间(秒)")
    trim_start: float = Field(default=0.0, ge=0, description="修剪开始(秒)")
    trim_end: float = Field(default=0.0, ge=0, description="修剪结束(秒)")
    hidden: bool = Field(default=False, description="是否隐藏")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "elem_123",
                "name": "视频片段1",
                "duration": 5.0,
                "start_time": 0.0,
                "trim_start": 0.5,
                "trim_end": 0.0,
                "hidden": False
            }
        }

class MediaElement(BaseTimelineElement):
    """媒体元素（视频/图片）"""
    type: Literal["media"] = "media"
    media_id: str = Field(..., description="媒体文件ID或路径")
    media_url: Optional[str] = Field(None, description="媒体URL")
    muted: bool = Field(default=False, description="是否静音")

    # 可选的视觉效果
    opacity: float = Field(default=1.0, ge=0, le=1, description="透明度")
    volume: float = Field(default=1.0, ge=0, le=2, description="音量")
    speed: float = Field(default=1.0, gt=0, le=4, description="播放速度")

class TextElement(BaseTimelineElement):
    """文字元素"""
    type: Literal["text"] = "text"
    content: str = Field(..., description="文字内容")

    # 文字样式
    font_size: int = Field(default=40, ge=8, le=200, description="字体大小")
    font_family: str = Field(default="Arial", description="字体")
    color: str = Field(default="#FFFFFF", description="文字颜色(HEX)")
    background_color: Optional[str] = Field(None, description="背景颜色(HEX)")

    # 文字对齐和装饰
    text_align: Literal["left", "center", "right"] = Field(default="center")
    font_weight: Literal["normal", "bold"] = Field(default="normal")
    font_style: Literal["normal", "italic"] = Field(default="normal")
    text_decoration: Literal["none", "underline", "line-through"] = Field(default="none")

    # 位置和变换
    x: int = Field(default=0, description="X坐标(相对画布中心)")
    y: int = Field(default=0, description="Y坐标(相对画布中心)")
    rotation: float = Field(default=0.0, description="旋转角度(度)")
    opacity: float = Field(default=1.0, ge=0, le=1, description="透明度")

    # 可选：描边
    stroke_color: Optional[str] = Field(None, description="描边颜色")
    stroke_width: int = Field(default=0, ge=0, description="描边宽度")

# Union 类型
TimelineElement = Union[MediaElement, TextElement]

# ==================== 轨道 ====================
class TimelineTrack(BaseModel):
    """时间轴轨道"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="轨道名称")
    type: Literal["media", "text", "audio"] = Field(..., description="轨道类型")
    elements: List[TimelineElement] = Field(default_factory=list, description="轨道元素列表")
    muted: bool = Field(default=False, description="是否静音")
    is_main: bool = Field(default=False, description="是否为主轨道")

    # 可选：轨道级别效果
    volume: float = Field(default=1.0, ge=0, le=2, description="轨道音量")
    locked: bool = Field(default=False, description="是否锁定")

# ==================== 时间轴 ====================
class Timeline(BaseModel):
    """完整时间轴"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(default="未命名时间轴", description="时间轴名称")
    tracks: List[TimelineTrack] = Field(default_factory=list, description="轨道列表")

    # 画布设置
    canvas_width: int = Field(default=1920, ge=640, le=7680, description="画布宽度")
    canvas_height: int = Field(default=1080, ge=360, le=4320, description="画布高度")
    fps: int = Field(default=30, ge=24, le=120, description="帧率")
    background_color: str = Field(default="#000000", description="背景颜色")

    # 时间轴设置
    duration: float = Field(default=0.0, ge=0, description="总时长(秒，自动计算)")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def calculate_duration(self) -> float:
        """计算时间轴总时长"""
        max_end_time = 0.0
        for track in self.tracks:
            for element in track.elements:
                end_time = element.start_time + element.duration
                max_end_time = max(max_end_time, end_time)
        self.duration = max_end_time
        return max_end_time
```

#### 4.1.2 编辑项目模型

```python
# app/models/editor/project.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

class EditorProjectStatus(str, Enum):
    """编辑项目状态"""
    DRAFT = "draft"           # 草稿
    EDITING = "editing"       # 编辑中
    RENDERING = "rendering"   # 渲染中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败

class EditorProject(BaseModel):
    """视频编辑项目"""
    id: str = Field(default_factory=lambda: f"editor_{uuid.uuid4()}")
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")

    # 时间轴关联
    timeline_id: Optional[str] = Field(None, description="关联的时间轴ID")
    timeline: Optional[Timeline] = Field(None, description="完整的时间轴数据")

    # 项目状���
    status: EditorProjectStatus = Field(default=EditorProjectStatus.DRAFT)

    # 输出设置
    output_path: Optional[str] = Field(None, description="最终视频路径")
    output_format: str = Field(default="mp4", description="输出格式")
    output_quality: str = Field(default="high", description="输出质量: low/medium/high")

    # 关联到 AI 生成项目（可选）
    source_ai_project_id: Optional[str] = Field(None, description="源AI项目ID")

    # 元数据
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    duration: float = Field(default=0.0, description="总时长(秒)")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
```

#### 4.1.3 字幕模型

```python
# app/models/editor/subtitle.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SubtitleSegment(BaseModel):
    """单个字幕片段"""
    index: int = Field(..., description="字幕序号")
    start_time: float = Field(..., ge=0, description="开始时间(秒)")
    end_time: float = Field(..., gt=0, description="结束时间(秒)")
    text: str = Field(..., min_length=1, description="字幕文本")

    # 可选：样式覆盖
    font_size: Optional[int] = Field(None, description="字体大小")
    color: Optional[str] = Field(None, description="文字颜色")

class SubtitleFile(BaseModel):
    """字幕文件"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = Field(..., description="所属项目ID")
    language: str = Field(default="zh-CN", description="语言代码")
    segments: List[SubtitleSegment] = Field(default_factory=list)

    # 全局样式
    default_font_size: int = Field(default=40)
    default_color: str = Field(default="#FFFFFF")
    default_position: str = Field(default="bottom", description="位置: top/center/bottom")

    created_at: datetime = Field(default_factory=datetime.now)
    srt_file_path: Optional[str] = Field(None, description="SRT文件路径")
```

#### 4.1.4 模板模型

```python
# app/models/editor/template.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class TemplateCategory(str):
    """模板分类"""
    INTRO = "intro"                 # 片头
    OUTRO = "outro"                 # 片尾
    TRANSITION = "transition"       # 转场
    LOWER_THIRD = "lower_third"     # 下三分屏
    FULL_VIDEO = "full_video"       # 完整视频模板

class VideoTemplate(BaseModel):
    """视频模板"""
    id: str = Field(default_factory=lambda: f"tmpl_{uuid.uuid4()}")
    name: str = Field(..., description="模板名称")
    description: str = Field(default="", description="模板描述")
    category: str = Field(..., description="模板分类")

    # 模板预览
    thumbnail_url: str = Field(..., description="缩略图URL")
    preview_video_url: Optional[str] = Field(None, description="预览视频URL")

    # 模板内容（核心）
    timeline_template: Timeline = Field(..., description="时间轴模板")

    # 可替换的占位符
    placeholders: Dict[str, Any] = Field(
        default_factory=dict,
        description="占位符定义 {placeholder_id: {type, name, default}}"
    )

    # 标签和元数据
    tags: List[str] = Field(default_factory=list, description="标签")
    duration: float = Field(..., description="模板时长(秒)")
    aspect_ratio: str = Field(default="16:9", description="宽高比")

    # 使用统计
    usage_count: int = Field(default=0, description="使用次数")

    # 是否公开
    is_public: bool = Field(default=True, description="是否公开")
    author: Optional[str] = Field(None, description="作者")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### 4.2 SQLAlchemy 数据库模型

```python
# app/utils/database.py (扩展现有文件)
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class EditorProjectDB(Base):
    """编辑项目数据库模型"""
    __tablename__ = "editor_projects"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # JSON 存储时间轴数据
    timeline_json = Column(JSON, nullable=True)

    status = Column(String(20), default="draft")

    # 输出设置
    output_path = Column(String(500), nullable=True)
    output_format = Column(String(10), default="mp4")
    output_quality = Column(String(20), default="high")

    # 关联
    source_ai_project_id = Column(String(100), nullable=True)

    # 元数据
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Float, default=0.0)
    file_size = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    subtitles = relationship("SubtitleFileDB", back_populates="project", cascade="all, delete-orphan")

class SubtitleFileDB(Base):
    """字幕文件数据库模型"""
    __tablename__ = "subtitle_files"

    id = Column(String(100), primary_key=True)
    project_id = Column(String(100), ForeignKey("editor_projects.id"), nullable=False)
    language = Column(String(10), default="zh-CN")

    # JSON 存储字幕片段
    segments_json = Column(JSON, nullable=False)

    # 全局样式
    default_font_size = Column(Integer, default=40)
    default_color = Column(String(20), default="#FFFFFF")
    default_position = Column(String(20), default="bottom")

    created_at = Column(DateTime, default=datetime.now)
    srt_file_path = Column(String(500), nullable=True)

    # 关系
    project = relationship("EditorProjectDB", back_populates="subtitles")

class VideoTemplateDB(Base):
    """视频模板数据库模型"""
    __tablename__ = "video_templates"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), nullable=False)

    thumbnail_url = Column(String(500), nullable=False)
    preview_video_url = Column(String(500), nullable=True)

    # JSON 存储模板时间轴
    timeline_template_json = Column(JSON, nullable=False)
    placeholders_json = Column(JSON, default={})

    tags = Column(JSON, default=[])
    duration = Column(Float, nullable=False)
    aspect_ratio = Column(String(20), default="16:9")

    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    author = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

---

## 5. 服务层设计

### 5.1 核心服务类

#### 5.1.1 TimelineRenderer (时间轴渲染器)

```python
# app/services/editor/timeline_renderer.py
from pathlib import Path
from typing import Optional
from app.models.editor.timeline import Timeline, TimelineTrack, MediaElement, TextElement
from app.services.video.ffmpeg_service import FFmpegService
from app.services.video.moviepy_composer import MoviePyComposer
import logging

logger = logging.getLogger(__name__)

class TimelineRenderer:
    """时间轴渲染器 - 核心渲染引擎"""

    def __init__(self):
        self.ffmpeg_service = FFmpegService()
        self.moviepy_composer = MoviePyComposer()

    async def render(
        self,
        timeline: Timeline,
        output_path: Path,
        quality: str = "high",
        on_progress: Optional[callable] = None
    ) -> Path:
        """
        渲染时间轴为最终视频

        Args:
            timeline: 时间轴对象
            output_path: 输出路径
            quality: 质量设置 (low/medium/high)
            on_progress: 进度回调函数 (progress: float) -> None

        Returns:
            Path: 最终视频路径

        Raises:
            ValueError: 时间轴数据无效
            RuntimeError: 渲染失败
        """
        logger.info(f"开始渲染时间轴: {timeline.name}")

        # 1. 验证时间轴
        self._validate_timeline(timeline)

        # 2. 准备渲染环境
        temp_dir = await self._prepare_render_environment(timeline)

        # 3. 按轨道分别处理
        track_outputs = []
        for track in timeline.tracks:
            if track.type == "media":
                track_video = await self._render_media_track(track, timeline, temp_dir)
                track_outputs.append(track_video)
            elif track.type == "text":
                # 文字轨道稍后叠加
                pass

        # 4. 合成所有轨道
        merged_video = await self._merge_tracks(track_outputs, timeline, temp_dir)

        # 5. 叠加文字轨道
        if self._has_text_tracks(timeline):
            final_video = await self._overlay_text_tracks(merged_video, timeline, temp_dir)
        else:
            final_video = merged_video

        # 6. 应用最终设置并导出
        final_output = await self._finalize_output(
            final_video,
            output_path,
            timeline,
            quality
        )

        # 7. 清理临时文件
        await self._cleanup(temp_dir)

        logger.info(f"渲染完成: {final_output}")
        return final_output

    def _validate_timeline(self, timeline: Timeline):
        """验证时间轴数据"""
        if not timeline.tracks:
            raise ValueError("时间轴至少需要一个轨道")

        # 检查元素重叠
        for track in timeline.tracks:
            self._check_overlaps(track)

    def _check_overlaps(self, track: TimelineTrack):
        """检查元素重叠"""
        elements = sorted(track.elements, key=lambda e: e.start_time)
        for i in range(len(elements) - 1):
            current_end = elements[i].start_time + elements[i].duration
            next_start = elements[i + 1].start_time
            if current_end > next_start:
                logger.warning(
                    f"检测到元素重叠: {elements[i].name} 和 {elements[i+1].name}"
                )

    async def _render_media_track(
        self,
        track: TimelineTrack,
        timeline: Timeline,
        temp_dir: Path
    ) -> Path:
        """渲染媒体轨道"""
        # 使用 MoviePy 组合器
        return await self.moviepy_composer.compose_media_track(
            track,
            timeline.canvas_width,
            timeline.canvas_height,
            timeline.fps,
            temp_dir
        )

    async def _merge_tracks(
        self,
        track_videos: list[Path],
        timeline: Timeline,
        temp_dir: Path
    ) -> Path:
        """合并多个轨道"""
        if len(track_videos) == 1:
            return track_videos[0]

        # 使用 FFmpeg 叠加
        return await self.ffmpeg_service.overlay_videos(
            track_videos,
            temp_dir / "merged.mp4"
        )

    async def _overlay_text_tracks(
        self,
        base_video: Path,
        timeline: Timeline,
        temp_dir: Path
    ) -> Path:
        """叠加文字轨道"""
        text_tracks = [t for t in timeline.tracks if t.type == "text"]

        return await self.moviepy_composer.add_text_overlays(
            base_video,
            text_tracks,
            temp_dir / "with_text.mp4"
        )

    async def _finalize_output(
        self,
        video: Path,
        output_path: Path,
        timeline: Timeline,
        quality: str
    ) -> Path:
        """最终输出"""
        codec_params = self._get_quality_params(quality)

        return await self.ffmpeg_service.transcode(
            video,
            output_path,
            **codec_params
        )

    def _get_quality_params(self, quality: str) -> dict:
        """获取质量参数"""
        quality_presets = {
            "low": {"crf": 28, "preset": "fast"},
            "medium": {"crf": 23, "preset": "medium"},
            "high": {"crf": 18, "preset": "slow"}
        }
        return quality_presets.get(quality, quality_presets["medium"])
```

#### 5.1.2 SubtitleService (字幕服务)

```python
# app/services/editor/subtitle_service.py
import whisper
import pysrt
from pathlib import Path
from typing import List, Optional
from app.models.editor.subtitle import SubtitleFile, SubtitleSegment
from app.services.video.ffmpeg_service import FFmpegService
from app.services.video.moviepy_composer import MoviePyComposer
import logging

logger = logging.getLogger(__name__)

class SubtitleService:
    """字幕服务 - 自动生成和管理字幕"""

    def __init__(self, whisper_model: str = "base"):
        """
        初始化字幕服务

        Args:
            whisper_model: Whisper 模型大小 (tiny/base/small/medium/large)
        """
        self.whisper_model = whisper.load_model(whisper_model)
        self.ffmpeg_service = FFmpegService()
        self.moviepy_composer = MoviePyComposer()

    async def generate_auto_subtitles(
        self,
        video_path: Path,
        project_id: str,
        language: str = "zh",
        max_chars_per_line: int = 20
    ) -> SubtitleFile:
        """
        自动生成字幕

        Args:
            video_path: 视频文件路径
            project_id: 项目ID
            language: 语言代码
            max_chars_per_line: 每行最大字符数

        Returns:
            SubtitleFile: 生成的字幕文件对象
        """
        logger.info(f"开始为视频生成字幕: {video_path}")

        # 1. 使用 Whisper 转录
        result = self.whisper_model.transcribe(
            str(video_path),
            language=language,
            verbose=False
        )

        # 2. 转换为字幕片段
        segments = []
        for i, seg in enumerate(result['segments'], 1):
            text = seg['text'].strip()

            # 处理长文本（简单换行）
            if len(text) > max_chars_per_line:
                text = self._split_text(text, max_chars_per_line)

            segments.append(SubtitleSegment(
                index=i,
                start_time=seg['start'],
                end_time=seg['end'],
                text=text
            ))

        # 3. 创建字幕文件对象
        subtitle_file = SubtitleFile(
            project_id=project_id,
            language=language,
            segments=segments
        )

        logger.info(f"字幕生成完成，共 {len(segments)} 个片段")
        return subtitle_file

    def _split_text(self, text: str, max_chars: int) -> str:
        """智能分割文本"""
        if len(text) <= max_chars:
            return text

        # 简单实现：在中间分割
        mid = len(text) // 2
        # 尝试在标点符号处分割
        for i in range(mid - 5, mid + 5):
            if i < len(text) and text[i] in "，。！？,.:!?":
                return f"{text[:i+1]}\n{text[i+1:]}"

        # 否则直接中间分割
        return f"{text[:mid]}\n{text[mid:]}"

    async def export_srt(
        self,
        subtitle_file: SubtitleFile,
        output_path: Path
    ) -> Path:
        """
        导出为 SRT 文件

        Args:
            subtitle_file: 字幕文件对象
            output_path: 输出路径

        Returns:
            Path: SRT 文件路径
        """
        subs = pysrt.SubRipFile()

        for seg in subtitle_file.segments:
            item = pysrt.SubRipItem(
                index=seg.index,
                start=pysrt.SubRipTime(seconds=seg.start_time),
                end=pysrt.SubRipTime(seconds=seg.end_time),
                text=seg.text
            )
            subs.append(item)

        subs.save(str(output_path), encoding='utf-8')
        logger.info(f"SRT 文件已导出: {output_path}")
        return output_path

    async def import_srt(
        self,
        srt_path: Path,
        project_id: str
    ) -> SubtitleFile:
        """
        导入 SRT 文件

        Args:
            srt_path: SRT 文件路径
            project_id: 项目ID

        Returns:
            SubtitleFile: 字幕文件对象
        """
        subs = pysrt.open(str(srt_path), encoding='utf-8')

        segments = [
            SubtitleSegment(
                index=sub.index,
                start_time=sub.start.ordinal / 1000.0,
                end_time=sub.end.ordinal / 1000.0,
                text=sub.text
            )
            for sub in subs
        ]

        return SubtitleFile(
            project_id=project_id,
            segments=segments,
            srt_file_path=str(srt_path)
        )

    async def burn_subtitles(
        self,
        video_path: Path,
        subtitle_file: SubtitleFile,
        output_path: Path,
        style: Optional[dict] = None
    ) -> Path:
        """
        烧录字幕到视频（硬字幕）

        Args:
            video_path: 输入视频
            subtitle_file: 字幕文件
            output_path: 输出路径
            style: 字幕样式 {font_size, color, position, ...}

        Returns:
            Path: 带字幕的视频路径
        """
        if style is None:
            style = {
                'font_size': subtitle_file.default_font_size,
                'color': subtitle_file.default_color,
                'position': subtitle_file.default_position
            }

        return await self.moviepy_composer.add_subtitles(
            video_path,
            subtitle_file,
            output_path,
            style
        )
```

### 5.2 工具服务类

#### 5.2.1 FFmpegService

```python
# app/services/video/ffmpeg_service.py
import ffmpeg
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FFmpegService:
    """FFmpeg 服务封装"""

    async def generate_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        time_seconds: float = 1.0,
        width: int = 320,
        height: int = 240
    ) -> Path:
        """生成视频缩略图"""
        try:
            (
                ffmpeg
                .input(str(video_path), ss=time_seconds)
                .filter('scale', width, height)
                .output(str(output_path), vframes=1, q=2)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            logger.info(f"缩略图生成成功: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"生成缩略图失败: {e.stderr.decode()}")
            raise RuntimeError(f"生成缩略图失败: {e.stderr.decode()}")

    async def trim_video(
        self,
        input_path: Path,
        output_path: Path,
        start_time: float,
        duration: float
    ) -> Path:
        """裁剪视频"""
        try:
            (
                ffmpeg
                .input(str(input_path), ss=start_time, t=duration)
                .output(str(output_path), c='copy')  # 流复制，更快
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"裁剪视频失败: {e.stderr.decode()}")

    async def merge_videos(
        self,
        video_paths: List[Path],
        output_path: Path
    ) -> Path:
        """合并多个视频"""
        concat_file = output_path.parent / "concat_list.txt"

        try:
            # 创建 concat 文件
            with open(concat_file, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{video_path.absolute()}'\n")

            # 合并
            (
                ffmpeg
                .input(str(concat_file), format='concat', safe=0)
                .output(str(output_path), c='copy')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )

            concat_file.unlink()
            return output_path
        except ffmpeg.Error as e:
            concat_file.unlink(missing_ok=True)
            raise RuntimeError(f"合并视频失败: {e.stderr.decode()}")

    async def extract_audio(
        self,
        video_path: Path,
        output_path: Path
    ) -> Path:
        """提取音频"""
        try:
            (
                ffmpeg
                .input(str(video_path))
                .output(str(output_path), acodec='aac', vn=None)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"提取音频失败: {e.stderr.decode()}")

    async def overlay_videos(
        self,
        video_paths: List[Path],
        output_path: Path
    ) -> Path:
        """叠加多个视频（画中画）"""
        if len(video_paths) < 2:
            raise ValueError("至少需要2个视频")

        try:
            inputs = [ffmpeg.input(str(p)) for p in video_paths]

            # 构建叠加滤镜链
            overlay = inputs[0]
            for i in range(1, len(inputs)):
                overlay = overlay.overlay(inputs[i])

            (
                overlay
                .output(str(output_path), vcodec='libx264', acodec='aac')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )

            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"视频叠加失败: {e.stderr.decode()}")

    async def transcode(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs
    ) -> Path:
        """
        转码视频

        Args:
            input_path: 输入路径
            output_path: 输出路径
            **kwargs: FFmpeg 参数 (crf, preset, vcodec, acodec, etc.)
        """
        try:
            (
                ffmpeg
                .input(str(input_path))
                .output(str(output_path), **kwargs)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"转码失败: {e.stderr.decode()}")
```

---

## 6. API接口设计

### 6.1 RESTful API 端点

```python
# app/api/routes/editor.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
from pathlib import Path

from app.models.editor.timeline import Timeline
from app.models.editor.project import EditorProject, EditorProjectStatus
from app.models.editor.subtitle import SubtitleFile
from app.models.editor.template import VideoTemplate

from app.services.editor.timeline_renderer import TimelineRenderer
from app.services.editor.subtitle_service import SubtitleService
from app.services.editor.template_service import TemplateService
from app.services.editor.project_manager import EditorProjectManager

router = APIRouter(prefix="/api/editor", tags=["视频编辑器"])

# 初始化服务
timeline_renderer = TimelineRenderer()
subtitle_service = SubtitleService()
template_service = TemplateService()
project_manager = EditorProjectManager()

# ==================== 项目管理 ====================

@router.post("/projects", response_model=EditorProject, status_code=201)
async def create_project(project: EditorProject):
    """
    创建新的编辑项目

    **请求体**:
    ```json
    {
      "name": "我的视频项目",
      "description": "项目描述",
      "timeline": {
        "tracks": [...],
        "canvas_width": 1920,
        "canvas_height": 1080
      }
    }
    ```
    """
    return await project_manager.create_project(project)

@router.get("/projects/{project_id}", response_model=EditorProject)
async def get_project(project_id: str):
    """获取项目详情"""
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project

@router.get("/projects", response_model=List[EditorProject])
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None
):
    """列出所有项目"""
    return await project_manager.list_projects(skip, limit, status)

@router.put("/projects/{project_id}", response_model=EditorProject)
async def update_project(project_id: str, project: EditorProject):
    """更新项目"""
    return await project_manager.update_project(project_id, project)

@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: str):
    """删除项目"""
    await project_manager.delete_project(project_id)
    return None

# ==================== 时间轴渲染 ====================

@router.post("/render", status_code=202)
async def render_timeline(
    background_tasks: BackgroundTasks,
    project_id: str,
    quality: str = "high"
):
    """
    渲染时间轴（异步任务）

    **参数**:
    - project_id: 项目ID
    - quality: 质量 (low/medium/high)

    **响应**:
    ```json
    {
      "task_id": "render_abc123",
      "status": "queued",
      "message": "渲染任务已加入队列"
    }
    ```
    """
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not project.timeline:
        raise HTTPException(status_code=400, detail="项目没有时间轴数据")

    # 创建后台任务
    task_id = f"render_{project_id}"
    background_tasks.add_task(
        _render_task,
        project,
        quality,
        task_id
    )

    return {
        "task_id": task_id,
        "status": "queued",
        "message": "渲染任务已加入队列"
    }

async def _render_task(project: EditorProject, quality: str, task_id: str):
    """后台渲染任务"""
    try:
        # 更新项目状态
        await project_manager.update_status(project.id, EditorProjectStatus.RENDERING)

        # 渲染
        output_path = Path(f"output/editor/{project.id}/final.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = await timeline_renderer.render(
            timeline=project.timeline,
            output_path=output_path,
            quality=quality
        )

        # 更新项目
        project.output_path = str(result)
        project.status = EditorProjectStatus.COMPLETED
        await project_manager.update_project(project.id, project)

    except Exception as e:
        await project_manager.update_status(project.id, EditorProjectStatus.FAILED)
        logger.error(f"渲染失败: {e}")

@router.get("/render/status/{task_id}")
async def get_render_status(task_id: str):
    """查询渲染状态"""
    # TODO: 实现任务状态跟踪
    return {"task_id": task_id, "status": "processing", "progress": 50}

@router.get("/render/download/{project_id}")
async def download_rendered_video(project_id: str):
    """下载渲染完成的视频"""
    project = await project_manager.get_project(project_id)
    if not project or not project.output_path:
        raise HTTPException(status_code=404, detail="视频不存在")

    video_path = Path(project.output_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"{project.name}.mp4"
    )

# ==================== 字幕功能 ====================

@router.post("/subtitle/generate", response_model=SubtitleFile, status_code=201)
async def generate_subtitle(
    project_id: str,
    video_file: UploadFile = File(...),
    language: str = "zh"
):
    """
    自动生成字幕

    **参数**:
    - project_id: 项目ID
    - video_file: 视频文件
    - language: 语言代码 (zh/en/ja/...)
    """
    # 保存上传的视频
    video_path = Path(f"temp/{project_id}_{video_file.filename}")
    video_path.parent.mkdir(parents=True, exist_ok=True)

    with open(video_path, "wb") as f:
        content = await video_file.read()
        f.write(content)

    # 生成字幕
    subtitle_file = await subtitle_service.generate_auto_subtitles(
        video_path,
        project_id,
        language
    )

    # 保存到数据库
    await project_manager.save_subtitle(subtitle_file)

    # 清理临时文件
    video_path.unlink()

    return subtitle_file

@router.get("/subtitle/{project_id}", response_model=List[SubtitleFile])
async def get_subtitles(project_id: str):
    """获取项目的所有字幕"""
    return await project_manager.get_subtitles(project_id)

@router.get("/subtitle/{subtitle_id}/srt")
async def export_subtitle_srt(subtitle_id: str):
    """导出 SRT 文件"""
    subtitle = await project_manager.get_subtitle(subtitle_id)
    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")

    srt_path = Path(f"output/subtitles/{subtitle_id}.srt")
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    await subtitle_service.export_srt(subtitle, srt_path)

    return FileResponse(
        srt_path,
        media_type="application/x-subrip",
        filename=f"subtitle_{subtitle_id}.srt"
    )

# ==================== 模板功能 ====================

@router.get("/templates", response_model=List[VideoTemplate])
async def list_templates(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取模板列表"""
    return await template_service.list_templates(category, skip, limit)

@router.get("/templates/{template_id}", response_model=VideoTemplate)
async def get_template(template_id: str):
    """获取模板详情"""
    template = await template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template

@router.post("/templates/{template_id}/apply", response_model=EditorProject)
async def apply_template(
    template_id: str,
    project_name: str,
    placeholders: dict
):
    """
    应用模板创建项目

    **请求体**:
    ```json
    {
      "project_name": "新项目",
      "placeholders": {
        "text_1": "标题文字",
        "video_1": "media_id_123"
      }
    }
    ```
    """
    template = await template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 应用模板
    project = await template_service.apply_template(
        template,
        project_name,
        placeholders
    )

    # 保存项目
    return await project_manager.create_project(project)
```

### 6.2 请求/响应示例

#### 示例1: 创建编辑项目

**请求**:
```http
POST /api/editor/projects
Content-Type: application/json

{
  "name": "我的第一个视频",
  "description": "测试项目",
  "timeline": {
    "name": "主时间轴",
    "tracks": [
      {
        "name": "视频轨道1",
        "type": "media",
        "elements": [
          {
            "type": "media",
            "name": "开场视频",
            "media_id": "video_001.mp4",
            "duration": 10.0,
            "start_time": 0.0,
            "trim_start": 0.0,
            "trim_end": 0.0
          }
        ]
      },
      {
        "name": "文字轨道",
        "type": "text",
        "elements": [
          {
            "type": "text",
            "name": "标题",
            "content": "欢迎观看",
            "duration": 5.0,
            "start_time": 2.0,
            "font_size": 60,
            "color": "#FFFFFF",
            "x": 0,
            "y": -200
          }
        ]
      }
    ],
    "canvas_width": 1920,
    "canvas_height": 1080,
    "fps": 30
  }
}
```

**响应**:
```json
{
  "id": "editor_abc123",
  "name": "我的第一个视频",
  "description": "测试项目",
  "timeline_id": "timeline_xyz789",
  "status": "draft",
  "output_format": "mp4",
  "output_quality": "high",
  "duration": 10.0,
  "created_at": "2024-11-28T10:00:00Z",
  "updated_at": "2024-11-28T10:00:00Z"
}
```

#### 示例2: 自动生成字幕

**请求**:
```http
POST /api/editor/subtitle/generate
Content-Type: multipart/form-data

project_id=editor_abc123
language=zh
video_file=<binary data>
```

**响应**:
```json
{
  "id": "sub_def456",
  "project_id": "editor_abc123",
  "language": "zh-CN",
  "segments": [
    {
      "index": 1,
      "start_time": 0.0,
      "end_time": 2.5,
      "text": "大家好，欢迎来到这个视频"
    },
    {
      "index": 2,
      "start_time": 2.5,
      "end_time": 5.0,
      "text": "今天我们来讨论一个有趣的话题"
    }
  ],
  "default_font_size": 40,
  "default_color": "#FFFFFF",
  "default_position": "bottom",
  "created_at": "2024-11-28T10:05:00Z"
}
```

---

## 7. 类图与时序图

### 7.1 核心类图

```
┌─────────────────────────────────────────────────────────────┐
│                     TimelineRenderer                        │
├─────────────────────────────────────────────────────────────┤
│ - ffmpeg_service: FFmpegService                             │
│ - moviepy_composer: MoviePyComposer                         │
├─────────────────────────────────────────────────────────────┤
│ + render(timeline, output_path, quality) → Path             │
│ - _validate_timeline(timeline) → None                       │
│ - _render_media_track(track, timeline, temp_dir) → Path     │
│ - _merge_tracks(videos, timeline, temp_dir) → Path          │
│ - _overlay_text_tracks(video, timeline, temp_dir) → Path    │
│ - _finalize_output(video, output, timeline, quality) → Path │
└─────────────────────────────────────────────────────────────┘
                      │ uses
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      FFmpegService                          │
├─────────────────────────────────────────────────────────────┤
│ + generate_thumbnail(...) → Path                            │
│ + trim_video(...) → Path                                    │
│ + merge_videos(...) → Path                                  │
│ + extract_audio(...) → Path                                 │
│ + overlay_videos(...) → Path                                │
│ + transcode(...) → Path                                     │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 渲染流程时序图

```
用户       API        ProjectManager    TimelineRenderer    FFmpegService    MoviePyComposer    文件系统
 │          │                │                 │                  │                 │              │
 ├─渲染请求→│                │                 │                  │                 │              │
 │          ├─获取项目────→│                 │                  │                 │              │
 │          │←─────项目数据─┤                 │                  │                 │              │
 │          ├─更新状态(RENDERING)             │                  │                 │              │
 │          │                │                 │                  │                 │              │
 │          ├─调用render────────────────→│                  │                 │              │
 │          │                │                 ├─验证时间轴─────→│                 │              │
 │          │                │                 ├─处理媒体轨道────────────────────→│              │
 │          │                │                 │                  │                 ├─读取视频──→│
 │          │                │                 │                  │                 ├─裁剪/合成────│
 │          │                │                 │                  │                 ├─写入临时文件→│
 │          │                │                 │←─────────────────────────轨道视频─┤              │
 │          │                │                 │                  │                 │              │
 │          │                │                 ├─合并多轨道──────→│                 │              │
 │          │                │                 │                  ├─ffmpeg overlay──────────────→│
 │          │                │                 │←─────合并视频────┤                 │              │
 │          │                │                 │                  │                 │              │
 │          │                │                 ├─叠加文字────────────────────────→│              │
 │          │                │                 │                  │                 ├─TextClip────→│
 │          │                │                 │←─────────────────────────最终视频─┤              │
 │          │                │                 │                  │                 │              │
 │          │                │                 ├─转码/优化───────→│                 │              │
 │          │                │                 │                  ├─ffmpeg transcode────────────→│
 │          │                │                 │←─────最终输出────┤                 │              │
 │          │←────────────渲染完成──────────┤                  │                 │              │
 │          ├─更新项目(COMPLETED)             │                  │                 │              │
 │←─响应───┤                │                 │                  │                 │              │
```

---

## 8. 数据库设计

### 8.1 数据库表结构

```sql
-- 编辑项目表
CREATE TABLE editor_projects (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    timeline_json JSON,
    status VARCHAR(20) DEFAULT 'draft',
    output_path VARCHAR(500),
    output_format VARCHAR(10) DEFAULT 'mp4',
    output_quality VARCHAR(20) DEFAULT 'high',
    source_ai_project_id VARCHAR(100),
    thumbnail_url VARCHAR(500),
    duration FLOAT DEFAULT 0.0,
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (source_ai_project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- 字幕文件表
CREATE TABLE subtitle_files (
    id VARCHAR(100) PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL,
    language VARCHAR(10) DEFAULT 'zh-CN',
    segments_json JSON NOT NULL,
    default_font_size INT DEFAULT 40,
    default_color VARCHAR(20) DEFAULT '#FFFFFF',
    default_position VARCHAR(20) DEFAULT 'bottom',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    srt_file_path VARCHAR(500),

    FOREIGN KEY (project_id) REFERENCES editor_projects(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id)
);

-- 视频模板表
CREATE TABLE video_templates (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    thumbnail_url VARCHAR(500) NOT NULL,
    preview_video_url VARCHAR(500),
    timeline_template_json JSON NOT NULL,
    placeholders_json JSON,
    tags JSON,
    duration FLOAT NOT NULL,
    aspect_ratio VARCHAR(20) DEFAULT '16:9',
    usage_count INT DEFAULT 0,
    is_public BOOLEAN DEFAULT TRUE,
    author VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_category (category),
    INDEX idx_is_public (is_public),
    FULLTEXT INDEX idx_name_desc (name, description)
);
```

### 8.2 数据库初始化脚本

```python
# app/utils/database.py (扩展)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 创建表
def init_editor_db():
    """初始化编辑器数据库表"""
    from app.utils.database import engine, Base
    from app.models.editor import (
        EditorProjectDB,
        SubtitleFileDB,
        VideoTemplateDB
    )

    Base.metadata.create_all(engine, tables=[
        EditorProjectDB.__table__,
        SubtitleFileDB.__table__,
        VideoTemplateDB.__table__
    ])

    print("✅ 编辑器数据库表创建成功")
```

---

## 9. 前端集成方案

### 9.1 React 组件结构

```
frontend/src/components/editor/
├── Timeline/
│   ├── Timeline.tsx              # 时间轴主容器
│   ├── TimelineTrack.tsx         # 轨道组件
│   ├── TimelineElement.tsx       # 元素块组件
│   ├── TimelinePlayhead.tsx      # 播放头
│   └── TimelineControls.tsx      # 控制条
├── Preview/
│   ├── PreviewPanel.tsx          # 预览面板
│   └── VideoPlayer.tsx           # 视频播放器
├── Properties/
│   ├── PropertiesPanel.tsx       # 属性面板
│   ├── MediaProperties.tsx       # 媒体属性
│   └── TextProperties.tsx        # 文字属性
├── Sidebar/
│   ├── MediaLibrary.tsx          # 媒体库
│   ├── Templates.tsx             # 模板库
│   └── Effects.tsx               # 特效库
└── EditorLayout.tsx              # 编辑器布局
```

### 9.2 API 客户端

```typescript
// frontend/src/services/editor-api.ts
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/editor';

export interface Timeline {
  id?: string;
  name: string;
  tracks: TimelineTrack[];
  canvas_width: number;
  canvas_height: number;
  fps: number;
}

export interface EditorProject {
  id?: string;
  name: string;
  description?: string;
  timeline?: Timeline;
  status: string;
}

export class EditorAPI {
  // 项目管理
  static async createProject(project: EditorProject): Promise<EditorProject> {
    const response = await axios.post(`${API_BASE}/projects`, project);
    return response.data;
  }

  static async getProject(projectId: string): Promise<EditorProject> {
    const response = await axios.get(`${API_BASE}/projects/${projectId}`);
    return response.data;
  }

  static async updateProject(
    projectId: string,
    project: EditorProject
  ): Promise<EditorProject> {
    const response = await axios.put(
      `${API_BASE}/projects/${projectId}`,
      project
    );
    return response.data;
  }

  // 渲染
  static async renderTimeline(
    projectId: string,
    quality: string = 'high'
  ): Promise<{ task_id: string }> {
    const response = await axios.post(`${API_BASE}/render`, null, {
      params: { project_id: projectId, quality }
    });
    return response.data;
  }

  // 字幕
  static async generateSubtitle(
    projectId: string,
    videoFile: File,
    language: string = 'zh'
  ): Promise<any> {
    const formData = new FormData();
    formData.append('video_file', videoFile);
    formData.append('project_id', projectId);
    formData.append('language', language);

    const response = await axios.post(
      `${API_BASE}/subtitle/generate`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return response.data;
  }

  // 模板
  static async listTemplates(category?: string): Promise<any[]> {
    const response = await axios.get(`${API_BASE}/templates`, {
      params: { category }
    });
    return response.data;
  }

  static async applyTemplate(
    templateId: string,
    projectName: string,
    placeholders: Record<string, any>
  ): Promise<EditorProject> {
    const response = await axios.post(
      `${API_BASE}/templates/${templateId}/apply`,
      { project_name: projectName, placeholders }
    );
    return response.data;
  }
}
```

---

## 10. 实施计划

### 10.1 开发阶段划分

#### Phase 1: 基础架构（2-3天）
- [x] ✅ 创建数据模型 (`app/models/editor/`)
- [x] ✅ 创建数据库表和迁移
- [x] ✅ 实现 FFmpegService
- [x] ✅ 实现 MoviePyComposer 基础功能
- [x] ✅ 编写单元测试

**验收标准**:
- 所有数据模型通过 Pydantic 验证
- FFmpeg 基础操作可用（裁剪、合并、转码）
- MoviePy 可以合成简单视频

---

#### Phase 2: 核心渲染引擎（3-4天）
- [x] ✅ 实现 TimelineRenderer
- [x] ✅ 支持多轨道渲染
- [x] ✅ 支持文字叠加
- [x] ✅ 支持基础转场
- [x] ✅ 性能优化

**验收标准**:
- 可以渲染包含 3 个轨道的时间轴
- 渲染速度 < 2倍视频时长
- 输出视频质量符合预期

---

#### Phase 3: 字幕功能（2-3天）
- [x] ✅ 集成 Whisper ASR
- [x] ✅ 实现 SubtitleService
- [x] ✅ 支持 SRT 导入/导出
- [x] ✅ 支持硬字幕烧录
- [x] ✅ 字幕样式自定义

**验收标准**:
- 自动识别准确率 > 85%（中文）
- SRT 文件格式正确
- 字幕样式可自定义

---

#### Phase 4: API 接口（2-3天）
- [x] ✅ 实现所有 REST API 端点
- [x] ✅ 添加请求验证和错误处理
- [x] ✅ 实现后台任务队列
- [x] ✅ API 文档（FastAPI 自动生成）
- [x] ✅ 接口测试

**验收标准**:
- 所有 API 通过 Postman 测试
- 错误处理完善
- API 文档完整

---

#### Phase 5: 模板系统（2-3天）
- [x] ✅ 实现 TemplateService
- [x] ✅ 创建基础模板库
- [x] ✅ 模板应用逻辑
- [x] ✅ 模板预览功能

**验收标准**:
- 至少 5 个可用模板
- 模板可以正确应用到项目
- 占位符替换正确

---

#### Phase 6: 前端集成（4-5天）
- [x] ✅ 从 OpenCut 提取 Timeline UI
- [x] ✅ 集成到现有前端
- [x] ✅ 实现预览播放器
- [x] ✅ 属性编辑面板
- [x] ✅ API 客户端

**验收标准**:
- 时间轴可拖拽编辑
- 预览播放流畅
- 与后端 API 正常通信

---

#### Phase 7: 测试与优化（2-3天）
- [x] ✅ 集成测试
- [x] ✅ 性能优化
- [x] ✅ Bug 修复
- [x] ✅ 文档完善

**验收标准**:
- 测试覆盖率 > 80%
- 无已知严重 Bug
- 文档完整

---

### 10.2 总开发时间估算

- **最小可行版本 (MVP)**: 2 周（Phase 1-4）
- **完整功能版本**: 3-4 周（Phase 1-7）

---

## 11. 附录

### 11.1 依赖库清单

```txt
# 新增依赖
pysrt>=1.1.2              # SRT 字幕处理（必需）

# 可选依赖
rembg>=2.0.50             # AI 抠图（如需抠图功能）
ass>=0.5.2                # ASS 高级字幕（可选）
```

### 11.2 配置文件示例

```python
# app/core/config.py (扩展)
class Settings(BaseSettings):
    # ... 现有配置 ...

    # 编辑器配置
    EDITOR_TEMP_DIR: str = "temp/editor"
    EDITOR_OUTPUT_DIR: str = "output/editor"
    EDITOR_MAX_VIDEO_SIZE: int = 500 * 1024 * 1024  # 500MB
    EDITOR_MAX_DURATION: int = 600  # 10分钟

    # Whisper 配置
    WHISPER_MODEL: str = "base"  # tiny/base/small/medium/large

    # 渲染配置
    RENDER_QUALITY_PRESETS: dict = {
        "low": {"crf": 28, "preset": "fast"},
        "medium": {"crf": 23, "preset": "medium"},
        "high": {"crf": 18, "preset": "slow"}
    }
```

### 11.3 错误码定义

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| EDITOR_001 | 项目不存在 | 404 |
| EDITOR_002 | 时间轴数据无效 | 400 |
| EDITOR_003 | 渲染失败 | 500 |
| EDITOR_004 | 字幕生成失败 | 500 |
| EDITOR_005 | 模板不存在 | 404 |
| EDITOR_006 | 文件太大 | 413 |
| EDITOR_007 | 视频时长超限 | 413 |

---

## 12. 总结

本设计文档详细定义了：

1. ✅ **代码组织**: 在现有 `app/` 目录下扩展，不创建新文件夹
2. ✅ **技术栈**: 继续使用 Python FastAPI，添加 `pysrt` 库
3. ✅ **数据模型**: 完整的 Pydantic 模型和 SQLAlchemy 数据库模型
4. ✅ **服务层**: TimelineRenderer、SubtitleService 等核心类设计
5. ✅ **API 接口**: RESTful API 端点和请求/响应格式
6. ✅ **数据库设计**: 表结构和索引设计
7. ✅ **实施计划**: 7 个阶段，2-4 周完成

### 下一步行动

1. **审阅本文档** - 确认所有设计符合需求
2. **创建开发分支** - `git checkout -b feature/video-editor`
3. **开始 Phase 1** - 创建数据模型和基础服务
4. **迭代开发** - 按阶段逐步实现

**准备好开始开发了吗？** 🚀
