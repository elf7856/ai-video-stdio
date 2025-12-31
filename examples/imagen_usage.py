#!/usr/bin/env python3
"""
Google Imagen 使用示例
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image.google_imagen_generator import GoogleImagenGenerator
from app.services.image.generator import ImageServiceManager


async def example_basic():
    """示例1: 基础使用"""
    print("=" * 60)
    print("示例1: 基础图像生成")
    print("=" * 60)

    generator = GoogleImagenGenerator()

    image_path = await generator.generate_image(
        prompt="A serene mountain lake at sunset",
        aspect_ratio="16:9",
        resolution="medium"
    )

    print(f"✅ 图像已保存到: {image_path}")


async def example_with_negative_prompt():
    """示例2: 使用负面提示词"""
    print("\n" + "=" * 60)
    print("示例2: 使用负面提示词")
    print("=" * 60)

    generator = GoogleImagenGenerator()

    image_path = await generator.generate_image(
        prompt="A realistic portrait of a person",
        negative_prompt="cartoon, anime, low quality, blurry",
        aspect_ratio="3:4",
        resolution="high"
    )

    print(f"✅ 图像已保存到: {image_path}")


async def example_batch_generation():
    """示例3: 批量生成"""
    print("\n" + "=" * 60)
    print("示例3: 批量生成多张图像")
    print("=" * 60)

    generator = GoogleImagenGenerator()

    prompts = [
        "A modern minimalist living room",
        "A cozy coffee shop interior",
        "A beautiful home office setup"
    ]

    image_paths = await generator.generate_image_batch(
        prompts=prompts,
        aspect_ratio="16:9"
    )

    print(f"✅ 成功生成 {len([p for p in image_paths if p])} 张图像")
    for i, path in enumerate(image_paths):
        if path:
            print(f"   {i+1}. {path}")


async def example_via_service_manager():
    """示例4: 通过服务管理器使用"""
    print("\n" + "=" * 60)
    print("示例4: 通过ImageServiceManager使用")
    print("=" * 60)

    manager = ImageServiceManager()

    # 查看可用的生成器
    available = manager.get_available_providers()
    print(f"可用的生成器: {', '.join(available)}")

    # 使用google_imagen
    image_path = await manager.generate_image(
        prompt="A futuristic cyberpunk city at night",
        provider="google_imagen",
        size=(1024, 576)  # 会自动转换为16:9
    )

    print(f"✅ 图像已保存到: {image_path}")


async def example_different_aspect_ratios():
    """示例5: 测试不同的宽高比"""
    print("\n" + "=" * 60)
    print("示例5: 不同宽高比示例")
    print("=" * 60)

    generator = GoogleImagenGenerator()

    test_cases = [
        ("1:1", "A square composition of geometric shapes"),
        ("9:16", "A tall building reaching into the sky"),
        ("16:9", "A wide panoramic view of a beach"),
    ]

    for ratio, prompt in test_cases:
        print(f"\n生成 {ratio} 图像...")
        image_path = await generator.generate_image(
            prompt=prompt,
            aspect_ratio=ratio
        )
        print(f"✅ {ratio}: {image_path}")


async def example_capabilities():
    """示例6: 获取模型能力信息"""
    print("\n" + "=" * 60)
    print("示例6: 查看模型能力")
    print("=" * 60)

    generator = GoogleImagenGenerator()
    capabilities = generator.get_capabilities()

    print(f"提供商: {capabilities['provider']}")
    print(f"模型: {capabilities['model']}")
    print(f"API状态: {capabilities['api_status']}")

    print("\n支持的宽高比:")
    for ratio_info in capabilities['supported_aspect_ratios']:
        print(f"  • {ratio_info['ratio']} ({ratio_info['resolution']}) - {ratio_info['description']}")

    print("\n特性:")
    for feature in capabilities['features']:
        print(f"  • {feature}")


async def main():
    """运行所有示例"""

    print("\n🎨 Google Imagen 使用示例集合\n")

    # 运行选定的示例
    # 注意：取消注释你想运行的示例

    # await example_basic()
    # await example_with_negative_prompt()
    # await example_batch_generation()  # 会生��3张图
    # await example_via_service_manager()
    # await example_different_aspect_ratios()  # 会生成3张图
    await example_capabilities()  # 无需生成图像

    print("\n" + "=" * 60)
    print("✅ 示例运行完成")
    print("=" * 60)
    print("\n提示: 编辑此文件取消注释其他示例来运行")


if __name__ == "__main__":
    asyncio.run(main())
