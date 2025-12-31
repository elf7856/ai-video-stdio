"""
基于视频创作平台的MCP服务器实现
提供视频处理、AI分析、内容生成等资源和工具
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import aiofiles
from pathlib import Path

# 导入项目核心服务
from app.core.config import settings
from app.services.llm.service import llm_service
from app.services.video.manager import VideoProcessingManager
from app.services.video.downloader import VideoDownloader
from app.services.image.generator import ImageServiceManager
from app.services.audio.tts_service import TTSService
from app.services.audio.asr_service import ASRService
from app.services.project.manager import ProjectManager  # 更新：从新位置导入
from app.services.analysis.content_analyzer import ContentAnalyzer

# MCP协议数据结构
@dataclass
class MCPRequest:
    jsonrpc: str = "2.0"
    method: str = ""
    params: Dict[str, Any] = None
    id: Optional[int] = None

@dataclass
class MCPResponse:
    jsonrpc: str = "2.0"
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int] = None

@dataclass
class MCPResource:
    uri: str
    name: str
    description: str
    mime_type: str
    metadata: Dict[str, Any] = None

@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]

# 资源处理器基类
class ResourceHandler(ABC):
    @abstractmethod
    async def read(self, uri: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def write(self, uri: str, content: Any) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def list(self, uri: str) -> List[Dict[str, Any]]:
        pass

# 项目资源处理器
class ProjectResourceHandler(ResourceHandler):
    """处理项目相关的资源访问"""
    
    def __init__(self):
        self.project_manager = ProjectManager()
        self.base_path = Path(settings.upload_dir)
        self.base_path.mkdir(exist_ok=True)
    
    async def read(self, uri: str) -> Dict[str, Any]:
        """读取项目资源"""
        try:
            # 解析URI: project://project_id/resource_type/resource_id
            parts = uri.replace("project://", "").split("/")
            
            if len(parts) < 2:
                raise ValueError("Invalid project URI format")
            
            project_id = parts[0]
            resource_type = parts[1]
            resource_id = parts[2] if len(parts) > 2 else None
            
            if resource_type == "info":
                # 获取项目信息
                project = self.project_manager.get_project(project_id)
                if not project:
                    raise FileNotFoundError(f"Project not found: {project_id}")
                project_info = {
                    "id": project.id,
                    "title": project.title,
                    "status": project.status.value,
                    "target_duration": project.target_duration,
                    "progress": project.get_progress_percentage(),
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                    "final_video_path": project.final_video_path,
                    "total_shots": project.total_shots,
                    "completed_shots": project.completed_shots,
                    "failed_shots": project.failed_shots
                }
                return {
                    "type": "project_info",
                    "project_id": project_id,
                    "data": project_info,
                    "uri": uri
                }
            
            elif resource_type == "shots":
                # 获取镜头信息
                project = self.project_manager.get_project(project_id)
                if not project:
                    raise FileNotFoundError(f"Project not found: {project_id}")
                shots = []
                # 从项目元数据读取分镜计划
                try:
                    metadata_dir = Path(project.output_dir) / "metadata"
                    shot_plan_file = metadata_dir / "shot_plan.json"
                    if shot_plan_file.exists():
                        with open(shot_plan_file, 'r', encoding='utf-8') as f:
                            shot_plan = json.load(f)
                        shots = shot_plan.get("shots", [])
                except Exception:
                    shots = []
                return {
                    "type": "shots_list", 
                    "project_id": project_id,
                    "shots": shots,
                    "uri": uri
                }
            
            elif resource_type == "assets":
                # 获取资源文件
                if resource_id:
                    asset_path = self.base_path / project_id / "assets" / resource_id
                    if asset_path.exists():
                        async with aiofiles.open(asset_path, 'rb') as f:
                            content = await f.read()
                        return {
                            "type": "asset",
                            "content": content.hex(),  # 二进制内容转hex
                            "size": len(content),
                            "uri": uri
                        }
                    else:
                        raise FileNotFoundError(f"Asset not found: {resource_id}")
                else:
                    # 列出所有资源
                    assets_dir = self.base_path / project_id / "assets"
                    if assets_dir.exists():
                        assets = [f.name for f in assets_dir.iterdir() if f.is_file()]
                        return {
                            "type": "assets_list",
                            "project_id": project_id,
                            "assets": assets,
                            "uri": uri
                        }
            
            elif resource_type == "analysis":
                # 获取分析结果
                analysis_path = self.base_path / project_id / "analysis.json"
                if analysis_path.exists():
                    async with aiofiles.open(analysis_path, 'r') as f:
                        content = await f.read()
                    return {
                        "type": "analysis",
                        "project_id": project_id,
                        "data": json.loads(content),
                        "uri": uri
                    }
            
            raise ValueError(f"Unknown resource type: {resource_type}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to read project resource {uri}: {str(e)}")
    
    async def write(self, uri: str, content: Any) -> Dict[str, Any]:
        """写入项目资源"""
        try:
            parts = uri.replace("project://", "").split("/")
            project_id = parts[0]
            resource_type = parts[1]
            
            project_dir = self.base_path / project_id
            project_dir.mkdir(exist_ok=True)
            
            if resource_type == "analysis":
                # 保存分析结果
                analysis_path = project_dir / "analysis.json"
                async with aiofiles.open(analysis_path, 'w') as f:
                    await f.write(json.dumps(content, indent=2))
                
                return {
                    "success": True,
                    "message": f"Analysis saved for project {project_id}",
                    "uri": uri
                }
            
            elif resource_type == "assets":
                # 保存资源文件
                resource_id = parts[2] if len(parts) > 2 else f"asset_{uuid.uuid4().hex[:8]}"
                assets_dir = project_dir / "assets"
                assets_dir.mkdir(exist_ok=True)
                
                asset_path = assets_dir / resource_id
                
                if isinstance(content, str):
                    # 文本内容
                    async with aiofiles.open(asset_path, 'w') as f:
                        await f.write(content)
                elif isinstance(content, bytes):
                    # 二进制内容
                    async with aiofiles.open(asset_path, 'wb') as f:
                        await f.write(content)
                else:
                    # JSON内容
                    async with aiofiles.open(asset_path, 'w') as f:
                        await f.write(json.dumps(content, indent=2))
                
                return {
                    "success": True,
                    "resource_id": resource_id,
                    "path": str(asset_path),
                    "uri": uri
                }
            
        except Exception as e:
            raise RuntimeError(f"Failed to write project resource {uri}: {str(e)}")
    
    async def list(self, uri: str) -> List[Dict[str, Any]]:
        """列出项目资源"""
        try:
            if uri == "project://":
                # 列出所有项目
                projects = []
                if self.base_path.exists():
                    for project_dir in self.base_path.iterdir():
                        if project_dir.is_dir():
                            projects.append({
                                "name": project_dir.name,
                                "type": "project",
                                "uri": f"project://{project_dir.name}",
                                "modified": project_dir.stat().st_mtime
                            })
                return projects
            
            else:
                # 列出项目内容
                parts = uri.replace("project://", "").split("/")
                project_id = parts[0]
                
                resources = []
                project_dir = self.base_path / project_id
                
                if project_dir.exists():
                    # 基本项目结构
                    resources.extend([
                        {
                            "name": "info",
                            "type": "project_info",
                            "uri": f"project://{project_id}/info",
                            "description": "项目基本信息"
                        },
                        {
                            "name": "shots",
                            "type": "shots_list",
                            "uri": f"project://{project_id}/shots", 
                            "description": "项目镜头列表"
                        },
                        {
                            "name": "assets",
                            "type": "assets_folder",
                            "uri": f"project://{project_id}/assets",
                            "description": "项目资源文件"
                        }
                    ])
                    
                    # 检查是否有分析结果
                    if (project_dir / "analysis.json").exists():
                        resources.append({
                            "name": "analysis",
                            "type": "analysis_result",
                            "uri": f"project://{project_id}/analysis",
                            "description": "项目分析结果"
                        })
                
                return resources
                
        except Exception as e:
            raise RuntimeError(f"Failed to list project resources {uri}: {str(e)}")

# 媒体资源处理器
class MediaResourceHandler(ResourceHandler):
    """处理媒体文件的资源访问"""
    
    def __init__(self):
        self.video_manager = VideoProcessingManager()
        self.media_path = Path(settings.upload_dir) / "media"
        self.media_path.mkdir(exist_ok=True)
    
    async def read(self, uri: str) -> Dict[str, Any]:
        """读取媒体资源"""
        try:
            # 解析URI: media://type/file_id
            parts = uri.replace("media://", "").split("/")
            media_type = parts[0]  # video, audio, image
            file_id = parts[1] if len(parts) > 1 else None
            
            if media_type == "video" and file_id:
                # 读取视频文件信息
                video_path = self.media_path / "videos" / file_id
                if video_path.exists():
                    # 获取视频元数据
                    metadata = await self.video_manager.get_video_info(str(video_path))
                    
                    return {
                        "type": "video",
                        "file_id": file_id,
                        "path": str(video_path),
                        "metadata": metadata,
                        "size": video_path.stat().st_size,
                        "uri": uri
                    }
            
            elif media_type == "analysis" and file_id:
                # 读取媒体分析结果
                analysis_path = self.media_path / "analysis" / f"{file_id}.json"
                if analysis_path.exists():
                    async with aiofiles.open(analysis_path, 'r') as f:
                        content = await f.read()
                    return {
                        "type": "media_analysis",
                        "file_id": file_id,
                        "data": json.loads(content),
                        "uri": uri
                    }
            
            raise FileNotFoundError(f"Media resource not found: {uri}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to read media resource {uri}: {str(e)}")
    
    async def write(self, uri: str, content: Any) -> Dict[str, Any]:
        """写入媒体资源"""
        try:
            parts = uri.replace("media://", "").split("/")
            media_type = parts[0]
            file_id = parts[1] if len(parts) > 1 else f"media_{uuid.uuid4().hex[:8]}"
            
            if media_type == "analysis":
                # 保存分析结果
                analysis_dir = self.media_path / "analysis"
                analysis_dir.mkdir(exist_ok=True)
                
                analysis_path = analysis_dir / f"{file_id}.json"
                async with aiofiles.open(analysis_path, 'w') as f:
                    await f.write(json.dumps(content, indent=2))
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "path": str(analysis_path),
                    "uri": uri
                }
            
        except Exception as e:
            raise RuntimeError(f"Failed to write media resource {uri}: {str(e)}")
    
    async def list(self, uri: str) -> List[Dict[str, Any]]:
        """列出媒体资源"""
        try:
            if uri == "media://":
                # 列出媒体类型
                return [
                    {"name": "videos", "type": "folder", "uri": "media://videos"},
                    {"name": "audios", "type": "folder", "uri": "media://audios"},
                    {"name": "images", "type": "folder", "uri": "media://images"},
                    {"name": "analysis", "type": "folder", "uri": "media://analysis"}
                ]
            
            else:
                parts = uri.replace("media://", "").split("/")
                media_type = parts[0]
                
                media_dir = self.media_path / media_type
                if media_dir.exists():
                    files = []
                    for file_path in media_dir.iterdir():
                        if file_path.is_file():
                            files.append({
                                "name": file_path.name,
                                "type": "file",
                                "uri": f"media://{media_type}/{file_path.name}",
                                "size": file_path.stat().st_size,
                                "modified": file_path.stat().st_mtime
                            })
                    return files
                
                return []
                
        except Exception as e:
            raise RuntimeError(f"Failed to list media resources {uri}: {str(e)}")

# 视频创作平台MCP服务器
class VideoCreatorMCPServer:
    """视频创作平台的MCP服务器"""
    
    def __init__(self):
        self.name = "Video Creator Platform MCP Server"
        self.version = "1.0.0"
        
        # 初始化资源处理器
        self.resources: Dict[str, ResourceHandler] = {
            "project": ProjectResourceHandler(),
            "media": MediaResourceHandler()
        }
        
        # 初始化服务
        self.llm_service = llm_service
        self.video_manager = VideoProcessingManager()
        self.video_downloader = VideoDownloader()
        self.image_service = ImageServiceManager()
        self.tts_service = TTSService()
        self.asr_service = ASRService()
        self.content_analyzer = ContentAnalyzer()
        
        # 工具注册
        self.tools: Dict[str, Callable] = {}
        self._register_tools()
        
        self.logger = logging.getLogger(__name__)
    
    def _register_tools(self):
        """注册所有可用工具"""
        
        # 视频下载工具
        async def download_video(params: Dict[str, Any]) -> Dict[str, Any]:
            url = params.get("url")
            if not url:
                raise ValueError("URL is required")
            
            try:
                result = await self.video_downloader.download_video(url)
                return {
                    "success": True,
                    "video_path": result.get("video_path"),
                    "title": result.get("title"),
                    "duration": result.get("duration"),
                    "file_size": result.get("file_size")
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 视频分析工具
        async def analyze_video(params: Dict[str, Any]) -> Dict[str, Any]:
            video_path = params.get("video_path")
            analysis_type = params.get("analysis_type", "comprehensive")
            
            if not video_path:
                raise ValueError("video_path is required")
            
            try:
                result = await self.content_analyzer.analyze_video_content(
                    video_path, 
                    analysis_type
                )
                return {
                    "success": True,
                    "analysis": result
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 图像生成工具
        async def generate_image(params: Dict[str, Any]) -> Dict[str, Any]:
            prompt = params.get("prompt")
            style = params.get("style", "realistic")
            size = params.get("size", "1024x1024")
            
            if not prompt:
                raise ValueError("prompt is required")
            
            try:
                result = await self.image_service.generate_image(
                    prompt=prompt,
                    style=style,
                    size=size
                )
                return {
                    "success": True,
                    "images": result.get("images", []),
                    "generation_time": result.get("generation_time", 0)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # TTS工具
        async def text_to_speech(params: Dict[str, Any]) -> Dict[str, Any]:
            text = params.get("text")
            voice = params.get("voice", "default")
            language = params.get("language", "zh-CN")
            
            if not text:
                raise ValueError("text is required")
            
            try:
                result = await self.tts_service.text_to_speech(
                    text=text,
                    voice=voice,
                    language=language
                )
                return {
                    "success": True,
                    "audio_path": result
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # ASR工具
        async def speech_to_text(params: Dict[str, Any]) -> Dict[str, Any]:
            audio_path = params.get("audio_path")
            language = params.get("language", "zh-CN")
            
            if not audio_path:
                raise ValueError("audio_path is required")
            
            try:
                result = await self.asr_service.transcribe_audio(
                    audio_path=audio_path,
                    language=language
                )
                return {
                    "success": True,
                    "transcript": result.get("text", ""),
                    "segments": result.get("segments", []),
                    "confidence": result.get("confidence", 0.0)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 智能编辑建议工具
        async def get_edit_suggestions(params: Dict[str, Any]) -> Dict[str, Any]:
            instruction = params.get("instruction")
            video_context = params.get("video_context", {})
            
            if not instruction:
                raise ValueError("instruction is required")
            
            try:
                # 构建分析提示
                context_info = "\n".join([f"{k}: {v}" for k, v in video_context.items()]) if video_context else "无上下文信息"
                prompt = f"""请分析以下视频编辑指令并提供建议：

编辑指令：{instruction}

视频上下文：
{context_info}

请提供：
1. 指令理解和解析
2. 具体的编辑建议
3. 可能需要的参数或设置

请以JSON格式返回建议。"""

                llm_result = llm_service.simple_call(prompt, max_tokens=1500, temperature=0.7)
                if llm_result.get("success"):
                    result = llm_result["content"]
                else:
                    raise Exception(llm_result.get("error", "LLM调用失败"))

                return {
                    "success": True,
                    "suggestions": result
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 项目创建工具
        async def create_project(params: Dict[str, Any]) -> Dict[str, Any]:
            project_name = params.get("name", f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            description = params.get("description", "")
            
            try:
                project_manager = ProjectManager()
                project_id = await project_manager.create_project(
                    name=project_name,
                    description=description
                )
                return {
                    "success": True,
                    "project_id": project_id,
                    "name": project_name
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 注册所有工具
        self.tools = {
            "download_video": download_video,
            "analyze_video": analyze_video, 
            "generate_image": generate_image,
            "text_to_speech": text_to_speech,
            "speech_to_text": speech_to_text,
            "get_edit_suggestions": get_edit_suggestions,
            "create_project": create_project
        }
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的schema定义"""
        return [
            {
                "name": "download_video",
                "description": "Download video from URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Video URL to download"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "analyze_video", 
                "description": "Analyze video content using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "video_path": {"type": "string", "description": "Path to video file"},
                        "analysis_type": {"type": "string", "description": "Type of analysis", "default": "comprehensive"}
                    },
                    "required": ["video_path"]
                }
            },
            {
                "name": "generate_image",
                "description": "Generate image using AI",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "prompt": {"type": "string", "description": "Image generation prompt"},
                        "style": {"type": "string", "description": "Image style", "default": "realistic"},
                        "size": {"type": "string", "description": "Image size", "default": "1024x1024"}
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "text_to_speech",
                "description": "Convert text to speech",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to convert"},
                        "voice": {"type": "string", "description": "Voice to use", "default": "default"},
                        "language": {"type": "string", "description": "Language code", "default": "zh-CN"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "speech_to_text",
                "description": "Convert speech to text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audio_path": {"type": "string", "description": "Path to audio file"},
                        "language": {"type": "string", "description": "Language code", "default": "zh-CN"}
                    },
                    "required": ["audio_path"]
                }
            },
            {
                "name": "get_edit_suggestions",
                "description": "Get AI-powered video editing suggestions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instruction": {"type": "string", "description": "Editing instruction"},
                        "video_context": {"type": "object", "description": "Video context information"}
                    },
                    "required": ["instruction"]
                }
            },
            {
                "name": "create_project",
                "description": "Create a new video project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Project name"},
                        "description": {"type": "string", "description": "Project description"}
                    }
                }
            }
        ]
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")
            
            method_parts = method.split("/")
            if len(method_parts) != 2:
                raise ValueError(f"Invalid method format: {method}")
            
            category, action = method_parts
            
            if category == "resources":
                return await self._handle_resource_request(action, params, request_id)
            elif category == "tools":
                return await self._handle_tool_request(action, params, request_id)
            elif category == "prompts":
                return await self._handle_prompt_request(action, params, request_id)
            else:
                raise ValueError(f"Unknown category: {category}")
        
        except Exception as e:
            self.logger.error(f"Error handling request: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -1,
                    "message": str(e)
                },
                "id": request.get("id")
            }
    
    async def _handle_resource_request(self, action: str, params: Dict[str, Any], request_id: Optional[int]) -> Dict[str, Any]:
        """处理资源请求"""
        uri = params.get("uri", "")
        scheme = uri.split("://")[0] if "://" in uri else "project"
        
        handler = self.resources.get(scheme)
        if not handler:
            raise ValueError(f"Unsupported resource scheme: {scheme}")
        
        if action == "read":
            result = await handler.read(uri)
        elif action == "write":
            content = params.get("content")
            result = await handler.write(uri, content)
        elif action == "list":
            result = await handler.list(uri)
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
    
    async def _handle_tool_request(self, action: str, params: Dict[str, Any], request_id: Optional[int]) -> Dict[str, Any]:
        """处理工具请求"""
        if action == "list":
            tools = self.get_tool_schemas()
            return {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            }
        
        elif action == "call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            result = await self.tools[tool_name](arguments)
            
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _handle_prompt_request(self, action: str, params: Dict[str, Any], request_id: Optional[int]) -> Dict[str, Any]:
        """处理提示符请求"""
        # 这里可以添加预定义的提示符模板
        prompts = [
            {
                "name": "video_analysis",
                "description": "Analyze video content comprehensively",
                "arguments": [
                    {"name": "video_path", "description": "Path to the video file", "required": True}
                ]
            },
            {
                "name": "edit_instruction",
                "description": "Generate editing suggestions based on natural language instructions",
                "arguments": [
                    {"name": "instruction", "description": "Natural language editing instruction", "required": True},
                    {"name": "video_context", "description": "Context about the video", "required": False}
                ]
            }
        ]
        
        if action == "list":
            return {
                "jsonrpc": "2.0",
                "result": {"prompts": prompts},
                "id": request_id
            }
        elif action == "get":
            name = params.get("name")
            prompt = next((p for p in prompts if p["name"] == name), None)
            if not prompt:
                raise ValueError(f"Unknown prompt: {name}")
            return {
                "jsonrpc": "2.0",
                "result": prompt,
                "id": request_id
            }
        
        return {
            "jsonrpc": "2.0",
            "result": {},
            "id": request_id
        }