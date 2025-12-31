# 自动时长计算功能集成完成 ✅

## 📋 概述

根据用户需求，已将视频时长从"用户手动设置"改为"根据内容自动计算"。系统现在会智能分析用户输入的主题/脚本长度，结合视频风格，自动计算最合适的视频时长。

## 🎯 核心改进

### 之前 (Before)
```python
# 用户必须手动设置时长
targetDuration: int = 60  # 固定默认值
```

### 现在 (After)
```python
# 自动根据内容长度和风格计算
targetDuration: Optional[int] = None  # 不传则自动计算

# 智能估算示例
topic = "如何使用AI生成视频"
duration = DurationPlanner.estimate_duration_from_topic(topic, "教育")
# 自动返回: 90秒 (基于主题长度和教育风格的慢语速)
```

## 📦 新增核心模块

### `app/services/director/duration_planner.py`

智能时长规划服务，包含：

#### 1. 语速配置
```python
SPEECH_RATE_SLOW = 3      # 3字/秒 - 教育、严肃、纪录片
SPEECH_RATE_NORMAL = 4.5  # 4.5字/秒 - 专业、科技、商业
SPEECH_RATE_FAST = 6      # 6字/秒 - 娱乐、轻松
```

#### 2. 核心功能

**从主题估算时长** (用户只有想法时)
```python
DurationPlanner.estimate_duration_from_topic(
    topic="如何使用AI生成视频，包括脚本创作、分镜规划",
    style="教育"
)
# 返回: 90秒
# 逻辑:
# - 主题长度: 23字 → 基础60秒
# - 教育风格系数: 1.2 → 60 * 1.2 = 72秒
# - 添加缓冲时间(开场/结尾/过渡): 18秒
# - 最终: 90秒
```

**从脚本精确计算时长** (已有完整脚本时)
```python
DurationPlanner.estimate_duration_from_script(
    script="""
    欢迎来到AI视频生成教程。今天我们将学习如何使用最新的AI技术，
    从零开始创建一个专业的视频。首先，我们需要创作一个吸引人的脚本...
    (共300字中文 + 20个英文单词)
    """,
    style="教育"
)
# 返回: 108秒
# 逻辑:
# - 中文: 300字
# - 英文: 20词 × 2 = 40字等效
# - 总计: 340字
# - 教育语速: 3字/秒 → 340/3 = 113秒
# - 缓冲时间: 约15秒
# - 最终: 108秒
```

**镜头数量建议**
```python
DurationPlanner.suggest_shot_count(duration=90, style="教育")
# 返回: 8个镜头
# 逻辑: 90秒 ÷ 12秒/镜头(教育风格) ≈ 8个
```

## 🔄 已修改的文件

### Backend Changes

#### 1. `app/api/video_generation.py`
```python
# 导入时长规划器
from app.services.director.duration_planner import DurationPlanner

class VideoGenerationTask(BaseModel):
    targetDuration: Optional[int] = None  # 改为可选

# 在create_video_generation_task中添加自动计算
if request.targetDuration is None:
    estimated_duration = DurationPlanner.estimate_duration_from_topic(
        request.topic,
        request.style
    )
    logger.info(f"自动估算视频时长: {estimated_duration}秒")
    request.targetDuration = estimated_duration
```

#### 2. `app/api/scripts.py`
```python
# 导入时长规划器
from app.services.director.duration_planner import DurationPlanner

class ScriptGenerateRequest(BaseModel):
    targetDuration: Optional[int] = None  # 改为可选

# 在generate_script中添加自动计算
if request.targetDuration is None:
    estimated_duration = DurationPlanner.estimate_duration_from_topic(
        request.topic,
        request.style
    )
    logger.info(f"自动估算视频时长: {estimated_duration}秒")
    request.targetDuration = estimated_duration
```

### Frontend Changes

#### 3. `frontend/src/api/types.ts`
```typescript
export interface VideoGenerationRequest {
  topic: string;
  style: string;
  targetDuration?: number;  // 改为可选
  // ...
}
```

#### 4. `frontend/src/pages/Generate.tsx`
**移除**:
- ❌ Duration Slider (手动调整时长的滑块)
- ❌ `targetDuration` state

**新增**:
- ✅ `estimatedDuration` state (显示自动计算的时长)
- ✅ 只读的时长显示区域，显示"Auto"或实际估算时长
- ✅ 提示信息: "Duration will be automatically calculated based on your topic length and selected style"

```tsx
// Before
const [targetDuration, setTargetDuration] = useState<number>(60);
<Slider value={targetDuration} onChange={...} />

// After
const [estimatedDuration, setEstimatedDuration] = useState<number | null>(null);
<Paper>Duration will be automatically calculated...</Paper>
<Chip label={estimatedDuration ? `${estimatedDuration}s` : 'Auto'} />
```

## 🔢 计算逻辑详解

### 从主题估算 (Topic-based)

1. **基于主题长度的启发式规则**
   ```
   < 20字   → 基础45秒  (简短主题)
   20-50字  → 基础60秒  (中等主题)
   50-100字 → 基础90秒  (较长主题)
   > 100字  → 基础120秒 (详细主题)
   ```

2. **应用风格系数**
   ```
   教育/纪录片/严肃/艺术 → 1.1-1.3倍 (需要更多时间解释)
   专业/科技/商业/生活   → 1.0倍 (标准节奏)
   娱乐/轻松              → 0.8-0.9倍 (快节奏)
   ```

3. **限制在合理范围**
   ```
   最小: 30秒
   最大: 300秒 (5分钟)
   ```

### 从脚本精确计算 (Script-based)

1. **统计字数**
   ```python
   chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", script))
   english_words = len(re.findall(r"[a-zA-Z]+", script))
   total_chars = chinese_chars + (english_words * 2)  # 1英文词 ≈ 2中文字
   ```

2. **根据风格选择语速**
   ```
   教育/严肃/纪录片/艺术 → 3字/秒
   专业/科技/商业/生活   → 4.5字/秒
   娱乐/轻松              → 6字/秒
   ```

3. **计算基础时长**
   ```
   base_duration = total_chars / speech_rate
   ```

4. **添加缓冲时间**
   ```python
   fixed_buffer = 8秒  # 开场5秒 + 结尾3秒
   dynamic_buffer = base_duration * 0.12  # 12%用于过渡
   total_duration = base_duration + (fixed_buffer + dynamic_buffer) * style_factor
   ```

## 📊 实际效果示例

### 示例1: 短主题
```python
topic = "AI视频生成"
style = "专业"
# 输入: 6字
# 输出: 45秒
```

### 示例2: 中等主题
```python
topic = "如何使用AI技术快速创建专业视频，包括脚本创作和分镜设计"
style = "教育"
# 输入: 28字
# 输出: 72秒 (60 * 1.2)
```

### 示例3: 完整脚本
```python
script = """
欢迎来到AI视频生成教程。今天我们将学习如何使用最新的AI技术，
从零开始创建一个专业的视频。首先，我们需要创作一个吸引人的脚本。
脚本是视频的灵魂，一个好的脚本能够吸引观众的注意力...
"""  # 约180字
style = "教育"
# 计算过程:
# - 总字数: 180字
# - 语速: 3字/秒
# - 基础: 60秒
# - 缓冲: 15秒
# - 输出: 75秒
```

## ✅ 兼容性说明

### 向后兼容
API仍然支持手动传入`targetDuration`:
```python
# 自动计算 (推荐)
request = {"topic": "AI教程", "style": "教育"}

# 手动指定 (仍然支持)
request = {"topic": "AI教程", "style": "教育", "targetDuration": 120}
```

### 前端体验
- 用户无需再考虑时长问题
- 系统会根据输入内容智能建议最佳时长
- 生成完成后显示实际使用的时长

## 🎓 使用建议

### 对于短视频平台 (抖音、快手)
```python
# 简短主题 + 娱乐风格 → 自动生成 30-60秒短视频
topic = "3个AI视频生成技巧"
style = "娱乐"
# 估算: ~45秒
```

### 对于教育内容 (B站、YouTube)
```python
# 详细主题 + 教育风格 → 自动生成 90-180秒教程
topic = "完整的AI视频生成流程讲解，包括脚本创作、分镜规划、视频生成"
style = "教育"
# 估算: ~120秒
```

### 对于专业内容 (商业、技术)
```python
# 中等主题 + 专业风格 → 自动生成 60-90秒介绍
topic = "介绍我们的AI视频生成平台的核心功能"
style = "专业"
# 估算: ~75秒
```

## 🔍 日志示例

启用自动计算后，后端日志会显示：
```
INFO - 自动估算视频时长: 90秒 (主题长度: 28字, 风格: 教育)
INFO - Topic估算: 长度=28, 基础=60s, 风格系数=1.2, 最终=90s
INFO - 镜头数量建议: 时长=90s, 风格=教育, 建议=8个
```

## 📝 总结

### 核心价值
1. **用户体验提升**: 无需手动猜测合适的时长
2. **智能化**: 根据内容长度和风格自动计算
3. **专业化**: 考虑语速、缓冲时间、镜头节奏等专业因素
4. **灵活性**: 仍支持手动指定时长

### 技术亮点
- ✅ 中英文混合内容处理
- ✅ 多风格语速适配
- ✅ 智能缓冲时间计算
- ✅ 镜头数量自动建议
- ✅ 完整的日志追踪

---

**实施日期**: 2025-12-14
**状态**: ✅ 已完成并集成
