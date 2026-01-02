# Prompt 管理系统使用指南

## 🎯 系统概述

项目已有完善的 Prompt 管理系统，使用 **Jinja2** 作为模板引擎，支持集中管理所有 AI prompts。

### 核心位置
```
app/prompts/
├── base.py                  # 核心：PromptTemplate, PromptManager
├── video_analysis.py        # 视频分析
├── image_generation.py      # 图像生成
├── llm_analysis.py          # LLM分析
├── video_generation.py      # 视频生成
├── tts.py                   # 语音合成
└── system.py                # 系统prompts
```

---

## 🚀 快速开始

### 1. 注册新 Prompt

```python
from app.prompts import register_prompt, render_prompt

# 注册prompt模板
register_prompt(
    name="youtube_description",
    template="""
为以下视频生成YouTube描述：

标题: {{ title }}
时长: {{ duration }}秒
风格: {{ style }}

要求：
- 吸引人的开头
- 包含关键词: {{ keywords }}
- 添加社交媒体链接
- 呼吁订阅

描述：
    """
)

# 使用prompt
description = render_prompt(
    "youtube_description",
    title="AI视频生成教程",
    duration=300,
    style="专业",
    keywords="AI, 视频, 教程"
)
```

### 2. 使用现有 Prompt

```python
from app.prompts import prompt_manager

# 获取模板
template = prompt_manager.get_template("video_analysis")

# 渲染
result = template.render(
    video_path="/path/to/video.mp4",
    analysis_type="content"
)
```

---

## 📚 现有 Prompt 模块

### 1. 视频分析 (video_analysis.py)

```python
from app.prompts.video_analysis import VIDEO_ANALYSIS_PROMPT

# 分析视频内容
prompt = VIDEO_ANALYSIS_PROMPT.format(
    transcription=transcript_text,
    focus="主题和关键点"
)
```

### 2. 图像生成 (image_generation.py)

```python
from app.prompts.image_generation import IMAGE_GENERATION_PROMPT

# 生成图像prompt
prompt = IMAGE_GENERATION_PROMPT.format(
    description="夕阳下的海滩",
    style="photorealistic",
    aspect_ratio="16:9"
)
```

### 3. LLM分析 (llm_analysis.py)

```python
from app.prompts.llm_analysis import CONTENT_ANALYSIS_PROMPT

# 内容分析
prompt = CONTENT_ANALYSIS_PROMPT.format(
    content=script_content,
    analysis_depth="detailed"
)
```

---

## 🎨 最佳实践

### 1. 模块化组织

按功能域划分 prompt 文件：

```python
# app/prompts/youtube_upload.py
"""YouTube上传相关prompts"""

VIDEO_TITLE_OPTIMIZATION = """
优化以下视频标题以提高YouTube SEO：

原标题: {{ original_title }}
主题: {{ topic }}
目标关键词: {{ keywords }}

优化要求：
- 长度: 60-70字符
- 包含主要关键词
- 吸引点击
- 准确描述内容

优化后的标题：
"""

VIDEO_DESCRIPTION_TEMPLATE = """
为YouTube视频生成完整描述：

【视频信息】
标题: {{ title }}
时长: {{ duration }}
主题: {{ topic }}

【内容大纲】
{{ content_outline }}

【生成要求】
1. 开头：吸引人的介绍（2-3句）
2. 内容：详细的视频内容说明
3. 时间戳：关键章节的时间点
4. 标签：5-10个相关标签
5. 链接：社交媒体和相关资源
6. 结尾：订阅呼吁

描述内容：
"""

# 注册prompts
from app.prompts import register_prompt

register_prompt("youtube_title_optimization", VIDEO_TITLE_OPTIMIZATION)
register_prompt("youtube_description", VIDEO_DESCRIPTION_TEMPLATE)
```

### 2. 使用变量验证

```python
from app.prompts.base import PromptTemplate

class ValidatedPromptTemplate(PromptTemplate):
    """带验证的Prompt模板"""

    def render(self, **kwargs) -> str:
        # 验证必需参数
        required = ['title', 'duration']
        missing = [k for k in required if k not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # 验证数据类型
        if not isinstance(kwargs.get('duration'), (int, float)):
            raise TypeError("duration must be a number")

        return super().render(**kwargs)
```

### 3. 分层结构

```python
# 基础prompt
BASE_ANALYSIS_PROMPT = """
分析以下内容：

{{ content }}

要求：
{{ requirements }}
"""

# 特定领域prompt（继承基础）
VIDEO_SCRIPT_ANALYSIS_PROMPT = BASE_ANALYSIS_PROMPT + """

【脚本分析】
请特别关注：
1. 故事结构
2. 节奏控制
3. 情感曲线
4. 视觉化建议
"""
```

### 4. 多语言支持

```python
# app/prompts/multilingual.py
PROMPTS = {
    'zh': {
        'greeting': '你好，{{ name }}！',
        'analysis': '请分析以下内容：\n{{ content }}'
    },
    'en': {
        'greeting': 'Hello, {{ name }}!',
        'analysis': 'Please analyze the following content:\n{{ content }}'
    }
}

def get_prompt(key: str, lang: str = 'zh', **kwargs) -> str:
    template = PROMPTS[lang][key]
    return Template(template).render(**kwargs)
```

---

## 🔧 添加新功能的 Prompts

### YouTube 上传优化

创建 `app/prompts/youtube.py`:

```python
"""YouTube相关Prompt模板"""
from app.prompts import register_prompt

# 标题优化
TITLE_OPTIMIZATION = """
优化YouTube视频标题以提高SEO和点击率。

【原标题】
{{ original_title }}

【视频信息】
- 主题: {{ topic }}
- 时长: {{ duration }}秒
- 目标受众: {{ audience }}

【关键词】
{{ keywords }}

【优化要求】
1. 长度: 60-70字符（避免被截断）
2. 前5个词最重要（搜索权重高）
3. 包含主要关键词
4. 数字和括号吸引眼球
5. 避免标题党，准确描述内容

【示例格式】
- "如何使用AI生成视频 | 完整教程 (2024最新)"
- "5分钟学会Python爬虫 - 零基础入门指南"
- "iPhone 15 Pro深度评测 - 值不值得买？"

请生成3个优化标题选项：
"""

# 描述生成
DESCRIPTION_GENERATION = """
为YouTube视频生成完整的描述内容。

【视频信息】
标题: {{ title }}
时长: {{ duration }}秒
主题: {{ topic }}

【脚本内容】
{{ script }}

【生成要求】

## 第一部分：简介（前3行）
- 用2-3句话概括视频内容
- 包含主要关键词
- 吸引观众继续阅读

## 第二部分：内容大纲
- 列出视频的主要章节
- 包含时间戳（如果可能）
- 格式：00:00 - 介绍

## 第三部分：详细说明
- 详细描述视频内容
- 提供额外的背景信息
- 回答可能的观众疑问

## 第四部分：标签和关键词
用逗号分隔的标签列表，5-10个

## 第五部分：链接
- 相关视频链接
- 社交媒体账号
- 外部资源（如有）

## 第六部分：呼吁行动
- 订阅频道
- 点赞和评论
- 开启小铃铛

请生成描述：
"""

# 标签生成
TAGS_GENERATION = """
为YouTube视频生成SEO优化的标签。

【视频信息】
标题: {{ title }}
描述: {{ description }}
主题: {{ topic }}

【标签策略】
1. 主要标签（3-5个）：最核心的关键词
2. 次要标签（5-10个）：相关主题
3. 长尾标签（5-10个）：更具体的短语

【标签类型】
- 品牌标签（频道名等）
- 内容标签（视频主题）
- 类别标签（领域分类）
- 长尾标签（具体查询）

【注意事项】
- 总数不超过500字符
- 优先使用搜索量大的词
- 包含同义词和相关词
- 混合使用中英文（如适用）

请生成标签列表（逗号分隔）：
"""

# 注册所有prompts
register_prompt("youtube_title_optimization", TITLE_OPTIMIZATION)
register_prompt("youtube_description", DESCRIPTION_GENERATION)
register_prompt("youtube_tags", TAGS_GENERATION)
```

### 使用示例

```python
from app.prompts import render_prompt

# 优化标题
optimized_titles = render_prompt(
    "youtube_title_optimization",
    original_title="AI视频教程",
    topic="人工智能视频生成",
    duration=300,
    audience="技术爱好者",
    keywords="AI, 视频生成, 教程, 机器学习"
)

# 生成描述
description = render_prompt(
    "youtube_description",
    title="5分钟学会AI视频生成",
    duration=300,
    topic="AI视频生成入门",
    script=video_script
)

# 生成标签
tags = render_prompt(
    "youtube_tags",
    title="5分钟学会AI视频生成",
    description=description,
    topic="AI视频生成"
)
```

---

## 📊 Prompt 版本管理

### 1. 版本化 Prompts

```python
# app/prompts/versioned.py
from typing import Dict
from app.prompts import PromptTemplate

class VersionedPromptTemplate:
    """支持版本管理的Prompt模板"""

    def __init__(self):
        self.versions: Dict[str, PromptTemplate] = {}
        self.current_version = "v1"

    def add_version(self, version: str, template: str):
        self.versions[version] = PromptTemplate(template)

    def render(self, version: str = None, **kwargs) -> str:
        v = version or self.current_version
        if v not in self.versions:
            raise ValueError(f"Version {v} not found")
        return self.versions[v].render(**kwargs)

# 使用示例
video_analysis = VersionedPromptTemplate()

video_analysis.add_version("v1", """
简单分析: {{ content }}
""")

video_analysis.add_version("v2", """
详细分析以下内容：

{{ content }}

请提供：
1. 主题
2. 关键点
3. 建议
""")

# 使用最新版本
result = video_analysis.render(content="...")

# 使用特定版本
result_v1 = video_analysis.render(version="v1", content="...")
```

### 2. A/B 测试

```python
from app.prompts.base import PromptTemplate
import random

class ABTestingPrompt:
    """支持A/B测试的Prompt"""

    def __init__(self, variant_a: str, variant_b: str):
        self.variant_a = PromptTemplate(variant_a)
        self.variant_b = PromptTemplate(variant_b)
        self.stats = {'a': 0, 'b': 0}

    def render(self, variant: str = None, **kwargs) -> tuple:
        """返回(prompt, variant_used)"""
        if variant is None:
            variant = 'a' if random.random() < 0.5 else 'b'

        self.stats[variant] += 1

        if variant == 'a':
            return self.variant_a.render(**kwargs), 'a'
        else:
            return self.variant_b.render(**kwargs), 'b'
```

---

## 🔍 调试和日志

```python
import logging
from app.prompts.base import PromptTemplate

logger = logging.getLogger(__name__)

class LoggingPromptTemplate(PromptTemplate):
    """带日志的Prompt模板"""

    def render(self, **kwargs) -> str:
        logger.info(f"Rendering prompt with variables: {list(kwargs.keys())}")

        try:
            result = super().render(**kwargs)
            logger.debug(f"Prompt rendered successfully. Length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Failed to render prompt: {e}")
            logger.error(f"Variables: {kwargs}")
            raise
```

---

## 📝 总结

### 当前系统优势
✅ 使用 Jinja2，功能强大
✅ 模块化组织，易于维护
✅ 全局变量支持
✅ 简单易用的API

### 建议改进
1. 添加 YouTube 相关的 prompts 模块
2. 实现 prompt 版本管理
3. 添加常用 prompt 的单元测试
4. 创建 prompt 效果评估机制

### 下一步
1. 创建 `app/prompts/youtube.py`
2. 创建 `app/prompts/video_script.py`
3. 统一现有代码中散落的 prompts
4. 编写 prompt 优化指南

---

**📖 更多信息**: 查看 `app/prompts/README.md` 了解完整的 DDD 架构说明。
