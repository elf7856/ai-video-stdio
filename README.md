# AI视频创作平台

一个基于AI的智能视频创作和处理平台，支持从视频链接下载、内容分析、自然语言编辑、TTS语音合成、AI图像生成等功能。

## 🌟 主要功能

### 1. 视频下载与处理
- **多平台支持**: YouTube、Bilibili、TikTok、Instagram、Twitter等
- **智能下载**: 自动识别平台并下载最佳质量视频
- **格式转换**: 支持多种视频格式的转换和处理

### 2. 视频内容分析
- **AI分析**: 使用大语言模型分析视频内容、主题、情感
- **关键帧提取**: 自动提取视频关键帧进行进一步分析
- **标签生成**: 智能生成视频标签和分类

### 3. 自然语言编辑
- **智能理解**: 理解自然语言编辑指令
- **自动生成**: 根据指令自动生成图像、音频等内容
- **视频合成**: 将生成的内容智能插入到视频中

### 4. AI图像生成
- **多API支持**: DALL-E、Stability AI、Replicate、Leonardo AI等
- **风格预设**: 支持多种艺术风格和效果
- **批量生成**: 支持批量图像生成和处理

### 5. TTS语音合成
- **多引擎支持**: Edge TTS、ElevenLabs等
- **多语言支持**: 支持多种语言和声音
- **情感控制**: 支持情感和语调的调整

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd video_creator_platform

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件并配置必要的API密钥：

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# 图像生成API
STABILITY_API_KEY=your_stability_api_key
REPLICATE_API_KEY=your_replicate_api_key
LEONARDO_API_KEY=your_leonardo_api_key

# TTS API
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# 其他配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=100000000
```

### 3. 运行服务器

```bash
# 启动开发服务器
python -m uvicorn app.main:app --reload

# 访问API文档
# http://localhost:8000/docs
```

## 📋 完整流程示例

### 从URL处理视频的完整流程

```python
from app.services.video.manager import VideoProcessingManager

# 初始化视频处理管理器
video_manager = VideoProcessingManager()

# 1. 从URL下载并分析视频
result = await video_manager.process_video_from_url(
    url="https://www.youtube.com/watch?v=example",
    auto_analyze=True
)

if result["success"]:
    print(f"视频下载成功: {result['video_title']}")
    print(f"分析结果: {result['analysis']}")
    
    # 2. 生成视频摘要
    summary = await video_manager.generate_video_summary(
        result["video_path"], 
        summary_type="text"
    )
    
    # 3. 自然语言编辑
    edit_result = await video_manager.process_natural_language_edit(
        result["video_path"],
        "在视频开头添加一个标题文字"
    )
```

### API使用示例

#### 1. 从URL处理视频

```bash
curl -X POST "http://localhost:8000/api/videos/process-url" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.youtube.com/watch?v=example",
       "auto_analyze": true
     }'
```

#### 2. 生成视频摘要

```bash
curl -X POST "http://localhost:8000/api/videos/1/summary" \
     -H "Content-Type: application/json" \
     -d '{
       "summary_type": "text"
     }'
```

#### 3. 自然语言编辑

```bash
curl -X POST "http://localhost:8000/api/videos/1/edit" \
     -H "Content-Type: application/json" \
     -d '{
       "instruction": "在视频开头添加一个标题文字"
     }'
```

## 🏗️ 项目结构

```
video_creator_platform/
├── app/
│   ├── api/                    # API路由
│   │   ├── videos.py          # 视频处理API
│   │   ├── images.py          # 图像生成API
│   │   └── tts.py             # TTS API
│   ├── services/              # 核心服务
│   │   ├── video/             # 视频处理服务
│   │   │   ├── downloader.py  # 视频下载器
│   │   │   ├── processor.py   # 视频处理器
│   │   │   └── manager.py     # 视频管理器
│   │   ├── image/             # 图像生成服务
│   │   │   └── generator.py   # 图像生成器
│   │   ├── tts/               # TTS服务
│   │   │   └── generator.py   # TTS生成器
│   │   └── llm/               # LLM服务
│   │       └── analyzer.py    # 内容分析器
│   ├── models/                # 数据模型
│   ├── prompts/               # 提示词模板
│   └── core/                  # 核心配置
├── tests/                     # 测试文件
│   ├── test_video_flow.py     # 视频流程测试
│   ├── test_image_generation.py # 图像生成测试
│   ├── test_prompt_system.py  # 提示词系统测试
│   ├── test_basic.py          # 基础功能测试
│   ├── test_system.py         # 系统集成测试
│   ├── conftest.py            # pytest配置
│   └── __init__.py            # 测试包初始化
├── examples/                  # 使用示例
├── docs/                      # 文档
├── uploads/                   # 上传文件目录
├── outputs/                   # 输出文件目录
├── run_tests.py               # 测试运行脚本
└── run.py                     # 应用启动脚本
```

## 🔧 核心组件

### VideoProcessingManager
视频处理的核心管理器，整合了下载、分析、编辑等功能：

- `process_video_from_url()`: 从URL处理视频的完整流程
- `analyze_video_content()`: 分析视频内容
- `generate_video_summary()`: 生成视频摘要
- `process_natural_language_edit()`: 处理自然语言编辑指令

### VideoDownloader
支持多平台的视频下载器：

- YouTube、Bilibili、TikTok、Instagram、Twitter
- 自动识别平台并选择最佳下载策略
- 支持获取视频信息而不下载

### ImageServiceManager
多API图像生成服务：

- DALL-E、Stability AI、Replicate、Leonardo AI
- 自动故障转移和负载均衡
- 支持多种艺术风格和预设

## 📚 API文档

启动服务器后访问 `http://localhost:8000/docs` 查看完整的API文档。

### 主要端点

- `POST /api/videos/process-url`: 从URL处理视频
- `POST /api/videos/{id}/analyze`: 分析视频内容
- `POST /api/videos/{id}/summary`: 生成视频摘要
- `POST /api/videos/{id}/edit`: 自然语言编辑
- `POST /api/images/generate`: 生成图像
- `POST /api/tts/generate`: 生成语音

## 🧪 测试

### 运行所有测试
```bash
# 使用测试运行脚本
python run_tests.py

# 或使用pytest
python -m pytest tests/ -v
```

### 运行单个测试
```bash
# 运行视频流程测试
python tests/test_video_flow.py

# 运行图像生成测试
python tests/test_image_generation.py

# 运行提示词系统测试
python tests/test_prompt_system.py
```

### 运行示例
```bash
# 运行完整流程示例
python examples/video_processing_flow.py
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [yt-dlp文档](https://github.com/yt-dlp/yt-dlp)
- [MoviePy文档](https://zulko.github.io/moviepy/)
- [LiteLLM文档](https://docs.litellm.ai/) 