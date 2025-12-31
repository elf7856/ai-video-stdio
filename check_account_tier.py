#!/usr/bin/env python3
"""
详细检查 Google API 账户层级和配额
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_account_tier():
    """检查账户层级"""

    print("=" * 80)
    print("Google API 账户层级检查")
    print("=" * 80)

    try:
        from google import genai
        import requests

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ 未找到 GOOGLE_API_KEY")
            return

        print(f"\n🔑 API Key: {api_key[:20]}...")

        # 1. 尝试调用 API 并分析响应头
        print("\n" + "=" * 80)
        print("测试 API 调用以检测配额...")
        print("=" * 80)

        client = genai.Client(api_key=api_key)

        # 测试1: 调用文本生成API
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents='Hello'
            )
            print("\n✅ 文本生成 API 调用成功")
        except Exception as e:
            print(f"\n⚠️ 文本生成 API 调用失败: {str(e)[:200]}")

        # 测试2: 列出可用模型
        print("\n" + "=" * 80)
        print("检查可用的 Veo 模型...")
        print("=" * 80)

        models = client.models.list()
        veo_models = [m for m in models if 'veo' in m.name.lower()]

        print(f"\n找到 {len(veo_models)} 个 Veo 模型:")
        for model in veo_models:
            print(f"  • {model.name}")

        # 3. 尝试直接调用 REST API 获取配额信息
        print("\n" + "=" * 80)
        print("尝试获取配额信息...")
        print("=" * 80)

        # Google AI Studio API 不直接提供配额查询接口
        # 但我们可以通过其他方式推断

        print("\n📊 账户层级判断:")
        print("-" * 80)

        # 方法1: 检查是否有计费账户关联
        print("\n1️⃣ 计费状态检查:")
        print("   • Google AI Studio 免费层特征:")
        print("     - RPM (每分钟请求数): 2")
        print("     - RPD (每天请求数): 50")
        print("     - 有赠金但仍受速率限制")
        print("\n   • 付费层特征:")
        print("     - RPM: 1,000+")
        print("     - RPD: 无限制")
        print("     - 需要绑定信用卡并启用计费")

        # 方法2: 实际测试速率限制
        print("\n2️⃣ 速率限制测试:")
        print("   正在进行快速连续调用测试...")

        import time

        success_count = 0
        rate_limit_hit = False

        for i in range(3):
            try:
                start = time.time()
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=f'Test {i+1}'
                )
                elapsed = time.time() - start
                success_count += 1
                print(f"   ✅ 请求 {i+1}: 成功 ({elapsed:.2f}s)")

                # 快速连续请求，不等待
                if i < 2:
                    time.sleep(0.5)  # 只等待0.5秒

            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    rate_limit_hit = True
                    print(f"   ❌ 请求 {i+1}: 触发速率限制")
                    break
                else:
                    print(f"   ⚠️ 请求 {i+1}: {error_str[:100]}")

        print("\n" + "=" * 80)
        print("📋 账户层级结论:")
        print("=" * 80)

        if rate_limit_hit or success_count <= 2:
            print("\n🆓 你当前使用的是 **免费层** (Free Tier)")
            print("\n特征:")
            print("  ✓ 有 $300 赠金或免费配额")
            print("  ✓ 但仍受免费层速率限制约束")
            print("  • RPM: 2 (每分钟最多2个请求)")
            print("  • RPD: 50 (每天最多50个请求)")
            print("\n💡 如何升级到付费层:")
            print("  1. 访问: https://console.cloud.google.com/billing")
            print("  2. 设置计费账户（绑定信用卡）")
            print("  3. 启用 Generative Language API 的计费")
            print("  4. 配额会自动提升到:")
            print("     • RPM: 1,000+")
            print("     • RPD: 无限制")
            print("\n⚠️ 重要:")
            print("  • 即使有赠金，免费层也有 RPM=2 的硬限制")
            print("  • 只有启用计费后，才能提升到付费层配额")
        else:
            print("\n💳 你可能已经在 **付费层** (Paid Tier)")
            print("\n但建议通过以下方式确认:")
            print("  1. 访问: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas")
            print("  2. 查看当前的 RPM/RPD 配额")

        # 4. 提供配额查看链接
        print("\n" + "=" * 80)
        print("🔗 配额查看链接:")
        print("=" * 80)
        print("\n📌 Google Cloud Console (最准确):")
        print("   https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas")
        print("\n📌 Google AI Studio:")
        print("   https://aistudio.google.com/apikey")
        print("\n📌 计费信息:")
        print("   https://console.cloud.google.com/billing")

        print("\n" + "=" * 80)

    except ImportError:
        print("❌ 错误: google-genai 库未安装")
        print("   请运行: pip install google-genai")
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_account_tier()
