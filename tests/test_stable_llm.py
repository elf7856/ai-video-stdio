#!/usr/bin/env python3
"""
稳定LLM测试 - 使用简化的稳定服务进行测试
专注于基础功能验证和稳定性
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.llm.stable_service import stable_llm_service

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查API密钥
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY')
    }
    
    available = []
    for name, key in api_keys.items():
        if key and key.strip():
            available.append(name.replace('_API_KEY', ''))
            print(f"✅ {name}: 已配置")
        else:
            print(f"❌ {name}: 未配置")
    
    if not available:
        print("⚠️ 没有检测到任何API密钥！")
        return False
    
    print(f"✅ 可用服务: {', '.join(available)}")
    
    # 检查稳定服务
    provider_count = len(stable_llm_service.providers)
    print(f"✅ 稳定LLM服务: {provider_count} 个提供商可用")
    
    return True

def test_basic_calls():
    """测试基础调用"""
    print("\n🔸 基础功能测试")
    print("-" * 40)
    
    test_prompts = [
        "请回复：OK",
        "1+1等于多少？",
        "用一句话介绍人工智能",
        "什么是机器学习？",
        "请说出三种编程语言"
    ]
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n测试 {i}/{len(test_prompts)}: {prompt}")
        
        start_time = time.time()
        result = stable_llm_service.simple_call(prompt, timeout=15, retry_count=2)
        elapsed = time.time() - start_time
        
        if result['success']:
            print(f"✅ 成功 ({elapsed:.2f}s, {result['provider']})")
            print(f"   响应: {result['content'][:80]}{'...' if len(result['content']) > 80 else ''}")
        else:
            print(f"❌ 失败 ({elapsed:.2f}s)")
            print(f"   错误: {result['error']}")
        
        results.append({
            'prompt': prompt,
            'success': result['success'],
            'elapsed': elapsed,
            'provider': result.get('provider', 'none'),
            'content_length': len(result.get('content', '')),
            'error': result.get('error', '')
        })
        
        # 添加间隔避免频率限制
        if i < len(test_prompts):
            time.sleep(1)
    
    return results

def test_complex_prompts():
    """测试复杂提示"""
    print("\n🔸 复杂提示测试")
    print("-" * 40)
    
    complex_prompts = [
        "请分析这句话的情感：'今天心情很好，工作进展顺利。'",
        "请总结人工智能在医疗领域的三个应用",
        "比较Python和JavaScript的优缺点",
        "请为一个5分钟的AI科普视频写个简短大纲"
    ]
    
    results = []
    
    for i, prompt in enumerate(complex_prompts, 1):
        print(f"\n测试 {i}/{len(complex_prompts)}: {prompt[:40]}...")
        
        start_time = time.time()
        result = stable_llm_service.simple_call(prompt, timeout=20, retry_count=2)
        elapsed = time.time() - start_time
        
        if result['success']:
            print(f"✅ 成功 ({elapsed:.2f}s, {result['provider']})")
            print(f"   响应长度: {len(result['content'])} 字符")
            print(f"   预览: {result['content'][:100]}{'...' if len(result['content']) > 100 else ''}")
        else:
            print(f"❌ 失败 ({elapsed:.2f}s)")
            print(f"   错误: {result['error']}")
        
        results.append({
            'prompt': prompt,
            'success': result['success'],
            'elapsed': elapsed,
            'provider': result.get('provider', 'none'),
            'content_length': len(result.get('content', '')),
            'error': result.get('error', '')
        })
        
        # 添加间隔
        if i < len(complex_prompts):
            time.sleep(2)
    
    return results

def test_edge_cases():
    """测试边界情况"""
    print("\n🔸 边界情况测试")
    print("-" * 40)
    
    edge_prompts = [
        "",  # 空提示
        "   ",  # 空格
        "a",  # 单字符
        "测试中文",  # 中文
        "Test English",  # 英文
        "🎉🚀💻",  # emoji
        "这是一个很长的提示 " * 10,  # 长提示
    ]
    
    results = []
    
    for i, prompt in enumerate(edge_prompts, 1):
        display_prompt = repr(prompt) if len(prompt) <= 20 else repr(prompt[:20] + "...")
        print(f"\n测试 {i}/{len(edge_prompts)}: {display_prompt}")
        
        start_time = time.time()
        result = stable_llm_service.simple_call(prompt, timeout=10, retry_count=1)
        elapsed = time.time() - start_time
        
        if result['success']:
            print(f"✅ 成功 ({elapsed:.2f}s, {result['provider']})")
            if result['content']:
                print(f"   响应: {result['content'][:60]}{'...' if len(result['content']) > 60 else ''}")
            else:
                print("   响应: [空内容]")
        else:
            print(f"❌ 失败 ({elapsed:.2f}s)")
            print(f"   错误: {result['error']}")
        
        results.append({
            'prompt': prompt,
            'success': result['success'],
            'elapsed': elapsed,
            'provider': result.get('provider', 'none'),
            'content_length': len(result.get('content', '')),
            'error': result.get('error', '')
        })
        
        # 短间隔
        time.sleep(0.5)
    
    return results

def test_health_check():
    """测试健康检查"""
    print("\n🔸 健康检查测试")
    print("-" * 40)
    
    start_time = time.time()
    health_result = stable_llm_service.health_check()
    elapsed = time.time() - start_time
    
    print(f"健康检查耗时: {elapsed:.2f}s")
    print(f"整体健康状态: {'✅' if health_result['overall_healthy'] else '❌'}")
    
    if health_result['providers']:
        print("提供商状态:")
        for provider, status in health_result['providers'].items():
            icon = "✅" if status['healthy'] else "❌"
            print(f"   {provider}: {icon}")
            if not status['healthy'] and status.get('error'):
                print(f"      错误: {status['error']}")
    
    if not health_result['overall_healthy'] and health_result.get('error'):
        print(f"总体错误: {health_result['error']}")
    
    return health_result

def generate_report(basic_results, complex_results, edge_results, health_result):
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("📊 稳定LLM服务测试报告")
    print("=" * 60)
    
    # 合并所有结果
    all_results = basic_results + complex_results + edge_results
    
    # 总体统计
    total_tests = len(all_results)
    successful_tests = sum(1 for r in all_results if r['success'])
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    total_time = sum(r['elapsed'] for r in all_results)
    avg_time = total_time / total_tests if total_tests > 0 else 0
    
    print(f"\n📈 总体统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功数: {successful_tests}")
    print(f"   成功率: {success_rate:.1%}")
    print(f"   总耗时: {total_time:.2f}s")
    print(f"   平均耗时: {avg_time:.2f}s")
    
    # 分类统计
    categories = [
        ('基础功能', basic_results),
        ('复杂提示', complex_results),
        ('边界情况', edge_results)
    ]
    
    print(f"\n📋 分类统计:")
    for cat_name, results in categories:
        if results:
            cat_success = sum(1 for r in results if r['success'])
            cat_total = len(results)
            cat_rate = cat_success / cat_total if cat_total > 0 else 0
            cat_avg_time = sum(r['elapsed'] for r in results) / cat_total
            print(f"   {cat_name:10}: {cat_success}/{cat_total} ({cat_rate:.1%}) - 平均 {cat_avg_time:.2f}s")
    
    # 提供商统计
    provider_stats = {}
    for result in all_results:
        if result['success']:
            provider = result['provider']
            if provider not in provider_stats:
                provider_stats[provider] = 0
            provider_stats[provider] += 1
    
    if provider_stats:
        print(f"\n🏢 提供商使用:")
        for provider, count in provider_stats.items():
            print(f"   {provider}: {count} 次")
    
    # 健康状态
    print(f"\n🔧 健康状态:")
    print(f"   整体健康: {'✅' if health_result['overall_healthy'] else '❌'}")
    
    # 失败案例
    failed_results = [r for r in all_results if not r['success']]
    if failed_results:
        print(f"\n❌ 失败案例 ({len(failed_results)} 个):")
        for result in failed_results[:3]:  # 只显示前3个
            prompt_preview = result['prompt'][:30] + "..." if len(result['prompt']) > 30 else result['prompt']
            print(f"   - {repr(prompt_preview)}: {result['error']}")
    
    # 性能分析
    successful_results = [r for r in all_results if r['success']]
    if successful_results:
        fast_results = [r for r in successful_results if r['elapsed'] <= 5]
        slow_results = [r for r in successful_results if r['elapsed'] > 10]
        
        print(f"\n⚡ 性能分析:")
        print(f"   快速响应 (≤5s): {len(fast_results)} 个")
        print(f"   慢速响应 (>10s): {len(slow_results)} 个")
        
        if slow_results:
            print("   慢速案例:")
            for result in slow_results[:2]:
                prompt_preview = result['prompt'][:30] + "..." if len(result['prompt']) > 30 else result['prompt']
                print(f"      {result['elapsed']:.2f}s: {repr(prompt_preview)}")
    
    # 总结
    print(f"\n🎯 测试结论:")
    if success_rate >= 0.9:
        print("   🎉 优秀！稳定LLM服务非常可靠")
        stability_grade = "A"
    elif success_rate >= 0.8:
        print("   ✅ 良好！稳定LLM服务基本可靠")
        stability_grade = "B"
    elif success_rate >= 0.6:
        print("   ⚠️ 一般，稳定性有待提高")
        stability_grade = "C"
    else:
        print("   ❌ 较差，需要重大改进")
        stability_grade = "D"
    
    print(f"   稳定性等级: {stability_grade}")
    
    return success_rate >= 0.7

def main():
    """主函数"""
    setup_logging()
    
    print("🚀 稳定LLM服务测试")
    print("=" * 60)
    
    # 检查环境
    if not check_environment():
        print("⚠️ 环境检查失败，请配置API密钥")
        return False
    
    try:
        # 健康检查
        health_result = test_health_check()
        
        # 如果健康检查失败，仍然继续测试
        if not health_result['overall_healthy']:
            print("⚠️ 健康检查失败，但继续进行功能测试...")
        
        # 运行测试
        basic_results = test_basic_calls()
        complex_results = test_complex_prompts()
        edge_results = test_edge_cases()
        
        # 生成报告
        success = generate_report(basic_results, complex_results, edge_results, health_result)
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 测试过程出现异常: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1) 