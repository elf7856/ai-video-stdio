# API接口参考

本平台所有功能均通过标准RESTful API提供。

- **API版本**: v1
- **基础URL**: `/api/v1`
- **认证方式**: JWT (Authorization: Bearer <token>)

---

## 通用规范

### 统一响应格式

#### 成功
```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "code": 200
}
```

#### 失败
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述"
    }
}
```

### 分页
分页信息包含在响应的`pagination`字段中，包含`page`, `limit`, `total`, `pages`等。

---

## 核心API端点

### 1. AI导演系统 (`/ai-director`)

#### `POST /ai-director/create`
使用AI导演从脚本创建完整的长视频。这是平台的核心功能。

**请求体**:
```json
{
  "title": "AI技术介绍",
  "script": "介绍人工智能的基本概念...",
  "target_duration": 120,
  "style_preferences": {
    "visual_style": "modern",
    "mood": "professional"
  },
  "enable_narration": true,
  "narration_voice": "xiaoxiao"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_123456",
    "status": "queued",
    "estimated_time": 300
  }
}
```

#### `GET /ai-director/progress/{project_id}`
查询视频生成任务的实时进度。

---

### 2. 视频处理 (`/videos`)

#### `POST /videos/process-url`
从URL下载视频并进行初步分析。

**请求体**:
```json
{
  "url": "https://www.youtube.com/watch?v=example",
  "auto_analyze": true
}
```

#### `POST /videos/{video_id}/summary`
为指定视频生成摘要。

**请求体**:
```json
{
  "summary_type": "text" // "text", "audio", "video"
}
```

#### `POST /videos/{video_id}/edit`
使用自然语言指令编辑视频。

**请求体**:
```json
{
  "instruction": "在视频第10秒处插入一张关于“未来城市”的图片"
}
```

---

### 3. AI图像生成 (`/images`)

#### `POST /images/generate`
生成一张AI图像。

**请求体**:
```json
{
  "prompt": "一个宇航员在火星上喝咖啡，数字艺术",
  "provider": "dalle", // "dalle", "stability", "local"等
  "style": "realistic",
  "size": "1920x1080"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "image_path": "/outputs/images/generated_image.png"
  }
}
```

---

### 4. TTS语音合成 (`/tts`)

#### `POST /tts/generate`
将文本转换为语音。

**请求体**:
```json
{
  "text": "欢迎使用AI视频创作平台。",
  "voice_id": "xiaoxiao" // "xiaoxiao", "yunxi"等
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "audio_path": "/outputs/tts/generated_audio.mp3"
  }
}
```

#### `GET /tts/voices`
获取所有可用的TTS发音人列表。

---

### 5. 项目管理 (`/projects`)

#### `GET /projects`
获取所有项目的列表（支持分页）。

#### `POST /projects`
创建一个新的空项目。

#### `GET /projects/{project_id}`
获取特定项目的详细信息，包括其下的所有资源（视频片段、元数据等）。

---

*注：这是一个根据现有多个文档综合整理的API参考，可能与代码的最新实现有细微差别。完整的API文档请在服务启动后访问 `/docs`。*
