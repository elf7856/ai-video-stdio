"""
简化版提示词模板系统，使用Jinja2作为模板引擎
"""

from typing import Dict, Any, Optional
from jinja2 import Template

class PromptTemplate:
    """Jinja2模板包装"""
    def __init__(self, template: str, variables: Dict[str, Any] = None):
        self.template = template
        self.variables = variables or {}

    def render(self, **kwargs) -> str:
        all_vars = {**self.variables, **kwargs}
        template = Template(self.template)
        return template.render(**all_vars)

class PromptManager:
    """提示词管理器"""
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.global_variables: Dict[str, Any] = {}

    def register_template(self, name: str, template: str, variables: Dict[str, Any] = None):
        self.templates[name] = PromptTemplate(template, variables)

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        return self.templates.get(name)

    def render(self, template_name: str, **kwargs) -> str:
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        all_vars = {**self.global_variables, **kwargs}
        return template.render(**all_vars)

    def set_global_variable(self, name: str, value: Any):
        self.global_variables[name] = value

    def get_global_variables(self) -> Dict[str, Any]:
        return self.global_variables.copy()

# 全局提示词管理器实例
prompt_manager = PromptManager()

def register_prompt(name: str, template: str, variables: Dict[str, Any] = None):
    prompt_manager.register_template(name, template, variables)

def render_prompt(name: str, **kwargs) -> str:
    return prompt_manager.render(name, **kwargs) 