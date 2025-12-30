"""
提示词系统使用示例
展示Jinja2模板的使用方法
"""

from .base import register_prompt, render_prompt

def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 注册模板
    register_prompt(
        "video_analysis",
        """请分析以下视频内容：
        
视频信息：
- 标题: {{ title }}
- 时长: {{ duration }}秒
- 分辨率: {{ resolution }}
- 文件大小: {{ file_size }}字节

请从以下方面进行分析：
1. 内容类型和主题
2. 目标受众
3. 关键场景和元素
4. 适合的标签

请以JSON格式返回结果。"""
    )
    
    # 使用模板
    result = render_prompt("video_analysis", 
                          title="美食制作教程",
                          duration=300.0,
                          resolution="1920x1080",
                          file_size=1024000)
    
    print("生成的提示词:")
    print(result)
    print()

def example_multiple_templates():
    """多模板示例"""
    print("=== 多模板示例 ===")
    
    # 注册多个模板
    register_prompt(
        "system_role",
        "你是一个专业的{{ role_name }}，具备以下能力：\n{% for capability in capabilities %}{{ loop.index }}. {{ capability }}\n{% endfor %}"
    )
    
    register_prompt(
        "task_description",
        """任务描述：
{{ task_name }}

执行步骤：
{% for step in steps %}{{ loop.index }}. {{ step }}
{% endfor %}

{% if output_format %}请以{{ output_format }}格式返回结果。{% endif %}"""
    )
    
    # 使用模板
    role_prompt = render_prompt("system_role",
                               role_name="视频分析师",
                               capabilities=["内容分析", "场景识别", "受众分析", "标签生成"])
    
    task_prompt = render_prompt("task_description",
                               task_name="视频内容分析",
                               steps=["提取关键信息", "分析内容主题", "识别目标受众", "生成标签"],
                               output_format="JSON")
    
    print("系统角色提示词:")
    print(role_prompt)
    print()
    
    print("任务描述提示词:")
    print(task_prompt)
    print()

def example_conditional_content():
    """条件内容示例"""
    print("=== 条件内容示例 ===")
    
    register_prompt(
        "adaptive_analysis",
        """视频分析报告：

基本信息：
- 标题: {{ title }}
- 时长: {{ duration }}秒
- 分辨率: {{ resolution }}

{% if duration > 300 %}
由于视频较长（{{ duration }}秒），建议：
1. 分段分析以提高效率
2. 重点关注关键场景
3. 生成详细的时间轴分析
{% else %}
视频长度适中，可以进行：
1. 整体内容分析
2. 关键元素提取
3. 快速标签生成
{% endif %}

{% if file_size > 1000000 %}
注意：文件较大（{{ file_size }}字节），处理时间可能较长。
{% endif %}

请提供分析结果。"""
    )
    
    # 测试不同条件
    long_video = render_prompt("adaptive_analysis",
                              title="长视频示例",
                              duration=450.0,
                              resolution="1920x1080",
                              file_size=2048000)
    
    short_video = render_prompt("adaptive_analysis",
                               title="短视频示例",
                               duration=120.0,
                               resolution="1280x720",
                               file_size=512000)
    
    print("长视频分析提示词:")
    print(long_video)
    print()
    
    print("短视频分析提示词:")
    print(short_video)
    print()

def run_all_examples():
    """运行所有示例"""
    print("🚀 提示词系统使用示例")
    print("=" * 50)
    
    example_basic_usage()
    example_multiple_templates()
    example_conditional_content()
    
    print("=" * 50)
    print("✅ 所有示例运行完成！")
    print("\n💡 提示：")
    print("1. 使用 register_prompt() 注册模板")
    print("2. 使用 render_prompt() 渲染模板")
    print("3. 支持Jinja2的所有语法特性")
    print("4. 可以嵌套使用模板")

if __name__ == "__main__":
    run_all_examples() 