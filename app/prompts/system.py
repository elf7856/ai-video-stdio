"""
系统级别的提示词模板
"""

from .base import register_prompt

# 错误处理提示词
register_prompt(
    "error_analysis",
    """请分析以下错误信息，并提供解决方案：

错误类型：{{ error_type }}
错误信息：{{ error_message }}
上下文：{{ context }}

请提供：
1. 错误原因分析
2. 解决方案建议
3. 预防措施
4. 相关资源"""
)

# 系统状态检查
register_prompt(
    "system_status_check",
    """请检查以下系统状态信息：

系统组件：{{ components }}
状态信息：{{ status_info }}
性能指标：{{ performance_metrics }}

请分析：
1. 系统健康状态
2. 潜在问题
3. 优化建议
4. 维护建议"""
)

# 配置验证
register_prompt(
    "configuration_validation",
    """请验证以下配置信息：

配置类型：{{ config_type }}
配置内容：{{ config_content }}
验证要求：{{ validation_requirements }}

请检查：
1. 配置完整性
2. 格式正确性
3. 逻辑一致性
4. 安全性检查
5. 最佳实践"""
)

# 日志分析
register_prompt(
    "log_analysis",
    """请分析以下日志信息：

日志级别：{{ log_level }}
日志内容：{{ log_content }}
时间范围：{{ time_range }}

请提供：
1. 关键信息提取
2. 异常模式识别
3. 性能分析
4. 安全风险评估
5. 优化建议"""
)

# 用户反馈处理
register_prompt(
    "user_feedback_processing",
    """请处理以下用户反馈：

反馈内容：{{ feedback_content }}
用户类型：{{ user_type }}
反馈类型：{{ feedback_type }}

请分析：
1. 反馈要点
2. 问题分类
3. 优先级评估
4. 解决方案
5. 改进建议"""
)

# 系统角色定义
register_prompt(
    "system_administrator_role",
    "你是一个专业的系统管理员，擅长系统监控、故障诊断和性能优化。"
)

register_prompt(
    "technical_support_role",
    "你是一个专业的技术支持专家，能够快速诊断和解决技术问题。"
)

register_prompt(
    "quality_assurance_role",
    "你是一个专业的质量保证专家，擅长系统测试和质量控制。"
)

# 通用响应模板
register_prompt(
    "success_response",
    "操作成功完成。{{ additional_info }}"
)

register_prompt(
    "error_response",
    "操作失败：{{ error_message }}。请检查：{{ suggestions }}"
)

register_prompt(
    "processing_response",
    "正在处理中，请稍候...{{ progress_info }}"
)

register_prompt(
    "confirmation_request",
    "请确认以下操作：{{ operation_description }}。是否继续？"
) 