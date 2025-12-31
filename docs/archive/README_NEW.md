# AI视频创作平台 - 长视频智能生成系统

## 项目概述

这是一个AI驱动的视频创作平台，专注于**让用户方便地生成长视频**。用户只需提供文字稿件，系统就能自动进行智能分镜、精确时长分配，并生成完整的视频项目。

## 核心功能

### 🎬 智能分镜系统
- **自动内容分析**：理解用户稿件结构和意图
- **智能分镜规划**：将长稿件分解为多个镜头（3-15秒每镜头）
- **专业prompt生成**：为每个镜头生成专业的AI视频提示词

### ⏱️ 精确时长控制
- **智能时长分配**：基于内容重要性自动分配镜头时长
- **节奏策略优化**：支持平衡、快节奏、慢节奏等多种策略
- **约束验证**：确保每个镜头时长在合理范围内（3-15秒）

### 📁 独立项目管理
- **标准化目录结构**：每个项目在`outputs/projects/[project_id]/`下独立管理
- **完整元数据记录**：保存分镜计划、时长分配、生成统计等信息
- **详细日志系统**：记录整个创作过程的每个步骤

### 📊 实时进度追踪
- **阶段化进度**：内容分析→分镜规划→时长分配→视频生成→完成
- **实时状态更新**：显示当前任务和预估剩余时间
- **WebSocket支持**：支持实时进度推送

### 🎯 质量保证
- **自动质量检测**：检查生成视频的技术质量和内容相关性
- **智能重试机制**：失败镜头自动重试，支持多种重试策略
- **一致性检查**：确保镜头间的视觉和风格一致性

## 系统架构

```
app/
├── models/                    # 数据模型
│   ├── project.py            # 项目模型
│   ├── shot.py               # 镜头模型
│   └── timing.py             # 时长规划模型
├── services/director/         # AI导演系统核心
│   ├── new_ai_director.py    # 主控制器
│   ├── project_manager.py    # 项目管理器
│   ├── timing_allocator.py   # 时长分配器
│   ├── progress_tracker.py   # 进度追踪器
│   ├── quality_controller.py # 质量控制器
│   └── simple_*.py          # 简化实现组件
├── api/                      # REST API接口
│   └── projects.py          # 项目管理API
└── services/video_generation/ # AI视频生成客户端
    ├── google_robust_client.py
    ├── runway_client.py
    └── openai_client.py
```

## 输出目录结构

```
outputs/
├── projects/                 # 用户项目目录
│   └── [project_id]/        # 单个项目目录
│       ├── raw_clips/       # AI生成的原始视频片段
│       │   ├── shot_001_8s.mp4
│       │   ├── shot_002_6s.mp4
│       │   └── shot_003_10s.mp4
│       ├── final_video_40s.mp4  # 最终合成视频（待实现）
│       ├── metadata/        # 项目元数据
│       │   ├── project_info.json
│       │   ├── shot_plan.json
│       │   └── timing_plan.json
│       ├── logs/           # 详细日志
│       └── thumbnails/     # 缩略图
└── temp/                   # 临时文件
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API密钥
在`.env`文件中配置：
```bash
GOOGLE_API_KEY=your_google_api_key_here
# 其他API密钥...
```

### 3. 运行演示
```bash
# 快速功能测试
python demo_complete_platform.py

# 运行测试套件
python test_ai_video_platform.py
```

### 4. 启动API服务
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API使用示例

### 创建视频项目
```bash
curl -X POST "http://localhost:8000/api/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "产品介绍视频",
    "script": "欢迎了解我们的全新智能产品...",
    "target_duration": 60,
    "style_preferences": {
      "visual_style": "modern_commercial",
      "mood": "positive_engaging"
    }
  }'
```

### 查询项目进度
```bash
curl "http://localhost:8000/api/projects/{project_id}/progress"
```

### 获取项目列表
```bash
curl "http://localhost:8000/api/projects/"
```

## 核心优势

### ✅ 用户友好
- 仅需提供文字稿件，系统自动处理
- 无需视频制作经验
- 智能化的创作流程

### ✅ 智能分镜
- AI自动将长稿件分解为合理镜头
- 基于内容语义的智能分析
- 专业级的镜头类型选择

### ✅ 精确控制
- 精确分配每个镜头时长（3-15秒）
- 智能节奏策略
- 总时长精确匹配用户需求

### ✅ 文件管理
- 独立项目目录，避免文件混乱
- 完整的元数据记录
- 便于项目管理和追溯

### ✅ 质量保证
- 自动质量检测和重试
- 进度可视化
- 详细的日志记录

## 技术特点

- **模块化设计**：各组件独立，易于扩展和维护
- **异步处理**：支持并发生成，提升效率
- **错误恢复**：完善的异常处理和重试机制
- **实时反馈**：WebSocket支持实时进度更新
- **标准化**：统一的API接口和数据模型

## 开发状态

- ✅ **核心功能完成**：项目管理、分镜规划、时长分配
- ✅ **API接口完成**：RESTful API和WebSocket支持
- ✅ **测试覆盖**：完整的测试套件和演示脚本
- ⏳ **视频合成**：待完善视频片段合成功能
- ⏳ **前端界面**：可选的Web用户界面

## 扩展性

系统设计支持：
- 更多AI视频生成API的接入
- 自定义分镜策略
- 高级质量控制算法
- 视频后处理和特效
- 批量项目处理

---

## 详细文档

- 📖 [项目目标详解](AI_VIDEO_CREATOR_GOALS.md)
- 🧪 [测试用例](test_ai_video_platform.py)
- 🎬 [完整演示](demo_complete_platform.py)

---

*这个项目专注于解决"让用户方便地生成长视频"这一核心需求，通过AI智能分镜和精确时长控制，为用户提供专业级的视频创作体验。*