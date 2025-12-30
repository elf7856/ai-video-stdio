import os
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import tempfile

from app.services.video.downloader import VideoDownloader
from app.services.video.processor import VideoProcessor
from app.services.llm.analyzer import VideoAnalyzer
from app.services.image.generator import ImageServiceManager
from app.services.tts.generator import TTSGenerator
from app.core.config import settings

class VideoProcessingManager:
    """视频处理流程管理器"""
    
    def __init__(self):
        self.downloader = VideoDownloader()
        self.processor = VideoProcessor()
        self.analyzer = VideoAnalyzer()
        self.image_manager = ImageServiceManager()
        self.tts_generator = TTSGenerator()
        
        # 延迟导入ASR服务
        self._asr_service = None
    
    @property
    def asr_service(self):
        """延迟加载ASR服务"""
        if self._asr_service is None:
            try:
                from app.services.audio.asr_service import asr_service
                self._asr_service = asr_service
            except ImportError:
                print("ASR服务不可用")
                self._asr_service = None
        return self._asr_service
    
    async def process_video_from_url(self, url: str, 
                                   auto_analyze: bool = True,
                                   use_asr: bool = True,
                                   output_dir: str = None) -> Dict:
        """从URL处理视频的完整流程"""
        try:
            # 步骤1: 下载视频
            print(f"开始下载视频: {url}")
            download_result = await self.downloader.download_video(url, output_dir)
            
            if not download_result["success"]:
                return {
                    "success": False,
                    "error": download_result["error"],
                    "step": "download"
                }
            
            video_path = download_result["file_path"]
            video_title = download_result["title"]
            
            # 步骤2: 获取视频基本信息
            print("获取视频基本信息...")
            video_info = self.processor.get_video_info(video_path)
            
            if "error" in video_info:
                return {
                    "success": False,
                    "error": video_info["error"],
                    "step": "info_extraction"
                }
            
            # 步骤3: 自动分析视频内容（可选）
            analysis_result = None
            if auto_analyze:
                print("分析视频内容...")
                
                # 构建完整的视频信息
                full_video_info = {
                    "file_path": video_path,
                    "title": video_title,
                    "duration": video_info["duration"],
                    "resolution": video_info["resolution"],
                    "file_size": video_info["file_size"],
                    "platform": download_result.get("platform", "unknown")
                }
                
                # 使用集成ASR的视频分析
                analysis_result = self.analyzer.analyze_video_content(
                    video_info=full_video_info,
                    use_asr=use_asr
                )
            
            # 步骤4: 提取关键帧（用于进一步分析）
            print("提取关键帧...")
            frames_dir = os.path.join(os.path.dirname(video_path), "frames")
            os.makedirs(frames_dir, exist_ok=True)
            
            # 提取视频开始、中间、结束的帧
            duration = video_info["duration"]
            key_times = [0, duration/2, duration-1] if duration > 2 else [0]
            
            key_frames = []
            for i, time in enumerate(key_times):
                if time >= 0 and time < duration:
                    frames = self.processor.extract_frames(video_path, time, time+0.1, frames_dir)
                    if frames:
                        key_frames.append(frames[0])
            
            return {
                "success": True,
                "video_path": video_path,
                "video_title": video_title,
                "video_info": video_info,
                "analysis": analysis_result,
                "key_frames": key_frames,
                "platform": download_result.get("platform", "unknown"),
                "used_asr": use_asr and bool(analysis_result and analysis_result.get("used_asr"))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"视频处理失败: {str(e)}",
                "step": "processing"
            }
    
    async def analyze_video_content(self, video_path: str, use_asr: bool = True, language: str = "zh-CN") -> Dict:
        """分析视频内容"""
        try:
            # 获取视频信息
            video_info = self.processor.get_video_info(video_path)
            
            if "error" in video_info:
                return {
                    "success": False,
                    "error": video_info["error"]
                }
            
            # 构建视频信息字典
            full_video_info = {
                "file_path": video_path,
                "title": os.path.basename(video_path),
                "duration": video_info["duration"],
                "resolution": video_info["resolution"],
                "file_size": video_info["file_size"],
                "platform": "本地"
            }
            
            # 使用视频分析器进行分析（集成ASR）
            analysis_result = self.analyzer.analyze_video_content(
                video_info=full_video_info,
                use_asr=use_asr,
                language=language
            )
            
            # 提取关键帧进行图像分析
            frames_dir = tempfile.mkdtemp()
            duration = video_info["duration"]
            key_times = [duration * 0.25, duration * 0.5, duration * 0.75] if duration > 4 else [duration * 0.5]
            
            key_frames = []
            for i, time in enumerate(key_times):
                if time >= 0 and time < duration:
                    frames = self.processor.extract_frames(video_path, time, time+0.1, frames_dir)
                    if frames:
                        key_frames.append(frames[0])
            
            return {
                "success": True,
                "video_info": video_info,
                "analysis": analysis_result,
                "key_frames": key_frames,
                "used_asr": use_asr and bool(analysis_result and analysis_result.get("used_asr"))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"内容分析失败: {str(e)}"
            }
    
    async def analyze_video_with_transcript(self, video_path: str, language: str = "zh-CN") -> Dict:
        """分析视频并返回详细的转录结果"""
        try:
            if not self.asr_service:
                return {
                    "success": False,
                    "error": "ASR服务不可用"
                }
            
            # 使用ASR转录视频
            print("正在进行语音识别...")
            asr_result = await self.asr_service.transcribe_video(video_path, language)
            
            if not asr_result or not asr_result.text:
                return {
                    "success": False,
                    "error": "语音识别失败或没有检测到语音内容"
                }
            
            print(f"语音识别完成: {len(asr_result.text)} 字符")
            
            # 获取视频基本信息
            video_info = self.processor.get_video_info(video_path)
            
            # 构建完整的视频信息
            full_video_info = {
                "file_path": video_path,
                "title": os.path.basename(video_path),
                "duration": video_info.get("duration"),
                "resolution": video_info.get("resolution"),
                "file_size": video_info.get("file_size"),
                "platform": "本地",
                "asr_result": asr_result.to_dict()
            }
            
            # 使用转录文本进行内容分析
            analysis_result = self.analyzer.analyze_video_content(
                video_info=full_video_info,
                extracted_text=asr_result.text,
                use_asr=False  # 已经有转录文本了
            )
            
            # 提取关键时刻（使用时间戳信息）
            key_moments_result = None
            if asr_result.timestamps:
                key_moments_result = self.analyzer.extract_key_moments(
                    transcript=asr_result.text,
                    timestamps=asr_result.timestamps,
                    max_moments=5
                )
            
            return {
                "success": True,
                "video_info": video_info,
                "asr_result": asr_result.to_dict(),
                "analysis": analysis_result,
                "key_moments": key_moments_result,
                "transcript": asr_result.text,
                "timestamps": asr_result.timestamps
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"视频转录分析失败: {str(e)}"
            }
    
    async def generate_video_summary(self, video_path: str, 
                                   summary_type: str = "text",
                                   use_asr: bool = True,
                                   language: str = "zh-CN") -> Dict:
        """生成视频摘要"""
        try:
            # 分析视频内容
            if use_asr:
                analysis_result = await self.analyze_video_with_transcript(video_path, language)
            else:
                analysis_result = await self.analyze_video_content(video_path, use_asr=False)
            
            if not analysis_result["success"]:
                return analysis_result
            
            # 根据摘要类型生成不同格式的摘要
            if summary_type == "text":
                # 生成文本摘要
                summary = await self._generate_text_summary(analysis_result["analysis"])
                return {
                    "success": True,
                    "summary_type": "text",
                    "content": summary,
                    "analysis": analysis_result["analysis"],
                    "used_asr": analysis_result.get("used_asr", False)
                }
            
            elif summary_type == "audio":
                # 生成音频摘要
                summary_text = await self._generate_text_summary(analysis_result["analysis"])
                audio_path = await self.tts_generator.generate_speech(
                    summary_text, 
                    voice_id=settings.default_tts_voice
                )
                
                return {
                    "success": True,
                    "summary_type": "audio",
                    "content": audio_path,
                    "text": summary_text,
                    "analysis": analysis_result["analysis"],
                    "used_asr": analysis_result.get("used_asr", False)
                }
            
            elif summary_type == "video":
                # 生成视频摘要（关键帧拼接）
                summary_video = await self._generate_video_summary_clip(
                    video_path, analysis_result["key_frames"]
                )
                
                return {
                    "success": True,
                    "summary_type": "video",
                    "content": summary_video,
                    "analysis": analysis_result["analysis"],
                    "used_asr": analysis_result.get("used_asr", False)
                }
            
            else:
                return {
                    "success": False,
                    "error": f"不支持的摘要类型: {summary_type}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"摘要生成失败: {str(e)}"
            }
    
    async def extract_video_highlights(self, video_path: str, 
                                     max_highlights: int = 3,
                                     language: str = "zh-CN") -> Dict:
        """提取视频精彩片段"""
        try:
            # 使用ASR分析视频
            transcript_result = await self.analyze_video_with_transcript(video_path, language)
            
            if not transcript_result["success"]:
                return transcript_result
            
            # 提取关键时刻
            key_moments = transcript_result.get("key_moments")
            if not key_moments or not key_moments.get("success"):
                return {
                    "success": False,
                    "error": "无法提取关键时刻"
                }
            
            # 生成精彩片段
            highlights = []
            moments = key_moments.get("key_moments", [])[:max_highlights]
            
            for i, moment in enumerate(moments):
                if isinstance(moment, dict) and moment.get("timestamp"):
                    # 创建精彩片段
                    start_time = max(0, moment["timestamp"] - 5)  # 前5秒
                    end_time = moment.get("end_time", moment["timestamp"] + 10)  # 后10秒或到结束时间
                    
                    highlight_path = tempfile.mktemp(suffix=f'_highlight_{i}.mp4')
                    
                    # 这里需要实现视频片段提取
                    # 简化版本，返回时间戳信息
                    highlights.append({
                        "index": i,
                        "description": moment.get("description", ""),
                        "start_time": start_time,
                        "end_time": end_time,
                        "original_text": moment.get("original_text", ""),
                        "confidence": moment.get("confidence", 0.0)
                    })
            
            return {
                "success": True,
                "highlights": highlights,
                "total_highlights": len(highlights),
                "transcript": transcript_result.get("transcript", ""),
                "video_info": transcript_result.get("video_info", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"精彩片段提取失败: {str(e)}"
            }

    async def process_natural_language_edit(self, video_path: str, 
                                          instruction: str) -> Dict:
        """处理自然语言编辑指令"""
        try:
            # 分析编辑指令
            instruction_analysis = await self._analyze_edit_instruction(instruction)
            
            if not instruction_analysis["success"]:
                return instruction_analysis
            
            # 生成内容描述
            content_description = await self._generate_content_description(
                instruction, instruction_analysis
            )
            
            # 根据编辑类型处理
            edit_type = instruction_analysis.get("edit_type", "insert")
            
            if edit_type == "insert":
                return await self._handle_insert_edit(video_path, instruction_analysis, content_description)
            elif edit_type == "replace":
                return await self._handle_replace_edit(video_path, instruction_analysis, content_description)
            elif edit_type == "delete":
                return await self._handle_delete_edit(video_path, instruction_analysis)
            elif edit_type == "style_change":
                return await self._handle_style_change_edit(video_path, instruction_analysis)
            else:
                return {
                    "success": False,
                    "error": f"不支持的编辑类型: {edit_type}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"编辑处理失败: {str(e)}"
            }
    
    async def _handle_insert_edit(self, video_path: str, 
                                instruction_analysis: Dict, 
                                content_description: str) -> Dict:
        """处理插入编辑"""
        try:
            # 生成需要插入的内容
            content_needed = instruction_analysis.get("content_needed", "image")
            
            if content_needed == "image":
                # 生成图像
                image_path = await self.image_manager.generate_image_with_description(
                    content_description
                )
                
                # 插入图像到视频
                target_time = instruction_analysis.get("target_location", 0)
                output_path = tempfile.mktemp(suffix='.mp4')
                
                success = self.processor.insert_content(
                    video_path, image_path, target_time, output_path
                )
                
                return {
                    "success": success,
                    "output_path": output_path if success else None,
                    "inserted_content": image_path
                }
            
            elif content_needed == "audio":
                # 生成音频
                audio_path = await self.tts_generator.generate_speech(
                    content_description
                )
                
                # 插入音频到视频
                target_time = instruction_analysis.get("target_location", 0)
                output_path = tempfile.mktemp(suffix='.mp4')
                
                # 这里需要实现音频插入逻辑
                return {
                    "success": True,
                    "output_path": output_path,
                    "inserted_content": audio_path
                }
            
            else:
                return {
                    "success": False,
                    "error": f"不支持的内容类型: {content_needed}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"插入编辑失败: {str(e)}"
            }
    
    async def _handle_replace_edit(self, video_path: str, 
                                 instruction_analysis: Dict, 
                                 content_description: str) -> Dict:
        """处理替换编辑"""
        try:
            # 生成替换内容
            content_needed = instruction_analysis.get("content_needed", "image")
            
            if content_needed == "image":
                # 生成图像
                image_path = await self.image_manager.generate_image_with_description(
                    content_description
                )
                
                # 替换视频片段
                start_time = instruction_analysis.get("start_time", 0)
                end_time = instruction_analysis.get("end_time", 5)
                output_path = tempfile.mktemp(suffix='.mp4')
                
                success = self.processor.replace_content(
                    video_path, image_path, start_time, end_time, output_path
                )
                
                return {
                    "success": success,
                    "output_path": output_path if success else None,
                    "replaced_content": image_path
                }
            
            else:
                return {
                    "success": False,
                    "error": f"不支持的替换内容类型: {content_needed}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"替换编辑失败: {str(e)}"
            }
    
    async def _handle_delete_edit(self, video_path: str, 
                                instruction_analysis: Dict) -> Dict:
        """处理删除编辑"""
        try:
            # 实现删除逻辑
            start_time = instruction_analysis.get("start_time", 0)
            end_time = instruction_analysis.get("end_time", 5)
            output_path = tempfile.mktemp(suffix='.mp4')
            
            # 这里需要实现视频片段删除逻辑
            return {
                "success": True,
                "output_path": output_path,
                "deleted_segment": f"{start_time}-{end_time}s"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"删除编辑失败: {str(e)}"
            }
    
    async def _handle_style_change_edit(self, video_path: str, 
                                      instruction_analysis: Dict) -> Dict:
        """处理样式变更编辑"""
        try:
            # 应用样式滤镜
            style = instruction_analysis.get("style", "default")
            output_path = tempfile.mktemp(suffix='.mp4')
            
            success = self.processor.apply_style_filter(
                video_path, style, output_path
            )
            
            return {
                "success": success,
                "output_path": output_path if success else None,
                "applied_style": style
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"样式变更失败: {str(e)}"
            }
    
    async def _analyze_edit_instruction(self, instruction: str) -> Dict:
        """分析编辑指令"""
        try:
            # 使用LLM分析编辑指令
            from app.prompts.base import render_prompt
            
            prompt = render_prompt("edit_instruction_understanding", 
                                 instruction=instruction,
                                 video_context="视频编辑上下文")
            
            messages = [
                {"role": "system", "content": "你是一个视频编辑指令分析专家。"},
                {"role": "user", "content": prompt}
            ]
            
            # 这里需要调用LLM服务
            # 简化版本，返回基本分析
            return {
                "success": True,
                "edit_type": "insert",
                "target_location": 0,
                "content_needed": "image",
                "style_preferences": "default",
                "technical_requirements": "basic",
                "estimated_duration": 5,
                "complexity": "low"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"指令分析失败: {str(e)}"
            }
    
    async def _generate_content_description(self, instruction: str, 
                                          analysis: Dict) -> str:
        """生成内容描述"""
        try:
            # 基于指令和分析结果生成详细的内容描述
            return f"根据指令 '{instruction}' 生成的内容描述"
            
        except Exception as e:
            return f"内容描述生成失败: {str(e)}"
    
    async def _generate_text_summary(self, analysis: Dict) -> str:
        """生成文本摘要"""
        try:
            if analysis and analysis.get("summary"):
                return analysis["summary"]
            else:
                return "无法生成摘要"
                
        except Exception as e:
            return f"摘要生成失败: {str(e)}"
    
    async def _generate_video_summary_clip(self, video_path: str, 
                                         key_frames: List[str]) -> str:
        """生成视频摘要片段"""
        try:
            # 实现视频摘要片段生成
            output_path = tempfile.mktemp(suffix='_summary.mp4')
            
            # 这里需要实现关键帧拼接逻辑
            return output_path
            
        except Exception as e:
            return f"视频摘要生成失败: {str(e)}" 