#!/usr/bin/env python3
"""
简化测试运行脚本
整合系统健康检查和稳定LLM测试
"""

import os
import sys
import time
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_environment():
    """环境检查"""
    print("🔍 环境预检查")
    print("-" * 40)
    
    # Python版本检查
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}")
    
    # 工作目录检查
    if not os.path.exists("app") or not os.path.exists("tests"):
        print("❌ 缺少必要目录")
        return False
    
    print("✅ 目录结构正确")
    return True

def run_system_health_check():
    """运行系统健康检查"""
    print("\n🏥 系统健康检查")
    print("=" * 60)
    
    try:
        from tests.test_system_health import run_health_check
        return run_health_check()
    except Exception as e:
        print(f"❌ 系统健康检查失败: {e}")
        return False

def run_stable_llm_test():
    """运行稳定LLM测试"""
    print("\n🤖 稳定LLM测试")
    print("=" * 60)
    
    try:
        from tests.test_stable_llm import main as stable_test_main
        stable_test_main()
        return True
    except Exception as e:
        print(f"❌ 稳定LLM测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 视频创作平台 - 测试套件")
    print("=" * 80)
    
    start_time = time.time()
    
    # 环境预检查
    if not check_environment():
        print("❌ 环境检查失败，退出测试")
        sys.exit(1)
    
    # 运行测试
    results = []
    
    # 1. 系统健康检查
    health_ok = run_system_health_check()
    results.append(("系统健康检查", health_ok))
    
    # 2. 稳定LLM测试
    if health_ok:  # 只有健康检查通过才运行LLM测试
        llm_ok = run_stable_llm_test()
        results.append(("稳定LLM测试", llm_ok))
    else:
        print("\n⚠️ 跳过LLM测试（系统健康检查未通过）")
        results.append(("稳定LLM测试", False))
    
    # 生成总结报告
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📊 测试套件总结报告")
    print("=" * 80)
    
    passed_tests = sum(1 for _, ok in results if ok)
    
    for test_name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"{test_name}: {status}")
    
    overall_success = passed_tests == len(results)
    
    print(f"\n🎯 总体结果: {'✅ 全部通过' if overall_success else f'⚠️ {passed_tests}/{len(results)} 通过'}")
    print(f"⏱️ 总耗时: {elapsed:.2f}秒")
    
    if not overall_success:
        print("\n💡 建议:")
        print("   1. 检查API密钥配置: 复制 .env.example 为 .env")
        print("   2. 安装依赖: pip install -r requirements.txt")
        print("   3. 运行单项测试: python tests/test_system_health.py")
        print("   4. 运行LLM测试: python run_stable_test.py")
    else:
        print("\n🎉 所有测试通过！系统准备就绪。")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        sys.exit(1) 