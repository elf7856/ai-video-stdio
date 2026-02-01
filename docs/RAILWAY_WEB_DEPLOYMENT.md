# Railway Web 界面部署详细步骤

## 🎯 准备工作

1. 确保代码已推送到 GitHub
2. 准备好必需的 API Keys：
   - Google API Key (Gemini)
   - Replicate API Token
   - 其他可选的 API keys

## 📝 部署步骤

### 第一步：部署后端服务

1. **登录 Railway**
   - 访问 https://railway.app
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击右上角 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 授权 Railway 访问你的 GitHub（如果是第一次）

3. **选择仓库**
   - 在列表中找到 `elf7856/ai-video-stdio`
   - 点击选择

4. **配置后端服务**
   - Railway 会自动检测到根目录的 `Dockerfile`
   - 服务名称会自动生成，可以改为 `backend` 或 `api`
   - 点击 "Deploy Now"

5. **等待构建**
   - 可以在 "Deployments" 标签查看构建日志
   - 首次构建需要 5-10 分钟（安装依赖）

6. **设置环境变量**
   - 点击服务卡片
   - 选择 "Variables" 标签
   - 点击 "New Variable"
   - 添加以下变量：

   ```
   GOOGLE_API_KEY=你的Google API密钥
   REPLICATE_API_TOKEN=你的Replicate令牌
   OPENAI_API_KEY=你的OpenAI密钥（可选）
   PEXELS_API_KEY=你的Pexels密钥（可选）
   ELEVENLABS_API_KEY=你的ElevenLabs密钥（可选）
   ```

7. **获取后端 URL**
   - 在 "Settings" → "Networking" 中
   - 点击 "Generate Domain"
   - 复制生成的 URL，例如：`https://your-backend.up.railway.app`

8. **验证后端**
   - 访问 `https://your-backend.up.railway.app/health`
   - 应该看到健康检查响应

### 第二步：部署前端服务

1. **添加新服务**
   - 在同一个 Railway 项目页面
   - 点击 "New" → "GitHub Repo"
   - 选择相同的仓库 `elf7856/ai-video-stdio`

2. **配置前端服务**
   - 点击新创建的服务
   - 进入 "Settings" → "Source"
   - 设置以下配置：
     - **Root Directory**: `frontend`
     - **Dockerfile Path**: `frontend/Dockerfile`
   - 服务名称改为 `frontend`

3. **设置环境变量**
   - 在 "Variables" 标签
   - 添加：
   ```
   VITE_API_URL=https://your-backend.up.railway.app
   ```
   （使用第一步获取的后端 URL）

4. **触发部署**
   - 点击 "Deploy" 按钮
   - 或者修改配置后会自动重新部署

5. **获取前端 URL**
   - 在 "Settings" → "Networking" 中
   - 点击 "Generate Domain"
   - 复制生成的 URL，例如：`https://your-frontend.up.railway.app`

6. **验证前端**
   - 访问前端 URL
   - 应该看到你的应用界面

### 第三步：配置 CORS（重要！）

前端和后端在不同域名，需要配置 CORS：

1. **更新后端 CORS 配置**

   在本地修改 `app/main.py`，找到 CORS 配置部分：

   ```python
   origins = [
       "http://localhost:5173",  # 本地开发
       "https://your-frontend.up.railway.app",  # 添加你的前端 URL
   ]
   ```

2. **推送代码**
   ```bash
   git add app/main.py
   git commit -m "feat: add Railway frontend URL to CORS"
   git push origin dev
   ```

3. **Railway 会自动重新部署后端**

### 第四步：测试完整功能

1. 访问前端 URL
2. 尝试创建新项目
3. 测试视频生成功能
4. 检查浏览器控制台是否有错误

## 🔍 查看日志和监控

### 查看部署日志
1. 点击服务卡片
2. 选择 "Deployments" 标签
3. 点击最新的部署
4. 查看构建和运行日志

### 查看运行时日志
1. 点击服务卡片
2. 选择 "Logs" 标签
3. 实时查看应用日志

### 监控资源使用
1. 点击服务卡片
2. 选择 "Metrics" 标签
3. 查看 CPU、内存、网络使用情况

## ⚙️ 高级配置（可选）

### 添加自定义域名
1. 在 "Settings" → "Networking"
2. 点击 "Custom Domain"
3. 输入你的域名
4. 按照提示配置 DNS

### 添加持久化存储
1. 在项目页面点击 "New" → "Volume"
2. 设置挂载路径：
   - `/app/uploads` - 上传文件
   - `/app/outputs` - 生成的视频
3. 在服务的 "Settings" → "Volumes" 中连接

### 配置环境
1. 在 "Settings" → "Environment"
2. 可以创建多个环境（production, staging）
3. 每个环境可以有不同的变量

## 🐛 常见问题

### 构建失败
- 查看 "Deployments" 日志
- 检查 Dockerfile 语法
- 确保 requirements.txt 正确

### 前端无法连接后端
- 检查 CORS 配置
- 确认 VITE_API_URL 正确
- 查看浏览器控制台错误

### 内存不足
- 免费套餐 512MB 可能不够
- 升级到 Pro 套餐（$20/月）
- 或优化依赖包

### 环境变量不生效
- 确保变量名正确
- 重新部署服务以应用变量
- 检查代码中的变量读取逻辑

## 💰 成本控制

### 免费套餐
- $5 免费额度/月
- 适合开发和测试
- 可能需要优化以保持在限额内

### 优化建议
1. 使用外部服务处理视频（Replicate）
2. 使用云存储（S3, Cloudinary）
3. 优化 Docker 镜像大小
4. 使用 CDN 加速静态资源

## 📞 获取帮助

- Railway 文档: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- 项目 Issues: https://github.com/elf7856/ai-video-stdio/issues

## ✅ 部署检查清单

- [ ] 后端服务部署成功
- [ ] 前端服务部署成功
- [ ] 所有环境变量已设置
- [ ] 后端健康检查通过
- [ ] 前端可以访问
- [ ] CORS 配置正确
- [ ] API 调用正常
- [ ] 视频生成功能测试通过
- [ ] 日志没有错误
- [ ] 资源使用在合理范围内
