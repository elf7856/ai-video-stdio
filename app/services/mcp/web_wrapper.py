"""
MCP Web服务器包装器
将MCP服务器暴露为HTTP API
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json

from .server import VideoCreatorMCPServer

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = {}
    id: Optional[int] = None

class MCPWebWrapper:
    """MCP Web服务器包装器"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.mcp_server = VideoCreatorMCPServer()
        
        # 添加路由
        self.setup_routes()
    
    def setup_routes(self):
        """设置MCP路由"""
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: MCPRequest):
            """处理MCP请求"""
            try:
                request_dict = request.dict()
                response = await self.mcp_server.handle_request(request_dict)
                return response
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp/capabilities")
        async def get_capabilities():
            """获取MCP服务器能力"""
            try:
                capabilities = {
                    "resources": {
                        "supported_schemes": ["project", "media"],
                        "operations": ["read", "write", "list"]
                    },
                    "tools": {
                        "available_tools": list(self.mcp_server.tools.keys()),
                        "operations": ["list", "call"]
                    },
                    "server": {
                        "name": self.mcp_server.name,
                        "version": self.mcp_server.version,
                        "description": "Video Creator Platform MCP Server"
                    }
                }
                return capabilities
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp/tools")
        async def list_tools():
            """列出所有工具"""
            try:
                tools = self.mcp_server.get_tool_schemas()
                return {"tools": tools}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/tools/{tool_name}")
        async def call_tool(tool_name: str, arguments: Dict[str, Any] = {}):
            """直接调用工具（REST风格）"""
            try:
                if tool_name not in self.mcp_server.tools:
                    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
                
                result = await self.mcp_server.tools[tool_name](arguments)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp/resources")
        async def list_resources(uri: str = ""):
            """列出资源（REST风格）"""
            try:
                if not uri:
                    # 返回所有资源类型
                    return {
                        "resources": [
                            {"scheme": "project", "description": "Video projects and related data"},
                            {"scheme": "media", "description": "Media files and analysis results"}
                        ]
                    }
                
                scheme = uri.split("://")[0] if "://" in uri else "project"
                handler = self.mcp_server.resources.get(scheme)
                
                if not handler:
                    raise HTTPException(status_code=404, detail=f"Resource scheme not supported: {scheme}")
                
                result = await handler.list(uri)
                return {"resources": result}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp/resources/read")
        async def read_resource(uri: str):
            """读取资源（REST风格）"""
            try:
                scheme = uri.split("://")[0] if "://" in uri else "project" 
                handler = self.mcp_server.resources.get(scheme)
                
                if not handler:
                    raise HTTPException(status_code=404, detail=f"Resource scheme not supported: {scheme}")
                
                result = await handler.read(uri)
                return result
                
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/resources/write")
        async def write_resource(uri: str, content: Any):
            """写入资源（REST风格）"""
            try:
                scheme = uri.split("://")[0] if "://" in uri else "project"
                handler = self.mcp_server.resources.get(scheme)
                
                if not handler:
                    raise HTTPException(status_code=404, detail=f"Resource scheme not supported: {scheme}")
                
                result = await handler.write(uri, content)
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))