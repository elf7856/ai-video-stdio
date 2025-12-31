"""
时间轴数据模型 - Timeline, Tracks, Elements
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Union, Optional


class TimelineElement(BaseModel):
    """时间轴元素基类"""
    id: str
    name: str
    duration: float  # 秒
    start_time: float  # 秒
    trim_start: float = 0  # 裁剪起始点（秒）
    trim_end: float = 0  # 裁剪结束点（秒）


class MediaElement(TimelineElement):
    """媒体元素（视频/音频）"""
    type: Literal["media"] = "media"
    media_id: str  # 文件路径或ID
    muted: bool = False
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    speed: float = Field(default=1.0, gt=0.0, le=4.0)


class TextElement(TimelineElement):
    """文字元素"""
    type: Literal["text"] = "text"
    content: str
    font_size: int = Field(default=40, ge=10, le=200)
    font_family: str = "Arial"
    color: str = "#FFFFFF"  # 十六进制颜色
    x: int = 0  # 相对画布中心的X坐标
    y: int = 0  # 相对画布中心的Y坐标
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class TimelineTrack(BaseModel):
    """时间轴轨道"""
    id: str
    name: str
    type: Literal["media", "text", "audio"]
    elements: List[Union[MediaElement, TextElement]] = []
    muted: bool = False
    locked: bool = False  # 是否锁定（锁定后不可编辑）


class Timeline(BaseModel):
    """时间轴（完整的编辑序列）"""
    id: str
    name: str = "Untitled Timeline"
    tracks: List[TimelineTrack] = []
    canvas_width: int = 1920
    canvas_height: int = 1080
    fps: int = 30
    background_color: str = "#000000"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def total_duration(self) -> float:
        """计算时间轴总时长"""
        if not self.tracks:
            return 0.0

        max_duration = 0.0
        for track in self.tracks:
            for element in track.elements:
                end_time = element.start_time + element.duration
                max_duration = max(max_duration, end_time)

        return max_duration
