#!/usr/bin/env python3
"""
ASR (自动语音识别) 服务
支持多种语音识别API和本地识别方案
"""

import os
import tempfile
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ASRResult:
    """ASR识别结果"""
    def __init__(self, text: str, confidence: float = 0.0, 
                 timestamps: List[Tuple[float, float, str]] = None,
                 language: str = "zh-CN", provider: str = "unknown"):
        self.text = text
        self.confidence = confidence
        self.timestamps = timestamps or []  # [(start_time, end_time, text)]
        self.language = language
        self.provider = provider
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "text": self.text,
            "confidence": self.confidence,
            "timestamps": self.timestamps,
            "language": self.language,
            "provider": self.provider,
            "created_at": self.created_at.isoformat()
        }

class ASRProvider(ABC):
    """ASR提供商基类"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass
    
    @abstractmethod
    async def transcribe(self, audio_path: str, language: str = "zh-CN") -> ASRResult:
        """转录音频文件"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        pass

class OpenAIWhisperProvider(ASRProvider):
    """OpenAI Whisper ASR提供商"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
    def is_available(self) -> bool:
        """检查OpenAI API是否可用"""
        return bool(self.api_key)
    
    async def transcribe(self, audio_path: str, language: str = "zh-CN") -> ASRResult:
        """使用OpenAI Whisper进行转录"""
        if not self.is_available():
            raise Exception("OpenAI API密钥未配置")
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)
            
            # 将语言代码转换为Whisper支持的格式
            whisper_lang = self._convert_language_code(language)
            
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=whisper_lang,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # 解析响应
            text = response.text
            confidence = 0.9  # Whisper通常质量较高
            timestamps = []
            
            # 提取时间戳信息
            if hasattr(response, 'segments') and response.segments:
                for segment in response.segments:
                    timestamps.append((
                        segment.start,
                        segment.end,
                        segment.text
                    ))
            
            return ASRResult(
                text=text,
                confidence=confidence,
                timestamps=timestamps,
                language=language,
                provider="openai_whisper"
            )
            
        except Exception as e:
            logger.error(f"OpenAI Whisper转录失败: {str(e)}")
            raise Exception(f"OpenAI Whisper转录失败: {str(e)}")
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return [
            "zh-CN", "en-US", "ja-JP", "ko-KR", "es-ES", "fr-FR", 
            "de-DE", "it-IT", "pt-BR", "ru-RU", "ar-SA", "hi-IN"
        ]
    
    def _convert_language_code(self, language: str) -> str:
        """将语言代码转换为Whisper支持的格式"""
        mapping = {
            "zh-CN": "zh",
            "en-US": "en",
            "ja-JP": "ja",
            "ko-KR": "ko",
            "es-ES": "es",
            "fr-FR": "fr",
            "de-DE": "de",
            "it-IT": "it",
            "pt-BR": "pt",
            "ru-RU": "ru",
            "ar-SA": "ar",
            "hi-IN": "hi"
        }
        return mapping.get(language, "zh")

class LocalWhisperProvider(ASRProvider):
    """本地Whisper ASR提供商（使用openai-whisper库）"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size  # tiny, base, small, medium, large
        self.model = None
    
    def is_available(self) -> bool:
        """检查本地Whisper是否可用"""
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    async def transcribe(self, audio_path: str, language: str = "zh-CN") -> ASRResult:
        """使用本地Whisper进行转录"""
        if not self.is_available():
            raise Exception("本地Whisper未安装，请运行: pip install openai-whisper")
        
        try:
            import whisper
            
            # 加载模型（首次使用时）
            if self.model is None:
                logger.info(f"加载Whisper模型: {self.model_size}")
                self.model = whisper.load_model(self.model_size)
            
            # 转录音频
            whisper_lang = self._convert_language_code(language)
            result = self.model.transcribe(
                audio_path,
                language=whisper_lang,
                word_timestamps=True
            )
            
            # 解析结果
            text = result["text"]
            confidence = 0.85  # 本地Whisper质量稍低
            timestamps = []
            
            # 提取时间戳信息
            if "segments" in result:
                for segment in result["segments"]:
                    timestamps.append((
                        segment["start"],
                        segment["end"],
                        segment["text"]
                    ))
            
            return ASRResult(
                text=text,
                confidence=confidence,
                timestamps=timestamps,
                language=language,
                provider="local_whisper"
            )
            
        except Exception as e:
            logger.error(f"本地Whisper转录失败: {str(e)}")
            raise Exception(f"本地Whisper转录失败: {str(e)}")
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return [
            "zh-CN", "en-US", "ja-JP", "ko-KR", "es-ES", "fr-FR", 
            "de-DE", "it-IT", "pt-BR", "ru-RU", "ar-SA", "hi-IN"
        ]
    
    def _convert_language_code(self, language: str) -> str:
        """将语言代码转换为Whisper支持的格式"""
        mapping = {
            "zh-CN": "zh",
            "en-US": "en",
            "ja-JP": "ja",
            "ko-KR": "ko",
            "es-ES": "es",
            "fr-FR": "fr",
            "de-DE": "de",
            "it-IT": "it",
            "pt-BR": "pt",
            "ru-RU": "ru",
            "ar-SA": "ar",
            "hi-IN": "hi"
        }
        return mapping.get(language, "zh")

class GoogleSpeechProvider(ASRProvider):
    """Google Speech-to-Text ASR提供商"""
    
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    def is_available(self) -> bool:
        """检查Google Speech API是否可用"""
        try:
            from google.cloud import speech
            return bool(self.credentials_path and os.path.exists(self.credentials_path))
        except ImportError:
            return False
    
    async def transcribe(self, audio_path: str, language: str = "zh-CN") -> ASRResult:
        """使用Google Speech-to-Text进行转录"""
        if not self.is_available():
            raise Exception("Google Speech API未配置或库未安装")
        
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            # 读取音频文件
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            # 配置识别请求
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language,
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
            )
            
            # 执行识别
            response = client.recognize(config=config, audio=audio)
            
            # 解析结果
            text = ""
            confidence = 0.0
            timestamps = []
            
            for result in response.results:
                alternative = result.alternatives[0]
                text += alternative.transcript + " "
                confidence = max(confidence, alternative.confidence)
                
                # 提取时间戳信息
                if hasattr(alternative, 'words'):
                    for word in alternative.words:
                        start_time = word.start_time.total_seconds()
                        end_time = word.end_time.total_seconds()
                        timestamps.append((start_time, end_time, word.word))
            
            return ASRResult(
                text=text.strip(),
                confidence=confidence,
                timestamps=timestamps,
                language=language,
                provider="google_speech"
            )
            
        except Exception as e:
            logger.error(f"Google Speech转录失败: {str(e)}")
            raise Exception(f"Google Speech转录失败: {str(e)}")
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return [
            "zh-CN", "en-US", "ja-JP", "ko-KR", "es-ES", "fr-FR", 
            "de-DE", "it-IT", "pt-BR", "ru-RU", "ar-SA", "hi-IN"
        ]

class ASRService:
    """统一ASR服务管理器"""
    
    def __init__(self):
        # 初始化所有提供商
        self.providers = {
            "openai_whisper": OpenAIWhisperProvider(),
            "local_whisper": LocalWhisperProvider(),
            "google_speech": GoogleSpeechProvider(),
        }
        
        # 设置优先级顺序
        self.provider_priority = ["openai_whisper", "local_whisper", "google_speech"]
        
        # 预加载可用的提供商
        self.available_providers = self._get_available_providers()
    
    def _get_available_providers(self) -> List[str]:
        """获取可用的ASR提供商"""
        available = []
        for name, provider in self.providers.items():
            if provider.is_available():
                available.append(name)
                logger.info(f"ASR提供商 {name} 可用")
            else:
                logger.warning(f"ASR提供商 {name} 不可用")
        return available
    
    async def transcribe_audio(self, audio_path: str, 
                             language: str = "zh-CN",
                             provider: str = None) -> ASRResult:
        """转录音频文件"""
        
        # 选择提供商
        if provider and provider in self.available_providers:
            selected_provider = provider
        else:
            # 使用第一个可用的提供商
            if not self.available_providers:
                raise Exception("没有可用的ASR提供商")
            selected_provider = self.available_providers[0]
        
        logger.info(f"使用 {selected_provider} 进行语音识别")
        
        try:
            provider_instance = self.providers[selected_provider]
            result = await provider_instance.transcribe(audio_path, language)
            
            logger.info(f"语音识别成功: {len(result.text)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}")
            
            # 尝试其他提供商
            for fallback_provider in self.available_providers:
                if fallback_provider != selected_provider:
                    try:
                        logger.info(f"尝试备用提供商: {fallback_provider}")
                        provider_instance = self.providers[fallback_provider]
                        result = await provider_instance.transcribe(audio_path, language)
                        
                        logger.info(f"备用提供商识别成功: {len(result.text)} 字符")
                        return result
                        
                    except Exception as fallback_error:
                        logger.error(f"备用提供商 {fallback_provider} 也失败: {str(fallback_error)}")
                        continue
            
            # 所有提供商都失败
            raise Exception(f"所有ASR提供商都失败，最后错误: {str(e)}")
    
    async def transcribe_video(self, video_path: str, 
                             language: str = "zh-CN",
                             provider: str = None) -> ASRResult:
        """从视频文件中提取音频并转录"""
        
        # 提取音频
        audio_path = await self._extract_audio_from_video(video_path)
        
        try:
            # 转录音频
            result = await self.transcribe_audio(audio_path, language, provider)
            return result
            
        finally:
            # 清理临时音频文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
    
    async def _extract_audio_from_video(self, video_path: str) -> str:
        """从视频中提取音频"""
        try:
            from moviepy.editor import VideoFileClip
            
            # 创建临时音频文件
            audio_path = tempfile.mktemp(suffix='.wav')
            
            # 提取音频
            video = VideoFileClip(video_path)
            audio = video.audio
            
            if audio is None:
                raise Exception("视频中没有音频轨道")
            
            # 导出音频为WAV格式
            audio.write_audiofile(audio_path, verbose=False, logger=None)
            
            # 关闭资源
            audio.close()
            video.close()
            
            return audio_path
            
        except Exception as e:
            raise Exception(f"音频提取失败: {str(e)}")
    
    def get_available_providers(self) -> List[str]:
        """获取可用的ASR提供商列表"""
        return self.available_providers.copy()
    
    def get_supported_languages(self, provider: str = None) -> List[str]:
        """获取支持的语言列表"""
        if provider and provider in self.providers:
            return self.providers[provider].get_supported_languages()
        else:
            # 返回所有提供商支持的语言的并集
            all_languages = set()
            for provider_name in self.available_providers:
                provider_instance = self.providers[provider_name]
                all_languages.update(provider_instance.get_supported_languages())
            return list(all_languages)
    
    async def batch_transcribe(self, audio_paths: List[str], 
                             language: str = "zh-CN",
                             provider: str = None) -> List[ASRResult]:
        """批量转录音频文件"""
        results = []
        
        for audio_path in audio_paths:
            try:
                result = await self.transcribe_audio(audio_path, language, provider)
                results.append(result)
            except Exception as e:
                logger.error(f"批量转录失败 {audio_path}: {str(e)}")
                # 创建一个错误结果
                error_result = ASRResult(
                    text="",
                    confidence=0.0,
                    timestamps=[],
                    language=language,
                    provider="error"
                )
                results.append(error_result)
        
        return results
    
    def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        health = {}
        for name, provider in self.providers.items():
            health[name] = provider.is_available()
        return health

# 全局ASR服务实例
asr_service = ASRService()

async def test_asr_service():
    """测试ASR服务"""
    print("🎤 ASR服务测试")
    print("=" * 50)
    
    # 检查可用提供商
    available = asr_service.get_available_providers()
    print(f"可用提供商: {available}")
    
    # 健康检查
    health = asr_service.health_check()
    print(f"健康状态: {health}")
    
    # 支持的语言
    languages = asr_service.get_supported_languages()
    print(f"支持的语言: {languages}")
    
    # 如果有测试音频文件，可以进行转录测试
    test_audio = "test_audio.wav"
    if os.path.exists(test_audio):
        print(f"\n测试转录: {test_audio}")
        try:
            result = await asr_service.transcribe_audio(test_audio)
            print(f"转录结果: {result.text}")
            print(f"置信度: {result.confidence}")
            print(f"提供商: {result.provider}")
        except Exception as e:
            print(f"转录失败: {str(e)}")
    else:
        print(f"\n测试音频文件不存在: {test_audio}")

if __name__ == "__main__":
    asyncio.run(test_asr_service()) 