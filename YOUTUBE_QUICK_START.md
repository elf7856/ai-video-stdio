# YouTube上传 - 5分钟快速开始

## 🚀 快速步骤

### 1. 安装依赖 (30秒)

#### 方法1: 使用 uv（推荐，速度快10倍）
```bash
# 如果还没安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv pip install -r requirements.txt
```

#### 方法2: 使用传统 pip
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

> 💡 **推荐使用 uv**！详见 [INSTALL_WITH_UV.md](./INSTALL_WITH_UV.md)

### 2. 获取Google OAuth凭据 (3分钟)

1. 访问 https://console.cloud.google.com
2. 创建新项目（或选择现有项目）
3. 启用"YouTube Data API v3"
4. 创建OAuth 2.0凭据（桌面应用）
5. 下载JSON文件，重命名为 `client_secret.json`
6. 放在项目根目录

### 3. 运行认证测试 (1分钟)

```bash
python test_youtube_auth.py
```

这会：
- 打开浏览器让你登录Google
- 生成 `token.json` 文件
- 显示你的YouTube频道信息
- 输出配置命令

### 4. 测试上传视频 (1分钟)

```bash
python test_youtube_upload.py
```

这会自动上传 `./outputs/videos/` 目录中的第一个视频。

---

## 📋 详细步骤（如果上面不够清楚）

### 步骤1: Google Cloud配置

#### 1.1 创建项目
- 访问 https://console.cloud.google.com
- 点击顶部项目下拉菜单 -> "新建项目"
- 项目名称: `Video Creator Platform`
- 点击"创建"

#### 1.2 启用YouTube API
- 左侧菜单: "API和服务" -> "库"
- 搜索: `YouTube Data API v3`
- 点击进入 -> "启用"

#### 1.3 配置OAuth同意屏幕
- 左侧菜单: "API和服务" -> "OAuth同意屏幕"
- 用户类型: 选择"外部"
- 填写:
  - 应用名称: `Video Creator Platform`
  - 用户支持电子邮件: 你的Gmail
  - 开发者联系信息: 你的Gmail
- 点击"保存并继续"（其他默认即可）
- 测试用户: 添加你的Gmail账号

#### 1.4 创建OAuth凭据
- 左侧菜单: "API和服务" -> "凭据"
- 点击"创建凭据" -> "OAuth 2.0 客户端ID"
- 应用类型: "桌面应用"
- 名称: `Video Uploader`
- 点击"创建"
- 下载JSON文件

#### 1.5 保存凭据文件
```bash
# 将下载的文件重命名并移动到项目根目录
mv ~/Downloads/client_secret_*.json ./client_secret.json
```

### 步骤2: 认证和测试

#### 2.1 首次认证
```bash
python test_youtube_auth.py
```

**会发生什么**:
1. 终端显示: `🌐 即将打开浏览器进行授权...`
2. 浏览器自动打开Google登录页面
3. 选择你的Google账号
4. 点击"允许"授权应用
5. 看到"认证成功"页面
6. 回到终端，看到你的频道信息

**输出示例**:
```
✅ 频道信息:
  📛 频道名: 我的频道
  👥 订阅数: 100
  🎬 视频数: 5
```

#### 2.2 测试上传
```bash
python test_youtube_upload.py
```

**会发生什么**:
1. 查找 `./outputs/videos/` 目录中的视频
2. 上传第一个找到的视频
3. 显示上传进度（每10%更新一次）
4. 上传完成后显示视频链接

**输出示例**:
```
⏫ 正在上传...
  进度: 10%
  进度: 20%
  ...
  进度: 100%

✅ 上传完成!

🎬 视频信息:
  视频ID: dQw4w9WgXcQ
  视频链接: https://www.youtube.com/watch?v=dQw4w9WgXcQ
  隐私状态: private
```

### 步骤3: 查看你的视频

1. 访问 https://studio.youtube.com
2. 在左侧菜单点击"内容"
3. 你会看到刚上传的视频（状态为"私密"）
4. 可以修改标题、描述、隐私设置等

---

## 🔧 集成到系统

### 方式1: 使用API

#### 配置平台
```bash
# 从token.json获取凭证信息
cat token.json

# 配置YouTube平台
curl -X POST http://localhost:8000/api/upload/configure-platform \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "youtube",
    "enabled": true,
    "access_token": "从token.json复制token字段",
    "refresh_token": "从token.json复制refresh_token字段",
    "client_id": "从token.json复制client_id字段",
    "client_secret": "从token.json复制client_secret字段"
  }'
```

#### 上传视频
```bash
curl -X POST http://localhost:8000/api/upload/upload \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "./outputs/videos/your_video.mp4",
    "title": "我的视频标题",
    "description": "视频描述",
    "tags": ["AI", "技术"],
    "privacy": "public",
    "platforms": ["youtube"]
  }'
```

### 方式2: 使用前端界面

1. 启动后端: `python -m uvicorn app.main:app --reload`
2. 启动前端: `cd frontend && npm run dev`
3. 访问: http://localhost:5173/upload
4. 填写视频信息并上传

---

## ⚠️ 常见问题

### Q: 浏览器没有自动打开怎么办？

**A**: 手动复制终端显示的URL到浏览器打开。

### Q: 提示"Access blocked"

**A**:
1. 确保已配置OAuth同意屏幕
2. 将你的Gmail添加到测试用户列表
3. 应用状态应该是"测试"而非"生产"

### Q: 提示"quotaExceeded"

**A**:
- 每天只有10,000配额单位
- 一次上传消耗约1,600单位
- 可上传约6个视频/天
- 等到第二天或申请增加配额

### Q: token.json过期了怎么办？

**A**: 不用担心！refresh_token会自动刷新access_token。如果真的失效了，删除token.json重新运行认证。

---

## 📊 文件说明

运行后会生成这些文件：

```
video_creator_platform/
├── client_secret.json  # Google OAuth凭据（不要提交到git）
├── token.json          # 访问令牌（不要提交到git）
├── test_youtube_auth.py    # 认证测试脚本
└── test_youtube_upload.py  # 上传测试脚本
```

**重要**: 将这些文件添加到 `.gitignore`:
```
client_secret.json
token.json
```

---

## 🎯 成功标志

如果你看到以下输出，说明一切正常：

```
✅ 所有测试通过!
✅ 上传完成!
🎬 视频链接: https://www.youtube.com/watch?v=...
```

---

## 📚 更多信息

- 完整文档: [YOUTUBE_UPLOAD_GUIDE.md](./YOUTUBE_UPLOAD_GUIDE.md)
- API文档: http://localhost:8000/docs
- YouTube API: https://developers.google.com/youtube/v3

---

**🎉 现在开始上传你的视频到YouTube吧！**
