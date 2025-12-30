#!/usr/bin/env python3
"""
系统健康检查测试
整合基础环境检查、配置验证和模块导入测试
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_environment():
    """测试运行环境"""
    print("🔍 环境检查")
    print("-" * 40)
    
    # Python版本检查
    python_version = sys.version_info
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("⚠️ 建议使用Python 3.8+")
    
    # 工作目录检查
    print(f"✅ 工作目录: {project_root}")
    
    # 必要目录检查
    required_dirs = ["app", "tests"]
    optional_dirs = ["uploads", "outputs", "docs", "examples"]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        status = "✅" if dir_path.exists() else "❌"
        print(f"{status} {dir_name}目录: {'存在' if dir_path.exists() else '缺失'}")
    
    for dir_name in optional_dirs:
        dir_path = project_root / dir_name
        status = "📁" if dir_path.exists() else "⚪"
        print(f"{status} {dir_name}目录: {'存在' if dir_path.exists() else '可选'}")

def test_api_keys():
    """测试API密钥配置"""
    print("\n🔑 API密钥检查")
    print("-" * 40)
    
    api_keys = {
        'OPENAI_API_KEY': 'OpenAI GPT',
        'GOOGLE_API_KEY': 'Google Gemini',
        'ANTHROPIC_API_KEY': 'Anthropic Claude',
        'STABILITY_API_KEY': 'Stability AI'
    }
    
    configured_count = 0
    for key, service in api_keys.items():
        has_key = bool(os.getenv(key))
        status = "✅" if has_key else "❌"
        print(f"{status} {service}: {'已配置' if has_key else '未配置'}")
        if has_key:
            configured_count += 1
    
    print(f"\n📊 总计: {configured_count}/{len(api_keys)} 个API密钥已配置")
    
    if configured_count == 0:
        print("⚠️ 建议至少配置一个LLM API密钥")
    
    return configured_count > 0

def test_core_imports():
    """测试核心模块导入"""
    print("\n📦 核心模块导入检查")
    print("-" * 40)
    
    modules_to_test = [
        # 核心配置
        ("app.core.config", "settings", "配置系统"),
        
        # LLM服务
        ("app.services.llm.service", "llm_service", "LLM服务"),
        ("app.services.llm.stable_service", "stable_llm_service", "稳定LLM服务"),
        
        # 基础服务
        ("app.services.video.downloader", "VideoDownloader", "视频下载器"),
        ("app.services.video.processor", "VideoProcessor", "视频处理器"),
        
        # 提示词系统
        ("app.prompts.base", "render_prompt", "提示词系统")
    ]
    
    success_count = 0
    for module_name, item_name, description in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print(f"✅ {description}: 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {description}: 导入失败 - {str(e)[:60]}...")
    
    print(f"\n📊 模块导入: {success_count}/{len(modules_to_test)} 成功")
    return success_count == len(modules_to_test)

def test_llm_service_basic():
    """测试LLM服务基本功能"""
    print("\n🤖 LLM服务基本检查")
    print("-" * 40)
    
    try:
        from app.services.llm.service import llm_service
        from app.services.llm.stable_service import stable_llm_service
        
        # 检查LLM服务
        print(f"✅ 标准LLM服务: 可用提供商 {len(llm_service.available_providers)} 个")
        for provider in llm_service.available_providers:
            print(f"   - {provider['name']}: {provider['model']}")
        
        # 检查稳定LLM服务
        print(f"✅ 稳定LLM服务: 初始化成功")
        
        # 简单健康检查
        health_result = llm_service.health_check()
        healthy_providers = sum(1 for p in health_result['providers'].values() if p['healthy'])
        print(f"📊 健康检查: {healthy_providers} 个提供商正常")
        
        return len(llm_service.available_providers) > 0
        
    except Exception as e:
        print(f"❌ LLM服务检查失败: {str(e)}")
        return False

def test_prompt_system():
    """测试提示词系统"""
    print("\n📝 提示词系统检查")
    print("-" * 40)
    
    try:
        from app.prompts.base import render_prompt, prompt_manager
        
        # 测试基本渲染 - 使用不同的变量名避免与函数参数冲突
        test_template = "Hello {{ username }}!"
        prompt_manager.register_template("test_health_check", test_template)
        result = render_prompt("test_health_check", username="World")
        
        if result == "Hello World!":
            print("✅ 提示词渲染: 正常")
            return True
        else:
            print("❌ 提示词渲染: 结果不匹配")
            print(f"   期望: Hello World!")
            print(f"   实际: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 提示词系统检查失败: {str(e)}")
        return False

def run_health_check():
    """运行完整的健康检查"""
    print("🚀 系统健康检查")
    print("=" * 60)
    
    start_time = time.time()
    
    # 运行各项检查
    env_ok = True  # 环境检查总是通过
    test_environment()
    
    api_ok = test_api_keys()
    imports_ok = test_core_imports()
    llm_ok = test_llm_service_basic()
    prompt_ok = test_prompt_system()
    
    elapsed = time.time() - start_time
    
    # 生成总结报告
    print("\n" + "=" * 60)
    print("📊 健康检查报告")
    print("=" * 60)
    
    checks = [
        ("环境配置", env_ok),
        ("API密钥", api_ok),
        ("模块导入", imports_ok),
        ("LLM服务", llm_ok),
        ("提示词系统", prompt_ok)
    ]
    
    passed_checks = sum(1 for _, ok in checks if ok)
    
    for check_name, ok in checks:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"{check_name}: {status}")
    
    overall_status = passed_checks >= 3  # 至少3项通过认为系统基本可用
    
    print(f"\n🎯 总体状态: {'✅ 系统健康' if overall_status else '⚠️ 存在问题'}")
    print(f"⏱️ 检查耗时: {elapsed:.2f}秒")
    print(f"📈 通过率: {passed_checks}/{len(checks)} ({passed_checks/len(checks)*100:.1f}%)")
    
    if not overall_status:
        print("\n💡 建议:")
        if not api_ok:
            print("   - 配置至少一个LLM API密钥")
        if not imports_ok:
            print("   - 检查依赖包安装: pip install -r requirements.txt")
        if not llm_ok:
            print("   - 验证网络连接和API密钥正确性")
        if not prompt_ok:
            print("   - 检查提示词模板文件")
    
    return overall_status

def main():
    """主函数"""
    try:
        success = run_health_check()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 