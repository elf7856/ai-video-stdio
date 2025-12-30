#!/usr/bin/env python3
"""
视频ASR分析示例
展示如何使用ASR（自动语音识别）功能分析视频内容

使用方法:
python examples/video_asr_analysis.py
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.audio.asr_service import asr_service
from app.services.analysis.video_analyzer import video_analyzer
from app.services.video.manager import VideoProcessingManager

async def test_asr_service():
    """测试ASR服务基本功能"""
    print("🎤 测试ASR服务")
    print("=" * 60)
    
    # 检查可用的ASR提供商
    available_providers = asr_service.get_available_providers()
    print(f"可用的ASR提供商: {available_providers}")
    
    # 健康检查
    health_status = asr_service.health_check()
    print(f"健康状态: {health_status}")
    
    # 支持的语言
    supported_languages = asr_service.get_supported_languages()
    print(f"支持的语言: {supported_languages}")
    
    return len(available_providers) > 0

async def analyze_video_with_asr(video_path: str, language: str = "zh-CN"):
    """使用ASR分析视频"""
    print(f"\n🎬 使用ASR分析视频: {video_path}")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return None
    
    try:
        # 使用视频分析器的ASR功能
        result = video_analyzer.analyze_video_with_asr(
            video_path=video_path,
            language=language
        )
        
        if result["success"]:
            print("✅ ASR分析成功！")
            
            # 显示基本信息
            video_info = result.get("video_info", {})
            print(f"📊 视频信息:")
            print(f"   - 文件路径: {video_path}")
            print(f"   - 时长: {video_info.get('duration', 'N/A')} 秒")
            print(f"   - 分辨率: {video_info.get('resolution', 'N/A')}")
            
            # 显示ASR结果
            asr_result = video_info.get("asr_result")
            if asr_result:
                print(f"\n🎤 语音识别结果:")
                print(f"   - 提供商: {asr_result.get('provider', 'N/A')}")
                print(f"   - 置信度: {asr_result.get('confidence', 0):.2f}")
                print(f"   - 语言: {asr_result.get('language', 'N/A')}")
                print(f"   - 文本长度: {len(asr_result.get('text', ''))} 字符")
                
                # 显示转录文本（前200字符）
                transcript = asr_result.get('text', '')
                if transcript:
                    print(f"\n📝 转录文本预览:")
                    print(f"   {transcript[:200]}{'...' if len(transcript) > 200 else ''}")
            
            # 显示分析结果
            analysis = result.get("analysis")
            if analysis and analysis.get("success"):
                print(f"\n🔍 内容分析结果:")
                print(f"   - 摘要: {analysis.get('summary', 'N/A')}")
                print(f"   - 关键词: {analysis.get('key_points', [])}")
                print(f"   - 情感: {analysis.get('sentiment', 'N/A')}")
                print(f"   - 分类: {analysis.get('category', 'N/A')}")
                print(f"   - 标签: {analysis.get('tags', [])}")
            
            return result
        else:
            print(f"❌ ASR分析失败: {result.get('error', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ ASR分析异常: {str(e)}")
        return None

async def analyze_video_with_transcript(video_path: str, language: str = "zh-CN"):
    """使用完整转录功能分析视频"""
    print(f"\n🎯 完整转录分析: {video_path}")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return None
    
    try:
        # 使用视频管理器的完整转录功能
        video_manager = VideoProcessingManager()
        result = await video_manager.analyze_video_with_transcript(video_path, language)
        
        if result["success"]:
            print("✅ 完整转录分析成功！")
            
            # 显示转录结果
            transcript = result.get("transcript", "")
            timestamps = result.get("timestamps", [])
            
            print(f"📝 转录文本: {len(transcript)} 字符")
            print(f"⏱️ 时间戳: {len(timestamps)} 个片段")
            
            # 显示时间戳片段（前5个）
            if timestamps:
                print(f"\n⏰ 时间戳片段预览:")
                for i, (start, end, text) in enumerate(timestamps[:5]):
                    print(f"   [{start:.1f}s - {end:.1f}s]: {text}")
                if len(timestamps) > 5:
                    print(f"   ... 还有 {len(timestamps) - 5} 个片段")
            
            # 显示关键时刻
            key_moments = result.get("key_moments")
            if key_moments and key_moments.get("success"):
                moments = key_moments.get("key_moments", [])
                print(f"\n⭐ 关键时刻 ({len(moments)} 个):")
                for i, moment in enumerate(moments, 1):
                    if isinstance(moment, dict):
                        desc = moment.get("description", "")
                        timestamp = moment.get("timestamp")
                        confidence = moment.get("confidence", 0)
                        print(f"   {i}. {desc}")
                        if timestamp:
                            print(f"      时间: {timestamp:.1f}s (置信度: {confidence:.2f})")
                    else:
                        print(f"   {i}. {moment}")
            
            return result
        else:
            print(f"❌ 完整转录分析失败: {result.get('error', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 完整转录分析异常: {str(e)}")
        return None

async def extract_video_highlights(video_path: str, max_highlights: int = 3):
    """提取视频精彩片段"""
    print(f"\n🎯 提取视频精彩片段: {video_path}")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return None
    
    try:
        # 使用视频管理器提取精彩片段
        video_manager = VideoProcessingManager()
        result = await video_manager.extract_video_highlights(
            video_path, max_highlights=max_highlights
        )
        
        if result["success"]:
            highlights = result.get("highlights", [])
            print(f"✅ 成功提取 {len(highlights)} 个精彩片段")
            
            for i, highlight in enumerate(highlights, 1):
                print(f"\n🎬 精彩片段 {i}:")
                print(f"   描述: {highlight.get('description', 'N/A')}")
                print(f"   时间: {highlight.get('start_time', 0):.1f}s - {highlight.get('end_time', 0):.1f}s")
                print(f"   置信度: {highlight.get('confidence', 0):.2f}")
                
                original_text = highlight.get('original_text', '')
                if original_text:
                    print(f"   原文: {original_text[:100]}{'...' if len(original_text) > 100 else ''}")
            
            return result
        else:
            print(f"❌ 精彩片段提取失败: {result.get('error', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 精彩片段提取异常: {str(e)}")
        return None

async def compare_analysis_methods(video_path: str):
    """比较不同分析方法的结果"""
    print(f"\n📊 比较分析方法: {video_path}")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    try:
        video_manager = VideoProcessingManager()
        
        # 方法1: 不使用ASR
        print("1️⃣ 不使用ASR的分析...")
        result_no_asr = await video_manager.analyze_video_content(video_path, use_asr=False)
        
        # 方法2: 使用ASR
        print("2️⃣ 使用ASR的分析...")
        result_with_asr = await video_manager.analyze_video_content(video_path, use_asr=True)
        
        # 比较结果
        print("\n📈 分析结果比较:")
        print("-" * 40)
        
        if result_no_asr["success"] and result_with_asr["success"]:
            analysis_no_asr = result_no_asr.get("analysis", {})
            analysis_with_asr = result_with_asr.get("analysis", {})
            
            print("不使用ASR:")
            print(f"  摘要: {analysis_no_asr.get('summary', 'N/A')}")
            print(f"  关键词数量: {len(analysis_no_asr.get('key_points', []))}")
            
            print("\n使用ASR:")
            print(f"  摘要: {analysis_with_asr.get('summary', 'N/A')}")
            print(f"  关键词数量: {len(analysis_with_asr.get('key_points', []))}")
            print(f"  使用了ASR: {result_with_asr.get('used_asr', False)}")
            
            # 比较摘要长度
            summary_no_asr = analysis_no_asr.get('summary', '')
            summary_with_asr = analysis_with_asr.get('summary', '')
            
            print(f"\n📝 摘要长度比较:")
            print(f"  不使用ASR: {len(summary_no_asr)} 字符")
            print(f"  使用ASR: {len(summary_with_asr)} 字符")
            print(f"  差异: {len(summary_with_asr) - len(summary_no_asr):+d} 字符")
        
    except Exception as e:
        print(f"❌ 比较分析失败: {str(e)}")

async def save_analysis_results(video_path: str, results: dict):
    """保存分析结果到文件"""
    try:
        # 创建结果目录
        results_dir = Path("analysis_results")
        results_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        video_name = Path(video_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_name}_asr_analysis_{timestamp}.json"
        
        # 保存结果
        output_path = results_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 分析结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"❌ 保存结果失败: {str(e)}")

async def main():
    """主函数"""
    print("🎤 视频ASR分析示例")
    print("=" * 60)
    
    # 1. 测试ASR服务
    asr_available = await test_asr_service()
    
    if not asr_available:
        print("\n❌ 没有可用的ASR提供商")
        print("请确保至少配置了以下之一:")
        print("- OpenAI API密钥 (用于Whisper)")
        print("- 本地Whisper模型 (pip install openai-whisper)")
        print("- Google Cloud Speech API")
        return
    
    # 2. 查找测试视频
    test_videos = [
        "uploads/test_video.mp4",
        "test_video.mp4",
        "sample_video.mp4"
    ]
    
    video_path = None
    for path in test_videos:
        if os.path.exists(path):
            video_path = path
            break
    
    if not video_path:
        print(f"\n⚠️ 未找到测试视频文件")
        print("请将视频文件放在以下位置之一:")
        for path in test_videos:
            print(f"  - {path}")
        
        # 询问用户是否手动指定视频路径
        try:
            manual_path = input("\n请输入视频文件路径（或按Enter跳过）: ").strip()
            if manual_path and os.path.exists(manual_path):
                video_path = manual_path
            else:
                print("跳过视频分析测试")
                return
        except KeyboardInterrupt:
            print("\n用户中断")
            return
    
    print(f"\n🎬 使用测试视频: {video_path}")
    
    # 3. 执行各种分析
    results = {}
    
    # ASR基础分析
    print("\n" + "="*60)
    asr_result = await analyze_video_with_asr(video_path)
    if asr_result:
        results["asr_analysis"] = asr_result
    
    # 完整转录分析
    print("\n" + "="*60)
    transcript_result = await analyze_video_with_transcript(video_path)
    if transcript_result:
        results["transcript_analysis"] = transcript_result
    
    # 精彩片段提取
    print("\n" + "="*60)
    highlights_result = await extract_video_highlights(video_path)
    if highlights_result:
        results["highlights"] = highlights_result
    
    # 比较分析方法
    print("\n" + "="*60)
    await compare_analysis_methods(video_path)
    
    # 保存结果
    if results:
        await save_analysis_results(video_path, results)
    
    print("\n✅ ASR分析示例完成！")

if __name__ == "__main__":
    asyncio.run(main()) 