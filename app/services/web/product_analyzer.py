"""
产品信息分析器
使用LLM分析从URL提取的产品信息，生成结构化的产品背景材料
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from app.services.llm.service import LLMService, ProviderType

logger = logging.getLogger(__name__)


class ProductAnalyzer:
    """产品信息分析器"""

    def __init__(self):
        self.llm = LLMService(provider=ProviderType.GOOGLE)

    async def analyze_product(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析产品信息，生成结构化的背景材料

        Args:
            content: 从URL提取的原始内容

        Returns:
            结构化的产品信息
        """
        if not content:
            logger.warning("内容为空，无法分析")
            return {}

        try:
            # 构建分析提示词
            prompt = self._build_analysis_prompt(content)

            # 调用LLM分析
            logger.info("🤖 使用LLM分析产品信息...")
            result = await asyncio.to_thread(
                self.llm.simple_call,
                prompt,
                timeout=20,
                retry_count=1,
            )
            response = result.get("content", "")

            # 解析LLM响应
            product_info = self._parse_llm_response(response)

            logger.info(f"✅ 产品分析完成: {product_info.get('product_name', 'Unknown')}")
            return product_info

        except Exception as e:
            logger.error(f"产品分析失败: {e}")
            return self._fallback_analysis(content)

    def _build_analysis_prompt(self, content: Dict[str, Any]) -> str:
        """构建LLM分析提示词"""
        prompt = """你是一个专业的产品分析师。请分析以下从网页提取的内容，提取关键的产品信息。

# 网页内容

## 标题
{title}

## 描述
{description}

## Open Graph 数据
{og_data}

## 产品信息
{product_info}

## 主要内容（前1000字符）
{main_content}

---

请分析以上内容，提取以下信息（以JSON格式返回）：

```json
{{
  "product_name": "产品名称",
  "product_category": "产品类别（如：智能手机、电动汽车、软件服务等）",
  "brand": "品牌名称",
  "key_features": [
    "核心特性1",
    "核心特性2",
    "核心特性3"
  ],
  "target_audience": "目标用户群体",
  "unique_selling_points": [
    "独特卖点1",
    "独特卖点2"
  ],
  "price_range": "价格区间（如果有）",
  "product_summary": "产品的简短总结（2-3句话）",
  "tone_and_style": "品牌调性（如：科技感、专业、年轻活力等）",
  "visual_style": "视觉风格建议（用于视频生成）"
}}
```

注意：
1. 如果某些信息无法从内容中提取，请填写 "未知" 或留空
2. 重点关注产品的核心价值和差异化特点
3. 提取的信息要准确、简洁
4. 只返回JSON，不要有其他文字
"""

        # 格式化内容
        formatted_prompt = prompt.format(
            title=content.get('title', '无'),
            description=content.get('description', '无'),
            og_data=self._format_og_data(content.get('og_data', {})),
            product_info=self._format_product_info(content.get('product_info', {})),
            main_content=content.get('main_content', '')[:1000]
        )

        return formatted_prompt

    def _format_og_data(self, og_data: Dict[str, str]) -> str:
        """格式化Open Graph数据"""
        if not og_data:
            return "无"

        lines = []
        for key, value in og_data.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _format_product_info(self, product_info: Dict[str, Any]) -> str:
        """格式化产品信息"""
        if not product_info:
            return "无"

        lines = []

        if 'name' in product_info:
            lines.append(f"产品名称: {product_info['name']}")

        if 'prices' in product_info:
            lines.append(f"价格: {', '.join(product_info['prices'])}")

        if 'features' in product_info:
            lines.append("特性:")
            for feature in product_info['features']:
                lines.append(f"  - {feature}")

        if 'specs' in product_info:
            lines.append("规格:")
            for key, value in list(product_info['specs'].items())[:5]:
                lines.append(f"  - {key}: {value}")

        return "\n".join(lines) if lines else "无"

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        import json
        import re

        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                product_info = json.loads(json_str)
                return product_info
            else:
                logger.warning("无法从LLM响应中提取JSON")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}")
            logger.debug(f"LLM响应: {response}")
            return {}

    def _fallback_analysis(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """降级分析（不使用LLM）"""
        logger.info("使用降级分析...")

        product_info = {
            "product_name": content.get('title', '未知产品'),
            "product_summary": content.get('description', ''),
            "source_url": content.get('url', '')
        }

        # 从原始产品信息中提取
        raw_product_info = content.get('product_info', {})

        if 'features' in raw_product_info:
            product_info['key_features'] = raw_product_info['features']

        if 'prices' in raw_product_info:
            product_info['price_range'] = ', '.join(raw_product_info['prices'])

        return product_info

    def create_background_material(self, product_info: Dict[str, Any]) -> str:
        """
        将产品信息转换为背景材料文本

        Args:
            product_info: 结构化的产品信息

        Returns:
            格式化的背景材料文本
        """
        if not product_info:
            return ""

        lines = []

        # 产品名称和类别
        if product_info.get('product_name'):
            lines.append(f"# 产品: {product_info['product_name']}")

        if product_info.get('brand'):
            lines.append(f"品牌: {product_info['brand']}")

        if product_info.get('product_category'):
            lines.append(f"类别: {product_info['product_category']}")

        lines.append("")

        # 产品总结
        if product_info.get('product_summary'):
            lines.append("## 产品概述")
            lines.append(product_info['product_summary'])
            lines.append("")

        # 核心特性
        if product_info.get('key_features'):
            lines.append("## 核心特性")
            for feature in product_info['key_features']:
                lines.append(f"- {feature}")
            lines.append("")

        # 独特卖点
        if product_info.get('unique_selling_points'):
            lines.append("## 独特卖点")
            for usp in product_info['unique_selling_points']:
                lines.append(f"- {usp}")
            lines.append("")

        # 目标用户
        if product_info.get('target_audience'):
            lines.append(f"## 目标用户: {product_info['target_audience']}")
            lines.append("")

        # 价格
        if product_info.get('price_range'):
            lines.append(f"## 价格: {product_info['price_range']}")
            lines.append("")

        # 品牌调性
        if product_info.get('tone_and_style'):
            lines.append(f"## 品牌调性: {product_info['tone_and_style']}")
            lines.append("")

        # 视觉风格
        if product_info.get('visual_style'):
            lines.append(f"## 视觉风格建议: {product_info['visual_style']}")
            lines.append("")

        return "\n".join(lines)


async def test_analyzer():
    """测试产品分析器"""
    print("🧪 测试产品分析器")
    print("=" * 80)

    # 模拟从URL提取的内容
    mock_content = {
        "url": "https://www.apple.com/iphone-15-pro/",
        "title": "iPhone 15 Pro - Apple",
        "description": "iPhone 15 Pro features a titanium design, A17 Pro chip, and advanced camera system.",
        "og_data": {
            "title": "iPhone 15 Pro",
            "description": "The most powerful iPhone ever with titanium design",
            "type": "product"
        },
        "product_info": {
            "name": "iPhone 15 Pro",
            "prices": ["$999", "$1,199"],
            "features": [
                "Titanium design",
                "A17 Pro chip",
                "48MP camera system",
                "Action button",
                "USB-C"
            ]
        },
        "main_content": """
        iPhone 15 Pro. Forged in titanium.

        The most powerful iPhone ever features a titanium design,
        making it the lightest Pro model ever. A17 Pro chip delivers
        incredible performance and efficiency. The advanced camera system
        includes a 48MP main camera with improved low-light performance.

        New Action button replaces the Ring/Silent switch, giving you
        quick access to your favorite features. USB-C connector enables
        faster transfer speeds.
        """
    }

    analyzer = ProductAnalyzer()

    # 分析产品
    product_info = await analyzer.analyze_product(mock_content)

    print("\n📊 分析结果:")
    print("-" * 80)
    import json
    print(json.dumps(product_info, indent=2, ensure_ascii=False))

    # 生成背景材料
    print("\n📝 背景材料:")
    print("-" * 80)
    background = analyzer.create_background_material(product_info)
    print(background)

    print("\n" + "=" * 80)
    print("✅ 测试完成")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_analyzer())
