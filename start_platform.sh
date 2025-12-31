#!/bin/bash

# AI视频创作平台 - 集成启动脚本
echo "🎬 AI视频创作平台 - 集成启动"
echo "================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python 3.8+"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js 16+"
    exit 1
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, installing basic dependencies..."
    pip install fastapi uvicorn pydantic
fi

# 进入前端目录并构建
echo "🔧 构建前端应用..."
cd frontend

# 安装前端依赖（如果node_modules不存在）
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 构建前端
echo "🏗️  构建前端生产版本..."
npm run build

# 返回根目录
cd ..

# 创建输出目录
mkdir -p output

# 启动集成服务器
echo "🚀 启动集成服务器..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 访问地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "💡 按 Ctrl+C 停止服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python integrated_server.py