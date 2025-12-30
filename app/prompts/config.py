"""
提示词系统配置管理
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .base import ContextType

@dataclass
class PromptConfig:
    """提示词配置"""
    name: str
    template: str
    variables: Dict[str, Any] = field(default_factory=dict)
    cache_duration: Optional[int] = None  # 缓存时长（秒）
    max_retries: Optional[int] = None
    validators: List[str] = field(default_factory=list)
    fallback: Optional[str] = None
    description: str = ""

@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    components: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

@dataclass
class ComponentConfig:
    """组件配置"""
    name: str
    type: str  # template, dynamic, conditional, composite
    config: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

@dataclass
class PromptSystemConfig:
    """提示词系统配置"""
    version: str = "1.0.0"
    default_context_type: str = "video"
    cache_enabled: bool = True
    default_cache_duration: int = 3600  # 1小时
    max_retries: int = 3
    retry_delay: float = 1.0
    templates: Dict[str, PromptConfig] = field(default_factory=dict)
    strategies: Dict[str, StrategyConfig] = field(default_factory=dict)
    components: Dict[str, ComponentConfig] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "prompts_config.yaml"
        self.config = PromptSystemConfig()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self._parse_config(data)
        else:
            self._create_default_config()
    
    def _parse_config(self, data: Dict[str, Any]):
        """解析配置数据"""
        # 基本配置
        self.config.version = data.get('version', '1.0.0')
        self.config.default_context_type = data.get('default_context_type', 'video')
        self.config.cache_enabled = data.get('cache_enabled', True)
        self.config.default_cache_duration = data.get('default_cache_duration', 3600)
        self.config.max_retries = data.get('max_retries', 3)
        self.config.retry_delay = data.get('retry_delay', 1.0)
        
        # 全局变量
        self.config.global_variables = data.get('global_variables', {})
        
        # 模板配置
        templates_data = data.get('templates', {})
        for name, template_data in templates_data.items():
            self.config.templates[name] = PromptConfig(
                name=name,
                template=template_data.get('template', ''),
                variables=template_data.get('variables', {}),
                cache_duration=template_data.get('cache_duration'),
                max_retries=template_data.get('max_retries'),
                validators=template_data.get('validators', []),
                fallback=template_data.get('fallback'),
                description=template_data.get('description', '')
            )
        
        # 策略配置
        strategies_data = data.get('strategies', {})
        for name, strategy_data in strategies_data.items():
            self.config.strategies[name] = StrategyConfig(
                name=name,
                components=strategy_data.get('components', []),
                variables=strategy_data.get('variables', {}),
                description=strategy_data.get('description', '')
            )
        
        # 组件配置
        components_data = data.get('components', {})
        for name, component_data in components_data.items():
            self.config.components[name] = ComponentConfig(
                name=name,
                type=component_data.get('type', 'template'),
                config=component_data.get('config', {}),
                description=component_data.get('description', '')
            )
    
    def _create_default_config(self):
        """创建默认配置"""
        default_config = {
            'version': '1.0.0',
            'default_context_type': 'video',
            'cache_enabled': True,
            'default_cache_duration': 3600,
            'max_retries': 3,
            'retry_delay': 1.0,
            'global_variables': {
                'default_language': 'zh-CN',
                'default_style': 'professional'
            },
            'templates': {
                'video_analysis': {
                    'template': '请分析视频：{{ title }}',
                    'description': '视频分析模板',
                    'cache_duration': 1800
                },
                'image_generation': {
                    'template': '生成图像：{{ description }}',
                    'description': '图像生成模板',
                    'max_retries': 2
                }
            },
            'strategies': {
                'video_analysis': {
                    'components': ['system_role', 'video_info', 'analysis_task'],
                    'description': '视频分析策略'
                },
                'edit_instruction': {
                    'components': ['editor_role', 'video_context', 'user_instruction'],
                    'description': '编辑指令理解策略'
                }
            },
            'components': {
                'system_role': {
                    'type': 'template',
                    'config': {
                        'template': '你是一个专业的{{ role }}，具备以下能力：\n{{ capabilities }}'
                    },
                    'description': '系统角色组件'
                }
            }
        }
        
        self._parse_config(default_config)
        self.save_config()
    
    def save_config(self):
        """保存配置到文件"""
        config_data = {
            'version': self.config.version,
            'default_context_type': self.config.default_context_type,
            'cache_enabled': self.config.cache_enabled,
            'default_cache_duration': self.config.default_cache_duration,
            'max_retries': self.config.max_retries,
            'retry_delay': self.config.retry_delay,
            'global_variables': self.config.global_variables,
            'templates': {
                name: {
                    'template': template.template,
                    'variables': template.variables,
                    'cache_duration': template.cache_duration,
                    'max_retries': template.max_retries,
                    'validators': template.validators,
                    'fallback': template.fallback,
                    'description': template.description
                }
                for name, template in self.config.templates.items()
            },
            'strategies': {
                name: {
                    'components': strategy.components,
                    'variables': strategy.variables,
                    'description': strategy.description
                }
                for name, strategy in self.config.strategies.items()
            },
            'components': {
                name: {
                    'type': component.type,
                    'config': component.config,
                    'description': component.description
                }
                for name, component in self.config.components.items()
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    
    def get_template_config(self, name: str) -> Optional[PromptConfig]:
        """获取模板配置"""
        return self.config.templates.get(name)
    
    def get_strategy_config(self, name: str) -> Optional[StrategyConfig]:
        """获取策略配置"""
        return self.config.strategies.get(name)
    
    def get_component_config(self, name: str) -> Optional[ComponentConfig]:
        """获取组件配置"""
        return self.config.components.get(name)
    
    def add_template(self, name: str, template: str, **kwargs):
        """添加模板配置"""
        self.config.templates[name] = PromptConfig(
            name=name,
            template=template,
            **kwargs
        )
        self.save_config()
    
    def add_strategy(self, name: str, components: List[str], **kwargs):
        """添加策略配置"""
        self.config.strategies[name] = StrategyConfig(
            name=name,
            components=components,
            **kwargs
        )
        self.save_config()
    
    def add_component(self, name: str, component_type: str, config: Dict[str, Any], **kwargs):
        """添加组件配置"""
        self.config.components[name] = ComponentConfig(
            name=name,
            type=component_type,
            config=config,
            **kwargs
        )
        self.save_config()
    
    def set_global_variable(self, name: str, value: Any):
        """设置全局变量"""
        self.config.global_variables[name] = value
        self.save_config()
    
    def get_global_variable(self, name: str, default: Any = None) -> Any:
        """获取全局变量"""
        return self.config.global_variables.get(name, default)
    
    def validate_config(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 检查模板配置
        for name, template in self.config.templates.items():
            if not template.template:
                errors.append(f"Template '{name}' has empty template")
        
        # 检查策略配置
        for name, strategy in self.config.strategies.items():
            if not strategy.components:
                errors.append(f"Strategy '{name}' has no components")
        
        # 检查组件配置
        for name, component in self.config.components.items():
            if not component.type:
                errors.append(f"Component '{name}' has no type")
        
        return errors

# 全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config() -> PromptSystemConfig:
    """获取配置"""
    return config_manager.config

def get_template_config(name: str) -> Optional[PromptConfig]:
    """获取模板配置"""
    return config_manager.get_template_config(name)

def get_strategy_config(name: str) -> Optional[StrategyConfig]:
    """获取策略配置"""
    return config_manager.get_strategy_config(name)

def add_template(name: str, template: str, **kwargs):
    """添加模板"""
    config_manager.add_template(name, template, **kwargs)

def add_strategy(name: str, components: List[str], **kwargs):
    """添加策略"""
    config_manager.add_strategy(name, components, **kwargs)

def set_global_variable(name: str, value: Any):
    """设置全局变量"""
    config_manager.set_global_variable(name, value)

def get_global_variable(name: str, default: Any = None) -> Any:
    """获取全局变量"""
    return config_manager.get_global_variable(name, default) 