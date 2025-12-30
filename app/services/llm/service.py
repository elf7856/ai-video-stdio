"""
LLM服务 - 专门负责稳定的API调用
分离关注点：只处理LLM API的调用、重试、错误处理等基础功能
"""

import os
import json
import logging
import time
import ssl
import urllib3
from typing import Dict, Any, Optional, List, Iterator, Union
import litellm

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# 配置常量 - 更保守的设置，针对网络问题优化
DEFAULT_TIMEOUT = 8  # 减少到8秒，避免长时间等待导致的SSL问题
DEFAULT_RETRY_COUNT = 3  # 增加重试次数
DEFAULT_RETRY_DELAY = 2  # 增加重试间隔

class LLMService:
    """
    LLM服务管理器 - 专注于稳定的API调用
    职责：
    1. 管理多个LLM提供商
    2. 处理重试机制
    3. 网络配置和错误处理
    4. 提供统一的调用接口
    """
    
    def __init__(self):
        self.setup_api_keys()
        self._setup_network_config()
        self._setup_providers()
        
        if not self.available_providers:
            logger.warning("没有可用的LLM提供商！请配置至少一个API密钥")
    
    def _setup_network_config(self):
        """配置网络和SSL设置 - 优化网络稳定性"""
        try:
            # 设置更短的超时时间
            os.environ['LITELLM_REQUEST_TIMEOUT'] = '8'
            
            # 禁用SSL验证（解决SSL错误）
            os.environ['CURL_CA_BUNDLE'] = ''
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            
            # 配置SSL上下文
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # LiteLLM特定配置
            litellm.set_verbose = False
            litellm.drop_params = True  # 自动删除不支持的参数
            
            # 为Gemini API设置特殊配置
            litellm.success_callback = []
            litellm.failure_callback = []
            
            logger.info("网络配置完成 - 已优化SSL和超时设置")
        except Exception as e:
            logger.warning(f"网络配置失败: {e}")
    
    def _setup_providers(self):
        """设置提供商配置 - 使用更稳定的模型和参数"""
        # 多个LLM提供商配置 - 优化参数，降级到更稳定的模型
        self.providers = [
            {
                "name": "google",
                "model": "gemini/gemini-1.5-flash",  # 降级到1.5版本，更稳定
                "available": bool(os.getenv('GOOGLE_API_KEY')),
                "max_tokens": 2000,  # 减少token数避免截断
                "temperature": 0.3,  # 提高temperature减少"思考"
                "max_retries": 2
            },
            {
                "name": "openai",
                "model": "gpt-4o-mini",
                "available": bool(os.getenv('OPENAI_API_KEY')),
                "max_tokens": 800,
                "temperature": 0.3,
                "max_retries": 2
            },
            {
                "name": "anthropic",
                "model": "claude-3-haiku-20240307", 
                "available": bool(os.getenv('ANTHROPIC_API_KEY')),
                "max_tokens": 800,
                "temperature": 0.3,
                "max_retries": 2
            }
        ]
        
        # 过滤可用的提供商
        self.available_providers = [p for p in self.providers if p['available']]
        
        if self.available_providers:
            providers_list = [p['name'] for p in self.available_providers]
            logger.info(f"可用提供商: {', '.join(providers_list)}")
        else:
            logger.warning("没有可用的LLM提供商")

    def setup_api_keys(self):
        """设置API密钥"""
        # Google Gemini
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key:
            os.environ['GEMINI_API_KEY'] = google_key
        
        # OpenAI
        openai_key = os.getenv('OPENAI_API_KEY') 
        if openai_key:
            os.environ['OPENAI_API_KEY'] = openai_key
            
        # Anthropic
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            os.environ['ANTHROPIC_API_KEY'] = anthropic_key

    def call_llm(
        self, 
        messages: List[Dict[str, str]], 
        provider_name: str = None,
        timeout: int = DEFAULT_TIMEOUT,
        retry_count: int = DEFAULT_RETRY_COUNT,
        **kwargs
    ) -> Dict[str, Any]:
        """
        基础LLM调用方法 - 最核心的稳定调用
        
        Args:
            messages: 消息列表
            provider_name: 指定提供商，None表示自动选择
            timeout: 超时时间
            retry_count: 重试次数
            **kwargs: 其他参数
            
        Returns:
            调用结果字典
        """
        if not self.available_providers:
            return {
                "success": False,
                "error": "没有可用的LLM提供商",
                "content": None
            }
        
        # 选择提供商
        if provider_name:
            providers_to_try = [p for p in self.available_providers if p['name'] == provider_name]
            if not providers_to_try:
                providers_to_try = self.available_providers
        else:
            providers_to_try = self.available_providers
        
        last_error = None
        
        # 尝试每个提供商
        for provider in providers_to_try:
            try:
                result = self._call_single_provider(
                    provider=provider,
                    messages=messages,
                    timeout=timeout,
                    retry_count=retry_count,
                    **kwargs
                )
                
                if result["success"]:
                    return result
                else:
                    last_error = result["error"]
                    logger.warning(f"提供商 {provider['name']} 调用失败: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"提供商 {provider['name']} 异常: {last_error}")
                continue
        
        # 所有提供商都失败
        return {
            "success": False,
            "error": f"所有LLM提供商调用失败。最后错误: {last_error}",
            "content": None
        }
    
    def _call_single_provider(
        self,
        provider: Dict[str, Any],
        messages: List[Dict[str, str]],
        timeout: int,
        retry_count: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用单个提供商 - 带重试机制（优化版）
        """
        model = provider["model"]
        provider_name = provider["name"]
        
        # 合并参数 - 使用更保守的设置
        call_params = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", provider.get("max_tokens", 600)),
            "temperature": kwargs.get("temperature", provider.get("temperature", 0.3)),
            "timeout": min(timeout, 6),  # 更短超时，减少SSL问题
        }
        
        # 对于Google特别优化
        if provider_name == "google":
            call_params["timeout"] = min(timeout, 10)  # Gemini用更短超时
            call_params["temperature"] = 0.1  # 更低的temperature
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                logger.info(f"尝试 {attempt+1}/{retry_count}: {provider_name} - {model}")
                start_time = time.time()
                
                # 核心API调用
                response = litellm.completion(**call_params)
                
                elapsed = time.time() - start_time
                logger.info(f"✅ 调用成功: {provider_name} (耗时: {elapsed:.2f}秒)")
                
                # 解析响应
                content = self._extract_content(response)
                if content:
                    return {
                        "success": True,
                        "content": content,
                        "provider": provider_name,
                        "model": model,
                        "elapsed_time": elapsed
                    }
                else:
                    last_error = "返回内容为空"
                    logger.warning(f"提供商 {provider_name} 返回空内容")
                    # 对于空内容，立即重试而不等待
                    continue
                    
            except Exception as e:
                elapsed = time.time() - start_time if 'start_time' in locals() else 0
                last_error = str(e)
                
                # 分类处理错误 - 针对不同错误类型使用不同策略
                if "ssl" in last_error.lower() or "eof" in last_error.lower():
                    logger.warning(f"❌ SSL错误 {attempt+1}/{retry_count}: {provider_name}")
                    # SSL错误需要更长等待
                    wait_time = DEFAULT_RETRY_DELAY * 2
                elif "timeout" in last_error.lower() or "timed out" in last_error.lower():
                    logger.warning(f"❌ 超时 {attempt+1}/{retry_count}: {provider_name} ({elapsed:.2f}s)")
                    wait_time = DEFAULT_RETRY_DELAY
                elif "rate limit" in last_error.lower() or "quota" in last_error.lower():
                    logger.warning(f"❌ 限流 {attempt+1}/{retry_count}: {provider_name}")
                    wait_time = DEFAULT_RETRY_DELAY * 3  # 限流需要更长等待
                else:
                    logger.warning(f"❌ 调用失败 {attempt+1}/{retry_count}: {provider_name} - {last_error[:100]}")
                    wait_time = DEFAULT_RETRY_DELAY
                
                # 等待后重试
                if attempt < retry_count - 1:
                    logger.info(f"等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
        
        return {
            "success": False,
            "error": f"{provider_name} 调用失败，{retry_count}次重试全部失败。最后错误: {last_error}",
            "content": None
        }
    
    def _extract_content(self, response) -> Optional[str]:
        """提取响应内容（Gemini 2.5兼容版）"""
        try:
            if not response:
                logger.debug("❌ Response为空")
                return None
                
            if not hasattr(response, 'choices'):
                logger.debug("❌ Response没有choices属性")
                return None
                
            if not response.choices:
                logger.debug("❌ Response.choices为空列表")
                return None
                
            choice = response.choices[0]
            logger.debug(f"✅ 获取到choice: {type(choice)}")
            
            if not hasattr(choice, 'message'):
                logger.debug("❌ Choice没有message属性")
                return None
                
            message = choice.message
            logger.debug(f"✅ 获取到message: {type(message)}")
            
            # 检查finish_reason，如果是MAX_TOKENS可能内容被截断
            if hasattr(choice, 'finish_reason'):
                finish_reason = choice.finish_reason
                logger.debug(f"🔍 Finish reason: {finish_reason}")
                if finish_reason == "MAX_TOKENS":
                    logger.warning("⚠️ 响应因达到最大token限制而被截断")
            
            # 兼容Gemini 2.5的新格式 - 检查content.parts
            if hasattr(message, 'content'):
                content = message.content
                logger.debug(f"✅ 获取到content: {type(content)}, repr: {repr(content)}")
                
                # 如果content是字符串（OpenAI格式）
                if isinstance(content, str):
                    if content and content.strip():
                        logger.debug(f"✅ 成功提取字符串内容: 长度={len(content.strip())}")
                        return content.strip()
                    else:
                        logger.debug("❌ 字符串content为空或只有空白")
                        return None
                
                # 如果content是字典（Gemini格式）
                elif isinstance(content, dict):
                    # 尝试从parts中提取文本
                    if 'parts' in content:
                        parts = content['parts']
                        logger.debug(f"🔍 发现content.parts: {parts}")
                        
                        if isinstance(parts, list) and parts:
                            text_parts = []
                            for part in parts:
                                if isinstance(part, dict) and 'text' in part:
                                    text_parts.append(part['text'])
                                elif isinstance(part, str):
                                    text_parts.append(part)
                            
                            if text_parts:
                                combined_text = ' '.join(text_parts).strip()
                                logger.debug(f"✅ 成功从parts提取内容: 长度={len(combined_text)}")
                                return combined_text
                    
                    # 如果content字典中直接有text字段
                    elif 'text' in content:
                        text = content['text']
                        if text and text.strip():
                            logger.debug(f"✅ 成功从content.text提取内容: 长度={len(text.strip())}")
                            return text.strip()
                    
                    logger.debug("❌ Content字典中没有找到有效的文本内容")
                    return None
                
                # content为None或其他类型
                else:
                    logger.debug(f"❌ Content类型不受支持: {type(content)}")
                    return None
            else:
                logger.debug("❌ Message没有content属性")
                return None
                
        except Exception as e:
            logger.error(f"提取响应内容异常: {e}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
            return None
    
    def simple_call(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        简化的调用接口 - 直接传入提示词
        """
        messages = [{"role": "user", "content": prompt}]
        return self.call_llm(messages, **kwargs)
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查 - 测试各个提供商是否可用
        """
        results = {
            "overall_healthy": False,
            "providers": {}
        }
        
        test_prompt = "请回复'OK'"
        
        for provider in self.available_providers:
            try:
                result = self.call_llm(
                    messages=[{"role": "user", "content": test_prompt}],
                    provider_name=provider["name"],
                    timeout=5,
                    retry_count=1
                )
                
                results["providers"][provider["name"]] = {
                    "healthy": result["success"],
                    "error": result.get("error") if not result["success"] else None
                }
                
                if result["success"]:
                    results["overall_healthy"] = True
                    
            except Exception as e:
                results["providers"][provider["name"]] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return results

# 全局LLM服务实例
llm_service = LLMService()
