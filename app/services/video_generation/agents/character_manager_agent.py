"""
CharacterManagerAgent - 角色管理 Agent
负责识别和管理角色，生成角色参考图，确保跨镜头一致性
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from app.services.image.google_imagen_generator import GoogleImagenGenerator
from app.services.storage import get_storage_service

logger = logging.getLogger(__name__)


@dataclass
class CharacterAsset:
    """角色资产"""
    character_id: str
    name: str
    description: str  # 详细描述
    visual_keywords: List[str]  # 关键视觉特征
    reference_image_path: Optional[str] = None  # 参考图路径
    style_guide: str = ""  # 风格指南
    consistency_level: str = "high"  # 一致性要求：low/medium/high
    generation_strategy: str = "reference_only"  # 生成策略


@dataclass
class ConsistencyRule:
    """一致性规则"""
    rule_type: str  # character/color/style/environment
    description: str
    applies_to: List[str]  # 应用到哪些角色/元素


@dataclass
class CharacterManagementResult:
    """角色管理结果"""
    character_assets: List[CharacterAsset]
    consistency_rules: List[ConsistencyRule]
    global_reference_prompt: str  # 全局参考 prompt
    requires_character_ref: bool  # 是否需要角色参考
    estimated_generation_time: float  # 预估生成时间（秒）


class CharacterManagerAgent:
    """
    角色管理 Agent - 角色一致性保证

    职责：
    1. 识别剧本中的角色和主要物体
    2. 判断哪些需要一致性保证
    3. 生成角色参考图
    4. 维护角色库
    5. 提供一致性规则
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.image_generator = GoogleImagenGenerator()
        self.storage = get_storage_service()
        self.output_dir = output_dir or "outputs"

    async def manage_characters(
        self,
        characters: List[Dict[str, Any]],
        visual_style_guide: Dict[str, str],
        task_id: str,
        consistency_level: str = "high"
    ) -> CharacterManagementResult:
        """
        管理角色资产

        Args:
            characters: 角色列表（来自编剧Agent）
            visual_style_guide: 视觉风格指南
            task_id: 任务ID
            consistency_level: 一致性要求

        Returns:
            CharacterManagementResult: 角色管理结果
        """
        logger.info(f"🎭 角色管理Agent开始处理 {len(characters)} 个角色...")

        # 1. 筛选需要一致性保证的角色
        characters_needing_ref = [
            char for char in characters
            if char.get("consistency_required", True)
        ]

        logger.info(f"   需要生成参考图的角色: {len(characters_needing_ref)}")

        # 2. 为每个角色生成资产
        character_assets = []
        for char in characters:
            asset = await self._create_character_asset(
                character=char,
                visual_style_guide=visual_style_guide,
                task_id=task_id,
                consistency_level=consistency_level
            )
            character_assets.append(asset)

        # 3. 生成一致性规则
        consistency_rules = self._generate_consistency_rules(
            characters=characters,
            visual_style_guide=visual_style_guide
        )

        # 4. 构建全局参考 prompt
        global_reference_prompt = self._build_global_reference_prompt(
            character_assets=character_assets,
            visual_style_guide=visual_style_guide
        )

        # 5. 计算预估时间
        estimated_time = len(characters_needing_ref) * 15  # 每个角色约15秒

        result = CharacterManagementResult(
            character_assets=character_assets,
            consistency_rules=consistency_rules,
            global_reference_prompt=global_reference_prompt,
            requires_character_ref=len(characters_needing_ref) > 0,
            estimated_generation_time=estimated_time
        )

        logger.info(f"✅ 角色管理完成:")
        logger.info(f"   角色资产: {len(character_assets)}")
        logger.info(f"   一致性规则: {len(consistency_rules)}")
        logger.info(f"   需要参考图: {result.requires_character_ref}")

        return result

    async def _create_character_asset(
        self,
        character: Dict[str, Any],
        visual_style_guide: Dict[str, str],
        task_id: str,
        consistency_level: str
    ) -> CharacterAsset:
        """为单个角色创建资产"""

        char_name = character.get("name", "Unknown")
        char_description = character.get("description", "")
        visual_keywords = character.get("visual_keywords", [])
        consistency_required = character.get("consistency_required", True)

        logger.info(f"   处理角色: {char_name}")

        # 生成角色ID
        character_id = f"char_{char_name.lower().replace(' ', '_')}"

        # 决定生成策略
        if consistency_level == "high":
            generation_strategy = "first_frame_ref"
        elif consistency_level == "medium":
            generation_strategy = "reference_only"
        else:
            generation_strategy = "pure_text"

        # 生成参考图（如果需要）
        reference_image_path = None
        if consistency_required:
            reference_image_path = await self._generate_reference_image(
                character=character,
                visual_style_guide=visual_style_guide,
                task_id=task_id
            )

        # 构建风格指南
        style_guide = self._build_character_style_guide(
            character=character,
            visual_style_guide=visual_style_guide
        )

        asset = CharacterAsset(
            character_id=character_id,
            name=char_name,
            description=char_description,
            visual_keywords=visual_keywords,
            reference_image_path=reference_image_path,
            style_guide=style_guide,
            consistency_level=consistency_level,
            generation_strategy=generation_strategy
        )

        return asset

    async def _generate_reference_image(
        self,
        character: Dict[str, Any],
        visual_style_guide: Dict[str, str],
        task_id: str
    ) -> Optional[str]:
        """生成角色参考图"""

        char_name = character.get("name", "character")
        char_description = character.get("description", "")

        logger.info(f"      生成参考图: {char_name}")

        # 构建参考图生成 prompt
        reference_prompt = self._build_reference_image_prompt(
            character=character,
            visual_style_guide=visual_style_guide
        )

        try:
            # 生成图片
            img_path = await asyncio.to_thread(
                self.image_generator.generate_image,
                prompt=reference_prompt
            )

            if img_path:
                # 保存到项目目录
                safe_name = char_name.lower().replace(' ', '_')
                stored_path = self.storage.save(
                    img_path,
                    f"projects/{task_id}/characters/{safe_name}_reference.jpg"
                )

                logger.info(f"      ✅ 参考图已生成: {stored_path}")
                return stored_path
            else:
                logger.warning(f"      ❌ 参考图生成失败")
                return None

        except Exception as e:
            logger.error(f"生成参考图失败: {e}")
            return None

    def _build_reference_image_prompt(
        self,
        character: Dict[str, Any],
        visual_style_guide: Dict[str, str]
    ) -> str:
        """构建参考图生成 prompt"""

        char_description = character.get("description", "")
        visual_keywords = character.get("visual_keywords", [])

        # 提取风格关键词
        color_palette = visual_style_guide.get("color_palette", "")
        lighting_style = visual_style_guide.get("lighting_style", "soft natural light")
        visual_quality = visual_style_guide.get("visual_quality", "high quality")

        # 构建 prompt
        prompt = f"{char_description}, "

        # 添加视觉关键词
        if visual_keywords:
            prompt += f"{', '.join(visual_keywords)}, "

        # 添加风格
        prompt += f"{lighting_style}, {visual_quality}, "

        # 添加色彩（如果适用）
        if color_palette:
            prompt += f"{color_palette}, "

        # 添加参考图特定要求
        prompt += "character reference sheet, consistent design, front view, high detail, professional character design"

        return prompt

    def _build_character_style_guide(
        self,
        character: Dict[str, Any],
        visual_style_guide: Dict[str, str]
    ) -> str:
        """构建角色风格指南"""

        char_name = character.get("name", "")
        visual_keywords = character.get("visual_keywords", [])

        style_guide = f"角色 '{char_name}' 的一致性要求:\n"
        style_guide += f"- 核心特征: {', '.join(visual_keywords)}\n"
        style_guide += f"- 在所有镜头中必须保持这些特征不变\n"
        style_guide += f"- 使用相同的描述词: {character.get('description', '')}\n"

        return style_guide

    def _generate_consistency_rules(
        self,
        characters: List[Dict[str, Any]],
        visual_style_guide: Dict[str, str]
    ) -> List[ConsistencyRule]:
        """生成一致性规则"""

        rules = []

        # 角色一致性规则
        for char in characters:
            if char.get("consistency_required", True):
                rule = ConsistencyRule(
                    rule_type="character",
                    description=f"角色 '{char.get('name')}' 必须在所有镜头中保持一致的外观",
                    applies_to=[char.get("name", "")]
                )
                rules.append(rule)

        # 色彩一致性规则
        if "color_palette" in visual_style_guide:
            rule = ConsistencyRule(
                rule_type="color",
                description=f"所有镜头必须使用统一的色彩基调: {visual_style_guide['color_palette']}",
                applies_to=["all"]
            )
            rules.append(rule)

        # 光影一致性规则
        if "lighting_style" in visual_style_guide:
            rule = ConsistencyRule(
                rule_type="style",
                description=f"所有镜头必须使用统一的光影风格: {visual_style_guide['lighting_style']}",
                applies_to=["all"]
            )
            rules.append(rule)

        # 环境一致性规则
        if "environment" in visual_style_guide:
            rule = ConsistencyRule(
                rule_type="environment",
                description=f"环境设定必须保持一致: {visual_style_guide['environment']}",
                applies_to=["all"]
            )
            rules.append(rule)

        return rules

    def _build_global_reference_prompt(
        self,
        character_assets: List[CharacterAsset],
        visual_style_guide: Dict[str, str]
    ) -> str:
        """构建全局参考 prompt（用于所有镜头）"""

        # 提取所有角色的关键描述
        character_descriptions = []
        for asset in character_assets:
            if asset.visual_keywords:
                desc = f"{asset.name}: {', '.join(asset.visual_keywords)}"
                character_descriptions.append(desc)

        # 构建全局 prompt
        global_prompt = "Consistent visual style: "

        # 添加色彩
        if "color_palette" in visual_style_guide:
            global_prompt += f"{visual_style_guide['color_palette']}, "

        # 添加光影
        if "lighting_style" in visual_style_guide:
            global_prompt += f"{visual_style_guide['lighting_style']}, "

        # 添加质感
        if "visual_quality" in visual_style_guide:
            global_prompt += f"{visual_style_guide['visual_quality']}, "

        # 添加角色
        if character_descriptions:
            global_prompt += f"Characters: {'; '.join(character_descriptions)}"

        return global_prompt

    def get_character_reference_for_shot(
        self,
        shot_characters: List[str],
        character_assets: List[CharacterAsset]
    ) -> List[str]:
        """获取镜头所需的角色参考图路径"""

        reference_paths = []

        for char_name in shot_characters:
            # 查找对应的角色资产
            asset = next(
                (a for a in character_assets if a.name == char_name),
                None
            )

            if asset and asset.reference_image_path:
                reference_paths.append(asset.reference_image_path)

        return reference_paths


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        agent = CharacterManagerAgent()

        # 模拟角色数据（来自编剧Agent）
        characters = [
            {
                "name": "橙色小猫",
                "description": "A fluffy orange tabby cat with big green eyes and a bushy tail",
                "role": "主角",
                "consistency_required": True,
                "visual_keywords": ["orange", "fluffy", "green eyes", "bushy tail"],
                "personality": "好奇、活泼"
            },
            {
                "name": "城市街道",
                "description": "Modern city street with tall buildings",
                "role": "场景",
                "consistency_required": False,
                "visual_keywords": ["urban", "modern", "buildings"]
            }
        ]

        visual_style_guide = {
            "color_palette": "warm golden tones",
            "lighting_style": "soft natural light",
            "visual_quality": "cinematic",
            "overall_mood": "温馨治愈"
        }

        # 管理角色
        result = await agent.manage_characters(
            characters=characters,
            visual_style_guide=visual_style_guide,
            task_id="test_task_001",
            consistency_level="high"
        )

        print("=" * 80)
        print("角色管理结果")
        print("=" * 80)
        print(f"\n角色资产数: {len(result.character_assets)}")
        for asset in result.character_assets:
            print(f"\n  {asset.name}:")
            print(f"    ID: {asset.character_id}")
            print(f"    描述: {asset.description[:50]}...")
            print(f"    关键词: {', '.join(asset.visual_keywords)}")
            print(f"    参考图: {asset.reference_image_path or '无'}")
            print(f"    策略: {asset.generation_strategy}")

        print(f"\n一致性规则数: {len(result.consistency_rules)}")
        for rule in result.consistency_rules:
            print(f"  - [{rule.rule_type}] {rule.description}")

        print(f"\n全局参考 Prompt:")
        print(f"  {result.global_reference_prompt}")

        print(f"\n需要角色参考: {'是' if result.requires_character_ref else '否'}")
        print(f"预估生成时间: {result.estimated_generation_time}秒")

    asyncio.run(test())
