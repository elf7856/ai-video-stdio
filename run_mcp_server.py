"""
独立的MCP服务器启动脚本
可以单独运行MCP服务，不依赖主应用
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.mcp.web_wrapper import MCPWebWrapper
from app.core.config import settings

def create_mcp_app():
    """创建独立的MCP应用"""
    
    app = FastAPI(
        title="Video Creator Platform MCP Server",
        version="1.0.0",
        description="Model Context Protocol server for Video Creator Platform",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 添加CORS支持
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 初始化MCP服务
    mcp_wrapper = MCPWebWrapper(app)
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "name": "Video Creator Platform MCP Server",
            "version": "1.0.0",
            "description": "Model Context Protocol server providing video processing and AI capabilities",
            "endpoints": {
                "mcp": "/mcp",
                "capabilities": "/mcp/capabilities", 
                "tools": "/mcp/tools",
                "resources": "/mcp/resources"
            },
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "service": "Video Creator MCP Server",
            "capabilities": {
                "resources": ["project", "media"],
                "tools": 7,  # 当前工具数量
                "version": "1.0.0"
            }
        }
    
    return app

async def start_mcp_server():
    """启动MCP服务器"""
    print("🔌 启动独立MCP服务器...")
    print(f"📡 服务器地址: http://localhost:8001")
    print(f"📚 API文档: http://localhost:8001/docs")
    print(f"🔧 MCP端点: http://localhost:8001/mcp")
    print("-" * 50)
    
    app = create_mcp_app()
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=True
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(start_mcp_server())
    except KeyboardInterrupt:
        print("\n\n⏹️  MCP服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")