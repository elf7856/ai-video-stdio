"""
LLM分析相关的提示词模板
"""

from .base import register_prompt

# 基础内容分析提示词
register_prompt(
    "content_analysis_basic",
    """请分析以下内容并返回JSON格式的结果：

内容: {{ content }}

请返回以下格式的JSON：
{
    "summary": "内容摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "sentiment": "positive/negative/neutral",
    "category": "分类",
    "tags": ["标签1", "标签2"]
}"""
)

# 教育内容分析提示词
register_prompt(
    "content_analysis_educational",
    """请分析以下教育内容并返回JSON格式的结果：

内容: {{ content }}

请返回以下格式的JSON：
{
    "summary": "内容摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "sentiment": "positive/negative/neutral",
    "category": "分类",
    "tags": ["标签1", "标签2"],
    "educational_value": "教育价值描述",
    "learning_objectives": ["学习目标1", "学习目标2"],
    "difficulty_level": "初级/中级/高级",
    "core_concepts": ["核心概念1", "核心概念2"]
}

额外要求：
- 识别教育价值和学习目标
- 分析难度级别
- 提取核心概念"""
)

# 娱乐内容分析提示词
register_prompt(
    "content_analysis_entertainment",
    """请分析以下娱乐内容并返回JSON格式的结果：

内容: {{ content }}

请返回以下格式的JSON：
{
    "summary": "内容摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "sentiment": "positive/negative/neutral",
    "category": "分类",
    "tags": ["标签1", "标签2"],
    "entertainment_elements": ["娱乐元素1", "娱乐元素2"],
    "target_audience": "目标受众描述",
    "engagement_level": "吸引力评级(1-10)",
    "content_quality": "内容质量评估"
}

额外要求：
- 分析娱乐元素和吸引力
- 识别目标受众
- 评估内容质量"""
)

# 营销内容分析提示词
register_prompt(
    "content_analysis_marketing",
    """请分析以下营销内容并返回JSON格式的结果：

内容: {{ content }}

请返回以下格式的JSON：
{
    "summary": "内容摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "sentiment": "positive/negative/neutral",
    "category": "分类",
    "tags": ["标签1", "标签2"],
    "marketing_strategy": "营销策略分析",
    "selling_points": ["卖点1", "卖点2"],
    "target_market": "目标市场描述",
    "conversion_potential": "转化潜力评估(1-10)"
}

额外要求：
- 识别营销策略和卖点
- 分析目标市场
- 评估转化潜力"""
)

# 视频内容组合分析提示词
register_prompt(
    "video_content_analysis",
    """请分析以下视频内容：

{% if video_info %}
视频信息：
{% if video_info.title %}标题: {{ video_info.title }}{% endif %}
{% if video_info.description %}描述: {{ video_info.description[:500] }}{% endif %}
{% if video_info.duration %}时长: {{ video_info.duration }}{% endif %}
{% endif %}

{% if extracted_text %}
提取的文本内容：
{{ extracted_text[:1000] }}
{% endif %}

请返回以下格式的JSON：
{
    "summary": "内容摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "sentiment": "positive/negative/neutral",
    "category": "分类",
    "tags": ["标签1", "标签2"],
    "video_analysis": {
        "content_type": "视频类型",
        "quality_assessment": "质量评估",
        "audience_engagement": "观众参与度预测"
    }
}"""
)

# 改进建议提示词
register_prompt(
    "improvement_suggestions",
    """基于以下视频分析结果，请提供改进建议：

分析结果：{{ analysis_summary }}

请返回以下格式的JSON：
{
    "content_improvements": ["内容改进建议1", "建议2"],
    "technical_improvements": ["技术改进建议1", "建议2"],
    "engagement_improvements": ["参与度提升建议1", "建议2"],
    "overall_rating": "整体评分(1-10)",
    "priority_actions": ["优先行动1", "行动2"]
}"""
)

# 脚本生成提示词
register_prompt(
    "script_generation",
    """请为以下主题生成一个{{ duration_minutes }}分钟的{{ style }}风格视频脚本：

主题：{{ topic }}

请包含以下结构：
1. 开场白（吸引观众注意）
2. 主要内容（分段展示）
3. 互动环节（如适用）
4. 总结和呼吁行动

脚本格式要求：
- 自然的语言表达
- 合适的节奏控制
- 清晰的段落划分
- 适当的转场过渡

请返回完整的脚本内容。"""
)

# 关键时刻提取提示词
register_prompt(
    "key_moments_extraction",
    """请从以下视频转录文本中提取{{ max_moments }}个关键时刻：

转录文本：{{ transcript }}

请返回以下格式的JSON：
{
    "key_moments": [
        {
            "timestamp": "时间点描述",
            "description": "关键时刻描述",
            "importance": "重要性(1-10)",
            "category": "时刻类型"
        }
    ],
    "summary": "关键时刻总结"
}

要求：
- 识别最有价值的时刻
- 提供时间定位信息
- 说明重要性原因"""
)

# 流式分析基础提示词（用于流式返回）
register_prompt(
    "streaming_analysis",
    """请对以下内容进行详细分析，以易读的格式逐步输出分析结果：

内容: {{ content }}

分析类型: {{ analysis_type }}

请按以下顺序输出分析结果：
1. 内容概述
2. 主要观点
3. 情感分析
4. 分类和标签
5. 详细评估

注意：请使用清晰的段落分隔，便于阅读。"""
) 