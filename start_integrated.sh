#!/bin/bash

# 一体化部署启动脚本

echo "🚀 启动Video Creator Platform一体化部署..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 停止可能运行的服务
echo "🛑 停止现有服务..."
pkill -f "npm run dev" || true
pkill -f "uvicorn" || true

# 构建和启动所有服务
echo "🔨 构建Docker镜像..."
docker compose build

echo "🚀 启动所有服务..."
docker compose up -d

echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker compose ps

# 健康检查
echo "🏥 进行健康检查..."
curl -f http://localhost/health || echo "❌ 健康检查失败"

echo ""
echo "✅ 部署完成！"
echo "🌐 前端访问: http://localhost"
echo "🔌 API文档: http://localhost/api/docs"
echo "📋 查看日志: docker compose logs -f"
echo "🛑 停止服务: docker compose down"