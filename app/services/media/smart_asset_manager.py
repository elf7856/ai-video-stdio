"""
智能素材管理器
根据场景自动搜索、评分和选择最佳素材
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from google import genai
from google.genai import types

from app.services.media.pexels import PexelsClient
from app.services.media.shutterstock import ShutterstockClient
from app.prompts.asset_analysis_prompt import (
    KEYWORD_EXTRACTION_PROMPT,
    VIDEO_SPECS_INFERENCE_PROMPT,
    SPECIAL_EFFECTS_DETECTION_PROMPT
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AssetSource(str, Enum):
    """素材来源"""
    PEXELS = "pexels"
    SHUTTERSTOCK = "shutterstock"
    PIXABAY = "pixabay"
    UNSPLASH = "unsplash"
    LOCAL = "local"
    AI_GENERATED = "ai_generated"


class AssetType(str, Enum):
    """素材类型"""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"


@dataclass
class AssetScore:
    """素材评分"""
    relevance: float  # 相关性 0-1
    quality: float    # 质量 0-1
    duration_match: float  # 时长匹配度 0-1
    overall: float    # 综合评分 0-1

    def __post_init__(self):
        # 计算综合评分
        self.overall = (
            self.relevance * 0.5 +      # 相关性权重 50%
            self.quality * 0.3 +         # 质量权重 30%
            self.duration_match * 0.2    # 时长匹配权重 20%
        )


@dataclass
class Asset:
    """素材信息"""
    id: str
    source: AssetSource
    type: AssetType
    url: str
    thumbnail_url: Optional[str]
    title: str
    description: Optional[str]
    duration: Optional[float]  # 视频时长（秒）
    width: Optional[int]
    height: Optional[int]
    author: Optional[str]
    license: Optional[str]
    score: Optional[AssetScore] = None


@dataclass
class AssetSearchResult:
    """素材搜索结果"""
    query: str
    assets: List[Asset]
    best_match: Optional[Asset]  # 最佳匹配
    use_ai_generation: bool  # 是否建议使用 AI 生成
    reason: str  # 决策原因


class SmartAssetManager:
    """智能素材管理器"""

    def __init__(self):
        self.pexels = PexelsClient()
        self.shutterstock = ShutterstockClient()

        self._client = genai.Client(api_key=settings.google_api_key)

        # 质量阈值
        self.min_quality_score = 0.6
        self.min_relevance_score = 0.5

    async def search_and_evaluate(
        self,
        prompt: str,
        duration: float,
        asset_type: AssetType = AssetType.VIDEO,
        orientation: str = None,  # "landscape", "portrait", "square"
        min_size: str = None  # "large" (4K), "medium" (Full HD), "small" (HD)
    ) -> AssetSearchResult:
        """
        搜索并评估素材

        Args:
            prompt: 场景描述
            duration: 需要的时长
            asset_type: 素材类型
            orientation: 视频方向 - "landscape"（横屏16:9）, "portrait"（竖屏9:16）, "square"（方形1:1）
            min_size: 最小分辨率 - "large"(4K), "medium"(Full HD), "small"(HD)

        Returns:
            AssetSearchResult: 搜索结果和建议
        """
        logger.info(f"🔍 搜索素材: {prompt[:50]}...")
        if orientation:
            logger.info(f"   方向筛选: {orientation}")
        if min_size:
            logger.info(f"   分辨率筛选: {min_size}")

        # 1. 提取关键词（使用 LLM）
        keywords = await self._extract_keywords(prompt)
        search_query = " ".join(keywords[:3])  # 使用前3个关键词

        # 2. 搜索素材（带筛选条件）
        assets = await self._search_assets(
            search_query,
            asset_type,
            orientation=orientation,
            min_size=min_size
        )

        if not assets:
            logger.info(f"❌ 未找到素材，建议使用 AI 生成")
            return AssetSearchResult(
                query=search_query,
                assets=[],
                best_match=None,
                use_ai_generation=True,
                reason="未找到相关素材"
            )

        # 3. 评分
        scored_assets = self._score_assets(assets, prompt, duration)

        # 4. 选择最佳匹配
        best_match = self._select_best_match(scored_assets)

        # 5. 决策：使用素材 vs AI 生成（使用 LLM）
        use_ai = await self._should_use_ai_generation(best_match, prompt)

        reason = self._get_decision_reason(best_match, use_ai)

        logger.info(
            f"✅ 找到 {len(scored_assets)} 个素材，"
            f"最佳评分: {best_match.score.overall:.2f}，"
            f"建议: {'AI生成' if use_ai else '使用素材'}"
        )

        return AssetSearchResult(
            query=search_query,
            assets=scored_assets,
            best_match=best_match if not use_ai else None,
            use_ai_generation=use_ai,
            reason=reason
        )

    async def _extract_keywords(self, prompt: str) -> List[str]:
        """使用 LLM 提取关键词"""
        try:
            extraction_prompt = KEYWORD_EXTRACTION_PROMPT.format(prompt=prompt)

            response = await self._client.aio.models.generate_content(
                model='gemini-3-flash',
                contents=extraction_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)
            keywords = result.get("keywords", [])

            logger.info(f"LLM 提取关键词: {keywords}")
            logger.debug(f"  主体: {result.get('primary_subject')}")
            logger.debug(f"  动作: {result.get('action')}")
            logger.debug(f"  场景: {result.get('scene')}")

            return keywords

        except Exception as e:
            logger.error(f"LLM 关键词提取失败: {e}")
            # 降级方案：使用前3个单词
            words = prompt.lower().split()[:3]
            fallback_keywords = [w for w in words if len(w) > 3]
            logger.info(f"使用降级方案: {fallback_keywords}")
            return fallback_keywords

    async def infer_video_specs(
        self,
        prompt: str = None,
        platform: str = None
    ) -> Dict[str, str]:
        """
        智能推断视频规格（方向和分辨率）- 使用 LLM

        Args:
            prompt: 场景描述（可从中推断）
            platform: 目标平台 - "tiktok", "instagram", "youtube", "twitter", "web"

        Returns:
            Dict with "orientation" and "size" keys
        """
        # 默认值
        specs = {"orientation": "landscape", "size": "medium"}

        # 如果没有提供任何信息，返回默认值
        if not prompt and not platform:
            return specs

        try:
            # 使用 LLM 推断
            inference_prompt = VIDEO_SPECS_INFERENCE_PROMPT.format(
                prompt=prompt or "无场景描述",
                platform=platform or "无指定平台"
            )

            response = await self._client.aio.models.generate_content(
                model='gemini-3-flash',
                contents=inference_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)

            specs["orientation"] = result.get("orientation", "landscape")
            specs["size"] = result.get("size", "medium")

            logger.info(f"LLM 推断视频规格: {specs}")
            logger.debug(f"  置信度: {result.get('confidence')}")
            logger.debug(f"  推理: {result.get('reasoning')}")

            return specs

        except Exception as e:
            logger.error(f"LLM 视频规格推断失败: {e}")

            # 降级方案：基于平台的简单规则
            if platform:
                platform_lower = platform.lower()

                if platform_lower in ["tiktok", "instagram-story", "reels", "shorts"]:
                    specs["orientation"] = "portrait"
                    specs["size"] = "medium"
                elif platform_lower in ["youtube", "bilibili", "web"]:
                    specs["orientation"] = "landscape"
                    specs["size"] = "large"
                elif platform_lower in ["instagram-post", "square"]:
                    specs["orientation"] = "square"
                    specs["size"] = "medium"

            logger.info(f"使用降级方案: {specs}")
            return specs

    async def _search_assets(
        self,
        query: str,
        asset_type: AssetType,
        orientation: str = None,
        min_size: str = None
    ) -> List[Asset]:
        """搜索素材（支持筛选条件）- 并行搜索多个素材源"""
        import asyncio

        assets = []

        # 并行搜索多个素材源
        if asset_type == AssetType.VIDEO:
            # 并行搜索 Pexels 和 Shutterstock
            pexels_task = self.pexels.search_videos(
                query,
                per_page=10,
                orientation=orientation,
                size=min_size
            )
            shutterstock_task = self.shutterstock.search_videos(
                query,
                per_page=10,
                orientation=orientation,
                resolution=min_size
            )

            # 等待所有搜索完成
            pexels_videos, shutterstock_videos = await asyncio.gather(
                pexels_task,
                shutterstock_task,
                return_exceptions=True
            )

            # 处理 Pexels 结果
            if isinstance(pexels_videos, list):
                for video in pexels_videos:
                    video_files = video.get("video_files", [])
                    if not video_files:
                        continue

                    # 选择 HD 质量
                    hd_file = next(
                        (f for f in video_files if f.get("quality") == "hd"),
                        video_files[0]
                    )

                    assets.append(Asset(
                        id=f"pexels_{video['id']}",
                        source=AssetSource.PEXELS,
                        type=AssetType.VIDEO,
                        url=hd_file["link"],
                        thumbnail_url=video.get("image"),
                        title=f"Pexels Video {video['id']}",
                        description=None,
                        duration=float(video.get("duration", 0)),
                        width=hd_file.get("width"),
                        height=hd_file.get("height"),
                        author=video.get("user", {}).get("name"),
                        license="Pexels License (Free)"
                    ))

            # 处理 Shutterstock 结果
            if isinstance(shutterstock_videos, list):
                for video in shutterstock_videos:
                    # Shutterstock 返回的数据结构
                    assets_data = video.get("assets", {})
                    preview_urls = assets_data.get("preview_mp4", {})

                    # 获取预览视频 URL
                    preview_url = preview_urls.get("url") if preview_urls else None

                    # 获取缩略图
                    thumb_data = assets_data.get("thumb_jpg", {})
                    thumbnail_url = thumb_data.get("url") if thumb_data else None

                    assets.append(Asset(
                        id=f"shutterstock_{video['id']}",
                        source=AssetSource.SHUTTERSTOCK,
                        type=AssetType.VIDEO,
                        url=preview_url or "",
                        thumbnail_url=thumbnail_url,
                        title=video.get("description", f"Shutterstock Video {video['id']}"),
                        description=video.get("description"),
                        duration=float(video.get("duration", 0)),
                        width=video.get("width"),
                        height=video.get("height"),
                        author=video.get("contributor", {}).get("display_name"),
                        license="Shutterstock License (Paid)"
                    ))

        elif asset_type == AssetType.IMAGE:
            # 并行搜索 Pexels 和 Shutterstock
            pexels_task = self.pexels.search_photos(query, per_page=10)
            shutterstock_task = self.shutterstock.search_images(
                query,
                per_page=10,
                orientation=orientation
            )

            # 等待所有搜索完成
            pexels_photos, shutterstock_images = await asyncio.gather(
                pexels_task,
                shutterstock_task,
                return_exceptions=True
            )

            # 处理 Pexels 结果
            if isinstance(pexels_photos, list):
                for photo in pexels_photos:
                    assets.append(Asset(
                        id=f"pexels_{photo['id']}",
                        source=AssetSource.PEXELS,
                        type=AssetType.IMAGE,
                        url=photo["src"]["original"],
                        thumbnail_url=photo["src"]["medium"],
                        title=photo.get("alt", f"Pexels Photo {photo['id']}"),
                        description=photo.get("alt"),
                        duration=None,
                        width=photo.get("width"),
                        height=photo.get("height"),
                        author=photo.get("photographer"),
                        license="Pexels License (Free)"
                    ))

            # 处理 Shutterstock 结果
            if isinstance(shutterstock_images, list):
                for image in shutterstock_images:
                    # Shutterstock 返回的数据结构
                    assets_data = image.get("assets", {})
                    preview_data = assets_data.get("preview", {})
                    thumb_data = assets_data.get("small_thumb", )

                    assets.append(Asset(
                        id=f"shutterstock_{image['id']}",
                        source=AssetSource.SHUTTERSTOCK,
                        type=AssetType.IMAGE,
                        url=preview_data.get("url", ""),
                        thumbnail_url=thumb_data.get("url"),
                        title=image.get("description", f"Shutterstock Image {image['id']}"),
                        description=image.get("description"),
                        duration=None,
                        width=preview_data.get("width"),
                        height=preview_data.get("height"),
                        author=image.get("contributor", {}).get("display_name"),
                        license="Shutterstock License (Paid)"
                    ))

        logger.info(f"从多个素材源找到 {len(assets)} 个素材")
        return assets

    def _score_assets(
        self,
        assets: List[Asset],
        prompt: str,
        target_duration: float
    ) -> List[Asset]:
        """为素材评分"""
        prompt_lower = prompt.lower()

        for asset in assets:
            # 1. 相关性评分（基于标题和描述）
            relevance = self._calculate_relevance(
                prompt_lower,
                asset.title.lower() if asset.title else "",
                asset.description.lower() if asset.description else ""
            )

            # 2. 质量评分（基于分辨率）
            quality = self._calculate_quality(asset)

            # 3. 时长匹配度（仅视频）
            duration_match = 1.0
            if asset.type == AssetType.VIDEO and asset.duration:
                duration_match = self._calculate_duration_match(
                    asset.duration,
                    target_duration
                )

            asset.score = AssetScore(
                relevance=relevance,
                quality=quality,
                duration_match=duration_match,
                overall=0.0  # 会在 __post_init__ 中计算
            )

        # 按综合评分排序
        assets.sort(key=lambda a: a.score.overall, reverse=True)

        return assets

    def _calculate_relevance(
        self,
        prompt: str,
        title: str,
        description: str
    ) -> float:
        """计算相关性"""
        # 提取提示词中的关键词
        prompt_words = set(prompt.split())
        title_words = set(title.split())
        desc_words = set(description.split()) if description else set()

        # 计算交集
        title_overlap = len(prompt_words & title_words) / max(len(prompt_words), 1)
        desc_overlap = len(prompt_words & desc_words) / max(len(prompt_words), 1)

        # 综合相关性
        relevance = title_overlap * 0.7 + desc_overlap * 0.3

        return min(relevance, 1.0)

    def _calculate_quality(self, asset: Asset) -> float:
        """计算质量评分"""
        if not asset.width or not asset.height:
            return 0.5  # 默认中等质量

        # 基于分辨率评分
        pixels = asset.width * asset.height

        if pixels >= 1920 * 1080:  # Full HD+
            return 1.0
        elif pixels >= 1280 * 720:  # HD
            return 0.8
        elif pixels >= 854 * 480:  # SD
            return 0.6
        else:
            return 0.4

    def _calculate_duration_match(
        self,
        asset_duration: float,
        target_duration: float
    ) -> float:
        """计算时长匹配度"""
        if asset_duration >= target_duration:
            # 素材时长足够，完美匹配
            return 1.0
        else:
            # 素材时长不足，按比例扣分
            return asset_duration / target_duration

    def _select_best_match(self, assets: List[Asset]) -> Optional[Asset]:
        """选择最佳匹配"""
        if not assets:
            return None

        # 已经按评分排序，返回第一个
        return assets[0]

    async def _should_use_ai_generation(
        self,
        best_match: Optional[Asset],
        prompt: str
    ) -> bool:
        """决策：是否使用 AI 生成 - 使用 LLM"""
        if not best_match or not best_match.score:
            return True

        # 评分太低，使用 AI 生成
        if best_match.score.overall < self.min_quality_score:
            return True

        # 相关性太低，使用 AI 生成
        if best_match.score.relevance < self.min_relevance_score:
            return True

        # 使用 LLM 检测是否需要特殊效果
        try:
            detection_prompt = SPECIAL_EFFECTS_DETECTION_PROMPT.format(prompt=prompt)

            response = await self._client.aio.models.generate_content(
                model='gemini-3-flash',
                contents=detection_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)

            requires_effects = result.get("requires_special_effects", False)
            recommendation = result.get("recommendation", "use_stock")

            logger.info(f"LLM 特效检测: {result}")

            if requires_effects or recommendation == "use_ai_generation":
                return True

        except Exception as e:
            logger.error(f"LLM 特效检测失败: {e}")
            # 降级方案：不使用 AI 生成（保守策略）

        # 素材质量足够，使用素材
        return False

    def _get_decision_reason(
        self,
        best_match: Optional[Asset],
        use_ai: bool
    ) -> str:
        """获取决策原因"""
        if not best_match:
            return "未找到相关素材"

        if use_ai:
            if best_match.score.overall < self.min_quality_score:
                return f"素材质量不足 (评分: {best_match.score.overall:.2f})"
            elif best_match.score.relevance < self.min_relevance_score:
                return f"相关性不足 (评分: {best_match.score.relevance:.2f})"
            else:
                return "场景需要特殊效果，AI 生成更合适"
        else:
            return f"找到高质量素材 (评分: {best_match.score.overall:.2f})"

    def estimate_cost_savings(
        self,
        use_asset: bool,
        ai_generation_cost: float = 4.0
    ) -> Dict[str, Any]:
        """估算成本节省"""
        if use_asset:
            # 使用素材：免费（Pexels）
            return {
                "cost": 0.0,
                "savings": ai_generation_cost,
                "savings_percentage": 100.0
            }
        else:
            # 使用 AI 生成
            return {
                "cost": ai_generation_cost,
                "savings": 0.0,
                "savings_percentage": 0.0
            }


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        manager = SmartAssetManager()

        test_cases = [
            ("A person walking through a busy city street", 5.0),
            ("Epic explosion with fire and smoke", 6.0),
            ("A cat sitting on a chair", 4.0),
        ]

        for prompt, duration in test_cases:
            print(f"\n{'='*70}")
            print(f"场景: {prompt}")
            print(f"时长: {duration}秒")
            print(f"{'='*70}")

            result = await manager.search_and_evaluate(prompt, duration)

            print(f"搜索关键词: {result.query}")
            print(f"找到素材: {len(result.assets)} 个")

            if result.best_match:
                print(f"\n最佳匹配:")
                print(f"  来源: {result.best_match.source.value}")
                print(f"  标题: {result.best_match.title}")
                print(f"  评分: {result.best_match.score.overall:.2f}")
                print(f"    - 相关性: {result.best_match.score.relevance:.2f}")
                print(f"    - 质量: {result.best_match.score.quality:.2f}")
                print(f"    - 时长匹配: {result.best_match.score.duration_match:.2f}")

            print(f"\n决策: {'使用 AI 生成' if result.use_ai_generation else '使用素材库'}")
            print(f"原因: {result.reason}")

            cost_info = manager.estimate_cost_savings(not result.use_ai_generation)
            print(f"成本: ${cost_info['cost']:.2f}")
            print(f"节省: ${cost_info['savings']:.2f} ({cost_info['savings_percentage']:.0f}%)")

    asyncio.run(test())
