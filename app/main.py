from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.utils.database import init_db
from app.api import videos, images

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI驱动的视频二创平台，支持自然语言编辑和多媒体生成"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
if os.path.exists(settings.output_dir):
    app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")

# 包含路由
app.include_router(videos.router)
app.include_router(images.router)

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 初始化数据库
    init_db()
    
    # 确保目录存在
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)
    
    print(f"🚀 {settings.app_name} v{settings.version} 启动成功")
    print(f"📁 上传目录: {settings.upload_dir}")
    print(f"📁 输出目录: {settings.output_dir}")

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
            "视频处理和合成"
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