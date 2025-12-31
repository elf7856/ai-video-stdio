# API端点修复说明

## 🔧 已修复的问题

### 问题：视频生成404错误

**原因**：前端API路径与后端不匹配

**后端实际端点**：
```
POST /api/video-generation/create-task   # 创建任务
GET  /api/video-generation/task/{task_id} # 获取任务状态
```

**前端之前调用**（错误）：
```
POST /api/video-generation/generate       # ❌ 不存在
GET  /api/video-generation/tasks/{taskId}  # ❌ 不存在
```

**已修复为**：
```typescript
// frontend/src/api/videos.ts
createTask: '/api/video-generation/create-task'  ✅
getTaskStatus: '/api/video-generation/task/{taskId}'  ✅
```

---

## 📋 完整的API端点列表

### 1. 脚本生成 ✅
```
POST /api/scripts/generate
```
**请求**：
```json
{
  "topic": "如何泡咖啡",
  "style": "生活",
  "targetDuration": 60,
  "additionalRequirements": "简洁明了"
}
```

**响应**：
```json
{
  "success": true,
  "script": "完整脚本内容...",
  "shots": [
    {
      "sequence": 1,
      "prompt": "镜头描述...",
      "duration": 8.0,
      "shotType": "特写"
    }
  ],
  "totalDuration": 60
}
```

---

### 2. 视频生成 ✅ (已修复)

#### 创建任务
```
POST /api/video-generation/create-task
```
**请求**：
```json
{
  "topic": "如何泡咖啡",
  "style": "生活",
  "targetDuration": 60,
  "additionalRequirements": "简洁明了",
  "autoGenerate": true
}
```

**响应**：
```json
{
  "taskId": "task_20231207_123456_xxx",
  "status": "pending",
  "progress": 0.0,
  "script": null,
  "shots": null,
  "generatedVideos": [],
  "error": null,
  "createdAt": "2023-12-07T12:34:56",
  "completedAt": null
}
```

#### 获取任务状态
```
GET /api/video-generation/task/{task_id}
```

**响应**：
```json
{
  "taskId": "task_xxx",
  "status": "completed",
  "progress": 100.0,
  "script": "脚本内容...",
  "shots": [...],
  "generatedVideos": [
    {
      "sequence": 1,
      "shotType": "特写",
      "status": "success",
      "videoPath": "./outputs/videos/veo_xxx.mp4",
      "duration": 8.0,
      "cost": 5.00,
      "fileSize": 12345678,
      "generationTime": 45.2
    }
  ],
  "error": null,
  "createdAt": "2023-12-07T12:34:56",
  "completedAt": "2023-12-07T12:39:30"
}
```

#### 任务状态说明
- `pending` - 等待中
- `generating_script` - 生成脚本中
- `generating_videos` - 生成视频中
- `completed` - 已完成
- `failed` - 失败

---

### 3. 图像生成 ✅

#### 生成图像
```
POST /api/images/generate
```
**请求**：
```json
{
  "prompt": "A beautiful sunset over mountains",
  "provider": "google_imagen",
  "aspectRatio": "16:9",
  "resolution": "medium",
  "negativePrompt": "blurry, low quality"
}
```

**响应**：
```json
{
  "success": true,
  "imagePath": "./outputs/images/gemini_imagen_1234567890.png",
  "provider": "google_imagen",
  "error": null
}
```

#### 获取可用提供商
```
GET /api/images/providers
```

**响应**：
```json
{
  "providers": [
    "google_imagen",
    "dalle",
    "stability",
    "replicate",
    "leonardo",
    "local"
  ]
}
```

---

## 🧪 测试命令

### 测试脚本生成
```bash
curl -X POST http://localhost:8000/api/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "如何泡咖啡",
    "style": "生活",
    "targetDuration": 60
  }'
```

### 测试视频生成
```bash
# 1. 创建任务
TASK_ID=$(curl -X POST http://localhost:8000/api/video-generation/create-task \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "如何泡咖啡",
    "style": "生活",
    "targetDuration": 60,
    "autoGenerate": true
  }' | jq -r '.taskId')

echo "任务ID: $TASK_ID"

# 2. 查询状态
curl http://localhost:8000/api/video-generation/task/$TASK_ID
```

### 测试图像生成
```bash
curl -X POST http://localhost:8000/api/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset",
    "provider": "google_imagen",
    "aspectRatio": "16:9",
    "resolution": "medium"
  }'
```

---

## 🔍 调试技巧

### 1. 查看后端日志
启动后端时会显示所有可用的路由：
```bash
python -m uvicorn app.main:app --reload
```

### 2. 查看API文档
访问自动生成的文档：
```
http://localhost:8000/docs
```

### 3. 检查网络请求
在浏览器开发者工具中：
- 打开 Network 标签
- 点击"一键生成视频"
- 查看请求URL和响应

### 4. 前端控制台日志
前端代码已添加了详细日志：
```javascript
console.log('发送请求:', request);
console.log('收到响应:', response);
console.log('视频生成任务已创建:', taskId);
console.log('任务进度更新:', task);
```

---

## ✅ 修复验证清单

完成这些步骤确认修复成功：

- [x] 前端API客户端路径已修正
- [ ] 后端服务器正常启动
- [ ] 前端开发服务器正常启动
- [ ] 访问 http://localhost:8000/docs 看到API文档
- [ ] 在Swagger文档中测试 `/api/video-generation/create-task`
- [ ] 在前端界面点击"一键生成视频"
- [ ] 浏览器控制台无404错误
- [ ] 进度条正常更新
- [ ] 视频生成成功并可下载

---

## 🚀 现在可以测试了

1. **重启前端开发服务器**（如果正在运行）：
```bash
cd frontend
# Ctrl+C 停止
npm run dev
```

2. **清除浏览器缓存**（重要！）：
- Chrome: Ctrl/Cmd + Shift + R
- 或者打开开发者工具 → Network → Disable cache

3. **测试流程**：
- 输入主题："如何泡一杯咖啡"
- 点击"一键生成视频"
- 打开开发者工具Console查看日志
- 观察进度条更新
- 等待3-5分钟
- 查看生成的视频列表

---

**✅ API路径已修复，现在应该可以正常工作了！**

如果还有问题，请查看：
1. 浏览器控制台的错误信息
2. 后端终端的日志输出
3. Network标签中的具体请求URL
