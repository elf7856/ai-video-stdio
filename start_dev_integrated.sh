#!/bin/bash
# 启动开发环境脚本

echo "🚀 启动AI视频创作平台集成开发环境"
echo "================================================"

# 检查端口占用
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        echo "⚠️  端口 $1 被占用，正在清理..."
        lsof -ti :$1 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# 清理端口
check_port 8000
check_port 3000

echo "🔧 启动后端服务 (Video Creator Platform)..."
cd /Users/xikangsong/workplace/video_creator_platform
python -m uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

echo "⏳ 等待后端服务启动..."
sleep 5

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务启动成功 (PID: $BACKEND_PID)"
    echo "📖 API文档: http://localhost:8000/docs"
    echo "🌐 网关健康检查: http://localhost:8000/api/gateway/health"
else
    echo "❌ 后端服务启动失败"
    echo "📋 查看日志: tail -f backend.log"
    exit 1
fi

echo "🎬 启动前端服务 (OpenCut Editor)..."
cd /Users/xikangsong/workplace/OpenCut/apps/web
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "⏳ 等待前端服务启动..."
sleep 8

# 检查前端是否启动成功
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务启动成功 (PID: $FRONTEND_PID)"
    echo "🎨 编辑器: http://localhost:3000"
else
    echo "❌ 前端服务启动失败"
    echo "📋 查看日志: tail -f frontend.log"
fi

echo ""
echo "🎉 集成开发环境启动完成！"
echo "================================================"
echo "🔗 服务地址:"
echo "  📡 后端API: http://localhost:8000"
echo "  📖 API文档: http://localhost:8000/docs"
echo "  🌐 API网关: http://localhost:8000/api/gateway"
echo "  🎬 视频编辑器: http://localhost:3000"
echo ""
echo "🛑 停止服务: kill $BACKEND_PID $FRONTEND_PID"
echo "📋 查看日志: tail -f backend.log frontend.log"

# 保存PID到文件
echo "$BACKEND_PID $FRONTEND_PID" > .dev_pids

echo "✋ 按 Ctrl+C 停止服务..."
trap "echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# 保持脚本运行
wait