from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

# 依赖注入和配置
from app.core.config import settings
from app.utils.database import init_db
from app import dependencies

# 导入所有需要实例化的服务
from app.services.video.downloader import VideoDownloader
# 使用轻量级处理器（基于 ffmpeg，不需要 cv2/moviepy）
try:
    from app.services.video.processor_lite import VideoProcessor
except ImportError:
    from app.services.video.processor import VideoProcessor
from app.services.llm.analyzer import VideoAnalyzer
from app.services.image.generator import ImageServiceManager
from app.services.tts.generator import TTSGenerator
from app.services.video.manager import VideoProcessingManager

# 导入API路由
from app.api import videos, images
from app.api.projects import router as projects_router  # 恢复启用
from app.api.gateway import gateway_router
from app.api.ai_director import router as ai_director_router
from app.api.audio import router as audio_router
from app.api.scripts import router as scripts_router
from app.api.video_generation import router as video_generation_router
from app.api.upload import router as upload_router
from app.api.editor import router as editor_router  # 新增：视频编辑器
from app.api.quality import router as quality_router  # 新增：质量检查
from app.api.templates import router as templates_router # 新增：模板
from app.api import auth, users  # 新增
import app.models.user  # 确保模型注册
# from app.services.mcp.web_wrapper import MCPWebWrapper  # 临时禁用
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI驱动的视频二创平台，支持自然语言编辑和多媒体生成"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    # TODO: [安全性] 生产环境中必须将 "*" 替换为明确的前端域名。
    # 警告: 使用 "*" 会允许任何网站访问此API，存在CSRF安全风险。
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加自定义中间件为静态文件添加 CORS 头
class StaticFilesCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # 为 /outputs 和 /uploads 路径添加 CORS 头
        if request.url.path.startswith(("/outputs", "/uploads")):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(StaticFilesCORSMiddleware)

# 包含API路由
app.include_router(auth.router)  # 新增
app.include_router(users.router) # 新增
app.include_router(scripts_router)
app.include_router(video_generation_router)
app.include_router(editor_router)  # 新增：视频编辑器
app.include_router(projects_router)  # 恢复启用
app.include_router(gateway_router)
app.include_router(audio_router)
app.include_router(videos.router)
app.include_router(images.router)
app.include_router(ai_director_router)
app.include_router(upload_router)
app.include_router(quality_router)  # 新增：质量检查
app.include_router(templates_router) # 新增：模板

# 初始化MCP服务 - 临时禁用避免启动错误
# mcp_wrapper = MCPWebWrapper(app)

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 1. 初始化数据库
    init_db()
    
    # 2. 确保目录存在
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)
    
    # 3. 创建并注入依赖
    logger.info("🔧 Initializing and injecting services...")
    downloader = VideoDownloader()
    processor = VideoProcessor()
    analyzer = VideoAnalyzer()
    image_manager = ImageServiceManager()
    tts_generator = TTSGenerator()
    
    # 将所有服务实例注入到VideoProcessingManager中
    dependencies.video_manager = VideoProcessingManager(
        downloader=downloader,
        processor=processor,
        analyzer=analyzer,
        image_manager=image_manager,
        tts_generator=tts_generator
    )
    logger.info("✅ Services initialized and injected.")
    
    logger.info(f"🚀 {settings.app_name} v{settings.version} 启动成功")
    logger.info(f"📁 上传目录: {settings.upload_dir}")
    logger.info(f"📁 输出目录: {settings.output_dir}")
    logger.info(f"🔌 MCP服务已启用: http://localhost:{settings.port}/mcp")

# 挂载静态文件
output_path = os.path.abspath(settings.output_dir)
upload_path = os.path.abspath(settings.upload_dir)

if not os.path.exists(output_path):
    os.makedirs(output_path, exist_ok=True)
    logger.info(f"创建输出目录: {output_path}")

app.mount("/outputs", StaticFiles(directory=output_path), name="outputs")
logger.info(f"✅ 静态目录挂载成功: /outputs -> {output_path}")

if os.path.exists(upload_path):
    app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.app_name}",
        "version": settings.version,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": settings.app_name}

@app.get("/api/info")
async def get_api_info():
    """获取API信息"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "features": [
            "视频上传和分析",
            "自然语言编辑",
            "TTS语音合成",
            "AI图像生成",
            "视频处理和合成",
            "视频质量检查",
            "自动重新生成低质量片段"
        ],
        "supported_formats": {
            "video": settings.allowed_video_formats,
            "audio": settings.allowed_audio_formats,
            "image": settings.allowed_image_formats
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 