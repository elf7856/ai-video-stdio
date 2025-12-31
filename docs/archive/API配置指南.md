# 🔑 API配置指南

## 📋 配置概述

根据当前平台状态，建议按以下优先级配置API服务。

## 🥇 第一优先级：OpenAI API

### 为什么选择OpenAI？
- **一个API KEY解锁4个服务**：GPT、Whisper、DALL-E、TTS
- **质量最高**：业界标准，稳定可靠
- **文档完善**：集成简单，社区支持好
- **性价比高**：相比单独购买多个服务更划算

### 配置步骤

1. **获取API KEY**
   - 访问：https://platform.openai.com/api-keys
   - 注册/登录OpenAI账号
   - 创建新的API密钥
   - **重要**：复制并安全保存密钥（只显示一次）

2. **配置环境变量**
   ```bash
   # 在项目根目录创建 .env 文件（如果还没有）
   echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
   ```

3. **验证配置**
   ```bash
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print('OpenAI API Key配置状态:', '已配置' if os.getenv('OPENAI_API_KEY') else '未配置')
   "
   ```

### 解锁的功能
- ✅ **GPT-4/GPT-3.5** - 智能内容分析和生成
- ✅ **Whisper** - 高质量语音识别（支持99种语言）
- ✅ **DALL-E** - AI图像生成
- ✅ **TTS** - 自然语音合成

### 预估费用
- **GPT-4**: ~$0.03/1K tokens（输入），~$0.06/1K tokens（输出）
- **Whisper**: $0.006/分钟
- **DALL-E**: $0.020/图（1024×1024）
- **TTS**: $0.015/1K字符

## 🥈 第二优先级：图像生成增强

### Replicate API

**优势**：
- 多种开源模型可选
- 按使用量付费
- 社区模型丰富

**配置步骤**：
1. 访问：https://replicate.com/account/api-tokens
2. 创建API token
3. 添加到环境变量：
   ```bash
   echo "REPLICATE_API_TOKEN=your_replicate_token" >> .env
   ```

### Stability AI

**优势**：
- Stable Diffusion官方API
- 图像质量稳定
- 支持多种模型

**配置步骤**：
1. 访问：https://platform.stability.ai/account/keys
2. 创建API key
3. 添加到环境变量：
   ```bash
   echo "STABILITY_API_KEY=your_stability_key" >> .env
   ```

## 🥉 第三优先级：高级语音服务

### ElevenLabs TTS

**优势**：
- 最高质量的语音合成
- 支持语音克隆
- 情感表达丰富

**配置步骤**：
1. 访问：https://elevenlabs.io/speech-synthesis
2. 注册并获取API key
3. 添加到环境变量：
   ```bash
   echo "ELEVENLABS_API_KEY=your_elevenlabs_key" >> .env
   ```

**注意**：价格较高，建议在基础功能稳定后再考虑

## 🔧 配置验证

配置完成后，运行以下命令验证：

```bash
python -c "
from app.core.api_manager import api_manager
import asyncio

async def verify_config():
    print('🔍 验证API配置...')
    results = await api_manager.check_all_apis()
    
    print('\n📊 配置结果:')
    for api_name, status in results.items():
        icon = '✅' if status.value == 'ready' else '⚠️' if status.value == 'configured' else '❌'
        print(f'{icon} {api_name}: {status.value}')
    
    # 统计可用服务
    ready_count = sum(1 for s in results.values() if s.value == 'ready')
    total_count = len(results)
    print(f'\n总体状态: {ready_count}/{total_count} 个API就绪')

asyncio.run(verify_config())
"
```

## 💰 费用预估

### 轻度使用（个人/测试）
- **OpenAI**: $10-30/月
- **Replicate**: $5-15/月
- **总计**: $15-45/月

### 中度使用（小团队/产品）
- **OpenAI**: $50-150/月
- **Replicate**: $20-50/月
- **Stability**: $30-80/月
- **总计**: $100-280/月

### 重度使用（商业产品）
- **OpenAI**: $200-500/月
- **多个图像服务**: $100-300/月
- **ElevenLabs**: $50-200/月
- **总计**: $350-1000/月

## 📝 最佳实践

### 1. 安全性
- ❌ 不要在代码中硬编码API密钥
- ✅ 使用环境变量存储密钥
- ✅ 将.env文件添加到.gitignore
- ✅ 定期轮换API密钥

### 2. 成本控制
- 设置每月消费限额
- 监控API使用量
- 优先使用免费额度
- 缓存结果减少重复调用

### 3. 性能优化
- 实现API调用重试机制
- 使用备用提供商
- 合理设置超时时间
- 批量处理提高效率

## 🚀 快速开始

最小化配置（仅OpenAI）：

```bash
# 1. 获取OpenAI API Key
# 2. 配置环境变量
echo "OPENAI_API_KEY=your_key_here" >> .env

# 3. 验证配置
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

if os.getenv('OPENAI_API_KEY'):
    print('✅ OpenAI API配置成功！')
    print('🎉 你已解锁：GPT、Whisper、DALL-E、TTS')
else:
    print('❌ 请检查OPENAI_API_KEY配置')
"
```

配置完成后，重启服务：
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🆘 常见问题

### Q: API密钥无效
**A**: 检查密钥是否正确复制，注意去除多余空格

### Q: 配置后仍显示未就绪
**A**: 重启应用，某些配置需要重新加载

### Q: 费用控制
**A**: 在各平台设置月度限额，并监控使用量

### Q: 中国大陆访问问题
**A**: 某些API可能需要配置代理，建议使用海外服务器 