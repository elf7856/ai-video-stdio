#!/usr/bin/env python3
"""
Prompt 分析辅助脚本

用于扫描和分析 app/prompts/ 目录中的所有 prompts
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def extract_prompts_from_file(file_path: Path) -> List[Dict]:
    """从 Python 文件中提取所有 register_prompt 调用"""
    prompts = []

    try:
        content = file_path.read_text(encoding='utf-8')

        # 匹配 register_prompt 调用
        pattern = r'register_prompt\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\'"]{3}([^"\']+)["\'"]{3}\s*\)'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            prompt_name = match.group(1)
            prompt_content = match.group(2)

            # 提取变量
            variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', prompt_content)

            prompts.append({
                'name': prompt_name,
                'content': prompt_content.strip(),
                'variables': list(set(variables)),
                'file': file_path.name,
                'length': len(prompt_content.strip())
            })

    except Exception as e:
        print(f"错误: 无法读取 {file_path}: {e}", file=sys.stderr)

    return prompts


def analyze_prompt_quality(prompt: Dict) -> Tuple[int, List[str], List[str]]:
    """
    分析单个 prompt 的质量

    返回: (评分, 优点列表, 改进建议列表)
    """
    score = 10
    strengths = []
    improvements = []

    content = prompt['content']

    # 检查是否有结构化输出
    if 'json' in content.lower() or '{' in content:
        strengths.append("包含结构化输出格式")
    else:
        improvements.append("建议添加结构化输出格式（如 JSON）")
        score -= 2

    # 检查是否有约束条件
    if '要求' in content or '请提供' in content or '请检查' in content:
        strengths.append("包含明确的约束条件")
    else:
        improvements.append("建议添加明确的约束条件和输出要求")
        score -= 1

    # 检查是否有示例
    if '示例' in content or 'example' in content.lower():
        strengths.append("包含示例说明")
    else:
        improvements.append("考虑添加 few-shot examples 提升效果")
        score -= 1

    # 检查长度
    if prompt['length'] < 50:
        improvements.append("Prompt 过于简短，可能缺少必要信息")
        score -= 2
    elif prompt['length'] > 1000:
        improvements.append("Prompt 可能过长，考虑简化或模块化")
        score -= 1
    else:
        strengths.append("长度适中")

    # 检查变量使用
    if prompt['variables']:
        strengths.append(f"使用了 {len(prompt['variables'])} 个变量")
    else:
        improvements.append("没有使用变量，考虑增加灵活性")
        score -= 1

    # 检查是否有角色定义
    if '你是' in content or '作为' in content:
        strengths.append("包含角色定义")

    return max(1, min(10, score)), strengths, improvements


def print_prompt_analysis(prompt: Dict, score: int, strengths: List[str], improvements: List[str]):
    """打印单个 prompt 的分析结果"""
    print(f"\n{'='*80}")
    print(f"Prompt: {prompt['name']}")
    print(f"文件: {prompt['file']}")
    print(f"质量评分: {score}/10")
    print(f"长度: {prompt['length']} 字符")
    print(f"变量: {', '.join(prompt['variables']) if prompt['variables'] else '无'}")

    if strengths:
        print(f"\n✅ 优点:")
        for s in strengths:
            print(f"  - {s}")

    if improvements:
        print(f"\n🔧 改进建议:")
        for i in improvements:
            print(f"  - {i}")

    print(f"\n内容预览:")
    preview = prompt['content'][:200]
    print(f"  {preview}{'...' if len(prompt['content']) > 200 else ''}")


def main():
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    prompts_dir = project_root / "app" / "prompts"

    if not prompts_dir.exists():
        print(f"错误: 找不到 prompts 目录: {prompts_dir}", file=sys.stderr)
        sys.exit(1)

    # 如果指定了 prompt 名称，只分析该 prompt
    target_prompt = sys.argv[1] if len(sys.argv) > 1 else None

    # 扫描所有 Python 文件
    all_prompts = []
    for py_file in prompts_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        prompts = extract_prompts_from_file(py_file)
        all_prompts.extend(prompts)

    if not all_prompts:
        print("未找到任何 prompts")
        return

    # 过滤目标 prompt
    if target_prompt:
        all_prompts = [p for p in all_prompts if p['name'] == target_prompt]
        if not all_prompts:
            print(f"错误: 找不到 prompt '{target_prompt}'", file=sys.stderr)
            sys.exit(1)

    # 分析每个 prompt
    total_score = 0
    for prompt in all_prompts:
        score, strengths, improvements = analyze_prompt_quality(prompt)
        total_score += score
        print_prompt_analysis(prompt, score, strengths, improvements)

    # 总结
    print(f"\n{'='*80}")
    print(f"总结:")
    print(f"  - 总计 prompts: {len(all_prompts)}")
    print(f"  - 平均评分: {total_score / len(all_prompts):.1f}/10")

    # 分类统计
    excellent = sum(1 for p in all_prompts if analyze_prompt_quality(p)[0] >= 9)
    good = sum(1 for p in all_prompts if 7 <= analyze_prompt_quality(p)[0] < 9)
    needs_improvement = sum(1 for p in all_prompts if analyze_prompt_quality(p)[0] < 7)

    print(f"  - 优秀 (9-10分): {excellent}")
    print(f"  - 良好 (7-8分): {good}")
    print(f"  - 需要改进 (<7分): {needs_improvement}")


if __name__ == "__main__":
    main()
