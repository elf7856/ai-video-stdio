#!/usr/bin/env python3
"""
简单的Google Gemini API测试
直接使用环境变量中的配置进行测试
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

def test_gemini():
    """测试Google Gemini API"""
    
    print("🔍 Google Gemini API 测试")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ 未找到GOOGLE_API_KEY环境变量")
        print("请在.env文件中配置: GOOGLE_API_KEY=your_api_key")
        return False
    
    print(f"✅ API密钥已配置: {api_key[:10]}...{api_key[-4:]}")
    
    # API配置
    model = "gemini-1.5-flash"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    # 测试数据
    test_data = {
        "contents": [{
            "parts": [{"text": "你好！请简单介绍一下你自己，不超过50字。"}]
        }],
        "generationConfig": {
            "maxOutputTokens": 100,
            "temperature": 0.3
        }
    }
    
    print(f"🎯 测试模型: {model}")
    print(f"🌐 API端点: {endpoint.split('?')[0]}")
    print(f"📝 测试问题: {test_data['contents'][0]['parts'][0]['text']}")
    print()
    
    # 发送请求
    try:
        print("🚀 发送API请求...")
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            headers={
                "Content-Type": "application/json"
            },
            json=test_data,
            timeout=30
        )
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        print(f"⏱️ 响应时间: {response_time}秒")
        print(f"📊 HTTP状态码: {response.status_code}")
        
        # 处理响应
        if response.status_code == 200:
            result = response.json()
            
            if 'candidates' in result and result['candidates']:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print("✅ API调用成功！")
                print(f"📝 Gemini回复: {content}")
                
                # 显示详细信息
                if 'usageMetadata' in result:
                    usage = result['usageMetadata']
                    print(f"📈 Token使用情况:")
                    print(f"   输入Token: {usage.get('promptTokenCount', 'N/A')}")
                    print(f"   输出Token: {usage.get('candidatesTokenCount', 'N/A')}")
                    print(f"   总计Token: {usage.get('totalTokenCount', 'N/A')}")
                
                return True
            else:
                print("❌ API返回空结果")
                print(f"📄 完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return False
                
        else:
            print(f"❌ API调用失败 (HTTP {response.status_code})")
            try:
                error_data = response.json()
                print(f"📄 错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                
                # 分析常见错误
                if response.status_code == 400:
                    error_message = error_data.get('error', {}).get('message', '')
                    if 'location' in error_message.lower():
                        print("💡 这是地区限制问题，需要:")
                        print("   1. 使用VPN连接到支持的地区")
                        print("   2. 或者部署到海外服务器")
                    elif 'key' in error_message.lower():
                        print("💡 这是API密钥问题，请检查:")
                        print("   1. API密钥是否正确")
                        print("   2. 是否启用了Generative AI API")
                
                elif response.status_code == 429:
                    print("💡 请求频率限制，建议:")
                    print("   1. 等待一段时间后重试")
                    print("   2. 升级到付费计划")
                
                elif response.status_code == 503:
                    print("💡 服务暂时不可用，建议:")
                    print("   1. 等待几分钟后重试")
                    print("   2. 配置其他API作为备用")
                    
            except:
                print(f"📄 原始错误响应: {response.text}")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时 (30秒)")
        print("💡 可能的原因:")
        print("   1. 网络连接问题")
        print("   2. Google服务器响应慢")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        print("💡 可能的原因:")
        print("   1. 网络连接问题")
        print("   2. 需要VPN访问Google服务")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False

def run_multiple_tests():
    """运行多个测试"""
    print("🔄 运行连续测试 (3次)...")
    print()
    
    success_count = 0
    total_tests = 3
    
    for i in range(total_tests):
        print(f"📝 测试 #{i+1}/{total_tests}")
        print("-" * 30)
        
        if test_gemini():
            success_count += 1
        
        print()
        
        # 如果不是最后一次测试，等待一下
        if i < total_tests - 1:
            print("⏳ 等待3秒后继续...")
            time.sleep(3)
    
    print("=" * 50)
    print(f"📊 测试总结: {success_count}/{total_tests} 成功")
    
    if success_count == total_tests:
        print("🎉 所有测试都成功! Google Gemini API工作正常")
    elif success_count > 0:
        print("⚠️ 部分测试成功，API可能不稳定")
    else:
        print("❌ 所有测试都失败，请检查配置和网络")

if __name__ == "__main__":
    print("🚀 Google Gemini API 测试工具")
    print()
    
    # 选择测试模式
    mode = input("选择测试模式 (1=单次测试, 2=连续测试): ").strip()
    
    print()
    
    if mode == "2":
        run_multiple_tests()
    else:
        test_gemini() 