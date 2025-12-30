#!/usr/bin/env python3
"""
统一TTS (Text-to-Speech) 服务
提供多种发音人选择，用户无需配置API密钥
"""

import os
import tempfile
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class Voice:
    """发音人信息"""
    def __init__(self, id: str, name: str, gender: str, language: str, 
                 provider: str, description: str = "", sample_url: str = ""):
        self.id = id
        self.name = name
        self.gender = gender  # male, female
        self.language = language  # zh-CN, en-US等
        self.provider = provider
        self.description = description
        self.sample_url = sample_url
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "language": self.language,
            "provider": self.provider,
            "description": self.description,
            "sample_url": self.sample_url
        }

class TTSProvider(ABC):
    """TTS提供商基类"""
    
    @abstractmethod
    def get_voices(self) -> List[Voice]:
        """获取可用语音列表"""
        pass
    
    @abstractmethod
    async def generate_speech(self, text: str, voice_id: str, **kwargs) -> str:
        """生成语音文件"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass

class EdgeTTSProvider(TTSProvider):
    """Edge TTS提供商（免费，优先使用）"""
    
    def __init__(self):
        self.name = "Edge TTS"
        
    def is_available(self) -> bool:
        try:
            import edge_tts
            return True
        except ImportError:
            return False
    
    def get_voices(self) -> List[Voice]:
        """获取Edge TTS语音列表"""
        return [
            # 中文发音人
            Voice("xiaoxiao", "小小 (女)", "female", "zh-CN", "edge", 
                  "温柔甜美的女声，适合故事朗读"),
            Voice("yunxi", "云希 (男)", "male", "zh-CN", "edge", 
                  "成熟稳重的男声，适合新闻播报"),
            Voice("yunyang", "云扬 (男)", "male", "zh-CN", "edge", 
                  "年轻活力的男声，适合广告配音"),
            Voice("xiaoyi", "小艺 (女)", "female", "zh-CN", "edge", 
                  "亲切自然的女声，适合对话场景"),
            Voice("yunye", "云野 (男)", "male", "zh-CN", "edge", 
                  "磁性低沉的男声，适合深度内容"),
            Voice("xiaoxuan", "小萱 (女)", "female", "zh-CN", "edge", 
                  "清脆明亮的女声，适合儿童内容"),
            
            # 英文发音人
            Voice("aria", "Aria (女)", "female", "en-US", "edge", 
                  "专业的美式英语女声"),
            Voice("jenny", "Jenny (女)", "female", "en-US", "edge", 
                  "友善的美式英语女声"),
            Voice("guy", "Guy (男)", "male", "en-US", "edge", 
                  "成熟的美式英语男声"),
            Voice("davis", "Davis (男)", "male", "en-US", "edge", 
                  "年轻的美式英语男声"),
        ]
    
    async def generate_speech(self, text: str, voice_id: str, **kwargs) -> str:
        """使用Edge TTS生成语音"""
        if not self.is_available():
            raise Exception("Edge TTS未安装，请运行: pip install edge-tts")
        
        try:
            import edge_tts
            
            # 映射我们的voice_id到Edge TTS的实际ID
            voice_mapping = {
                "xiaoxiao": "zh-CN-XiaoxiaoNeural",
                "yunxi": "zh-CN-YunxiNeural", 
                "yunyang": "zh-CN-YunyangNeural",
                "xiaoyi": "zh-CN-XiaoyiNeural",
                "yunye": "zh-CN-YunyeNeural",
                "xiaoxuan": "zh-CN-XiaoxuanNeural",
                "aria": "en-US-AriaNeural",
                "jenny": "en-US-JennyNeural",
                "guy": "en-US-GuyNeural",
                "davis": "en-US-DavisNeural",
            }
            
            edge_voice = voice_mapping.get(voice_id, "zh-CN-XiaoxiaoNeural")
            output_path = tempfile.mktemp(suffix='.mp3')
            
            # 获取语音参数
            rate = kwargs.get('rate', '+0%')  # 语速
            pitch = kwargs.get('pitch', '+0Hz')  # 音调
            volume = kwargs.get('volume', '+0%')  # 音量
            
            # 直接使用edge_tts.Communicate的内置参数
            communicate = edge_tts.Communicate(
                text=text,
                voice=edge_voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            
            await communicate.save(output_path)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Edge TTS生成失败: {str(e)}")

class SystemTTSProvider(TTSProvider):
    """系统内置TTS（备用方案）"""
    
    def __init__(self):
        self.name = "System TTS"
        
    def is_available(self) -> bool:
        # 检查系统是否支持TTS
        import platform
        return platform.system() in ['Darwin', 'Windows', 'Linux']
    
    def get_voices(self) -> List[Voice]:
        """获取系统TTS语音列表"""
        import platform
        system = platform.system()
        
        voices = []
        
        if system == 'Darwin':  # macOS
            voices.extend([
                Voice("ting", "婷婷 (系统)", "female", "zh-CN", "system", 
                      "macOS系统中文女声"),
                Voice("alex", "Alex (系统)", "male", "en-US", "system", 
                      "macOS系统英文男声"),
            ])
        elif system == 'Windows':  # Windows
            voices.extend([
                Voice("huihui", "慧慧 (系统)", "female", "zh-CN", "system", 
                      "Windows系统中文女声"),
                Voice("zira", "Zira (系统)", "female", "en-US", "system", 
                      "Windows系统英文女声"),
            ])
        
        return voices
    
    async def generate_speech(self, text: str, voice_id: str, **kwargs) -> str:
        """使用系统TTS生成语音"""
        import platform
        import subprocess
        
        output_path = tempfile.mktemp(suffix='.wav')
        system = platform.system()
        
        try:
            if system == 'Darwin':  # macOS
                voice_mapping = {
                    "ting": "Ting-Ting",
                    "alex": "Alex"
                }
                voice = voice_mapping.get(voice_id, "Ting-Ting")
                
                cmd = [
                    'say', 
                    '-v', voice,
                    '-o', output_path,
                    text
                ]
                
                await asyncio.create_subprocess_exec(*cmd)
                
            elif system == 'Windows':  # Windows
                # 使用PowerShell调用Windows Speech API
                ps_script = f'''
                Add-Type -AssemblyName System.Speech
                $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synth.SetOutputToWaveFile("{output_path}")
                $synth.Speak("{text}")
                $synth.Dispose()
                '''
                
                cmd = ['powershell', '-Command', ps_script]
                await asyncio.create_subprocess_exec(*cmd)
            
            else:
                raise Exception(f"不支持的系统: {system}")
            
            if os.path.exists(output_path):
                return output_path
            else:
                raise Exception("系统TTS生成失败")
                
        except Exception as e:
            raise Exception(f"系统TTS生成失败: {str(e)}")

class TTSGenerator:
    """统一TTS服务管理器"""
    
    def __init__(self):
        # 初始化所有提供商
        self.providers = {
            "edge": EdgeTTSProvider(),
            "system": SystemTTSProvider(),
        }
        
        # 确定优先级顺序（免费的Edge TTS优先）
        self.provider_priority = ["edge", "system"]
        
        # 预加载所有可用语音
        self._load_voices()
    
    def _load_voices(self):
        """加载所有可用语音"""
        self.all_voices = {}
        self.voices_by_language = {}
        self.voices_by_gender = {}
        
        for provider_name, provider in self.providers.items():
            if provider.is_available():
                voices = provider.get_voices()
                for voice in voices:
                    self.all_voices[voice.id] = voice
                    
                    # 按语言分组
                    if voice.language not in self.voices_by_language:
                        self.voices_by_language[voice.language] = []
                    self.voices_by_language[voice.language].append(voice)
                    
                    # 按性别分组
                    if voice.gender not in self.voices_by_gender:
                        self.voices_by_gender[voice.gender] = []
                    self.voices_by_gender[voice.gender].append(voice)
    
    def get_available_voices(self, language: str = None, gender: str = None) -> List[Dict]:
        """获取可用语音列表"""
        voices = list(self.all_voices.values())
        
        # 按语言过滤
        if language:
            voices = [v for v in voices if v.language == language]
        
        # 按性别过滤
        if gender:
            voices = [v for v in voices if v.gender == gender]
        
        return [voice.to_dict() for voice in voices]
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict]:
        """获取特定语音的信息"""
        voice = self.all_voices.get(voice_id)
        return voice.to_dict() if voice else None
    
    def get_default_voice(self, language: str = "zh-CN") -> str:
        """获取指定语言的默认语音"""
        voices = self.voices_by_language.get(language, [])
        if voices:
            return voices[0].id
        
        # 如果没有指定语言的语音，返回第一个可用的
        if self.all_voices:
            return list(self.all_voices.keys())[0]
        
        return "xiaoxiao"  # 最后的兜底
    
    async def generate_speech(self, text: str, voice_id: str = None, **kwargs) -> str:
        """生成语音"""
        # 如果没有指定语音，使用默认的
        if not voice_id:
            voice_id = self.get_default_voice()
        
        # 查找语音信息
        voice = self.all_voices.get(voice_id)
        if not voice:
            raise Exception(f"未找到语音: {voice_id}")
        
        # 获取对应的提供商
        provider = self.providers.get(voice.provider)
        if not provider or not provider.is_available():
            raise Exception(f"语音提供商 {voice.provider} 不可用")
        
        logger.info(f"使用 {voice.name} ({voice.provider}) 生成语音")
        
        try:
            result = await provider.generate_speech(text, voice_id, **kwargs)
            logger.info(f"语音生成成功: {result}")
            return result
        except Exception as e:
            logger.error(f"语音生成失败: {e}")
            raise
    
    async def generate_batch_speech(self, texts: List[str], voice_id: str = None, **kwargs) -> List[str]:
        """批量生成语音"""
        results = []
        for text in texts:
            try:
                result = await self.generate_speech(text, voice_id, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"批量语音生成失败: {e}")
                results.append(None)
        return results
    
    async def save_speech(self, text: str, output_path: str, voice_id: str = None, **kwargs) -> bool:
        """生成语音并直接保存到指定路径"""
        import shutil
        
        try:
            # 生成语音到临时文件
            temp_path = await self.generate_speech(text, voice_id, **kwargs)
            
            if temp_path and os.path.exists(temp_path):
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                
                # 移动文件到目标位置
                shutil.move(temp_path, output_path)
                logger.info(f"语音文件已保存到: {output_path}")
                return True
            else:
                logger.error("语音生成失败")
                return False
                
        except Exception as e:
            logger.error(f"保存语音文件失败: {e}")
            return False
    
    async def save_batch_speech(self, texts: List[str], output_dir: str, voice_id: str = None, 
                              filename_template: str = "audio_{index}.mp3", **kwargs) -> List[str]:
        """批量生成语音并保存到指定目录"""
        import shutil
        
        results = []
        os.makedirs(output_dir, exist_ok=True)
        
        for i, text in enumerate(texts):
            try:
                # 生成文件名
                filename = filename_template.format(index=i+1, text=text[:20])
                output_path = os.path.join(output_dir, filename)
                
                # 生成并保存
                success = await self.save_speech(text, output_path, voice_id, **kwargs)
                results.append(output_path if success else None)
                
            except Exception as e:
                logger.error(f"批量保存语音失败 ({i+1}): {e}")
                results.append(None)
        
        return results
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return list(self.voices_by_language.keys())
    
    def get_provider_status(self) -> Dict[str, bool]:
        """获取各提供商状态"""
        return {
            name: provider.is_available() 
            for name, provider in self.providers.items()
        }
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return any(provider.is_available() for provider in self.providers.values())

# 全局TTS生成器实例
tts_generator = TTSGenerator() 