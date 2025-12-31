"""
视频分析器 - 专门负责视频内容分析
分离关注点：专门处理视频相关的分析任务
"""

import logging
from typing import Dict, Any, Optional, List
from app.services.analysis.content_analyzer import content_analyzer

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """
    视频分析器 - 专门负责视频内容分析任务
    职责：
    1. 视频内容分析
    2. 视频改进建议
    3. 关键时刻提取
    4. 视频脚本生成
    """
    
    def __init__(self):
        self.content_analyzer = content_analyzer
        # 延迟导入ASR服务，避免循环导入
        self._asr_service = None
    
    @property
    def asr_service(self):
        """延迟加载ASR服务"""
        if self._asr_service is None:
            try:
                from app.services.audio.asr_service import asr_service
                self._asr_service = asr_service
            except ImportError:
                logger.warning("ASR服务不可用")
                self._asr_service = None
        return self._asr_service
    
    def analyze_video_content(
        self, 
        video_info: Dict[str, Any], 
        extracted_text: str = None,
        use_asr: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        分析视频内容（同步版本）
        
        Args:
            video_info: 视频基本信息
            extracted_text: 提取的视频文本（字幕、语音转文字等）
            use_asr: 是否使用ASR进行语音识别
            **kwargs: 其他参数
            
        Returns:
            结构化的视频分析结果
        """
        try:
            # 如果没有提供extracted_text且启用ASR，尝试从视频中提取语音
            if not extracted_text and use_asr and self.asr_service:
                video_path = video_info.get("file_path")
                if video_path:
                    try:
                        # 使用ASR提取语音内容 - 修复事件循环问题
                        import asyncio
                        
                        # 检查是否已经在事件循环中
                        try:
                            loop = asyncio.get_running_loop()
                            # 如果已经在事件循环中，创建任务而不是运行新的循环
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    lambda: asyncio.run(self.asr_service.transcribe_video(
                                        video_path, 
                                        language=kwargs.get('language', 'zh-CN')
                                    ))
                                )
                                asr_result = future.result(timeout=60)  # 60秒超时
                        except RuntimeError:
                            # 没有运行的事件循环，可以直接使用asyncio.run
                            asr_result = asyncio.run(self.asr_service.transcribe_video(
                                video_path, 
                                language=kwargs.get('language', 'zh-CN')
                            ))
                        
                        if asr_result and asr_result.text:
                            extracted_text = asr_result.text
                            logger.info(f"ASR提取语音成功: {len(extracted_text)} 字符")
                            
                            # 将ASR结果添加到video_info中
                            video_info["asr_result"] = asr_result.to_dict()
                        else:
                            logger.warning("ASR未能提取到语音内容")
                    except Exception as e:
                        logger.error(f"ASR语音提取失败: {str(e)}")
                        # ASR失败不影响其他分析，继续进行
            
            # 构建分析内容
            analysis_content = self._build_video_content_for_analysis(video_info, extracted_text)
            
            if not analysis_content.strip():
                return {
                    "success": False,
                    "error": "没有可分析的视频内容",
                    "analysis_type": "video",
                    "video_info": video_info
                }
            
            # 使用内容分析器进行分析
            result = self.content_analyzer.analyze_general_content(
                content=analysis_content,
                analysis_type="general",
                timeout=kwargs.get('timeout', 30),  # 增加基础分析超时到30秒
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 1024)
            )
            
            # 添加视频信息到结果中
            if result["success"]:
                result["video_info"] = video_info
                result["analysis_type"] = "video"
                result["used_asr"] = bool(extracted_text and use_asr)
            else:
                result["video_info"] = video_info
                result["analysis_type"] = "video"
                result["used_asr"] = False
            
            return result
                
        except Exception as e:
            logger.error(f"视频内容分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"视频内容分析异常: {str(e)}",
                "analysis_type": "video",
                "video_info": video_info
            }

    def suggest_improvements(
        self, 
        analysis_result: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        基于分析结果提供改进建议（同步版本）
        
        Args:
            analysis_result: 视频分析结果
            **kwargs: 其他参数
            
        Returns:
            改进建议结果
        """
        try:
            # 构建改进建议的输入内容
            improvement_content = self._build_improvement_content(analysis_result)
            
            # 使用内容分析器生成改进建议
            result = self.content_analyzer.suggest_improvements(
                content=improvement_content,
                content_type="video",
                timeout=kwargs.get('timeout', 25),  # 增加改进建议超时到25秒
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 800)
            )
            
            return result
                
        except Exception as e:
            logger.error(f"改进建议生成失败: {str(e)}")
            return {
                "success": False,
                "error": f"改进建议生成异常: {str(e)}"
            }
    
    def extract_key_moments(
        self, 
        transcript: str, 
        max_moments: int = 5,
        timestamps: List = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        从转录文本中提取关键时刻（同步版本）
        
        Args:
            transcript: 转录文本
            max_moments: 最大关键时刻数量
            timestamps: 时间戳信息 [(start_time, end_time, text)]
            **kwargs: 其他参数
            
        Returns:
            关键时刻提取结果
        """
        try:
            if not transcript or not transcript.strip():
                return {
                    "success": False,
                    "error": "没有提供转录文本"
                }
            
            # 构建关键时刻提取的提示内容
            moments_content = self._build_key_moments_content(transcript, max_moments, timestamps)
            
            # 使用内容分析器提取关键要点
            result = self.content_analyzer.extract_key_points(
                content=moments_content,
                max_points=max_moments,
                timeout=kwargs.get('timeout', 20),  # 增加关键要点超时到20秒
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 600)
            )
            
            # 重新格式化结果以适应关键时刻的语义
            if result["success"]:
                key_moments = result["key_points"]
                
                # 如果有时间戳信息，尝试为关键时刻添加时间信息
                if timestamps:
                    key_moments = self._add_timestamps_to_moments(key_moments, timestamps)
                
                return {
                    "success": True,
                    "key_moments": key_moments,
                    "max_moments": max_moments,
                    "provider": result.get("provider"),
                    "has_timestamps": bool(timestamps)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"关键时刻提取失败: {str(e)}")
            return {
                "success": False,
                "error": f"关键时刻提取异常: {str(e)}"
            }
    
    def generate_content_script(
        self, 
        topic: str, 
        style: str = "informative", 
        duration_minutes: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成内容脚本（同步版本）
        
        Args:
            topic: 主题
            style: 风格
            duration_minutes: 时长（分钟）
            **kwargs: 其他参数
            
        Returns:
            脚本生成结果
        """
        try:
            # 构建脚本生成内容
            script_content = self._build_script_content(topic, style, duration_minutes)
            
            # 使用内容分析器生成内容（这里复用分析器的能力）
            result = self.content_analyzer.analyze_general_content(
                content=script_content,
                analysis_type="script_generation",
                timeout=kwargs.get('timeout', 25),
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 1500)
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "script": result["summary"],
                    "topic": topic,
                    "style": style,
                    "duration_minutes": duration_minutes,
                    "provider": result.get("provider")
                }
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "topic": topic
                }
                
        except Exception as e:
            logger.error(f"脚本生成失败: {str(e)}")
            return {
                "success": False,
                "error": f"脚本生成异常: {str(e)}",
                "topic": topic
            }

    def analyze_video_with_asr(
        self,
        video_path: str,
        language: str = "zh-CN",
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用ASR分析视频内容的便捷方法
        
        Args:
            video_path: 视频文件路径
            language: 语言代码
            **kwargs: 其他参数
            
        Returns:
            包含ASR结果的完整分析结果
        """
        try:
            if not self.asr_service:
                return {
                    "success": False,
                    "error": "ASR服务不可用"
                }
            
            # 构建视频信息
            video_info = {
                "file_path": video_path,
                "title": kwargs.get("title", "未知视频"),
                "duration": kwargs.get("duration"),
                "platform": kwargs.get("platform", "本地")
            }
            
            # 使用ASR分析
            result = self.analyze_video_content(
                video_info=video_info,
                use_asr=True,
                language=language,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"ASR视频分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"ASR视频分析异常: {str(e)}"
            }

    def _build_video_content_for_analysis(
        self, 
        video_info: Dict[str, Any], 
        extracted_text: str = None
    ) -> str:
        """构建用于分析的视频内容"""
        content_parts = []
        
        # 添加视频基本信息
        if video_info:
            content_parts.append("=== 视频基本信息 ===")
            
            if "title" in video_info and video_info["title"]:
                content_parts.append(f"标题: {video_info['title']}")
            
            if "description" in video_info and video_info["description"]:
                # 限制描述长度
                description = video_info["description"][:800] + "..." if len(video_info["description"]) > 800 else video_info["description"]
                content_parts.append(f"描述: {description}")
            
            if "platform" in video_info and video_info["platform"]:
                content_parts.append(f"平台: {video_info['platform']}")
            
            if "duration" in video_info and video_info["duration"]:
                # 处理不同格式的时长
                duration = video_info["duration"]
                if isinstance(duration, (int, float)):
                    # 数字格式的时长（秒）
                    duration_min = int(duration) // 60
                    duration_sec = int(duration) % 60
                    content_parts.append(f"时长: {duration_min}分{duration_sec}秒")
                elif isinstance(duration, str):
                    # 字符串格式的时长，直接使用
                    content_parts.append(f"时长: {duration}")
                else:
                    # 其他格式，转换为字符串
                    content_parts.append(f"时长: {str(duration)}")
            
            # 添加ASR结果信息
            if "asr_result" in video_info:
                asr_info = video_info["asr_result"]
                content_parts.append(f"语音识别提供商: {asr_info.get('provider', '未知')}")
                content_parts.append(f"语音识别置信度: {asr_info.get('confidence', 0):.2f}")
        
        # 添加提取的文本内容（包括ASR结果）
        if extracted_text and extracted_text.strip():
            content_parts.append("\n=== 视频语音内容 ===")
            # 限制文本长度
            text_content = extracted_text[:2000] + "..." if len(extracted_text) > 2000 else extracted_text
            content_parts.append(text_content)
        
        return "\n".join(content_parts)
    
    def _build_improvement_content(self, analysis_result: Dict[str, Any]) -> str:
        """构建改进建议的输入内容"""
        content_parts = []
        
        # 添加分析摘要
        if analysis_result.get("summary"):
            content_parts.append("=== 当前分析结果 ===")
            content_parts.append(analysis_result["summary"])
        
        # 添加视频信息
        video_info = analysis_result.get("video_info", {})
        if video_info:
            content_parts.append("\n=== 视频信息 ===")
            if video_info.get("title"):
                content_parts.append(f"标题: {video_info['title']}")
            if video_info.get("platform"):
                content_parts.append(f"平台: {video_info['platform']}")
            if video_info.get("duration"):
                # 处理不同格式的时长
                duration = video_info["duration"]
                if isinstance(duration, (int, float)):
                    # 数字格式的时长（秒）
                    duration_min = int(duration) // 60
                    duration_sec = int(duration) % 60
                    content_parts.append(f"时长: {duration_min}分{duration_sec}秒")
                elif isinstance(duration, str):
                    # 字符串格式的时长，直接使用
                    content_parts.append(f"时长: {duration}")
                else:
                    # 其他格式，转换为字符串
                    content_parts.append(f"时长: {str(duration)}")
            
            # 添加ASR信息
            if video_info.get("asr_result"):
                asr_info = video_info["asr_result"]
                content_parts.append(f"包含语音内容: 是 (置信度: {asr_info.get('confidence', 0):.2f})")
            
            # 添加是否使用了ASR的信息
            if analysis_result.get("used_asr"):
                content_parts.append("分析方式: 包含语音内容分析")
        
        # 如果所有部分都为空，提供一个默认的描述
        if not content_parts:
            content_parts.append("=== 视频内容分析 ===")
            content_parts.append("这是一个视频内容分析的结果，需要提供改进建议。")
            content_parts.append("分析类型: " + analysis_result.get("analysis_type", "general"))
        
        result = "\n".join(content_parts)
        
        # 确保返回的内容不为空
        if not result.strip():
            result = "请为以下视频内容提供改进建议：视频分析已完成，需要改进建议。"
        
        return result
    
    def _build_key_moments_content(self, transcript: str, max_moments: int, timestamps: List = None) -> str:
        """构建关键时刻提取的输入内容"""
        content = f"""=== 视频转录文本分析 ===

                请从以下视频转录文本中提取{max_moments}个最重要的关键时刻：

                转录内容：
                {transcript[:2000]}

                要求：
                - 识别内容的转折点、高潮、重要信息点
                - 每个关键时刻简洁描述
                - 按时间或重要性排序"""
        
        if timestamps:
            content += "\n- 如果可能，请结合时间戳信息定位关键时刻"
        
        return content
    
    def _build_script_content(self, topic: str, style: str, duration_minutes: int) -> str:
        """构建脚本生成的输入内容"""
        style_descriptions = {
            "informative": "信息性强、逻辑清晰、专业可信",
            "entertaining": "轻松幽默、生动有趣、娱乐性强",
            "educational": "教育性、循序渐进、易于理解",
            "promotional": "宣传性、说服力强、行动导向"
        }
        
        style_desc = style_descriptions.get(style, "通用风格")
        
        content = f"""=== 视频脚本创作任务 ===
            请为以下主题创作一个视频脚本：
            主题: {topic}
            风格: {style}（{style_desc}）
            目标时长: {duration_minutes}分钟
            脚本要求：
            1. 结构清晰：开头、中间、结尾
            2. 语言流畅，适合口述
            3. 内容充实，信息密度适中
            4. 符合指定风格特点
            5. 时长控制在{duration_minutes}分钟左右

            请创作完整的视频脚本内容。"""
        
        return content
    
    def _add_timestamps_to_moments(self, key_moments: List[str], timestamps: List) -> List[Dict]:
        """为关键时刻添加时间戳信息"""
        enhanced_moments = []
        
        for moment in key_moments:
            # 尝试在时间戳中找到相关的文本
            best_match = None
            best_score = 0
            
            for start_time, end_time, text in timestamps:
                # 简单的文本匹配评分
                score = self._calculate_text_similarity(moment, text)
                if score > best_score:
                    best_score = score
                    best_match = (start_time, end_time, text)
            
            moment_dict = {
                "description": moment,
                "timestamp": best_match[0] if best_match else None,
                "end_time": best_match[1] if best_match else None,
                "original_text": best_match[2] if best_match else None,
                "confidence": best_score
            }
            
            enhanced_moments.append(moment_dict)
        
        return enhanced_moments
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简单实现）"""
        if not text1 or not text2:
            return 0.0
        
        # 简单的关键词匹配
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

# 全局视频分析器实例
video_analyzer = VideoAnalyzer() 