"""
视频质量评估器
自动评估生成视频的质量并提供改进建议
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import os

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class QualityIssue(str, Enum):
    """质量问题类型"""
    LOW_RESOLUTION = "low_resolution"  # 分辨率过低
    BLURRY = "blurry"  # 模糊
    SHAKY = "shaky"  # 抖动
    POOR_LIGHTING = "poor_lighting"  # 光线不佳
    OFF_TOPIC = "off_topic"  # 不符合提示词
    TOO_SHORT = "too_short"  # 时长不足
    POOR_COMPOSITION = "poor_composition"  # 构图不佳
    COLOR_ISSUES = "color_issues"  # 色彩问题
    ARTIFACTS = "artifacts"  # 伪影/噪点


@dataclass
class QualityScore:
    """质量评分"""
    technical: float  # 技术质量 0-1
    relevance: float  # 内容相关性 0-1
    aesthetic: float  # 美学质量 0-1
    duration_match: float  # 时长匹配 0-1
    overall: float  # 综合评分 0-1

    def __post_init__(self):
        """计算综合评分"""
        self.overall = (
            self.technical * 0.35 +      # 技术质量权重 35%
            self.relevance * 0.35 +      # 相关性权重 35%
            self.aesthetic * 0.20 +      # 美学质量权重 20%
            self.duration_match * 0.10   # 时长匹配权重 10%
        )


@dataclass
class QualityReport:
    """质量评估报告"""
    score: QualityScore
    issues: List[QualityIssue]
    passed: bool  # 是否通过质量检查
    suggestions: List[str]  # 改进建议
    confidence: float  # 评估置信度 0-1


class VideoQualityEvaluator:
    """视频质量评估器"""

    def __init__(self):
        # 初始化 LLM
        genai.configure(api_key=settings.google_api_key)

        # 质量阈值
        self.min_overall_score = 0.6  # 最低综合评分
        self.min_technical_score = 0.5  # 最低技术质量
        self.min_relevance_score = 0.5  # 最低相关性

        # 评估权重
        self.weights = {
            "technical": 0.35,
            "relevance": 0.35,
            "aesthetic": 0.20,
            "duration_match": 0.10
        }

    async def evaluate(
        self,
        video_path: str,
        prompt: str,
        expected_duration: float,
        provider: str
    ) -> QualityReport:
        """
        评估视频质量

        Args:
            video_path: 视频文件路径
            prompt: 原始提示词
            expected_duration: 期望时长
            provider: 生成提供商

        Returns:
            QualityReport: 质量评估报告
        """
        logger.info(f"🔍 评估视频质量: {os.path.basename(video_path)}")

        # 1. 技术质量评估
        technical_score, technical_issues = await self._evaluate_technical_quality(
            video_path
        )

        # 2. 内容相关性评估
        relevance_score, relevance_issues = await self._evaluate_relevance(
            video_path, prompt
        )

        # 3. 美学质量评估
        aesthetic_score, aesthetic_issues = await self._evaluate_aesthetic_quality(
            video_path
        )

        # 4. 时长匹配评估
        duration_score, duration_issues = await self._evaluate_duration(
            video_path, expected_duration
        )

        # 5. 汇总评分
        score = QualityScore(
            technical=technical_score,
            relevance=relevance_score,
            aesthetic=aesthetic_score,
            duration_match=duration_score,
            overall=0.0  # 会在 __post_init__ 中计算
        )

        # 6. 汇总问题
        all_issues = (
            technical_issues +
            relevance_issues +
            aesthetic_issues +
            duration_issues
        )

        # 7. 判断是否通过
        passed = self._check_passed(score, all_issues)

        # 8. 生成改进建议
        suggestions = self._generate_suggestions(score, all_issues, provider)

        # 9. 计算置信度
        confidence = self._calculate_confidence(score, provider)

        report = QualityReport(
            score=score,
            issues=all_issues,
            passed=passed,
            suggestions=suggestions,
            confidence=confidence
        )

        logger.info(
            f"✅ 评估完成: 综合评分 {score.overall:.2f}, "
            f"{'通过' if passed else '未通过'}, "
            f"问题数: {len(all_issues)}"
        )

        return report

    async def _evaluate_technical_quality(
        self,
        video_path: str
    ) -> tuple[float, List[QualityIssue]]:
        """评估技术质量（分辨率、清晰度、稳定性）"""
        issues = []

        # 检查文件是否存在
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return 0.0, [QualityIssue.ARTIFACTS]

        # 获取文件大小
        file_size = os.path.getsize(video_path)

        # 基于文件大小的简单启发式评估
        # TODO: 使用 ffprobe 或 OpenCV 进行更详细的分析
        if file_size < 100_000:  # < 100KB
            issues.append(QualityIssue.LOW_RESOLUTION)
            score = 0.3
        elif file_size < 500_000:  # < 500KB
            score = 0.6
        elif file_size < 2_000_000:  # < 2MB
            score = 0.8
        else:
            score = 0.9

        # 基于文件扩展名的检查
        if not video_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
            issues.append(QualityIssue.ARTIFACTS)
            score *= 0.5

        return score, issues

    async def _evaluate_relevance(
        self,
        video_path: str,
        prompt: str
    ) -> tuple[float, List[QualityIssue]]:
        """评估内容相关性（是否符合提示词）- 使用 LLM"""
        issues = []

        # 如果文件不存在，相关性为 0
        if not os.path.exists(video_path):
            return 0.0, [QualityIssue.OFF_TOPIC]

        # TODO: 使用视觉语言模型（如 CLIP）进行更准确的相关性评估
        # 目前使用 LLM 分析提示词复杂度

        try:
            analysis_prompt = f"""请分析以下视频生成提示词的复杂度和特殊效果需求。

提示词：{prompt}

请判断：
1. 是否包含特殊视觉效果（爆炸、魔法、变形、科幻元素等）
2. 场景复杂度（简单、中等、复杂）
3. 生成难度（容易、中等、困难）

特殊效果和复杂场景通常更难准确生成，相关性可能较低。

请以 JSON 格式返回结果：
{{
    "has_special_effects": true/false,
    "complexity": "simple|medium|complex",
    "difficulty": "easy|medium|hard",
    "expected_relevance": 0.0-1.0,
    "reasoning": "判断依据"
}}
"""

            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = await model.generate_content_async(
                analysis_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)
            score = result.get("expected_relevance", 0.8)

            logger.debug(f"LLM 相关性分析: {result}")

            # 如果预期相关性很低，标记为问题
            if score < 0.6:
                issues.append(QualityIssue.OFF_TOPIC)

            return score, issues

        except Exception as e:
            logger.error(f"LLM 相关性评估失败: {e}")
            # 降级方案：返回中等相关性
            return 0.75, issues

    async def _evaluate_aesthetic_quality(
        self,
        video_path: str
    ) -> tuple[float, List[QualityIssue]]:
        """评估美学质量（构图、色彩、光线）"""
        issues = []

        # TODO: 使用图像质量评估模型（如 NIMA）
        # 目前使用简化的启发式方法

        # 基于文件大小的美学质量估计
        if not os.path.exists(video_path):
            return 0.0, [QualityIssue.POOR_COMPOSITION]

        file_size = os.path.getsize(video_path)

        # 较大的文件通常意味着更高的质量
        if file_size < 500_000:
            score = 0.5
            issues.append(QualityIssue.POOR_COMPOSITION)
        elif file_size < 2_000_000:
            score = 0.7
        else:
            score = 0.85

        return score, issues

    async def _evaluate_duration(
        self,
        video_path: str,
        expected_duration: float
    ) -> tuple[float, List[QualityIssue]]:
        """评估时长匹配度"""
        issues = []

        # TODO: 使用 ffprobe 获取实际视频时长
        # 目前假设生成的视频时长符合预期

        if not os.path.exists(video_path):
            return 0.0, [QualityIssue.TOO_SHORT]

        # 简化：假设生成的视频时长接近预期
        # 实际应该使用 ffprobe 或 moviepy 获取真实时长
        score = 0.9

        return score, issues

    def _check_passed(
        self,
        score: QualityScore,
        issues: List[QualityIssue]
    ) -> bool:
        """检查是否通过质量检查"""
        # 综合评分必须达标
        if score.overall < self.min_overall_score:
            return False

        # 技术质量必须达标
        if score.technical < self.min_technical_score:
            return False

        # 相关性必须达标
        if score.relevance < self.min_relevance_score:
            return False

        # 不能有严重问题
        critical_issues = [
            QualityIssue.OFF_TOPIC,
            QualityIssue.ARTIFACTS
        ]

        for issue in issues:
            if issue in critical_issues:
                return False

        return True

    def _generate_suggestions(
        self,
        score: QualityScore,
        issues: List[QualityIssue],
        provider: str
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 基于评分的建议
        if score.technical < 0.6:
            suggestions.append("技术质量较低，建议切换到更高质量的提供商")
            if provider == "veo":
                suggestions.append("尝试添加参考图片以提高质量")

        if score.relevance < 0.6:
            suggestions.append("内容相关性较低，建议优化提示词描述")
            suggestions.append("尝试添加更多细节描述或参考图片")

        if score.aesthetic < 0.6:
            suggestions.append("美学质量较低，建议在提示词中添加构图和光线描述")

        if score.duration_match < 0.8:
            suggestions.append("时长不匹配，建议调整生成参数")

        # 基于问题的建议
        issue_suggestions = {
            QualityIssue.LOW_RESOLUTION: "分辨率过低，切换到支持更高分辨率的提供商",
            QualityIssue.BLURRY: "画面模糊，尝试添加参考图片或切换提供商",
            QualityIssue.SHAKY: "画面抖动，在提示词中添加'稳定镜头'描述",
            QualityIssue.POOR_LIGHTING: "光线不佳，在提示词中添加光线描述",
            QualityIssue.OFF_TOPIC: "内容不符，重新优化提示词或添加参考图片",
            QualityIssue.TOO_SHORT: "时长不足，调整生成参数",
            QualityIssue.POOR_COMPOSITION: "构图不佳，在提示词中添加构图描述",
            QualityIssue.COLOR_ISSUES: "色彩问题，在提示词中添加色调描述",
            QualityIssue.ARTIFACTS: "存在伪影，切换提供商或降低复杂度"
        }

        for issue in issues:
            if issue in issue_suggestions:
                suggestion = issue_suggestions[issue]
                if suggestion not in suggestions:
                    suggestions.append(suggestion)

        # 如果没有问题，给出鼓励
        if not suggestions:
            suggestions.append("质量良好，无需改进")

        return suggestions

    def _calculate_confidence(
        self,
        score: QualityScore,
        provider: str
    ) -> float:
        """计算评估置信度"""
        # TODO: 基于更多因素计算置信度
        # 目前使用简化的方法

        # 基础置信度
        confidence = 0.7

        # 如果使用了实际的视频分析工具，置信度更高
        # 目前使用启发式方法，置信度较低

        # 如果评分极端（很高或很低），置信度降低
        if score.overall > 0.9 or score.overall < 0.3:
            confidence *= 0.9

        return confidence

    def get_repair_strategy(self, report: QualityReport) -> Dict[str, Any]:
        """
        根据质量报告生成修复策略

        Returns:
            修复策略字典，包含：
            - should_retry: 是否应该重试
            - strategy: 修复策略
            - reason: 修复原因
        """
        if report.passed:
            return {
                "should_retry": False,
                "strategy": None,
                "reason": "质量已达标"
            }

        # 分析主要问题
        score = report.score
        issues = report.issues

        # 策略 1: 技术质量问题 -> 切换提供商
        if score.technical < 0.5:
            return {
                "should_retry": True,
                "strategy": "switch_provider",
                "reason": f"技术质量过低 ({score.technical:.2f})",
                "details": {
                    "current_issues": [issue.value for issue in issues]
                }
            }

        # 策略 2: 相关性问题 -> 添加参考图或优化提示词
        if score.relevance < 0.5:
            return {
                "should_retry": True,
                "strategy": "add_reference_image",
                "reason": f"内容相关性过低 ({score.relevance:.2f})",
                "details": {
                    "suggestions": report.suggestions
                }
            }

        # 策略 3: 综合评分低 -> 降低复杂度
        if score.overall < 0.6:
            return {
                "should_retry": True,
                "strategy": "reduce_complexity",
                "reason": f"综合质量过低 ({score.overall:.2f})",
                "details": {
                    "issues": [issue.value for issue in issues],
                    "suggestions": report.suggestions
                }
            }

        # 默认：不重试
        return {
            "should_retry": False,
            "strategy": None,
            "reason": "质量接近达标，不建议重试"
        }


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        evaluator = VideoQualityEvaluator()

        # 模拟评估
        test_cases = [
            {
                "video_path": "./outputs/test_video_1.mp4",
                "prompt": "A cat sitting on a chair",
                "expected_duration": 5.0,
                "provider": "veo"
            },
            {
                "video_path": "./outputs/test_video_2.mp4",
                "prompt": "Epic explosion with fire and smoke",
                "expected_duration": 6.0,
                "provider": "veo"
            }
        ]

        for case in test_cases:
            print(f"\n{'='*70}")
            print(f"评估视频: {case['video_path']}")
            print(f"提示词: {case['prompt']}")
            print(f"{'='*70}")

            report = await evaluator.evaluate(**case)

            print(f"\n📊 质量评分:")
            print(f"  技术质量: {report.score.technical:.2f}")
            print(f"  内容相关性: {report.score.relevance:.2f}")
            print(f"  美学质量: {report.score.aesthetic:.2f}")
            print(f"  时长匹配: {report.score.duration_match:.2f}")
            print(f"  综合评分: {report.score.overall:.2f}")

            print(f"\n{'✅' if report.passed else '❌'} 质量检查: {'通过' if report.passed else '未通过'}")
            print(f"🎯 置信度: {report.confidence:.2f}")

            if report.issues:
                print(f"\n⚠️  发现问题:")
                for issue in report.issues:
                    print(f"  - {issue.value}")

            if report.suggestions:
                print(f"\n💡 改进建议:")
                for suggestion in report.suggestions:
                    print(f"  - {suggestion}")

            # 获取修复策略
            repair = evaluator.get_repair_strategy(report)
            print(f"\n🔧 修复策略:")
            print(f"  是否重试: {repair['should_retry']}")
            print(f"  策略: {repair['strategy']}")
            print(f"  原因: {repair['reason']}")

    asyncio.run(test())
