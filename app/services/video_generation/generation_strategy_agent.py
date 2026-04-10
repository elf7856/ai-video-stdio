"""
视频生成策略 Agent - 使用 LLM 智能决策
根据任务类型和需求，通过 LLM 分析并智能选择最佳生成策略
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from app.services.llm.service import LLMService, ProviderType

logger = logging.getLogger(__name__)


class GenerationStrategy(str, Enum):
    """生成策略类型"""
    PURE_STOCK = "pure_stock"                    # 纯素材库
    USER_IMAGE_TO_VIDEO = "user_image_to_video"  # 用户图片生成视频
    URL_IMAGE_TO_VIDEO = "url_image_to_video"    # URL图片生成视频
    REFERENCE_ONLY = "reference_only"            # 仅角色参考
    FIRST_FRAME_REFERENCE = "first_frame_ref"    # 第一帧+参考图
    FIRST_LAST_CHAIN = "first_last_chain"        # 第一帧-最后帧链
    PURE_TEXT_TO_VIDEO = "pure_text_to_video"    # 纯文本生成


class TaskType(str, Enum):
    """任务类型"""
    PRODUCT_INTRO = "product_intro"              # 产品介绍
    STORY_TELLING = "story_telling"              # 故事叙述
    TUTORIAL = "tutorial"                        # 教程演示
    SHOWCASE = "showcase"                        # 展示类
    ABSTRACT = "abstract"                        # 抽象内容
    CHARACTER_DRIVEN = "character_driven"        # 角色驱动
    SCENE_DRIVEN = "scene_driven"                # 场景驱动


@dataclass
class TaskContext:
    """任务上下文"""
    task_type: TaskType
    user_images: List[str] = None
    user_urls: List[str] = None
    has_specific_character: bool = False
    needs_continuity: bool = False
    scene_count: int = 1
    shot_count: int = 6
    budget_constraint: str = "medium"
    quality_requirement: str = "medium"

    # 新增：原始配置
    raw_config: Dict[str, Any] = None


@dataclass
class StrategyDecision:
    """策略决策结果"""
    strategy: GenerationStrategy
    reason: str
    steps: List[str]
    estimated_cost: float
    estimated_time: float
    requires_asset_search: bool
    requires_character_ref: bool
    requires_first_frames: bool
    confidence: float = 0.0  # LLM 决策的置信度


class GenerationStrategyAgent:
    """视频生成策略决策 Agent - LLM 驱动"""

    def __init__(self):
        self.llm = LLMService(provider=ProviderType.GOOGLE)

        # 策略成本估算（美元/镜头）
        self.strategy_costs = {
            GenerationStrategy.PURE_STOCK: 0.0,
            GenerationStrategy.USER_IMAGE_TO_VIDEO: 2.0,
            GenerationStrategy.URL_IMAGE_TO_VIDEO: 2.0,
            GenerationStrategy.REFERENCE_ONLY: 2.5,
            GenerationStrategy.FIRST_FRAME_REFERENCE: 3.5,
            GenerationStrategy.FIRST_LAST_CHAIN: 3.0,
            GenerationStrategy.PURE_TEXT_TO_VIDEO: 2.0,
        }

        # 策略时间估算（秒/镜头）
        self.strategy_times = {
            GenerationStrategy.PURE_STOCK: 5,
            GenerationStrategy.USER_IMAGE_TO_VIDEO: 60,
            GenerationStrategy.URL_IMAGE_TO_VIDEO: 70,
            GenerationStrategy.REFERENCE_ONLY: 65,
            GenerationStrategy.FIRST_FRAME_REFERENCE: 90,
            GenerationStrategy.FIRST_LAST_CHAIN: 80,
            GenerationStrategy.PURE_TEXT_TO_VIDEO: 60,
        }

    async def decide_strategy(self, config: Dict[str, Any]) -> StrategyDecision:
        """
        使用 LLM 智能决策生成策略

        Args:
            config: 生成配置

        Returns:
            StrategyDecision: 策略决策结果
        """
        logger.info(f"🤖 LLM Agent 开始分析任务...")

        # 🎉 首次用户特殊处理
        is_first_time = config.get("is_first_time_user", False)
        if is_first_time:
            logger.info("🎉 检测到首次用户，强制使用完备流程")
            # 强制使用 first_frame_ref 策略（最完备的流程）
            return StrategyDecision(
                strategy=GenerationStrategy.FIRST_FRAME_REFERENCE,
                reason="首次使用，采用最完备的AI生成流程，展示最佳效果和完整功能",
                steps=[
                    "生成角色参考图（保证角色一致性）",
                    "为每个镜头生成第一帧（精确控制起始画面）",
                    "使用 first_frame + reference 生成视频",
                    "实现最高质量的视频生成体验"
                ],
                estimated_cost=config.get("shot_count", 6) * 3.5,
                estimated_time=config.get("shot_count", 6) * 90,
                requires_asset_search=False,
                requires_character_ref=True,
                requires_first_frames=True,
                confidence=1.0
            )

        # 1. 使用 LLM 分析任务
        analysis = await self._llm_analyze_task(config)

        logger.info(f"✅ LLM 分析完成:")
        logger.info(f"   任务类型: {analysis.get('task_type')}")
        logger.info(f"   推荐策略: {analysis.get('strategy')}")
        logger.info(f"   置信度: {analysis.get('confidence', 0):.0%}")

        # 2. 构建决策结果
        decision = self._build_decision(analysis, config)

        logger.info(f"📊 最终决策:")
        logger.info(f"   策略: {decision.strategy.value}")
        logger.info(f"   原因: {decision.reason}")
        logger.info(f"   预估成本: ${decision.estimated_cost:.2f}")

        return decision

    async def _llm_analyze_task(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """使用 LLM 分析任务并推荐策略"""

        # 构建分析提示词
        prompt = self._build_analysis_prompt(config)

        try:
            # 调用 LLM
            response = self.llm.call(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3  # 较低的温度以获得更稳定的决策
            )

            # 解析 LLM 响应
            analysis = self._parse_llm_response(response["content"])

            return analysis

        except Exception as e:
            logger.error(f"LLM 分析失败: {e}")
            # 降级到基础规则
            return self._fallback_analysis(config)

    def _build_analysis_prompt(self, config: Dict[str, Any]) -> str:
        """构建 LLM 分析提示词"""

        # 提取配置信息
        topic = config.get("topic", "")
        shot_count = config.get("shot_count", 6)
        scene_count = config.get("scene_count", 1)
        budget = config.get("budget_constraint", "medium")
        user_images = config.get("user_images", [])
        user_urls = config.get("user_urls", [])
        generation_mode = config.get("generation_mode", "")

        # 策略说明
        strategies_info = """
可选的生成策略:

1. **pure_stock** (纯素材库)
   - 成本: $0/镜头
   - 适用: 通用场景、产品展示、预算紧张
   - 特点: 最经济，但创意受限
   - 要求: 场景在素材库中能找到

2. **user_image_to_video** (用户图片生成视频)
   - 成本: $2/镜头
   - 适用: 用户提供了图片或照片
   - 特点: 直接使用用户素材，个性化强
   - 要求: 用户必须提供图片

3. **url_image_to_video** (URL图片生成视频)
   - 成本: $2/镜头
   - 适用: 介绍网页产品、爬取内容
   - 特点: 自动提取网页内容
   - 要求: 用户必须提供URL

4. **pure_text_to_video** (纯文本生成视频)
   - 成本: $2/镜头
   - 适用: 抽象概念、无角色要求、创意内容
   - 特点: 最灵活，每个镜头独立
   - 要求: 不需要角色或场景一致性

5. **reference_only** (仅角色参考)
   - 成本: $2.5/镜头
   - 适用: 有特定角色但不需要严格连贯性、多场景切换
   - 特点: 角色外观一致，动作灵活，可并行生成
   - 要求: 需要生成角色参考图

6. **first_frame_ref** (第一帧+参考图)
   - 成本: $3.5/镜头
   - 适用: 需要精确控制起始姿势、角色一致性要求高
   - 特点: 最精确的控制，角色一致性最好
   - 要求: 需要生成角色参考图和每个镜头的第一帧

7. **first_last_chain** (第一帧-最后帧链)
   - 成本: $3/镜头
   - 适用: 单场景连续动作、需要动作流畅衔接
   - 特点: 动作最连贯，但必须顺序生成
   - 要求: 同一场景，动作连续
"""

        prompt = f"""你是一个视频生成策略专家。请分析以下任务并推荐最佳的生成策略。

任务信息:
- 主题: {topic}
- 镜头数量: {shot_count}
- 场景数量: {scene_count}
- 预算约束: {budget}
- 生成模式: {generation_mode or '未指定'}
- 用户提供图片: {"是 (" + str(len(user_images)) + "张)" if user_images else "否"}
- 用户提供URL: {"是 (" + str(len(user_urls)) + "个)" if user_urls else "否"}

{strategies_info}

请分析任务需求，回答以下问题:

1. **任务类型**: 这是什么类型的任务？
   - product_intro (产品介绍)
   - story_telling (故事叙述)
   - tutorial (教程演示)
   - showcase (展示类)
   - abstract (抽象内容)
   - character_driven (角色驱动)
   - scene_driven (场景驱动)

2. **关键特征**:
   - 是否有特定角色需要保持一致? (是/否)
   - 是否需要动作连贯性? (是/否)
   - 主要约束是什么? (成本/质量/时间/创意)

3. **推荐策略**: 从上述7种策略中选择最合适的一种

4. **理由**: 为什么推荐这个策略？(50字以内)

5. **置信度**: 你对这个推荐的置信度 (0-100)

请以 JSON 格式返回结果:
```json
{{
  "task_type": "任务类型",
  "has_specific_character": true/false,
  "needs_continuity": true/false,
  "main_constraint": "主要约束",
  "strategy": "推荐的策略",
  "reason": "推荐理由",
  "confidence": 85,
  "key_factors": ["关键因素1", "关键因素2"]
}}
```

重要提示:
- 如果用户提供了图片，优先考虑 user_image_to_video
- 如果用户提供了URL，优先考虑 url_image_to_video
- 如果预算是 low，优先考虑 pure_stock 或 pure_text_to_video
- 如果有特定角色且需要连贯性，考虑 first_frame_ref 或 first_last_chain
- 如果有特定角色但不需要严格连贯性，考虑 reference_only
- 如果是抽象内容或创意视频，考虑 pure_text_to_video
"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 提取 JSON 部分
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response_text.strip()

            analysis = json.loads(json_str)

            # 验证必要字段
            required_fields = ["task_type", "strategy", "reason"]
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"缺少必要字段: {field}")

            return analysis

        except Exception as e:
            logger.error(f"解析 LLM 响应失败: {e}")
            logger.error(f"响应内容: {response_text[:200]}")
            raise

    def _fallback_analysis(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """降级到基础规则分析"""
        logger.warning("使用降级规则进行分析")

        # 简单的规则判断
        topic = config.get("topic", "").lower()
        budget = config.get("budget_constraint", "medium")
        user_images = config.get("user_images", [])
        user_urls = config.get("user_urls", [])

        # 规则决策
        if user_images:
            strategy = "user_image_to_video"
            reason = "用户提供了图片"
        elif user_urls:
            strategy = "url_image_to_video"
            reason = "用户提供了URL"
        elif budget == "low":
            strategy = "pure_stock"
            reason = "预算紧张，优先素材库"
        else:
            strategy = "reference_only"
            reason = "通用场景，使用参考图模式"

        return {
            "task_type": "character_driven",
            "has_specific_character": False,
            "needs_continuity": False,
            "main_constraint": "cost",
            "strategy": strategy,
            "reason": reason,
            "confidence": 60,
            "key_factors": ["fallback_rule"]
        }

    def _build_decision(
        self,
        analysis: Dict[str, Any],
        config: Dict[str, Any]
    ) -> StrategyDecision:
        """根据 LLM 分析结果构建决策"""

        # 提取策略
        strategy_str = analysis.get("strategy")
        try:
            strategy = GenerationStrategy(strategy_str)
        except ValueError:
            logger.warning(f"未知策略 {strategy_str}，使用默认策略")
            strategy = GenerationStrategy.REFERENCE_ONLY

        # 计算成本和时间
        shot_count = config.get("shot_count", 6)
        estimated_cost = self.strategy_costs[strategy] * shot_count
        estimated_time = self.strategy_times[strategy] * shot_count

        # 确定需求
        requires_asset_search = (strategy == GenerationStrategy.PURE_STOCK)
        requires_character_ref = strategy in [
            GenerationStrategy.REFERENCE_ONLY,
            GenerationStrategy.FIRST_FRAME_REFERENCE
        ]
        requires_first_frames = strategy in [
            GenerationStrategy.FIRST_FRAME_REFERENCE,
            GenerationStrategy.FIRST_LAST_CHAIN
        ]

        # 生成执行步骤
        steps = self._generate_steps(strategy, analysis)

        # 提取置信度
        confidence = analysis.get("confidence", 0) / 100.0

        return StrategyDecision(
            strategy=strategy,
            reason=analysis.get("reason", ""),
            steps=steps,
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
            requires_asset_search=requires_asset_search,
            requires_character_ref=requires_character_ref,
            requires_first_frames=requires_first_frames,
            confidence=confidence
        )

    def _generate_steps(
        self,
        strategy: GenerationStrategy,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """根据策略生成执行步骤"""

        steps_map = {
            GenerationStrategy.PURE_STOCK: [
                "1. 分析每个镜头的场景需求",
                "2. 从 Pexels 素材库搜索匹配素材",
                "3. 评估素材质量和相关性",
                "4. 下载并使用高质量素材",
                "5. 如果找不到合适素材，降级到其他策略"
            ],
            GenerationStrategy.USER_IMAGE_TO_VIDEO: [
                "1. 加载用户提供的图片",
                "2. 分析图片内容和风格",
                "3. 使用图片作为 first_frame 生成视频",
                "4. 如果有多个镜头，可复用图片作为 reference"
            ],
            GenerationStrategy.URL_IMAGE_TO_VIDEO: [
                "1. 爬取用户提供的 URL",
                "2. 提取页面中的关键图片和文本",
                "3. 生成视频脚本",
                "4. 使用提取的图片作为参考生成视频"
            ],
            GenerationStrategy.PURE_TEXT_TO_VIDEO: [
                "1. 优化每个镜头的提示词",
                "2. 纯文本模式生成视频",
                "3. 所有镜头可并行生成",
                "4. 无需参考图或角色管理"
            ],
            GenerationStrategy.REFERENCE_ONLY: [
                "1. 识别视频中的角色/物体",
                "2. 生成高质量的角色/物体参考图",
                "3. 所有镜头使用 reference_images 模式",
                "4. 并行生成所有视频",
                "5. 保证角色外观一致"
            ],
            GenerationStrategy.FIRST_FRAME_REFERENCE: [
                "1. 生成角色参考图",
                "2. 为每个镜头生成 first_frame（使用角色参考保证一致性）",
                "3. 使用 first_frame + reference 生成视频",
                "4. 实现最高的角色一致性和姿势控制"
            ],
            GenerationStrategy.FIRST_LAST_CHAIN: [
                "1. 生成第一个镜头的视频",
                "2. 提取视频的 last_frame",
                "3. 使用 last_frame 作为下一个镜头的 first_frame",
                "4. 链式生成所有镜头",
                "5. 实现最佳的动作连贯性"
            ]
        }

        return steps_map.get(strategy, ["执行相应策略"])


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_llm_agent():
        agent = GenerationStrategyAgent()

        test_cases = [
            {
                "name": "产品介绍（低预算）",
                "config": {
                    "topic": "介绍新款智能手表的各项功能",
                    "shot_count": 6,
                    "budget_constraint": "low"
                }
            },
            {
                "name": "角色故事",
                "config": {
                    "topic": "一只橙色小猫在城市里的冒险故事，从清晨到傍晚",
                    "shot_count": 8,
                    "scene_count": 3,
                    "generation_mode": "continuous"
                }
            },
            {
                "name": "用户提供产品图",
                "config": {
                    "topic": "介绍这款耳机的特点",
                    "user_images": ["product.jpg", "detail.jpg"],
                    "shot_count": 4
                }
            }
        ]

        print("=" * 80)
        print("🧪 测试 LLM 驱动的策略 Agent")
        print("=" * 80)

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'=' * 80}")
            print(f"测试 {i}: {test['name']}")
            print(f"{'=' * 80}")

            try:
                decision = await agent.decide_strategy(test['config'])

                print(f"\n📊 决策结果:")
                print(f"   策略: {decision.strategy.value}")
                print(f"   原因: {decision.reason}")
                print(f"   置信度: {decision.confidence:.0%}")
                print(f"   预估成本: ${decision.estimated_cost:.2f}")
                print(f"   预估时间: {decision.estimated_time:.0f}秒")

                print(f"\n📝 执行步骤:")
                for step in decision.steps:
                    print(f"   {step}")

            except Exception as e:
                print(f"\n❌ 测试失败: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n{'=' * 80}")
        print("✅ 测试完成")
        print("=" * 80)

    asyncio.run(test_llm_agent())
