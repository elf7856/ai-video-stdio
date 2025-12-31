import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx import resize, crop, colorx
import os
from typing import Dict, List, Optional, Tuple
from app.core.config import settings
import tempfile
import logging

logger = logging.getLogger(__name__)

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
            logger.error(f"插入内容失败: {str(e)}", exc_info=True)
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
            logger.error(f"替换内容失败: {str(e)}", exc_info=True)
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
            logger.error(f"应用滤镜失败: {str(e)}", exc_info=True)
            return False
    
    def add_text_overlay(self, video_path: str, text: str, position: str = "bottom",
                        output_path: str = None) -> str:
        """添加文字覆盖"""
        try:
            clip = VideoFileClip(video_path)
            
            # 创建文字剪辑
            txt_clip = TextClip(text, fontsize=70, color='white', font='Arial-Bold')
            txt_clip = txt_clip.set_position(position).set_duration(clip.duration)
            
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
            logger.error(f"添加文字失败: {str(e)}", exc_info=True)
            return None
    
    def resize_video(self, video_path: str, target_size: Tuple[int, int],
                    output_path: str) -> bool:
        """调整视频尺寸"""
        try:
            clip = VideoFileClip(video_path)
            resized = clip.fx(resize, target_size)         
            resized.write_videofile(output_path,
                                  codec='libx264',
                                  audio_codec='aac',
                                  fps=clip.fps)
            
            clip.close()
            resized.close()
            
            return True
        except Exception as e:
            logger.error(f"调整尺寸失败: {str(e)}", exc_info=True)
            return False
    
    def extract_audio(self, video_path: str, output_path: str) -> bool:
        """提取音频"""
        try:
            clip = VideoFileClip(video_path)
            audio = clip.audio
            if audio is None:
                return False
            audio.write_audiofile(output_path)
            
            clip.close()
            audio.close()
            
            return True
        except Exception as e:
            logger.error(f"提取音频失败: {str(e)}", exc_info=True)
            return False
    
    def merge_videos(self, video_paths: List[str], output_path: str) -> bool:
        """顺序合并多个视频为长视频"""
        return self.merge_videos_with_audio(video_paths, output_path, None)
    
    def merge_videos_with_audio(self, video_paths: List[str], output_path: str, 
                               narration_audio_path: Optional[str] = None,
                               audio_volume: float = 0.8, video_volume: float = 0.3) -> bool:
        """顺序合并多个视频为长视频，并可选添加旁白音频"""
        try:
            from moviepy.editor import concatenate_videoclips, CompositeAudioClip
            
            logger.info(f"开始合并 {len(video_paths)} 个视频片段...")
            clips = []
            
            for i, path in enumerate(video_paths):
                if not os.path.exists(path):
                    logger.warning(f"警告: 视频文件不存在 {path}")
                    continue
                
                try:
                    clip = VideoFileClip(path)
                    # 确保所有视频有相同的分辨率和帧率
                    if i == 0:
                        # 第一个视频作为参考
                        target_size = clip.size
                        target_fps = clip.fps
                    else:
                        # 其他视频调整到相同参数
                        if clip.size != target_size:
                            clip = clip.resize(target_size)
                        if abs(clip.fps - target_fps) > 0.1:
                            clip = clip.set_fps(target_fps)
                    
                    clips.append(clip)
                    logger.debug(f"加载视频片段 {i+1}: {os.path.basename(path)} ({clip.duration:.1f}秒)")
                    
                except Exception as e:
                    logger.error(f"加载视频片段失败 {path}: {e}")
                    continue
            
            if not clips:
                logger.error("错误: 没有可用的视频片段")
                return False
            
            # 顺序连接视频
            if len(clips) == 1:
                final_video = clips[0]
            else:
                logger.info(f"顺序连接 {len(clips)} 个视频片段...")
                final_video = concatenate_videoclips(clips, method="compose")
            
            # 如果有旁白音频，添加到视频中
            if narration_audio_path and os.path.exists(narration_audio_path):
                logger.info(f"添加旁白音频: {narration_audio_path}")
                try:
                    # 加载旁白音频
                    narration_audio = AudioFileClip(narration_audio_path)
                    
                    # 调整旁白音频长度匹配视频
                    video_duration = final_video.duration
                    if narration_audio.duration > video_duration:
                        # 如果音频太长，截断
                        narration_audio = narration_audio.subclip(0, video_duration)
                    elif narration_audio.duration < video_duration:
                        # 如果音频太短，循环播放或静音补齐
                        logger.warning(f"旁白音频 ({narration_audio.duration:.1f}s) 短于视频 ({video_duration:.1f}s)")
                    
                    # 调整音量
                    narration_audio = narration_audio.volumex(audio_volume)
                    
                    # 获取原视频音频并降低音量
                    if final_video.audio is not None:
                        original_audio = final_video.audio.volumex(video_volume)
                        # 混合音频
                        mixed_audio = CompositeAudioClip([original_audio, narration_audio])
                    else:
                        # 如果原视频没有音频，直接使用旁白
                        mixed_audio = narration_audio
                    
                    # 设置新音频
                    final_video = final_video.set_audio(mixed_audio)
                    logger.info("旁白音频添加成功")
                    
                except Exception as e:
                    logger.error(f"添加旁白音频失败: {e}", exc_info=True)
                    # 继续处理，即使音频失败
            
            logger.info(f"写入最终视频: {output_path}")
            final_video.write_videofile(output_path,
                                      codec='libx264',
                                      audio_codec='aac',
                                      temp_audiofile='temp-audio.m4a',
                                      remove_temp=True)
            
            # 清理资源
            for clip in clips:
                clip.close()
            final_video.close()
            
            # 验证输出文件
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"合并完成: {output_path} ({file_size:,} bytes)")
                return True
            else:
                logger.error("错误: 输出文件未生成")
                return False
                
        except Exception as e:
            logger.error(f"合并视频失败: {str(e)}", exc_info=True)
            return False

    def merge_with_narration(self, video_path: str, narration_audio: str,
                            output_path: str, audio_volume: float = 1.0,
                            video_volume: float = 0.3) -> bool:
        """
        为单个视频添加旁白音频

        Args:
            video_path: 原视频路径
            narration_audio: 旁白音频路径
            output_path: 输出视频路径
            audio_volume: 旁白音量 (0.0-1.0)
            video_volume: 原视频音量 (0.0-1.0)

        Returns:
            是否成功
        """
        return self.merge_videos_with_audio(
            video_paths=[video_path],
            output_path=output_path,
            narration_audio_path=narration_audio,
            audio_volume=audio_volume,
            video_volume=video_volume
        ) 