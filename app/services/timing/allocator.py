"""
时长分配器
智能分析内容重要性并分配镜头时长
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.timing import TimingPlan, ShotTiming, PacingStrategy, ContentImportance
from app.models.shot import Shot, ShotType
from app.services.llm.service import llm_service as default_llm_service

logger = logging.getLogger(__name__)


class TimingAllocator:
    """时长分配器"""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service or default_llm_service

        # 内容重要性权重映射
        self.importance_weights = {
            ContentImportance.CRITICAL: 1.5,
            ContentImportance.HIGH: 1.2,
            ContentImportance.MEDIUM: 1.0,
            ContentImportance.LOW: 0.8,
            ContentImportance.FILLER: 0.6
        }

        # 镜头类型时长倾向
        self.shot_type_factors = {
            ShotType.ESTABLISHING: 1.3,  # 建立镜头通常较长
            ShotType.CLOSE_UP: 0.9,      # 特写相对较短
            ShotType.MEDIUM: 1.0,        # 中景标准
            ShotType.WIDE: 1.2,          # 广角稍长
            ShotType.TRANSITION: 0.7,    # 过渡镜头较短
            ShotType.ACTION: 1.1,        # 动作镜头适中
            ShotType.DETAIL: 0.8,        # 细节镜头较短
            ShotType.CUTAWAY: 0.6        # 插切最短
        }

        logger.info("TimingAllocator初始化完成")

    async def create_timing_plan(
        self,
        project_id: str,
        content_segments: List[str],
        shots: List[Shot],
        target_duration: float,
        pacing_strategy: PacingStrategy = PacingStrategy.BALANCED
    ) -> TimingPlan:
        """创建时长分配计划"""
        logger.info(f"开始创建时长分配计划: 项目{project_id}, 目标时长{target_duration}秒")

        # 创建时长计划对象
        timing_plan = TimingPlan(
            project_id=project_id,
            target_total_duration=target_duration,
            pacing_strategy=pacing_strategy
        )

        # 分析内容重要性
        importance_analysis = await self._analyze_content_importance(content_segments)

        # 为每个镜头创建时长分配
        for i, shot in enumerate(shots):
            content_segment = content_segments[i] if i < len(content_segments) else ""
            importance = importance_analysis.get(i, ContentImportance.MEDIUM)

            shot_timing = ShotTiming(
                shot_id=shot.id,
                sequence=shot.sequence,
                content_segment=content_segment,
                importance_level=importance,
                importance_weight=self.importance_weights[importance],
                base_duration=target_duration / len(shots),  # 平均基础时长
                adjusted_duration=target_duration / len(shots),
                is_opening=(i == 0),
                is_closing=(i == len(shots) - 1),
                is_climax=await self._is_climax_content(content_segment)
            )

            timing_plan.add_shot_timing(shot_timing)

        # 执行智能优化
        await self._optimize_timing_plan(timing_plan, shots)

        logger.info(f"时长分配计划创建完成: {len(timing_plan.shot_timings)}个镜头")
        return timing_plan

    async def _analyze_content_importance(self, content_segments: List[str]) -> Dict[int, ContentImportance]:
        """分析内容重要性"""
        logger.debug("开始分析内容重要性")

        importance_analysis = {}

        for i, segment in enumerate(content_segments):
            try:
                # 使用LLM分析内容重要性
                importance = await self._llm_analyze_importance(segment, i, len(content_segments))
                importance_analysis[i] = importance

                logger.debug(f"片段 {i+1} 重要性: {importance.value}")
            except Exception as e:
                logger.warning(f"分析片段 {i+1} 重要性失败，使用默认值: {e}")
                importance_analysis[i] = ContentImportance.MEDIUM

        return importance_analysis

    async def _llm_analyze_importance(self, segment: str, index: int, total_segments: int) -> ContentImportance:
        """使用LLM分析单个片段的重要性"""
        position_context = ""
        if index == 0:
            position_context = "这是开头片段"
        elif index == total_segments - 1:
            position_context = "这是结尾片段"
        else:
            position_context = f"这是第{index+1}个片段，共{total_segments}个"

        prompt = f"""请分析以下内容片段在视频中的重要性等级。

{position_context}：
"{segment}"

请从以下等级中选择一个：
1. CRITICAL - 关键内容（核心信息、重要转折点）
2. HIGH - 高重要性（重要细节、关键支撑）
3. MEDIUM - 中等重要性（一般信息、连接内容）
4. LOW - 低重要性（补充信息、次要细节）
5. FILLER - 填充内容（过渡内容、氛围营造）

请只回答等级名称（如：HIGH）："""

        try:
            result = self.llm_service.simple_call(prompt, max_tokens=100, temperature=0.3)
            if result.get("success"):
                response_clean = result["content"].strip().upper()
            else:
                logger.warning(f"LLM调用失败: {result.get('error')}��使用默认值")
                return ContentImportance.MEDIUM

            # 尝试解析响应
            if "CRITICAL" in response_clean:
                return ContentImportance.CRITICAL
            elif "HIGH" in response_clean:
                return ContentImportance.HIGH
            elif "LOW" in response_clean:
                return ContentImportance.LOW
            elif "FILLER" in response_clean:
                return ContentImportance.FILLER
            else:
                return ContentImportance.MEDIUM

        except Exception as e:
            logger.warning(f"LLM重要性分析失败: {e}")
            return ContentImportance.MEDIUM

    async def _is_climax_content(self, content: str) -> bool:
        """判断是否为高潮内容"""
        # 关键词检测
        climax_keywords = [
            "高潮", "关键", "重要", "核心", "亮点", "精彩", "震撼",
            "转折", "突破", "成功", "实现", "达成", "完成"
        ]

        content_lower = content.lower()
        for keyword in climax_keywords:
            if keyword in content:
                return True

        # 英文关键词
        english_keywords = [
            "key", "important", "critical", "highlight", "breakthrough",
            "success", "achieve", "accomplish", "climax", "peak"
        ]

        for keyword in english_keywords:
            if keyword in content_lower:
                return True

        return False

    async def _optimize_timing_plan(self, timing_plan: TimingPlan, shots: List[Shot]):
        """优化时长分配计划"""
        logger.debug("开始优化时长分配")

        # 1. 应用镜头类型因子
        self._apply_shot_type_factors(timing_plan, shots)

        # 2. 应用内容密度分析
        await self._analyze_content_density(timing_plan)

        # 3. 执行优化算法
        timing_plan.optimize_durations()

        # 4. 验证约束条件
        violations = timing_plan.validate_constraints()
        if violations:
            logger.warning(f"时长约束违规: {violations}")
            # 尝试修正
            self._fix_constraint_violations(timing_plan, violations)

        logger.debug("时长分配优化完成")

    def _apply_shot_type_factors(self, timing_plan: TimingPlan, shots: List[Shot]):
        """应用镜头类型因子"""
        for i, timing in enumerate(timing_plan.shot_timings):
            if i < len(shots):
                shot = shots[i]
                type_factor = self.shot_type_factors.get(shot.shot_type, 1.0)
                timing.base_duration *= type_factor
                timing.adjustment_reason = f"镜头类型调整 ({shot.shot_type.value}: {type_factor}x)"

    async def _analyze_content_density(self, timing_plan: TimingPlan):
        """分析内容密度"""
        for timing in timing_plan.shot_timings:
            # 基于内容长度和复杂度评估密度
            content = timing.content_segment

            # 简单的密度计算
            word_count = len(content.split())
            sentence_count = len(re.split(r'[.!?。！？]', content))

            # 归一化密度分数
            if word_count > 0:
                density = min(1.0, (word_count * 0.1 + sentence_count * 0.2))
                timing.content_density = max(0.1, density)
            else:
                timing.content_density = 0.3  # 默认低密度

    def _fix_constraint_violations(self, timing_plan: TimingPlan, violations: List[str]):
        """修正约束违规"""
        logger.info("尝试修正时长约束违规")

        for timing in timing_plan.shot_timings:
            # 确保单个镜头时长在合理范围内
            if timing.adjusted_duration < timing.min_duration:
                timing.adjusted_duration = timing.min_duration
                timing.adjustment_reason += " | 最小时长限制"
            elif timing.adjusted_duration > timing.max_duration:
                timing.adjusted_duration = timing.max_duration
                timing.adjustment_reason += " | 最大时长限制"

        # 重新平衡总时长
        current_total = sum(t.adjusted_duration for t in timing_plan.shot_timings)
        if abs(current_total - timing_plan.target_total_duration) > timing_plan.duration_tolerance:
            adjustment_ratio = timing_plan.target_total_duration / current_total

            for timing in timing_plan.shot_timings:
                new_duration = timing.adjusted_duration * adjustment_ratio
                timing.adjusted_duration = max(timing.min_duration,
                                             min(timing.max_duration, new_duration))

        timing_plan._recalculate_totals()

    def calculate_optimal_shot_count(self, target_duration: float, content_length: int) -> int:
        """计算最优镜头数量 - 考虑Google Veo 8秒限制"""
        # Google Veo限制每个镜头最大8秒
        max_shot_duration = 8.0

        # 基于最大时长限制计算最小镜头数
        min_shots = max(3, int(target_duration / max_shot_duration) + 1)

        # 基础镜头数：每6-7秒一个镜头（更保守）
        base_shot_count = max(min_shots, int(target_duration / 6.5))

        # 内容长度调整
        if content_length > 1000:  # 长内容
            base_shot_count = int(base_shot_count * 1.2)
        elif content_length < 300:  # 短内容
            base_shot_count = max(min_shots, int(base_shot_count * 0.9))

        # 确保不超过合理范围
        return max(min_shots, min(20, base_shot_count))

    def suggest_pacing_strategy(self, content_segments: List[str], target_audience: str = "") -> PacingStrategy:
        """建议节奏策略"""
        # 基于内容类型和目标受众的策略建议

        content_text = " ".join(content_segments).lower()

        # 教育内容 - 平衡节奏
        if any(word in content_text for word in ["教学", "学习", "教程", "步骤", "方法"]):
            return PacingStrategy.BALANCED

        # 营销内容 - 动态节奏
        if any(word in content_text for word in ["产品", "购买", "优惠", "限时", "促销"]):
            return PacingStrategy.DYNAMIC

        # 故事内容 - 渐强节奏
        if any(word in content_text for word in ["故事", "情节", "角色", "结局", "高潮"]):
            return PacingStrategy.CRESCENDO

        # 冥想/放松内容 - 慢节奏
        if any(word in content_text for word in ["冥想", "放松", "宁静", "平静", "舒缓"]):
            return PacingStrategy.SLOW_PACED

        # 默认平衡节奏
        return PacingStrategy.BALANCED

    async def analyze_timing_quality(self, timing_plan: TimingPlan) -> Dict[str, Any]:
        """分析时长分配质量"""
        analysis = {
            "overall_score": 0.0,
            "balance_score": timing_plan.duration_balance_score,
            "variety_score": timing_plan.pacing_variety_score,
            "constraint_violations": timing_plan.validate_constraints(),
            "recommendations": []
        }

        # 综合评分
        scores = [
            analysis["balance_score"],
            analysis["variety_score"],
            1.0 if len(analysis["constraint_violations"]) == 0 else 0.5
        ]
        analysis["overall_score"] = sum(scores) / len(scores)

        # 生成建议
        if analysis["balance_score"] < 0.8:
            analysis["recommendations"].append("建议调整总时长分配以更好匹配目标")

        if analysis["variety_score"] < 0.3:
            analysis["recommendations"].append("建议增加镜头时长的变化以提升节奏感")
        elif analysis["variety_score"] > 0.8:
            analysis["recommendations"].append("镜头时长变化较大，考虑适当平衡")

        if analysis["constraint_violations"]:
            analysis["recommendations"].append("存在时长约束违规，需要调整")

        return analysis

    def export_timing_report(self, timing_plan: TimingPlan) -> str:
        """导出时长分配报告"""
        report_lines = []
        report_lines.append(f"# 时长分配报告")
        report_lines.append(f"项目ID: {timing_plan.project_id}")
        report_lines.append(f"创建时间: {timing_plan.created_at.isoformat()}")
        report_lines.append(f"")
        report_lines.append(f"## 总体信息")
        report_lines.append(f"- 目标时长: {timing_plan.target_total_duration}秒")
        report_lines.append(f"- 实际时长: {timing_plan.actual_total_duration}秒")
        report_lines.append(f"- 节奏策略: {timing_plan.pacing_strategy.value}")
        report_lines.append(f"- 镜头数量: {len(timing_plan.shot_timings)}")
        report_lines.append(f"")
        report_lines.append(f"## 镜头时长分配")

        for i, timing in enumerate(timing_plan.shot_timings, 1):
            report_lines.append(f"### 镜头 {i}")
            report_lines.append(f"- 内容: {timing.content_segment[:50]}...")
            report_lines.append(f"- 重要性: {timing.importance_level.value}")
            report_lines.append(f"- 基础时长: {timing.base_duration:.1f}秒")
            report_lines.append(f"- 调整后时长: {timing.adjusted_duration:.1f}秒")
            if timing.adjustment_reason:
                report_lines.append(f"- 调整原因: {timing.adjustment_reason}")
            report_lines.append(f"")

        report_lines.append(f"## 质量指标")
        report_lines.append(f"- 时长平衡分: {timing_plan.duration_balance_score:.3f}")
        report_lines.append(f"- 节奏变化分: {timing_plan.pacing_variety_score:.3f}")

        violations = timing_plan.validate_constraints()
        if violations:
            report_lines.append(f"")
            report_lines.append(f"## 约束违规")
            for violation in violations:
                report_lines.append(f"- {violation}")

        return "\n".join(report_lines)
