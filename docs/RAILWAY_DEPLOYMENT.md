# Railway 部署指南

本指南将帮助你将视频创作平台部署到 Railway。

## 项目架构

这是一个全栈应用，包含：
- **后端**: FastAPI (Python) - 处理视频生成、AI 调用等
- **前端**: React + Vite - 用户界面和视频编辑器

## Railway 部署方案

Railway 需要分别部署前后端作为两个独立的服务。

### 方案 A: 推荐方案（两个独立服务）

#### 1. 后端服务部署

**步骤：**

1. **登录 Railway**
   - 访问 https://railway.app
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库

3. **配置后端服务**
   - Railway 会自动检测到 `Dockerfile` 并使用它构建
   - 服务名称: `backend` 或 `api`

4. **设置环境变量**

   在 Railway 项目的 Variables 标签页添加以下环境变量：

   ```bash
   # 必需的环境变量
   PORT=8000
   PYTHONPATH=/app
   PYTHONUNBUFFERED=1

   # AI 服务配置
   GOOGLE_API_KEY=your_google_api_key
   OPENAI_API_KEY=your_openai_api_key

   # 视频生成服务
   REPLICATE_API_TOKEN=your_replicate_token

   # 数据库（如果使用）
   DATABASE_URL=postgresql://...

   # 其他 API Keys
   PEXELS_API_KEY=your_pexels_key
   SHUTTERSTOCK_API_KEY=your_shutterstock_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   ```

5. **添加持久化存储（可选）**
   - 在 Railway 项目中添加 Volume
   - 挂载路径: `/app/uploads` 和 `/app/outputs`
   - 这样上传的文件和生成的视频不会在重启后丢失

6. **部署**
   - Railway 会自动构建和部署
   - 记录后端 URL，例如: `https://your-backend.railway.app`

#### 2. 前端服务部署

**步骤：**

1. **在同一个 Railway 项目中添加新服务**
   - 点击 "New Service"
   - 选择 "GitHub Repo"
   - 选择相同的仓库

2. **配置前端服务**
   - 服务名称: `frontend`
   - Root Directory: 设置为 `frontend`
   - Dockerfile Path: `frontend/Dockerfile`

3. **设置环境变量**

   ```bash
   # 后端 API 地址
   VITE_API_URL=https://your-backend.railway.app
   ```

4. **更新前端 API 配置**

   修改 `frontend/src/api/index.ts` 或相关配置文件：

   ```typescript
   const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
   ```

5. **部署**
   - Railway 会自动构建和部署前端
   - 前端 URL: `https://your-frontend.railway.app`

#### 3. 配置 CORS

确保后端允许前端域名的跨域请求。

修改 `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 配置 CORS
origins = [
    "http://localhost:5173",  # 本地开发
    "https://your-frontend.railway.app",  # Railway 前端
    # 添加其他允许的域名
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 方案 B: 单一服务（Monorepo）

如果你想在一个服务中同时部署前后端：

1. **修改根目录 Dockerfile**

   创建 `Dockerfile.monorepo`:

   ```dockerfile
   # Stage 1: Build frontend
   FROM node:20-alpine AS frontend-builder
   WORKDIR /app/frontend
   COPY frontend/package*.json ./
   RUN npm ci
   COPY frontend/ ./
   RUN npm run build

   # Stage 2: Backend with frontend
   FROM python:3.12-slim
   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       ffmpeg git curl wget \
       && rm -rf /var/lib/apt/lists/*

   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy backend code
   COPY . .

   # Copy frontend build
   COPY --from=frontend-builder /app/frontend/dist ./static

   # Create directories
   RUN mkdir -p uploads outputs

   # Environment variables
   ENV PYTHONPATH=/app
   ENV PYTHONUNBUFFERED=1

   EXPOSE 8000

   # Start command
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **修改 FastAPI 以服务静态文件**

   在 `app/main.py` 中添加：

   ```python
   from fastapi.staticfiles import StaticFiles

   # 挂载静态文件
   app.mount("/", StaticFiles(directory="static", html=True), name="static")
   ```

3. **在 Railway 中配置**
   - Dockerfile Path: `Dockerfile.monorepo`
   - 只需要一个服务

## 部署后检查清单

- [ ] 后端健康检查: `https://your-backend.railway.app/health`
- [ ] 前端可访问: `https://your-frontend.railway.app`
- [ ] API 调用正常（检查浏览器控制台）
- [ ] CORS 配置正确
- [ ] 环境变量已设置
- [ ] 文件上传功能正常
- [ ] 视频生成功能正常

## 常见问题

### 1. 构建失败

**问题**: Python 依赖安装失败
**解决**:
- 检查 `requirements.txt` 中的包版本
- 某些包（如 torch）可能需要特定的安装命令
- 考虑使用更轻量的替代品

### 2. 内存不足

**问题**: Railway 免费套餐内存限制（512MB-1GB）
**解决**:
- 升级到 Pro 套餐
- 优化依赖（移除不必要的包）
- 使用外部服务处理视频（如 Replicate）

### 3. 文件存储

**问题**: 生成的视频在重启后丢失
**解决**:
- 使用 Railway Volumes（持久化存储）
- 或使用云存储（S3, Cloudinary 等）

### 4. 环境变量

**问题**: API keys 不生效
**解决**:
- 确保在 Railway Variables 中正确设置
- 重新部署服务以应用新的环境变量
- 检查变量名称是否与代码中一致

### 5. CORS 错误

**问题**: 前端无法调用后端 API
**解决**:
- 在后端 CORS 配置中添加前端域名
- 确保使用 HTTPS（Railway 自动提供）
- 检查浏览器控制台的具体错误信息

## 成本估算

### Railway 免费套餐
- $5 免费额度/月
- 512MB RAM
- 1GB 磁盘空间
- 适合开发和测试

### Railway Pro 套餐
- $20/月起
- 8GB RAM
- 100GB 磁盘空间
- 适合生产环境

### 优化建议
1. 使用外部 AI 服务（按需付费）
2. 视频存储使用 S3 或 Cloudinary
3. 数据库使用 Railway PostgreSQL 或外部服务
4. 考虑使用 CDN 加速静态资源

## 监控和日志

Railway 提供内置的监控和日志功能：

1. **查看日志**
   - 在 Railway 项目页面点击服务
   - 选择 "Logs" 标签
   - 实时查看应用日志

2. **监控指标**
   - CPU 使用率
   - 内存使用率
   - 网络流量
   - 请求响应时间

3. **设置告警**
   - 在 Settings 中配置告警规则
   - 通过 Email 或 Webhook 接收通知

## 下一步

1. 设置自定义域名
2. 配置 SSL 证书（Railway 自动提供）
3. 设置 CI/CD 自动部署
4. 配置数据库备份
5. 实施监控和告警

## 支持

如果遇到问题：
- Railway 文档: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- 项目 Issues: https://github.com/your-repo/issues
