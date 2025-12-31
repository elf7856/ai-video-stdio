"""
字幕服务 - 自动生成字幕、导入导出SRT
"""
import logging
from pathlib import Path
from typing import Optional, List
import re

from app.models.editor.subtitle import SubtitleFile, SubtitleSegment
from app.services.audio.asr_service import ASRService

logger = logging.getLogger(__name__)


class SubtitleService:
    """字幕服务"""

    def __init__(self):
        self.asr_service = ASRService()
        self.logger = logger

    async def generate_auto_subtitles(
        self,
        video_path: Path,
        language: str = "zh",
        project_id: str = ""
    ) -> SubtitleFile:
        """
        自动生成字幕（使用Whisper ASR）

        Args:
            video_path: 视频文件路径
            language: 语言代码
            project_id: 项目ID

        Returns:
            字幕文件对象
        """
        try:
            self.logger.info(f"开始生成字幕: {video_path}")

            # 使用ASR服务转录
            result = await self.asr_service.transcribe_video(
                video_path=str(video_path),
                provider="whisper",
                model="base",
                language=language
            )

            if not result["success"]:
                raise Exception(f"ASR转录失败: {result.get('error')}")

            # 转换为字幕片段
            segments: List[SubtitleSegment] = []
            for idx, seg_data in enumerate(result["segments"], start=1):
                segment = SubtitleSegment(
                    index=idx,
                    start_time=seg_data["start"],
                    end_time=seg_data["end"],
                    text=seg_data["text"].strip()
                )
                segments.append(segment)

            # 创建字幕文件
            subtitle_file = SubtitleFile(
                id=f"subtitle_{project_id}_{int(Path(video_path).stat().st_mtime)}",
                project_id=project_id,
                language=language,
                segments=segments
            )

            self.logger.info(f"✅ 字幕生成完成: {len(segments)} 个片段")
            return subtitle_file

        except Exception as e:
            self.logger.error(f"字幕生成失败: {e}", exc_info=True)
            raise

    async def import_srt(
        self,
        srt_path: Path,
        project_id: str = ""
    ) -> SubtitleFile:
        """
        导入SRT字幕文件

        Args:
            srt_path: SRT文件路径
            project_id: 项目ID

        Returns:
            字幕文件对象
        """
        try:
            self.logger.info(f"导入SRT文件: {srt_path}")

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析SRT格式
            segments = self._parse_srt(content)

            subtitle_file = SubtitleFile(
                id=f"subtitle_{project_id}_{srt_path.stem}",
                project_id=project_id,
                segments=segments
            )

            self.logger.info(f"✅ SRT导入完成: {len(segments)} 个片段")
            return subtitle_file

        except Exception as e:
            self.logger.error(f"SRT导入失败: {e}")
            raise

    async def export_srt(
        self,
        subtitle_file: SubtitleFile,
        output_path: Path
    ) -> Path:
        """
        导出为SRT文件

        Args:
            subtitle_file: 字幕文件对象
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"导出SRT文件: {output_path}")

            srt_content = subtitle_file.to_srt()

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)

            self.logger.info(f"✅ SRT导出完成")
            return output_path

        except Exception as e:
            self.logger.error(f"SRT导出失败: {e}")
            raise

    def _parse_srt(self, content: str) -> List[SubtitleSegment]:
        """
        解析SRT格式字幕

        Args:
            content: SRT文件内容

        Returns:
            字幕片段列表
        """
        segments: List[SubtitleSegment] = []

        # SRT格式正则表达式
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.*\n?)+?)(?=\n\n|\Z)'

        matches = re.findall(pattern, content, re.MULTILINE)

        for match in matches:
            index = int(match[0])
            start_time = self._parse_srt_time(match[1])
            end_time = self._parse_srt_time(match[2])
            text = match[3].strip()

            segment = SubtitleSegment(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text
            )
            segments.append(segment)

        return segments

    @staticmethod
    def _parse_srt_time(time_str: str) -> float:
        """
        解析SRT时间格式为秒

        Args:
            time_str: SRT时间字符串 (HH:MM:SS,mmm)

        Returns:
            秒数
        """
        # 格式: 00:01:23,456
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds

    async def optimize_subtitle_timing(
        self,
        subtitle_file: SubtitleFile,
        max_chars_per_second: int = 20,
        min_duration: float = 1.0,
        max_duration: float = 7.0
    ) -> SubtitleFile:
        """
        优化字幕时长

        Args:
            subtitle_file: 字幕文件
            max_chars_per_second: 每秒最大字符数
            min_duration: 最小时长
            max_duration: 最大时长

        Returns:
            优化后的字幕文件
        """
        optimized_segments: List[SubtitleSegment] = []

        for segment in subtitle_file.segments:
            text_length = len(segment.text)
            optimal_duration = text_length / max_chars_per_second

            # 限制在min和max之间
            optimal_duration = max(min_duration, min(optimal_duration, max_duration))

            # 保持原始开始时间，调整结束时间
            optimized_segment = SubtitleSegment(
                index=segment.index,
                start_time=segment.start_time,
                end_time=segment.start_time + optimal_duration,
                text=segment.text
            )
            optimized_segments.append(optimized_segment)

        subtitle_file.segments = optimized_segments
        return subtitle_file
