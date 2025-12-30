# 图像生成功能文档

## 概述

Video Creator Platform 现在支持多个主流的第三方图像生成API，提供强大而灵活的图像生成能力。系统会自动选择可用的最佳生成器，并支持故障转移机制。

## 支持的图像生成器

### 1. DALL-E (OpenAI)
- **特点**: 高质量、创意丰富、理解能力强
- **模型**: DALL-E 3
- **尺寸**: 1024x1024, 1792x1024, 1024x1792
- **质量**: standard, hd
- **风格**: vivid, natural
- **配置**: 使用 `OPENAI_API_KEY`

### 2. Stability AI
- **特点**: 开源模型、高度可定制、支持多种风格
- **模型**: Stable Diffusion XL 1024
- **尺寸**: 自定义
- **特点**: 支持负面提示词、种子控制
- **配置**: 使用 `STABILITY_API_KEY`

### 3. Replicate
- **特点**: 云端推理、多种模型、易于使用
- **模型**: Stability AI SDXL
- **尺寸**: 自定义
- **特点**: 支持批量生成、多种参数调整
- **配置**: 使用 `REPLICATE_API_KEY`

### 4. Leonardo AI
- **特点**: 专业级质量、独特风格、创意工具
- **模型**: Leonardo Creative
- **尺寸**: 自定义
- **特点**: Prompt Magic、PhotoReal模式
- **配置**: 使用 `LEONARDO_API_KEY`

### 5. 本地 Stable Diffusion
- **特点**: 离线运行、隐私保护、完全控制
- **模型**: 可自定义
- **要求**: GPU加速（推荐）
- **特点**: 无需API密钥、无网络依赖

## 配置说明

### 环境变量配置

在 `.env` 文件中配置相应的API密钥：

```bash
# 图像生成API Keys
OPENAI_API_KEY=your_openai_api_key_here
STABILITY_API_KEY=your_stability_api_key_here
REPLICATE_API_KEY=your_replicate_api_key_here
LEONARDO_API_KEY=your_leonardo_api_key_here

# 图像生成配置
DEFAULT_IMAGE_PROVIDER=dalle
DALLE_MODEL=dall-e-3
DALLE_QUALITY=standard
DALLE_STYLE=vivid
STABILITY_MODEL=stable-diffusion-xl-1024-v1-0
REPLICATE_MODEL=stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b
LEONARDO_MODEL=ac614f96-1082-45bf-be9d-757f2d31c174
```

### 获取API密钥

1. **DALL-E**: 在 [OpenAI Platform](https://platform.openai.com/) 注册并获取API密钥
2. **Stability AI**: 在 [Stability AI](https://platform.stability.ai/) 注册并获取API密钥
3. **Replicate**: 在 [Replicate](https://replicate.com/) 注册并获取API密钥
4. **Leonardo AI**: 在 [Leonardo AI](https://leonardo.ai/) 注册并获取API密钥

## API 使用

### 1. 获取可用生成器

```bash
GET /api/images/providers
```

响应示例：
```json
{
  "available_providers": ["dalle", "stability", "replicate"],
  "provider_info": {
    "dalle": {"available": true, "current": true},
    "stability": {"available": true, "current": false},
    "replicate": {"available": true, "current": false}
  },
  "default_provider": "dalle"
}
```

### 2. 生成图像

```bash
POST /api/images/generate
```

参数：
- `prompt`: 图像描述
- `style`: 风格（可选）
- `provider`: 指定生成器（可选）
- `size`: 尺寸，格式为 "宽x高"（可选）
- `negative_prompt`: 负面提示词（可选）

示例：
```bash
curl -X POST "http://localhost:8000/api/images/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一个未来科技感的城市夜景，霓虹灯闪烁",
    "style": "cyberpunk",
    "provider": "dalle",
    "size": "1024x1024"
  }'
```

### 3. 基于内容需求生成图像

```bash
POST /api/images/generate-with-description
```

参数：
- `content_requirement`: 内容需求描述
- `style`: 风格（默认: realistic）
- `provider`: 指定生成器（可选）
- `size`: 尺寸（可选）

### 4. 批量生成图像

```bash
POST /api/images/generate-batch
```

参数：
- `prompts`: 提示词列表（最多10个）
- `style`: 风格（可选）
- `provider`: 指定生成器（可选）
- `size`: 尺寸（可选）
- `negative_prompt`: 负面提示词（可选）

### 5. 获取可用风格

```bash
GET /api/images/styles
```

响应示例：
```json
{
  "styles": {
    "realistic": "写实风格，高细节，照片级质量",
    "anime": "动漫风格，鲜艳色彩，详细插画",
    "cartoon": "卡通风格，简单色彩，清晰线条",
    "cyberpunk": "赛博朋克风格，霓虹灯，未来感"
  },
  "default_style": "realistic"
}
```

## 编程接口使用

### 基本使用

```python
from app.services.image.generator import ImageServiceManager

# 初始化图像服务
image_manager = ImageServiceManager()

# 生成图像
image_path = await image_manager.generate_image(
    prompt="一只可爱的小猫在花园里玩耍",
    style="realistic",
    provider="dalle",
    size=(1024, 1024)
)

print(f"生成的图像路径: {image_path}")
```

### 批量生成

```python
# 批量生成图像
prompts = [
    "一只可爱的小猫在花园里玩耍",
    "夕阳西下的海滩风景",
    "现代科技感的办公环境"
]

results = await image_manager.generator.generate_image_batch(
    prompts=prompts,
    style="realistic",
    size=(512, 512)
)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"图像 {i+1} 生成失败: {result}")
    else:
        print(f"图像 {i+1} 生成成功: {result}")
```

### 获取生成器信息

```python
# 获取可用的生成器
providers = image_manager.get_available_providers()
print(f"可用的生成器: {providers}")

# 获取生成器详细信息
provider_info = image_manager.get_provider_info()
print(f"生成器信息: {provider_info}")
```

## 风格预设

系统内置了多种风格预设，可以快速应用：

- **realistic**: 写实风格，高细节，照片级质量
- **anime**: 动漫风格，鲜艳色彩，详细插画
- **cartoon**: 卡通风格，简单色彩，清晰线条
- **oil_painting**: 油画风格，艺术感，质感笔触
- **watercolor**: 水彩画风格，柔和色彩，流动感
- **cyberpunk**: 赛博朋克风格，霓虹灯，未来感
- **vintage**: 复古风格，复古色彩，老式风格
- **minimalist**: 极简风格，简单，干净，几何

## 故障转移机制

系统具有智能的故障转移机制：

1. 优先使用配置的默认生成器
2. 如果默认生成器失败，自动尝试其他可用的生成器
3. 支持手动指定生成器
4. 提供详细的错误信息和状态反馈

## 性能优化

### 并发控制
- 最大并发生成数：5
- 生成超时时间：300秒
- 重试次数：3次

### 缓存机制
- 支持图像结果缓存
- 避免重复生成相同内容
- 提高响应速度

## 错误处理

常见错误及解决方案：

1. **API密钥错误**
   - 检查API密钥是否正确配置
   - 确认API密钥是否有效
   - 检查账户余额和配额

2. **网络连接问题**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试使用本地模型

3. **内容过滤**
   - 修改提示词避免敏感内容
   - 使用更温和的描述
   - 尝试不同的生成器

4. **资源不足**
   - 减少并发请求数
   - 使用更小的图像尺寸
   - 等待资源释放后重试

## 最佳实践

1. **提示词优化**
   - 使用详细、具体的描述
   - 包含风格、光照、构图等细节
   - 避免模糊或矛盾的描述

2. **生成器选择**
   - DALL-E：适合创意和艺术性内容
   - Stability AI：适合技术性和精确控制
   - Replicate：适合快速原型和实验
   - Leonardo AI：适合专业级作品

3. **批量生成**
   - 合理控制批量大小
   - 使用相似的风格和参数
   - 监控API使用量和成本

4. **错误处理**
   - 实现重试机制
   - 记录错误日志
   - 提供用户友好的错误信息

## 扩展开发

### 添加新的生成器

1. 继承 `ImageGeneratorBase` 类
2. 实现 `generate_image` 和 `is_available` 方法
3. 在 `ImageGenerator` 类中注册新生成器
4. 添加相应的配置项

### 自定义风格

1. 在 `apply_style_preset` 方法中添加新风格
2. 更新风格描述和参数
3. 测试新风格的效果

### 集成新的API

1. 研究API文档和限制
2. 实现API客户端
3. 处理认证和错误
4. 添加配置和测试 