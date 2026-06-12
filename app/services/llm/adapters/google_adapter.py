#!/usr/bin/env python3
"""
Google Gemini官方SDK适配器
使用Google官方新版SDK实现LLM调用
"""

import os
import time
import logging
import io
from typing import List, Dict, Any, Optional
from PIL import Image

from .base import BaseLLMAdapter
from app.services.google_error_utils import format_google_api_error

logger = logging.getLogger(__name__)

class GoogleAdapter(BaseLLMAdapter):
    """Google Gemini官方新版SDK适配器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("google", config)
        self.provider = "google"
    
    def _setup(self) -> None:
        """初始化Google Gemini客户端"""
        try:
            from app.core.config import settings

            # 动态导入Google新版SDK
            try:
                from google import genai
                from google.genai import types

                self.genai = genai
                self.types = types

                # 优先用 Vertex AI key，没有则降级到 AI Studio
                if settings.vertex_api_key:
                    self.client = genai.Client(
                        vertexai=True,
                        api_key=settings.vertex_api_key,
                    )
                    logger.info("Google适配器使用 Vertex AI (api_key 模式)")
                elif settings.vertex_project_id:
                    self.client = genai.Client(
                        vertexai=True,
                        project=settings.vertex_project_id,
                        location=settings.vertex_location,
                    )
                    logger.info(f"Google适配器使用 Vertex AI (project={settings.vertex_project_id})")
                elif settings.google_api_key:
                    self.client = genai.Client(api_key=settings.google_api_key)
                    logger.info("Google适配器使用 AI Studio")
                else:
                    logger.error("未找到任何 Google API 密钥配置")
                    self.available = False
                    return

                # 模型配置
                self.model_name = self.config.get("model", "gemini-3-flash")
                
                # 为了兼容性，创建一个model对象的包装器
                self.model = self._create_model_wrapper()
                
                self.model_config = {
                    "max_output_tokens": self.config.get("max_tokens", 2000),
                    "temperature": self.config.get("temperature", 0.3),
                    "timeout": self.config.get("timeout", 10)
                }
                
                self.available = True
                logger.info(f"Google适配器初始化成功，模型: {self.model_name}")
                
            except ImportError:
                logger.error("Google GenAI SDK未安装，请运行: pip install google-genai")
                self.available = False
                
        except Exception as e:
            logger.error(f"Google适配器初始化失败: {e}")
            self.available = False
    
    def _create_model_wrapper(self):
        """创建一个模型包装器以保持兼容性"""
        class ModelWrapper:
            def __init__(self, client, model_name, types_module):
                self.client = client
                self.model_name = model_name
                self.types = types_module
            
            def generate_content(self, prompt, generation_config=None, stream=False):
                """兼容旧版API的generate_content方法"""
                # 如果是字符串提示，转换为新版格式
                if isinstance(prompt, str):
                    contents = [self.types.Content(
                        role="user",
                        parts=[self.types.Part(text=prompt)]
                    )]
                else:
                    contents = prompt
                
                # 新版SDK使用generate_content_stream方法实现流式调用
                if stream:
                    return self.client.models.generate_content_stream(
                        model=self.model_name,
                        contents=contents
                    )
                else:
                    return self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents
                    )
        
        return ModelWrapper(self.client, self.model_name, self.types)
    
    def is_available(self) -> bool:
        """检查适配器是否可用"""
        return self.available and hasattr(self, 'client')
    
    def call(
        self, 
        messages: List[Dict[str, str]], 
        timeout: int = 10,
        retry_count: int = 2,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用Google新版SDK进行文本生成
        """
        if not self.is_available():
            return {
                "success": False,
                "content": "",
                "provider": "google",
                "model": "",
                "usage": {},
                "error": "Google适配器不可用"
            }
        
        for attempt in range(retry_count + 1):
            try:
                # 转换消息格式为新版SDK格式
                contents = []
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    content = self.types.Content(
                        role=role,
                        parts=[self.types.Part(text=msg["content"])]
                    )
                    contents.append(content)
                
                # 调用新版API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
                
                # 检查响应
                if response.text and response.text.strip():
                    # 提取使用统计（新版SDK可能有不同的属性结构）
                    usage = {
                        "prompt_tokens": getattr(response, "prompt_token_count", 0),
                        "completion_tokens": getattr(response, "candidates_token_count", 0),
                        "total_tokens": getattr(response, "total_token_count", 0)
                    }
                    
                    return {
                        "success": True,
                        "content": response.text.strip(),
                        "provider": "google",
                        "model": self.model_name,
                        "usage": usage,
                        "error": None
                    }
                else:
                    error_msg = "响应为空或被安全过滤器阻止"
                    
                    return {
                        "success": False,
                        "content": "",
                        "provider": "google",
                        "model": self.model_name,
                        "usage": {},
                        "error": error_msg
                    }
                    
            except Exception as e:
                raw_error_msg = str(e)
                logger.warning(
                    "Google Gemini 文本调用失败详情: %s",
                    format_google_api_error(
                        e,
                        {
                            "model": self.model_name,
                            "attempt": attempt + 1,
                            "retry_count": retry_count,
                        },
                    ),
                )
                error_msg = raw_error_msg
                
                # 特定错误处理
                if "quota" in error_msg.lower():
                    error_msg = f"API配额已用完: {raw_error_msg}"
                elif "permission" in error_msg.lower():
                    error_msg = f"API权限不足: {raw_error_msg}"
                elif "safety" in error_msg.lower():
                    error_msg = f"内容被安全过滤器阻止: {raw_error_msg}"
                
                if attempt < retry_count:
                    logger.warning(f"Google API调用失败 (尝试 {attempt + 1}/{retry_count + 1}): {error_msg}")
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    logger.error(f"Google API调用最终失败: {error_msg}")
                    return {
                        "success": False,
                        "content": "",
                        "provider": "google",
                        "model": self.model_name,
                        "usage": {},
                        "error": error_msg
                    }
        
        # 如果循环结束仍未返回，返回默认错误响应
        return {
            "success": False,
            "content": "",
            "provider": "google",
            "model": self.model_name,
            "usage": {},
            "error": "未知错误：所有重试均失败"
        }
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """将消息列表转换为Gemini提示词格式"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self.is_available():
            return {
                "healthy": False,
                "error": "适配器不可用",
                "model": self.model_name if hasattr(self, 'model_name') else "unknown"
            }
        
        try:
            result = self.call(
                messages=[{"role": "user", "content": "请回复'OK'"}],
                timeout=5,
                retry_count=1
            )
            
            return {
                "healthy": result["success"],
                "model": self.model_name,
                "error": result.get("error")
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "model": self.model_name,
                "error": str(e)
            }
    
    def vision_call(
        self, 
        prompt: str, 
        image_data: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """
        视觉理解调用 - Google特有功能
        支持图像分析和理解
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Google适配器不可用"
            }
        
        try:
            from PIL import Image
            import io
            
            # 处理图像数据
            image = Image.open(io.BytesIO(image_data))
            
            # 生成配置
            generation_config = {
                "max_output_tokens": kwargs.get("max_tokens", self.model_config["max_output_tokens"]),
                "temperature": kwargs.get("temperature", self.model_config["temperature"])
            }
            
            # 使用已初始化的模型对象进行视觉理解
            # Google Gemini支持多模态输入：文本 + 图像
            response = self.model.generate_content(
                [prompt, image],
                generation_config=generation_config
            )
            
            # 检查响应
            if response.text and response.text.strip():
                # 提取使用统计
                usage = {}
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = {
                        "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                        "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                        "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                    }
                
                return {
                    "success": True,
                    "content": response.text.strip(),
                    "provider": "google",
                    "model": self.model_name,
                    "usage": usage,
                    "error": None
                }
            
            # 检查是否被安全过滤器阻止
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    if finish_reason and 'SAFETY' in str(finish_reason):
                        return {
                            "success": False,
                            "error": f"内容被安全过滤器阻止: {finish_reason}"
                        }
            
            return {
                "success": False,
                "error": "视觉理解响应为空或被过滤"
            }
            
        except Exception as e:
            error_msg = str(e)
            # 提供更详细的错误信息
            if "quota" in error_msg.lower():
                error_msg = "API配额已用完，请检查Google AI Studio配额"
            elif "permission" in error_msg.lower():
                error_msg = "API权限不足，请检查API密钥权限"
            elif "safety" in error_msg.lower():
                error_msg = "内容违反安全政策，请修改输入内容"
            
            return {
                "success": False,
                "error": f"视觉理解调用失败: {error_msg}"
            }
    
    def stream_call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        流式调用 - 返回文本迭代器

        Yields:
            文本字符串片段
        """
        if not self.is_available():
            logger.error("Google适配器不可用")
            yield ""
            return

        try:
            prompt = self._convert_messages_to_prompt(messages)

            generation_config = {
                "max_output_tokens": kwargs.get("max_tokens", self.model_config["max_output_tokens"]),
                "temperature": kwargs.get("temperature", self.model_config["temperature"])
            }

            # 获取流式响应
            response_stream = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )

            # 从 Google 的响应对象中提取文本
            for chunk in response_stream:
                # Google Gemini 响应格式处理
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                elif hasattr(chunk, 'candidates') and chunk.candidates:
                    for candidate in chunk.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    yield part.text

        except Exception as e:
            logger.error(f"Google 流式调用��败: {e}")
            yield ""
