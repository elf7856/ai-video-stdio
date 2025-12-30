"""
TTS相关的提示词模板
"""

from .base import register_prompt

# TTS文本优化提示词
register_prompt(
    "tts_text_optimization",
    """请优化以下文本以适合TTS合成：

原始文本：{{ original_text }}
目标风格：{{ style }}
目标情感：{{ emotion }}
目标语速：{{ speed }}

请输出优化后的文本。"""
)

# 语音风格描述生成
register_prompt(
    "voice_style_description",
    """请描述以下语音风格：

风格类型：{{ style_type }}
情感色彩：{{ emotion }}
语速要求：{{ speed }}
音调要求：{{ pitch }}
目标受众：{{ audience }}

请输出详细的风格描述。"""
)

# 文本情感分析
register_prompt(
    "text_emotion_analysis",
    """请分析以下文本的情感：

文本内容：{{ text }}

请输出情感类型和强度。"""
)

# 多语言文本处理
register_prompt(
    "multilingual_text_processing",
    """请处理以下多语言文本：

文本：{{ text }}
目标语言：{{ target_language }}
发音要求：{{ pronunciation_requirements }}

请输出适合TTS的文本。"""
)

# 系统角色定义
register_prompt(
    "tts_optimizer_role",
    "你是一个专业的TTS文本优化专家，能够优化文本以提升语音合成质量。"
)

register_prompt(
    "voice_style_expert_role",
    "你是一个专业的语音风格设计专家。"
)

register_prompt(
    "emotion_analyst_role",
    "你是一个专业的情感分析专家。"
) 