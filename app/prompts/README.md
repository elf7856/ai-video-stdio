# 高级抽象提示词系统

一个基于领域驱动设计(DDD)和策略模式的高级提示词管理系统，提供强大的抽象表示能力和灵活的扩展性。

## 🎯 核心特性

### 1. **领域驱动设计(DDD)**
- 清晰的领域模型和边界
- 上下文驱动的提示词生成
- 类型安全的变量管理

### 2. **策略模式**
- 可插拔的提示词策略
- 动态策略选择
- 策略组合和扩展

### 3. **组件化架构**
- 可组合的提示词组件
- 装饰器模式支持
- 管道式处理

### 4. **高级功能**
- 智能缓存机制
- 自动重试和回退
- 内容验证
- 上下文感知
- 自适应处理

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PromptEngine  │    │  PromptRegistry │    │  PromptContext  │
│                 │    │                 │    │                 │
│ - 创建提示词    │◄──►│ - 策略注册      │◄──►│ - 上下文数据    │
│ - 缓存管理      │    │ - 组件管理      │    │ - 类型信息      │
│ - 上下文管理    │    │ - 模板管理      │    │ - 元数据        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ PromptStrategy  │    │PromptComponent  │    │ PromptVariable  │
│                 │    │                 │    │                 │
│ - 策略接口      │    │ - 组件基类      │    │ - 变量定义      │
│ - 具体策略      │    │ - 模板组件      │    │ - 验证规则      │
│ - 策略组合      │    │ - 动态组件      │    │ - 类型检查      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 核心组件

### **基础组件**

#### `PromptContext` - 提示词上下文
```python
from app.prompts import PromptContext, ContextType

context = PromptContext(
    context_type=ContextType.VIDEO,
    data={
        "title": "美食制作教程",
        "duration": 300.0,
        "resolution": "1920x1080"
    },
    metadata={
        "user_preferences": "professional",
        "target_audience": "cooking_enthusiasts"
    }
)
```

#### `PromptVariable` - 提示词变量
```python
from app.prompts import PromptVariable

# 基础变量
title_var = PromptVariable(
    name="title",
    value="美食制作教程",
    type="string",
    required=True,
    description="视频标题"
)

# 带验证的变量
def validate_duration(value):
    return isinstance(value, (int, float)) and value > 0

duration_var = PromptVariable(
    name="duration",
    value=300.0,
    type="float",
    required=True,
    validation=validate_duration
)
```

### **高级组件**

#### `CachedComponent` - 缓存组件
```python
from app.prompts.components import CachedComponent
from datetime import timedelta

# 创建带缓存的模板组件
cached_component = CachedComponent(
    "video_analysis",
    base_component,
    cache_duration=timedelta(hours=1)
)
```

#### `ValidatedComponent` - 验证组件
```python
from app.prompts.components import ValidatedComponent

def validate_json(content: str) -> bool:
    try:
        import json
        json.loads(content)
        return True
    except:
        return False

validated_component = ValidatedComponent(
    "json_response",
    base_component,
    validators=[validate_json]
)
```

#### `AdaptiveComponent` - 自适应组件
```python
from app.prompts.components import AdaptiveComponent

# 根据上下文复杂度选择不同的处理策略
adaptive_component = AdaptiveComponent(
    "analysis",
    simple_component,
    complex_component,
    complexity_threshold=100
)
```

## 🎨 策略模式

### **预定义策略**

#### 视频分析策略
```python
from app.prompts import create_prompt

context = PromptContext(
    context_type=ContextType.VIDEO,
    data={
        "title": "旅行vlog",
        "duration": 180.0,
        "resolution": "1920x1080"
    }
)

prompt = create_prompt("video_analysis", context)
```

#### 编辑指令理解策略
```python
context = PromptContext(
    context_type=ContextType.VIDEO,
    data={
        "instruction": "在视频的第30秒处插入爆炸特效",
        "video_context": {...}
    }
)

prompt = create_prompt("edit_instruction", context)
```

### **自定义策略**
```python
from app.prompts.base import PromptStrategy, PromptComponent, CompositeComponent

class CustomAnalysisStrategy(PromptStrategy):
    def get_strategy_name(self) -> str:
        return "custom_analysis"
    
    def create_prompt(self, context: PromptContext) -> PromptComponent:
        composite = CompositeComponent("custom_analysis_prompt")
        
        # 添加自定义组件
        role_component = TemplateComponent(
            "custom_role",
            "你是一个专业的{{ specialty }}分析师"
        )
        
        composite.add_component(role_component)
        return composite

# 注册策略
from app.prompts import register_strategy
register_strategy(CustomAnalysisStrategy())
```

## 🔧 构建器模式

### **组件构建器**
```python
from app.prompts.components import ComponentBuilder
from datetime import timedelta

builder = ComponentBuilder("video_processor")

# 添加模板组件
builder.add_template(
    "你是一个专业的视频处理专家，擅长：\n"
    "1. 视频剪辑和合成\n"
    "2. 特效添加和调整\n"
    "3. 音频同步和优化"
)

# 添加动态组件
def generate_requirements(context: PromptContext) -> str:
    duration = context.get_data("duration", 0)
    if duration > 300:
        return "由于视频较长，建议分段处理。"
    return "视频长度适中，可以直接处理。"

builder.add_dynamic(generate_requirements)

# 启用高级功能
builder.with_caching(timedelta(hours=2))
builder.with_retry(3)

# 构建组件
component = builder.build()
```

### **模板工厂**
```python
from app.prompts.components import TemplateFactory

# 创建系统角色模板
capabilities = [
    "深度理解视频内容",
    "识别关键场景和元素",
    "分析目标受众"
]
role_component = TemplateFactory.create_system_role("视频分析师", capabilities)

# 创建数据展示模板
data_fields = {
    "title": "标题",
    "duration": "时长",
    "resolution": "分辨率"
}
data_component = TemplateFactory.create_data_display(data_fields)

# 创建任务描述模板
task_steps = [
    "分析视频内容和主题",
    "识别关键场景和元素",
    "生成标签和摘要"
]
task_component = TemplateFactory.create_task_description(task_steps, "JSON格式")
```

## ⚙️ 配置管理

### **YAML配置文件**
```yaml
version: "1.0.0"
default_context_type: "video"
cache_enabled: true
default_cache_duration: 3600
max_retries: 3

global_variables:
  default_language: "zh-CN"
  default_style: "professional"

templates:
  video_analysis:
    template: "请分析视频：{{ title }}"
    description: "视频分析模板"
    cache_duration: 1800
    max_retries: 2

strategies:
  video_analysis:
    components: ["system_role", "video_info", "analysis_task"]
    description: "视频分析策略"

components:
  system_role:
    type: "template"
    config:
      template: "你是一个专业的{{ role }}，具备以下能力：\n{{ capabilities }}"
    description: "系统角色组件"
```

### **配置管理API**
```python
from app.prompts.config import (
    add_template, add_strategy, set_global_variable,
    get_template_config, get_strategy_config
)

# 添加模板
add_template(
    "custom_template",
    "自定义模板：{{ variable }}",
    cache_duration=1800,
    description="自定义模板"
)

# 添加策略
add_strategy(
    "custom_strategy",
    ["component1", "component2"],
    description="自定义策略"
)

# 设置全局变量
set_global_variable("api_version", "v2.0")
```

## 🚀 使用示例

### **基础使用**
```python
from app.prompts import PromptContext, ContextType, create_prompt

# 创建上下文
context = PromptContext(
    context_type=ContextType.VIDEO,
    data={
        "title": "美食制作教程",
        "duration": 300.0,
        "resolution": "1920x1080"
    }
)

# 使用策略生成提示词
prompt = create_prompt("video_analysis", context)
print(prompt)
```

### **组合使用**
```python
from app.prompts import create_composite_prompt

# 使用多个组件创建提示词
component_names = ["system_role", "video_info", "analysis_task"]
prompt = create_composite_prompt(component_names, context)
```

### **高级功能**
```python
from app.prompts.components import (
    create_cached_template, create_validated_template,
    create_adaptive_template
)

# 创建带缓存的模板
cached_template = create_cached_template(
    "video_info",
    "视频信息：{{ title }}",
    timedelta(hours=1)
)

# 创建带验证的模板
def validate_json(content: str) -> bool:
    try:
        import json
        json.loads(content)
        return True
    except:
        return False

validated_template = create_validated_template(
    "json_response",
    "请返回JSON格式：{\"status\": \"success\"}",
    [validate_json]
)

# 创建自适应模板
adaptive_template = create_adaptive_template(
    "analysis",
    "简单分析：{{ description }}",
    "详细分析：\n1. 内容：{{ description }}\n2. 技术：{{ technical }}\n3. 建议：{{ suggestions }}",
    complexity_threshold=50
)
```

## 🔍 调试和监控

### **组件验证**
```python
from app.prompts.base import PromptComponent

# 验证组件变量
errors = component.validate_variables()
if errors:
    print("验证错误:", errors)
```

### **配置验证**
```python
from app.prompts.config import config_manager

# 验证配置
errors = config_manager.validate_config()
if errors:
    print("配置错误:", errors)
```

### **缓存管理**
```python
from app.prompts.components import CachedComponent

# 清除缓存
cached_component.clear_cache()

# 检查缓存状态
cache_info = cached_component._cache
```

## 📈 性能优化

### **缓存策略**
- 基于内容哈希的智能缓存
- 可配置的缓存时长
- 自动缓存失效

### **重试机制**
- 可配置的重试次数
- 指数退避策略
- 错误分类处理

### **自适应处理**
- 基于复杂度的策略选择
- 动态资源分配
- 性能监控

## 🔧 扩展开发

### **添加新组件类型**
```python
from app.prompts.base import PromptComponent

class CustomComponent(PromptComponent):
    def __init__(self, name: str, custom_param: str):
        super().__init__(name)
        self.custom_param = custom_param
    
    def render(self, context: PromptContext) -> str:
        # 自定义渲染逻辑
        return f"自定义组件：{self.custom_param}"
```

### **添加新策略**
```python
from app.prompts.base import PromptStrategy

class CustomStrategy(PromptStrategy):
    def get_strategy_name(self) -> str:
        return "custom_strategy"
    
    def create_prompt(self, context: PromptContext) -> PromptComponent:
        # 自定义策略逻辑
        return custom_component
```

### **添加新验证器**
```python
def custom_validator(content: str) -> bool:
    # 自定义验证逻辑
    return "required_keyword" in content

validated_component = ValidatedComponent(
    "custom_validated",
    base_component,
    validators=[custom_validator]
)
```

## 🎯 最佳实践

### **1. 上下文设计**
- 明确定义上下文类型
- 合理组织数据结构
- 避免过度复杂化

### **2. 组件设计**
- 单一职责原则
- 可复用性优先
- 清晰的接口定义

### **3. 策略设计**
- 策略职责明确
- 避免策略间耦合
- 支持策略组合

### **4. 性能考虑**
- 合理使用缓存
- 避免重复计算
- 监控资源使用

### **5. 错误处理**
- 优雅的错误处理
- 有意义的错误信息
- 适当的回退机制

## 🔮 未来规划

- [ ] 支持更多AI模型
- [ ] 增加机器学习优化
- [ ] 提供可视化配置界面
- [ ] 支持分布式部署
- [ ] 增加更多预设策略
- [ ] 提供性能分析工具

---

这个高级抽象提示词系统为视频创作平台提供了强大、灵活、可扩展的提示词管理能力，支持复杂的业务场景和未来的功能扩展。 