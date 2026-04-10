"""
PromptEvaluatorAgent - Prompt 评估 Agent
负责前置评估分镜 prompt 质量，预测生成难度，提供优化建议
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.services.llm.service import LLMService, ProviderType

logger = logging.getLogger(__name__)


class PromptQualityLevel(str, Enum):
    """Prompt 质量等级"""
    EXCELLENT = "excellent"  # 优秀（>0.8）
    GOOD = "good"  # 良好（0.6-0.8）
    FAIR = "fair"  # 一般（0.4-0.6）
    POOR = "poor"  # 较差（<0.4）


class ComplexityLevel(str, Enum):
    """复杂度等级"""
    SIMPLE = "simple"  # 简单
    MEDIUM = "medium"  # 中等
    COMPLEX = "complex"  # 复杂
    VERY_COMPLEX = "very_complex"  # 非常复杂


class IssueType(str, Enum):
    """问题类型"""
    TOO_VAGUE = "too_vague"  # 描述过于模糊
    TOO_COMPLEX = "too_complex"  # 过于复杂
    INCONSISTENT = "inconsistent"  # 不一致
    MISSING_DETAILS = "missing_details"  # 缺少细节
    UNREALISTIC = "unrealistic"  # 不现实/难以生成
    CONFLICTING_ELEMENTS = "conflicting_elements"  # 元素冲突
    POOR_STRUCTURE = "poor_structure"  # 结构不佳


@dataclass
class PromptIssue:
    """Prompt 问题"""
    type: IssueType
    description: str  # 问题描述
    severity: str  # 严重程度：critical/major/minor
    suggestion: str  # 改进建议


@dataclass
class ShotEvaluation:
    """单个镜头的评估结果"""
    shot_id: int
    prompt: str
    quality_score: float  # 0-1
    quality_level: PromptQualityLevel
    complexity: ComplexityLevel
    predicted_success_rate: float  # 0-1
    issues: List[PromptIssue]
    strengths: List[str]  # 优点
    suggestions: List[str]  # 改进建议
    optimized_prompt: Optional[str] = None  # 优化后的 prompt


@dataclass
class ConsistencyCheck:
    """一致性检查结果"""
    is_consistent: bool
    consistency_score: float  # 0-1
    issues: List[str]  # 一致性问题
    suggestions: List[str]  # 改进建议


@dataclass
class StoryboardEvaluation:
    """整体分镜评估结果"""
    overall_quality_score: float  # 0-1
    overall_complexity: ComplexityLevel
    predicted_overall_success_rate: float  # 0-1
    shot_evaluations: List[ShotEvaluation]
    consistency_check: ConsistencyCheck
    global_issues: List[str]  # 全局问题
    global_suggestions: List[str]  # 全局建议
    should_proceed: bool  # 是否应该继续生成
    optimization_priority: List[int]  # 需要优先优化的镜头ID


class PromptEvaluatorAgent:
    """
    Prompt 评估 Agent - 前置质量评估

    职责：
    1. 评估每个镜头 prompt 的质量
    2. 预测生成难度和成功率
    3. 检查镜头间的一致性
    4. 提供优化建议
    5. 决定是否应该继续生成
    """

    def __init__(self):
        self.llm = LLMService(provider=ProviderType.GOOGLE)

        # 质量阈值
        self.min_quality_score = 0.5  # 最低质量分数
        self.min_success_rate = 0.6  # 最低预期成功率

    async def evaluate_storyboard(
        self,
        storyboard: List[Dict[str, Any]],
        visual_style_guide: Dict[str, str],
        characters: Optional[List[Dict[str, Any]]] = None
    ) -> StoryboardEvaluation:
        """
        评估整个分镜脚本

        Args:
            storyboard: 分镜列表
            visual_style_guide: 视觉风格指南
            characters: 角色列表

        Returns:
            StoryboardEvaluation: 评估结果
        """
        logger.info(f"🔍 Prompt评估Agent开始评估 {len(storyboard)} 个镜头...")

        # 1. 评估每个镜头
        shot_evaluations = []
        for shot in storyboard:
            evaluation = await self._evaluate_single_shot(
                shot=shot,
                visual_style_guide=visual_style_guide,
                characters=characters
            )
            shot_evaluations.append(evaluation)

        # 2. 一致性检查
        consistency_check = await self._check_consistency(
            storyboard=storyboard,
            visual_style_guide=visual_style_guide,
            characters=characters
        )

        # 3. 全局分析
        overall_quality = sum(e.quality_score for e in shot_evaluations) / len(shot_evaluations)
        overall_success_rate = sum(e.predicted_success_rate for e in shot_evaluations) / len(shot_evaluations)

        # 4. 确定整体复杂度
        complexity_scores = {
            ComplexityLevel.SIMPLE: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.COMPLEX: 3,
            ComplexityLevel.VERY_COMPLEX: 4
        }
        avg_complexity = sum(complexity_scores[e.complexity] for e in shot_evaluations) / len(shot_evaluations)
        if avg_complexity < 1.5:
            overall_complexity = ComplexityLevel.SIMPLE
        elif avg_complexity < 2.5:
            overall_complexity = ComplexityLevel.MEDIUM
        elif avg_complexity < 3.5:
            overall_complexity = ComplexityLevel.COMPLEX
        else:
            overall_complexity = ComplexityLevel.VERY_COMPLEX

        # 5. 全局问题和建议
        global_issues = []
        global_suggestions = []

        # 检查质量分布
        low_quality_count = sum(1 for e in shot_evaluations if e.quality_score < 0.6)
        if low_quality_count > len(shot_evaluations) * 0.3:
            global_issues.append(f"有 {low_quality_count} 个镜头质量较低（超过30%）")
            global_suggestions.append("建议优化低质量镜头的 prompt，或考虑重新设计分镜")

        # 检查一致性
        if not consistency_check.is_consistent:
            global_issues.append("镜头间存在一致性问题")
            global_suggestions.extend(consistency_check.suggestions)

        # 检查复杂度
        if overall_complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
            global_suggestions.append("整体复杂度较高，建议增加参考图或降低复杂度")

        # 6. 决定是否应该继续
        should_proceed = (
            overall_quality >= self.min_quality_score and
            overall_success_rate >= self.min_success_rate and
            consistency_check.consistency_score >= 0.6
        )

        # 7. 优化优先级（质量最低的镜头）
        optimization_priority = [
            e.shot_id for e in sorted(shot_evaluations, key=lambda e: e.quality_score)
        ][:3]

        result = StoryboardEvaluation(
            overall_quality_score=overall_quality,
            overall_complexity=overall_complexity,
            predicted_overall_success_rate=overall_success_rate,
            shot_evaluations=shot_evaluations,
            consistency_check=consistency_check,
            global_issues=global_issues,
            global_suggestions=global_suggestions,
            should_proceed=should_proceed,
            optimization_priority=optimization_priority
        )

        logger.info(f"✅ 评估完成:")
        logger.info(f"   整体质量: {overall_quality:.2f}")
        logger.info(f"   预期成功率: {overall_success_rate:.2f}")
        logger.info(f"   一致性: {consistency_check.consistency_score:.2f}")
        logger.info(f"   是否继续: {'✅ 是' if should_proceed else '❌ 否'}")

        return result

    async def _evaluate_single_shot(
        self,
        shot: Dict[str, Any],
        visual_style_guide: Dict[str, str],
        characters: Optional[List[Dict[str, Any]]]
    ) -> ShotEvaluation:
        """评估单个镜头的 prompt"""

        prompt = shot.get("prompt", "")
        shot_id = shot.get("sequence", shot.get("shot_id", 0))

        logger.debug(f"评估镜头 {shot_id}: {prompt[:50]}...")

        # 构建评估提示词
        evaluation_prompt = self._build_evaluation_prompt(
            prompt=prompt,
            visual_style_guide=visual_style_guide,
            characters=characters
        )

        try:
            # 调用 LLM 评估
            response = self.llm.call(
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.3  # 较低温度以获得稳定评估
            )

            # 解析评估结果
            eval_data = self._parse_evaluation_response(response["content"])

            # 构建评估对象
            issues = []
            for issue in eval_data.get("issues", []):
                try:
                    issue_type = IssueType(issue["type"])
                except ValueError:
                    logger.warning(f"未知问题类型: '{issue.get('type')}'，跳过")
                    continue
                issues.append(PromptIssue(
                    type=issue_type,
                    description=issue.get("description", ""),
                    severity=issue.get("severity", "minor"),
                    suggestion=issue.get("suggestion", "")
                ))

            try:
                quality_level = PromptQualityLevel(eval_data["quality_level"])
            except ValueError:
                quality_level = PromptQualityLevel.FAIR

            try:
                complexity = ComplexityLevel(eval_data["complexity"])
            except ValueError:
                complexity = ComplexityLevel.MEDIUM

            evaluation = ShotEvaluation(
                shot_id=shot_id,
                prompt=prompt,
                quality_score=float(eval_data.get("quality_score", 0.5)),
                quality_level=quality_level,
                complexity=complexity,
                predicted_success_rate=float(eval_data.get("predicted_success_rate", 0.5)),
                issues=issues,
                strengths=eval_data.get("strengths", []),
                suggestions=eval_data.get("suggestions", []),
                optimized_prompt=eval_data.get("optimized_prompt")
            )

            return evaluation

        except Exception as e:
            logger.warning(f"评估镜头 {shot_id} 失败，使用保守默认值: {e}")
            return ShotEvaluation(
                shot_id=shot_id,
                prompt=prompt,
                quality_score=0.5,
                quality_level=PromptQualityLevel.FAIR,
                complexity=ComplexityLevel.MEDIUM,
                predicted_success_rate=0.5,
                issues=[],
                strengths=[],
                suggestions=[f"评估失败，请人工检查此镜头: {e}"]
            )

    def _build_evaluation_prompt(
        self,
        prompt: str,
        visual_style_guide: Dict[str, str],
        characters: Optional[List[Dict[str, Any]]]
    ) -> str:
        """构建评估提示词"""

        # 角色信息
        character_info = ""
        if characters:
            character_info = "\n**角色信息**:\n"
            for char in characters:
                character_info += f"- {char.get('name')}: {char.get('description', '')}\n"

        # 视觉风格指南
        style_info = "\n**视觉风格指南**:\n"
        for key, value in visual_style_guide.items():
            style_info += f"- {key}: {value}\n"

        evaluation_prompt = f"""你是一位专业的视频生成 prompt 质量评估专家。请评估以下视频生成 prompt 的质量。

{character_info}
{style_info}

**待评估的 Prompt**:
```
{prompt}
```

**评估维度**:

1. **清晰度** (0-1)
   - 描述是否清晰、具体、无歧义
   - 是否包含足够的细节

2. **可生成性** (0-1)
   - 是否符合视频生成模型的能力
   - 是否包含难以生成的元素（特效、复杂动作等）

3. **一致性** (0-1)
   - 是否与视觉风格指南一致
   - 是否与角色描述一致

4. **结构性** (0-1)
   - 是否包含必要的元素（主体、动作、环境、光线、镜头）
   - 结构是否合理

5. **复杂度评估**
   - simple: 简单场景，静态或简单动作
   - medium: 中等复杂度，有一定动作和场景元素
   - complex: 复杂场景，多个元素或复杂动作
   - very_complex: 非常复杂，包含特效或极其复杂的场景

6. **预测成功率** (0-1)
   - 基于以上维度，预测生成成功的概率

**问题类型**:
- too_vague: 描述过于模糊
- too_complex: 过于复杂
- inconsistent: 与风格指南或角色不一致
- missing_details: 缺少关键细节
- unrealistic: 不现实/难以生成
- conflicting_elements: 元素冲突
- poor_structure: 结构不佳

**输出格式 - JSON**:
```json
{{
  "quality_score": 0.85,
  "quality_level": "excellent/good/fair/poor",
  "complexity": "simple/medium/complex/very_complex",
  "predicted_success_rate": 0.90,

  "dimension_scores": {{
    "clarity": 0.9,
    "generability": 0.85,
    "consistency": 0.8,
    "structure": 0.9
  }},

  "issues": [
    {{
      "type": "问题类型",
      "description": "问题描述",
      "severity": "critical/major/minor",
      "suggestion": "改进建议"
    }}
  ],

  "strengths": [
    "优点1",
    "优点2"
  ],

  "suggestions": [
    "改进建议1",
    "改进建议2"
  ],

  "optimized_prompt": "优化后的 prompt（如果需要优化）",

  "reasoning": "评估理由（简短说明）"
}}
```

**评估标准**:

- **Excellent (>0.8)**: 描述清晰、具体、结构完整、高度可生成
- **Good (0.6-0.8)**: 描述较好，可能缺少一些细节或有小问题
- **Fair (0.4-0.6)**: 描述一般，存在明显问题，需要优化
- **Poor (<0.4)**: 描述不佳，严重问题，强烈建议重写

请开始评估！
"""

        return evaluation_prompt

    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """解析评估响应"""
        try:
            # 提取 JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text.strip()

            eval_data = json.loads(json_str)
            return eval_data

        except Exception as e:
            logger.error(f"解析评估响应失败: {e}")
            raise

    async def _check_consistency(
        self,
        storyboard: List[Dict[str, Any]],
        visual_style_guide: Dict[str, str],
        characters: Optional[List[Dict[str, Any]]]
    ) -> ConsistencyCheck:
        """检查镜头间的一致性"""

        logger.debug("检查镜头间一致性...")

        # 提取所有 prompts
        prompts = [shot.get("prompt", "") for shot in storyboard]

        # 构建一致性检查提示词
        consistency_prompt = self._build_consistency_prompt(
            prompts=prompts,
            visual_style_guide=visual_style_guide,
            characters=characters
        )

        try:
            response = self.llm.call(
                messages=[{"role": "user", "content": consistency_prompt}],
                temperature=0.3
            )

            # 解析响应
            consistency_data = self._parse_evaluation_response(response["content"])

            return ConsistencyCheck(
                is_consistent=consistency_data["is_consistent"],
                consistency_score=consistency_data["consistency_score"],
                issues=consistency_data.get("issues", []),
                suggestions=consistency_data.get("suggestions", [])
            )

        except Exception as e:
            logger.error(f"一致性检查失败: {e}")
            # 返回默认结果
            return ConsistencyCheck(
                is_consistent=True,
                consistency_score=0.8,
                issues=[],
                suggestions=[]
            )

    def _build_consistency_prompt(
        self,
        prompts: List[str],
        visual_style_guide: Dict[str, str],
        characters: Optional[List[Dict[str, Any]]]
    ) -> str:
        """构建一致性检查提示词"""

        # 格式化 prompts
        prompts_text = "\n\n".join([f"**镜头 {i+1}**:\n{p}" for i, p in enumerate(prompts)])

        # 角色信息
        character_info = ""
        if characters:
            character_info = "\n**角色信息**:\n"
            for char in characters:
                character_info += f"- {char.get('name')}: {', '.join(char.get('visual_keywords', []))}\n"

        # 视觉风格
        style_info = "\n**视觉风格指南**:\n"
        for key, value in visual_style_guide.items():
            style_info += f"- {key}: {value}\n"

        prompt = f"""你是一位视频一致性专家。请检查以下分镜 prompts 之间的一致性。

{character_info}
{style_info}

**分镜 Prompts**:
{prompts_text}

**一致性检查维度**:

1. **角色一致性**
   - 如果有角色，所有镜头中的角色描述是否一致？
   - 关键视觉特征（颜色、外观、服装等）是否保持一致？

2. **视觉风格一致性**
   - 色彩基调是否一致？
   - 光影风格是否一致？
   - 画面质感是否一致？

3. **环境一致性**
   - 如果在同一场景，环境描述是否一致？
   - 场景切换是否有逻辑性？

4. **时间/天气一致性**
   - 时间设定是否一致（或有合理变化）？
   - 天气氛围是否一致？

**输出格式 - JSON**:
```json
{{
  "is_consistent": true/false,
  "consistency_score": 0.85,

  "dimension_scores": {{
    "character_consistency": 0.9,
    "visual_style_consistency": 0.85,
    "environment_consistency": 0.8,
    "temporal_consistency": 0.9
  }},

  "issues": [
    "一致性问题1",
    "一致性问题2"
  ],

  "suggestions": [
    "改进建议1",
    "改进建议2"
  ],

  "inconsistent_shots": [1, 3],

  "reasoning": "一致性评估理由"
}}
```

请开始检查！
"""

        return prompt

    async def convert_image_to_video_prompt(
        self,
        image_prompt: str,
        duration: float,
        visual_style_guide: Dict[str, str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        将静态图片prompt转换为动态视频prompt

        Args:
            image_prompt: 原始图片prompt（静态描述）
            duration: 视频时长（秒）
            visual_style_guide: 视觉风格指南
            context: 额外上下文信息（如场景类型、情绪等）

        Returns:
            转换后的视频prompt（包含运动和时间维度）
        """
        logger.info(f"🎬 将图片prompt转换为视频prompt (时长: {duration}s)...")

        # 视觉风格
        style_info = "\n**视觉风格指南**:\n"
        for key, value in visual_style_guide.items():
            style_info += f"- {key}: {value}\n"

        # 上下文信息
        context_info = ""
        if context:
            context_info = "\n**上下文信息**:\n"
            for key, value in context.items():
                context_info += f"- {key}: {value}\n"

        conversion_prompt = f"""你是一位专业的视频生成prompt专家。请将以下静态图片prompt转换为适合视频生成的动态prompt。

{style_info}
{context_info}

**原始图片Prompt**:
```
{image_prompt}
```

**视频时长**: {duration}秒

**转换要求**:

1. **保留核心视觉元素**
   - 保留主体描述（人物、物体、产品等）
   - 保留环境描述（场景、背景、氛围）
   - 保留光影描述（lighting, shadows, highlights）
   - 保留色彩描述（color palette, tones）
   - 保留视觉风格（风格、质感、调性）
   - 保留视觉风格指南中的关键词

2. **添加动态元素**
   - 添加合适的镜头运动（camera movement）：
     * 产品/物体: slowly rotating, gentle push in, smooth pan around
     * 人物: slow zoom in, subtle dolly, tracking shot
     * 风景: sweeping pan, crane shot, aerial movement
     * 静态场景: subtle camera drift, gentle push in
   - 添加主体动作（subject motion）：
     * 人物: natural movements, gestures, expressions
     * 物体: subtle movements, floating, rotating
     * 自然元素: wind effects, water flow, light changes
   - 添加时间维度描述：
     * 短视频(≤5s): quick, dynamic, energetic
     * 中等(5-8s): smooth, flowing, cinematic
     * 长视频(>8s): slow, contemplative, immersive

3. **优化视频生成关键词**
   - 添加运动质量关键词：smooth motion, fluid movement, cinematic flow
   - 添加时间关键词：slow motion, real-time, time-lapse（根据需要）
   - 添加视频技术关键词：4K video, high frame rate, professional cinematography
   - 移除纯图片关键词：static composition, still frame, photograph

4. **根据内容类型优化**
   - 产品展示: 强调360度展示、细节特写、光影变化
   - 人物场景: 强调自然动作、情绪表达、环境互动
   - 风景场景: 强调大气运动、光影变化、空间感
   - 抽象/艺术: 强调流动感、变化、视觉冲击

5. **保持视觉一致性**
   - 确保添加的运动不会破坏原有的构图和美感
   - 运动应该增强而不是干扰主体
   - 保持与视觉风格指南的一致性

**输出格式 - JSON**:
```json
{{
  "video_prompt": "转换后的视频生成prompt（英文）",
  "added_camera_movement": "添加的镜头运动描述",
  "added_subject_motion": "添加的主体动作描述",
  "added_temporal_elements": [
    "添加的时间元素1",
    "添加的时间元素2"
  ],
  "preserved_elements": [
    "保留的核心元素1",
    "保留的核心元素2"
  ],
  "removed_elements": [
    "移除的纯图片元素1",
    "移除的纯图片元素2"
  ],
  "motion_intensity": "subtle/moderate/dynamic",
  "reasoning": "转换理由（简短说明为什么选择这些运动方式）"
}}
```

**示例**:

原始图片prompt:
"A sleek silver smartwatch with blue display, perfectly centered on minimalist white surface, soft studio lighting with blue accent lights, modern tech aesthetic, high-quality product photography, sharp focus, 8K ultra-detailed"

转换后的视频prompt:
"A sleek silver smartwatch with blue display on minimalist white surface, camera slowly rotating around the watch revealing all angles, soft studio lighting with blue accent lights creating dynamic reflections, modern tech aesthetic, smooth cinematic motion, 4K video quality, professional product cinematography"

---

原始图片prompt:
"Young woman in red dress standing in sunlit garden, golden hour lighting, warm tones, portrait composition, professional photography"

转换后的视频prompt:
"Young woman in red dress standing in sunlit garden, gentle breeze moving her hair and dress, slow zoom in capturing her natural expression, golden hour lighting with soft shadows, warm tones, cinematic portrait, smooth camera movement, 4K video"

请开始转换！
"""

        try:
            response = self.llm.call(
                messages=[{"role": "user", "content": conversion_prompt}],
                temperature=0.4  # 稍高温度以获得更有创意的运动描述
            )

            # 解析响应
            result = self._parse_evaluation_response(response["content"])
            video_prompt = result["video_prompt"]

            logger.info(f"✅ 视频prompt转换完成")
            logger.debug(f"   原始图片: {image_prompt[:80]}...")
            logger.debug(f"   转换视频: {video_prompt[:80]}...")
            logger.debug(f"   镜头运动: {result.get('added_camera_movement', 'N/A')}")
            logger.debug(f"   运动强度: {result.get('motion_intensity', 'N/A')}")

            return video_prompt

        except Exception as e:
            logger.error(f"转换视频prompt失败: {e}")
            # 降级方案：简单添加基础运动描述
            fallback_prompt = image_prompt

            # 移除纯图片关键词
            image_keywords = [
                r'static composition',
                r'still frame',
                r'photograph(y)?',
                r'photo shot',
                r'perfectly centered',
                r'sharp focus'
            ]
            for pattern in image_keywords:
                fallback_prompt = re.sub(pattern, '', fallback_prompt, flags=re.IGNORECASE)

            # 添加基础运动描述
            if duration <= 5:
                motion = "smooth camera movement, dynamic motion"
            elif duration <= 8:
                motion = "slow cinematic camera movement, fluid motion"
            else:
                motion = "gentle camera drift, contemplative motion"

            fallback_prompt = f"{fallback_prompt.strip()}, {motion}, 4K video quality"

            logger.warning(f"使用降级方案生成视频prompt")
            return fallback_prompt.strip()

    async def generate_image_prompt_from_video_prompt(
        self,
        video_prompt: str,
        visual_style_guide: Dict[str, str],
        purpose: str = "first_frame"
    ) -> str:
        """
        从视频prompt生成适合图片生成的prompt

        Args:
            video_prompt: 视频生成的prompt
            visual_style_guide: 视觉风格指南
            purpose: 图片用途 (first_frame/character_reference/storyboard)

        Returns:
            优化后的图片生成prompt
        """
        logger.info(f"🎨 为 {purpose} 生成图片prompt...")

        # 视觉风格
        style_info = "\n**视觉风格指南**:\n"
        for key, value in visual_style_guide.items():
            style_info += f"- {key}: {value}\n"

        conversion_prompt = f"""你是一位专业的图片生成prompt专家。请将以下视频生成prompt转换为适合图片生成的prompt。

{style_info}

**原始视频Prompt**:
```
{video_prompt}
```

**图片用途**: {purpose}

**转换要求**:

1. **移除动态元素**
   - 移除所有镜头运动描述（camera movement, panning, rotating, pushing, pulling等）
   - 移除所有动作描述（slow motion, moving, flowing, blowing等）
   - 移除时间相关描述（duration, sequence等）

2. **强化静态视觉元素**
   - 强调构图（composition, framing, layout）
   - 强调光影（lighting, shadows, highlights）
   - 强调细节（texture, details, quality）
   - 强调色彩（color palette, tones, saturation）

3. **保持核心元素**
   - 保留主体描述（人物、物体、产品等）
   - 保留环境描述（场景、背景、氛围）
   - 保留视觉风格（风格、质感、调性）
   - 保留视觉风格指南中的关键词

4. **针对不同用途优化**
   - first_frame: 强调"opening frame"、"establishing shot"、"key moment"
   - character_reference: 强调"character design"、"reference sheet"、"consistent appearance"
   - storyboard: 强调"storyboard frame"、"concept art"、"visual planning"

5. **添加图片生成优化关键词**
   - 添加质量关键词：high quality, detailed, sharp focus, professional
   - 添加构图关键词：well-composed, balanced, centered/rule of thirds
   - 添加技术关键词：8K, ultra-detailed, photorealistic/artistic（根据风格）

**输出格式 - JSON**:
```json
{{
  "image_prompt": "转换后的图片生成prompt（英文）",
  "removed_elements": [
    "移除的动态元素1",
    "移除的动态元素2"
  ],
  "added_elements": [
    "添加的静态元素1",
    "添加的静态元素2"
  ],
  "key_preserved_elements": [
    "保留的核心元素1",
    "保留的核心元素2"
  ],
  "reasoning": "转换理由（简短说明为什么这样转换）"
}}
```

**示例**:

原始视频prompt:
"A sleek silver smartwatch with blue display, camera slowly rotating around the watch, soft studio lighting, modern tech aesthetic, 4K quality"

转换后的图片prompt:
"A sleek silver smartwatch with blue display, perfectly centered on minimalist white surface, soft studio lighting with blue accent lights, modern tech aesthetic, high-quality product photography, sharp focus, well-composed, 8K ultra-detailed, professional commercial shot"

请开始转换！
"""

        try:
            response = self.llm.call(
                messages=[{"role": "user", "content": conversion_prompt}],
                temperature=0.3
            )

            # 解析响应
            result = self._parse_evaluation_response(response["content"])
            image_prompt = result["image_prompt"]

            logger.info(f"✅ 图片prompt生成完成")
            logger.debug(f"   原始: {video_prompt[:80]}...")
            logger.debug(f"   转换: {image_prompt[:80]}...")

            return image_prompt

        except Exception as e:
            logger.error(f"生成图片prompt失败: {e}")
            # 降级方案：简单移除动态关键词
            fallback_prompt = video_prompt
            # 移除常见的动态描述
            dynamic_keywords = [
                r'camera (slowly|gently|quickly)?\s*(rotating|panning|tilting|pushing|pulling|moving)',
                r'slow motion',
                r'in motion',
                r'moving',
                r'flowing',
                r'blowing'
            ]
            for pattern in dynamic_keywords:
                fallback_prompt = re.sub(pattern, '', fallback_prompt, flags=re.IGNORECASE)

            # 添加静态关键词
            fallback_prompt += ", static composition, high detail, professional photography"

            logger.warning(f"使用降级方案生成图片prompt")
            return fallback_prompt.strip()


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        agent = PromptEvaluatorAgent()

        # 模拟分镜
        storyboard = [
            {
                "sequence": 1,
                "prompt": "A fluffy orange cat sitting on a windowsill, morning sunlight, warm tones, close-up shot"
            },
            {
                "sequence": 2,
                "prompt": "The same orange cat jumping down from the windowsill, soft lighting, medium shot"
            },
            {
                "sequence": 3,
                "prompt": "A black dog running in the park, bright daylight, wide shot"  # 不一致！
            }
        ]

        visual_style_guide = {
            "color_palette": "warm golden tones",
            "lighting_style": "soft natural light",
            "visual_quality": "cinematic"
        }

        characters = [
            {
                "name": "橙色小猫",
                "description": "A fluffy orange tabby cat with big green eyes",
                "visual_keywords": ["orange", "fluffy", "green eyes"]
            }
        ]

        # 评估
        result = await agent.evaluate_storyboard(
            storyboard=storyboard,
            visual_style_guide=visual_style_guide,
            characters=characters
        )

        print("=" * 80)
        print("Prompt 评估结果")
        print("=" * 80)
        print(f"\n整体质量: {result.overall_quality_score:.2f}")
        print(f"整体复杂度: {result.overall_complexity.value}")
        print(f"预期成功率: {result.predicted_overall_success_rate:.2f}")
        print(f"一致性: {result.consistency_check.consistency_score:.2f}")
        print(f"是否继续: {'✅ 是' if result.should_proceed else '❌ 否'}")

        print(f"\n镜头评估:")
        for eval in result.shot_evaluations:
            print(f"\n  镜头 {eval.shot_id}:")
            print(f"    质量: {eval.quality_score:.2f} ({eval.quality_level.value})")
            print(f"    复杂度: {eval.complexity.value}")
            print(f"    预期成功率: {eval.predicted_success_rate:.2f}")
            if eval.issues:
                print(f"    问题: {len(eval.issues)} 个")

        if result.global_issues:
            print(f"\n全局问题:")
            for issue in result.global_issues:
                print(f"  - {issue}")

        if result.global_suggestions:
            print(f"\n全局建议:")
            for suggestion in result.global_suggestions:
                print(f"  - {suggestion}")

    asyncio.run(test())
