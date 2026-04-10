"""
ScriptWriterAgent - 编剧 Agent
负责理解用户意图，补充完整剧本，提取关键元素
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from app.services.llm.service import LLMService, ProviderType

logger = logging.getLogger(__name__)


class NarrativeArc(str, Enum):
    """叙事结构类型"""
    THREE_ACT = "three_act"  # 三幕剧：开端-发展-结局
    HERO_JOURNEY = "hero_journey"  # 英雄之旅
    PROBLEM_SOLUTION = "problem_solution"  # 问题-解决方案
    BEFORE_AFTER = "before_after"  # 前后对比
    SHOWCASE = "showcase"  # 展示型（无明显叙事）
    TUTORIAL = "tutorial"  # 教程型


@dataclass
class Character:
    """角色信息"""
    name: str
    description: str  # 详细的视觉描述
    role: str  # 主角/配角/道具
    consistency_required: bool  # 是否需要一致性保证
    visual_keywords: List[str]  # 关键视觉特征
    personality: Optional[str] = None  # 性格特点（可选）


@dataclass
class Scene:
    """场景信息"""
    id: int
    location: str  # 地点
    time: str  # 时间（如：清晨、黄昏）
    mood: str  # 氛围（如：宁静、紧张）
    visual_style: str  # 视觉风格描述


@dataclass
class NarrativeStructure:
    """叙事结构"""
    arc_type: NarrativeArc
    setup: str  # 开端
    conflict: Optional[str] = None  # 冲突/发展
    climax: Optional[str] = None  # 高潮
    resolution: str = ""  # 结局


@dataclass
class ScriptMetadata:
    """剧本元数据"""
    characters: List[Character]
    scenes: List[Scene]
    narrative: NarrativeStructure
    theme: str  # 主题
    emotional_tone: str  # 情感基调
    target_audience: str  # 目标受众
    key_messages: List[str]  # 核心信息点


@dataclass
class ScriptResult:
    """编剧 Agent 输出结果"""
    script: str  # 完整剧本文本
    metadata: ScriptMetadata  # 结构化元数据
    visual_style_guide: Dict[str, str]  # 视觉风格指南
    estimated_duration: int  # 预估时长（秒）
    recommended_shot_count: int  # 推荐镜头数
    complexity_level: str  # 复杂度：simple/medium/complex


class ScriptWriterAgent:
    """
    编剧 Agent - 专业剧本创作

    职责：
    1. 理解用户意图和需求
    2. 补充完整的剧本内容
    3. 提取关键元素（角色、场景、情节、情感）
    4. 确保叙事连贯性
    5. 输出结构化的剧本元数据
    """

    def __init__(self):
        self.llm = LLMService(provider=ProviderType.GOOGLE)

    async def write_script(
        self,
        user_input: str,
        duration: Optional[int] = None,
        style: str = "专业",
        target_audience: str = "通用",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ScriptResult:
        """
        创作完整剧本

        Args:
            user_input: 用户输入的主题/需求
            duration: 目标时长（秒）
            style: 视觉风格
            target_audience: 目标受众
            additional_context: 额外上下文（如产品背景材料）

        Returns:
            ScriptResult: 完整的剧本结果
        """
        logger.info(f"📝 编剧Agent开始创作剧本: {user_input[:50]}...")

        # 1. 构建创作提示词
        prompt = self._build_script_prompt(
            user_input=user_input,
            duration=duration,
            style=style,
            target_audience=target_audience,
            additional_context=additional_context
        )

        # 2. 调用 LLM 创作剧本
        try:
            response = self.llm.call(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7  # 较高的温度以获得更有创意的剧本
            )

            # 3. 解析 LLM 响应
            script_data = self._parse_script_response(response["content"])

            # 4. 构建结果
            result = self._build_script_result(script_data)

            logger.info(f"✅ 剧本创作完成:")
            logger.info(f"   角色数: {len(result.metadata.characters)}")
            logger.info(f"   场景数: {len(result.metadata.scenes)}")
            logger.info(f"   叙事结构: {result.metadata.narrative.arc_type.value}")
            logger.info(f"   复杂度: {result.complexity_level}")

            return result

        except Exception as e:
            logger.error(f"剧本创作失败: {e}")
            raise

    def _build_script_prompt(
        self,
        user_input: str,
        duration: Optional[int],
        style: str,
        target_audience: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """构建剧本创作提示词"""

        # 处理额外上下文
        context_section = ""
        if additional_context:
            if "product_background" in additional_context:
                context_section = f"""
**【产品背景材料】**
以下是产品的详细信息，请在剧本中准确体现：

{additional_context['product_background']}

---
"""
            elif "reference_materials" in additional_context:
                context_section = f"""
**【参考材料】**
{additional_context['reference_materials']}

---
"""

        # 时长建议
        duration_guidance = ""
        if duration:
            duration_guidance = f"目标时长约为 {duration} 秒。"
        else:
            duration_guidance = "请根据内容深度自主规划合理的时长（建议15-90秒）。"

        prompt = f"""你是一位获得过艾美奖的专业编剧和叙事专家。请为以下视频创作一个完整、专业的剧本。

{context_section}

**【创作任务】**
- **用户需求**: {user_input}
- **视觉风格**: {style}
- **目标受众**: {target_audience}
- **时长要求**: {duration_guidance}

**【编剧职责】**

作为专业编剧，你需要：

1. **深度理解用户意图**
   - 分析用户真正想要表达的核心信息
   - 识别潜在的情感诉求和传播目标
   - 补充用户未明确但必要的细节

2. **构建完整叙事**
   - 选择合适的叙事结构（三幕剧/英雄之旅/问题解决/前后对比/展示型/教程型）
   - 确保故事有清晰的开端、发展、高潮、结局
   - 创造情感起伏，引发观众共鸣

3. **角色与场景设计**
   - 如果有角色，详细描述其视觉特征（外观、服装、特征）
   - 如果有产品，详细描述其外观（颜色、材质、形状）
   - 设计具体的场景（地点、时间、氛围）
   - 确保角色和场景在整个视频中保持一致

4. **视觉风格统一**
   - 定义整体的视觉风格指南（色彩、光影、质感）
   - 确保所有场景符合统一的视觉风格
   - 考虑视频生成模型的能力限制

**【叙事结构类型】**

根据内容选择合适的叙事结构：

- **three_act**: 三幕剧（开端-发展-结局），适合故事类内容
- **hero_journey**: 英雄之旅，适合角色成长类故事
- **problem_solution**: 问题-解决方案，适合产品介绍
- **before_after**: 前后对比，适合效果展示
- **showcase**: 展示型，适合产品/场景展示
- **tutorial**: 教程型，适合操作演示

**【角色设计原则】**

如果视频中有角色或主要物体：

1. **详细的视觉描述**
   - 人物：年龄、性别、发型、服装、体型、肤色、特征
   - 产品：颜色、材质、形状、尺寸、品牌标识
   - 动物：种类、颜色、体型、特征

2. **一致性关键词**
   - 提取3-5个核心视觉关键词
   - 这些关键词将在所有镜头中使用
   - 例如："orange tabby cat, fluffy tail, big green eyes"

3. **角色作用**
   - 主角：需要高度一致性
   - 配角：需要中等一致性
   - 道具/背景：低一致性要求

**【场景设计原则】**

1. **具体化**
   - 不要说"一个房间"，要说"现代简约风格的客厅，白色墙壁，木质地板"
   - 不要说"户外"，要说"城市公园，绿树成荫，阳光明媚"

2. **一致性**
   - 如果在同一场景，环境描述必须完全一致
   - 场景切换要有逻辑性

3. **氛围营造**
   - 通过时间、天气、光线营造氛围
   - 氛围要服务于叙事和情感表达

**【输出格式 - 严格的 JSON】**

```json
{{
  "script": "完整的视频剧本文本，包含旁白、场景描述、情感基调...",

  "metadata": {{
    "theme": "核心主题（一句话概括）",
    "emotional_tone": "情感基调（如：温馨、激励、专业、有趣）",
    "target_audience": "目标受众",
    "key_messages": ["核心信息点1", "核心信息点2", "核心信息点3"],

    "narrative": {{
      "arc_type": "叙事结构类型（从上述类型中选择）",
      "setup": "开端描述",
      "conflict": "冲突/发展描述（如果适用）",
      "climax": "高潮描述（如果适用）",
      "resolution": "结局描述"
    }},

    "characters": [
      {{
        "name": "角色名称（如：橙色小猫、iPhone 15 Pro、主人公）",
        "description": "详细的视觉描述（100字以内，英文）",
        "role": "主角/配角/道具",
        "consistency_required": true/false,
        "visual_keywords": ["关键词1", "关键词2", "关键词3"],
        "personality": "性格特点（可选）"
      }}
    ],

    "scenes": [
      {{
        "id": 1,
        "location": "具体地点描述",
        "time": "时间（如：清晨、黄昏、正午）",
        "mood": "氛围（如：宁静、紧张、欢快）",
        "visual_style": "该场景的视觉风格描述"
      }}
    ]
  }},

  "visual_style_guide": {{
    "color_palette": "整体色彩基调（英文描述，如：warm golden tones, cool blue and silver）",
    "lighting_style": "光影风格（英文描述，如：soft natural light, dramatic shadows）",
    "visual_quality": "画面质感（英文描述，如：cinematic, documentary style）",
    "camera_style": "镜头风格（如：稳定、动态、手持）",
    "overall_mood": "整体氛围（中文）"
  }},

  "production_notes": {{
    "estimated_duration": 60,
    "recommended_shot_count": 6,
    "complexity_level": "simple/medium/complex",
    "special_requirements": ["特殊要求1", "特殊要求2"],
    "consistency_priorities": ["需要重点保证一致性的元素"]
  }}
}}
```

**【质量标准】**

1. ✅ 剧本必须完整、连贯、有情感起伏
2. ✅ 角色描述必须详细、具体、可视化
3. ✅ 场景描述必须具体、有氛围感
4. ✅ 视觉风格指南必须统一、明确
5. ✅ 叙事结构必须清晰、符合逻辑
6. ✅ 核心信息点必须在剧本中体现

**【创意要求】**

- 不要生成平淡无奇的剧本，要有创意和亮点
- 考虑视觉冲击力和情感共鸣
- 确保内容适合视频媒介（而非文字媒介）
- 每个场景都要有画面感

**【重要提醒】**

- 如果有产品背景材料，必须准确体现产品特点，不要编造
- 如果有角色，必须在所有场景中保持一致的描述
- 视觉风格指南将被后续的导演Agent使用，必须详细明确
- 复杂度评估要考虑视频生成的难度（特效、动作、场景切换等）

现在，请开始创作！
"""

        return prompt

    def _parse_script_response(self, response_text: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 提取 JSON 部分
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response_text.strip()

            script_data = json.loads(json_str)

            # 验证必要字段
            required_fields = ["script", "metadata", "visual_style_guide", "production_notes"]
            for field in required_fields:
                if field not in script_data:
                    raise ValueError(f"缺少必要字段: {field}")

            return script_data

        except Exception as e:
            logger.error(f"解析剧本响应失败: {e}")
            logger.error(f"响应内容: {response_text[:500]}")
            raise

    def _build_script_result(self, script_data: Dict[str, Any]) -> ScriptResult:
        """构建剧本结果对象"""

        # 解析角色
        characters = []
        for char_data in script_data["metadata"].get("characters", []):
            characters.append(Character(
                name=char_data["name"],
                description=char_data["description"],
                role=char_data["role"],
                consistency_required=char_data.get("consistency_required", True),
                visual_keywords=char_data.get("visual_keywords", []),
                personality=char_data.get("personality")
            ))

        # 解析场景
        scenes = []
        for scene_data in script_data["metadata"].get("scenes", []):
            scenes.append(Scene(
                id=scene_data["id"],
                location=scene_data["location"],
                time=scene_data["time"],
                mood=scene_data["mood"],
                visual_style=scene_data["visual_style"]
            ))

        # 解析叙事结构
        narrative_data = script_data["metadata"]["narrative"]
        arc_type_str = narrative_data.get("arc_type", "")
        try:
            arc_type = NarrativeArc(arc_type_str)
        except ValueError:
            logger.warning(f"未知叙事结构类型: '{arc_type_str}'，降级为 showcase")
            arc_type = NarrativeArc.SHOWCASE
        narrative = NarrativeStructure(
            arc_type=arc_type,
            setup=narrative_data.get("setup", ""),
            conflict=narrative_data.get("conflict"),
            climax=narrative_data.get("climax"),
            resolution=narrative_data.get("resolution", "")
        )

        # 构建元数据
        metadata = ScriptMetadata(
            characters=characters,
            scenes=scenes,
            narrative=narrative,
            theme=script_data["metadata"]["theme"],
            emotional_tone=script_data["metadata"]["emotional_tone"],
            target_audience=script_data["metadata"]["target_audience"],
            key_messages=script_data["metadata"]["key_messages"]
        )

        # 构建结果
        result = ScriptResult(
            script=script_data["script"],
            metadata=metadata,
            visual_style_guide=script_data["visual_style_guide"],
            estimated_duration=script_data["production_notes"]["estimated_duration"],
            recommended_shot_count=script_data["production_notes"]["recommended_shot_count"],
            complexity_level=script_data["production_notes"]["complexity_level"]
        )

        return result

    def to_dict(self, result: ScriptResult) -> Dict[str, Any]:
        """将结果转换为字典（用于序列化）"""
        return {
            "script": result.script,
            "metadata": {
                "theme": result.metadata.theme,
                "emotional_tone": result.metadata.emotional_tone,
                "target_audience": result.metadata.target_audience,
                "key_messages": result.metadata.key_messages,
                "narrative": {
                    "arc_type": result.metadata.narrative.arc_type.value,
                    "setup": result.metadata.narrative.setup,
                    "conflict": result.metadata.narrative.conflict,
                    "climax": result.metadata.narrative.climax,
                    "resolution": result.metadata.narrative.resolution
                },
                "characters": [
                    {
                        "name": char.name,
                        "description": char.description,
                        "role": char.role,
                        "consistency_required": char.consistency_required,
                        "visual_keywords": char.visual_keywords,
                        "personality": char.personality
                    }
                    for char in result.metadata.characters
                ],
                "scenes": [
                    {
                        "id": scene.id,
                        "location": scene.location,
                        "time": scene.time,
                        "mood": scene.mood,
                        "visual_style": scene.visual_style
                    }
                    for scene in result.metadata.scenes
                ]
            },
            "visual_style_guide": result.visual_style_guide,
            "production_notes": {
                "estimated_duration": result.estimated_duration,
                "recommended_shot_count": result.recommended_shot_count,
                "complexity_level": result.complexity_level
            }
        }


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        agent = ScriptWriterAgent()

        # 测试案例1：简单故事
        result = await agent.write_script(
            user_input="一只橙色小猫在城市里的冒险",
            duration=60,
            style="温馨治愈",
            target_audience="儿童和家庭"
        )

        print("=" * 80)
        print("剧本创作结果")
        print("=" * 80)
        print(f"\n📝 剧本:\n{result.script}\n")
        print(f"🎭 角色数: {len(result.metadata.characters)}")
        for char in result.metadata.characters:
            print(f"  - {char.name} ({char.role}): {char.description[:50]}...")
        print(f"\n🎬 场景数: {len(result.metadata.scenes)}")
        print(f"📖 叙事结构: {result.metadata.narrative.arc_type.value}")
        print(f"⏱️  预估时长: {result.estimated_duration}秒")
        print(f"🎥 推荐镜头数: {result.recommended_shot_count}")
        print(f"📊 复杂度: {result.complexity_level}")

    asyncio.run(test())
