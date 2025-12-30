#!/usr/bin/env python3
"""
API状态管理器
统一管理所有API接入状态、配置和使用
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class APIStatus(Enum):
    """API状态枚举"""
    READY = "ready"           # 已就绪，可以使用
    CONFIGURED = "configured" # 已配置，但未测试
    MISSING_CONFIG = "missing_config"  # 缺少配置
    ERROR = "error"           # 出现错误
    NOT_INSTALLED = "not_installed"    # 依赖未安装

class APIInfo:
    """API信息类"""
    def __init__(self, name: str, service_type: str, provider: str = "", 
                 status: APIStatus = APIStatus.NOT_INSTALLED,
                 config_required: List[str] = None,
                 dependencies: List[str] = None,
                 description: str = "",
                 priority: int = 5):
        self.name = name
        self.service_type = service_type  # llm, tts, image, video
        self.provider = provider
        self.status = status
        self.config_required = config_required or []
        self.dependencies = dependencies or []
        self.description = description
        self.priority = priority  # 1=最高优先级，5=最低优先级
        self.last_check = None
        self.error_message = ""

class APIManager:
    """API管理器"""
    
    def __init__(self):
        self.apis: Dict[str, APIInfo] = {}
        self._initialize_apis()
    
    def _initialize_apis(self):
        """初始化所有API信息"""
        
        # LLM APIs
        self.apis["openai_llm"] = APIInfo(
            name="OpenAI LLM",
            service_type="llm",
            provider="openai",
            config_required=["OPENAI_API_KEY"],
            dependencies=["openai"],
            description="OpenAI GPT模型，用于内容分析和生成",
            priority=1
        )
        
        self.apis["google_llm"] = APIInfo(
            name="Google Gemini",
            service_type="llm", 
            provider="google",
            config_required=["GOOGLE_API_KEY"],
            dependencies=["google.generativeai"],
            description="Google Gemini模型，免费额度较大",
            priority=1
        )
        
        self.apis["anthropic_llm"] = APIInfo(
            name="Anthropic Claude",
            service_type="llm",
            provider="anthropic", 
            config_required=["ANTHROPIC_API_KEY"],
            dependencies=["anthropic"],
            description="Anthropic Claude模型，擅长长文本处理",
            priority=2
        )
        
        # TTS APIs  
        self.apis["edge_tts"] = APIInfo(
            name="Edge TTS",
            service_type="tts",
            provider="edge",
            config_required=[],  # 免费，不需要API密钥
            dependencies=["edge_tts"],
            description="微软Edge TTS，免费，支持多种中文语音",
            priority=1
        )
        
        self.apis["openai_tts"] = APIInfo(
            name="OpenAI TTS", 
            service_type="tts",
            provider="openai",
            config_required=["OPENAI_API_KEY"],
            dependencies=["openai"],
            description="OpenAI语音合成，质量高但收费",
            priority=3
        )
        
        self.apis["elevenlabs_tts"] = APIInfo(
            name="ElevenLabs TTS",
            service_type="tts",
            provider="elevenlabs",
            config_required=["ELEVENLABS_API_KEY"],
            dependencies=["aiohttp"],
            description="ElevenLabs语音合成，质量极高但价格昂贵",
            priority=4
        )
        
        # 图像生成 APIs
        self.apis["dalle"] = APIInfo(
            name="DALL-E",
            service_type="image",
            provider="openai",
            config_required=["OPENAI_API_KEY"],
            dependencies=["openai"],
            description="OpenAI DALL-E图像生成",
            priority=2
        )
        
        self.apis["stability"] = APIInfo(
            name="Stability AI",
            service_type="image", 
            provider="stability",
            config_required=["STABILITY_API_KEY"],
            dependencies=["stability_sdk"],
            description="Stability AI Stable Diffusion",
            priority=3
        )
        
        self.apis["replicate"] = APIInfo(
            name="Replicate", 
            service_type="image",
            provider="replicate",
            config_required=["REPLICATE_API_TOKEN"],
            dependencies=["replicate"],
            description="Replicate平台各种AI模型",
            priority=3
        )
        
        # 视频处理 APIs
        self.apis["youtube_dl"] = APIInfo(
            name="YouTube下载",
            service_type="video",
            provider="youtube",
            config_required=[],
            dependencies=["yt_dlp"],
            description="YouTube视频下载和信息提取",
            priority=2
        )
        
        # ASR APIs
        self.apis["openai_whisper"] = APIInfo(
            name="OpenAI Whisper",
            service_type="asr",
            provider="openai",
            config_required=["OPENAI_API_KEY"],
            dependencies=["openai"],
            description="OpenAI Whisper语音识别，质量高，支持多语言",
            priority=1
        )
        
        self.apis["local_whisper"] = APIInfo(
            name="本地Whisper",
            service_type="asr",
            provider="local",
            config_required=[],  # 不需要API密钥
            dependencies=["openai-whisper"],
            description="本地Whisper模型，免费使用但需要下载模型",
            priority=2
        )
        
        self.apis["google_speech"] = APIInfo(
            name="Google Speech-to-Text",
            service_type="asr",
            provider="google",
            config_required=["GOOGLE_APPLICATION_CREDENTIALS"],
            dependencies=["google-cloud-speech"],
            description="Google Cloud语音识别，准确度高",
            priority=3
        )
    
    async def check_api_status(self, api_key: str) -> APIStatus:
        """检查单个API状态"""
        api = self.apis.get(api_key)
        if not api:
            return APIStatus.ERROR
        
        try:
            # 检查依赖
            for dep in api.dependencies:
                try:
                    __import__(dep)
                except ImportError:
                    api.status = APIStatus.NOT_INSTALLED
                    api.error_message = f"缺少依赖: {dep}"
                    return api.status
            
            # 检查配置
            missing_config = []
            for config in api.config_required:
                if not os.getenv(config):
                    missing_config.append(config)
            
            if missing_config:
                api.status = APIStatus.MISSING_CONFIG
                api.error_message = f"缺少配置: {', '.join(missing_config)}"
                return api.status
            
            # 执行实际测试
            if api.service_type == "llm":
                api.status = await self._test_llm_api(api)
            elif api.service_type == "tts":
                api.status = await self._test_tts_api(api)
            elif api.service_type == "image":
                api.status = await self._test_image_api(api)
            elif api.service_type == "video":
                api.status = await self._test_video_api(api)
            else:
                api.status = APIStatus.CONFIGURED
                
        except Exception as e:
            api.status = APIStatus.ERROR
            api.error_message = str(e)
        
        return api.status
    
    async def _test_llm_api(self, api: APIInfo) -> APIStatus:
        """测试LLM API"""
        try:
            from app.services.llm.service import LLMService
            llm = LLMService()
            
            # 简单测试调用 - 使用正确的方法名
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: llm.simple_call("测试", preferred_provider=api.provider)
            )
            
            if response and response.get("success") and response.get("content"):
                return APIStatus.READY
            else:
                api.error_message = f"API调用失败: {response.get('error', '无响应')}"
                return APIStatus.ERROR
                
        except Exception as e:
            api.error_message = f"LLM测试失败: {str(e)[:100]}"
            return APIStatus.ERROR
    
    async def _test_tts_api(self, api: APIInfo) -> APIStatus:
        """测试TTS API"""
        try:
            from app.services.tts.generator import TTSGenerator
            tts = TTSGenerator()
            
            if api.provider == "edge":
                # Edge TTS特殊处理
                if tts.is_available():
                    return APIStatus.READY
                else:
                    return APIStatus.NOT_INSTALLED
            else:
                # 其他TTS提供商
                return APIStatus.CONFIGURED  # 暂时标记为已配置
                
        except Exception as e:
            api.error_message = f"TTS测试失败: {str(e)[:100]}"
            return APIStatus.ERROR
    
    async def _test_image_api(self, api: APIInfo) -> APIStatus:
        """测试图像生成API"""
        try:
            from app.services.image.generator import ImageGenerator
            img_gen = ImageGenerator()
            
            providers = img_gen.get_available_providers()
            if api.provider in [p.lower() for p in providers]:
                return APIStatus.READY
            else:
                return APIStatus.CONFIGURED
                
        except Exception as e:
            api.error_message = f"图像API测试失败: {str(e)[:100]}"
            return APIStatus.ERROR
    
    async def _test_video_api(self, api: APIInfo) -> APIStatus:
        """测试视频API"""
        try:
            # 简单检查依赖是否存在
            return APIStatus.CONFIGURED
        except Exception as e:
            api.error_message = f"视频API测试失败: {str(e)[:100]}"
            return APIStatus.ERROR
    
    async def check_all_apis(self) -> Dict[str, APIStatus]:
        """检查所有API状态"""
        results = {}
        
        for api_key in self.apis:
            status = await self.check_api_status(api_key)
            results[api_key] = status
            
        return results
    
    def get_apis_by_service(self, service_type: str) -> List[APIInfo]:
        """获取指定服务类型的所有API"""
        return [api for api in self.apis.values() if api.service_type == service_type]
    
    def get_ready_apis(self, service_type: str = None) -> List[APIInfo]:
        """获取已就绪的API"""
        ready_apis = [api for api in self.apis.values() if api.status == APIStatus.READY]
        
        if service_type:
            ready_apis = [api for api in ready_apis if api.service_type == service_type]
            
        return sorted(ready_apis, key=lambda x: x.priority)
    
    def get_next_priority_apis(self, limit: int = 3) -> List[APIInfo]:
        """获取下一步应该配置的API（按优先级）"""
        pending_apis = [
            api for api in self.apis.values() 
            if api.status in [APIStatus.MISSING_CONFIG, APIStatus.NOT_INSTALLED]
        ]
        
        return sorted(pending_apis, key=lambda x: x.priority)[:limit]
    
    def get_api_summary(self) -> Dict[str, Dict[str, int]]:
        """获取API状态摘要"""
        summary = {
            "by_service": {},
            "by_status": {}
        }
        
        # 按服务类型统计
        for api in self.apis.values():
            service = api.service_type
            if service not in summary["by_service"]:
                summary["by_service"][service] = {
                    "total": 0, "ready": 0, "configured": 0, "missing": 0, "error": 0
                }
            
            summary["by_service"][service]["total"] += 1
            
            if api.status == APIStatus.READY:
                summary["by_service"][service]["ready"] += 1
            elif api.status == APIStatus.CONFIGURED:
                summary["by_service"][service]["configured"] += 1
            elif api.status in [APIStatus.MISSING_CONFIG, APIStatus.NOT_INSTALLED]:
                summary["by_service"][service]["missing"] += 1
            else:
                summary["by_service"][service]["error"] += 1
        
        # 按状态统计
        for api in self.apis.values():
            status_name = api.status.value
            summary["by_status"][status_name] = summary["by_status"].get(status_name, 0) + 1
        
        return summary
    
    def print_status_report(self):
        """打印状态报告"""
        print("📊 API接入状态报告")
        print("="*60)
        
        # 按服务类型展示
        services = ["llm", "tts", "image", "video"]
        service_names = {"llm": "语言模型", "tts": "语音合成", "image": "图像生成", "video": "视频处理"}
        
        for service in services:
            apis = self.get_apis_by_service(service)
            if not apis:
                continue
                
            print(f"\n🔧 {service_names[service]} ({len(apis)} 个API)")
            
            for api in sorted(apis, key=lambda x: x.priority):
                status_icon = {
                    APIStatus.READY: "✅",
                    APIStatus.CONFIGURED: "⚠️",
                    APIStatus.MISSING_CONFIG: "❌",
                    APIStatus.NOT_INSTALLED: "📦",
                    APIStatus.ERROR: "🚫"
                }.get(api.status, "❓")
                
                print(f"  {status_icon} {api.name:20} - {api.status.value}")
                if api.error_message:
                    print(f"      错误: {api.error_message}")
        
        # 下一步建议
        print(f"\n🎯 建议下一步配置的API:")
        next_apis = self.get_next_priority_apis(3)
        
        for i, api in enumerate(next_apis, 1):
            print(f"  {i}. {api.name} - {api.description}")
            if api.config_required:
                print(f"     需要配置: {', '.join(api.config_required)}")
            if api.dependencies:
                print(f"     需要安装: pip install {' '.join(api.dependencies)}")

# 全局API管理器实例
api_manager = APIManager() 