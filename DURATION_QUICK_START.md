# 智能时长计算功能 - 快速开始

## ✨ 核心改进

**之前**: 用户必须手动设置视频时长
**现在**: 系统根据内容长度和风格自动计算最佳时长

## 🚀 快速使用

### Python API

```python
from app.services.director.duration_planner import DurationPlanner

# 方式1: 从主题估算 (用户只有想法时)
duration = DurationPlanner.estimate_duration_from_topic(
    topic="如何使用AI生成视频",
    style="教育"
)
# 返回: 54秒

# 方式2: 从脚本精确计算 (已有完整脚本时)
duration = DurationPlanner.estimate_duration_from_script(
    script="欢迎来到AI视频生成教程...(完整脚本内容)",
    style="专业"
)
# 返回: 65秒

# 方式3: 完整规划
total_duration, shot_count, shot_durations = plan_video_structure(
    content="用户输入的主题或脚本",
    style="教育",
    content_type="topic"  # 或 "script"
)
# 返回: (54, 4, [13.5, 13.5, 13.5, 13.5])
```

### REST API

**自动计算** (推荐):
```bash
# 不传 targetDuration，系统自动计算
curl -X POST "http://localhost:8000/api/scripts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "如何使用AI生成视频",
    "style": "教育"
  }'
```

**手动指定** (仍支持):
```bash
# 传入 targetDuration，使用指定时长
curl -X POST "http://localhost:8000/api/scripts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "如何使用AI生成视频",
    "style": "教育",
    "targetDuration": 120
  }'
```

### Frontend (React/TypeScript)

```typescript
// 不传 targetDuration，让后端自动计算
const response = await scriptsApi.generateScript({
    topic: "如何使用AI生成视频",
    style: "教育",
    // targetDuration 不传，自动计算
});

// 显示自动计算的时长
console.log(`估算时长: ${response.totalDuration}秒`);
```

## 📊 时长计算规则

### 不同风格的语速

| 风格 | 语速 | 说明 | 适用场景 |
|------|------|------|----------|
| 娱乐 | 6字/秒 | 快节奏 | 短视频、搞笑内容 |
| 轻松 | 6字/秒 | 快节奏 | 生活分享、vlog |
| 专业 | 4.5字/秒 | 标准节奏 | 产品介绍、技术分享 |
| 科技 | 4.5字/秒 | 标准节奏 | 科技评测、技术教程 |
| 商业 | 4.5字/秒 | 标准节奏 | 企业宣传、商业推广 |
| 生活 | 4.5字/秒 | 标准节奏 | 生活记录、日常分享 |
| 教育 | 3字/秒 | 慢速清晰 | 教学课程、知识讲解 |
| 严肃 | 3字/秒 | 慢速庄重 | 新闻播报、正式场合 |
| 艺术 | 3字/秒 | 慢速留白 | 艺术展示、创意视频 |
| 纪录片 | 3字/秒 | 深度叙述 | 纪实内容、深度报道 |

### 相同主题不同风格的时长差异

以 **"如何使用AI生成视频，包括脚本创作和分镜规划"** (22字) 为例:

```
娱乐风格    →  48秒  (快节奏)
轻松风格    →  51秒  (较快)
专业风格    →  60秒  (标准)
科技风格    →  60秒  (标准)
教育风格    →  72秒  (慢速，便于理解)
纪录片风格  →  78秒  (深度叙述)
```

## 🎯 实际应用场景

### 场景1: 短视频平台 (抖音、快手)

```python
# 短主题 + 娱乐风格 = 30-60秒短视频
topic = "3个AI视频生成技巧"
style = "娱乐"
duration = estimate_duration_from_topic(topic, style)
# 结果: 45秒 ✓ 适合短视频平台
```

### 场景2: 教育平台 (B站、YouTube)

```python
# 详细主题 + 教育风格 = 90-180秒教程
topic = "完整的AI视频生成流程讲解，包括脚本创作、分镜规划、视频生成和后期处理"
style = "教育"
duration = estimate_duration_from_topic(topic, style)
# 结果: 117秒 ✓ 适合深度教程
```

### 场景3: 企业宣传

```python
# 中等主题 + 专业风格 = 60-90秒宣传片
topic = "介绍我们的AI视频生成平台的核心功能和优势"
style = "专业"
duration = estimate_duration_from_topic(topic, style)
# 结果: 60秒 ✓ 适合企业宣传
```

## 🔍 计算过程示例

### 示例: "如何使用AI生成视频" + 教育风格

```
1. 主题分析
   - 长度: 10字
   - 类型: 中等主题 (< 20字)
   - 基础时长: 45秒

2. 应用风格系数
   - 教育风格: 1.2倍
   - 调整后: 45 * 1.2 = 54秒

3. 最终时长: 54秒

4. 建议镜头数
   - 教育风格: 12秒/镜头
   - 镜头数: 54 ÷ 12 ≈ 4个
   - 各镜头时长: [13.5, 13.5, 13.5, 13.5]秒
```

## 📝 测试验证

运行测试:
```bash
python test_duration_planner.py
```

测试涵盖:
- ✅ 不同长度主题的时长估算
- ✅ 不同风格的时长差异
- ✅ 中英文混合内容处理
- ✅ 镜头数量和时长分配
- ✅ 加权镜头规划
- ✅ 完整视频结构规划

## 🎨 前端体验

### Before (手动设置)
```
┌─────────────────────────────┐
│ 时长: [====●====] 60秒       │  ← 用户手动调整
└─────────────────────────────┘
```

### After (自动计算)
```
┌─────────────────────────────┐
│ ✨ 估算时长: 54秒             │  ← 自动显示
│ 根据内容长度和风格自动计算    │
└─────────────────────────────┘
```

## 💡 技术细节

### 缓冲时间计算

```python
# 固定缓冲: 开场 + 结尾
fixed_buffer = 5 + 3 = 8秒

# 动态缓冲: 根据内容长度
dynamic_buffer = base_duration * 0.12  # 12%用于过渡

# 风格系数
style_factors = {
    "娱乐": 0.8,    # 快节奏，少留白
    "艺术": 1.3,    # 多留白，有美感
    "纪录片": 1.2   # 氛围营造
}

# 总缓冲时间
buffer = (fixed_buffer + dynamic_buffer) * style_factor
```

### 中英文混合处理

```python
# 统计中文字数
chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))

# 统计英文单词
english_words = len(re.findall(r"[a-zA-Z]+", text))

# 折算 (1个英文单词 ≈ 2个中文字)
total_chars = chinese_chars + (english_words * 2)
```

## 📚 相关文档

- 完整文档: `DURATION_AUTO_CALCULATION.md`
- 测试脚本: `test_duration_planner.py`
- 源代码: `app/services/director/duration_planner.py`
- API文档: `app/api/video_generation.py`, `app/api/scripts.py`

## 🎓 最佳实践

### DO ✅
- 让系统自动计算时长 (推荐)
- 提供清晰详细的主题描述
- 选择合适的视频风格
- 相信AI的智能估算

### DON'T ❌
- 不要手动猜测时长 (除非有特殊需求)
- 不要忽略风格选择 (影响语速和节奏)
- 不要期望固定时长 (内容长度决定时长)

## 🔧 调试

查看日志了解计算过程:
```python
import logging
logging.basicConfig(level=logging.INFO)

# 日志会显示:
# INFO - 自动估算视频时长: 54秒 (主题长度: 10字, 风格: 教育)
# INFO - Topic估算: 长度=10, 基础=45s, 风格系数=1.2, 最终=54s
```

## 📞 支持

遇到问题? 检查:
1. 主题长度是否合理 (建议 10-100字)
2. 风格是否在支持列表中
3. 日志输出的计算过程
4. 参考测试用例

---

**版本**: 1.0.0
**更新日期**: 2025-12-14
**状态**: ✅ 生产就绪
