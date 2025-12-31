"""
内容分析器 - 负责具体的分析逻辑
分离关注点：专门处理内容分析的业务逻辑、提示词构建等
"""

import logging
from typing import Dict, Any, Optional, List
from app.services.llm.service import llm_service
from app.prompts.base import render_prompt

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """
    内容分析器 - 专门负责各种内容分析任务
    职责：
    1. 构建分析提示词
    2. 调用LLM服务
    3. 解析和格式化结果
    4. 提供不同类型的分析方法
    """
    
    def __init__(self):
        self.llm_service = llm_service
    
    def analyze_general_content(
        self, 
        content: str, 
        analysis_type: str = "general",
        max_content_length: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        通用内容分析
        
        Args:
            content: 要分析的内容
            analysis_type: 分析类型
            max_content_length: 最大内容长度
            **kwargs: 其他参数
            
        Returns:
            分析结果字典
        """
        try:
            # 截断过长的内容
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
                logger.info(f"内容过长，已截断到{max_content_length}字符")
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(content, analysis_type)
            
            # 调用LLM
            result = self.llm_service.simple_call(
                prompt=prompt,
                timeout=kwargs.get('timeout', 25),  # 增加默认超时到25秒
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 1024)
            )
            
            if result["success"]:
                # 解析和格式化结果
                return self._format_analysis_result(
                    raw_content=result["content"],
                    analysis_type=analysis_type,
                    provider=result.get("provider"),
                    original_content_length=len(content)
                )
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "analysis_type": analysis_type
                }
                
        except Exception as e:
            logger.error(f"内容分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"内容分析异常: {str(e)}",
                "analysis_type": analysis_type
            }
    
    def generate_summary(
        self, 
        content: str, 
        summary_length: str = "medium",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成内容摘要
        
        Args:
            content: 要总结的内容
            summary_length: 摘要长度 (short/medium/long)
            **kwargs: 其他参数
        """
        try:
            prompt = self._build_summary_prompt(content, summary_length)
            
            result = self.llm_service.simple_call(
                prompt=prompt,
                timeout=kwargs.get('timeout', 20),  # 增加默认超时到20秒
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 512)
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "summary": result["content"],
                    "summary_length": summary_length,
                    "provider": result.get("provider"),
                    "original_length": len(content)
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
                
        except Exception as e:
            logger.error(f"摘要生成失败: {str(e)}")
            return {
                "success": False,
                "error": f"摘要生成异常: {str(e)}"
            }
    
    def suggest_improvements(
        self, 
        content: str, 
        content_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成改进建议
        
        Args:
            content: 要改进的内容描述
            content_type: 内容类型
            **kwargs: 其他参数
        """
        try:
            prompt = self._build_improvement_prompt(content, content_type)
            
            result = self.llm_service.simple_call(
                prompt=prompt,
                timeout=kwargs.get('timeout', 20),  # 增加默认超时到20秒
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 800)
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "suggestions": result["content"],
                    "content_type": content_type,
                    "provider": result.get("provider")
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
                
        except Exception as e:
            logger.error(f"改进建议生成失败: {str(e)}")
            return {
                "success": False,
                "error": f"改进建议生成异常: {str(e)}"
            }
    
    def extract_key_points(
        self, 
        content: str, 
        max_points: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        提取关键要点
        
        Args:
            content: 要分析的内容
            max_points: 最大要点数量
            **kwargs: 其他参数
        """
        try:
            prompt = self._build_key_points_prompt(content, max_points)
            
            result = self.llm_service.simple_call(
                prompt=prompt,
                timeout=kwargs.get('timeout', 20),  # 增加默认超时到20秒
                retry_count=kwargs.get('retry_count', 2),
                max_tokens=kwargs.get('max_tokens', 600)
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "key_points": result["content"],
                    "max_points": max_points,
                    "provider": result.get("provider")
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
                
        except Exception as e:
            logger.error(f"关键要点提取失败: {str(e)}")
            return {
                "success": False,
                "error": f"关键要点提取异常: {str(e)}"
            }
    
    def _build_analysis_prompt(self, content: str, analysis_type: str) -> str:
        """构建分析提示词"""
        try:
            # 尝试使用提示词模板
            template_map = {
                "general": "content_analysis_basic",
                "educational": "content_analysis_educational", 
                "entertainment": "content_analysis_entertainment",
                "marketing": "content_analysis_marketing"
            }
            
            template_name = template_map.get(analysis_type, "content_analysis_basic")
            return render_prompt(template_name, content=content)
            
        except Exception as e:
            logger.warning(f"使用提示词模板失败: {e}，使用默认模板")
            # 回退到简单模板
            return f"""请分析以下内容并提供简洁的总结：
                内容：
                {content}

                请从以下角度进行分析：
                1. 主要内容概述
                2. 关键信息要点
                3. 内容特点和风格
                4. 目标受众分析

                请用简洁明了的中文回复，重点突出。"""

    def _build_summary_prompt(self, content: str, summary_length: str) -> str:
        """构建摘要提示词"""
        length_instructions = {
            "short": "用1-2句话简述",
            "medium": "用3-5句话概括", 
            "long": "用一段话详细总结"
        }
        
        instruction = length_instructions.get(summary_length, "用3-5句话概括")
        
        return f"""请{instruction}以下内容：

内容：
{content[:1500]}

要求：
- 保留主要信息
- 语言简洁明了
- 用中文回复"""

    def _build_improvement_prompt(self, content: str, content_type: str) -> str:
        """构建改进建议提示词"""
        return f"""基于以下{content_type}内容，请提供具体的改进建议：

内容描述：
{content}

请从以下方面提供建议：
1. 内容结构优化
2. 表达方式改进
3. 观众体验提升
4. 技术质量改进

请提供实用、具体的建议，用中文回复。"""

    def _build_key_points_prompt(self, content: str, max_points: int) -> str:
        """构建关键要点提示词"""
        return f"""请从以下内容中提取最重要的{max_points}个关键要点：

内容：
{content[:1200]}

要求：
- 每个要点简洁明了
- 按重要性排序
- 用中文回复
- 用数字编号列出"""

    def _format_analysis_result(
        self, 
        raw_content: str, 
        analysis_type: str,
        provider: str = None,
        original_content_length: int = 0
    ) -> Dict[str, Any]:
        """格式化分析结果"""
        try:
            # 尝试解析JSON格式的结果
            import json
            parsed_result = json.loads(raw_content)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "summary": parsed_result.get("summary", raw_content),
                "details": parsed_result,
                "provider": provider,
                "content_length": original_content_length
            }
            
        except json.JSONDecodeError:
            # 如果不是JSON，直接返回文本结果
            return {
                "success": True,
                "analysis_type": analysis_type,
                "summary": raw_content,
                "provider": provider,
                "content_length": original_content_length
            }
        except Exception as e:
            logger.error(f"格式化分析结果失败: {e}")
            return {
                "success": True,
                "analysis_type": analysis_type,
                "summary": raw_content,
                "provider": provider,
                "content_length": original_content_length,
                "format_error": str(e)
            }

# 全局内容分析器实例
content_analyzer = ContentAnalyzer() 