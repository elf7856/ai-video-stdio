#!/usr/bin/env python3
"""
简单视频内容分析示例
用户输入视频URL，获得AI生成的视频内容总结

使用方法:
python examples/simple_video_analysis.py
然后输入视频URL即可

支持平台: YouTube, B站, TikTok, Instagram等
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.video.downloader import VideoDownloader
# 使用新的分离架构
from app.services.analysis.video_analyzer import video_analyzer

async def analyze_video_content(video_url: str) -> dict:
    """
    分析视频内容并返回总结
    
    Args:
        video_url: 视频URL
        
    Returns:
        包含分析结果的字典
    """
    print(f"🎬 正在分析视频: {video_url}")
    print("-" * 50)
    
    downloader = VideoDownloader()
    
    try:
        # 步骤1: 获取视频基本信息
        print("📊 获取视频信息...")
        video_info = await downloader.get_video_info(video_url)
        
        if not video_info.get("success", False):
            return {
                "success": False,
                "error": f"无法获取视频信息: {video_info.get('error', '未知错误')}"
            }
        
        print(f"✅ 标题: {video_info.get('title', '未知')}")
        print(f"📺 平台: {video_info.get('platform', '未知')}")
        
        if 'duration' in video_info and video_info['duration']:
            duration_min = int(video_info['duration']) // 60
            duration_sec = int(video_info['duration']) % 60
            print(f"⏱️ 时长: {duration_min}分{duration_sec}秒")
        
        # 步骤2: 下载视频
        print("\n📥 下载视频...")
        download_result = await downloader.download_video(video_url)
        
        if not download_result.get("success", False):
            return {
                "success": False,
                "error": f"视频下载失败: {download_result.get('error', '未知错误')}"
            }
        
        video_path = download_result["file_path"]
        print(f"✅ 下载完成: {os.path.basename(video_path)}")
        
        # 步骤3: AI内容分析
        print("\n🤖 AI分析中...")
        
        video_metadata = {
            "title": download_result.get("title", "未知标题"),
            "platform": download_result.get("platform", "未知平台"),
            "duration": download_result.get("duration"),
            "url": video_url
        }
        
        # 使用新的VideoAnalyzer进行分析（注意：现在是同步方法）
        analysis_result = video_analyzer.analyze_video_content(
            video_info=video_metadata,
            timeout=30,
            retry_count=2
        )
        
        # 生成改进建议
        suggestions = None
        if analysis_result.get("success"):
            print("💡 生成改进建议...")
            suggestions = video_analyzer.suggest_improvements(
                analysis_result,
                timeout=20,
                retry_count=1
            )
        
        # 清理下载的文件
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"🧹 已清理临时文件")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")
        
        # 返回结果
        return {
            "success": True,
            "video_info": video_metadata,
            "content_analysis": analysis_result,
            "improvement_suggestions": suggestions,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"分析过程出错: {str(e)}"
        }

def display_results(results: dict):
    """显示分析结果"""
    print("\n" + "=" * 60)
    print("📋 视频内容分析结果")
    print("=" * 60)
    
    if not results.get("success"):
        print(f"❌ 分析失败: {results.get('error', '未知错误')}")
        return
    
    # 基本信息
    video_info = results["video_info"]
    print(f"\n📺 视频信息:")
    print(f"   🎬 标题: {video_info.get('title', '未知')}")
    print(f"   🌐 平台: {video_info.get('platform', '未知')}")
    print(f"   🔗 链接: {video_info.get('url', '未知')}")
    
    if video_info.get('duration'):
        duration_min = int(video_info['duration']) // 60
        duration_sec = int(video_info['duration']) % 60
        print(f"   ⏱️ 时长: {duration_min}分{duration_sec}秒")
    
    # 内容分析
    analysis = results.get("content_analysis", {})
    if analysis and analysis.get("success"):
        print(f"\n📝 AI内容总结:")
        summary = analysis.get("summary", "无法生成摘要")
        
        # 格式化显示摘要
        lines = summary.split('\n')
        for line in lines:
            if line.strip():
                print(f"   {line.strip()}")
        
        # 显示其他分析信息（如果有）
        for key, value in analysis.items():
            if key not in ["success", "summary", "video_info", "provider"] and value:
                if isinstance(value, list):
                    print(f"\n   {key}:")
                    for item in value:
                        print(f"     • {item}")
                elif isinstance(value, str) and len(value) < 100:
                    print(f"   {key}: {value}")
    else:
        print(f"\n❌ AI分析失败: {analysis.get('error', '未知错误')}")
    
    # 改进建议
    suggestions = results.get("improvement_suggestions")
    if suggestions and suggestions.get("success"):
        print(f"\n💡 AI改进建议:")
        suggestions_text = suggestions.get("suggestions", "无建议")
        lines = suggestions_text.split('\n')
        for line in lines:
            if line.strip():
                print(f"   {line.strip()}")
    
    print(f"\n⏰ 分析时间: {results.get('timestamp', '未知')}")
    print("=" * 60)

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查API密钥
    api_keys = {
        "Google Gemini": os.getenv('GOOGLE_API_KEY'),
        "OpenAI": os.getenv('OPENAI_API_KEY'),
        "Anthropic": os.getenv('ANTHROPIC_API_KEY')
    }
    
    available_services = []
    for service_name, api_key in api_keys.items():
        if api_key:
            available_services.append(service_name)
    
    if not available_services:
        print("❌ 未检测到任何LLM API密钥")
        print("请在环境变量中设置至少一个API密钥:")
        print("   - GOOGLE_API_KEY (推荐，免费额度较多)")
        print("   - OPENAI_API_KEY")
        print("   - ANTHROPIC_API_KEY")
        print("\n示例设置方法:")
        print("   export GOOGLE_API_KEY='your_api_key_here'")
        return False
    else:
        print(f"✅ 可用的AI服务: {', '.join(available_services)}")
        
        # 测试LLM服务健康状态
        print("🔧 测试LLM服务连接...")
        try:
            from app.services.llm.service import llm_service
            health_result = llm_service.health_check()
            
            if health_result.get("overall_healthy"):
                healthy_providers = [
                    name for name, status in health_result["providers"].items() 
                    if status["healthy"]
                ]
                print(f"✅ LLM服务正常: {', '.join(healthy_providers)}")
                return True
            else:
                print("⚠️ LLM服务连接异常，但将继续尝试")
                for name, status in health_result["providers"].items():
                    if not status["healthy"]:
                        print(f"   ❌ {name}: {status.get('error', '未知错误')}")
                return True  # 即使健康检查失败也继续，可能是网络临时问题
                
        except Exception as e:
            print(f"⚠️ LLM服务健康检查失败: {e}")
            return True  # 继续执行，让用户决定

def get_sample_urls():
    """获取示例URL"""
    return {
        "YouTube经典": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "B站热门": "https://www.bilibili.com/video/BV1xx411c7mu",
        "教育内容": "https://www.youtube.com/watch?v=9bZkp7q19f0",  # 示例教育视频
    }

async def interactive_mode():
    """交互模式"""
    print("\n🎯 交互式视频分析")
    print("-" * 30)
    
    while True:
        print("\n请选择:")
        print("1. 输入视频URL分析")
        print("2. 使用示例URL")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            video_url = input("\n请输入视频URL: ").strip()
            if video_url:
                results = await analyze_video_content(video_url)
                display_results(results)
            else:
                print("❌ URL不能为空")
                
        elif choice == "2":
            sample_urls = get_sample_urls()
            print("\n示例视频:")
            for i, (name, url) in enumerate(sample_urls.items(), 1):
                print(f"{i}. {name}: {url}")
            
            try:
                sample_choice = int(input(f"\n请选择示例 (1-{len(sample_urls)}): ").strip())
                if 1 <= sample_choice <= len(sample_urls):
                    selected_url = list(sample_urls.values())[sample_choice - 1]
                    results = await analyze_video_content(selected_url)
                    display_results(results)
                else:
                    print("❌ 选择超出范围")
            except ValueError:
                print("❌ 请输入有效数字")
                
        elif choice == "3":
            print("👋 感谢使用！")
            break
        else:
            print("❌ 无效选择，请重新输入")

async def main():
    """主函数"""
    print("🚀 视频内容AI分析工具")
    print("=" * 60)
    print("功能: 输入视频URL，获得AI生成的内容总结和改进建议")
    print("支持: YouTube, B站, TikTok, Instagram等主流平台")
    print("=" * 60)
    
    # 检查环境
    if not check_environment():
        print("\n⚠️ 请配置API密钥后重新运行")
        return
    
    try:
        # 检查命令行参数
        if len(sys.argv) > 1:
            # 直接分析命令行传入的URL
            video_url = sys.argv[1]
            print(f"\n📌 分析指定URL: {video_url}")
            results = await analyze_video_content(video_url)
            display_results(results)
        else:
            # 进入交互模式
            await interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序出错: {str(e)}")

if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main()) 