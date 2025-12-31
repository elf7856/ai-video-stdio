# 视频创作平台 MCP 服务指南

## 🎯 概述

基于你的视频创作平台实现的 Model Context Protocol (MCP) 服务，让AI模型能够直接访问和操作视频处理、内容分析、媒体生成等功能。

## 🏗️ 架构设计

```
┌─────────────────┐    MCP Protocol    ┌──────────────────┐
│   AI Client     │◄─────────────────►│  Video Creator   │
│   (Claude/GPT)  │                    │  MCP Server      │
└─────────────────┘                    └──────────────────┘
                                                │
                                       ┌────────┴────────┐
                                       │  Video Platform │
                                       │     Services    │
                                       │                 │
                                       │ • Video Manager │
                                       │ • LLM Service   │
                                       │ • Image Gen     │
                                       │ • TTS/ASR       │
                                       │ • Project Mgmt  │
                                       └─────────────────┘
```

## 🚀 快速开始

### 1. 启动服务

#### 方式1：集成在主应用中
```bash
cd /Users/xikangsong/workplace/video_creator_platform
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
MCP端点: `http://localhost:8000/mcp`

#### 方式2：独立MCP服务器
```bash
python run_mcp_server.py
```
MCP端点: `http://localhost:8001/mcp`

### 2. 验证服务
```bash
# 健康检查
curl http://localhost:8000/health

# MCP能力查询
curl http://localhost:8000/mcp/capabilities

# 工具列表
curl http://localhost:8000/mcp/tools
```

### 3. 运行测试
```bash
# 运行基本测试
python test_mcp.py

# 运行完整演示
python examples/mcp_demo.py
```

## 📊 功能特性

### 资源类型 (Resources)

#### 1. 项目资源 (`project://`)
```
project://                          # 列出所有项目
project://{project_id}/info          # 项目基本信息
project://{project_id}/shots         # 项目镜头列表
project://{project_id}/assets        # 项目资源文件
project://{project_id}/analysis      # 项目分析结果
```

**使用示例**:
```python
# 读取项目信息
project_info = await client.read_resource("project://demo_project/info")

# 保存分析结果
await client.write_resource("project://demo_project/analysis", analysis_data)
```

#### 2. 媒体资源 (`media://`)
```
media://                            # 列出媒体类型
media://videos/                     # 视频文件列表
media://audios/                     # 音频文件列表
media://images/                     # 图像文件列表
media://analysis/{file_id}          # 媒体分析结果
```

### 工具集 (Tools)

#### 1. 视频处理工具

**`download_video`** - 视频下载
```json
{
  "name": "download_video",
  "arguments": {
    "url": "https://example.com/video.mp4"
  }
}
```

**`analyze_video`** - 视频分析
```json
{
  "name": "analyze_video", 
  "arguments": {
    "video_path": "/path/to/video.mp4",
    "analysis_type": "comprehensive"
  }
}
```

#### 2. 媒体生成工具

**`generate_image`** - AI图像生成
```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "一个现代化的视频工作室",
    "style": "realistic",
    "size": "1920x1080"
  }
}
```

**`text_to_speech`** - 文字转语音
```json
{
  "name": "text_to_speech",
  "arguments": {
    "text": "欢迎使用AI视频创作平台",
    "voice": "default", 
    "language": "zh-CN"
  }
}
```

**`speech_to_text`** - 语音转文字
```json
{
  "name": "speech_to_text",
  "arguments": {
    "audio_path": "/path/to/audio.mp3",
    "language": "zh-CN"
  }
}
```

#### 3. 智能编辑工具

**`get_edit_suggestions`** - 智能编辑建议
```json
{
  "name": "get_edit_suggestions",
  "arguments": {
    "instruction": "创建30秒精彩集锦，添加动态字幕",
    "video_context": {
      "duration": 120,
      "topics": ["技术", "教程"]
    }
  }
}
```

#### 4. 项目管理工具

**`create_project`** - 创建项目
```json
{
  "name": "create_project",
  "arguments": {
    "name": "我的视频项目",
    "description": "项目描述"
  }
}
```

## 🔧 客户端使用

### 基础客户端
```python
from app.services.mcp.client import VideoCreatorMCPClient

async with VideoCreatorMCPClient("http://localhost:8000/mcp") as client:
    # 列出工具
    tools = await client.list_tools()
    
    # 调用工具
    result = await client.call_tool("create_project", {
        "name": "Test Project"
    })
    
    # 读取资源
    project_info = await client.read_resource("project://test_project/info")
```

### 高级客户端
```python
from app.services.mcp.client import AdvancedVideoCreatorClient

async with AdvancedVideoCreatorClient("http://localhost:8000/mcp") as client:
    # 从URL创建完整项目
    result = await client.create_video_project_from_url(
        video_url="https://example.com/video.mp4",
        project_name="My Project"
    )
    
    # 智能编辑工作流
    edit_result = await client.intelligent_video_editing(
        project_id=result["project_id"],
        editing_instruction="创建吸引人的短视频"
    )
```

## 🌐 REST API 接口

除了标准MCP协议，还提供REST风格的API：

### 工具调用
```bash
# 直接调用工具
POST /mcp/tools/create_project
Content-Type: application/json

{
  "name": "My Project",
  "description": "Project description"
}
```

### 资源访问
```bash
# 列出资源
GET /mcp/resources?uri=project://

# 读取资源
GET /mcp/resources/read?uri=project://demo_project/info

# 写入资源
POST /mcp/resources/write?uri=project://demo_project/analysis
Content-Type: application/json

{
  "analysis_data": {...}
}
```

## 📝 集成示例

### 与Claude桌面版集成

1. 在Claude桌面版的配置文件中添加：
```json
{
  "mcpServers": {
    "video-creator": {
      "command": "node",
      "args": ["path/to/mcp-client.js"],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8000/mcp"
      }
    }
  }
}
```

2. Claude就能直接调用你的视频处理功能：
```
用户: "帮我从这个YouTube链接创建一个项目并分析视频内容"
Claude: 我来帮你处理这个视频...
[调用 download_video 工具]
[调用 create_project 工具]  
[调用 analyze_video 工具]
```

### 自定义AI应用集成

```python
import openai
from app.services.mcp.client import VideoCreatorMCPClient

class AIVideoAssistant:
    def __init__(self):
        self.mcp_client = VideoCreatorMCPClient("http://localhost:8000/mcp")
        self.openai_client = openai.Client()
    
    async def process_user_request(self, user_input: str):
        # 1. LLM分析用户意图
        analysis = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user", 
                "content": f"分析用户需求并生成MCP工具调用: {user_input}"
            }]
        )
        
        # 2. 执行MCP工具调用
        tool_calls = parse_tool_calls(analysis.choices[0].message.content)
        
        results = []
        async with self.mcp_client as client:
            for tool_call in tool_calls:
                result = await client.call_tool(
                    tool_call["name"], 
                    tool_call["arguments"]
                )
                results.append(result)
        
        return results
```

## 🔍 监控和调试

### 日志查看
```bash
# 查看MCP请求日志
tail -f logs/mcp.log

# 查看服务器日志
tail -f logs/server.log
```

### 性能监控
```python
# 内置性能监控
GET /mcp/stats
{
  "requests_count": 150,
  "tools_called": {
    "analyze_video": 45,
    "generate_image": 30,
    "create_project": 20
  },
  "resources_accessed": {
    "project": 80,
    "media": 35
  },
  "average_response_time": "1.2s"
}
```

## ⚡ 最佳实践

### 1. 资源访问优化
```python
# ✅ 好的做法：批量获取
resources = await client.list_resources("project://")
for resource in resources:
    info = await client.read_resource(resource["uri"])

# ❌ 避免：频繁单个查询
for project_id in project_ids:
    info = await client.read_resource(f"project://{project_id}/info")
```

### 2. 错误处理
```python
try:
    result = await client.call_tool("analyze_video", {"video_path": path})
    if not result.get("success"):
        handle_tool_error(result.get("error"))
except Exception as e:
    handle_network_error(e)
```

### 3. 异步处理
```python
# 对于长时间运行的任务，使用后台处理
async def process_large_video(video_path: str):
    # 启动后台任务
    task_id = await client.call_tool("start_background_analysis", {
        "video_path": video_path
    })
    
    # 轮询状态
    while True:
        status = await client.read_resource(f"project://tasks/{task_id}")
        if status["completed"]:
            return status["result"]
        await asyncio.sleep(5)
```

## 🚨 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查服务状态
   curl http://localhost:8000/health
   
   # 检查端口占用
   lsof -i :8000
   ```

2. **工具调用失败**
   ```bash
   # 查看工具列表
   curl http://localhost:8000/mcp/tools
   
   # 检查参数格式
   python test_mcp.py
   ```

3. **资源访问错误**
   ```bash
   # 检查资源权限
   ls -la uploads/
   
   # 查看资源列表
   curl "http://localhost:8000/mcp/resources?uri=project://"
   ```

### 调试技巧

1. **开启详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用测试工具**
   ```bash
   # 运行完整测试套件
   python test_mcp.py http://localhost:8000
   ```

3. **手动测试MCP请求**
   ```bash
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "method": "tools/list",
       "params": {},
       "id": 1
     }'
   ```

## 📈 扩展开发

### 添加新工具
```python
# 在 VideoCreatorMCPServer 中添加
async def custom_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    # 工具逻辑
    return {"success": True, "result": "..."}

# 注册工具
self.tools["custom_tool"] = custom_tool
```

### 添加新资源类型
```python
class CustomResourceHandler(ResourceHandler):
    async def read(self, uri: str) -> Dict[str, Any]:
        # 读取逻辑
        pass
    
    async def write(self, uri: str, content: Any) -> Dict[str, Any]:
        # 写入逻辑
        pass

# 注册资源处理器
server.resources["custom"] = CustomResourceHandler()
```

---

## 🎉 总结

这个MCP实现为你的视频创作平台提供了：

✅ **标准化接口** - 符合MCP协议规范  
✅ **丰富功能** - 完整的视频处理和AI能力  
✅ **灵活部署** - 可集成或独立运行  
✅ **易于扩展** - 模块化设计，便于添加新功能  
✅ **完善工具** - 测试、监控、调试工具齐全  

现在AI模型可以直接操作你的视频平台，创建真正的AI驱动视频创作工作流！