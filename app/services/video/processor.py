import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx import resize, crop, colorx
import os
from typing import Dict, List, Optional, Tuple
from app.core.config import settings
import tempfile

class VideoProcessor:
    def __init__(self):
        self.supported_formats = settings.allowed_video_formats
        
    def get_video_info(self, video_path: str) -> Dict:
        """获取视频信息"""
        try:
            clip = VideoFileClip(video_path)
            info = {
                "duration": clip.duration,
                "fps": clip.fps,
                "size": clip.size,
                "resolution": f"{clip.size[0]}x{clip.size[1]}",
                "file_size": os.path.getsize(video_path)
            }
            clip.close()
            return info
        except Exception as e:
            return {"error": f"获取视频信息失败: {str(e)}"}
    
    def extract_frames(self, video_path: str, start_time: float, end_time: float, 
                      output_dir: str) -> List[str]:
        """提取视频帧"""
        try:
            clip = VideoFileClip(video_path)
            frames = []
            
            for t in np.arange(start_time, end_time, 1/clip.fps):
                frame = clip.get_frame(t)
                frame_path = os.path.join(output_dir, f"frame_{t:.2f}.jpg")
                cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                frames.append(frame_path)
            
            clip.close()
            return frames
        except Exception as e:
            return []
    
    def insert_content(self, original_path: str, insert_path: str, 
                      start_time: float, output_path: str) -> bool:
        """在指定时间插入内容"""
        try:
            original = VideoFileClip(original_path)
            insert = VideoFileClip(insert_path)
            
            # 分割原视频
            before = original.subclip(0, start_time)
            after = original.subclip(start_time)
            
            # 合成新视频
            final = CompositeVideoClip([
                before,
                insert.set_start(start_time),
                after.set_start(start_time + insert.duration)
            ])
            
            final.write_videofile(output_path, 
                                codec='libx264', 
                                audio_codec='aac',
                                fps=original.fps)
            
            original.close()
            insert.close()
            final.close()
            
            return True
        except Exception as e:
            print(f"插入内容失败: {str(e)}")
            return False
    
    def replace_content(self, original_path: str, replacement_path: str,
                       start_time: float, end_time: float, output_path: str) -> bool:
        """替换指定时间段的内容"""
        try:
            original = VideoFileClip(original_path)
            replacement = VideoFileClip(replacement_path)
            
            # 分割原视频
            before = original.subclip(0, start_time)
            after = original.subclip(end_time)
            
            # 合成新视频
            final = CompositeVideoClip([
                before,
                replacement.set_start(start_time),
                after.set_start(start_time + replacement.duration)
            ])
            
            final.write_videofile(output_path,
                                codec='libx264',
                                audio_codec='aac',
                                fps=original.fps)
            
            original.close()
            replacement.close()
            final.close()
            
            return True
        except Exception as e:
            print(f"替换内容失败: {str(e)}")
            return False
    
    def apply_style_filter(self, video_path: str, style: str, output_path: str) -> bool:
        """应用风格滤镜"""
        try:
            clip = VideoFileClip(video_path)
            
            if style == "vintage":
                # 复古风格
                modified = clip.fx(colorx, 1.2).fx(lambda c: c.set_duration(c.duration))
            elif style == "black_white":
                # 黑白风格
                modified = clip.fx(lambda c: c.set_duration(c.duration))
            elif style == "warm":
                # 暖色调
                modified = clip.fx(colorx, 1.1).fx(lambda c: c.set_duration(c.duration))
            elif style == "cool":
                # 冷色调
                modified = clip.fx(colorx, 0.9).fx(lambda c: c.set_duration(c.duration))
            else:
                modified = clip
            
            modified.write_videofile(output_path,
                                   codec='libx264',
                                   audio_codec='aac',
                                   fps=clip.fps)
            
            clip.close()
            modified.close()
            
            return True
        except Exception as e:
            print(f"应用滤镜失败: {str(e)}")
            return False
    
    def add_text_overlay(self, video_path: str, text: str, position: str = "bottom",
                        output_path: str = None) -> str:
        """添加文字覆盖"""
        try:
            clip = VideoFileClip(video_path)
            
            # 创建文字剪辑
            txt_clip = TextClip(text, fontsize=70, color='white', font='Arial-Bold')
            txt_clip = txt_clip.set_pos(position).set_duration(clip.duration)
            
            # 合成视频
            final = CompositeVideoClip([clip, txt_clip])
            
            if output_path is None:
                output_path = tempfile.mktemp(suffix='.mp4')
            
            final.write_videofile(output_path,
                                codec='libx264',
                                audio_codec='aac',
                                fps=clip.fps)
            
            clip.close()
            txt_clip.close()
            final.close()
            
            return output_path
        except Exception as e:
            print(f"添加文字失败: {str(e)}")
            return None
    
    def resize_video(self, video_path: str, target_size: Tuple[int, int],
                    output_path: str) -> bool:
        """调整视频尺寸"""
        try:
            clip = VideoFileClip(video_path)
            resized = clip.resize(target_size)
            
            resized.write_videofile(output_path,
                                  codec='libx264',
                                  audio_codec='aac',
                                  fps=clip.fps)
            
            clip.close()
            resized.close()
            
            return True
        except Exception as e:
            print(f"调整尺寸失败: {str(e)}")
            return False
    
    def extract_audio(self, video_path: str, output_path: str) -> bool:
        """提取音频"""
        try:
            clip = VideoFileClip(video_path)
            audio = clip.audio
            audio.write_audiofile(output_path)
            
            clip.close()
            audio.close()
            
            return True
        except Exception as e:
            print(f"提取音频失败: {str(e)}")
            return False
    
    def merge_videos(self, video_paths: List[str], output_path: str) -> bool:
        """合并多个视频"""
        try:
            clips = [VideoFileClip(path) for path in video_paths]
            final = CompositeVideoClip(clips)
            
            final.write_videofile(output_path,
                                codec='libx264',
                                audio_codec='aac')
            
            for clip in clips:
                clip.close()
            final.close()
            
            return True
        except Exception as e:
            print(f"合并视频失败: {str(e)}")
            return False 