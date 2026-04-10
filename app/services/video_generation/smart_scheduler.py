"""
智能视频生成调度器
使用 LLM 进行场景分析和策略推荐
集成素材库智能搜索和选择
"""

import logging
import json
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SceneComplexity(str, Enum):
    """场景复杂度"""
    SIMPLE = "simple"      # 简单场景（静态、单一主体）
    MEDIUM = "medium"      # 中等场景（动态、多个元素）
    COMPLEX = "complex"    # 复杂场景（特效、多场景切换）


class GenerationStrategy(str, Enum):
    """生成策略"""
    TEXT_TO_VIDEO = "text_to_video"          # 直接文本生成视频
    IMAGE_TO_VIDEO = "image_to_video"        # 先生成图片再生成视频
    MULTI_ATTEMPT = "multi_attempt"          # 多次尝试取最佳
    USE_STOCK_FOOTAGE = "use_stock_footage"  # 使用素材库视频


@dataclass
class SceneAnalysis:
    """场景分析结果"""
    complexity: SceneComplexity
    strategy: GenerationStrategy
    recommended_provider: str  # "aistudio" or "vertexai"
    estimated_cost: float
    estimated_time: float
    confidence: float  # 0-1，推荐的置信度
    reasoning: str = ""  # LLM 分析理由
    # 素材库相关
    use_stock_footage: bool = False  # 是否使用素材库
    stock_asset_url: Optional[str] = None  # 素材URL
    stock_asset_score: Optional[float] = None  # 素材评分
    cost_savings: float = 0.0  # 成本节省


class SmartVideoScheduler:
    """智能视频生成调度器（使用 LLM 分析）"""

    def __init__(self, enable_stock_footage: bool = True):
        """
        Args:
            enable_stock_footage: 是否启用素材库功能
        """
        self.enable_stock_footage = enable_stock_footage

        # 导入 LLM 服务
        from app.services.llm.service import llm_service
        from app.prompts.base import render_prompt
        self.llm_service = llm_service
        self.render_prompt = render_prompt

        # 延迟导入，避免循环依赖
        if enable_stock_footage:
            try:
                from app.services.media.smart_asset_manager import SmartAssetManager, AssetType
                self.asset_manager = SmartAssetManager()
                self.AssetType = AssetType
            except ImportError as e:
                logger.warning(f"无法导入素材管理器: {e}，素材库功能将被禁用")
                self.enable_stock_footage = False
                self.asset_manager = None
        else:
            self.asset_manager = None

        # 成本估算（美元/秒）
        self.cost_per_second = {
            "aistudio": 0.50,   # AI Studio 成本
            "vertexai": 0.75,   # Vertex AI 成本（更高质量）
        }

    def analyze_scene(self, prompt: str, duration: float = 5.0) -> SceneAnalysis:
        """
        使用 LLM 分析场景并推荐最佳策略

        Args:
            prompt: 视频提示词
            duration: 视频时长（秒）

        Returns:
            SceneAnalysis: 分析结果和推荐
        """
        try:
            # 使用 LLM 分析场景
            analysis_prompt = self.render_prompt(
                "scene_complexity_analysis",
                prompt=prompt,
                duration=duration
            )

            messages = [
                {"role": "user", "content": analysis_prompt}
            ]

            logger.info(f"🧠 使用 LLM 分析场景: {prompt[:50]}...")

            result = self.llm_service.call(
                messages,
                max_tokens=1000,
                temperature=0.3,  # 较低温度，保证分析稳定性
                response_format={"type": "json_object"}  # 要求返回 JSON
            )

            if not result["success"]:
                logger.error(f"LLM 分析失败: {result.get('error')}")
                # 降级到简单规则
                return self._fallback_analysis(prompt, duration)

            # 解析 LLM 返回的 JSON
            llm_analysis = json.loads(result["content"])

            # 提取分析结果
            complexity = SceneComplexity(llm_analysis.get("complexity", "medium"))
            strategy = GenerationStrategy(llm_analysis.get("recommended_strategy", "text_to_video"))
            provider = llm_analysis.get("recommended_provider", "aistudio")
            confidence = float(llm_analysis.get("confidence", 0.7))
            reasoning = llm_analysis.get("reasoning", "")

            # 估算成本和时间
            estimated_cost = self._estimate_cost(provider, duration)
            estimated_time = self._estimate_time(complexity, strategy)

            result = SceneAnalysis(
                complexity=complexity,
                strategy=strategy,
                recommended_provider=provider,
                estimated_cost=estimated_cost,
                estimated_time=estimated_time,
                confidence=confidence,
                reasoning=reasoning,
                use_stock_footage=False,
                stock_asset_url=None,
                stock_asset_score=None,
                cost_savings=0.0
            )

            logger.info(f"📊 LLM 场景分析完成:")
            logger.info(f"   复杂度: {complexity.value}")
            logger.info(f"   策略: {strategy.value}")
            logger.info(f"   推荐服务: {provider}")
            logger.info(f"   预估成本: ${estimated_cost:.2f}")
            logger.info(f"   预估时间: {estimated_time:.0f}秒")
            logger.info(f"   置信度: {confidence:.0%}")
            logger.info(f"   分析理由: {reasoning[:100]}...")

            return result

        except Exception as e:
            logger.error(f"LLM 场景分析异常: {e}", exc_info=True)
            # 降级到简单规则
            return self._fallback_analysis(prompt, duration)

    def _fallback_analysis(self, prompt: str, duration: float) -> SceneAnalysis:
        """
        降级分析方法（当 LLM 不可用时）
        使用简单规则进行分析
        """
        logger.warning("使用降级分析方法")

        # 简单规则：根据时长判断
        if duration > 8.0:
            complexity = SceneComplexity.COMPLEX
            strategy = GenerationStrategy.MULTI_ATTEMPT
            provider = "vertexai"
        elif duration > 5.0:
            complexity = SceneComplexity.MEDIUM
            strategy = GenerationStrategy.TEXT_TO_VIDEO
            provider = "aistudio"
        else:
            complexity = SceneComplexity.SIMPLE
            strategy = GenerationStrategy.TEXT_TO_VIDEO
            provider = "aistudio"

        estimated_cost = self._estimate_cost(provider, duration)
        estimated_time = self._estimate_time(complexity, strategy)

        return SceneAnalysis(
            complexity=complexity,
            strategy=strategy,
            recommended_provider=provider,
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
            confidence=0.5,  # 降级方法置信度较低
            reasoning="使用降级规则分析（LLM 不可用）",
            use_stock_footage=False,
            stock_asset_url=None,
            stock_asset_score=None,
            cost_savings=0.0
        )

    async def analyze_scene_with_stock(
        self,
        prompt: str,
        duration: float = 5.0
    ) -> SceneAnalysis:
        """
        分析场景并推荐最佳策略（包含素材库搜索）

        Args:
            prompt: 视频提示词
            duration: 视频时长（秒）

        Returns:
            SceneAnalysis: 分析结果和推荐（包含素材库信息）
        """
        # 1. 基础分析
        analysis = self.analyze_scene(prompt, duration)

        # 2. 🆕 搜索素材库
        if self.enable_stock_footage and self.asset_manager:
            try:
                logger.info(f"🔍 搜索素材库...")
                asset_result = await self.asset_manager.search_and_evaluate(
                    prompt,
                    duration,
                    self.AssetType.VIDEO
                )

                if not asset_result.use_ai_generation and asset_result.best_match:
                    # 找到合适的素材
                    analysis.use_stock_footage = True
                    analysis.stock_asset_url = asset_result.best_match.url
                    analysis.stock_asset_score = asset_result.best_match.score.overall
                    analysis.strategy = GenerationStrategy.USE_STOCK_FOOTAGE

                    # 计算成本节省
                    cost_info = self.asset_manager.estimate_cost_savings(
                        use_asset=True,
                        ai_generation_cost=analysis.estimated_cost
                    )
                    analysis.cost_savings = cost_info["savings"]
                    analysis.estimated_cost = 0.0  # 素材库免费

                    logger.info(f"✅ 找到合适素材:")
                    logger.info(f"   评分: {analysis.stock_asset_score:.2f}")
                    logger.info(f"   节省成本: ${analysis.cost_savings:.2f}")
                else:
                    logger.info(f"❌ 未找到合适素材，使用 AI 生成")
                    logger.info(f"   原因: {asset_result.reason}")

            except Exception as e:
                logger.warning(f"素材库搜索失败: {e}，将使用 AI 生成")

        return analysis

    def _estimate_cost(self, provider: str, duration: float) -> float:
        """估算成本"""
        return self.cost_per_second[provider] * duration

    def _estimate_time(
        self,
        complexity: SceneComplexity,
        strategy: GenerationStrategy
    ) -> float:
        """估算生成时间（秒）"""
        base_time = 60.0  # 基础生成时间

        # 复杂度影响
        if complexity == SceneComplexity.COMPLEX:
            base_time *= 1.5
        elif complexity == SceneComplexity.MEDIUM:
            base_time *= 1.2

        # 策略影响
        if strategy == GenerationStrategy.IMAGE_TO_VIDEO:
            base_time += 30.0  # 额外的图片生成时间
        elif strategy == GenerationStrategy.MULTI_ATTEMPT:
            base_time *= 2.0  # 多次尝试

        return base_time

    def should_use_image_reference(self, analysis: SceneAnalysis) -> bool:
        """是否应该使用参考图"""
        return (
            analysis.strategy == GenerationStrategy.IMAGE_TO_VIDEO or
            analysis.complexity == SceneComplexity.COMPLEX
        )

    def get_retry_strategy(
        self,
        failed_attempts: int,
        original_analysis: SceneAnalysis
    ) -> Dict:
        """获取重试策略"""
        if failed_attempts == 1:
            # 第一次失败：切换到 Image-to-Video
            return {
                "strategy": GenerationStrategy.IMAGE_TO_VIDEO,
                "provider": original_analysis.recommended_provider,
                "reason": "切换到参考图模式"
            }
        elif failed_attempts == 2:
            # 第二次失败：切换服务商
            new_provider = (
                "vertexai" if original_analysis.recommended_provider == "aistudio"
                else "aistudio"
            )
            return {
                "strategy": GenerationStrategy.IMAGE_TO_VIDEO,
                "provider": new_provider,
                "reason": f"切换到 {new_provider}"
            }
        else:
            # 第三次失败：降低要求
            return {
                "strategy": GenerationStrategy.TEXT_TO_VIDEO,
                "provider": "aistudio",
                "reason": "降低复杂度重试"
            }


# 使用示例
if __name__ == "__main__":
    scheduler = SmartVideoScheduler()

    # 测试不同场景
    test_prompts = [
        ("A cat sitting on a chair", 5.0),
        ("A person walking through a busy street", 6.0),
        ("Epic explosion with multiple characters and special effects", 8.0),
    ]

    for prompt, duration in test_prompts:
        print(f"\n{'='*60}")
        print(f"提示词: {prompt}")
        print(f"时长: {duration}秒")
        print(f"{'='*60}")

        analysis = scheduler.analyze_scene(prompt, duration)
        print(f"\n推荐策略: {analysis.strategy.value}")
        print(f"是否需要参考图: {scheduler.should_use_image_reference(analysis)}")
