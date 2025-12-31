# AI视频创作平台 (AI Video Creator Platform)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个AI驱动的视频创作平台，专注于**将用户的文字稿件自动转换为包含多个镜头的专业视频**。

本平台的核心是“AI导演”系统，它模仿人类导演的工作流程，负责从内容理解、智能分镜、时长分配到视频生成的端到端自动化流程，旨在将传统数小时甚至数天的视频制作周期缩短到分钟级别。

> 详细的 **[架构设计](docs/architecture.md)**, **[功能列表](docs/features.md)**, **[API参考](docs/api_reference.md)**, 和 **[安装指南](docs/setup.md)** 请查阅 `docs` 目录。

## 🌟 核心功能

- **AI导演系统**:
  - **智能脚本分析**: 使用LLM深度理解脚本，并自动切分为逻辑连贯的场景。
  - **自动分镜规划**: 为每个场景设计专业的镜头（Shot），并生成高质量的视频生成Prompt。
  - **精确时长分配**: 根据内容重要性和用户目标，为每个镜头（3-15秒）分配合理的时长。
- **多API视频生成**:
  - 集成并管理多个主流视频生成API（如Google Veo, Runway等）。
  - 根据成本和内容类型智能选择API，并支持失败重试。
- **模块化AI工具箱**:
  - **视频处理**: 从URL下载视频、内容分析、关键帧提取。
  - **图像生成**: 集成DALL-E, Stable Diffusion等，支持本地模型。
  - **语音合成 (TTS)**: 集成Edge TTS等，并提供系统TTS作为备用。
- **标准化项目管理**:
  - 为每个视频生成任务创建独立、结构化的项目目录。
  - 完整记录分镜计划、元数据和生成日志，便于追溯和管理。

## 🚀 快速上手

### 1. 环境准备
- Python 3.11+
- FFmpeg

### 2. 安装与配置
```bash
# 克隆项目
git clone <repository-url>
cd video_creator_platform

# 安装依赖 (建议在虚拟环境中)
pip install -r requirements.txt

# 创建并配置环境变量
cp .env.example .env
# 然后编辑 .env 文件，至少填入一个AI服务的API密钥，如 OPENAI_API_KEY
```

### 3. 启动服务
```bash
# 启动后端API服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后，即可通过API与平台交互。
- **API文档**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **健康检查**: [http://localhost:8000/health](http://localhost:8000/health)

## 🧪 运行测试
在开始使用前，建议运行测试以确保所有组件正常工作。
```bash
# 运行完整的测试套件
pytest tests/
```

## 🗂️ 项目结构
```
.
├── app/                  # 核心应用代码
│   ├── api/              # API路由
│   ├── core/             # 核心配置与服务
│   ├── models/           # Pydantic数据模型
│   └── services/         # 业务逻辑服务
│       ├── director/     # AI导演系统核心
│       ├── image/        # 图像生成服务
│       ├── tts/          # TTS服务
│       └── video/        # 视频处理服务
├── docs/                 # 详细文档
│   ├── architecture.md
│   ├── api_reference.md
│   ├── features.md
│   ├── setup.md
│   └── archive/          # 旧文档归档
├── tests/                # 测试代码
├── .env.example          # 环境变量示例
├── docker-compose.yml    # Docker部署配置
└── requirements.txt      # Python依赖
```

## 🤝 贡献

欢迎提交Issue和Pull Request。

## 📄 许可证

本项目采用 [MIT License](LICENSE)。