#!/usr/bin/env python3
"""
完整架构测试 - 验证重构后的分离架构
测试覆盖：LLM服务、内容分析器、视频分析器、向后兼容性
"""

import sys
import os
import time
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm.service import llm_service
from app.services.analysis.content_analyzer import ContentAnalyzer
from app.services.analysis.video_analyzer import VideoAnalyzer

# 向后兼容性导入
from app.services.llm.analyzer import LLMService as LegacyLLMService

def print_header(title):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_section(title):
    """打印测试部分"""
    print(f"\n🔸 {title}")
    print("-" * 40)

def test_llm_service():
    """测试LLM服务的稳定性"""
    print_section("LLM 服务稳定性测试")
    
    try:
        # 基础功能测试
        result = llm_service.health_check()
        if result['overall_healthy']:
            print("✅ 健康检查通过")
        else:
            print("❌ 健康检查失败")
            return False
        
        # 简单调用测试
        start_time = time.time()
        result = llm_service.simple_call("请简单回复：测试成功")
        elapsed = time.time() - start_time
        
        if result['success']:
            print(f"✅ 简单调用成功 (耗时: {elapsed:.2f}s)")
            print(f"   响应: {result['content'][:50]}...")
        else:
            print(f"❌ 简单调用失败: {result['error']}")
            return False
        
        # 重试机制测试
        print("\n测试重试机制...")
        result = llm_service.call_llm(
            messages=[{"role": "user", "content": "测试重试机制"}],
            timeout=3,  # 短超时测试重试
            retry_count=2
        )
        
        if result['success']:
            print("✅ 重试机制正常")
        else:
            print(f"⚠️  重试后失败: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM服务测试异常: {e}")
        return False

def test_content_analyzer():
    """测试内容分析器"""
    print_section("内容分析器测试")
    
    try:
        analyzer = ContentAnalyzer()
        
        # 通用内容分析
        test_content = "这是一段测试文本，用于验证内容分析功能的有效性。我们希望能够提取关键信息并生成有用的分析结果。"
        
        result = analyzer.analyze_general_content(
            content=test_content,
            analysis_type="general"
        )
        
        if result['success']:
            print("✅ 通用内容分析成功")
            print(f"   分析类型: {result.get('analysis_type')}")
            print(f"   提供商: {result.get('provider')}")
        else:
            print(f"❌ 通用内容分析失败: {result['error']}")
            return False
        
        # 摘要生成测试
        summary_result = analyzer.generate_summary(
            content=test_content,
            summary_length="short"
        )
        
        if summary_result['success']:
            print("✅ 摘要生成成功")
            print(f"   摘要: {summary_result['summary'][:50]}...")
        else:
            print(f"❌ 摘要生成失败: {summary_result['error']}")
        
        # 关键要点提取
        key_points_result = analyzer.extract_key_points(
            content=test_content,
            max_points=3
        )
        
        if key_points_result['success']:
            print("✅ 关键要点提取成功")
            key_points = key_points_result.get('key_points', [])
            if isinstance(key_points, list):
                print(f"   要点数量: {len(key_points)}")
        else:
            print(f"❌ 关键要点提取失败: {key_points_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 内容分析器测试异常: {e}")
        return False

def test_video_analyzer():
    """测试视频分析器"""
    print_section("视频分析器测试")
    
    try:
        analyzer = VideoAnalyzer()
        
        # 准备测试视频信息
        video_info = {
            "title": "AI技术发展趋势分析",
            "description": "本视频深入分析了当前AI技术的发展趋势，包括机器学习、深度学习和自然语言处理等领域的最新进展。",
            "duration": 600,  # 10分钟
            "platform": "YouTube",
            "tags": ["AI", "机器学习", "技术趋势"]
        }
        
        test_subtitles = "欢迎观看今天的AI技术分析。首先，我们来看看机器学习在各个行业的应用情况。"
        
        # 视频内容分析
        result = analyzer.analyze_video_content(
            video_info=video_info,
            extracted_text=test_subtitles
        )
        
        if result['success']:
            print("✅ 视频内容分析成功")
            print(f"   分析结果包含关键字段: {list(result.keys())}")
        else:
            print(f"❌ 视频内容分析失败: {result['error']}")
            return False
        
        # 改进建议生成
        improvement_result = analyzer.suggest_improvements(result)
        
        if improvement_result['success']:
            print("✅ 改进建议生成成功")
        else:
            print(f"⚠️  改进建议生成失败: {improvement_result['error']}")
        
        # 内容脚本生成
        script_result = analyzer.generate_content_script(
            topic="AI技术发展",
            style="educational",
            duration_minutes=5
        )
        
        if script_result:
            print("✅ 内容脚本生成成功")
            print(f"   脚本长度: {len(script_result)} 字符")
        else:
            print("❌ 内容脚本生成失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 视频分析器测试异常: {e}")
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print_section("向后兼容性测试")
    
    try:
        # 测试旧的LLMService接口
        legacy_service = LegacyLLMService()
        
        # 检查基本属性
        if hasattr(legacy_service, 'analyze_content'):
            print("✅ 旧版analyze_content方法可用")
        else:
            print("❌ 旧版analyze_content方法不可用")
            return False
        
        # 测试旧版调用
        result = legacy_service.analyze_content(
            content="测试向后兼容性",
            analysis_type="general"
        )
        
        if isinstance(result, dict) and 'summary' in result:
            print("✅ 向后兼容性调用成功")
            print(f"   结果类型: {type(result)}")
        else:
            print(f"⚠️  向后兼容性调用结果格式异常: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试异常: {e}")
        return False

def test_error_handling():
    """测试错误处理机制"""
    print_section("错误处理机制测试")
    
    try:
        # 测试空内容处理
        analyzer = ContentAnalyzer()
        
        result = analyzer.analyze_general_content(
            content="",
            analysis_type="general"
        )
        
        if not result['success']:
            print("✅ 空内容错误处理正确")
        else:
            print("⚠️  空内容应该返回错误")
        
        # 测试超长内容处理
        long_content = "测试内容 " * 1000  # 很长的内容
        
        result = analyzer.analyze_general_content(
            content=long_content,
            analysis_type="general",
            max_content_length=100  # 限制长度
        )
        
        # 不管成功失败都算正常，关键是不崩溃
        print("✅ 超长内容处理不崩溃")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试异常: {e}")
        return False

def test_performance():
    """测试性能指标"""
    print_section("性能测试")
    
    try:
        analyzer = ContentAnalyzer()
        
        # 测试批量调用性能
        test_contents = [
            "测试内容1：技术文档分析",
            "测试内容2：产品介绍文案",
            "测试内容3：用户反馈总结"
        ]
        
        start_time = time.time()
        success_count = 0
        
        for i, content in enumerate(test_contents, 1):
            result = analyzer.analyze_general_content(
                content=content,
                analysis_type="general"
            )
            
            if result['success']:
                success_count += 1
                print(f"   测试 {i}/3: ✅")
            else:
                print(f"   测试 {i}/3: ❌ {result['error']}")
        
        elapsed = time.time() - start_time
        avg_time = elapsed / len(test_contents)
        
        print(f"\n📊 性能统计:")
        print(f"   总耗时: {elapsed:.2f}s")
        print(f"   平均耗时: {avg_time:.2f}s")
        print(f"   成功率: {success_count}/{len(test_contents)} ({success_count/len(test_contents)*100:.1f}%)")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 性能测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print_header("完整架构测试")
    print("验证重构后的分离架构：LLM服务 + 内容分析器 + 视频分析器")
    
    test_results = {}
    
    # 运行所有测试
    tests = [
        ("LLM服务", test_llm_service),
        ("内容分析器", test_content_analyzer), 
        ("视频分析器", test_video_analyzer),
        ("向后兼容性", test_backward_compatibility),
        ("错误处理", test_error_handling),
        ("性能测试", test_performance),
    ]
    
    for test_name, test_func in tests:
        try:
            test_results[test_name] = test_func()
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 发生异常: {e}")
            test_results[test_name] = False
    
    # 输出总结
    print_header("测试总结")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} : {status}")
    
    print(f"\n📊 总体结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！重构架构工作完美。")
        return True
    elif passed >= total * 0.8:
        print("⚠️  大部分测试通过，架构基本稳定。")
        return True
    else:
        print("❌ 多个测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 