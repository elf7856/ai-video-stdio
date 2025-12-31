# AI视频创作平台 RESTful API 设计文档

## 📋 目录
- [API概述](#api概述)
- [认证和授权](#认证和授权)
- [通用规范](#通用规范)
- [用户管理API](#用户管理api)
- [项目管理API](#项目管理api)
- [AI视频生成API](#ai视频生成api)
- [视频编辑API](#视频编辑api)
- [TTS和音频API](#tts和音频api)
- [文件管理API](#文件管理api)
- [作品库API](#作品库api)
- [模板库API](#模板库api)
- [支付订阅API](#支付订阅api)
- [分析统计API](#分析统计api)
- [系统管理API](#系统管理api)

---

## API概述

### 基础信息
- **API版本**: v1
- **基础URL**: `https://your-domain.com/api/v1`
- **数据格式**: JSON
- **编码**: UTF-8
- **协议**: HTTPS

### 设计原则
- RESTful设计风格
- 统一的请求响应格式
- 清晰的错误处理机制
- 完整的权限控制
- 详细的API文档

---

## 认证和授权

### JWT Token认证
```http
Authorization: Bearer <your_jwt_token>
```

### API Key认证 (可选)
```http
X-API-Key: <your_api_key>
```

---

## 通用规范

### 统一响应格式

#### 成功响应
```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "code": 200,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 错误响应
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": "详细错误信息"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 分页格式
```json
{
    "data": [],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 100,
        "pages": 5,
        "has_next": true,
        "has_prev": false
    }
}
```

### HTTP状态码
- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 权限不足
- `404` - 资源不存在
- `429` - 请求频率限制
- `500` - 服务器内部错误

---

## 用户管理API

### 认证相关

#### 用户注册
```http
POST /api/v1/auth/register
```

**请求体**:
```json
{
    "username": "user123",
    "email": "user@example.com",
    "password": "password123",
    "confirm_password": "password123"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "user_id": "user_123456",
        "username": "user123",
        "email": "user@example.com",
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

#### 用户登录
```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
        "expires_in": 3600,
        "user": {
            "id": "user_123456",
            "username": "user123",
            "email": "user@example.com",
            "subscription_plan": "free"
        }
    }
}
```

#### 用户登出
```http
POST /api/v1/auth/logout
```

#### 刷新Token
```http
POST /api/v1/auth/refresh
```

**请求体**:
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### 忘记密码
```http
POST /api/v1/auth/forgot-password
```

#### 重置密码
```http
POST /api/v1/auth/reset-password
```

### 用户信息管理

#### 获取用户信息
```http
GET /api/v1/users/profile
```

#### 更新用户信息
```http
PUT /api/v1/users/profile
```

#### 获取使用统计
```http
GET /api/v1/users/usage
```

**响应**:
```json
{
    "success": true,
    "data": {
        "monthly_video_count": 15,
        "monthly_limit": 50,
        "storage_used": "2.5GB",
        "storage_limit": "10GB",
        "api_calls_used": 150,
        "api_calls_limit": 1000
    }
}
```

#### 获取订阅信息
```http
GET /api/v1/users/subscription
```

---

## 项目管理API

#### 获取项目列表
```http
GET /api/v1/projects?page=1&limit=20&status=active
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 20)
- `status`: 项目状态 (active, archived, draft)
- `search`: 搜索关键词

#### 创建新项目
```http
POST /api/v1/projects
```

**请求体**:
```json
{
    "title": "我的AI视频项目",
    "description": "项目描述",
    "category": "education",
    "tags": ["AI", "教学", "演示"]
}
```

#### 获取项目详情
```http
GET /api/v1/projects/{project_id}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "id": "proj_123456",
        "title": "我的AI视频项目",
        "description": "项目描述",
        "status": "in_progress",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T12:30:00Z",
        "settings": {
            "target_duration": 120,
            "style_preferences": {
                "visual_style": "realistic",
                "color_tone": "warm",
                "mood": "professional"
            }
        },
        "files": [
            {
                "id": "file_001",
                "type": "video",
                "name": "intro.mp4",
                "size": 1024000,
                "url": "/api/v1/files/file_001"
            }
        ]
    }
}
```

#### 更新项目
```http
PUT /api/v1/projects/{project_id}
```

#### 删除项目
```http
DELETE /api/v1/projects/{project_id}
```

#### 复制项目
```http
POST /api/v1/projects/{project_id}/duplicate
```

#### 分享项目
```http
POST /api/v1/projects/{project_id}/share
```

#### 获取版本历史
```http
GET /api/v1/projects/{project_id}/versions
```

---

## AI视频生成API

### 视频生成

#### AI生成视频
```http
POST /api/v1/ai/generate/video
```

**请求体**:
```json
{
    "project_id": "proj_123456",
    "title": "我的视频项目",
    "script": "创建一个关于AI技术的教学视频，首先介绍AI的基本概念...",
    "style_preferences": {
        "visual_style": "realistic",
        "color_tone": "warm",
        "mood": "professional"
    },
    "target_duration": 120,
    "api_provider": "google_veo",
    "quality": "1080p",
    "segments": [
        {
            "text": "介绍AI的基本概念",
            "duration": 30,
            "style": "educational"
        },
        {
            "text": "AI的应用场景展示",
            "duration": 60,
            "style": "demonstration"
        },
        {
            "text": "总结和展望",
            "duration": 30,
            "style": "conclusion"
        }
    ]
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "task_id": "task_123456",
        "project_id": "proj_789",
        "estimated_time": 300,
        "status": "queued",
        "segments_count": 3,
        "progress_url": "/api/v1/ai/generate/task_123456"
    },
    "message": "视频生成任务已启动"
}
```

#### 获取生成进度
```http
GET /api/v1/ai/generate/{task_id}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "task_id": "task_123456",
        "status": "generating",
        "progress": 65,
        "current_step": "generating_segment_2",
        "message": "正在生成第2个视频片段...",
        "completed_segments": 1,
        "total_segments": 3,
        "estimated_remaining": 120,
        "segments": [
            {
                "id": "segment_1",
                "status": "completed",
                "file_url": "/api/v1/files/segment_1.mp4"
            },
            {
                "id": "segment_2", 
                "status": "generating",
                "progress": 30
            },
            {
                "id": "segment_3",
                "status": "pending"
            }
        ]
    }
}
```

#### 取消生成任务
```http
POST /api/v1/ai/generate/{task_id}/cancel
```

### 脚本和分镜

#### 生成脚本
```http
POST /api/v1/ai/script/generate
```

**请求体**:
```json
{
    "topic": "人工智能基础教学",
    "duration": 120,
    "style": "educational",
    "target_audience": "初学者",
    "key_points": [
        "AI的定义",
        "机器学习基础",
        "应用场景",
        "未来发展"
    ]
}
```

#### 生成分镜
```http
POST /api/v1/ai/storyboard/create
```

#### 优化脚本
```http
POST /api/v1/ai/script/optimize
```

### AI模型管理

#### 获取可用AI模型
```http
GET /api/v1/ai/models
```

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "id": "google_veo",
            "name": "Google Veo",
            "description": "谷歌最新视频生成模型",
            "max_duration": 300,
            "quality": ["720p", "1080p", "4K"],
            "cost_per_second": 0.1,
            "available": true
        },
        {
            "id": "runway_gen3",
            "name": "Runway Gen-3",
            "description": "Runway第三代视频生成模型", 
            "max_duration": 180,
            "quality": ["720p", "1080p"],
            "cost_per_second": 0.15,
            "available": true
        }
    ]
}
```

#### 获取可用风格
```http
GET /api/v1/ai/styles
```

---

## 视频编辑API

### 基础编辑

#### 视频裁剪
```http
POST /api/v1/video/cut
```

**请求体**:
```json
{
    "video_id": "video_123",
    "operations": [
        {
            "type": "cut",
            "start_time": 10.5,
            "end_time": 45.2,
            "name": "intro_segment"
        },
        {
            "type": "cut",
            "start_time": 60.0, 
            "end_time": 90.5,
            "name": "main_content"
        }
    ],
    "output_format": "mp4",
    "quality": "high"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "task_id": "edit_456",
        "clips": [
            {
                "clip_id": "clip_001",
                "name": "intro_segment",
                "duration": 34.7,
                "file_url": "/api/v1/files/clip_001.mp4",
                "thumbnail": "/api/v1/files/clip_001_thumb.jpg"
            },
            {
                "clip_id": "clip_002",
                "name": "main_content",
                "duration": 30.5,
                "file_url": "/api/v1/files/clip_002.mp4",
                "thumbnail": "/api/v1/files/clip_002_thumb.jpg"
            }
        ]
    }
}
```

#### 视频合并
```http
POST /api/v1/video/merge
```

**请求体**:
```json
{
    "clips": [
        {
            "video_id": "video_001",
            "start_time": 0,
            "end_time": 30
        },
        {
            "video_id": "video_002", 
            "start_time": 10,
            "end_time": 40
        }
    ],
    "transitions": [
        {
            "type": "fade",
            "duration": 1.0
        }
    ],
    "output_settings": {
        "format": "mp4",
        "quality": "1080p",
        "frame_rate": 30
    }
}
```

#### 视频分割
```http
POST /api/v1/video/split
```

#### 调整分辨率
```http
POST /api/v1/video/resize
```

### 高级编辑

#### 添加滤镜
```http
POST /api/v1/video/filter
```

**请求体**:
```json
{
    "video_id": "video_123",
    "filters": [
        {
            "type": "brightness",
            "value": 1.2,
            "start_time": 0,
            "end_time": 30
        },
        {
            "type": "blur",
            "radius": 2,
            "start_time": 10,
            "end_time": 20
        }
    ]
}
```

#### 添加转场
```http
POST /api/v1/video/transition
```

#### 添加覆盖层
```http
POST /api/v1/video/overlay
```

#### 调整播放速度
```http
POST /api/v1/video/speed
```

### 音频处理

#### 添加音频
```http
POST /api/v1/video/audio/add
```

#### 移除音频
```http
POST /api/v1/video/audio/remove
```

#### 调整音量
```http
POST /api/v1/video/audio/adjust
```

---

## TTS和音频API

### TTS语音合成

#### 文字转语音
```http
POST /api/v1/tts/synthesize
```

**请求体**:
```json
{
    "text": "欢迎来到AI视频创作平台，让我们开始创造精彩的内容吧！",
    "voice": "zh-CN-XiaoxiaoNeural",
    "speed": 1.0,
    "pitch": 0,
    "volume": 100,
    "output_format": "mp3",
    "quality": "high",
    "ssml_enabled": false
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "audio_id": "audio_789",
        "duration": 5.2,
        "file_url": "/api/v1/files/audio_789.mp3",
        "file_size": 83200,
        "sample_rate": 44100,
        "bit_rate": 128
    }
}
```

#### 获取可用语音
```http
GET /api/v1/tts/voices?language=zh-CN
```

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "voice_id": "zh-CN-XiaoxiaoNeural",
            "name": "晓晓",
            "gender": "Female",
            "language": "zh-CN",
            "sample_url": "/api/v1/tts/samples/xiaoxiao.mp3",
            "description": "温和亲切的女声"
        },
        {
            "voice_id": "zh-CN-YunyangNeural", 
            "name": "云扬",
            "gender": "Male",
            "language": "zh-CN",
            "sample_url": "/api/v1/tts/samples/yunyang.mp3",
            "description": "磁性稳重的男声"
        }
    ]
}
```

#### 预览语音
```http
POST /api/v1/tts/preview
```

### 音频处理

#### 上传音频
```http
POST /api/v1/audio/upload
```

#### 音频处理
```http
POST /api/v1/audio/process
```

#### 音频混合
```http
POST /api/v1/audio/mix
```

#### 获取音频信息
```http
GET /api/v1/audio/{audio_id}
```

---

## 文件管理API

### 文件操作

#### 文件上传
```http
POST /api/v1/files/upload
```

**请求** (multipart/form-data):
```
file: <binary_data>
category: video|audio|image|document
project_id: proj_123456
description: 文件描述
```

**响应**:
```json
{
    "success": true,
    "data": {
        "file_id": "file_123456",
        "original_name": "my_video.mp4",
        "file_name": "file_123456.mp4",
        "file_size": 10485760,
        "mime_type": "video/mp4",
        "category": "video",
        "upload_time": "2024-01-15T10:30:00Z",
        "file_url": "/api/v1/files/file_123456",
        "thumbnail_url": "/api/v1/files/file_123456/thumbnail",
        "metadata": {
            "duration": 120.5,
            "resolution": "1920x1080",
            "frame_rate": 30,
            "bit_rate": 5000
        }
    }
}
```

#### 文件下载
```http
GET /api/v1/files/{file_id}
```

#### 删除文件
```http
DELETE /api/v1/files/{file_id}
```

#### 文件信息
```http
GET /api/v1/files/{file_id}/info
```

### 文件管理

#### 文件列表
```http
GET /api/v1/files?category=video&page=1&limit=20
```

**查询参数**:
- `category`: 文件类型 (video, audio, image, document)
- `project_id`: 项目ID
- `search`: 搜索关键词
- `sort`: 排序方式 (created_at, file_size, name)
- `order`: 排序顺序 (asc, desc)

#### 文件整理
```http
POST /api/v1/files/organize
```

#### 文件搜索
```http
GET /api/v1/files/search?q=关键词&category=video
```

#### 批量删除
```http
POST /api/v1/files/batch-delete
```

**请求体**:
```json
{
    "file_ids": ["file_001", "file_002", "file_003"]
}
```

---

## 作品库API

### 作品管理

#### 获取作品列表
```http
GET /api/v1/works?category=education&page=1&limit=20
```

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "id": "work_123456",
            "title": "AI基础教学视频",
            "description": "详细介绍人工智能基础概念",
            "category": "education",
            "tags": ["AI", "教学", "基础"],
            "duration": 120,
            "thumbnail": "/api/v1/files/work_123456_thumb.jpg",
            "video_url": "/api/v1/files/work_123456.mp4",
            "created_at": "2024-01-15T10:30:00Z",
            "views": 1250,
            "likes": 89,
            "status": "published"
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 156,
        "pages": 8
    }
}
```

#### 作品详情
```http
GET /api/v1/works/{work_id}
```

#### 保存作品
```http
POST /api/v1/works
```

**请求体**:
```json
{
    "title": "我的AI视频作品",
    "description": "作品描述",
    "category": "education",
    "tags": ["AI", "教学"],
    "video_file_id": "file_123456",
    "thumbnail_file_id": "file_789",
    "status": "draft",
    "metadata": {
        "script": "原始脚本内容",
        "generation_settings": {
            "style": "realistic",
            "duration": 120
        }
    }
}
```

#### 更新作品
```http
PUT /api/v1/works/{work_id}
```

#### 删除作品
```http
DELETE /api/v1/works/{work_id}
```

### 检索和分类

#### 搜索作品
```http
GET /api/v1/works/search?q=AI教学&category=education&sort=created_at
```

#### 获取分类
```http
GET /api/v1/works/categories
```

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "id": "education",
            "name": "教育",
            "description": "教学和培训相关视频",
            "count": 245
        },
        {
            "id": "marketing",
            "name": "营销",
            "description": "产品宣传和营销视频",
            "count": 189
        }
    ]
}
```

#### 添加标签
```http
POST /api/v1/works/{work_id}/tag
```

#### 获取标签列表
```http
GET /api/v1/works/tags
```

---

## 模板库API

### 模板管理

#### 获取模板列表
```http
GET /api/v1/templates?category=education&featured=true
```

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "id": "template_001",
            "name": "教育视频模板",
            "description": "适合制作教学和培训视频",
            "category": "education",
            "thumbnail": "/api/v1/files/template_001_thumb.jpg",
            "preview_video": "/api/v1/files/template_001_preview.mp4",
            "duration_range": [60, 300],
            "difficulty": "beginner",
            "tags": ["教学", "演示", "专业"],
            "usage_count": 1250,
            "rating": 4.8,
            "is_featured": true,
            "is_premium": false
        }
    ]
}
```

#### 模板详情
```http
GET /api/v1/templates/{template_id}
```

#### 使用模板
```http
POST /api/v1/templates/use
```

**请求体**:
```json
{
    "template_id": "template_001",
    "project_title": "我的新项目",
    "customizations": {
        "script": "自定义脚本内容",
        "style_preferences": {
            "color_tone": "warm",
            "mood": "professional"
        }
    }
}
```

#### 保存为模板
```http
POST /api/v1/templates/save
```

### 模板分类

#### 模板分类
```http
GET /api/v1/templates/categories
```

#### 推荐模板
```http
GET /api/v1/templates/featured
```

#### 最近使用
```http
GET /api/v1/templates/recent
```

---

## 支付订阅API

### 订阅管理

#### 获取套餐列表
```http
GET /api/v1/subscription/plans
```

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "id": "free",
            "name": "免费版",
            "price": 0,
            "currency": "CNY",
            "billing_cycle": "monthly",
            "features": {
                "video_generation_limit": 5,
                "storage_limit": "1GB",
                "max_duration": 60,
                "quality": "720p",
                "watermark": true
            },
            "description": "适合个人用户体验"
        },
        {
            "id": "pro",
            "name": "专业版",
            "price": 99,
            "currency": "CNY", 
            "billing_cycle": "monthly",
            "features": {
                "video_generation_limit": 100,
                "storage_limit": "50GB",
                "max_duration": 300,
                "quality": "4K",
                "watermark": false,
                "priority_processing": true,
                "advanced_editing": true
            },
            "description": "适合专业创作者"
        }
    ]
}
```

#### 订阅套餐
```http
POST /api/v1/subscription/subscribe
```

#### 更新订阅
```http
PUT /api/v1/subscription/update
```

#### 取消订阅
```http
POST /api/v1/subscription/cancel
```

### 支付处理

#### 创建支付订单
```http
POST /api/v1/payment/create
```

**请求体**:
```json
{
    "plan_id": "pro",
    "billing_cycle": "monthly",
    "payment_method": "wechat",
    "return_url": "https://yourapp.com/payment/success"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "order_id": "order_123456",
        "amount": 99.00,
        "currency": "CNY",
        "payment_url": "https://pay.wechat.com/...",
        "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        "expires_at": "2024-01-15T11:30:00Z"
    }
}
```

#### 支付回调
```http
POST /api/v1/payment/callback
```

#### 支付历史
```http
GET /api/v1/payment/history
```

#### 申请退款
```http
POST /api/v1/payment/refund
```

---

## 分析统计API

### 使用统计

#### 使用量统计
```http
GET /api/v1/analytics/usage?period=month&start_date=2024-01-01
```

**响应**:
```json
{
    "success": true,
    "data": {
        "period": "2024-01",
        "video_generation": {
            "count": 25,
            "total_duration": 1800,
            "success_rate": 0.96
        },
        "storage": {
            "used": "8.5GB",
            "limit": "50GB",
            "usage_rate": 0.17
        },
        "api_calls": {
            "total": 450,
            "by_endpoint": {
                "/api/v1/ai/generate/video": 25,
                "/api/v1/video/cut": 15,
                "/api/v1/tts/synthesize": 30
            }
        }
    }
}
```

#### 性能统计
```http
GET /api/v1/analytics/performance
```

#### 热门内容
```http
GET /api/v1/analytics/popular
```

#### 趋势分析
```http
GET /api/v1/analytics/trends
```

---

## 系统管理API

### 系统状态

#### 健康检查
```http
GET /api/v1/system/health
```

**响应**:
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "ai_service": "healthy",
            "file_storage": "healthy"
        },
        "version": "1.0.0",
        "uptime": 86400
    }
}
```

#### 系统状态
```http
GET /api/v1/system/status
```

#### 版本信息
```http
GET /api/v1/system/version
```

### 配置管理

#### 获取系统配置
```http
GET /api/v1/config/settings
```

#### 更新配置
```http
PUT /api/v1/config/settings
```

---

## 错误代码

### 通用错误
- `INVALID_REQUEST` - 请求参数无效
- `UNAUTHORIZED` - 未授权访问
- `FORBIDDEN` - 权限不足
- `NOT_FOUND` - 资源不存在
- `RATE_LIMIT_EXCEEDED` - 请求频率超限
- `INTERNAL_ERROR` - 服务器内部错误

### 业务错误
- `USER_NOT_EXISTS` - 用户不存在
- `INVALID_CREDENTIALS` - 登录凭证无效
- `EMAIL_ALREADY_EXISTS` - 邮箱已存在
- `PROJECT_NOT_FOUND` - 项目不存在
- `FILE_TOO_LARGE` - 文件过大
- `UNSUPPORTED_FORMAT` - 不支持的文件格式
- `INSUFFICIENT_QUOTA` - 配额不足
- `GENERATION_FAILED` - 视频生成失败
- `PROCESSING_FAILED` - 视频处理失败
- `PAYMENT_FAILED` - 支付失败

---

## 附录

### 请求限制
- API请求频率: 100次/分钟 (根据用户套餐调整)
- 文件上传大小: 500MB
- 视频最大时长: 300秒 (根据用户套餐调整)

### 支持的文件格式
- **视频**: MP4, AVI, MOV, MKV
- **音频**: MP3, WAV, AAC, M4A
- **图片**: JPG, PNG, GIF, BMP

### Webhook事件
```http
POST /your-webhook-url
```

**事件类型**:
- `video.generation.completed` - 视频生成完成
- `video.generation.failed` - 视频生成失败
- `payment.completed` - 支付完成
- `subscription.updated` - 订阅更新

**Webhook载荷**:
```json
{
    "event": "video.generation.completed",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "task_id": "task_123456",
        "project_id": "proj_789",
        "video_url": "/api/v1/files/final_video.mp4"
    }
}
```

---

*文档版本: v1.0*  
*最后更新: 2024-01-15*