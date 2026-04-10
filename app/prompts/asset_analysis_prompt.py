"""
素材分析相关的 LLM 提示词
"""

# 关键词提取提示词
KEYWORD_EXTRACTION_PROMPT = """你是一个专业的视频素材搜索专家。请分析以下场景描述，提取最适合用于素材库搜索的关键词。

场景描述：{prompt}

请提取 3-5 个最核心的搜索关键词，这些关键词应该：
1. 能够在素材库（如 Pexels）中找到相关视频或图片
2. 优先提取具体的对象、动作、场景元素
3. 避免抽象概念和形容词
4. 使用英文关键词（素材库主要是英文）

示例：
- "一个人在繁忙的城市街道上行走" → ["person", "walking", "city", "street", "urban"]
- "日落时分的海滩，海浪拍打着岸边" → ["beach", "sunset", "ocean", "waves", "shore"]
- "一只猫坐在窗台上看着外面" → ["cat", "sitting", "window", "indoor", "pet"]

请以 JSON 格式返回结果：
{{
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "primary_subject": "主要主体（如：person, cat, car）",
    "action": "主要动作（如：walking, sitting, flying）",
    "scene": "场景类型（如：city, nature, indoor）",
    "reasoning": "关键词选择的理由"
}}
"""

# 视频规格推断提示词
VIDEO_SPECS_INFERENCE_PROMPT = """你是一个专业的视频制作专家。请分析以下信息，推断最适合的视频规格。

场景描述：{prompt}
目标平台：{platform}

请从以下维度进行分析：

1. **视频方向** (orientation)
   - landscape: 横屏 16:9，适合 YouTube、Bilibili、电影风格
   - portrait: 竖屏 9:16，适合 TikTok、Instagram Story、手机观看
   - square: 方形 1:1，适合 Instagram Post

2. **视频分辨率** (size)
   - large: 4K (3840x2160)，适合高质量、电影级内容
   - medium: Full HD (1920x1080)，适合常规视频
   - small: HD (1280x720)，适合快速预览

推断规则：
- 如果提到"电影"、"宽屏"、"全景"、"风景" → landscape
- 如果提到"手机"、"竖屏"、"人物特写"、"TikTok" → portrait
- 如果提到"Instagram"、"方形" → square
- 如果平台是 TikTok/Reels/Shorts → portrait
- 如果平台是 YouTube/Bilibili → landscape
- 如果需要高质量、电影感 → large
- 常规内容 → medium

请以 JSON 格式返回结果：
{{
    "orientation": "landscape|portrait|square",
    "size": "large|medium|small",
    "confidence": 0.0-1.0,
    "reasoning": "推断依据"
}}
"""

# 特殊效果检测提示词
SPECIAL_EFFECTS_DETECTION_PROMPT = """你是一个专业的视频特效分析专家。请分析以下场景描述，判断是否需要特殊效果或 AI 生成。

场景描述：{prompt}

请判断这个场景是否包含以下特征：

1. **特殊视觉效果**
   - 爆炸、火焰、烟雾等特效
   - 魔法、变形、超自然现象
   - 科幻元素（激光、全息投影等）
   - 幻想元素（龙、魔法阵等）

2. **复杂动作或场景**
   - 高难度动作（飞行、悬浮、瞬移）
   - 不常见的场景组合
   - 特定的艺术风格（赛博朋克、蒸汽朋克等）

3. **素材库难以找到的内容**
   - 非常具体的场景组合
   - 特定的情绪或氛围
   - 创意性的概念场景

如果场景包含以上特征，建议使用 AI 生成；否则可以使用素材库。

请以 JSON 格式返回结果：
{{
    "requires_special_effects": true/false,
    "effect_types": ["explosion", "magic", "sci-fi", ...],
    "difficulty_level": "simple|medium|complex",
    "recommendation": "use_stock|use_ai_generation",
    "confidence": 0.0-1.0,
    "reasoning": "判断依据"
}}
"""
