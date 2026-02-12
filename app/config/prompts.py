"""
Prompt 配置文件
集中管理所有 LLM prompts，便于维护和 A/B 测试
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Prompt 模板"""
    name: str
    template: str
    description: str
    version: str = "1.0"


class VideoScriptPrompts:
    """视频脚本生成 Prompts"""

    # 主 Prompt 模板
    MAIN_TEMPLATE = PromptTemplate(
        name="video_script_generation_v2",
        description="视频脚本和分镜生成 - 优化版",
        version="2.0",
        template="""你是一个获得过奥斯卡奖的视频导演和视觉艺术专家。请为我策划一个高品质的视频分镜方案。

**【创作核心】**
- **视频主题:** {topic}
- **视觉风格:** {style}
- **时长要求:** {duration_constraint}
- **分镜要求:** {shot_constraint}
{additional_requirements}

**【导演指南】**
1. **深度叙事:** 先思考主题的核心情感或信息点，撰写一段极具表现力的完整视频脚本。
2. **动态规划:**
   - 如果用户未指定镜头数，请运用你的专业判断：**简单主题追求精致，复杂主题追求宏大**。
   - 确保镜头之间的衔接具有逻辑性（如从宏观全景切入微观特写）。
3. **高标准生成描述 (Prompts):**
   - 为AI视频模型（如Sora/Kling/Veo）编写**极其详细的英文画面描述**。
   - 必须包含：主体动作(Action)、镜头运动(Camera Movement)、光影氛围(Lighting)、环境细节(Environment)。

**【输出协议 - 必须为严格的 JSON 格式】**
```json
{{
  "metadata": {{
    "chosen_duration": "AI最终规划的总时长(秒)",
    "chosen_shot_count": "AI最终规划的镜头总数",
    "pacing": "节奏类型(如：快节奏、抒情、叙事等)"
  }},
  "script": "完整的视频脚本内容...",
  "shots": [
    {{
      "sequence": 1,
      "prompt": "Professional English prompt including light, motion and composition...",
      "duration": 7.0,
      "shotType": "镜头语言(如：Long Shot, Dutch Angle等)"
    }}
  ]
}}
```

**【重要约束】**
- 每个镜头的 duration 不能超过 8.0 秒（AI视频生成限制）
- prompt 必须使用英文，且非常详细（至少50个单词）
- 所有镜头的 duration 总和应接近目标时长
- 必须严格按照 JSON 格式输出，不要添加任何额外的文字说明
"""
    )

    # 简化版 Prompt（用于快速生成）
    SIMPLE_TEMPLATE = PromptTemplate(
        name="video_script_generation_simple",
        description="简化版脚本生成 - 适合快速原型",
        version="1.0",
        template="""Create a video script for: {topic}

Style: {style}
Duration: {target_duration} seconds
Shots: {shot_count}

Output JSON format:
{{
  "script": "Full script text...",
  "shots": [
    {{
      "sequence": 1,
      "prompt": "Detailed English description...",
      "duration": 7.0,
      "shotType": "medium shot"
    }}
  ]
}}

Requirements:
- Each shot max 8 seconds
- Prompts in English, very detailed
- Total duration should match target
"""
    )

    @classmethod
    def build_prompt(
        cls,
        topic: str,
        style: str = "专业",
        target_duration: int = None,
        shot_count: int = None,
        additional_requirements: str = "",
        use_simple: bool = False
    ) -> str:
        """
        构建 prompt

        Args:
            topic: 视频主题
            style: 视觉风格
            target_duration: 目标时长（秒）
            shot_count: 镜头数量
            additional_requirements: 额外要求
            use_simple: 是否使用简化版

        Returns:
            完整的 prompt 字符串
        """
        # 选择模板
        template = cls.SIMPLE_TEMPLATE if use_simple else cls.MAIN_TEMPLATE

        # 构建约束条件
        if target_duration:
            duration_constraint = f"目标时长必须为 {target_duration} 秒。"
        else:
            duration_constraint = (
                "请根据主题的叙事深度，自主规划合理的视频总时长"
                "（例如：快节奏短片建议15-30s，深度叙事建议60-180s）。"
            )

        if shot_count:
            shot_constraint = f"必须生成恰好 {shot_count} 个镜头。"
        else:
            shot_constraint = (
                "不要限制镜头数量。请根据主题复杂度和叙事节奏，"
                "自主规划最合适的镜头总数，确保每一幕都有存在的意义。"
            )

        additional_req = (
            f"\n- **开发者特别强调:** {additional_requirements}"
            if additional_requirements
            else ""
        )

        # 填充模板
        if use_simple:
            return template.template.format(
                topic=topic,
                style=style,
                target_duration=target_duration or 60,
                shot_count=shot_count or 6
            )
        else:
            return template.template.format(
                topic=topic,
                style=style,
                duration_constraint=duration_constraint,
                shot_constraint=shot_constraint,
                additional_requirements=additional_req
            )


class VideoStylePrompts:
    """视频风格 Prompts"""

    STYLES: Dict[str, str] = {
        "专业": "professional, clean, corporate, polished",
        "电影感": "cinematic, film-like, dramatic lighting, professional cinematography, movie quality",
        "纪录片": "documentary, realistic, natural lighting, authentic, informative",
        "商业广告": "commercial, polished, high-end, professional, marketing, brand-focused",
        "社交媒体": "social media, engaging, fast-paced, trendy, viral, attention-grabbing",
        "教育": "educational, clear, informative, well-structured, easy to follow",
        "娱乐": "entertaining, fun, engaging, humorous, light-hearted, enjoyable"
    }

    @classmethod
    def get_style_description(cls, style: str) -> str:
        """获取风格描述"""
        return cls.STYLES.get(style, cls.STYLES["专业"])


class PromptConfig:
    """Prompt 配置管理"""

    # 当前使用的版本
    CURRENT_VERSION = "2.0"

    # 是否启用 fallback
    ENABLE_FALLBACK = True

    # 重试次数
    MAX_RETRIES = 2

    # 超时时间（秒）
    TIMEOUT = 60

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取配置"""
        return {
            "version": cls.CURRENT_VERSION,
            "enable_fallback": cls.ENABLE_FALLBACK,
            "max_retries": cls.MAX_RETRIES,
            "timeout": cls.TIMEOUT
        }
