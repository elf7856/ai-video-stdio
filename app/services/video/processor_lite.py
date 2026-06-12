"""
轻量级视频处理器 - 使用 ffmpeg CLI 代替 moviepy/opencv
"""
import os
import json
import subprocess
from typing import Dict, List, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class VideoProcessor:
    """使用 ffmpeg 的轻量级视频处理器"""

    def __init__(self):
        self.supported_formats = settings.allowed_video_formats

    def get_video_info(self, video_path: str) -> Dict:
        """使用 ffprobe 获取视频信息"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # 提取视频流信息
            video_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                return {"error": "未找到视频流"}

            format_info = data.get('format', {})

            info = {
                "duration": float(format_info.get('duration', 0)),
                "fps": eval(video_stream.get('r_frame_rate', '0/1')),
                "width": int(video_stream.get('width', 0)),
                "height": int(video_stream.get('height', 0)),
                "size": [int(video_stream.get('width', 0)), int(video_stream.get('height', 0))],
                "resolution": f"{video_stream.get('width')}x{video_stream.get('height')}",
                "file_size": os.path.getsize(video_path),
                "codec": video_stream.get('codec_name', 'unknown')
            }

            return info

        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe 执行失败: {e}")
            return {"error": f"获取视频信息失败: {str(e)}"}
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {"error": f"获取视频信息失败: {str(e)}"}

    def extract_frames(self, video_path: str, start_time: float, end_time: float,
                      output_dir: str, fps: int = 1) -> List[str]:
        """使用 ffmpeg 提取视频帧"""
        try:
            os.makedirs(output_dir, exist_ok=True)

            duration = end_time - start_time
            output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-t', str(duration),
                '-i', video_path,
                '-vf', f'fps={fps}',
                '-q:v', '2',
                output_pattern,
                '-y'
            ]

            subprocess.run(cmd, capture_output=True, check=True)

            # 获取生成的帧文件列表
            frames = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith('frame_') and f.endswith('.jpg')
            ])

            return frames

        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg 提取帧失败: {e}")
            return []
        except Exception as e:
            logger.error(f"提取帧失败: {e}")
            return []

    def trim_video(self, video_path: str, start_time: float, end_time: float,
                   output_path: str) -> bool:
        """使用 ffmpeg 裁剪视频"""
        try:
            duration = end_time - start_time

            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-t', str(duration),
                '-i', video_path,
                '-c', 'copy',
                output_path,
                '-y'
            ]

            subprocess.run(cmd, capture_output=True, check=True)
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg 裁剪视频失败: {e}")
            return False
        except Exception as e:
            logger.error(f"裁剪视频失败: {e}")
            return False

    def merge_videos(self, video_paths: List[str], output_path: str) -> bool:
        """使用 ffmpeg 合并视频"""
        try:
            # 创建临时文件列表
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for video_path in video_paths:
                    f.write(f"file '{video_path}'\n")
                list_file = f.name

            try:
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', list_file,
                    '-c', 'copy',
                    output_path,
                    '-y'
                ]

                try:
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                    return True
                except subprocess.CalledProcessError as copy_error:
                    logger.warning(f"ffmpeg copy 合并失败，尝试重编码合并: {copy_error.stderr}")
                    fallback_cmd = [
                        'ffmpeg',
                        '-f', 'concat',
                        '-safe', '0',
                        '-i', list_file,
                        '-c:v', 'libx264',
                        '-preset', 'veryfast',
                        '-crf', '20',
                        '-c:a', 'aac',
                        '-movflags', '+faststart',
                        output_path,
                        '-y'
                    ]
                    subprocess.run(fallback_cmd, capture_output=True, text=True, check=True)
                    return True

            finally:
                os.unlink(list_file)

        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg 合并视频失败: {e.stderr or e}")
            return False
        except Exception as e:
            logger.error(f"合并视频失败: {e}")
            return False
