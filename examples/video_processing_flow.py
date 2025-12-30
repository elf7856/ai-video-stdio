#!/usr/bin/env python3
"""
完整的视频处理流程示例
演示从URL下载视频到分析、编辑的完整流程
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.video.manager import VideoProcessingManager
from app.services.video.downloader import VideoDownloader

async def example_complete_video_flow():
    """完整的视频处理流程示例"""
    print("🎬 完整视频处理流程示例")
    print("=" * 50)
    
    # 初始化视频处理管理器
    video_manager = VideoProcessingManager()
    
    # 示例视频URL（请替换为实际的视频URL）
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 示例URL
    
    print(f"1. 开始处理视频URL: {video_url}")
    print("-" * 30)
    
    # 步骤1: 从URL下载并处理视频
    result = await video_manager.process_video_from_url(
        url=video_url,
        auto_analyze=True
    )
    
    if not result["success"]:
        print(f"❌ 视频处理失败: {result['error']}")
        return
    
    print(f"✅ 视频下载成功: {result['video_title']}")
    print(f"📁 文件路径: {result['video_path']}")
    print(f"📊 视频信息: {result['video_info']}")
    print(f"🏷️ 平台: {result['platform']}")
    
    if result["analysis"]:
        print(f"📝 分析结果: {result['analysis']}")
    
    print(f"🖼️ 关键帧数量: {len(result['key_frames'])}")
    
    # 步骤2: 生成视频摘要
    print("\n2. 生成视频摘要")
    print("-" * 30)
    
    summary_result = await video_manager.generate_video_summary(
        result["video_path"], 
        summary_type="text"
    )
    
    if summary_result["success"]:
        print(f"📄 文本摘要: {summary_result['content']}")
    else:
        print(f"❌ 摘要生成失败: {summary_result['error']}")
    
    # 步骤3: 自然语言编辑示例
    print("\n3. 自然语言编辑示例")
    print("-" * 30)
    
    edit_instructions = [
        "在视频开头添加一个标题文字",
        "将视频转换为黑白风格",
        "在视频中间插入一个风景图片"
    ]
    
    for i, instruction in enumerate(edit_instructions, 1):
        print(f"\n编辑指令 {i}: {instruction}")
        
        edit_result = await video_manager.process_natural_language_edit(
            result["video_path"], 
            instruction
        )
        
        if edit_result["success"]:
            print(f"✅ 编辑类型: {edit_result['edit_type']}")
            print(f"📝 内容描述: {edit_result['content_description']}")
            
            if edit_result["result"]["success"]:
                print(f"🎬 编辑结果: {edit_result['result']}")
            else:
                print(f"❌ 编辑执行失败: {edit_result['result']['error']}")
        else:
            print(f"❌ 编辑理解失败: {edit_result['error']}")

async def example_video_download_only():
    """仅下载视频示例"""
    print("\n📥 仅下载视频示例")
    print("=" * 50)
    
    downloader = VideoDownloader()
    
    # 示例URL
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.bilibili.com/video/BV1xx411c7mu",  # 示例B站URL
        "https://www.tiktok.com/@username/video/1234567890"  # 示例TikTok URL
    ]
    
    for url in test_urls:
        print(f"\n尝试下载: {url}")
        
        # 首先获取视频信息
        info_result = await downloader.get_video_info(url)
        if info_result["success"]:
            print(f"📊 视频信息: {info_result}")
        else:
            print(f"❌ 获取信息失败: {info_result['error']}")
            continue
        
        # 然后下载视频
        download_result = await downloader.download_video(url)
        if download_result["success"]:
            print(f"✅ 下载成功: {download_result['title']}")
            print(f"📁 文件路径: {download_result['file_path']}")
        else:
            print(f"❌ 下载失败: {download_result['error']}")

async def example_video_analysis():
    """视频分析示例"""
    print("\n🔍 视频分析示例")
    print("=" * 50)
    
    video_manager = VideoProcessingManager()
    
    # 假设有一个本地视频文件
    video_path = "example_video.mp4"
    
    if os.path.exists(video_path):
        print(f"分析视频: {video_path}")
        
        # 分析视频内容
        analysis_result = await video_manager.analyze_video_content(video_path)
        
        if analysis_result["success"]:
            print(f"✅ 分析成功")
            print(f"📊 视频信息: {analysis_result['video_info']}")
            print(f"📝 分析结果: {analysis_result['analysis']}")
            print(f"🖼️ 关键帧: {len(analysis_result['key_frames'])} 个")
            
            if analysis_result["audio_path"]:
                print(f"🎵 音频提取: {analysis_result['audio_path']}")
        else:
            print(f"❌ 分析失败: {analysis_result['error']}")
    else:
        print(f"⚠️ 示例视频文件不存在: {video_path}")

async def example_supported_platforms():
    """支持的平台示例"""
    print("\n🌐 支持的视频平台")
    print("=" * 50)
    
    downloader = VideoDownloader()
    
    platforms = [
        ("YouTube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("Bilibili", "https://www.bilibili.com/video/BV1xx411c7mu"),
        ("TikTok", "https://www.tiktok.com/@username/video/1234567890"),
        ("Instagram", "https://www.instagram.com/p/ABC123/"),
        ("Twitter", "https://twitter.com/user/status/1234567890"),
        ("通用链接", "https://example.com/video.mp4")
    ]
    
    for platform_name, url in platforms:
        platform = downloader._identify_platform(url)
        print(f"{platform_name}: {platform}")

def main():
    """主函数"""
    print("🚀 视频处理平台 - 完整流程演示")
    print("=" * 60)
    
    # 运行示例
    asyncio.run(example_supported_platforms())
    asyncio.run(example_video_download_only())
    asyncio.run(example_video_analysis())
    asyncio.run(example_complete_video_flow())
    
    print("\n✅ 所有示例完成！")
    print("\n📋 使用说明:")
    print("1. 确保已安装所有依赖: pip install -r requirements.txt")
    print("2. 配置环境变量（API密钥等）")
    print("3. 替换示例中的URL为实际的视频链接")
    print("4. 运行服务器: python -m uvicorn app.main:app --reload")
    print("5. 访问API文档: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 