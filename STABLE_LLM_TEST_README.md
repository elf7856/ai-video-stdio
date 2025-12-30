# 稳定LLM服务测试

## 概述

为了解决当前LLM调用不稳定的问题，我们创建了一个简化的稳定LLM服务和相应的测试框架。

## 特点

### 🎯 稳定性优化
- **简化依赖**: 直接使用HTTP请求，避免复杂的第三方库问题
- **保守配置**: 使用经过验证的稳定模型和参数
- **智能重试**: 针对不同错误类型的重试策略
- **优先级顺序**: OpenAI > Google > Anthropic

### 🔧 技术改进
- **固定超时**: 10秒超时，避免长时间等待
- **简化重试**: 最多2次重试，间隔3秒
- **错误分类**: 针对SSL、超时、限流等不同错误的处理
- **会话复用**: 使用requests.Session提高连接效率

## 快速开始

### 1. 设置API密钥
```bash
# 至少设置一个API密钥
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"  
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 2. 运行测试
```bash
# 一键运行稳定性测试
python run_stable_test.py

# 或者直接运行测试文件
python tests/test_stable_llm.py
```

## 测试内容

### 📋 测试类别

1. **基础功能测试** (5个测试)
   - 简单问答
   - 基础计算
   - 概念解释
   - 列举任务

2. **复杂提示测试** (4个测试)
   - 情感分析
   - 技术总结
   - 比较分析
   - 内容创作

3. **边界情况测试** (7个测试)
   - 空输入
   - 单字符
   - 中英文混合
   - emoji字符
   - 长文本

4. **健康检查**
   - 服务可用性
   - 响应时间
   - 错误处理

### 📊 报告内容

- **总体统计**: 成功率、平均响应时间
- **分类统计**: 各类测试的成功率
- **提供商统计**: 各API服务的使用情况
- **性能分析**: 快速/慢速响应分布
- **失败分析**: 失败案例和错误类型
- **稳定性等级**: A/B/C/D等级评定

## 文件结构

```
├── app/services/llm/
│   ├── stable_service.py          # 稳定LLM服务核心
│   └── service.py                 # 原有复杂服务
├── tests/
│   ├── test_stable_llm.py         # 稳定性测试主文件
│   ├── test_prompt_stability.py   # 原有prompt测试
│   └── test_video_analysis_mock.py # 模拟视频分析测试
├── run_stable_test.py             # 一键启动脚本
└── STABLE_LLM_TEST_README.md      # 本说明文档
```

## 使用示例

### 基础调用
```python
from app.services.llm.stable_service import stable_llm_service

# 简单调用
result = stable_llm_service.simple_call("什么是人工智能？")

if result['success']:
    print(f"回答: {result['content']}")
    print(f"提供商: {result['provider']}")
else:
    print(f"错误: {result['error']}")
```

### 健康检查
```python
# 检查服务健康状态
health = stable_llm_service.health_check()
print(f"服务健康: {health['overall_healthy']}")
```

## 稳定性对比

| 特性 | 原有服务 | 稳定服务 |
|------|----------|----------|
| 依赖库 | litellm + 多种配置 | requests（标准库） |
| 超时策略 | 复杂可变 | 固定10秒 |
| 重试机制 | 多层嵌套 | 简化2次 |
| 错误处理 | 复杂分类 | 基础分类 |
| 模型选择 | 最新模型 | 稳定模型 |
| SSL处理 | 复杂配置 | 标准处理 |

## 常见问题

### Q: 为什么要创建新的稳定服务？
A: 原有服务依赖复杂，在某些环境下容易出现SSL、超时等问题。稳定服务专注于基础功能，提高可靠性。

### Q: 稳定服务支持哪些功能？
A: 目前支持基础的文本生成，足够满足大部分测试和开发需求。

### Q: 可以同时使用两种服务吗？
A: 可以。稳定服务主要用于测试和开发阶段，原有服务可以用于生产环境的复杂需求。

### Q: 如何提高成功率？
A: 
1. 确保网络连接稳定
2. 设置多个API密钥作为备用
3. 避免在高峰期测试
4. 简化prompt复杂度

## 下一步计划

1. **性能监控**: 添加详细的性能指标收集
2. **缓存机制**: 对相同请求进行缓存
3. **配置优化**: 根据测试结果调整超时和重试参数
4. **集成测试**: 与CI/CD系统集成

## 贡献

如果遇到问题或有改进建议，请：
1. 运行测试并收集错误日志
2. 记录具体的环境信息
3. 提供复现步骤
4. 提交issue或PR

---

*稳定LLM服务 - 简单、稳定、可靠* 🚀 