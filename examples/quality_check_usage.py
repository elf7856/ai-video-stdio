"""
质量检查服务使用示例

展示如何使用质量检查功能检测视频质量并自动重新生成低质量片段
"""

import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.quality import (
    VideoQualityChecker,
    QualityCheckConfig,
    check_video_quality,
    check_project_quality
)


def example_check_single_video():
    """示例：检查单个视频质量"""
    print("\n" + "="*60)
    print("示例 1: 检查单个视频质量")
    print("="*60)

    # 配置
    config = QualityCheckConfig(
        keyframe_count=5,              # 提取5个关键帧
        min_acceptable_score=0.5,      # 最低可接受分数
        regeneration_threshold=0.4,    # 低于此分数需要重新生成
        use_llm_analysis=True,         # 使用LLM分析
        weights={
            "visual_consistency": 0.3,  # 视觉一致性权重
            "content_match": 0.4,       # 内容匹配度权重
            "technical_quality": 0.3    # 技术质量权重
        }
    )

    # 检查视频（替换为实际视频路径）
    video_path = "outputs/videos/example.mp4"
    prompt = "一只可爱的猫咪在阳光下玩耍，背景是绿色的草地"

    if not os.path.exists(video_path):
        print(f"⚠️ 示例视频不存在: {video_path}")
        print("请创建一个测试视频或修改路径")
        return

    result = check_video_quality(
        video_path=video_path,
        prompt=prompt,
        config=config
    )

    # 打印结果
    print(f"\n📊 质量检查结果:")
    print(f"  综合分数: {result.overall_score:.2f} ({result.overall_level.value})")
    print(f"  视觉一致性: {result.visual_consistency.score:.2f}")
    print(f"    - 色彩一致性: {result.visual_consistency.color_consistency:.2f}")
    print(f"    - 风格一致性: {result.visual_consistency.style_consistency:.2f}")
    print(f"    - 光照一致性: {result.visual_consistency.lighting_consistency:.2f}")
    print(f"  内容匹配度: {result.content_match.score:.2f}")
    print(f"    - 语义匹配: {result.content_match.semantic_match:.2f}")
    print(f"    - 视觉匹配: {result.content_match.visual_match:.2f}")
    print(f"  技术质量: {result.technical_quality.score:.2f}")
    print(f"    - 分辨率: {result.technical_quality.resolution}")
    print(f"    - 帧率: {result.technical_quality.fps}")

    if result.needs_regeneration:
        print(f"\n⚠️ 建议重新生成!")
        print(f"  原因: {result.regeneration_reason}")
        if result.regeneration_suggestions:
            print(f"  建议:")
            for s in result.regeneration_suggestions[:3]:
                print(f"    - {s}")


def example_check_project():
    """示例：检查整个项目的视频质量"""
    print("\n" + "="*60)
    print("示例 2: 检查项目视频质量")
    print("="*60)

    # 模拟项目中的多个视频
    videos = [
        {
            "path": "outputs/videos/shot_1.mp4",
            "prompt": "开场镜头：城市的日出，高楼大厦的轮廓在晨光中渐渐清晰",
            "shot_index": 0,
            "shot_id": "opening"
        },
        {
            "path": "outputs/videos/shot_2.mp4",
            "prompt": "主角走在街道上，周围是繁忙的人群",
            "shot_index": 1,
            "shot_id": "main_1"
        },
        {
            "path": "outputs/videos/shot_3.mp4",
            "prompt": "特写镜头：主角的表情从迷茫变为坚定",
            "shot_index": 2,
            "shot_id": "closeup"
        }
    ]

    # 检查哪些视频存在
    existing_videos = [v for v in videos if os.path.exists(v["path"])]

    if not existing_videos:
        print("⚠️ 没有找到示例视频文件")
        print("请创建以下测试视频:")
        for v in videos:
            print(f"  - {v['path']}")
        return

    # 执行质量检查
    report = check_project_quality(
        videos=existing_videos,
        project_id="demo_project"
    )

    # 打印报告
    print(f"\n📊 项目质量报告:")
    print(f"  项目ID: {report.project_id}")
    print(f"  综合分数: {report.overall_score:.2f} ({report.overall_level.value})")
    print(f"  视觉一致性: {report.overall_visual_consistency:.2f}")
    print(f"  内容匹配度: {report.overall_content_match:.2f}")
    print(f"  技术质量: {report.overall_technical_quality:.2f}")

    print(f"\n  各镜头质量:")
    for shot in report.shots:
        status = "✅" if not shot.needs_regeneration else "❌"
        print(f"    {status} 镜头 {shot.shot_index}: {shot.overall_score:.2f}")

    if report.shots_to_regenerate:
        print(f"\n  需要重新生成的镜头: {report.shots_to_regenerate}")

    print(f"\n  总结: {report.summary}")
    if report.recommendations:
        print(f"  建议:")
        for r in report.recommendations:
            print(f"    - {r}")


def example_quality_config():
    """示例：自定义质量检查配置"""
    print("\n" + "="*60)
    print("示例 3: 自定义质量检查配置")
    print("="*60)

    # 严格配置（适用于高质量要求）
    strict_config = QualityCheckConfig(
        keyframe_count=10,              # 更多关键帧
        min_acceptable_score=0.7,       # 更高的可接受标准
        regeneration_threshold=0.6,     # 更高的重新生成阈值
        use_llm_analysis=True,
        weights={
            "visual_consistency": 0.35,
            "content_match": 0.45,      # 更重视内容匹配
            "technical_quality": 0.20
        }
    )

    # 宽松配置（适用于快速迭代）
    relaxed_config = QualityCheckConfig(
        keyframe_count=3,               # 更少关键帧，更快
        min_acceptable_score=0.4,       # 更低的可接受标准
        regeneration_threshold=0.3,
        use_llm_analysis=False,         # 不使用LLM，纯技术指标
        weights={
            "visual_consistency": 0.25,
            "content_match": 0.25,
            "technical_quality": 0.50   # 更重视技术质量
        }
    )

    # 仅技术检查（最快）
    tech_only_config = QualityCheckConfig(
        check_visual_consistency=False,
        check_content_match=False,
        check_technical_quality=True,
        use_llm_analysis=False
    )

    print("严格配置:")
    print(f"  关键帧数: {strict_config.keyframe_count}")
    print(f"  可接受分数: {strict_config.min_acceptable_score}")
    print(f"  权重: {strict_config.weights}")

    print("\n宽松配置:")
    print(f"  关键帧数: {relaxed_config.keyframe_count}")
    print(f"  可接受分数: {relaxed_config.min_acceptable_score}")
    print(f"  权重: {relaxed_config.weights}")

    print("\n仅技术检查:")
    print(f"  视觉一致性: {tech_only_config.check_visual_consistency}")
    print(f"  内容匹配: {tech_only_config.check_content_match}")
    print(f"  技术质量: {tech_only_config.check_technical_quality}")


def main():
    """运行所有示例"""
    print("="*60)
    print("视频质量检查服务 - 使用示例")
    print("="*60)

    # 示例3：配置说明（不需要视频文件）
    example_quality_config()

    # 示例1和2需要实际视频文件
    print("\n" + "-"*60)
    print("以下示例需要实际视频文件，请确保文件存在后运行")
    print("-"*60)

    # example_check_single_video()
    # example_check_project()


if __name__ == "__main__":
    main()
