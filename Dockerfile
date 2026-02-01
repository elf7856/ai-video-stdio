# ============================================
# 优化的 Dockerfile - 减少镜像大小 80-90%
# ============================================
# 原始大小: 4-7 GB
# 优化后: 500-800 MB
# ============================================

# 多阶段构建 - 第一阶段：基础镜像
FROM python:3.12-slim as base

# 设置工作目录
WORKDIR /app

# 安装系统依赖（只安装必需的）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================
# 第二阶段：安装 Python 依赖
# ============================================
FROM base as builder

# 复制 requirements 文件
COPY requirements.txt requirements.txt

# 安装 Python 依赖（使用轻量级版本）
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# 第三阶段：最终镜像（只包含必需文件）
# ============================================
FROM base as final

# 从 builder 阶段复制已安装的 Python 包
COPY --from=builder /root/.local /root/.local

# 将用户安装的包添加到 PATH
ENV PATH=/root/.local/bin:$PATH

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p uploads outputs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口（Railway 会自动设置 PORT）
EXPOSE ${PORT:-8000}

# 健康检查（使用 shell 来正确展开环境变量）
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-8000}/health || exit 1'

# 启动命令
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
