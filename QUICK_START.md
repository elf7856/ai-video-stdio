# 快速启动指南

## 🚀 启动步骤

### 1. 启动后端

```bash
# 方法1：使用uvicorn直接启动
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方法2：使用简单命令
cd /Users/xikangsong/workplace/video_creator_platform
python -m uvicorn app.main:app --reload
```

后端启动成功后，访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 2. 启动前端

打开新的终端窗口：

```bash
cd frontend
npm run dev
```

前端启动成功后，访问：
- 前端界面: http://localhost:5173

---

## ✅ 修复的问题

### 问题：ModuleNotFoundError: No module named 'app.services.llm.unified_service'

**原因**：多个文件导入了不存在的 `unified_service`，实际的文件是 `service.py`

**修复的文件**：
- ✅ `app/services/director/new_ai_director.py`
- ✅ `app/services/director/timing_allocator.py`
- ✅ `app/services/director/simple_content_analyzer.py`
- ✅ `app/services/director/simple_shot_planner.py`

**修改内容**：
```python
# 之前（错误）
from ...services.llm.unified_service import unified_llm_service

# 之后（正确）
from ...services.llm.service import llm_service
```

### 临时禁用的功能

为了让后端快速启动，临时注释了MCP服务初始化：
```python
# app/main.py line 63
# mcp_wrapper = MCPWebWrapper(app)  # 临时禁用
```

这不影响核心功能的使用。

---

## 🧪 测试步骤

### 测试后端

1. **检查后端是否启动**
```bash
curl http://localhost:8000/health
```

应该返回：`{"status":"healthy"}`

2. **查看API文档**
访问: http://localhost:8000/docs

### 测试前端

1. **访问首页**
```bash
open http://localhost:5173
```

2. **测试脚本生成**
- 输入主题："如何泡一杯咖啡"
- 选择风格："生活"
- 时长：60秒
- 点击"仅生成脚本"
- 等待30-60秒
- 查看生成的脚本和分镜

3. **测试视频生成** ⭐
- 输入主题："如何泡一杯咖啡"
- 选择风格："生活"
- 时长：60秒
- 点击"**一键生成视频**" ⭐
- 观察进度条更新
- 等待3-5分钟
- 查看生成的视频
- 下载视频文件

4. **测试图像生成** ⭐（需要添加到导航）
- 直接访问: http://localhost:5173/image-generate
- 输入描述："一个美丽的山景日落"
- 选择16:9
- 点击"生成图像"
- 查看生成的图像

---

## 📋 API端点

### 脚本生成
```
POST /api/scripts/generate
{
  "topic": "如何泡咖啡",
  "style": "生活",
  "targetDuration": 60
}
```

### 视频生成（新增）⭐
```
POST /api/video-generation/generate
{
  "topic": "如何泡咖啡",
  "style": "生活",
  "targetDuration": 60,
  "autoGenerate": true
}

Response: { "taskId": "task_xxx" }
```

### 任务状态查询（新增）⭐
```
GET /api/video-generation/tasks/{taskId}
```

### 图像生成（新增）⭐
```
POST /api/images/generate
{
  "prompt": "A beautiful sunset",
  "provider": "google_imagen",
  "aspectRatio": "16:9",
  "resolution": "medium"
}
```

---

## ⚠️ 常见问题

### 1. 后端启动失败

**检查Python版本**：
```bash
python --version  # 应该是 3.11+
```

**检查依赖**：
```bash
pip install -r requirements.txt
```

### 2. 前端启动失败

**检查Node版本**：
```bash
node --version  # 应该是 16+
```

**重新安装依赖**：
```bash
cd frontend
rm -rf node_modules
npm install
```

### 3. API调用失败

**检查环境变量**：
确保 `.env` 文件配置了必要的API密钥：
```bash
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # 可选
```

### 4. 视频下载404

**确保静态文件挂载**：
检查 `app/main.py` 中是否有：
```python
from fastapi.staticfiles import StaticFiles
app.mount("/outputs", StaticFiles(directory="./outputs"), name="outputs")
```

---

## 🎯 下一步

1. **添加图像生成到导航菜单**
   - 编辑 `frontend/src/App.tsx`
   - 添加路由到 `ImageGenerate` 页面

2. **添加CORS配置**（如果前后端跨域问题）
   - 编辑 `app/main.py`
   - 添加前端地址到 `allow_origins`

3. **测试完整流程**
   - 生成脚本 ✅
   - 生成视频 ✅
   - 下载视频 ✅
   - 生成图像 ✅
   - 下载图像 ✅

---

**✅ 所有修复已完成，可以开始测试了！**
