"""
MCP客户端实现
用于连接和使用视频创作平台的MCP服务
"""
import aiohttp
import asyncio
import json
from typing import Dict, Any, List, Optional

class VideoCreatorMCPClient:
    """视频创作平台MCP客户端"""
    
    def __init__(self, server_url: str = "http://localhost:8000/mcp"):
        self.server_url = server_url
        self.session = None
        self.request_id = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _next_request_id(self) -> int:
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送MCP请求"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._next_request_id()
        }
        
        async with self.session.post(self.server_url, json=request_data) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP Error: {response.status}")
            
            result = await response.json()
            
            if "error" in result:
                raise RuntimeError(f"MCP Error: {result['error']['message']}")
            
            return result.get("result", {})
    
    # 资源操作方法
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源"""
        return await self._send_request("resources/read", {"uri": uri})
    
    async def write_resource(self, uri: str, content: Any) -> Dict[str, Any]:
        """写入资源"""
        return await self._send_request("resources/write", {"uri": uri, "content": content})
    
    async def list_resources(self, uri: str) -> List[Dict[str, Any]]:
        """列出资源"""
        result = await self._send_request("resources/list", {"uri": uri})
        return result if isinstance(result, list) else []
    
    # 工具操作方法
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        result = await self._send_request("tools/list")
        return result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用工具"""
        return await self._send_request("tools/call", {"name": name, "arguments": arguments or {}})
    
    # 项目管理方法
    async def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """创建新项目"""
        return await self.call_tool("create_project", {"name": name, "description": description})
    
    async def get_project_info(self, project_id: str) -> Dict[str, Any]:
        """获取项目信息"""
        return await self.read_resource(f"project://{project_id}/info")
    
    async def get_project_shots(self, project_id: str) -> Dict[str, Any]:
        """获取项目镜头列表"""
        return await self.read_resource(f"project://{project_id}/shots")
    
    async def save_project_analysis(self, project_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存项目分析结果"""
        return await self.write_resource(f"project://{project_id}/analysis", analysis_data)
    
    # 视频处理方法
    async def download_video(self, url: str) -> Dict[str, Any]:
        """下载视频"""
        return await self.call_tool("download_video", {"url": url})
    
    async def analyze_video(self, video_path: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """分析视频内容"""
        return await self.call_tool("analyze_video", {"video_path": video_path, "analysis_type": analysis_type})
    
    async def get_edit_suggestions(self, instruction: str, video_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取编辑建议"""
        return await self.call_tool("get_edit_suggestions", {
            "instruction": instruction,
            "video_context": video_context or {}
        })
    
    # 媒体生成方法
    async def generate_image(self, prompt: str, style: str = "realistic", size: str = "1024x1024") -> Dict[str, Any]:
        """生成图像"""
        return await self.call_tool("generate_image", {"prompt": prompt, "style": style, "size": size})
    
    async def text_to_speech(self, text: str, voice: str = "default", language: str = "zh-CN") -> Dict[str, Any]:
        """文字转语音"""
        return await self.call_tool("text_to_speech", {"text": text, "voice": voice, "language": language})
    
    async def speech_to_text(self, audio_path: str, language: str = "zh-CN") -> Dict[str, Any]:
        """语音转文字"""
        return await self.call_tool("speech_to_text", {"audio_path": audio_path, "language": language})
    
    # 媒体资源方法
    async def get_media_info(self, media_type: str, file_id: str) -> Dict[str, Any]:
        """获取媒体文件信息"""
        return await self.read_resource(f"media://{media_type}/{file_id}")
    
    async def save_media_analysis(self, file_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存媒体分析结果"""
        return await self.write_resource(f"media://analysis/{file_id}", analysis_data)
    
    async def list_media_files(self, media_type: str = "") -> List[Dict[str, Any]]:
        """列出媒体文件"""
        uri = f"media://{media_type}" if media_type else "media://"
        return await self.list_resources(uri)

# 高级客户端包装器
class AdvancedVideoCreatorClient(VideoCreatorMCPClient):
    """高级视频创作客户端，提供更便捷的工作流"""
    
    async def create_video_project_from_url(self, video_url: str, project_name: str = None) -> Dict[str, Any]:
        """从URL创建完整的视频项目"""
        
        # 1. 下载视频
        print("📥 下载视频...")
        download_result = await self.download_video(video_url)
        if not download_result.get("success"):
            return {"success": False, "error": "Failed to download video"}
        
        video_path = download_result["video_path"]
        video_title = download_result.get("title", "Untitled")
        
        # 2. 创建项目
        project_name = project_name or f"Project_{video_title}"
        print(f"📁 创建项目: {project_name}")
        project_result = await self.create_project(project_name, f"Project created from {video_url}")
        if not project_result.get("success"):
            return {"success": False, "error": "Failed to create project"}
        
        project_id = project_result["project_id"]
        
        # 3. 分析视频
        print("🔍 分析视频内容...")
        analysis_result = await self.analyze_video(video_path)
        if analysis_result.get("success"):
            # 保存分析结果
            await self.save_project_analysis(project_id, analysis_result["analysis"])
        
        return {
            "success": True,
            "project_id": project_id,
            "project_name": project_name,
            "video_path": video_path,
            "analysis": analysis_result.get("analysis") if analysis_result.get("success") else None
        }
    
    async def generate_video_assets(self, project_id: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """为项目生成所需的资源"""
        
        generated_assets = {}
        
        # 生成封面图片
        if "cover_image" in requirements:
            print("🖼️  生成封面图片...")
            cover_prompt = requirements["cover_image"]["prompt"]
            cover_result = await self.generate_image(
                prompt=cover_prompt,
                style=requirements["cover_image"].get("style", "realistic")
            )
            if cover_result.get("success"):
                generated_assets["cover_image"] = cover_result["images"]
        
        # 生成配音
        if "voiceover" in requirements:
            print("🎤 生成配音...")
            voiceover_text = requirements["voiceover"]["text"]
            tts_result = await self.text_to_speech(
                text=voiceover_text,
                voice=requirements["voiceover"].get("voice", "default"),
                language=requirements["voiceover"].get("language", "zh-CN")
            )
            if tts_result.get("success"):
                generated_assets["voiceover"] = tts_result["audio_path"]
        
        # 生成字幕（如果需要ASR）
        if "subtitles" in requirements:
            print("📝 生成字幕...")
            audio_path = requirements["subtitles"]["audio_path"]
            asr_result = await self.speech_to_text(
                audio_path=audio_path,
                language=requirements["subtitles"].get("language", "zh-CN")
            )
            if asr_result.get("success"):
                generated_assets["subtitles"] = {
                    "transcript": asr_result["transcript"],
                    "segments": asr_result["segments"]
                }
        
        return {
            "success": True,
            "project_id": project_id,
            "generated_assets": generated_assets
        }
    
    async def intelligent_video_editing(self, project_id: str, editing_instruction: str) -> Dict[str, Any]:
        """智能视频编辑工作流"""
        
        # 1. 获取项目信息
        print("📋 获取项目信息...")
        project_info = await self.get_project_info(project_id)
        
        # 2. 获取项目分析结果
        try:
            analysis_info = await self.read_resource(f"project://{project_id}/analysis")
            video_context = {
                "project": project_info,
                "analysis": analysis_info.get("data", {})
            }
        except:
            video_context = {"project": project_info}
        
        # 3. 获取编辑建议
        print("🤖 生成编辑建议...")
        suggestions_result = await self.get_edit_suggestions(editing_instruction, video_context)
        
        if not suggestions_result.get("success"):
            return {"success": False, "error": "Failed to generate edit suggestions"}
        
        suggestions = suggestions_result["suggestions"]
        
        # 4. 根据建议生成所需资源
        assets_to_generate = {}
        
        # 检查是否需要生成新的资源
        if "needs_cover_image" in suggestions and suggestions["needs_cover_image"]:
            assets_to_generate["cover_image"] = {
                "prompt": suggestions.get("cover_prompt", "Create a compelling thumbnail for this video"),
                "style": "youtube_thumbnail"
            }
        
        if "needs_voiceover" in suggestions and suggestions["needs_voiceover"]:
            assets_to_generate["voiceover"] = {
                "text": suggestions.get("voiceover_text", ""),
                "voice": "default"
            }
        
        # 生成资源
        generated_assets = {}
        if assets_to_generate:
            print("🛠️  生成所需资源...")
            assets_result = await self.generate_video_assets(project_id, assets_to_generate)
            if assets_result.get("success"):
                generated_assets = assets_result["generated_assets"]
        
        return {
            "success": True,
            "project_id": project_id,
            "editing_instruction": editing_instruction,
            "suggestions": suggestions,
            "generated_assets": generated_assets
        }