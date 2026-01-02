# Google Imagen 集成文档

## 概述

成功将 Google Gemini 3 Pro Image Preview 模型集成到视频创作平台中，用于生成高质量图像。

## 集成的模型

- **模型名称**: `gemini-3-pro-image-preview`
- **API方法**: `client.models.generate_content()`
- **响应模式**: `['TEXT', 'IMAGE']`

## 文件结构

### 核���文件

1. **app/services/image/google_imagen_generator.py** (新建)
   - `GoogleImagenGenerator` 类：核心图像生成器
   - 支持多种宽高比和分辨率
   - 懒加载客户端实例
   - 批量生成功能

2. **app/services/image/generator.py** (修改)
   - 添加 `GoogleImagenAdapter` 适配器
   - 集成到 `ImageGenerator` 统一管理
   - 在 `generators` 字典中注册为 `'google_imagen'`

3. **test_imagen_quick.py** (新建)
   - 快速测试脚本
   - 测试基础生成和API集成

## 使用方法

### 直接使用

```python
from app.services.image.google_imagen_generator import GoogleImagenGenerator

generator = GoogleImagenGenerator()

# 生成图像
image_path = await generator.generate_image(
    prompt="A beautiful sunset over mountains",
    aspect_ratio="16:9",
    resolution="medium"
)
```

### 通过服务管理器使用

```python
from app.services.image.generator import ImageServiceManager

manager = ImageServiceManager()

# 使用google_imagen生成器
image_path = await manager.generate_image(
    prompt="A futuristic city skyline",
    provider="google_imagen",
    size=(1024, 576)  # 16:9
)
```

## 支持的参数

### 宽高比 (aspect_ratio)
- `"1:1"` - 正方形 (1024x1024)
- `"3:4"` - 竖向 (768x1024)
- `"4:3"` - 横向 (1024x768)
- `"9:16"` - 手机竖屏 (576x1024)
- `"16:9"` - 宽屏横向 (1024x576)

### 分辨率 (resolution)
- `"low"` - 低分辨率
- `"medium"` - 中等分辨率（默认）
- `"high"` - 高分辨率

### 其他参数
- `negative_prompt` - 负面提示词（整合到prompt中）
- `size` - 像素尺寸，自动转换为aspect_ratio

## 技术要点

### API调用方式

```python
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=prompt,
    config=genai.types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
    )
)
```

### 重要发现

1. **不支持 media_resolution 参数**
   - 官方教程显示的 `media_resolution` 参数在 `gemini-3-pro-image-preview` 模型中不可用
   - 错误信息: "Media resolution is not enabled for this model"

2. **参数传递方式**
   - aspect_ratio 和 resolution 需要通过 **prompt 描述** 传递
   - 示例: "Create a high resolution image with 16:9 aspect ratio. [原始prompt]"

3. **响应处理**
   - 使用 `response_modalities=['TEXT', 'IMAGE']` 指定返回类型
   - 从 `response.candidates[0].content.parts` 中提取图像数据
   - 图像数据在 `part.inline_data.data` 中

## 测试结果

### 测试1: 基础图像生成
✅ 通过
- 成功生成图像
- 文件大小: ~0.8-1.0 MB
- 输出格式: PNG

### 测试2: API集成
✅ 通过
- 通过 ImageServiceManager 调用成功
- 与其他生成器无缝集成
- 可用生成器列表中显示 `google_imagen`

## 生成的测试图像

```bash
ls -lh ./outputs/images/gemini_imagen_*.png
-rw-r--r--  1.0M  gemini_imagen_1765116381.png
-rw-r--r--  807K  gemini_imagen_1765116432.png
-rw-r--r--  1.0M  gemini_imagen_1765116463.png
```

## 能力信息

```python
capabilities = generator.get_capabilities()
```

返回值包含:
- 提供商信息
- 支持的宽高比列表
- 最大图像数量
- 安全过滤级别
- 定价信息

## 批量生成

```python
# 批量生成多张图像
image_paths = await generator.generate_image_batch(
    prompts=[
        "A mountain landscape",
        "A city skyline",
        "A forest scene"
    ],
    aspect_ratio="16:9"
)
```

## 环境配置

需要在 `.env` 或环境变量中设置:

```bash
GOOGLE_API_KEY=your_api_key_here
```

## 依赖项

```bash
pip install google-genai
```

## 注意事项

1. **API限制**: 根据Google AI定价，每次生成都会产生费用
2. **生成时间**: 每张图像生成约需 10-30 秒
3. **文件大小**: 生成的PNG文件约 0.8-1.5 MB
4. **错误处理**: 包含完整的异常捕获和日志记录

## 下一步

- [ ] 探索 Imagen 4.0 系列模型 (imagen-4.0-fast-generate-001 等)
- [ ] 测试更多风格和场景
- [ ] 优化批量生成性能
- [ ] 添加图像质量评估

## 相关文件

- 生成器实现: `app/services/image/google_imagen_generator.py`
- 适配器: `app/services/image/generator.py`
- 测试脚本: `test_imagen_quick.py`, `test_imagen_generation.py`
- 输出目录: `./outputs/images/`
