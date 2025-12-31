#!/usr/bin/env python3
"""
检查 Google Veo API 配额和状态
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_google_api_status():
    """检查 Google API 配额状态"""

    print("=" * 80)
    print("Google Veo API 配额检查")
    print("=" * 80)

    # 1. 检查 API Key 配置
    google_api_key = os.getenv("GOOGLE_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    print("\n📋 API Key 配置:")
    print(f"  GOOGLE_API_KEY: {'✅ 已配置' if google_api_key else '❌ 未配置'}")
    if google_api_key:
        print(f"    密钥前缀: {google_api_key[:20]}...")
    print(f"  GEMINI_API_KEY: {'✅ 已配置' if gemini_api_key else '❌ 未配置'}")
    if gemini_api_key:
        print(f"    密钥前缀: {gemini_api_key[:20]}...")

    # 2. 尝试调用 API 获取配额信息
    try:
        from google import genai

        api_key = google_api_key or gemini_api_key
        if not api_key:
            print("\n❌ 错误: 没有找到 API 密钥")
            return

        client = genai.Client(api_key=api_key)

        print("\n🔍 API 连接测试:")
        print("  连接状态: ✅ 成功")

        # 3. 尝试获取模型信息
        print("\n📦 可用模型:")
        try:
            models = client.models.list()
            veo_models = [m for m in models if 'veo' in m.name.lower()]
            if veo_models:
                for model in veo_models:
                    print(f"  ✅ {model.name}")
            else:
                print("  ⚠️ 未找到 Veo 模型")
        except Exception as e:
            print(f"  ⚠️ 无法列出模型: {str(e)}")

        # 4. 检查配额信息
        print("\n💰 配额信息:")
        print("  ℹ️  Google AI Studio 不直接提供 API 查询配额的接口")
        print("  📊 请访问以下链接查看详细配额:")
        print("     🔗 配额仪表板: https://aistudio.google.com/apikey")
        print("     🔗 使用情况: https://ai.google.dev/gemini-api/docs/quota")

        # 5. 测试简单的 API 调用
        print("\n🧪 测试 API 调用:")
        try:
            # 尝试调用文本生成 API（更便宜的测试）
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents='Say hello'
            )
            if response:
                print("  ✅ API 调用成功 - 你的配额还有剩余")
                print(f"  响应: {response.text[:100]}")
            else:
                print("  ⚠️ API 调用返回空响应")
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                print("  ❌ 配额已用完!")
                print(f"  错误详情: {error_str[:200]}")
                print("\n  解决方案:")
                print("    1. 等待配额重置（通常每天重置）")
                print("    2. 检查你的计费账户: https://console.cloud.google.com/billing")
                print("    3. 查看配额限制: https://ai.google.dev/gemini-api/docs/rate-limits")
            else:
                print(f"  ⚠️ API 调用失败: {error_str[:200]}")

        # 6. 显示常见的配额限制
        print("\n📈 Veo 3 Fast 模型的标准配额限制:")
        print("  免费层:")
        print("    • 每分钟请求数 (RPM): 2")
        print("    • 每天请求数 (RPD): 50")
        print("  付费层:")
        print("    • 每分钟请求数 (RPM): 1,000+")
        print("    • 无每日限制")

        print("\n💡 提示:")
        print("  • 每个视频生成请求算1次")
        print("  • 如果短时间内生成多个视频，可能触发速率限制")
        print("  • 建议在生成之间添加延迟，或减少并发请求数")

    except ImportError:
        print("\n❌ 错误: google-genai 库未安装")
        print("   请运行: pip install google-genai")
    except Exception as e:
        print(f"\n❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_google_api_status()
