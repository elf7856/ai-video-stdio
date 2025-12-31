# AI视频创作平台 - 环境部署手册

## 📋 系统环境要求

### 🐍 Python后端环境 (Video Creator Platform)
```bash
# Python版本
Python 3.12.9 (推荐 3.11+)
pip 25.0+

# 操作系统支持
- macOS (开发环境)
- Ubuntu 20.04+ (生产推荐)
- Windows 10+ (开发支持)
```

### 🟢 Node.js前端环境 (OpenCut)
```bash
# Node.js版本
Node.js v24.2.0 (推荐 18+)
npm 11.4.2+

# 包管理器
bun 1.2.18 (推荐，更快的包管理器)
# 或使用 npm/yarn
```

## 🔧 核心依赖汇总

### 后端依赖 (requirements.txt)
```txt
# Web框架
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6

# AI和LLM服务
litellm>=1.70.0
openai>=1.3.0
anthropic>=0.7.0
google-genai>=0.1.0

# 视频处理
moviepy>=1.0.3
opencv-python>=4.8.0
ffmpeg-python>=0.2.0
yt-dlp>=2023.12.30

# 音频处理和ASR
pydub>=0.25.1
librosa>=0.10.1
openai-whisper>=20231117
google-cloud-speech>=2.21.0

# 图像生成和处理
Pillow>=10.0.0
diffusers>=0.24.0
transformers>=4.35.0
torch>=2.0.0

# TTS语音合成
edge-tts>=6.1.9
elevenlabs>=0.2.26

# 数据库
sqlalchemy>=2.0.0
alembic>=1.12.0

# 图像生成API
replicate>=0.22.0
stability-sdk>=0.8.0
```

### 前端依赖 (package.json核心部分)
```json
{
  "dependencies": {
    "@ffmpeg/ffmpeg": "^0.12.15",
    "@ffmpeg/core": "^0.12.10",
    "next": "^14.x.x",
    "react": "^18.x.x",
    "typescript": "^5.x.x",
    "@hello-pangea/dnd": "^18.0.1",
    "@radix-ui/*": "^1.x.x",
    "better-auth": "^1.2.7",
    "drizzle-orm": "^0.x.x",
    "zustand": "^4.x.x"
  }
}
```

## 🐳 Docker环境配置

### 后端Dockerfile
```dockerfile
FROM python:3.12-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 前端Dockerfile
```dockerfile
FROM node:24-alpine

# 安装bun
RUN npm install -g bun

# 设置工作目录
WORKDIR /app

# 复制包配置文件
COPY package.json bun.lockb ./

# 安装依赖
RUN bun install

# 复制应用代码
COPY . .

# 构建应用
RUN bun run build

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["bun", "run", "start"]
```

## 🏗️ Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端API服务
  video-creator-api:
    build: 
      context: ./video_creator_platform
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/video_creator
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs

  # 前端编辑器
  opencut-editor:
    build:
      context: ./OpenCut/apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - video-creator-api

  # 数据库
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: video_creator
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # 缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - video-creator-api
      - opencut-editor

volumes:
  postgres_data:
  redis_data:
```

## 🔑 环境变量配置

### 后端环境变量 (.env)
```bash
# 应用配置
APP_NAME=AI视频创作平台
VERSION=1.0.0
DEBUG=True

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/video_creator
REDIS_URL=redis://localhost:6379

# AI服务API密钥
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_API_KEY=AIzaSyxxx
REPLICATE_API_TOKEN=r8_xxx

# 云存储配置
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_S3_BUCKET=video-creator-storage

# 文件路径
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
```

### 前端环境变量 (.env.local)
```bash
# API配置
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# 认证配置
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# 数据库配置 (OpenCut自用)
DATABASE_URL=postgresql://postgres:password@localhost:5432/opencut

# Redis配置
UPSTASH_REDIS_REST_URL=xxx
UPSTASH_REDIS_REST_TOKEN=xxx
```

## 🚀 快速启动脚本

### 开发环境启动
```bash
#!/bin/bash
# start_dev.sh

echo "🚀 启动AI视频创作平台开发环境"

# 启动后端
echo "📡 启动Video Creator API (端口8000)..."
cd video_creator_platform
python -m uvicorn app.main:app --reload --port 8000 &

# 启动前端
echo "🎬 启动OpenCut编辑器 (端口3000)..."
cd ../OpenCut/apps/web
bun run dev &

echo "✅ 开发环境启动完成!"
echo "📖 API文档: http://localhost:8000/docs"
echo "🎨 编辑器: http://localhost:3000"

wait
```

### 生产环境启动
```bash
#!/bin/bash
# start_prod.sh

echo "🏭 启动生产环境"

# 启动Docker服务
docker-compose up -d

echo "✅ 生产环境启动完成!"
echo "🌐 访问地址: http://localhost"
```

## 📦 系统要求

### 最低配置
```
CPU: 4核心
内存: 8GB RAM
存储: 50GB可用空间
网络: 稳定的互联网连接
```

### 推荐配置
```
CPU: 8核心+ (支持AVX指令集，加速AI推理)
内存: 16GB+ RAM
GPU: NVIDIA GPU (CUDA 11.8+, 用于图像生成)
存储: 100GB+ SSD
网络: 带宽≥100Mbps
```

## 🧪 环境验证脚本

```bash
#!/bin/bash
# check_env.sh

echo "🔍 检查环境配置"

# 检查Python
python --version
pip --version

# 检查Node.js
node --version
npm --version

# 检查FFmpeg
ffmpeg -version | head -1

# 检查GPU (可选)
nvidia-smi

# 检查端口占用
lsof -i :8000
lsof -i :3000
lsof -i :5432
lsof -i :6379

echo "✅ 环境检查完成"
```

## 📋 部署检查清单

- [ ] Python 3.11+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] FFmpeg 已安装
- [ ] PostgreSQL 数据库可连接
- [ ] Redis 缓存可连接
- [ ] API密钥已配置
- [ ] 云存储已配置
- [ ] 端口 8000, 3000 可用
- [ ] SSL证书已配置 (生产环境)
- [ ] 域名解析已配置 (生产环境)

这个环境手册涵盖了完整的部署需求！🎯