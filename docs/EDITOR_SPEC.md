# 视频编辑器技术规范

> 核心技术文档，直接用于开发

---

## 1. 数据模型

### Timeline 数据结构
```python
# app/models/editor/timeline.py

class TimelineElement(BaseModel):
    id: str
    name: str
    duration: float        # 秒
    start_time: float      # 秒
    trim_start: float = 0  # 秒
    trim_end: float = 0    # 秒

class MediaElement(TimelineElement):
    type: Literal["media"] = "media"
    media_id: str          # 文件路径或ID
    muted: bool = False
    volume: float = 1.0
    speed: float = 1.0

class TextElement(TimelineElement):
    type: Literal["text"] = "text"
    content: str
    font_size: int = 40
    font_family: str = "Arial"
    color: str = "#FFFFFF"
    x: int = 0             # 相对画布中心
    y: int = 0
    opacity: float = 1.0

class TimelineTrack(BaseModel):
    id: str
    name: str
    type: Literal["media", "text", "audio"]
    elements: List[Union[MediaElement, TextElement]]
    muted: bool = False

class Timeline(BaseModel):
    id: str
    tracks: List[TimelineTrack]
    canvas_width: int = 1920
    canvas_height: int = 1080
    fps: int = 30
    background_color: str = "#000000"
```

### Subtitle 数据结构
```python
# app/models/editor/subtitle.py

class SubtitleSegment(BaseModel):
    index: int
    start_time: float
    end_time: float
    text: str

class SubtitleFile(BaseModel):
    id: str
    project_id: str
    language: str = "zh-CN"
    segments: List[SubtitleSegment]
    default_font_size: int = 40
    default_color: str = "#FFFFFF"
```

### EditorProject 数据结构
```python
# app/models/editor/project.py

class EditorProject(BaseModel):
    id: str
    name: str
    timeline: Optional[Timeline] = None
    status: Literal["draft", "editing", "rendering", "completed", "failed"]
    output_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

---

## 2. 核心服务

### FFmpegService (底层工具)
```python
# app/services/video/ffmpeg_service.py

class FFmpegService:
    async def trim_video(
        self,
        input_path: Path,
        output_path: Path,
        start: float,
        duration: float
    ) -> Path:
        """裁剪视频"""
        ffmpeg.input(str(input_path), ss=start, t=duration) \
              .output(str(output_path), c='copy') \
              .run()
        return output_path

    async def merge_videos(
        self,
        video_paths: List[Path],
        output_path: Path
    ) -> Path:
        """合并视频"""
        # 使用 concat demuxer

    async def add_text_overlay(
        self,
        video_path: Path,
        text: str,
        output_path: Path,
        **style
    ) -> Path:
        """添加文字"""
        # 使用 drawtext filter
```

### SubtitleService (字幕处理)
```python
# app/services/editor/subtitle_service.py

class SubtitleService:
    def __init__(self):
        self.whisper_model = whisper.load_model("base")

    async def generate_auto_subtitles(
        self,
        video_path: Path,
        language: str = "zh"
    ) -> SubtitleFile:
        """自动生成字幕（Whisper ASR）"""
        result = self.whisper_model.transcribe(str(video_path))
        # 转换为 SubtitleFile

    async def export_srt(
        self,
        subtitle_file: SubtitleFile,
        output_path: Path
    ) -> Path:
        """导出 SRT 文件"""
        # 使用 pysrt 库
```

### TimelineRenderer (渲染引擎)
```python
# app/services/editor/timeline_renderer.py

class TimelineRenderer:
    def __init__(self):
        self.ffmpeg = FFmpegService()

    async def render(
        self,
        timeline: Timeline,
        output_path: Path,
        quality: str = "high"
    ) -> Path:
        """渲染时间轴为视频"""
        # 1. 处理每个轨道
        track_videos = []
        for track in timeline.tracks:
            if track.type == "media":
                video = await self._render_media_track(track)
                track_videos.append(video)

        # 2. 合并轨道
        merged = await self.ffmpeg.merge_videos(track_videos)

        # 3. 叠加文字
        if self._has_text_tracks(timeline):
            merged = await self._add_text_overlays(merged, timeline)

        # 4. 最终转码
        return await self.ffmpeg.transcode(merged, output_path, quality)

    async def _render_media_track(
        self,
        track: TimelineTrack
    ) -> Path:
        """处理单个媒体轨道"""
        clips = []
        for element in track.elements:
            # 裁剪每个片段
            clip = await self.ffmpeg.trim_video(
                element.media_id,
                start=element.trim_start,
                duration=element.duration
            )
            clips.append(clip)

        # 合并片段
        return await self.ffmpeg.merge_videos(clips)
```

---

## 3. API 接口

### 路由定义
```python
# app/api/editor.py

router = APIRouter(prefix="/api/editor", tags=["视频编辑器"])

@router.post("/projects", response_model=EditorProject)
async def create_project(project: EditorProject):
    """创建编辑项目"""

@router.get("/projects/{project_id}", response_model=EditorProject)
async def get_project(project_id: str):
    """获取项目"""

@router.post("/render")
async def render_timeline(
    background_tasks: BackgroundTasks,
    project_id: str,
    quality: str = "high"
):
    """渲染视频（后台任务）"""
    # 返回 task_id

@router.post("/subtitle/generate", response_model=SubtitleFile)
async def generate_subtitle(
    project_id: str,
    video_file: UploadFile
):
    """自动生成字幕"""
```

### 请求/响应示例

**创建项目**:
```json
POST /api/editor/projects

{
  "name": "我的视频",
  "timeline": {
    "tracks": [
      {
        "name": "主轨道",
        "type": "media",
        "elements": [
          {
            "type": "media",
            "name": "片段1",
            "media_id": "video_001.mp4",
            "duration": 10.0,
            "start_time": 0.0
          }
        ]
      }
    ]
  }
}
```

**响应**:
```json
{
  "id": "editor_abc123",
  "name": "我的视频",
  "status": "draft",
  "created_at": "2025-11-29T10:00:00Z"
}
```

---

## 4. 数据库表

```sql
-- 编辑项目表
CREATE TABLE editor_projects (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    timeline_json JSON,
    status VARCHAR(20) DEFAULT 'draft',
    output_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 字幕表
CREATE TABLE subtitle_files (
    id VARCHAR(100) PRIMARY KEY,
    project_id VARCHAR(100),
    language VARCHAR(10) DEFAULT 'zh-CN',
    segments_json JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES editor_projects(id)
);
```

---

## 5. 目录结构

```
app/
├── models/editor/              # 新增
│   ├── __init__.py
│   ├── timeline.py
│   ├── project.py
│   └── subtitle.py
│
├── services/editor/           # 新增
│   ├── __init__.py
│   ├── timeline_renderer.py
│   ├── subtitle_service.py
│   └── project_manager.py
│
├── services/video/            # 扩展
│   ├── ffmpeg_service.py     # 新增
│   ├── moviepy_composer.py   # 新增（可选）
│   ├── manager.py            # 现有
│   └── processor.py          # 现有
│
└── api/
    └── editor.py              # 新增
```

---

## 6. 开发清单

### Phase 1: 基础设施（3天）
- [ ] 创建数据模型 (`models/editor/`)
- [ ] 实现 FFmpegService 基础方法
- [ ] 数据库迁移脚本
- [ ] 单元测试

### Phase 2: 渲染引擎（4天）
- [ ] TimelineRenderer 核心逻辑
- [ ] 多轨道处理
- [ ] 文字叠加
- [ ] 性能测试

### Phase 3: 字幕功能（3天）
- [ ] SubtitleService (Whisper 集成)
- [ ] SRT 导入/导出
- [ ] 字幕渲染

### Phase 4: API（2天）
- [ ] 所有 REST 端点
- [ ] 后台任务队列
- [ ] API 测试

---

## 7. 技术要点

### FFmpeg 参数优化
```python
# 高质量输出
quality_params = {
    "vcodec": "libx264",
    "crf": 18,          # 18-23 推荐
    "preset": "slow",   # slow/medium/fast
    "acodec": "aac",
    "audio_bitrate": "192k"
}

# 快速预览
preview_params = {
    "vcodec": "libx264",
    "crf": 28,
    "preset": "ultrafast",
    "scale": "640:360"
}
```

### 并发控制
```python
# 使用 Celery 或 asyncio.Queue
from asyncio import Queue

render_queue = Queue(maxsize=3)  # 最多 3 个并发

async def queue_render(timeline):
    await render_queue.put(timeline)
    # 处理...
    render_queue.task_done()
```

### 临时文件管理
```python
import tempfile
from pathlib import Path

async def render(timeline):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # 所有中间文件存这里
        # 函数结束自动清理
```

---

## 8. 测试用例

```python
# tests/test_editor/test_renderer.py

async def test_simple_timeline():
    timeline = Timeline(
        tracks=[
            TimelineTrack(
                type="media",
                elements=[
                    MediaElement(
                        media_id="test.mp4",
                        duration=5.0,
                        start_time=0.0
                    )
                ]
            )
        ]
    )

    renderer = TimelineRenderer()
    output = await renderer.render(timeline, Path("output.mp4"))

    assert output.exists()
    assert get_video_duration(output) == 5.0
```

---

## 9. 配置

```python
# app/core/config.py (扩展)

class Settings(BaseSettings):
    # 编辑器配置
    EDITOR_TEMP_DIR: str = "temp/editor"
    EDITOR_OUTPUT_DIR: str = "output/editor"
    EDITOR_MAX_CONCURRENT: int = 3

    # Whisper 配置
    WHISPER_MODEL: str = "base"  # tiny/base/small/medium/large

    # 渲染质量预设
    RENDER_QUALITY = {
        "low": {"crf": 28, "preset": "fast"},
        "medium": {"crf": 23, "preset": "medium"},
        "high": {"crf": 18, "preset": "slow"}
    }
```

---

## 10. 依赖

```bash
# requirements.txt (新增)
pysrt>=1.1.2              # SRT 字幕处理

# 已有依赖（复用）
ffmpeg-python>=0.2.0
moviepy>=1.0.3
openai-whisper>=20231117
Pillow>=10.0.0
```

---

**核心原则**:
- 简单优先，避免过度设计
- 复用现有代码和基础设施
- 渐进式开发，MVP 先行
