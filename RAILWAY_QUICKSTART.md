# Railway 快速部署指南

## 🚀 一键部署

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

## 📋 前置要求

1. Railway 账号（免费）: https://railway.app
2. GitHub 账号
3. 必需的 API Keys:
   - Google AI API Key (Gemini)
   - Replicate API Token (视频生成)
   - Pexels API Key (素材库，可选)

## 🎯 部署步骤

### 方法 1: 使用 Railway CLI（推荐）

```bash
# 1. 安装 Railway CLI
npm install -g @railway/cli

# 2. 登录
railway login

# 3. 初始化项目
railway init

# 4. 部署后端
railway up

# 5. 部署前端（在新终端）
cd frontend
railway up
```

### 方法 2: 使用 Railway Web 界面

#### 部署后端

1. 访问 https://railway.app
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择你的仓库
4. Railway 会自动检测 Dockerfile 并构建
5. 在 Variables 标签页添加环境变量（见下方）
6. 等待部署完成

#### 部署前端

1. 在同一个项目中点击 "New Service"
2. 选择相同的 GitHub 仓库
3. 设置 Root Directory 为 `frontend`
4. 添加环境变量: `VITE_API_URL=<后端URL>`
5. 等待部署完成

## 🔑 必需的环境变量

### 后端服务

```bash
# AI 服务
GOOGLE_API_KEY=your_google_api_key
REPLICATE_API_TOKEN=your_replicate_token

# 可选
OPENAI_API_KEY=your_openai_key
PEXELS_API_KEY=your_pexels_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### 前端服务

```bash
VITE_API_URL=https://your-backend.railway.app
```

## ✅ 验证部署

1. 后端健康检查: `https://your-backend.railway.app/health`
2. 前端访问: `https://your-frontend.railway.app`
3. 测试视频生成功能

## 📊 成本估算

- **免费套餐**: $5 免费额度/月（适合测试）
- **Pro 套餐**: $20/月起（适合生产）

## 🔧 故障排查

### 构建失败
- 检查 Dockerfile 语法
- 确保所有依赖在 requirements.txt 中

### 内存不足
- 升级到 Pro 套餐
- 优化依赖包

### CORS 错误
- 在后端添加前端域名到 CORS 配置
- 检查 `app/main.py` 中的 `allow_origins`

## 📚 详细文档

完整部署指南: [docs/RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md)

## 💡 提示

- Railway 会自动设置 `PORT` 环境变量
- 使用 Railway Volumes 持久化文件存储
- 配置自定义域名以获得更好的 URL
- 启用自动部署以实现 CI/CD

## 🆘 获取帮助

- Railway 文档: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- 项目 Issues: [GitHub Issues](https://github.com/your-repo/issues)
