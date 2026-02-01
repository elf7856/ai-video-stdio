#!/bin/bash

# Railway 快速部署脚本
# 使用方法: ./deploy-railway.sh

set -e

echo "🚀 Railway 部署准备检查..."

# 检查是否安装了 Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI 未安装"
    echo "📦 正在安装 Railway CLI..."
    npm install -g @railway/cli
fi

echo "✅ Railway CLI 已安装"

# 检查是否登录
if ! railway whoami &> /dev/null; then
    echo "🔐 请登录 Railway..."
    railway login
fi

echo "✅ 已登录 Railway"

# 选择部署方式
echo ""
echo "请选择部署方式:"
echo "1) 部署后端服务"
echo "2) 部署前端服务"
echo "3) 部署完整应用（前后端）"
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo "📦 部署后端服务..."
        railway up
        echo "✅ 后端部署完成！"
        echo "🔗 请在 Railway 控制台查看服务 URL"
        ;;
    2)
        echo "📦 部署前端服务..."
        cd frontend
        railway up
        cd ..
        echo "✅ 前端部署完成！"
        echo "🔗 请在 Railway 控制台查看服务 URL"
        ;;
    3)
        echo "📦 部署完整应用..."
        echo "⚠️  请确保已在 Railway 控制台创建了两个服务"
        echo ""
        echo "部署后端..."
        railway up
        echo ""
        echo "部署前端..."
        cd frontend
        railway up
        cd ..
        echo "✅ 完整应用部署完成！"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "🎉 部署完成！"
echo ""
echo "📝 下一步:"
echo "1. 在 Railway 控制台设置环境变量"
echo "2. 配置自定义域名（可选）"
echo "3. 检查服务健康状态"
echo ""
echo "📚 详细文档: docs/RAILWAY_DEPLOYMENT.md"
