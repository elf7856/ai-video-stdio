#!/usr/bin/env python3
"""
LLM服务测试 - 测试新的分离架构
专门测试LLM调用的稳定性和各个组件的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_environment():
    """测试环境配置"""
    print("🔍 检查环境配置...")
    
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
        print("\n⚠️ 没有检测到任何API密钥！")
        return False
    
    print(f"\n✅ 可用服务: {', '.join(available_keys)}")
    return True

def test_llm_service():
    """测试基础LLM服务"""
    print("\n🔧 测试LLM服务...")
    
    try:
        from app.services.llm.service import llm_service
        
        # 1. 测试服务初始化
        print(f"   服务初始化: {'✅' if llm_service.available_providers else '❌'}")
        if llm_service.available_providers:
            providers = [p['name'] for p in llm_service.available_providers]
            print(f"   可用提供商: {', '.join(providers)}")
        
        # 2. 测试健康检查
        print("   执行健康检查...")
        health_result = llm_service.health_check()
        
        overall_healthy = health_result.get("overall_healthy", False)
        print(f"   整体健康状态: {'✅' if overall_healthy else '❌'}")
        
        for provider_name, status in health_result.get("providers", {}).items():
            is_healthy = status.get("healthy", False)
            status_icon = "✅" if is_healthy else "❌"
            print(f"   {provider_name}: {status_icon}")
            if not is_healthy and status.get("error"):
                print(f"      错误: {status['error']}")
        
        # 3. 测试简单调用
        if overall_healthy:
            print("   测试简单调用...")
            test_result = llm_service.simple_call("请回复'测试成功'", timeout=10, retry_count=1)
            
            if test_result.get("success"):
                print(f"   ✅ 调用成功: {test_result['content'][:50]}...")
                print(f"   使用提供商: {test_result.get('provider')}")
                print(f"   耗时: {test_result.get('elapsed_time', 0):.2f}秒")
                return True
            else:
                print(f"   ❌ 调用失败: {test_result.get('error')}")
                return False
        else:
            print("   ⚠️ 服务不健康，跳过调用测试")
            return False
            
    except Exception as e:
        print(f"   ❌ LLM服务测试异常: {e}")
        return False

def test_content_analyzer():
    """测试内容分析器"""
    print("\n📝 测试内容分析器...")
    
    try:
        from app.services.analysis.content_analyzer import content_analyzer
        
        # 测试内容分析
        test_content = "这是一段测试内容，用于验证内容分析功能是否正常工作。"
        
        print("   执行内容分析...")
        result = content_analyzer.analyze_general_content(
            content=test_content,
            analysis_type="general",
            timeout=15,
            retry_count=1
        )
        
        if result.get("success"):
            print(f"   ✅ 分析成功")
            print(f"   分析结果: {result['summary'][:100]}...")
            print(f"   使用提供商: {result.get('provider')}")
            return True
        else:
            print(f"   ❌ 分析失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ 内容分析器测试异常: {e}")
        return False

def test_video_analyzer():
    """测试视频分析器"""
    print("\n🎬 测试视频分析器...")
    
    try:
        from app.services.analysis.video_analyzer import video_analyzer
        
        # 模拟视频信息
        test_video_info = {
            "title": "测试视频标题",
            "platform": "youtube",
            "duration": 180,
            "url": "https://example.com/test"
        }
        
        print("   执行视频内容分析...")
        result = video_analyzer.analyze_video_content(
            video_info=test_video_info,
            timeout=15,
            retry_count=1
        )
        
        if result.get("success"):
            print(f"   ✅ 视频分析成功")
            print(f"   分析结果: {result['summary'][:100]}...")
            print(f"   使用提供商: {result.get('provider')}")
            
            # 测试改进建议
            print("   测试改进建议...")
            suggestions = video_analyzer.suggest_improvements(
                result,
                timeout=12,
                retry_count=1
            )
            
            if suggestions.get("success"):
                print(f"   ✅ 改进建议生成成功")
                print(f"   建议: {suggestions['suggestions'][:100]}...")
                return True
            else:
                print(f"   ❌ 改进建议失败: {suggestions.get('error')}")
                return False
        else:
            print(f"   ❌ 视频分析失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ 视频分析器测试异常: {e}")
        return False

def test_compatibility():
    """测试向后兼容性"""
    print("\n🔄 测试向后兼容性...")
    
    try:
        # 测试原有接口是否正常工作
        from app.services.llm.analyzer import VideoAnalyzer, LLMService
        
        # 测试LLMService兼容接口
        llm_compat = LLMService()
        print(f"   LLMService兼容接口: {'✅' if llm_compat.available_providers else '❌'}")
        
        # 测试VideoAnalyzer兼容接口
        video_compat = VideoAnalyzer()
        print(f"   VideoAnalyzer兼容接口: ✅")
        
        # 测试兼容方法
        test_video_info = {
            "title": "兼容性测试视频",
            "platform": "test",
            "duration": 120
        }
        
        compat_result = video_compat.analyze_video_content(
            video_info=test_video_info,
            timeout=10,
            retry_count=1
        )
        
        if compat_result.get("success"):
            print(f"   ✅ 兼容性测试成功")
            return True
        else:
            print(f"   ❌ 兼容性测试失败: {compat_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ 兼容性测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 LLM服务架构测试")
    print("=" * 60)
    print("测试新的分离架构：LLM服务、内容分析器、视频分析器")
    print("=" * 60)
    
    # 执行所有测试
    tests = [
        ("环境配置", test_environment),
        ("LLM服务", test_llm_service),
        ("内容分析器", test_content_analyzer),
        ("视频分析器", test_video_analyzer),
        ("向后兼容性", test_compatibility)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}\n")
    
    # 测试总结
    print("=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新架构工作正常")
        return True
    elif passed >= total // 2:
        print("⚠️ 部分测试通过，系统基本可用")
        return True
    else:
        print("❌ 大部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试程序异常: {e}")
        sys.exit(1) 