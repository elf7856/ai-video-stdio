from pydantic_settings import BaseSettings
from pydantic import Field
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
    elevenlabs_api_key: Optional[str] = Field(default=None, alias="ELEVENLABS_API_KEY")
    
    # 图像生成API Keys
    midjourney_api_key: Optional[str] = Field(default=None, alias="MIDJOURNEY_API_KEY")
    stability_api_key: Optional[str] = Field(default=None, alias="STABILITY_API_KEY")
    replicate_api_key: Optional[str] = Field(default=None, alias="REPLICATE_API_KEY")
    leonardo_api_key: Optional[str] = Field(default=None, alias="LEONARDO_API_KEY")
    
    # 视频生成API Keys
    runway_api_key: str = Field(default="", alias="RUNWAY_API_KEY", description="Runway ML API密钥")
    luma_api_key: str = Field(default="", alias="LUMA_API_KEY", description="Luma Dream Machine API密钥")
    pika_api_key: str = Field(default="", alias="PIKA_API_KEY", description="Pika Labs API密钥")
    kling_api_key: str = Field(default="", alias="KLING_API_KEY", description="Kling AI API密钥")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY", description="Google Gemini API密钥")
    pexels_api_key: str = Field(default="", alias="PEXELS_API_KEY", description="Pexels API密钥")

    # Vertex AI 配置
    vertex_project_id: Optional[str] = Field(default=None, alias="VERTEX_PROJECT_ID")
    vertex_location: str = Field(default="us-central1", alias="VERTEX_LOCATION")
    vertex_api_key: Optional[str] = Field(default=None, alias="VERTEX_API_KEY")
    vertex_auth_method: str = Field(default="api_key", alias="VERTEX_AUTH_METHOD")

    # 多平台上传配置
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID", description="Google OAuth Client ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET", description="Google OAuth Client Secret")
    
    # 数据库配置
    database_url: str = "sqlite:///./video_creator.db"
    
    # 文件存储配置
    upload_dir: str = os.path.abspath("./uploads")
    output_dir: str = os.path.abspath("./outputs")
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
    default_image_provider: str = "google_imagen"  # google_imagen, stability, replicate, leonardo, midjourney, local
    image_size: tuple = (512, 512)

    # 图像生成API配置
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
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allowed_hosts: str = "localhost,127.0.0.1,0.0.0.0"
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600

    # ============================================================
    # 存储配置 (Storage Configuration)
    # ============================================================
    storage_type: str = Field(default="local", alias="STORAGE_TYPE", description="存储类型: local 或 oss")
    
    # OSS / S3 配置
    oss_access_key_id: Optional[str] = Field(default=None, alias="OSS_ACCESS_KEY_ID")
    oss_access_key_secret: Optional[str] = Field(default=None, alias="OSS_ACCESS_KEY_SECRET")
    oss_endpoint: Optional[str] = Field(default=None, alias="OSS_ENDPOINT", description="例如: oss-cn-hangzhou.aliyuncs.com")
    oss_bucket_name: Optional[str] = Field(default=None, alias="OSS_BUCKET_NAME")
    oss_region: Optional[str] = Field(default=None, alias="OSS_REGION")
    
    # CDN 配置 (如果不配置，默认使用 OSS 域名)
    cdn_domain: Optional[str] = Field(default=None, alias="CDN_DOMAIN", description="例如: https://cdn.example.com")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # 允许额外字段
        populate_by_name = True  # 允许通过字段名或别名填充

# 创建全局设置实例
settings = Settings()

# 辅助函数：检查API密钥是否可用
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
    if settings.google_api_key and settings.google_api_key.strip():
        providers.append("google")
    return providers

# 确保目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True) 