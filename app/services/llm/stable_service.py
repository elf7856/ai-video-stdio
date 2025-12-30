#!/usr/bin/env python3
"""
稳定LLM服务 - 简化版本，专注于稳定性
解决当前LLM调用不稳定的问题
"""

import os
import time
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class StableLLMService:
    """
    稳定的LLM服务 - 简化版本
    特点：
    1. 减少依赖，直接使用HTTP请求
    2. 简化重试逻辑
    3. 更保守的超时设置
    4. 优先使用最稳定的提供商
    """
    
    def __init__(self):
        self.setup_providers()
        self.request_timeout = 10  # 固定10秒超时
        self.max_retries = 2  # 最多重试2次
        self.retry_delay = 3  # 重试间隔3秒
        
        # 设置请求session
        self.session = requests.Session()
        self.session.timeout = self.request_timeout
        
        logger.info(f"稳定LLM服务初始化完成，可用提供商: {len(self.providers)}")
    
    def setup_providers(self):
        """设置提供商 - 只使用最稳定的配置"""
        self.providers = []
        
        # OpenAI - 最稳定的提供商
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key.strip():
            self.providers.append({
                'name': 'openai',
                'api_key': openai_key,
                'model': 'gpt-4o-mini',  # 使用更快的mini版本
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'max_tokens': 1000,
                'temperature': 0.3
            })
        
        # Google Gemini - 备用
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key and google_key.strip():
            self.providers.append({
                'name': 'google',
                'api_key': google_key,
                'model': 'gemini-1.5-flash',
                'endpoint': f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={google_key}',
                'max_tokens': 1000,
                'temperature': 0.3
            })
        
        # Anthropic - 最后备用
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and anthropic_key.strip():
            self.providers.append({
                'name': 'anthropic',
                'api_key': anthropic_key,
                'model': 'claude-3-haiku-20240307',
                'endpoint': 'https://api.anthropic.com/v1/messages',
                'max_tokens': 1000,
                'temperature': 0.3
            })
    
    def simple_call(self, prompt: str, timeout: int = None, retry_count: int = None) -> Dict[str, Any]:
        """
        简单调用 - 最基础的稳定接口
        
        Args:
            prompt: 提示词
            timeout: 超时时间（可选）
            retry_count: 重试次数（可选）
            
        Returns:
            结果字典 {success: bool, content: str, error: str, provider: str}
        """
        if not self.providers:
            return {
                'success': False,
                'content': '',
                'error': '没有可用的LLM提供商，请配置API密钥',
                'provider': 'none'
            }
        
        timeout = timeout or self.request_timeout
        retry_count = retry_count or self.max_retries
        
        # 按优先级尝试每个提供商
        for provider in self.providers:
            try:
                logger.info(f"尝试使用 {provider['name']} 调用LLM...")
                result = self._call_provider(provider, prompt, timeout, retry_count)
                
                if result['success']:
                    logger.info(f"✅ {provider['name']} 调用成功")
                    result['provider'] = provider['name']
                    return result
                else:
                    logger.warning(f"❌ {provider['name']} 调用失败: {result['error']}")
                    
            except Exception as e:
                logger.error(f"❌ {provider['name']} 异常: {str(e)}")
                continue
        
        # 所有提供商都失败
        return {
            'success': False,
            'content': '',
            'error': '所有LLM提供商调用失败',
            'provider': 'none'
        }
    
    def _call_provider(self, provider: Dict[str, Any], prompt: str, timeout: int, retry_count: int) -> Dict[str, Any]:
        """调用单个提供商"""
        for attempt in range(retry_count + 1):
            try:
                if provider['name'] == 'openai':
                    return self._call_openai(provider, prompt, timeout)
                elif provider['name'] == 'google':
                    return self._call_google(provider, prompt, timeout)
                elif provider['name'] == 'anthropic':
                    return self._call_anthropic(provider, prompt, timeout)
                else:
                    return {
                        'success': False,
                        'content': '',
                        'error': f'不支持的提供商: {provider["name"]}'
                    }
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"{provider['name']} 第{attempt+1}次尝试失败: {error_msg}")
                
                if attempt < retry_count:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    return {
                        'success': False,
                        'content': '',
                        'error': f'重试{retry_count}次后仍失败: {error_msg}'
                    }
    
    def _call_openai(self, provider: Dict[str, Any], prompt: str, timeout: int) -> Dict[str, Any]:
        """调用OpenAI API"""
        headers = {
            'Authorization': f'Bearer {provider["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': provider['model'],
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': provider['max_tokens'],
            'temperature': provider['temperature']
        }
        
        response = self.session.post(
            provider['endpoint'],
            headers=headers,
            json=data,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return {
                'success': True,
                'content': content.strip(),
                'error': ''
            }
        else:
            return {
                'success': False,
                'content': '',
                'error': f'OpenAI API错误: {response.status_code} - {response.text}'
            }
    
    def _call_google(self, provider: Dict[str, Any], prompt: str, timeout: int) -> Dict[str, Any]:
        """调用Google Gemini API"""
        data = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'maxOutputTokens': provider['max_tokens'],
                'temperature': provider['temperature']
            }
        }
        
        response = self.session.post(
            provider['endpoint'],
            json=data,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return {
                    'success': True,
                    'content': content.strip(),
                    'error': ''
                }
            else:
                return {
                    'success': False,
                    'content': '',
                    'error': 'Google API返回空结果'
                }
        else:
            return {
                'success': False,
                'content': '',
                'error': f'Google API错误: {response.status_code} - {response.text}'
            }
    
    def _call_anthropic(self, provider: Dict[str, Any], prompt: str, timeout: int) -> Dict[str, Any]:
        """调用Anthropic Claude API"""
        headers = {
            'x-api-key': provider['api_key'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': provider['model'],
            'max_tokens': provider['max_tokens'],
            'temperature': provider['temperature'],
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = self.session.post(
            provider['endpoint'],
            headers=headers,
            json=data,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']
            return {
                'success': True,
                'content': content.strip(),
                'error': ''
            }
        else:
            return {
                'success': False,
                'content': '',
                'error': f'Anthropic API错误: {response.status_code} - {response.text}'
            }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查 - 简化版本"""
        if not self.providers:
            return {
                'overall_healthy': False,
                'providers': {},
                'error': '没有可用的提供商'
            }
        
        # 简单测试第一个提供商
        test_result = self.simple_call("测试", timeout=5, retry_count=1)
        
        return {
            'overall_healthy': test_result['success'],
            'providers': {
                test_result.get('provider', 'unknown'): {
                    'healthy': test_result['success'],
                    'error': test_result.get('error') if not test_result['success'] else None
                }
            },
            'error': test_result.get('error') if not test_result['success'] else None
        }

# 全局实例
stable_llm_service = StableLLMService() 