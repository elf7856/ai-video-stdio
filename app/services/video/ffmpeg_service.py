"""
FFmpeg服务 - 底层视频处理工具
提供视频裁剪、合并、转码、文字叠加等基础功能
"""
import ffmpeg
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import tempfile
import os

logger = logging.getLogger(__name__)


class FFmpegService:
    """FFmpeg视频处理服务"""

    def __init__(self):
        self.logger = logger

    async def trim_video(
        self,
        input_path: Path,
        output_path: Path,
        start: float,
        duration: float,
        copy_codec: bool = True
    ) -> Path:
        """
        裁剪视频

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            start: 起始时间（秒）
            duration: 持续时间（秒）
            copy_codec: 是否直接复制编码（快速但可能不精确）

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"裁剪视频: {input_path} [{start}s - {start+duration}s]")

            if copy_codec:
                # 快速模式：直接复制流，不重新编码
                (
                    ffmpeg
                    .input(str(input_path), ss=start, t=duration)
                    .output(str(output_path), c='copy', avoid_negative_ts=1)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            else:
                # 精确模式：重新编码
                (
                    ffmpeg
                    .input(str(input_path), ss=start, t=duration)
                    .output(
                        str(output_path),
                        vcodec='libx264',
                        acodec='aac',
                        **{'crf': 18, 'preset': 'medium'}
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )

            self.logger.info(f"✅ 视频裁剪完成: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"视频裁剪失败: {error_msg}")
            raise Exception(f"FFmpeg裁剪失败: {error_msg}")

    async def merge_videos(
        self,
        video_paths: List[Path],
        output_path: Path,
        transition_duration: float = 0.0
    ) -> Path:
        """
        合并多个视频

        Args:
            video_paths: 视频文件路径列表
            output_path: 输出视频路径
            transition_duration: 转场时长（秒，0表示无转场）

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"合并 {len(video_paths)} 个视频")

            if len(video_paths) == 0:
                raise ValueError("视频列表为空")

            if len(video_paths) == 1:
                # 只有一个视频，直接复制
                import shutil
                shutil.copy(str(video_paths[0]), str(output_path))
                return output_path

            # 创建临时concat文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                concat_file = f.name
                for video_path in video_paths:
                    f.write(f"file '{video_path}'\n")

            try:
                # 使用concat demuxer合并
                (
                    ffmpeg
                    .input(concat_file, format='concat', safe=0)
                    .output(
                        str(output_path),
                        c='copy'  # 直接复制流，快速合并
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )

                self.logger.info(f"✅ 视频合并完成: {output_path}")
                return output_path

            finally:
                # 清理临时文件
                if os.path.exists(concat_file):
                    os.unlink(concat_file)

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"视频合并失败: {error_msg}")
            raise Exception(f"FFmpeg合并失败: {error_msg}")

    async def add_text_overlay(
        self,
        video_path: Path,
        text: str,
        output_path: Path,
        font_size: int = 40,
        font_color: str = "white",
        x: str = "(w-text_w)/2",  # 居中
        y: str = "h-th-20",  # 底部留20px
        font_file: Optional[str] = None,
        start_time: float = 0.0,
        duration: Optional[float] = None
    ) -> Path:
        """
        在视频上添加文字

        Args:
            video_path: 输入视频路径
            text: 文字内容
            output_path: 输出视频路径
            font_size: 字体大小
            font_color: 字体颜色
            x: X坐标表达式
            y: Y坐标表达式
            font_file: 字体文件路径
            start_time: 文字开始时间（秒）
            duration: 文字持续时间（秒）

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"添加文字叠加: {text[:20]}...")

            # 构建drawtext滤镜参数
            drawtext_params = {
                'text': text.replace("'", "\\'"),  # 转义单引号
                'fontsize': font_size,
                'fontcolor': font_color,
                'x': x,
                'y': y,
            }

            if font_file:
                drawtext_params['fontfile'] = font_file

            # 时间控制
            if start_time > 0 or duration is not None:
                enable_expr = f"between(t,{start_time},"
                if duration:
                    enable_expr += f"{start_time + duration})"
                else:
                    enable_expr += "100000)"  # 大数表示到视频结束
                drawtext_params['enable'] = enable_expr

            # 构建drawtext字符串
            drawtext_str = ":".join([f"{k}={v}" for k, v in drawtext_params.items()])

            # 应用滤镜
            (
                ffmpeg
                .input(str(video_path))
                .filter('drawtext', drawtext_str)
                .output(
                    str(output_path),
                    vcodec='libx264',
                    acodec='copy',
                    **{'crf': 18, 'preset': 'medium'}
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.logger.info(f"✅ 文字叠加完成: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"文字叠加失败: {error_msg}")
            raise Exception(f"FFmpeg文字叠加失败: {error_msg}")

    async def transcode(
        self,
        input_path: Path,
        output_path: Path,
        quality: str = "high",
        resolution: Optional[tuple] = None,
        fps: Optional[int] = None
    ) -> Path:
        """
        转码视频

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            quality: 质量预设 (low/medium/high)
            resolution: 分辨率 (width, height)
            fps: 帧率

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"转码视频: {input_path} -> {quality}")

            # 质量参数
            quality_params = {
                'low': {'crf': 28, 'preset': 'fast'},
                'medium': {'crf': 23, 'preset': 'medium'},
                'high': {'crf': 18, 'preset': 'slow'}
            }
            params = quality_params.get(quality, quality_params['medium'])

            # 构建输出参数
            output_params = {
                'vcodec': 'libx264',
                'acodec': 'aac',
                'audio_bitrate': '192k',
                **params
            }

            # 应用分辨率
            input_stream = ffmpeg.input(str(input_path))
            if resolution:
                input_stream = input_stream.filter('scale', resolution[0], resolution[1])

            # 应用帧率
            if fps:
                input_stream = input_stream.filter('fps', fps=fps)

            # 执行转码
            (
                input_stream
                .output(str(output_path), **output_params)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.logger.info(f"✅ 视频转码完成: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"视频转码失败: {error_msg}")
            raise Exception(f"FFmpeg转码失败: {error_msg}")

    async def extract_audio(
        self,
        video_path: Path,
        output_path: Path,
        audio_format: str = "mp3"
    ) -> Path:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径
            audio_format: 音频格式

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"提取音频: {video_path}")

            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(output_path),
                    acodec='libmp3lame' if audio_format == 'mp3' else 'aac',
                    audio_bitrate='192k'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.logger.info(f"✅ 音频提取完成: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"音频提取失败: {error_msg}")
            raise Exception(f"FFmpeg音频提取失败: {error_msg}")

    async def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息字典
        """
        try:
            probe = ffmpeg.probe(str(video_path))

            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )

            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )

            info = {
                'duration': float(probe['format'].get('duration', 0)),
                'size': int(probe['format'].get('size', 0)),
                'format': probe['format'].get('format_name', ''),
            }

            if video_stream:
                info.update({
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                    'video_codec': video_stream.get('codec_name', '')
                })

            if audio_stream:
                info.update({
                    'audio_codec': audio_stream.get('codec_name', ''),
                    'sample_rate': int(audio_stream.get('sample_rate', 0))
                })

            return info

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.logger.error(f"获取视频信息失败: {error_msg}")
            raise Exception(f"FFmpeg probe失败: {error_msg}")
