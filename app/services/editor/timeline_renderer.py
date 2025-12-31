"""
时间轴渲染器 - 将Timeline渲染为视频
"""
import logging
from pathlib import Path
from typing import Optional, List
import tempfile
import os

from app.models.editor.timeline import Timeline, TimelineTrack, MediaElement, TextElement
from app.services.video.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class TimelineRenderer:
    """时间轴渲染器"""

    def __init__(self):
        self.ffmpeg = FFmpegService()
        self.logger = logger

    async def render(
        self,
        timeline: Timeline,
        output_path: Path,
        quality: str = "high"
    ) -> Path:
        """
        渲染时间轴为视频

        Args:
            timeline: 时间轴对象
            output_path: 输出视频路径
            quality: 输出质量 (low/medium/high)

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"开始渲染时间轴: {timeline.name}")

            # 创建临时目录用于中间文件
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 1. 处理每个媒体轨道
                track_videos: List[Path] = []

                for track in timeline.tracks:
                    if track.type == "media":
                        track_video = await self._render_media_track(track, temp_path)
                        if track_video:
                            track_videos.append(track_video)

                if not track_videos:
                    raise Exception("没有可渲染的媒体轨道")

                # 2. 合并所有轨道（如果有多个）
                if len(track_videos) > 1:
                    merged_video = temp_path / "merged.mp4"
                    await self.ffmpeg.merge_videos(track_videos, merged_video)
                else:
                    merged_video = track_videos[0]

                # 3. 叠加文字轨道
                if self._has_text_tracks(timeline):
                    text_video = await self._add_text_overlays(merged_video, timeline, temp_path)
                    merged_video = text_video

                # 4. 最终转码输出
                await self.ffmpeg.transcode(
                    merged_video,
                    output_path,
                    quality=quality,
                    resolution=(timeline.canvas_width, timeline.canvas_height),
                    fps=timeline.fps
                )

                self.logger.info(f"✅ 时间轴渲染完成: {output_path}")
                return output_path

        except Exception as e:
            self.logger.error(f"渲染失败: {e}", exc_info=True)
            raise

    async def _render_media_track(
        self,
        track: TimelineTrack,
        temp_path: Path
    ) -> Optional[Path]:
        """
        渲染单个媒体轨道

        Args:
            track: 媒体轨道
            temp_path: 临时目录路径

        Returns:
            渲染后的视频路径
        """
        try:
            if not track.elements:
                return None

            self.logger.info(f"渲染媒体轨道: {track.name}")

            # 处理每个元素
            clips: List[Path] = []
            for idx, element in enumerate(track.elements):
                if not isinstance(element, MediaElement):
                    continue

                clip_path = temp_path / f"{track.id}_clip_{idx}.mp4"

                # 裁剪片段
                input_path = Path(element.media_id)
                if not input_path.exists():
                    self.logger.warning(f"媒体文件不存在: {input_path}")
                    continue

                await self.ffmpeg.trim_video(
                    input_path=input_path,
                    output_path=clip_path,
                    start=element.trim_start,
                    duration=element.duration,
                    copy_codec=True
                )

                clips.append(clip_path)

            if not clips:
                return None

            # 合并所有片段
            if len(clips) > 1:
                track_output = temp_path / f"{track.id}_merged.mp4"
                await self.ffmpeg.merge_videos(clips, track_output)
                return track_output
            else:
                return clips[0]

        except Exception as e:
            self.logger.error(f"媒体轨道渲染失败: {e}")
            raise

    async def _add_text_overlays(
        self,
        video_path: Path,
        timeline: Timeline,
        temp_path: Path
    ) -> Path:
        """
        添加文字叠加

        Args:
            video_path: 输入视频路径
            timeline: 时间轴对象
            temp_path: 临时目录路径

        Returns:
            添加文字后的视频路径
        """
        try:
            self.logger.info("添加文字叠加")

            current_video = video_path
            text_count = 0

            for track in timeline.tracks:
                if track.type != "text":
                    continue

                for element in track.elements:
                    if not isinstance(element, TextElement):
                        continue

                    text_count += 1
                    output_video = temp_path / f"text_overlay_{text_count}.mp4"

                    # 计算文字位置（相对于画布中心）
                    x_expr = f"({timeline.canvas_width}/2)+{element.x}"
                    y_expr = f"({timeline.canvas_height}/2)+{element.y}"

                    await self.ffmpeg.add_text_overlay(
                        video_path=current_video,
                        text=element.content,
                        output_path=output_video,
                        font_size=element.font_size,
                        font_color=element.color,
                        x=x_expr,
                        y=y_expr,
                        start_time=element.start_time,
                        duration=element.duration
                    )

                    current_video = output_video

            return current_video

        except Exception as e:
            self.logger.error(f"文字叠加失败: {e}")
            raise

    def _has_text_tracks(self, timeline: Timeline) -> bool:
        """检查是否有文字轨道"""
        return any(track.type == "text" and track.elements for track in timeline.tracks)

    async def render_preview(
        self,
        timeline: Timeline,
        output_path: Path,
        max_duration: float = 10.0
    ) -> Path:
        """
        渲染预览视频（快速、低质量）

        Args:
            timeline: 时间轴对象
            output_path: 输出路径
            max_duration: 最大预览时长

        Returns:
            输出文件路径
        """
        # 创建截断的时间轴副本
        preview_timeline = timeline.copy(deep=True)

        # 截断到max_duration
        for track in preview_timeline.tracks:
            track.elements = [
                el for el in track.elements
                if el.start_time < max_duration
            ]

        # 使用低质量快速渲染
        return await self.render(preview_timeline, output_path, quality="low")
