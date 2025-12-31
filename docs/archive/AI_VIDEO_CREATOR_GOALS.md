# AI视频创作平台 - 项目目标详解

## 核心目标

**让用户能够方便地生成长视频，通过AI智能分镜和自动化生成流程，将用户的文字稿件转换为专业的视频内容。**

---

## 详细功能目标

### 1. 用户输入处理
- **输入内容类型**：用户提供的文字稿件/脚本
- **输入格式**：自然语言描述，可以是：
  - 故事脚本
  - 教学内容
  - 产品介绍
  - 解说词
  - 营销文案
- **输入长度**：支持长篇内容（目标生成30秒-300秒视频）

### 2. 智能分镜理解
- **自动分析**：
  - 理解用户稿件的内容结构
  - 识别关键场景和转折点
  - 提取重要视觉元素
  - 分析情感基调和风格需求

- **分镜规划**：
  - 将长稿件分解为多个独立镜头
  - 为每个镜头生成专业的prompt
  - 确定镜头类型（特写、全景、过渡等）
  - 设置镜头风格参数

### 3. 智能时长分配
- **时长规划**：
  - 根据内容重要性分配镜头时长
  - 确保总时长符合用户预期
  - 平衡各镜头的时间占比
  - 考虑转场和节奏需求

- **时长配置**：
  - 每个镜头：3-15秒（可调）
  - 总视频：30-300秒（用户指定）
  - 自动优化时长分配
  - 支持手动调整

### 4. AI视频生成
- **多API支持**：
  - Google Gemini Veo
  - OpenAI Sora（待接入）
  - Runway Gen-4
  - 其他主流生成API

- **生成策略**：
  - 并发生成多个镜头
  - 智能API选择（根据内容类型）
  - 失败重试机制
  - 质量检测和筛选

### 5. 文件管理系统
- **输出目录结构**：
  ```
  outputs/
  ├── projects/
  │   ├── [project_id]/
  │   │   ├── raw_clips/          # 原始生成片段
  │   │   │   ├── shot_001.mp4
  │   │   │   ├── shot_002.mp4
  │   │   │   └── ...
  │   │   ├── final_video.mp4     # 最终合成视频
  │   │   ├── project_info.json   # 项目元数据
  │   │   ├── shot_plan.json      # 分镜计划
  │   │   └── generation_log.txt  # 生成日志
  │   └── [project_id_2]/
  └── temp/                       # 临时文件
  ```

- **文件命名规范**：
  - 项目ID：`proj_YYYYMMDD_HHMMSS_[random]`
  - 镜头文件：`shot_[序号]_[时长]s.mp4`
  - 最终视频：`final_[总时长]s_[timestamp].mp4`

---

## 核心工作流程

### 阶段1：内容理解
1. **用户输入接收**：
   - 接收用户的文字稿件
   - 解析内容结构和意图
   - 识别关键词和主题

2. **智能分析**：
   - 使用LLM分析内容语义
   - 提取视觉化元素
   - 确定视频风格和基调

### 阶段2：分镜规划
1. **内容分段**：
   - 将稿件分解为逻辑段落
   - 识别场景转换点
   - 确定镜头边界

2. **镜头设计**：
   - 为每个镜头生成详细prompt
   - 设定视觉风格参数
   - 分配时长和优先级

3. **计划优化**：
   - 检查镜头连贯性
   - 优化转场效果
   - 调整时长分配

### 阶段3：视频生成
1. **并发生成**：
   - 同时调用多个AI API
   - 生成各个镜头片段
   - 实时监控进度

2. **质量控制**：
   - 检测生成质量
   - 处理失败重试
   - 记录生成统计

### 阶段4：结果管理
1. **文件组织**：
   - 创建独立项目目录
   - 保存所有生成片段
   - 记录项目元数据

2. **用户反馈**：
   - 提供生成进度
   - 显示项目结构
   - 支持结果预览

---

## 项目结构规划

### 整体架构设计

```
video_creator_platform/
├── 📁 app/                    # 核心应用层
│   ├── 🌐 api/               # REST API接口层
│   │   ├── videos.py         # 视频生成API
│   │   └── projects.py       # 项目管理API (新增)
│   ├── 📊 models/            # 数据模型定义
│   │   ├── video.py          # 基础视频模型
│   │   ├── project.py        # 项目模型 (新增)
│   │   └── shot.py           # 镜头模型 (新增)
│   ├── ⚙️ services/          # 业务逻辑服务层
│   │   ├── 🎬 director/      # AI导演系统 (核心)
│   │   │   ├── content_analyzer.py    # 内容分析器
│   │   │   ├── shot_planner.py       # 分镜规划器  
│   │   │   ├── timing_allocator.py   # 时长分配器 (新增)
│   │   │   ├── api_orchestrator.py   # API协调器
│   │   │   └── project_manager.py    # 项目管理器 (新增)
│   │   ├── 🎥 video_generation/      # AI视频生成客户端
│   │   │   ├── google_robust_client.py
│   │   │   ├── runway_client.py
│   │   │   └── openai_client.py
│   │   ├── 🧠 llm/           # LLM服务集成
│   │   └── 📈 analysis/      # 内容分析服务
│   ├── 🔧 core/             # 核心配置
│   └── 🛠️ utils/            # 工具函数
├── 🖥️ frontend/             # 用户界面
│   ├── src/views/           # 页面视图
│   └── src/components/      # UI组件
├── 📤 outputs/              # 输出目录 (核心重点)
│   ├── projects/           # 用户项目目录
│   │   └── [project_id]/   # 单个项目目录
│   │       ├── raw_clips/          # 原始AI生成片段
│   │       │   ├── shot_001_8s.mp4
│   │       │   ├── shot_002_6s.mp4
│   │       │   └── shot_003_10s.mp4
│   │       ├── final_video_120s.mp4   # 最终合成视频
│   │       ├── metadata/           # 项目元数据
│   │       │   ├── project_info.json
│   │       │   ├── shot_plan.json
│   │       │   └── generation_stats.json
│   │       └── logs/               # 生成日志
│   │           ├── content_analysis.log
│   │           ├── shot_planning.log
│   │           └── generation.log
│   └── temp/               # 临时工作文件
├── 📥 inputs/              # 用户输入文件
├── 📚 docs/                # 项目文档
├── 🧪 tests/               # 测试文件
└── 📋 examples/            # 使用示例
```

### 核心服务架构详解

#### 1. AI导演系统 (app/services/director/)
```python
director/
├── __init__.py
├── ai_director.py              # 主控制器
├── content_analyzer.py         # 内容分析器
│   ├── parse_script()         # 解析用户稿件
│   ├── extract_scenes()       # 提取场景信息
│   └── analyze_emotion()      # 分析情感基调
├── shot_planner.py            # 分镜规划器  
│   ├── segment_content()      # 内容分段
│   ├── design_shots()         # 镜头设计
│   └── optimize_flow()        # 优化连贯性
├── timing_allocator.py        # 时长分配器 (新增)
│   ├── calculate_durations()  # 计算镜头时长
│   ├── balance_timing()       # 平衡时间分配
│   └── adjust_pacing()        # 调整节奏
├── api_orchestrator.py        # API协调器
│   ├── select_api()          # 智能API选择
│   ├── manage_concurrency()  # 并发管理
│   └── handle_failures()     # 失败处理
└── project_manager.py         # 项目管理器 (新增)
    ├── create_project()      # 创建项目目录
    ├── manage_files()        # 文件组织管理
    └── track_progress()      # 进度追踪
```

#### 2. 数据模型设计 (app/models/)
```python
# project.py - 项目模型
class Project:
    id: str                    # 项目唯一标识
    title: str                 # 项目标题
    script: str                # 用户原始稿件
    target_duration: int       # 目标总时长(秒)
    created_at: datetime       # 创建时间
    status: ProjectStatus      # 项目状态
    output_dir: str           # 输出目录路径
    
# shot.py - 镜头模型  
class Shot:
    id: str                   # 镜头ID
    sequence: int             # 镜头序号
    prompt: str              # 生成prompt
    duration: float          # 镜头时长
    shot_type: ShotType      # 镜头类型
    style_params: dict       # 样式参数
    api_provider: str        # 使用的API
    file_path: Optional[str] # 生成文件路径
    
# timing_plan.py - 时长规划模型
class TimingPlan:
    total_duration: float    # 总时长
    shots: List[ShotTiming] # 各镜头时长分配
    pacing_strategy: str    # 节奏策略
    transition_time: float  # 转场时间
```

#### 3. 输出目录标准化
```
outputs/projects/[project_id]/
├── 📹 raw_clips/              # AI生成的原始片段
│   ├── shot_001_8s.mp4       # 镜头1，8秒时长
│   ├── shot_002_6s.mp4       # 镜头2，6秒时长
│   ├── shot_003_10s.mp4      # 镜头3，10秒时长
│   ├── shot_004_5s.mp4       # 镜头4，5秒时长
│   └── shot_005_11s.mp4      # 镜头5，11秒时长
├── 🎬 final_video_40s.mp4     # 最终合成的40秒视频
├── 🖼️ thumbnails/             # 缩略图
│   ├── shot_001_thumb.jpg
│   └── final_thumb.jpg
├── 📊 metadata/               # 项目元数据
│   ├── project_info.json     # 项目基本信息
│   │   {
│   │     "id": "proj_20250813_143022_abc123",
│   │     "title": "产品介绍视频",
│   │     "script": "用户原始稿件...",
│   │     "target_duration": 40,
│   │     "actual_duration": 40.2,
│   │     "shots_count": 5,
│   │     "created_at": "2025-08-13T14:30:22Z",
│   │     "status": "completed"
│   │   }
│   ├── shot_plan.json        # 详细分镜计划
│   │   {
│   │     "shots": [
│   │       {
│   │         "id": "shot_001",
│   │         "sequence": 1,
│   │         "prompt": "产品开箱特写镜头...",
│   │         "duration": 8.0,
│   │         "type": "close_up",
│   │         "api_provider": "google_veo"
│   │       }
│   │     ]
│   │   }
│   └── generation_stats.json # 生成统计信息
│       {
│         "total_cost": 2.45,
│         "generation_time": 680,
│         "success_rate": 0.85,
│         "api_usage": {
│           "google_veo": 3,
│           "runway": 2
│         }
│       }
└── 📋 logs/                   # 详细日志
    ├── content_analysis.log   # 内容分析日志
    ├── shot_planning.log      # 分镜规划日志
    ├── generation.log         # 视频生成日志
    └── project_timeline.log   # 项目时间线
```

### 关键组件设计

#### 1. 项目管理器 (ProjectManager)
```python
class ProjectManager:
    def create_project(self, script: str, duration: int) -> Project:
        """创建新项目，建立目录结构"""
        
    def setup_directories(self, project_id: str) -> str:
        """创建标准化的项目目录结构"""
        
    def save_metadata(self, project: Project, metadata: dict):
        """保存项目元数据到JSON文件"""
        
    def track_progress(self, project_id: str, stage: str, progress: float):
        """追踪项目进度，更新状态"""
        
    def cleanup_temp_files(self, project_id: str):
        """清理临时文件"""
```

#### 2. 时长分配器 (TimingAllocator)
```python
class TimingAllocator:
    def analyze_content_importance(self, segments: List[str]) -> List[float]:
        """分析各段落的重要性权重"""
        
    def calculate_shot_durations(self, 
                               segments: List[str], 
                               total_duration: int,
                               importance_weights: List[float]) -> List[float]:
        """基于重要性权重分配镜头时长"""
        
    def optimize_pacing(self, durations: List[float]) -> List[float]:
        """优化节奏，避免时长过于单调"""
        
    def validate_timing_constraints(self, durations: List[float]) -> bool:
        """验证时长约束(3-15秒每镜头)"""
```

#### 3. 质量控制器 (QualityController)
```python
class QualityController:
    def validate_generation_result(self, clip_path: str) -> QualityScore:
        """验证生成视频的质量"""
        
    def check_visual_consistency(self, clips: List[str]) -> ConsistencyReport:
        """检查镜头间视觉一致性"""
        
    def detect_generation_failures(self, result: GenerationResult) -> bool:
        """检测生成失败并触发重试"""
```

#### 4. 进度追踪器 (ProgressTracker)
```python
class ProgressTracker:
    def initialize_tracking(self, project_id: str, total_shots: int):
        """初始化进度追踪"""
        
    def update_stage_progress(self, project_id: str, stage: str, progress: float):
        """更新某个阶段的进度"""
        
    def get_overall_progress(self, project_id: str) -> ProgressStatus:
        """获取整体项目进度"""
        
    def notify_completion(self, project_id: str):
        """通知项目完成"""
```

### 工作流程整合

#### 完整的视频生成流程
```python
async def create_long_video(script: str, target_duration: int) -> Project:
    """完整的长视频生成流程"""
    
    # 1. 项目初始化
    project = project_manager.create_project(script, target_duration)
    progress_tracker.initialize_tracking(project.id, estimated_shots=10)
    
    # 2. 内容分析 (进度: 0-20%)
    content_analysis = await content_analyzer.analyze_script(script)
    progress_tracker.update_stage_progress(project.id, "analysis", 20)
    
    # 3. 分镜规划 (进度: 20-40%)  
    shot_plan = await shot_planner.create_plan(content_analysis)
    progress_tracker.update_stage_progress(project.id, "planning", 40)
    
    # 4. 时长分配 (进度: 40-50%)
    timing_plan = timing_allocator.allocate_durations(
        shot_plan, target_duration
    )
    progress_tracker.update_stage_progress(project.id, "timing", 50)
    
    # 5. 并发生成 (进度: 50-90%)
    raw_clips = await api_orchestrator.generate_all_shots(
        shot_plan, timing_plan, 
        progress_callback=lambda p: progress_tracker.update_stage_progress(
            project.id, "generation", 50 + p * 40
        )
    )
    
    # 6. 质量检查和文件组织 (进度: 90-100%)
    quality_controller.validate_all_clips(raw_clips)
    project_manager.organize_final_output(project.id, raw_clips)
    progress_tracker.update_stage_progress(project.id, "finalization", 100)
    
    return project
```

---

## 技术实现要求

### 1. 核心模块
- **ContentAnalyzer**：内容分析器
- **ShotPlanner**：分镜规划器  
- **VideoGenerator**：视频生成协调器
- **ProjectManager**：项目管理器

### 2. API集成
- **统一接口**：标准化的API调用接口
- **负载均衡**：智能分配生成任务
- **错误处理**：完善的异常处理机制

### 3. 文件系统
- **目录管理**：自动创建和维护项目目录
- **元数据存储**：完整记录项目信息
- **清理机制**：定期清理临时文件

### 4. 用户体验
- **进度显示**：实时显示生成进度
- **结果预览**：支持快速预览生成结果
- **错误提示**：友好的错误信息和建议

---

## 成功标准

### 功能标准
- ✅ 能够处理500-2000字的文字稿件
- ✅ 自动生成5-20个合理的镜头分段
- ✅ 准确分配每个镜头的时长（3-15秒）
- ✅ 成功调用AI API生成高质量视频片段
- ✅ 在独立目录中组织所有生成文件

### 性能标准
- ✅ 单个项目处理时间：5-15分钟
- ✅ 并发处理：支持3-5个项目同时进行
- ✅ 成功率：>85%的镜头生成成功
- ✅ 存储效率：合理的文件大小和存储占用

### 质量标准
- ✅ 镜头内容与原稿匹配度>80%
- ✅ 视觉风格保持一致性
- ✅ 镜头间逻辑连贯
- ✅ 时长分配合理

---

## 当前状态评估

### 已完成
- ✅ 基础的内容分析功能
- ✅ 分镜规划算法框架
- ✅ 多个AI API客户端
- ✅ 基本的项目结构

### 待实现
- ❌ 完整的文件管理系统
- ❌ 智能时长分配算法  
- ❌ 项目目录自动化管理
- ❌ 用户友好的进度显示
- ❌ 结果预览和管理界面

### 需要优化
- 🔄 分镜算法的准确性
- 🔄 API调用的稳定性
- 🔄 错误处理的完善性
- 🔄 生成效率的提升

---

## 下一步行动计划

### 优先级1：核心功能完善
1. 实现完整的项目目录管理
2. 优化分镜算法和时长分配
3. 建立稳定的API调用机制

### 优先级2：用户体验提升  
1. 添加进度显示和状态反馈
2. 实现结果预览功能
3. 优化错误处理和提示

### 优先级3：系统优化
1. 提升并发处理能力
2. 优化存储和清理机制
3. 添加性能监控和统计

---

*最后更新：2025-08-13*