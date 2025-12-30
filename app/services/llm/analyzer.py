"""
LLM分析器 - 兼容性接口
重构后的简化版本，主要作为向后兼容的接口，内部调用新的分离架构
"""

import logging
from typing import Dict, Any, Optional, List, Iterator

# 导入新的分离架构
from app.services.llm.service import llm_service
from app.services.analysis.content_analyzer import content_analyzer
from app.services.analysis.video_analyzer import video_analyzer as new_video_analyzer

logger = logging.getLogger(__name__)

# 为了向后兼容，保留原有的类名和接口
class LLMService:
    """
    LLM服务兼容性接口 - 重定向到新的LLM服务
    """
    
    def __init__(self):
        self.service = llm_service
        self.available_providers = self.service.available_providers
    
    def analyze_content(
        self, 
        content: str, 
        analysis_type: str = "general",
        timeout: int = 15,
        retry_count: int = 2
    ) -> Dict[str, Any]:
        """分析内容 - 兼容性方法"""
        return content_analyzer.analyze_general_content(
            content=content,
            analysis_type=analysis_type,
            timeout=timeout,
            retry_count=retry_count
        )
    
    def complete(
        self, 
        messages: List[Dict], 
        task_type: str = "general",
        timeout: int = 15,
        retry_count: int = 2,
        **kwargs
    ) -> str:
        """通用LLM完成任务 - 兼容性方法"""
        result = self.service.call_llm(
            messages=messages,
            timeout=timeout,
            retry_count=retry_count,
            **kwargs
        )
        
        if result["success"]:
            return result["content"]
        else:
            raise Exception(result["error"])
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return self.service.health_check()


class VideoAnalyzer:
    """
    视频分析器兼容性接口 - 重定向到新的视频分析器
    """
    
    def __init__(self):
        self.analyzer = new_video_analyzer
        self.llm_service = llm_service  # 保持向后兼容
    
    def analyze_video_content(
        self, 
        video_info: Dict[str, Any], 
        extracted_text: str = None,
        timeout: int = 20,
        retry_count: int = 2
    ) -> Dict[str, Any]:
        """
        分析视频内容 - 兼容性方法（同步版本）
        """
        return self.analyzer.analyze_video_content(
            video_info=video_info,
            extracted_text=extracted_text,
            timeout=timeout,
            retry_count=retry_count
        )
    
    def suggest_improvements(
        self, 
        analysis_result: Dict[str, Any],
        timeout: int = 15,
        retry_count: int = 2
    ) -> Dict[str, Any]:
        """
        基于分析结果提供改进建议 - 兼容性方法（同步版本）
        """
        return self.analyzer.suggest_improvements(
            analysis_result=analysis_result,
            timeout=timeout,
            retry_count=retry_count
        )
    
    def generate_content_script(
        self, 
        topic: str, 
        style: str = "informative", 
        duration_minutes: int = 5,
        timeout: int = 25,
        retry_count: int = 2
    ) -> str:
        """
        生成内容脚本 - 兼容性方法（同步版本）
        """
        result = self.analyzer.generate_content_script(
            topic=topic,
            style=style,
            duration_minutes=duration_minutes,
            timeout=timeout,
            retry_count=retry_count
        )
        
        if result["success"]:
            return result["script"]
        else:
            return f"脚本生成失败: {result['error']}"
    
    def extract_key_moments(
        self, 
        transcript: str, 
        max_moments: int = 5,
        timeout: int = 12,
        retry_count: int = 2
    ) -> Dict[str, Any]:
        """
        从转录文本中提取关键时刻 - 兼容性方法（同步版本）
        """
        return self.analyzer.extract_key_moments(
            transcript=transcript,
            max_moments=max_moments,
            timeout=timeout,
            retry_count=retry_count
        )


# 简化的流式接口（如果需要的话）
class StreamingAnalyzer:
    """
    流式分析器 - 简化的流式接口
    注意：当前架构中LLM服务是同步的，流式功能需要额外实现
    """
    
    def __init__(self):
        self.service = llm_service
    
    def analyze_content_stream(
        self, 
        content: str, 
        analysis_type: str = "general",
        timeout: int = 15,
        retry_count: int = 2
    ) -> Iterator[str]:
        """
        流式分析内容 - 简化实现
        目前返回单次结果，后续可以扩展为真正的流式
        """
        try:
            result = content_analyzer.analyze_general_content(
                content=content,
                analysis_type=analysis_type,
                timeout=timeout,
                retry_count=retry_count
            )
            
            if result["success"]:
                # 模拟流式输出，将结果分块返回
                content_text = result["summary"]
                chunk_size = 50  # 每次返回50个字符
                
                for i in range(0, len(content_text), chunk_size):
                    chunk = content_text[i:i + chunk_size]
                    yield chunk
            else:
                yield f"错误：{result['error']}"
                
        except Exception as e:
            yield f"错误：分析失败 - {str(e)}"


# 全局实例，保持向后兼容
llm_service_compat = LLMService()
video_analyzer_compat = VideoAnalyzer()
streaming_analyzer = StreamingAnalyzer()

# 为了完全向后兼容，也可以直接暴露原来的变量名
llm_service = llm_service_compat  # 注意：这会覆盖导入的新llm_service，需要注意 