---
name: llm-prompt-optimizer
description: 分析和优化LLM提示词。当需要改进脚本分析、分镜生成、或内容理解的prompt质量时激活。包括审查app/prompts/中的提示词、分析prompt结构、提供优化建议、对比不同LLM适配器的prompt策略。
allowed-tools: Read, Glob, Grep
---

# LLM Prompt 优化 Skill

这个 skill 专门用于分析和优化 **video_creator_platform** 项目中 `app/prompts/` 目录下的所有 LLM 提示词。

## 🎯 功能概述

### 1. **Prompt 审查**
- 扫描 `app/prompts/*.py` 中所有已注册的 prompt
- 分析 prompt 的结构、清晰度和完整性
- 识别潜在的问题和改进空间

### 2. **质量分析**
- **清晰度**: 指令是否明确、易于理解
- **完整性**: 是否包含所有必要的上下文和约束
- **一致性**: 格式和风格是否统一
- **有效性**: 是否使用了最佳实践（few-shot examples、结构化输出等）

### 3. **优化建议**
- 提供具体的改进建议
- 展示优化前后的对比
- 给出优化理由和预期效果

### 4. **多模型适配**
- 分析针对不同 LLM 提供商（OpenAI, Anthropic, Google）的 prompt 策略
- 识别模型特定的优化机会
- 建议跨模型的最佳实践

## 📋 项目 Prompt 系统结构

根据项目架构，主要的 prompt 文件包括：

```
app/prompts/
├── base.py              # 基础组件和策略
├── config.py            # 配置管理
├── system.py            # 系统级提示词（错误处理、日志分析等）
├── llm_analysis.py      # 内容分析提示词
├── video_analysis.py    # 视频分析提示词
├── video_generation.py  # 视频生成提示词
├── image_generation.py  # 图像生成提示词
├── tts.py              # TTS 提示词
└── examples.py         # 示例数据
```

## 🔍 分析流程

### 第一步：发现所有 Prompts
```bash
# 使用 Grep 搜索所有 register_prompt 调用
pattern: register_prompt\(
path: app/prompts/
```

### 第二步：读取和分析
对每个 prompt 进行：
1. 提取 prompt 名称和内容
2. 识别使用的变量 (`{{ variable }}`)
3. 分析结构和格式
4. 评估清晰度和完整性

### 第三步：生成报告
提供以下内容：
- Prompt 清单和分类
- 质量评分（1-10分）
- 具体改进建议
- 优化示例

## 💡 优化最佳实践

### 1. **结构化输出**
**差**:
```
请分析视频内容并返回结果
```

**好**:
```
请分析视频内容并返回JSON格式：
{
  "summary": "内容摘要",
  "key_points": ["要点1", "要点2"],
  "sentiment": "positive/negative/neutral"
}
```

### 2. **Few-shot Examples**
为复杂任务添加示例：
```
# 示例1:
输入: "一段关于美食制作的视频"
输出: {"category": "cooking", "tags": ["food", "tutorial"]}

# 你的任务:
输入: {{ content }}
输出:
```

### 3. **清晰的约束条件**
```
要求：
- 摘要长度不超过100字
- 提取3-5个关键点
- 情感分析必须是 positive/negative/neutral 之一
- 标签数量不超过5个
```

### 4. **上下文感知**
```
根据视频类型调整分析策略：
- 教育类: 关注学习价值和知识点
- 娱乐类: 关注吸引力和互动性
- 营销类: 关注转化潜力和卖点
```

## 🎨 针对不同 LLM 的优化

### OpenAI (GPT-4, GPT-3.5)
- 擅长结构化输出和 JSON 格式
- 使用 system/user/assistant 角色明确
- 支持 function calling

### Anthropic (Claude)
- 擅长长文本理解和复杂推理
- 使用 XML 标签组织内容效果好
- 明确的思考过程引导

### Google (Gemini)
- 多模态能力强
- 简洁明确的指令效果更好
- 适合视频和图像分析任务

## 📊 Prompt 评分标准

### 满分 Prompt (9-10分)
- 指令明确、目标清晰
- 包含结构化输出格式
- 有示例或约束条件
- 考虑了边界情况
- 变量使用合理

### 良好 Prompt (7-8分)
- 指令清晰
- 有基本的输出格式
- 变量定义明确
- 缺少示例或约束

### 需要改进 (5-6分)
- 指令模糊
- 输出格式不清晰
- 缺少重要约束
- 变量使用不当

### 差劲 Prompt (1-4分)
- 指令不明确
- 无输出格式定义
- 逻辑混乱
- 变量缺失或错误

## 🚀 使用场景

### 场景 1: 全面审查
**用户说**: "帮我审查一下所有的 prompt 质量"

**Skill 行动**:
1. 扫描 `app/prompts/` 所有文件
2. 提取所有 `register_prompt` 调用
3. 逐个分析和评分
4. 生成综合报告

### 场景 2: 单个 Prompt 优化
**用户说**: "优化一下视频分析的 prompt"

**Skill 行动**:
1. 定位 `video_analysis.py` 或相关文件
2. 读取和分析目标 prompt
3. 提供具体优化建议和改写示例
4. 解释优化理由

### 场景 3: 新 Prompt 设计
**用户说**: "帮我设计一个评估视频质量的 prompt"

**Skill 行动**:
1. 理解需求和目标
2. 参考项目现有 prompt 风格
3. 设计符合项目架构的新 prompt
4. 提供集成建议

### 场景 4: 跨模型对比
**用户说**: "这个 prompt 在不同模型上的效果会有什么差异？"

**Skill 行动**:
1. 分析 prompt 特点
2. 对比 OpenAI、Anthropic、Google 的处理方式
3. 提供模型特定的优化建议
4. 建议通用性最好的写法

## 📝 输出格式

### Prompt 分析报告模板

```markdown
## Prompt 分析: [prompt_name]

### 基本信息
- **文件位置**: app/prompts/xxx.py
- **用途**: [简要描述]
- **变量**: {{ var1 }}, {{ var2 }}

### 质量评分: [X/10]

### 优点
- [列出做得好的地方]

### 改进空间
1. [具体问题1]
2. [具体问题2]

### 优化建议

#### 当前版本
```python
register_prompt(
    "xxx",
    """[当前内容]"""
)
```

#### 优化版本
```python
register_prompt(
    "xxx",
    """[优化后内容]"""
)
```

#### 优化理由
[解释为什么这样改进]

#### 预期效果
[改进后预期的效果]
```

## 🔧 辅助工具

### 使用 analyze_prompt.py 脚本
```bash
cd video_creator_platform
python .claude/skills/llm-prompt-optimizer/analyze_prompt.py [prompt_name]
```

### 使用优化模板
参考 `prompt_optimization_template.md` 进行系统化优化。

## 📚 参考资源

- 项目 Prompt 系统文档: `app/prompts/README.md`
- OpenAI Prompt Engineering Guide
- Anthropic Prompt Design Best Practices
- Google Gemini Prompt Guidelines

## 🎯 成功指标

优化后的 prompt 应该：
1. 提高 LLM 响应的准确性和一致性
2. 减少需要重试的次数
3. 输出格式更规范，易于解析
4. 降低 token 使用量（在不影响质量的前提下）
5. 提升跨模型的兼容性

---

## 使用提示

当你激活这个 skill 时，Claude 会：
1. 自动扫描和分析项目中的 prompt
2. 识别优化机会
3. 提供具体的改进建议
4. 帮助你实施优化

你可以说：
- "分析所有 prompt 的质量"
- "优化视频分析的 prompt"
- "这个 prompt 有什么问题？"
- "帮我设计一个新的 prompt"
- "对比一下不同模型的 prompt 策略"
