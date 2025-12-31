# LLM Prompt Optimizer Skill

这是一个专为 **video_creator_platform** 项目设计的 Claude Code skill，用于自动分析和优化 `app/prompts/` 目录中的所有 LLM 提示词。

## 📁 Skill 结构

```
llm-prompt-optimizer/
├── SKILL.md                          # Skill 主文件（Claude 会读取这个）
├── analyze_prompt.py                 # Prompt 分析脚本
├── prompt_optimization_template.md   # 优化模板和最佳实践
└── README.md                         # 本文件
```

## 🎯 功能概述

### 自动激活场景

当你说以下话时，Claude 会自动激活这个 skill：

1. **全面审查**
   - "帮我审查所有 prompt 的质量"
   - "分析一下 prompts 有哪些可以改进"
   - "检查 app/prompts/ 目录"

2. **单个优化**
   - "优化视频分析的 prompt"
   - "content_analysis_basic 这个 prompt 有什么问题？"
   - "改进一下 script_generation prompt"

3. **新 Prompt 设计**
   - "帮我设计一个评估视频质量的 prompt"
   - "需要一个新的 prompt 来..."

4. **跨模型对比**
   - "这个 prompt 在 GPT-4 和 Claude 上效果有什么差异？"
   - "如何让 prompt 在不同模型上都有好效果？"

## 🚀 使用方法

### 方式 1: 让 Claude 自动使用

直接在对话中提出需求，Claude 会自动激活这个 skill：

```
你: 帮我分析所有 prompt 的质量

Claude: [自动激活 llm-prompt-optimizer skill]
我来帮你分析 app/prompts/ 中的所有 prompts...
[使用 Glob 找到所有 .py 文件]
[使用 Grep 搜索 register_prompt]
[使用 Read 读取和分析]
...
```

### 方式 2: 使用分析脚本

你也可以直接运行分析脚本：

```bash
# 进入项目目录
cd video_creator_platform

# 分析所有 prompts
python .claude/skills/llm-prompt-optimizer/analyze_prompt.py

# 分析特定 prompt
python .claude/skills/llm-prompt-optimizer/analyze_prompt.py content_analysis_basic
```

## 📊 Skill 会做什么

### 1. 发现所有 Prompts
使用 `Grep` 搜索所有 `register_prompt` 调用：
```bash
pattern: register_prompt\(
path: app/prompts/
```

### 2. 逐个分析
对每个 prompt 进行：
- 提取名称、内容、变量
- 评估清晰度、完整性、一致性
- 打分（1-10）
- 列出优点和改进建议

### 3. 提供优化方案
- 展示优化前后对比
- 解释优化理由
- 给出具体实施建议

### 4. 生成报告
输出格式化的分析报告，包含：
- 总体统计
- 详细分析
- 优先级建议

## 📝 示例对话

### 示例 1: 全面审查

```
你: 帮我审查所有 prompt 的质量

Claude: 好的，我来全面审查 app/prompts/ 中的所有 prompts。

[使用 Glob 查找文件]
找到以下文件:
- system.py
- llm_analysis.py
- video_analysis.py
- video_generation.py
- image_generation.py
- tts.py

[使用 Grep 提取 prompts]
共发现 25 个 prompts

[逐个分析...]

## 分析报告

### 总体情况
- 总计: 25 个 prompts
- 平均评分: 7.2/10
- 优秀 (9-10分): 5
- 良好 (7-8分): 12
- 需要改进 (<7分): 8

### 需要优先优化的 Prompts

1. **video_analysis** (5/10)
   - 问题: 指令过于简单，缺少输出格式
   - 建议: 添加结构化输出和约束条件
   - 影响: 高（核心功能）

2. **content_analysis_basic** (6/10)
   - 问题: 没有 few-shot examples
   - 建议: 添加示例提升准确性
   - 影响: 中

...
```

### 示例 2: 单个优化

```
你: 优化 video_analysis prompt

Claude: 让我先查看这个 prompt 的当前版本。

[读取 app/prompts/video_analysis.py]

## 当前版本分析

**评分: 5/10**

问题:
1. 指令过于简单
2. 没有明确输出格式
3. 缺少分析维度
4. 没有约束条件

## 优化方案

### 优化后版本

```python
register_prompt(
    "video_analysis",
    """你是一个专业的视频内容分析师...

    [完整的优化版本]
    """
)
```

### 优化说明

1. 添加了角色定义 - 提升专业性
2. 明确了 JSON 输出格式 - 便于解析
3. 列出了具体分析维度 - 提高准确性
4. 添加了约束条件 - 规范输出

预期提升:
- 准确性: +20%
- 一致性: +30%
- 可用性: +40%

是否应用这个优化？
```

### 示例 3: 新 Prompt 设计

```
你: 帮我设计一个评估视频质量的 prompt

Claude: 好的，我来为你设计一个视频质量评估 prompt。

基于你项目现有的 prompt 风格，我建议这样设计：

```python
register_prompt(
    "video_quality_evaluation",
    """你是一个专业的视频质量评估专家...

    [完整的新 prompt]
    """
)
```

这个 prompt 的特点:
1. 遵循项目现有风格
2. 使用了项目的变量命名规范
3. 输出格式与其他 prompt 一致
4. 考虑了视频创作平台的特定需求

你想要调整哪些方面？
```

## 🎓 学习资源

### 内部文档
- **Skill 文档**: `SKILL.md` - 完整的 skill 说明
- **优化模板**: `prompt_optimization_template.md` - 优化模板和案例
- **项目 Prompts 文档**: `app/prompts/README.md` - 现有 prompt 系统说明

### 外部资源
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Design](https://docs.anthropic.com/claude/docs/prompt-design)
- [Google Gemini Best Practices](https://ai.google.dev/gemini-api/docs/prompting-strategies)

## 🔧 高级用法

### 自定义分析标准

你可以修改 `analyze_prompt.py` 中的 `analyze_prompt_quality` 函数来调整评分标准：

```python
def analyze_prompt_quality(prompt: Dict) -> Tuple[int, List[str], List[str]]:
    score = 10
    # ... 添加你自己的评分逻辑
```

### 批量优化

对多个 prompts 进行批量优化：

```
你: 批量优化所有评分低于 7 分的 prompts

Claude: [自动处理多个 prompts]
```

### 对比测试

测试优化前后的效果：

```
你: 对比测试优化前后的 video_analysis prompt

Claude: [提供 A/B 测试建议和方法]
```

## ⚙️ 配置

### 调整 Skill 行为

你可以通过修改 `SKILL.md` 的 `allowed-tools` 来限制 skill 的权限：

```yaml
---
name: llm-prompt-optimizer
description: ...
allowed-tools: Read, Glob, Grep  # 只读权限
# 如果想允许直接修改，添加: Edit, Write
---
```

## 🐛 故障排除

### Skill 没有被激活？

确保你的请求明确提到了：
- "prompt" 或 "提示词"
- "优化" 或 "分析"
- `app/prompts/` 目录

### 分析脚本运行错误？

检查：
1. Python 环境是否正确
2. 文件路径是否正确
3. 是否在项目根目录运行

### 找不到 prompts？

确认：
1. `app/prompts/` 目录存在
2. 文件使用了 `register_prompt` 函数
3. 文件编码是 UTF-8

## 📈 效果跟踪

建议跟踪以下指标：

1. **Prompt 质量评分**
   - 优化前平均分
   - 优化后平均分
   - 提升百分比

2. **实际效果**
   - LLM 响应准确性
   - 输出格式一致性
   - Token 使用量

3. **开发效率**
   - Prompt 迭代次数
   - 调试时间
   - 维护成本

## 🤝 贡献

如果你发现了优化 prompt 的新技巧，欢迎：
1. 更新 `prompt_optimization_template.md`
2. 分享给团队
3. 改进分析脚本

## 📄 许可

与主项目相同的 MIT License。

---

**注意**: 这个 skill 是项目特定的，针对 video_creator_platform 的 prompt 系统设计。如果你在其他项目中使用，可能需要调整。
