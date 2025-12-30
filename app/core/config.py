from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Video Creator Platform"
    version: str = "0.1.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    # 图像生成API Keys
    dalle_api_key: Optional[str] = None  # 使用OpenAI API Key
    midjourney_api_key: Optional[str] = None
    stability_api_key: Optional[str] = None
    replicate_api_key: Optional[str] = None
    leonardo_api_key: Optional[str] = None
    runway_api_key: Optional[str] = None
    
    # 数据库配置
    database_url: str = "sqlite:///./video_creator.db"
    
    # 文件存储配置
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_video_formats: list = [".mp4", ".avi", ".mov", ".mkv", ".wmv"]
    allowed_audio_formats: list = [".mp3", ".wav", ".m4a", ".aac"]
    allowed_image_formats: list = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    # LLM配置 - 移除默认模型，在服务层根据提供商选择模型
    # default_llm_model: str = "gpt-4o-mini"  # 不再在配置中指定默认模型
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # TTS配置
    default_tts_voice: str = "zh-CN-XiaoxiaoNeural"
    tts_speed: float = 1.0
    
    # 视频处理配置
    max_video_duration: int = 300  # 5分钟
    video_quality: str = "medium"
    fps: int = 30
    
    # 图像生成配置
    default_image_model: str = "stabilityai/stable-diffusion-2-1"
    default_image_provider: str = "dalle"  # dalle, midjourney, stability, replicate, leonardo, runway, local
    image_size: tuple = (512, 512)
    
    # 图像生成API配置
    dalle_model: str = "dall-e-3"
    dalle_quality: str = "standard"  # standard, hd
    dalle_style: str = "vivid"  # vivid, natural
    
    stability_model: str = "stable-diffusion-xl-1024-v1-0"
    stability_engine: str = "stable-diffusion-xl-1024-v1-0"
    
    replicate_model: str = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
    
    leonardo_model: str = "ac614f96-1082-45bf-be9d-757f2d31c174"  # Leonardo Creative
    
    # 图像生成限制
    max_concurrent_generations: int = 5
    generation_timeout: int = 300  # 5分钟
    retry_attempts: int = 3
    
    # 前端配置
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # 安全配置
    secret_key: str = "your-secret-key-here-change-in-production"
    allowed_hosts: str = "localhost,127.0.0.1,0.0.0.0"
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # 允许额外字段

# 创建全局设置实例
settings = Settings()

# 辅助函数：检查API密钥是否可用
def has_openai_key() -> bool:
    """检查是否配置了有效的OpenAI API密钥"""
    return bool(settings.openai_api_key and settings.openai_api_key.strip())

def has_elevenlabs_key() -> bool:
    """检查是否配置了有效的ElevenLabs API密钥"""
    return bool(settings.elevenlabs_api_key and settings.elevenlabs_api_key.strip())

def has_stability_key() -> bool:
    """检查是否配置了有效的Stability AI API密钥"""
    return bool(settings.stability_api_key and settings.stability_api_key.strip())

def has_replicate_key() -> bool:
    """检查是否配置了有效的Replicate API密钥"""
    return bool(settings.replicate_api_key and settings.replicate_api_key.strip())

def has_leonardo_key() -> bool:
    """检查是否配置了有效的Leonardo API密钥"""
    return bool(settings.leonardo_api_key and settings.leonardo_api_key.strip())

def get_available_image_providers() -> list:
    """获取可用的图像生成服务提供商列表"""
    providers = []
    if has_openai_key():
        providers.append("dalle")
    if has_stability_key():
        providers.append("stability")
    if has_replicate_key():
        providers.append("replicate")
    if has_leonardo_key():
        providers.append("leonardo")
    return providers

def get_available_llm_providers() -> list:
    """获取可用的LLM服务提供商列表"""
    providers = []
    if has_openai_key():
        providers.append("openai")
    if settings.anthropic_api_key and settings.anthropic_api_key.strip():
        providers.append("anthropic")
    if settings.google_api_key and settings.google_api_key.strip():
        providers.append("google")
    return providers

# 确保目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True) 