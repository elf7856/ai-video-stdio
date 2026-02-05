# Railway 环境变量配置指南

## 必需的环境变量

### 1. Google API（核心功能）
```
GOOGLE_API_KEY=your_google_gemini_api_key
```
**用途：** Google Gemini LLM 和 Google Imagen 图像生成（默认提供商）

**获取方式：** https://makersuite.google.com/app/apikey

---

## 可选的环境变量

### 2. 图像生成服务（至少配置一个）

#### Stability AI
```
STABILITY_API_KEY=your_stability_api_key
```
**获取方式：** https://platform.stability.ai/

#### Replicate
```
REPLICATE_API_KEY=your_replicate_api_key
```
**获取方式：** https://replicate.com/account/api-tokens

#### Leonardo AI
```
LEONARDO_API_KEY=your_leonardo_api_key
```
**获取方式：** https://leonardo.ai/

#### Midjourney（如果使用）
```
MIDJOURNEY_API_KEY=your_midjourney_api_key
```

---

### 3. 视频生成服务（可选）

```
RUNWAY_API_KEY=your_runway_api_key
LUMA_API_KEY=your_luma_api_key
PIKA_API_KEY=your_pika_api_key
KLING_API_KEY=your_kling_api_key
```

---

### 4. 其他服务

#### ElevenLabs TTS（语音合成）
```
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```
**获取方式：** https://elevenlabs.io/

#### Pexels（素材库）
```
PEXELS_API_KEY=your_pexels_api_key
```
**获取方式：** https://www.pexels.com/api/

---

### 5. Google OAuth（YouTube 上传功能）
```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```
**获取方式：** https://console.cloud.google.com/apis/credentials

---

### 6. 数据库配置（Railway 自动提供）
```
DATABASE_URL=postgresql://user:password@host:port/database
```
**注意：** Railway 会自动设置此变量（如果你添加了 PostgreSQL 服务）

---

### 7. 存储配置（可选，使用 OSS/S3）
```
STORAGE_TYPE=oss
OSS_ACCESS_KEY_ID=your_oss_access_key_id
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name
OSS_REGION=cn-hangzhou
CDN_DOMAIN=https://cdn.example.com
```

---

### 8. 安全配置（生产环境必需）
```
SECRET_KEY=your-random-secret-key-change-this-in-production
DEBUG=false
```

**生成 SECRET_KEY：**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 9. 前端配置
```
FRONTEND_URL=https://your-frontend.vercel.app
BACKEND_URL=https://your-backend.railway.app
```

---

## Railway 配置步骤

### 方法 1：通过 Railway Dashboard

1. 进入你的 Railway 项目
2. 点击你的服务（backend）
3. 进入 **Variables** 标签
4. 点击 **New Variable**
5. 添加上述环境变量

### 方法 2：通过 Railway CLI

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 登录
railway login

# 链接项目
railway link

# 添加环境变量
railway variables set GOOGLE_API_KEY=your_key
railway variables set STABILITY_API_KEY=your_key
# ... 添加其他变量
```

### 方法 3：批量导入（推荐）

创建 `.env.railway` 文件：
```env
GOOGLE_API_KEY=your_google_api_key
STABILITY_API_KEY=your_stability_api_key
REPLICATE_API_KEY=your_replicate_api_key
SECRET_KEY=your_secret_key
DEBUG=false
```

然后使用 Railway CLI 导入：
```bash
railway variables set < .env.railway
```

---

## 最小配置（快速开始）

如果你只想快速测试，只需配置：

```
GOOGLE_API_KEY=your_google_gemini_api_key
```

这样就可以使用：
- ✅ Google Gemini LLM（脚本生成）
- ✅ Google Imagen（图像生成）
- ✅ Edge TTS（免费语音合成）

---

## 验证配置

部署后，访问以下端点检查配置：

```bash
# 健康检查
curl https://your-app.railway.app/health

# 检查可用的服务提供商
curl https://your-app.railway.app/api/providers
```

---

## 常见问题

### Q: 为什么应用启动失败？
A: 检查是否至少配置了 `GOOGLE_API_KEY`

### Q: 图像生成失败？
A: 确保至少配置了一个图像生成服务的 API key

### Q: 如何查看日志？
A: Railway Dashboard → 你的服务 → Logs 标签

### Q: 环境变量修改后需要重新部署吗？
A: 是的，修改环境变量后 Railway 会自动触发重新部署

---

## 安全提示

⚠️ **重要：**
- 不要将 API keys 提交到 Git 仓库
- 不要在代码中硬编码 API keys
- 定期轮换 API keys
- 为生产环境使用强随机的 SECRET_KEY
- 生产环境设置 `DEBUG=false`

---

## 成本估算

根据你配置的服务，预估每月成本：

| 服务 | 免费额度 | 付费价格 |
|------|---------|---------|
| Google Gemini | 60 请求/分钟 | $0.00025/1K tokens |
| Google Imagen | 有限免费 | $0.02/图像 |
| Stability AI | 无免费 | $0.002/图像 |
| Replicate | $5 免费额度 | 按使用计费 |
| ElevenLabs | 10,000 字符/月 | $5/月起 |
| Railway | $5 免费额度 | $0.000231/GB-hour |

**建议：** 从免费服务开始（Google Gemini + Imagen + Edge TTS）
