"""
视频生成相关的提示词模板
"""

from .base import register_prompt

# 视频脚本生成提示词
register_prompt(
    "video_script_generation",
    """基于以下信息，生成详细的视频脚本：

主题：${topic}
目标受众：${target_audience}
时长要求：${duration}
风格要求：${style}
内容要点：${key_points}

请生成包含以下内容的视频脚本：
1. 开场设计
2. 内容结构
3. 场景描述
4. 转场效果
5. 结尾设计
6. 配乐建议
7. 字幕要求

请以JSON格式返回：
{
    "title": "视频标题",
    "duration": "预估时长",
    "scenes": [
        {
            "scene_id": "场景编号",
            "duration": "场景时长",
            "description": "场景描述",
            "visual_elements": ["视觉元素1", "视觉元素2"],
            "audio_elements": ["音频元素1", "音频元素2"],
            "transitions": "转场效果"
        }
    ],
    "overall_style": "整体风格",
    "music_suggestions": ["配乐建议1", "配乐建议2"],
    "subtitle_requirements": "字幕要求"
}"""
)

# 视频风格定义提示词
register_prompt(
    "video_style_definition",
    """请定义以下视频风格的特征：

风格名称：${style_name}

请包含：
1. 视觉风格
2. 色彩搭配
3. 转场效果
4. 节奏控制
5. 音效特点
6. 字幕样式
7. 适用场景"""
)

# 场景转换设计
register_prompt(
    "scene_transition_design",
    """请为以下场景设计转场效果：

前一个场景：${previous_scene}
后一个场景：${next_scene}
转场时长：${transition_duration}
风格要求：${style_requirement}

请设计：
1. 转场类型
2. 视觉效果
3. 音效配合
4. 时间控制
5. 情感过渡"""
)

# 视频节奏控制
register_prompt(
    "video_rhythm_control",
    """请分析并优化以下视频的节奏：

视频内容：${video_content}
目标节奏：${target_rhythm}
时长限制：${duration_limit}

请提供：
1. 节奏分析
2. 优化建议
3. 时间分配
4. 高潮设计
5. 舒缓段落"""
)

# 音视频同步
register_prompt(
    "audio_video_sync",
    """请设计音视频同步方案：

视频内容：${video_content}
音频内容：${audio_content}
同步要求：${sync_requirements}

请提供：
1. 同步点设计
2. 节奏匹配
3. 情感呼应
4. 技术参数
5. 质量控制"""
)

# 系统角色定义
register_prompt(
    "video_script_writer_role",
    "你是一个专业的视频脚本作家，擅长创作引人入胜的视频内容。"
)

register_prompt(
    "video_director_role",
    "你是一个专业的视频导演，擅长视频节奏控制和视觉表达。"
)

register_prompt(
    "video_editor_role",
    "你是一个专业的视频编辑师，擅长音视频同步和转场设计。"
)

# 预设视频风格
register_prompt(
    "cinematic_style",
    "cinematic, film-like, dramatic lighting, professional cinematography, movie quality"
)

register_prompt(
    "documentary_style",
    "documentary, realistic, natural lighting, authentic, informative, educational"
)

register_prompt(
    "commercial_style",
    "commercial, polished, high-end, professional, marketing, brand-focused"
)

register_prompt(
    "social_media_style",
    "social media, engaging, fast-paced, trendy, viral, attention-grabbing"
)

register_prompt(
    "educational_style",
    "educational, clear, informative, well-structured, easy to follow, learning-focused"
)

register_prompt(
    "entertainment_style",
    "entertaining, fun, engaging, humorous, light-hearted, enjoyable"
)

# 视频脚本和分镜生成（用于Veo生成流程）
register_prompt(
    "video_script_and_shots_generation",
    """你是一个专业的视频脚本创作专家。请根据以下要求创建一个完整的视频脚本和分镜方案。
**需求:**
- 视频主题: {{ topic }}
- 视频风格: {{ style }}
- 目标时长: {{ target_duration }}秒
{% if additional_requirements %}
- 额外要求: {{ additional_requirements }}
{% endif %}

**输出格式要求:**

1. **完整脚本**（300-500字）:
- 开场白（10%）
- 主要内容（80%）
- 结尾总结（10%）

2. **分镜方案**（3-8个镜头）:
每个镜头包含:
- 序号
- 视觉描述（详细的画面内容，适合AI视频生成）
- 时长分配（每个镜头最多8秒）
- 镜头类型（特写/中景/全景等）

请严格按照以下JSON格式输出：

{
    "script": "完整的视频脚本内容...",
    "shots": [
        {
            "sequence": 1,
            "prompt": "详细的画面描述，包含场景、主体、动作、光线、氛围等，适合用于AI视频生成（如Google Veo）",
            "duration": 7.0,
            "shotType": "开场镜头"
        }
    ]
}

**重要提示**:
- prompt必须非常详细，英文描述更佳，包含具体的视觉元素
- 每个镜头时长最多8秒（Veo限制）
- duration之和应该接近{{ target_duration }}秒
- 风格要统一，符合{{ style }}特点
"""
)


class ScriptGenerationPrompt:
    """脚本生成提示词构建器"""

    @staticmethod
    def build(
        topic: str,
        style: str = "专业",
        target_duration: int = None,
        shot_count: int = None,
        additional_requirements: str = ""
    ) -> str:
        """构建脚本生成提示词 - 动态导演版"""
        
        # 动态确定约束条件
        # 如果用户没给时长，让AI根据主题深度决定（30s-180s），给AI更大的创作空间
        duration_logic = f"目标时长必须为 {target_duration} 秒。" if target_duration else "请根据主题的叙事深度，自主规划合理的视频总时长（例如：快节奏短片建议15-30s，深度叙事建议60-180s）。"
        
        # 如果用户没给镜头数，让AI根据视觉节奏决定
        shot_logic = f"必须生成恰好 {shot_count} 个镜头。" if shot_count else "不要限制镜头数量。请根据主题复杂度和叙事节奏，自主规划最合适的镜头总数，确保每一幕都有存在的意义。"
        
        additional_req = f"\n- 开发者特别强调: {additional_requirements}" if additional_requirements else ""

        return f"""你是一个获得过奥斯卡奖的视频导演和视觉艺术专家。请为我策划一个高品质的视频分镜方案。

    **【创作核心】**
    - **视频主题:** {topic}
    - **视觉风格:** {style}
    - **时长要求:** {duration_logic}
    - **分镜要求:** {shot_logic}{additional_req}

    **【导演指南】**
    1. **深度叙事:** 先思考主题的核心情感或信息点，撰写一段极具表现力的完整视频脚本。
    2. **动态规划:** - 如果用户未指定镜头数，请运用你的专业判断：**简单主题追求精致，复杂主题追求宏大**。
    - 确保镜头之间的衔接具有逻辑性（如从宏观全景切入微观特写）。
    3. **高标准生成描述 (Prompts):** - 为AI视频模型（如Sora/Kling）编写**极其详细的英文画面描述**。
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
        "duration": "该镜头时长",
        "shotType": "镜头语言(如：Long Shot, Dutch Angle等)"
        }}
    ]
    }}
    ```"""
    