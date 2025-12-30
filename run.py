#!/usr/bin/env python3
"""
Video Creator Platform 启动脚本
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"🚀 启动 {settings.app_name} v{settings.version}")
    print(f"📖 API文档: http://localhost:8000/docs")
    print(f"🔧 重新加载: {'启用' if settings.debug else '禁用'}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    ) 