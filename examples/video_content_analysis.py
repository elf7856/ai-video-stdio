#!/usr/bin/env python3
"""
视频内容分析示例
通过视频URL下载视频并生成详细的内容总结
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

from app.services.video.manager import VideoProcessingManager
from app.services.video.downloader import VideoDownloader
from app.services.llm.analyzer import VideoAnalyzer
from app.core.config import settings

class VideoContentAnalyzer:
    """视频内容分析器示例类"""
    
    def __init__(self):
        self.video_manager = VideoProcessingManager()
        self.downloader = VideoDownloader()
        self.analyzer = VideoAnalyzer()
    
    async def analyze_video_from_url(self, video_url: str, detailed: bool = True) -> dict:
        """
        从视频URL分析视频内容
        
        Args:
            video_url: 视频URL
            detailed: 是否进行详细分析
            
        Returns:
            包含视频信息和分析结果的字典
        """
        print(f"🎬 开始分析视频: {video_url}")
        print("=" * 60)
        
        try:
            # 步骤1: 获取视频信息（无需下载）
            print("📊 获取视频基本信息...")
            video_info = await self.downloader.get_video_info(video_url)
            
            if not video_info.get("success", False):
                print(f"❌ 获取视频信息失败: {video_info.get('error', '未知错误')}")
                return {"success": False, "error": video_info.get('error')}
            
            # 打印基本信息
            print(f"✅ 视频标题: {video_info.get('title', '未知')}")
            print(f"📺 平台: {video_info.get('platform', '未知')}")
            if 'duration' in video_info:
                duration_min = video_info['duration'] // 60
                duration_sec = video_info['duration'] % 60
                print(f"⏱️ 时长: {duration_min}分{duration_sec}秒")
            
            # 步骤2: 下载视频文件
            print("\n📥 下载视频文件...")
            download_result = await self.downloader.download_video(video_url)
            
            if not download_result.get("success", False):
                print(f"❌ 视频下载失败: {download_result.get('error', '未知错误')}")
                return {"success": False, "error": download_result.get('error')}
            
            video_path = download_result["file_path"]
            print(f"✅ 视频下载成功: {video_path}")
            
            # 步骤3: 基础内容分析
            print("\n🔍 分析视频内容...")
            
            # 构建视频信息字典
            video_metadata = {
                "title": download_result.get("title", "未知标题"),
                "platform": download_result.get("platform", "未知平台"),
                "duration": download_result.get("duration"),
                "file_path": video_path,
                "url": video_url
            }
            
            # 使用LLM分析器进行内容分析
            analysis_result = await self.analyzer.analyze_video_content(
                video_info=video_metadata,
                timeout=30,  # 30秒超时
                retry_count=2
            )
            
            # 步骤4: 生成改进建议（如果需要详细分析）
            suggestions = None
            if detailed and analysis_result.get("success"):
                print("\n💡 生成改进建议...")
                suggestions = await self.analyzer.suggest_improvements(
                    analysis_result,
                    timeout=20,
                    retry_count=2
                )
            
            # 步骤5: 提取关键时刻（如果有转录内容）
            key_moments = None
            if detailed:
                print("\n⭐ 提取关键时刻...")
                # 这里可以添加语音转文字的功能，然后提取关键时刻
                # 目前使用视频标题和描述作为示例
                transcript_placeholder = f"视频标题: {video_metadata['title']}"
                key_moments = await self.analyzer.extract_key_moments(
                    transcript=transcript_placeholder,
                    max_moments=5,
                    timeout=15
                )
            
            # 整理并返回结果
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "video_info": {
                    "title": video_metadata["title"],
                    "platform": video_metadata["platform"],
                    "duration": video_metadata["duration"],
                    "url": video_url,
                    "local_path": video_path
                },
                "content_analysis": analysis_result,
                "improvement_suggestions": suggestions,
                "key_moments": key_moments
            }
            
            # 清理下载的文件（可选）
            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print(f"\n🧹 已清理临时文件: {video_path}")
                except Exception as e:
                    print(f"\n⚠️ 清理文件失败: {e}")
            
            return result
            
        except Exception as e:
            print(f"❌ 分析过程出错: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def display_analysis_results(self, results: dict):
        """显示分析结果"""
        if not results.get("success"):
            print(f"❌ 分析失败: {results.get('error', '未知错误')}")
            return
        
        print("\n" + "=" * 60)
        print("📋 视频内容分析报告")
        print("=" * 60)
        
        # 基本信息
        video_info = results["video_info"]
        print(f"\n📺 基本信息:")
        print(f"   标题: {video_info['title']}")
        print(f"   平台: {video_info['platform']}")
        print(f"   链接: {video_info['url']}")
        if video_info.get('duration'):
            duration_min = video_info['duration'] // 60
            duration_sec = video_info['duration'] % 60
            print(f"   时长: {duration_min}分{duration_sec}秒")
        
        # 内容分析
        analysis = results.get("content_analysis", {})
        if analysis.get("success"):
            print(f"\n📝 内容摘要:")
            summary = analysis.get("summary", "无摘要")
            print(f"   {summary}")
            
            # 显示详细分析（如果是JSON格式）
            if isinstance(analysis, dict):
                for key, value in analysis.items():
                    if key not in ["success", "summary", "video_info"] and value:
                        print(f"   {key}: {value}")
        else:
            print(f"\n❌ 内容分析失败: {analysis.get('error', '未知错误')}")
        
        # 改进建议
        suggestions = results.get("improvement_suggestions")
        if suggestions and suggestions.get("success"):
            print(f"\n💡 改进建议:")
            suggestions_text = suggestions.get("suggestions", "无建议")
            print(f"   {suggestions_text}")
        
        # 关键时刻
        key_moments = results.get("key_moments")
        if key_moments and key_moments.get("success"):
            print(f"\n⭐ 关键时刻:")
            moments_text = key_moments.get("key_moments", "无关键时刻")
            print(f"   {moments_text}")
        
        print("\n" + "=" * 60)

async def example_youtube_analysis():
    """YouTube视频分析示例"""
    print("🎯 示例1: YouTube视频分析")
    print("-" * 40)
    
    analyzer = VideoContentAnalyzer()
    
    # 示例YouTube URL（请替换为实际URL）
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    results = await analyzer.analyze_video_from_url(youtube_url, detailed=True)
    analyzer.display_analysis_results(results)
    
    return results

async def example_bilibili_analysis():
    """B站视频分析示例"""
    print("\n🎯 示例2: B站视频分析")
    print("-" * 40)
    
    analyzer = VideoContentAnalyzer()
    
    # 示例B站URL（请替换为实际URL）
    bilibili_url = "https://www.bilibili.com/video/BV1xx411c7mu"
    
    results = await analyzer.analyze_video_from_url(bilibili_url, detailed=False)
    analyzer.display_analysis_results(results)
    
    return results

async def example_batch_analysis():
    """批量视频分析示例"""
    print("\n🎯 示例3: 批量视频分析")
    print("-" * 40)
    
    analyzer = VideoContentAnalyzer()
    
    # 示例视频URL列表
    video_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.bilibili.com/video/BV1xx411c7mu",
        # 可以添加更多URL
    ]
    
    results = []
    for i, url in enumerate(video_urls, 1):
        print(f"\n处理视频 {i}/{len(video_urls)}: {url}")
        result = await analyzer.analyze_video_from_url(url, detailed=False)
        results.append(result)
        
        # 显示简要结果
        if result.get("success"):
            title = result["video_info"]["title"]
            summary = result.get("content_analysis", {}).get("summary", "无摘要")[:100]
            print(f"✅ {title}: {summary}...")
        else:
            print(f"❌ 分析失败: {result.get('error')}")
    
    return results

async def save_results_to_file(results: list, filename: str = "video_analysis_results.json"):
    """保存分析结果到文件"""
    try:
        # 确保输出目录存在
        output_dir = os.path.join(project_root, "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析结果已保存到: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ 保存结果失败: {str(e)}")
        return None

def check_api_keys():
    """检查API密钥配置"""
    print("🔑 检查API密钥配置...")
    
    api_keys = {
        "GOOGLE_API_KEY": os.getenv('GOOGLE_API_KEY'),
        "OPENAI_API_KEY": os.getenv('OPENAI_API_KEY'),
        "ANTHROPIC_API_KEY": os.getenv('ANTHROPIC_API_KEY')
    }
    
    available_keys = []
    for key_name, key_value in api_keys.items():
        if key_value:
            available_keys.append(key_name.replace('_API_KEY', ''))
            print(f"✅ {key_name}: 已配置")
        else:
            print(f"❌ {key_name}: 未配置")
    
    if not available_keys:
        print("\n⚠️  警告: 未检测到任何LLM API密钥!")
        print("请在环境变量中设置至少一个API密钥:")
        print("- GOOGLE_API_KEY (推荐)")
        print("- OPENAI_API_KEY")
        print("- ANTHROPIC_API_KEY")
        return False
    else:
        print(f"\n✅ 检测到可用的LLM服务: {', '.join(available_keys)}")
        return True

async def main():
    """主函数"""
    print("🚀 视频内容分析工具")
    print("=" * 60)
    print("功能: 从视频URL下载视频并生成AI内容总结")
    print("支持平台: YouTube, B站, TikTok, Instagram等")
    print("=" * 60)
    
    # 检查API密钥
    if not check_api_keys():
        print("\n请配置API密钥后重新运行")
        return
    
    try:
        # 运行示例
        print("\n开始运行示例...")
        
        # 示例1: 单个YouTube视频分析
        result1 = await example_youtube_analysis()
        
        # 示例2: 单个B站视频分析（简化版）
        result2 = await example_bilibili_analysis()
        
        # 收集所有结果
        all_results = [result1, result2]
        
        # 保存结果到文件
        await save_results_to_file(all_results)
        
        print("\n✅ 所有示例运行完成!")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")

if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main()) 