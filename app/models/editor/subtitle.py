"""
字幕数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SubtitleSegment(BaseModel):
    """字幕片段"""
    index: int  # 序号
    start_time: float  # 开始时间（秒）
    end_time: float  # 结束时间（秒）
    text: str  # 字幕文本

    @property
    def duration(self) -> float:
        """片段时长"""
        return self.end_time - self.start_time


class SubtitleFile(BaseModel):
    """字幕文件"""
    id: str
    project_id: str  # 关联的项目ID
    language: str = "zh-CN"  # 语言代码
    segments: List[SubtitleSegment] = []

    # 默认样式
    default_font_size: int = 40
    default_color: str = "#FFFFFF"
    default_font_family: str = "Arial"
    default_position: str = "bottom"  # top, middle, bottom

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_duration(self) -> float:
        """字幕总时长"""
        if not self.segments:
            return 0.0
        return max(seg.end_time for seg in self.segments)

    def to_srt(self) -> str:
        """导出为SRT格式"""
        srt_content = []
        for seg in self.segments:
            # SRT时间格式: HH:MM:SS,mmm
            start = self._format_srt_time(seg.start_time)
            end = self._format_srt_time(seg.end_time)

            srt_content.append(f"{seg.index}")
            srt_content.append(f"{start} --> {end}")
            srt_content.append(seg.text)
            srt_content.append("")  # 空行分隔

        return "\n".join(srt_content)

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """格式化为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
