"""
智能视频时长规划服务
根据用户输入的内容（topic/script）自动计算合理的视频时长
"""
import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class DurationPlanner:
    """视频时长智能规划器"""

    # 配置参数
    MIN_DURATION = 30  # 最短30秒
    MAX_DURATION = 300  # 最长5分钟
    DEFAULT_DURATION = 60  # 默认60秒

    # 语速参数（字/秒）
    SPEECH_RATE_SLOW = 3  # 慢速：3字/秒（教学、严肃内容）
    SPEECH_RATE_NORMAL = 4.5  # 正常：4.5字/秒（标准内容）
    SPEECH_RATE_FAST = 6  # 快速：6字/秒（娱乐、快节奏）

    # 风格对应的语速
    STYLE_SPEECH_RATES = {
        "专业": SPEECH_RATE_NORMAL,
        "科技": SPEECH_RATE_NORMAL,
        "教育": SPEECH_RATE_SLOW,
        "生活": SPEECH_RATE_NORMAL,
        "娱乐": SPEECH_RATE_FAST,
        "商业": SPEECH_RATE_NORMAL,
        "艺术": SPEECH_RATE_SLOW,
        "纪录片": SPEECH_RATE_SLOW,
        "轻松": SPEECH_RATE_FAST,
        "严肃": SPEECH_RATE_SLOW,
    }

    @classmethod
    def estimate_duration_from_topic(cls, topic: str, style: str = "专业") -> int:
        """
        从主题估算时长（用户只提供topic，还没有脚本时）

        Args:
            topic: 用户输入的主题/需求
            style: 视频风格

        Returns:
            估算的时长（秒）
        """
        # 计算主题字数
        topic_length = len(topic.strip())

        # 基于主题长度的启发式规则
        if topic_length < 20:
            # 非常简短的主题：30-60秒
            base_duration = 45
        elif topic_length < 50:
            # 中等主题：45-90秒
            base_duration = 60
        elif topic_length < 100:
            # 较长主题：60-120秒
            base_duration = 90
        else:
            # 很长的主题：90-180秒
            base_duration = 120

        # 根据风格调整
        style_multiplier = cls._get_style_multiplier(style)
        estimated_duration = int(base_duration * style_multiplier)

        # 确保在合理范围内
        final_duration = cls._clamp_duration(estimated_duration)

        logger.info(
            f"Topic估算: 长度={topic_length}, 基础={base_duration}s, "
            f"风格系数={style_multiplier}, 最终={final_duration}s"
        )

        return final_duration

    @classmethod
    def estimate_duration_from_script(
        cls, script: str, style: str = "专业"
    ) -> int:
        """
        从脚本内容计算时长（已有脚本时）

        Args:
            script: 脚本内容
            style: 视频风格

        Returns:
            估算的时长（秒）
        """
        # 清理脚本：去除多余空白、标点符号
        cleaned_script = cls._clean_script(script)

        # 计算有效字数（中英文混合）
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", cleaned_script))
        english_words = len(re.findall(r"[a-zA-Z]+", cleaned_script))

        # 英文单词折算成中文字数（1个英文单词 ≈ 2个中文字）
        total_chars = chinese_chars + (english_words * 2)

        # 获取该风格的语速
        speech_rate = cls.STYLE_SPEECH_RATES.get(style, cls.SPEECH_RATE_NORMAL)

        # 计算基础时长
        base_duration = total_chars / speech_rate

        # 添加缓冲时间
        buffer_time = cls._calculate_buffer_time(base_duration, style)
        total_duration = base_duration + buffer_time

        # 确保在合理范围内
        final_duration = cls._clamp_duration(int(total_duration))

        logger.info(
            f"脚本估算: 中文={chinese_chars}字, 英文={english_words}词, "
            f"总={total_chars}字, 语速={speech_rate}字/秒, "
            f"基础={base_duration:.1f}s, 缓冲={buffer_time:.1f}s, "
            f"最终={final_duration}s"
        )

        return final_duration

    @classmethod
    def plan_shot_durations(
        cls, total_duration: int, shot_count: int, importance_scores: list = None
    ) -> list:
        """
        分配各镜头的时长

        Args:
            total_duration: 总时长（秒）
            shot_count: 镜头数量
            importance_scores: 各镜头的重要性分数（0-1），如果不提供则平均分配

        Returns:
            各镜头的时长列表
        """
        if not importance_scores:
            # 平均分配
            avg_duration = total_duration / shot_count
            return [round(avg_duration, 1)] * shot_count

        # 根据重要性加权分配
        if len(importance_scores) != shot_count:
            raise ValueError(
                f"Importance scores count ({len(importance_scores)}) "
                f"must match shot count ({shot_count})"
            )

        # 归一化重要性分数
        total_importance = sum(importance_scores)
        normalized_scores = [
            score / total_importance for score in importance_scores
        ]

        # 计算各镜头时长
        shot_durations = [
            round(score * total_duration, 1) for score in normalized_scores
        ]

        # 确保总和正确（处理四舍五入误差）
        duration_sum = sum(shot_durations)
        if duration_sum != total_duration:
            # 调整最长的那个镜头
            max_idx = shot_durations.index(max(shot_durations))
            shot_durations[max_idx] += total_duration - duration_sum

        logger.info(
            f"镜头时长分配: 总={total_duration}s, 数量={shot_count}, "
            f"分配={shot_durations}"
        )

        return shot_durations

    @classmethod
    def suggest_shot_count(cls, duration: int, style: str = "专业") -> int:
        """
        根据总时长建议镜头数量

        Args:
            duration: 总时长（秒）
            style: 视频风格

        Returns:
            建议的镜头数量
        """
        # 不同风格的平均镜头时长
        avg_shot_durations = {
            "专业": 10,  # 专业风格：平均10秒/镜头
            "科技": 8,  # 科技风格：稍快
            "教育": 12,  # 教育风格：稍慢，便于理解
            "生活": 8,  # 生活风格：节奏较快
            "娱乐": 6,  # 娱乐风格：快节奏
            "商业": 10,  # 商业风格：标准节奏
            "艺术": 12,  # 艺术风格：慢节奏，有美感
            "纪录片": 15,  # 纪录片：慢节奏，深度
            "轻松": 7,  # 轻松风格：较快
            "严肃": 12,  # 严肃风格：较慢
        }

        avg_duration = avg_shot_durations.get(style, 10)
        shot_count = max(3, min(20, round(duration / avg_duration)))

        logger.info(f"镜头数量建议: 时长={duration}s, 风格={style}, 建议={shot_count}个")

        return shot_count

    @classmethod
    def _clean_script(cls, script: str) -> str:
        """清理脚本内容"""
        # 去除多余空白
        cleaned = re.sub(r"\s+", " ", script.strip())
        # 去除标点符号对字数计算的影响较小，保留
        return cleaned

    @classmethod
    def _get_style_multiplier(cls, style: str) -> float:
        """获取风格时长调整系数"""
        multipliers = {
            "专业": 1.0,
            "科技": 1.0,
            "教育": 1.2,  # 教育类需要更多时间解释
            "生活": 0.9,  # 生活类可以稍快
            "娱乐": 0.8,  # 娱乐类节奏快
            "商业": 1.0,
            "艺术": 1.1,  # 艺术类需要留白
            "纪录片": 1.3,  # 纪录片节奏慢
            "轻松": 0.85,
            "严肃": 1.1,
        }
        return multipliers.get(style, 1.0)

    @classmethod
    def _calculate_buffer_time(cls, base_duration: float, style: str) -> float:
        """
        计算缓冲时间（用于开场、结尾、过渡等）

        缓冲时间计算：
        - 开场: 3-5秒
        - 结尾: 2-3秒
        - 过渡: 基础时长的10-15%
        """
        # 固定部分：开场+结尾
        fixed_buffer = 5 + 3  # 8秒

        # 动态部分：基于内容长度
        dynamic_buffer = base_duration * 0.12  # 12%

        # 根据风格调整
        style_factors = {
            "娱乐": 0.8,  # 娱乐类缓冲少
            "艺术": 1.3,  # 艺术类需要更多留白
            "纪录片": 1.2,  # 纪录片需要氛围营造
        }
        factor = style_factors.get(style, 1.0)

        return (fixed_buffer + dynamic_buffer) * factor

    @classmethod
    def _clamp_duration(cls, duration: int) -> int:
        """将时长限制在合理范围内"""
        return max(cls.MIN_DURATION, min(cls.MAX_DURATION, duration))


# 便捷函数

def estimate_video_duration(
    content: str, style: str = "专业", content_type: str = "topic"
) -> int:
    """
    估算视频时长（便捷函数）

    Args:
        content: 内容（topic或script）
        style: 风格
        content_type: 内容类型 ("topic" 或 "script")

    Returns:
        估算的时长（秒）
    """
    if content_type == "script":
        return DurationPlanner.estimate_duration_from_script(content, style)
    else:
        return DurationPlanner.estimate_duration_from_topic(content, style)


def plan_video_structure(
    content: str,
    style: str = "专业",
    content_type: str = "topic",
) -> Tuple[int, int, list]:
    """
    规划视频结构（便捷函数）

    Args:
        content: 内容
        style: 风格
        content_type: 内容类型

    Returns:
        (总时长, 镜头数量, 各镜头时长列表)
    """
    # 估算总时长
    total_duration = estimate_video_duration(content, style, content_type)

    # 建议镜头数量
    shot_count = DurationPlanner.suggest_shot_count(total_duration, style)

    # 分配镜头时长
    shot_durations = DurationPlanner.plan_shot_durations(
        total_duration, shot_count
    )

    return total_duration, shot_count, shot_durations


# 使用示例
if __name__ == "__main__":
    # 示例1：从topic估算
    topic = "如何使用AI生成视频，包括脚本创作、分镜规划和视频渲染的完整流程"
    duration1 = DurationPlanner.estimate_duration_from_topic(topic, "教育")
    print(f"Topic估算时长: {duration1}秒")

    # 示例2：从script估算
    script = """
    欢迎来到AI视频生成教程。今天我们将学习如何使用最新的AI技术，
    从零开始创建一个专业的视频。首先，我们需要创作一个吸引人的脚本。
    脚本是视频的灵魂，一个好的脚本能够吸引观众的注意力，并清晰地传达
    你想要表达的信息。接下来，我们会学习如何将脚本分解成多个镜头，
    每个镜头都有其独特的视觉元素和叙事目的。最后，我们会使用AI工具
    将这些镜头渲染成真实的视频画面。整个过程既简单又高效，让我们开始吧！
    """
    duration2 = DurationPlanner.estimate_duration_from_script(script, "教育")
    print(f"Script估算时长: {duration2}秒")

    # 示例3：规划视频结构
    total, count, durations = plan_video_structure(script, "教育", "script")
    print(f"\n视频结构规划:")
    print(f"  总时长: {total}秒")
    print(f"  镜头数: {count}个")
    print(f"  各镜头时长: {durations}")
