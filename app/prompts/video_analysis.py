"""
视频分析相关的提示词模板
"""

from .base import register_prompt

# 视频内容分析提示词
register_prompt(
    "video_analysis",
    """请分析以下视频内容，并提供详细的分析报告：

视频信息：
- 标题: {{ title }}
- 时长: {{ duration }}秒
- 分辨率: {{ resolution }}
- 文件大小: {{ file_size }}字节

请从以下方面进行分析：

1. 内容类型和主题
2. 目标受众
3. 情感色彩和氛围
4. 关键场景和元素
5. 可能的编辑建议
6. 适合的标签

请以JSON格式返回结果，包含以下字段：
{
    "content_type": "视频内容类型",
    "theme": "主题描述",
    "target_audience": "目标受众",
    "emotion": "情感色彩",
    "key_scenes": ["关键场景1", "关键场景2"],
    "key_elements": ["关键元素1", "关键元素2"],
    "editing_suggestions": ["编辑建议1", "编辑建议2"],
    "tags": ["标签1", "标签2", "标签3"],
    "summary": "内容摘要"
}"""
)

# 编辑指令理解提示词
register_prompt(
    "edit_instruction_understanding",
    """基于以下视频上下文，理解用户的编辑指令：

视频上下文：
{{ video_context }}

用户指令：{{ instruction }}

请分析这个编辑指令，并返回以下信息：
{
    "edit_type": "编辑类型 (insert/replace/delete/style_change)",
    "target_location": "目标位置描述",
    "content_needed": "需要生成的内容类型",
    "style_preferences": "风格偏好",
    "technical_requirements": "技术要求",
    "estimated_duration": "预估时长",
    "complexity": "复杂度 (low/medium/high)"
}"""
)

# 内容描述生成提示词
register_prompt(
    "content_description_generation",
    """基于以下信息，生成详细的内容描述：

编辑指令：{{ instruction }}
上下文信息：{{ context }}

请生成一个详细的内容描述，用于后续的内容生成。"""
)

# 系统角色定义
register_prompt(
    "video_analyst_role",
    "你是一个专业的视频内容分析师，能够深入分析视频的各个方面。"
)

register_prompt(
    "video_editor_role", 
    "你是一个专业的视频编辑助手，能够理解用户的编辑需求。"
)

register_prompt(
    "content_generator_role",
    "你是一个专业的内容描述生成器。"
) 