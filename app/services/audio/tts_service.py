import asyncio
import edge_tts
import os
from typing import Dict, Optional
from app.core.config import settings
from app.prompts.base import render_prompt
import tempfile
import litellm
from app.services.llm.service import llm_service
import logging

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.default_voice = settings.default_tts_voice
        self.default_speed = settings.tts_speed
        self.llm_service = llm_service
        
        # 预定义的声音配置
        self.voices = {
            "chinese_female": "zh-CN-XiaoxiaoNeural",
            "chinese_male": "zh-CN-YunxiNeural",
            "english_female": "en-US-JennyNeural",
            "english_male": "en-US-GuyNeural",
            "japanese_female": "ja-JP-NanamiNeural",
            "japanese_male": "ja-JP-KeitaNeural",
            "korean_female": "ko-KR-SunHiNeural",
            "korean_male": "ko-KR-InJoonNeural"
        }
    
    async def optimize_text_for_tts(self, text: str, style: str = "natural", 
                                  emotion: str = "neutral", speed: float = 1.0) -> str:
        """使用LLM优化文本以提升TTS质量"""
        try:
            prompt = render_prompt("tts_text_optimization",
                                 original_text=text,
                                 style=style,
                                 emotion=emotion,
                                 speed=f"{speed:.1f}")
            
            messages = [
                {"role": "system", "content": render_prompt("tts_optimizer_role")},
                {"role": "user", "content": prompt}
            ]

            result = self.llm_service.call(messages, max_tokens=1000, temperature=0.7)
            if result["success"]:
                content = result["content"]
            else:
                raise Exception(result["error"])
            return content.strip()
            
        except Exception as e:
            logger.error(f"文本优化失败: {str(e)}", exc_info=True)
            return text  # 如果优化失败，返回原文本
    
    async def generate_speech(self, text: str, voice: str = None, 
                            speed: float = None, output_path: str = None,
                            optimize_text: bool = True, style: str = "natural",
                            emotion: str = "neutral"):
        """生成语音"""
        try:
            # 可选的文本优化
            if optimize_text:
                text = await self.optimize_text_for_tts(text, style, emotion, speed or self.default_speed)
            
            # 使用指定的声音或默认声音
            voice_name = self.voices.get(voice, voice) or self.default_voice
            speed_value = speed or self.default_speed
            
            # 如果没有指定输出路径，创建临时文件
            if output_path is None:
                output_path = tempfile.mktemp(suffix='.mp3')
            
            # 使用 Edge TTS 生成语音 - 修复速度格式
            # edge_tts需要整数百分比格式，如 '+0%' 或 '-10%'
            speed_percent = int((speed_value - 1.0) * 100)
            rate_str = f"{speed_percent:+d}%" if speed_percent != 0 else "+0%"
            
            communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
            await communicate.save(output_path)
            
            return {
                "success": True,
                "output_path": output_path,
                "text": text,
                "voice": voice_name
            }
            
        except Exception as e:
            logger.error(f"TTS生成失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_speech_batch(self, texts: list, voice: str = None,
                                  speed: float = None, output_dir: str = None) -> list:
        """批量生成语音"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        results = []
        for i, text in enumerate(texts):
            output_path = os.path.join(output_dir, f"speech_{i:03d}.mp3")
            result = await self.generate_speech(text, voice, speed, output_path)
            results.append(result)
        
        return results
    
    def get_available_voices(self) -> Dict[str, str]:
        """获取可用的声音列表"""
        return self.voices.copy()
    
    async def test_voice(self, voice: str, test_text: str = "你好，这是一个测试。") -> bool:
        """测试声音是否可用"""
        try:
            result = await self.generate_speech(test_text, voice)
            if result and os.path.exists(result):
                os.remove(result)  # 清理测试文件
                return True
            return False
        except Exception:
            return False

class ElevenLabsTTS:
    """ElevenLabs TTS 服务（需要API密钥）"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.elevenlabs_api_key
        if self.api_key:
            try:
                from elevenlabs import ElevenLabs
                self.client = ElevenLabs(api_key=self.api_key)
                self.available = True
            except ImportError:
                self.available = False
                self.client = None
        else:
            self.available = False
            self.client = None
    
    def generate_speech(self, text: str, voice: str = "Rachel", 
                       output_path: str = None) -> str:
        """使用 ElevenLabs 生成语音"""
        if not self.available or self.client is None:
            return None
        
        try:
            if output_path is None:
                output_path = tempfile.mktemp(suffix='.mp3')
            
            # Generate audio using the new client API
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice,
                model_id="eleven_multilingual_v2"
            )
            
            # Save audio to file
            with open(output_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)
            
            return output_path
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS生成失败: {str(e)}", exc_info=True)
            return None
    
    def get_available_voices(self) -> list:
        """获取可用的声音列表"""
        if not self.available or self.client is None:
            return []
        
        try:
            voices_response = self.client.voices.get_all()
            return [voice.name for voice in voices_response.voices]
        except Exception:
            return []

class TTSServiceManager:
    """TTS服务管理器"""
    
    def __init__(self):
        self.edge_tts = TTSService()
        self.elevenlabs_tts = ElevenLabsTTS()
    
    async def generate_speech(self, text: str, service: str = "edge", 
                            voice: str = None, speed: float = None,
                            output_path: str = None):
        """生成语音（支持多种TTS服务）"""
        
        if service == "edge":
            return await self.edge_tts.generate_speech(text, voice, speed, output_path)
        elif service == "elevenlabs" and self.elevenlabs_tts.available:
            return self.elevenlabs_tts.generate_speech(text, voice, output_path)
        else:
            # 默认使用 Edge TTS
            return await self.edge_tts.generate_speech(text, voice, speed, output_path)
    
    def get_available_services(self) -> list:
        """获取可用的TTS服务"""
        services = ["edge"]
        if self.elevenlabs_tts.available:
            services.append("elevenlabs")
        return services
    
    def get_available_voices(self, service: str = "edge") -> Dict:
        """获取可用的声音列表"""
        if service == "edge":
            return self.edge_tts.get_available_voices()
        elif service == "elevenlabs":
            voices = self.elevenlabs_tts.get_available_voices()
            return {voice: voice for voice in voices}
        else:
            return {} 