#!/usr/bin/env python3
"""
基本使用示例
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.video.processor import VideoProcessor
from app.services.llm.analyzer import VideoAnalyzer
from app.services.tts.generator import TTSGenerator
from app.services.image.generator import ImageServiceManager
from app.services.video.editor import VideoEditor

def example_video_analysis():
    """视频分析示例"""
    print("\n🎬 视频分析示例")
    print("-" * 30)
    
    video_processor = VideoProcessor()
    video_analyzer = VideoAnalyzer()
    
    # 示例视频路径（需要实际存在的视频文件）
    video_path = "example_video.mp4"
    
    if os.path.exists(video_path):
        print(f"正在分析视频: {video_path}")
        
        # 获取视频信息
        video_info = video_processor.get_video_info(video_path)
        print(f"视频信息: {video_info}")
        
        # 分析视频内容
        analysis = asyncio.run(video_analyzer.analyze_video(video_path))
        print(f"分析结果: {analysis}")
    else:
        print("示例视频文件不存在，跳过分析")

async def example_tts_generation():
    """TTS语音生成示例"""
    print("\n🎤 TTS语音生成示例")
    print("-" * 30)
    
    tts_generator = TTSGenerator()
    
    text = "欢迎使用AI视频创作平台，这是一个强大的工具，可以帮助您创建精彩的视频内容。"
    
    print("正在生成语音...")
    audio_path = await tts_generator.generate_speech(text)
    
    if audio_path:
        print(f"✅ 语音生成成功！")
        print(f"文件路径: {audio_path}")
    else:
        print("❌ 语音生成失败")

async def example_image_generation():
    """图像生成示例"""
    print("\n🎨 图像生成示例")
    print("-" * 30)
    
    image_manager = ImageServiceManager()
    
    # 获取可用的生成器
    providers = image_manager.get_available_providers()
    print(f"可用的图像生成器: {providers}")
    
    prompt = "一个未来科技感的城市夜景，霓虹灯闪烁"
    
    print("正在生成图像...")
    print("注意：这可能需要一些时间，特别是没有GPU的情况下")
    
    try:
        # 尝试使用DALL-E生成
        if 'dalle' in providers:
            print("使用DALL-E生成图像...")
            image_path = await image_manager.generate_image(
                prompt=prompt,
                style="cyberpunk",
                provider="dalle",
                size=(1024, 1024)
            )
        # 尝试使用Stability AI生成
        elif 'stability' in providers:
            print("使用Stability AI生成图像...")
            image_path = await image_manager.generate_image(
                prompt=prompt,
                style="cyberpunk",
                provider="stability",
                size=(512, 512)
            )
        # 尝试使用Replicate生成
        elif 'replicate' in providers:
            print("使用Replicate生成图像...")
            image_path = await image_manager.generate_image(
                prompt=prompt,
                style="cyberpunk",
                provider="replicate",
                size=(512, 512)
            )
        # 使用本地模型
        else:
            print("使用本地模型生成图像...")
            image_path = await image_manager.generate_image(
                prompt=prompt,
                style="cyberpunk",
                provider="local",
                size=(512, 512)
            )
        
        if image_path:
            print(f"✅ 图像生成成功！")
            print(f"文件路径: {image_path}")
        else:
            print("❌ 图像生成失败")
            
    except Exception as e:
        print(f"❌ 图像生成失败: {str(e)}")
        print("请检查API密钥配置")

async def example_batch_image_generation():
    """批量图像生成示例"""
    print("\n🖼️ 批量图像生成示例")
    print("-" * 30)
    
    image_manager = ImageServiceManager()
    
    prompts = [
        "一只可爱的小猫在花园里玩耍",
        "夕阳西下的海滩风景",
        "现代科技感的办公环境"
    ]
    
    print("正在批量生成图像...")
    
    try:
        results = await image_manager.generator.generate_image_batch(
            prompts=prompts,
            style="realistic",
            size=(512, 512)
        )
        
        successful_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ 图像 {i+1} 生成失败: {str(result)}")
            elif result:
                print(f"✅ 图像 {i+1} 生成成功: {result}")
                successful_count += 1
        
        print(f"批量生成完成: {successful_count}/{len(prompts)} 成功")
        
    except Exception as e:
        print(f"❌ 批量生成失败: {str(e)}")

async def example_natural_language_edit():
    """自然语言编辑示例"""
    print("\n✏️ 自然语言编辑示例")
    print("-" * 30)
    
    video_editor = VideoEditor()
    
    # 示例编辑指令
    edit_instruction = "将视频的前10秒加速到2倍速，并在第5秒添加一个淡入淡出效果"
    
    print("正在处理编辑指令...")
    
    # 这里需要实际的视频文件
    video_path = "example_video.mp4"
    
    if os.path.exists(video_path):
        try:
            result = await video_editor.process_natural_language_edit(
                video_path, edit_instruction
            )
            print(f"编辑结果: {result}")
        except Exception as e:
            print(f"编辑失败: {str(e)}")
    else:
        print("示例视频文件不存在，跳过编辑")

async def main():
    """主函数"""
    print("🚀 Video Creator Platform 使用示例")
    print("=" * 50)
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置OPENAI_API_KEY，某些功能可能无法正常工作")
        print("请复制 env.example 为 .env 并填入您的API密钥")
        print()
    
    # 运行示例
    await example_video_analysis()
    await example_tts_generation()
    await example_image_generation()
    await example_batch_image_generation()
    await example_natural_language_edit()
    
    print("\n" + "=" * 50)
    print("🎉 示例运行完成！")
    print("\n💡 提示:")
    print("1. 这些示例展示了平台的核心功能")
    print("2. 实际使用时需要配置相应的API密钥")
    print("3. 图像生成支持多个第三方API：DALL-E、Stability AI、Replicate等")
    print("4. 可以通过API接口进行更复杂的操作")
    print("5. 批量图像生成功能可以同时处理多个提示词")

if __name__ == "__main__":
    asyncio.run(main()) 