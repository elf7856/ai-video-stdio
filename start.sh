#!/usr/bin/env bash
# Railway 启动脚本 - 正确处理 PORT 环境变量

set -e  # 遇到错误立即退出

# 如果 PORT 未设置，使用默认值 8000
PORT=${PORT:-8000}

echo "=========================================="
echo "Starting Video Creator Platform"
echo "Port: $PORT"
echo "=========================================="

# 启动 uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
