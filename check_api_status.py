#!/usr/bin/env python3
"""
API状态全面检查
为视频二创项目提供清晰的API接入建议
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.core.api_manager import api_manager

async def main():
    """主函数"""
    print("🚀 视频二创平台 API 接入状态检查")
    print("="*60)
    
    # 检查所有API状态
    print("⏳ 正在检查所有API状态...")
    await api_manager.check_all_apis()
    
    # 打印详细报告
    api_manager.print_status_report()
    
    # 获取摘要信息
    summary = api_manager.get_api_summary()
    
    print(f"\n📈 整体进度:")
    total_apis = sum(summary["by_status"].values())
    ready_count = summary["by_status"].get("ready", 0)
    progress = (ready_count / total_apis) * 100 if total_apis > 0 else 0
    
    print(f"  总API数量: {total_apis}")
    print(f"  已就绪API: {ready_count}")
    print(f"  完成度: {progress:.1f}%")
    
    # 立即可开始的工作
    ready_llm = api_manager.get_ready_apis("llm")
    ready_tts = api_manager.get_ready_apis("tts")
    
    print(f"\n🎉 立即可以开始的工作:")
    if ready_llm:
        print(f"  ✅ 视频内容分析 - 使用 {ready_llm[0].name}")
    if ready_tts:
        print(f"  ✅ 语音配音生成 - 使用 {ready_tts[0].name}")
        
    if ready_llm and ready_tts:
        print(f"  ✅ 开发基础Web界面")
        print(f"  ✅ 构建核心工作流")
    
    # 下一步建议
    next_apis = api_manager.get_next_priority_apis(3)
    if next_apis:
        print(f"\n⭐ 建议优先配置以下API:")
        for i, api in enumerate(next_apis, 1):
            print(f"  {i}. {api.name}")
            print(f"     作用: {api.description}")
            if api.config_required:
                print(f"     配置: export {api.config_required[0]}='your_api_key'")
            if api.dependencies and api.status.value == "not_installed":
                print(f"     安装: pip install {' '.join(api.dependencies)}")
    
    # 项目发展建议
    print(f"\n🗺️  项目发展路线图:")
    
    phase1_ready = len(ready_llm) > 0 and len(ready_tts) > 0
    if phase1_ready:
        print(f"  ✅ 第一阶段: 基础功能 (LLM + TTS)")
        print(f"     - 视频URL分析")
        print(f"     - 内容提取和总结") 
        print(f"     - 语音配音生成")
        print(f"     - 简单Web界面")
    else:
        print(f"  ⏳ 第一阶段: 基础功能 (需要配置LLM)")
    
    ready_image = api_manager.get_ready_apis("image")
    if ready_image:
        print(f"  ✅ 第二阶段: 视觉生成 (添加图像生成)")
        print(f"     - 根据剧情生成配图")
        print(f"     - 不同风格的视觉元素")
    else:
        print(f"  ⏳ 第二阶段: 视觉生成 (需要配置图像API)")
        
    print(f"  🔮 第三阶段: 完整视频合成")
    print(f"     - 自动视频剪辑")
    print(f"     - 背景音乐添加")
    print(f"     - 字幕和特效")
    
    # 给出具体的下一步操作建议
    print(f"\n💡 现在就可以做的事情:")
    
    if phase1_ready:
        print(f"  1. 🚀 开始构建核心功能:")
        print(f"     python -c \"")
        print(f"from app.services.llm.service import LLMService")
        print(f"from app.services.tts.generator import tts_generator")
        print(f"import asyncio")
        print(f"")
        print(f"async def demo():")
        print(f"    # 分析内容")
        print(f"    llm = LLMService()")
        print(f"    content = await llm.generate_content('为以下故事生成旁白：从前有一座山')")
        print(f"    print('生成内容:', content)")
        print(f"    ")
        print(f"    # 生成语音")
        print(f"    audio = await tts_generator.generate_speech(content, voice_id='xiaoxiao')")
        print(f"    print('语音文件:', audio)")
        print(f"")
        print(f"asyncio.run(demo())")
        print(f"\"")
        
        print(f"\n  2. 🌐 创建Web界面:")
        print(f"     cd app && python -m uvicorn main:app --reload")
        
    else:
        print(f"  1. 🔑 配置必要的API密钥:")
        if not ready_llm:
            print(f"     export GOOGLE_API_KEY='your_google_api_key'")
            print(f"     # 或者")
            print(f"     export OPENAI_API_KEY='your_openai_api_key'")
    
    print(f"\n{'='*60}")
    print(f"🎯 总结: 你的TTS服务已经完美运行，现在专注于接入LLM和图像API！")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main()) 