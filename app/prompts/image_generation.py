"""
图像生成相关的提示词模板
"""

from .base import register_prompt

# 图像描述生成提示词
register_prompt(
    "image_description_generation",
    """请根据以下需求生成图像描述：

内容需求：{{ content_requirement }}
风格要求：{{ style_requirement }}
场景描述：{{ scene_description }}
情感色彩：{{ emotion }}
技术规格：{{ technical_specs }}

请输出详细的图像描述。"""
)

# 风格转换提示词
register_prompt(
    "style_transformation",
    """请将以下描述转换为目标风格：

原始描述：{{ original_description }}
目标风格：{{ target_style }}
风格强度：{{ style_intensity }}

请输出转换后的描述。"""
)

# 场景扩展提示词
register_prompt(
    "scene_expansion",
    """请扩展以下场景描述：

基础场景：{{ base_scene }}
扩展要求：{{ expansion_requirement }}
细节层次：{{ detail_level }}

请输出扩展后的场景描述。"""
)

# 艺术风格描述
register_prompt(
    "artistic_style_description",
    """请描述以下艺术风格：

风格名称：{{ style_name }}

请输出详细的风格描述。"""
)

# 图像质量优化
register_prompt(
    "image_quality_optimization",
    """请优化以下图像描述以提升质量：

原始描述：{{ original_description }}
优化目标：{{ optimization_goal }}

请输出优化后的描述。"""
)

# 系统角色定义
register_prompt(
    "image_description_expert_role",
    "你是一个专业的图像描述生成专家，能够创建详细且富有创意的图像描述。"
)

register_prompt(
    "art_style_expert_role",
    "你是一个专业的艺术风格专家，对各种艺术风格有深入理解。"
)

register_prompt(
    "visual_designer_role",
    "你是一个专业的视觉设计师，擅长图像构图和视觉表达。"
)

# 预设风格模板
register_prompt(
    "photorealistic_style",
    "photorealistic, highly detailed, professional photography, 8k resolution, sharp focus"
)

register_prompt(
    "cartoon_style",
    "cartoon style, vibrant colors, clean lines, simple shapes, playful illustration"
)

register_prompt(
    "oil_painting_style",
    "oil painting, artistic, textured brushstrokes, rich colors, classical art style"
)

register_prompt(
    "watercolor_style",
    "watercolor painting, soft colors, flowing brushstrokes, artistic, dreamy atmosphere"
)

register_prompt(
    "cyberpunk_style",
    "cyberpunk, neon lights, futuristic, high tech, urban dystopia, dramatic lighting"
)

register_prompt(
    "fantasy_style",
    "fantasy art, magical, ethereal, mystical atmosphere, otherworldly, enchanting"
) 