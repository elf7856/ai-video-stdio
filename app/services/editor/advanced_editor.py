"""
高级视频编辑功能 - 转场、音频混合、滤镜等
"""
import ffmpeg
import logging
from pathlib import Path
from typing import List, Optional, Literal
import tempfile

from app.services.video.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class AdvancedVideoEditor:
    """高级视频编辑器"""

    def __init__(self):
        self.ffmpeg = FFmpegService()
        self.logger = logger

    async def add_transition(
        self,
        video1_path: Path,
        video2_path: Path,
        output_path: Path,
        transition_type: Literal["fade", "wipe", "dissolve", "slide"] = "fade",
        duration: float = 1.0
    ) -> Path:
        """
        在两个视频之间添加转场效果

        Args:
            video1_path: 第一个视频
            video2_path: 第二个视频
            output_path: 输出路径
            transition_type: 转场类型
            duration: 转场时长（秒）

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"添加转场效果: {transition_type}")

            # 获取视频信息
            info1 = await self.ffmpeg.get_video_info(video1_path)
            info2 = await self.ffmpeg.get_video_info(video2_path)

            v1_duration = info1['duration']
            offset = v1_duration - duration

            if transition_type == "fade":
                # 淡入淡出转场
                (
                    ffmpeg
                    .input(str(video1_path))
                    .filter('fade', type='out', start_time=offset, duration=duration)
                    .concat(
                        ffmpeg
                        .input(str(video2_path))
                        .filter('fade', type='in', start_time=0, duration=duration),
                        v=1, a=1
                    )
                    .output(str(output_path), vcodec='libx264', acodec='aac')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )

            elif transition_type == "dissolve":
                # 溶解转场（叠化）
                (
                    ffmpeg
                    .input(str(video1_path))
                    .overlay(
                        ffmpeg.input(str(video2_path)).filter('fade', type='in', duration=duration),
                        enable=f'between(t,{offset},{offset+duration})'
                    )
                    .output(str(output_path), vcodec='libx264', acodec='aac')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )

            else:
                # 默认：简单拼接
                self.logger.warning(f"转场类型 {transition_type} 暂未实现，使用简单拼接")
                await self.ffmpeg.merge_videos([video1_path, video2_path], output_path)

            self.logger.info(f"✅ 转场添加完成: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"转场添加失败: {e}")
            raise

    async def mix_audio(
        self,
        video_path: Path,
        audio_paths: List[Path],
        output_path: Path,
        volumes: Optional[List[float]] = None
    ) -> Path:
        """
        混合多个音频到视频

        Args:
            video_path: 视频文件
            audio_paths: 音频文件列表
            output_path: 输出路径
            volumes: 各音频音量（0.0-1.0）

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"混合 {len(audio_paths)} 个音频")

            if not audio_paths:
                raise ValueError("音频列表为空")

            if volumes is None:
                volumes = [1.0] * len(audio_paths)

            # 构建输入流
            inputs = [ffmpeg.input(str(video_path))]
            for audio_path in audio_paths:
                inputs.append(ffmpeg.input(str(audio_path)))

            # 提取视频流
            video_stream = inputs[0].video

            # 混合所有音频流
            audio_streams = [inp.audio for inp in inputs]

            # 调整音量并混合
            adjusted_audio = []
            for i, (stream, vol) in enumerate(zip(audio_streams, volumes)):
                adjusted = stream.filter('volume', volume=vol)
                adjusted_audio.append(adjusted)

            # 混合音频
            if len(adjusted_audio) > 1:
                mixed_audio = ffmpeg.filter(adjusted_audio, 'amix', inputs=len(adjusted_audio))
            else:
                mixed_audio = adjusted_audio[0]

            # 合并视频和音频
            (
                ffmpeg
                .output(video_stream, mixed_audio, str(output_path), vcodec='copy', acodec='aac')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.logger.info(f"✅ 音频混合完成: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"音频混合失败: {e}")
            raise

    async def apply_filter(
        self,
        video_path: Path,
        output_path: Path,
        filter_type: Literal["brightness", "contrast", "saturate", "blur", "sharpen", "vintage", "cool", "warm"],
        intensity: float = 1.0
    ) -> Path:
        """
        应用视频滤镜

        Args:
            video_path: 输入视频
            output_path: 输出路径
            filter_type: 滤镜类型
            intensity: 强度（0.0-2.0）

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"应用滤镜: {filter_type}, 强度: {intensity}")

            input_stream = ffmpeg.input(str(video_path))

            # 根据滤镜类型构建filter chain
            if filter_type == "brightness":
                # 亮度调整
                stream = input_stream.filter('eq', brightness=intensity - 1.0)

            elif filter_type == "contrast":
                # 对比度调整
                stream = input_stream.filter('eq', contrast=intensity)

            elif filter_type == "saturate":
                # 饱和度调整
                stream = input_stream.filter('eq', saturation=intensity)

            elif filter_type == "blur":
                # 模糊效果
                stream = input_stream.filter('boxblur', luma_radius=int(intensity * 5))

            elif filter_type == "sharpen":
                # 锐化效果
                stream = input_stream.filter('unsharp', luma_amount=intensity)

            elif filter_type == "vintage":
                # 复古效果（降低饱和度+增加暖色调）
                stream = (
                    input_stream
                    .filter('eq', saturation=0.6, contrast=1.2)
                    .filter('curves', preset='vintage')
                )

            elif filter_type == "cool":
                # 冷色调
                stream = input_stream.filter('colortemperature', temperature=5500)

            elif filter_type == "warm":
                # 暖色调
                stream = input_stream.filter('colortemperature', temperature=8500)

            else:
                raise ValueError(f"不支持的滤镜类型: {filter_type}")

            # 输出
            (
                stream
                .output(str(output_path), vcodec='libx264', acodec='copy', **{'crf': 18})
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.logger.info(f"✅ 滤镜应用完成: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"滤镜应用失败: {e}")
            raise

    async def add_background_music(
        self,
        video_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: float = 0.3,
        fade_in: float = 2.0,
        fade_out: float = 2.0
    ) -> Path:
        """
        添加背景音乐

        Args:
            video_path: 视频文件
            music_path: 音乐文件
            output_path: 输出路径
            music_volume: 音乐音量（0.0-1.0）
            fade_in: 淡入时长（秒）
            fade_out: 淡出时长（秒）

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"添加背景音乐: {music_path}")

            # 获取视频时长
            info = await self.ffmpeg.get_video_info(video_path)
            video_duration = info['duration']

            # 构建音频处理链
            video_input = ffmpeg.input(str(video_path))
            music_input = ffmpeg.input(str(music_path))

            # 处理音乐：循环、裁剪、淡入淡出、音量调整
            music_audio = (
                music_input
                .audio
                .filter('aloop', loop=-1, size=int(video_duration * 44100))  # 循环
                .filter('atrim', duration=video_duration)  # 裁剪到视频长度
                .filter('afade', type='in', start_time=0, duration=fade_in)  # 淡入
                .filter('afade', type='out', start_time=video_duration - fade_out, duration=fade_out)  # 淡出
                .filter('volume', volume=music_volume)  # 音量调整
            )

            # 保留原视频音频
            video_audio = video_input.audio

            # 混合音频
            mixed_audio = ffmpeg.filter([video_audio, music_audio], 'amix', inputs=2)

            # 合并输出
            (
                ffmpeg
                .output(
                    video_input.video,
                    mixed_audio,
                    str(output_path),
                    vcodec='copy',
                    acodec='aac',
                    audio_bitrate='192k'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.logger.info(f"✅ 背景音乐添加完成: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"背景音乐添加失败: {e}")
            raise

    async def create_picture_in_picture(
        self,
        main_video: Path,
        pip_video: Path,
        output_path: Path,
        position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "top-right",
        scale: float = 0.25
    ) -> Path:
        """
        创建画中画效果

        Args:
            main_video: 主视频
            pip_video: 画中画视频
            output_path: 输出路径
            position: 位置
            scale: 画中画缩放比例

        Returns:
            输出文件路径
        """
        try:
            self.logger.info(f"创建画中画效果: 位置={position}, 缩放={scale}")

            main = ffmpeg.input(str(main_video))
            pip = ffmpeg.input(str(pip_video))

            # 缩放画中画
            scaled_pip = pip.filter('scale', f'iw*{scale}', f'ih*{scale}')

            # 根据位置计算坐标
            if position == "top-left":
                x, y = 10, 10
            elif position == "top-right":
                x, y = "main_w-overlay_w-10", 10
            elif position == "bottom-left":
                x, y = 10, "main_h-overlay_h-10"
            else:  # bottom-right
                x, y = "main_w-overlay_w-10", "main_h-overlay_h-10"

            # 叠加画中画
            (
                main
                .overlay(scaled_pip, x=x, y=y)
                .output(str(output_path), vcodec='libx264', acodec='aac')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.logger.info(f"✅ 画中画创建完成: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"画中画创建失败: {e}")
            raise
