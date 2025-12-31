# Prompt 优化模板

这个模板提供了系统化的 prompt 优化流程和检查清单。

## 📋 优化检查清单

### ✅ 基础要素
- [ ] 有明确的任务描述
- [ ] 定义了角色或专家身份
- [ ] 指定了输出格式
- [ ] 包含必要的约束条件
- [ ] 使用了合适的变量

### ✅ 高级要素
- [ ] 提供了 few-shot examples
- [ ] 有清晰的思考过程引导
- [ ] 考虑了边界情况
- [ ] 包含错误处理指导
- [ ] 适配不同的 LLM 模型

### ✅ 输出质量
- [ ] 输出格式结构化（JSON/XML/Markdown）
- [ ] 有明确的字段说明
- [ ] 定义了数据类型和范围
- [ ] 提供了验证标准

## 🔧 优化模板

### 模板 1: 基础分析型 Prompt

```python
register_prompt(
    "prompt_name",
    """你是一个专业的{{ role }}，擅长{{ expertise }}。

请分析以下{{ content_type }}:
{{ content }}

{% if additional_context %}
额外上下文:
{{ additional_context }}
{% endif %}

请按照以下格式返回 JSON 结果：
{
    "summary": "内容摘要（50-100字）",
    "key_points": ["要点1", "要点2", "要点3"],
    "analysis": {
        "aspect1": "分析维度1",
        "aspect2": "分析维度2"
    },
    "confidence": "评估置信度（1-10）"
}

要求:
1. 摘要应简洁明确，突出核心内容
2. 提取3-5个最重要的要点
3. 分析应基于内容，避免主观臆断
4. 如果信息不足，请在相应字段说明

示例:
输入: "一段关于Python编程的教学视频"
输出: {
    "summary": "Python基础语法教学，适合初学者",
    "key_points": ["变量定义", "函数使用", "条件语句"],
    "analysis": {
        "difficulty": "初级",
        "quality": "高质量教学内容"
    },
    "confidence": 8
}"""
)
```

### 模板 2: 生成型 Prompt

```python
register_prompt(
    "generation_prompt",
    """你是一个专业的{{ role }}，负责创作{{ output_type }}。

创作要求:
主题: {{ topic }}
风格: {{ style }}
目标受众: {{ audience }}
{% if constraints %}
约束条件: {{ constraints }}
{% endif %}

请按照以下结构创作:
1. 开场 (吸引注意)
2. 主体内容 (分段展开)
3. 结尾 (总结和行动号召)

格式要求:
- 使用{{ language }}语言
- 长度: {{ length_requirement }}
- 语气: {{ tone }}

输出格式:
{
    "title": "标题",
    "content": "正文内容",
    "sections": [
        {
            "heading": "章节标题",
            "content": "章节内容",
            "duration": "预计时长(秒)"
        }
    ],
    "metadata": {
        "word_count": "字数",
        "estimated_reading_time": "预计阅读时间"
    }
}

示例:
主题: "健康饮食"
输出: {
    "title": "10个简单的健康饮食习惯",
    "sections": [
        {"heading": "多喝水", "content": "...", "duration": 30},
        {"heading": "均衡营养", "content": "...", "duration": 45}
    ]
}"""
)
```

### 模板 3: 评估型 Prompt

```python
register_prompt(
    "evaluation_prompt",
    """你是一个专业的{{ evaluator_role }}，负责评估{{ evaluation_target }}。

评估对象:
{{ content }}

评估维度:
{% for dimension in evaluation_dimensions %}
- {{ dimension.name }}: {{ dimension.description }}
{% endfor %}

请返回以下格式的评估报告:
{
    "overall_score": "总体评分(1-10)",
    "dimensions": {
        "dimension1": {
            "score": "评分(1-10)",
            "explanation": "评分理由",
            "suggestions": ["改进建议1", "建议2"]
        }
    },
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["缺点1", "缺点2"],
    "recommendations": {
        "priority_high": ["高优先级改进"],
        "priority_medium": ["中优先级改进"],
        "priority_low": ["低优先级改进"]
    }
}

评分标准:
- 9-10分: 优秀，达到行业顶尖水平
- 7-8分: 良好，符合专业标准
- 5-6分: 一般，有明显改进空间
- 1-4分: 较差，需要大幅改进

要求:
1. 评分应客观、有依据
2. 每个维度都需要具体说明
3. 改进建议应具体可执行
4. 优先级划分应合理"""
)
```

## 🎯 针对视频创作平台的优化建议

### 1. 视频分析 Prompts

**关注点:**
- 视频内容理解的深度
- 场景识别的准确性
- 情感和语气的捕捉
- 目标受众分析

**优化方向:**
```python
# 添加视频特定的分析维度
"visual_elements": ["画面构图", "色彩运用", "镜头语言"],
"audio_quality": ["语音清晰度", "背景音乐", "音效"],
"engagement_factors": ["开场吸引力", "节奏控制", "互动性"]
```

### 2. 分镜生成 Prompts

**关注点:**
- 镜头连贯性
- 时长分配合理性
- 视觉多样性
- 叙事逻辑

**优化方向:**
```python
# 提供分镜设计的具体指导
"""
每个镜头应包含:
1. 镜头类型: 特写/中景/全景
2. 运镜方式: 固定/推拉/摇移
3. 视觉重点: 主体描述
4. 时长: 3-15秒（根据内容复杂度）
5. 转场方式: 切换/淡入淡出/特效
"""
```

### 3. 内容理解 Prompts

**关注点:**
- 主题提取准确性
- 关键信息识别
- 情感倾向判断
- 内容分类精确度

**优化方向:**
```python
# 增强上下文理解
"""
基于以下信息进行综合分析:
1. 标题: {{ title }}
2. 描述: {{ description }}
3. 文本内容: {{ transcript }}
4. 视觉元素: {{ visual_description }}
5. 音频特征: {{ audio_features }}
"""
```

## 📊 优化前后对比模板

### 优化案例 1

**原始版本 (评分: 5/10)**
```python
register_prompt(
    "video_analysis",
    "分析这个视频: {{ video_info }}"
)
```

**问题:**
- 指令过于简单
- 没有明确输出格式
- 缺少分析维度
- 没有约束条件

**优化版本 (评分: 9/10)**
```python
register_prompt(
    "video_analysis",
    """你是一个专业的视频内容分析师，擅长内容理解和受众洞察。

请分析以下视频:
标题: {{ video_info.title }}
时长: {{ video_info.duration }}秒
{% if video_info.description %}
描述: {{ video_info.description }}
{% endif %}

请返回以下格式的 JSON 分析报告:
{
    "summary": "视频内容摘要（100字内）",
    "category": "内容分类",
    "key_topics": ["主题1", "主题2", "主题3"],
    "sentiment": "positive/neutral/negative",
    "target_audience": "目标受众描述",
    "engagement_prediction": "观众参与度预测（1-10）",
    "visual_style": "视觉风格描述",
    "production_quality": "制作质量评估（1-10）"
}

分析要求:
1. 基于实际内容，避免臆测
2. 分类从 [教育/娱乐/营销/新闻/其他] 中选择
3. 提取3-5个核心主题
4. 情感分析应基于整体基调
5. 受众描述应具体（年龄、兴趣、背景）"""
)
```

**改进点:**
1. ✅ 添加了角色定义
2. ✅ 明确了输出 JSON 格式
3. ✅ 定义了具体分析维度
4. ✅ 提供了清晰的约束条件
5. ✅ 指定了字段的可选值范围

## 🚀 实施步骤

### 步骤 1: 审查现有 Prompt
1. 运行分析脚本: `python .claude/skills/llm-prompt-optimizer/analyze_prompt.py`
2. 识别评分低于 7 分的 prompts
3. 记录主要问题

### 步骤 2: 制定优化计划
1. 按优先级排序（核心功能优先）
2. 分组处理（同类型 prompt 一起优化）
3. 设定时间表

### 步骤 3: 逐个优化
1. 使用上述模板作为参考
2. 保持项目风格一致
3. 在测试环境验证效果
4. 记录优化前后对比

### 步骤 4: 测试和迭代
1. 在实际场景中测试
2. 收集反馈和数据
3. 根据效果继续调整
4. 更新文档

## 📝 优化记录模板

```markdown
## Prompt 优化记录

**Prompt 名称:** [name]
**优化日期:** [date]
**优化人员:** [name]

**优化前评分:** X/10
**优化后评分:** X/10

**主要改进:**
1. [改进点1]
2. [改进点2]

**测试结果:**
- 准确性: [提升/持平/下降] X%
- 响应速度: [提升/持平/下降] X%
- Token 使用: [减少/持平/增加] X%

**后续计划:**
- [ ] 继续监控效果
- [ ] 收集用户反馈
- [ ] 考虑进一步优化
```

## 💡 额外建议

### 1. 版本控制
- 保留优化前的版本作为备份
- 使用 git 跟踪所有变更
- 添加详细的 commit 说明

### 2. A/B 测试
- 对关键 prompts 进行 A/B 测试
- 收集量化数据
- 基于数据做决策

### 3. 文档维护
- 更新 `app/prompts/README.md`
- 记录优化理由和效果
- 分享最佳实践

### 4. 持续改进
- 定期审查 prompt 效果
- 关注 LLM 模型更新
- 学习行业最佳实践
- 与团队分享经验
