# 多平台一键上传功能

## 🎯 功能概述

多平台一键上传功能让创作者可以将生成的视频同时发布到多个视频平台，无需手动上传多次。

### 支持的平台

- ✅ **YouTube** - 通过Google OAuth 2.0认证
- ✅ **哔哩哔哩(Bilibili)** - 通过Cookie认证
- ✅ **抖音(Douyin)** - 通过Web自动化
- 🔄 **快手(Kuaishou)** - 待开发
- 🔄 **小红书(Xiaohongshu)** - 待开发
- 🔄 **微信视频号(WeChat Channels)** - 待开发
- 🔄 **微博(Weibo)** - 待开发

---

## 📋 架构设计

### 1. 基础架构

```
app/services/upload/
├── base.py                    # 基础类和接口定义
├── manager.py                 # 上传管理器
├── youtube_uploader.py        # YouTube上传器
├── bilibili_uploader.py       # B站上传器
├── douyin_uploader.py         # 抖音上传器
└── ...                        # 其他平台上传器
```

### 2. 核心组件

#### PlatformUploader (基类)
所有平台上传器的抽象基类，定义了统一接口：
- `authenticate()` - 认证
- `upload_video()` - 上传视频
- `check_upload_status()` - 检查状态
- `delete_video()` - 删除视频

#### UploadManager (管理器)
协调多平台上传，提供：
- 并发上传到多个平台
- 任务管理和状态跟踪
- 失败重试机制
- 平台配置管理

---

## 🚀 快速开始

### 后端配置

#### 1. 安装依赖

```bash
pip install google-api-python-client google-auth-oauthlib httpx playwright
playwright install chromium  # 仅Douyin需要
```

#### 2. 配置环境变量

在 `.env` 文件中添加：

```env
# YouTube OAuth
GOOGLE_CLIENT_ID=your_youtube_client_id
GOOGLE_CLIENT_SECRET=your_youtube_client_secret

# 其他平台的配置...
```

#### 3. 启动后端

```bash
python -m uvicorn app.main:app --reload
```

### 前端配置

#### 1. 安装依赖

```bash
cd frontend
npm install
```

#### 2. 启动前端

```bash
npm run dev
```

#### 3. 访问上传页面

访问: http://localhost:5173/upload

---

## 📖 使用指南

### 方式1: 通过API直接调用

#### 步骤1: 配置平台

**YouTube (OAuth)**:
```bash
# 1. 获取OAuth授权URL
curl "http://localhost:8000/api/upload/oauth/youtube/authorize-url?redirect_uri=http://localhost:5173/oauth/callback"

# 2. 访问返回的URL进行授权
# 3. 获取授权码后调用callback
curl -X POST "http://localhost:8000/api/upload/oauth/youtube/callback?code=YOUR_CODE&redirect_uri=http://localhost:5173/oauth/callback"
```

**Bilibili (Cookie)**:
```bash
curl -X POST http://localhost:8000/api/upload/configure-platform \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "bilibili",
    "enabled": true,
    "cookies": {
      "SESSDATA": "your_sessdata",
      "bili_jct": "your_bili_jct",
      "DedeUserID": "your_dedeuserid"
    }
  }'
```

**获取B站Cookie的方法**:
1. 登录 https://www.bilibili.com
2. 打开浏览器开发者工具 (F12)
3. 切换到 Application/Storage -> Cookies
4. 复制 `SESSDATA`, `bili_jct`, `DedeUserID` 的值

#### 步骤2: 上传视频

```bash
curl -X POST http://localhost:8000/api/upload/upload \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "./outputs/videos/my_video.mp4",
    "title": "我的第一个视频",
    "description": "这是一个测试视频",
    "tags": ["测试", "AI", "视频创作"],
    "platforms": ["youtube", "bilibili"],
    "privacy": "public"
  }'
```

响应:
```json
{
  "success": true,
  "task_id": "upload_20231207_123456_xxx",
  "message": "Upload started for 2 platforms"
}
```

#### 步骤3: 查询上传状态

```bash
curl http://localhost:8000/api/upload/task/upload_20231207_123456_xxx
```

响应:
```json
{
  "task_id": "upload_20231207_123456_xxx",
  "status": "completed",
  "platforms": ["youtube", "bilibili"],
  "results": [
    {
      "platform": "youtube",
      "status": "success",
      "video_id": "dQw4w9WgXcQ",
      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "uploaded_at": "2023-12-07T12:34:56"
    },
    {
      "platform": "bilibili",
      "status": "success",
      "video_id": "BV1xx411c7XZ",
      "video_url": "https://www.bilibili.com/video/BV1xx411c7XZ",
      "uploaded_at": "2023-12-07T12:35:20"
    }
  ],
  "created_at": "2023-12-07T12:30:00",
  "completed_at": "2023-12-07T12:35:30"
}
```

### 方式2: 通过前端界面

#### 步骤1: 配置平台
1. 访问 http://localhost:5173/upload
2. 点击右上角的设置图标
3. 按照提示配置各平台

#### 步骤2: 上传视频
1. 填写视频文件路径 (如 `./outputs/videos/veo_xxx.mp4`)
2. 填写标题、描述、标签
3. 选择要发布的平台 (可多选)
4. 点击"发布到 X 个平台"按钮

#### 步骤3: 查看进度
- 上传过程中会实时显示各平台的上传进度
- 上传完成后可以看到每个平台的视频链接
- 失败的上传可以点击重试按钮

---

## 🔧 API端点参考

### 平台配置

#### POST /api/upload/configure-platform
配置平台认证信息

**请求体**:
```json
{
  "platform": "youtube",
  "enabled": true,
  "access_token": "...",
  "refresh_token": "...",
  "client_id": "...",
  "client_secret": "..."
}
```

#### GET /api/upload/configured-platforms
获取已配置的平台列表

**响应**:
```json
{
  "platforms": ["youtube", "bilibili"],
  "count": 2
}
```

### 视频上传

#### POST /api/upload/upload
上传视频到多个平台

**请求体**:
```json
{
  "video_path": "./outputs/videos/video.mp4",
  "title": "视频标题",
  "description": "视频描述",
  "tags": ["tag1", "tag2"],
  "category": "education",
  "thumbnail_path": "./path/to/thumbnail.jpg",
  "privacy": "public",
  "platforms": ["youtube", "bilibili", "douyin"]
}
```

**响应**:
```json
{
  "success": true,
  "task_id": "upload_xxx",
  "message": "Upload started for 3 platforms"
}
```

### 任务管理

#### GET /api/upload/task/{task_id}
获取任务状态

#### GET /api/upload/tasks
获取所有任务

#### POST /api/upload/task/{task_id}/retry
重试失败的上传

#### DELETE /api/upload/video
删除视频

**参数**:
- `video_id`: 视频ID
- `platforms`: 平台列表

### 统计信息

#### GET /api/upload/stats
获取上传统计信息

---

## 🎨 前端集成

### 1. 导入API客户端

```typescript
import { uploadApi, Platform } from '../api/upload';
```

### 2. 上传视频

```typescript
const handleUpload = async () => {
  const { task_id } = await uploadApi.uploadVideo({
    video_path: './outputs/videos/video.mp4',
    title: '我的视频',
    description: '视频描述',
    tags: ['AI', '视频'],
    platforms: ['youtube', 'bilibili']
  });

  // 轮询状态
  await uploadApi.pollTaskStatus(task_id, (task) => {
    console.log('Progress:', task.status);
    // 更新UI
  });
};
```

### 3. 配置平台

```typescript
const configurePlatform = async () => {
  await uploadApi.configurePlatform({
    platform: 'youtube',
    enabled: true,
    access_token: 'xxx',
    refresh_token: 'xxx',
    client_id: 'xxx',
    client_secret: 'xxx'
  });
};
```

---

## ⚠️ 注意事项

### YouTube上传

1. **API配额限制**
   - 每天有10,000个配额单位
   - 一次视频上传消耗约1600个单位
   - 合理安排上传计划

2. **OAuth认证**
   - 需要在Google Cloud Console创建OAuth 2.0客户端
   - 授权范围: `https://www.googleapis.com/auth/youtube.upload`

3. **视频处理时间**
   - 上传后YouTube需要时间处理视频
   - 不同清晰度处理时间不同

### Bilibili上传

1. **Cookie有效期**
   - Cookie可能会过期，需要定期更新
   - 建议每隔一段时间重新获取

2. **上传限制**
   - 单个视频最大4GB
   - 需要实名认证和手机绑定

3. **审核机制**
   - 视频上传后需要审核
   - 审核时间通常在几分钟到几小时

### 抖音上传

1. **Web自动化**
   - 使用Playwright进行自动化上传
   - 需要保持浏览器窗口打开
   - 上传过程不能中断

2. **账号安全**
   - 频繁上传可能触发风控
   - 建议控制上传频率

---

## 🐛 故障排除

### 问题1: YouTube认证失败

**错误**: `Authentication failed`

**解决方案**:
1. 检查OAuth配置是否正确
2. 确认client_id和client_secret有效
3. 重新获取access_token

### 问题2: Bilibili上传404

**错误**: `Upload URL not found`

**解决方案**:
1. 更新Cookie (可能已过期)
2. 检查账号是否有上传权限
3. 确认账号已实名认证

### 问题3: 上传超时

**错误**: `Upload timeout`

**解决方案**:
1. 检查网络连接
2. 增加超时时间参数
3. 尝试重试功能

---

## 📊 性能优化

### 1. 并发上传
- 默认并发上传到所有选择的平台
- 可以通过配置调整并发数

### 2. 断点续传
- YouTube支持分块上传
- Bilibili支持分片上传
- 上传失败可以从断点继续

### 3. 任务队列
- 使用后台任务避免阻塞API
- 支持批量上传任务

---

## 🔐 安全建议

1. **敏感信息存储**
   - 不要在代码中硬编码API密钥
   - 使用环境变量或密钥管理服务
   - Cookie和Token应该加密存储

2. **权限控制**
   - 限制上传API的访问权限
   - 实现用户认证和授权
   - 记录操作日志

3. **输入验证**
   - 验证视频文件路径
   - 检查文件大小和格式
   - 过滤恶意内容

---

## 📈 未来计划

- [ ] 添加快手平台支持
- [ ] 添加小红书平台支持
- [ ] 添加微信视频号支持
- [ ] 实现定时发布功能
- [ ] 添加视频数据分析
- [ ] 支持批量上传
- [ ] 添加上传模板功能
- [ ] 实现跨平台内容同步

---

## 📝 更新日志

### v1.0.0 (2023-12-07)
- ✅ 初始版本发布
- ✅ 支持YouTube上传
- ✅ 支持Bilibili上传
- ✅ 支持Douyin上传
- ✅ 实现上传管理器
- ✅ 添加前端UI界面
- ✅ 实现OAuth认证流程

---

## 🤝 贡献指南

欢迎贡献代码！如果你想添加新平台支持：

1. 在 `app/services/upload/` 创建新的上传器类
2. 继承 `PlatformUploader` 基类
3. 实现所有抽象方法
4. 在 `manager.py` 中注册新平台
5. 添加对应的测试用例
6. 更新文档

---

**✅ 多平台上传功能已完全实现！**

如有问题，请查看文档或提交Issue。
