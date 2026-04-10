"""
网页内容提取器
从URL提取图片、文本等内容
支持单页提取和全站爬取
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class WebContentExtractor:
    """网页内容提取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.visited_urls: Set[str] = set()  # 已访问的URL
        self.max_pages = 50  # 最多爬取页面数
        self.max_depth = 3  # 最大爬取深度

    async def extract_images_from_url(
        self,
        url: str,
        max_images: int = 10,
        min_size: int = 200  # 最小尺寸（像素）
    ) -> List[Dict[str, str]]:
        """
        从URL提取图片

        Args:
            url: 网页URL
            max_images: 最多提取多少张图片
            min_size: 最小图片尺寸（宽或高）

        Returns:
            图片列表，每个包含 url 和 alt 字段
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"获取网页失败: {response.status}")
                        return []

                    html = await response.text()

                    # 提取图片URL
                    images = self._extract_image_urls(html, url)

                    # 过滤和排序
                    filtered_images = await self._filter_images(
                        images,
                        session,
                        min_size=min_size
                    )

                    return filtered_images[:max_images]

        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            return []

    def _extract_image_urls(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """从HTML中提取图片URL"""
        images = []

        # 匹配 <img> 标签
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
        matches = re.finditer(img_pattern, html, re.IGNORECASE)

        for match in matches:
            img_url = match.group(1)
            alt_text = match.group(2) if match.group(2) else ""

            # 转换为绝对URL
            absolute_url = urljoin(base_url, img_url)

            # 过滤掉明显的小图标、logo等
            if self._is_valid_image_url(absolute_url):
                images.append({
                    "url": absolute_url,
                    "alt": alt_text
                })

        # 也尝试匹配 Open Graph 图片
        og_pattern = r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'
        og_matches = re.finditer(og_pattern, html, re.IGNORECASE)

        for match in og_matches:
            og_url = urljoin(base_url, match.group(1))
            if self._is_valid_image_url(og_url):
                images.insert(0, {  # OG图片优先级高
                    "url": og_url,
                    "alt": "Open Graph Image"
                })

        return images

    def _is_valid_image_url(self, url: str) -> bool:
        """检查是否是有效的图片URL"""
        # 过滤掉明显的小图标
        invalid_patterns = [
            'icon', 'logo', 'avatar', 'favicon',
            'sprite', 'button', 'badge', 'banner',
            '1x1', 'pixel', 'tracking'
        ]

        url_lower = url.lower()

        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False

        # 检查是否是图片格式
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        parsed = urlparse(url)
        path = parsed.path.lower()

        # 如果有明确的图片扩展名，认为有效
        if any(path.endswith(ext) for ext in valid_extensions):
            return True

        # 如果URL包含图片相关关键词，也认为可能有效
        if any(keyword in url_lower for keyword in ['image', 'img', 'photo', 'picture']):
            return True

        return False

    async def _filter_images(
        self,
        images: List[Dict[str, str]],
        session: aiohttp.ClientSession,
        min_size: int = 200
    ) -> List[Dict[str, str]]:
        """
        过滤图片（检查尺寸等）

        注意：这个方法会发起HEAD请求检查图片，可能比较慢
        为了性能，可以选择跳过尺寸检查
        """
        filtered = []

        for img in images:
            try:
                # 发起HEAD请求检查图片
                async with session.head(img["url"], headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')

                        # 检查是否是图片
                        if 'image' in content_type:
                            # 简单检查：如果Content-Length太小，可能是小图标
                            content_length = response.headers.get('Content-Length')
                            if content_length:
                                size_kb = int(content_length) / 1024
                                if size_kb < 10:  # 小于10KB，可能是小图标
                                    continue

                            filtered.append(img)

            except Exception as e:
                logger.debug(f"检查图片失败 {img['url']}: {e}")
                # 即使检查失败，也保留图片
                filtered.append(img)

        return filtered

    async def download_image(
        self,
        image_url: str,
        output_path: str
    ) -> bool:
        """
        下载图片到本地

        Args:
            image_url: 图片URL
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, headers=self.headers, timeout=30) as response:
                    if response.status == 200:
                        # 确保目录存在
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                        # 写入文件
                        with open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)

                        logger.info(f"✅ 图片下载成功: {output_path}")
                        return True
                    else:
                        logger.error(f"下载图片失败: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"下载图片异常: {e}")
            return False

    async def extract_content_from_url(
        self,
        url: str,
        max_images: int = 10
    ) -> Dict[str, Any]:
        """
        从URL提取完整内容（图片+文本）

        Args:
            url: 网页URL
            max_images: 最多提取多少张图片

        Returns:
            包含图片、标题、描述、正文等信息的字典
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"获取网页失败: {response.status}")
                        return {}

                    html = await response.text()

                    # 使用BeautifulSoup解析HTML
                    soup = BeautifulSoup(html, 'html.parser')

                    # 提取各种内容
                    content = {
                        "url": url,
                        "title": self._extract_title(soup),
                        "description": self._extract_description(soup),
                        "og_data": self._extract_og_data(soup),
                        "main_content": self._extract_main_content(soup),
                        "product_info": self._extract_product_info(soup),
                        "images": await self.extract_images_from_url(url, max_images)
                    }

                    logger.info(f"✅ 成功提取内容: {content['title']}")
                    return content

        except Exception as e:
            logger.error(f"提取内容失败: {e}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        # 优先使用 og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']

        # 其次使用 <title> 标签
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取页面描述"""
        # 优先使用 og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content']

        # 其次使用 meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']

        return ""

    def _extract_og_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取Open Graph数据"""
        og_data = {}

        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if property_name and content:
                og_data[property_name] = content

        return og_data

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取主要文本内容"""
        # 移除脚本和样式
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # 尝试找到主要内容区域
        main_content = None

        # 常见的主内容标签
        for selector in ['main', 'article', '[role="main"]', '.content', '#content', '.main']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # 如果没找到，使用body
        if not main_content:
            main_content = soup.find('body')

        if not main_content:
            return ""

        # 提取文本
        text = main_content.get_text(separator='\n', strip=True)

        # 清理多余的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # 限制长度（前5000字符）
        if len(text) > 5000:
            text = text[:5000] + "..."

        return text

    def _extract_product_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取产品相关信息"""
        product_info = {}

        # 提取价格
        price_patterns = [
            r'\$[\d,]+\.?\d*',
            r'¥[\d,]+\.?\d*',
            r'€[\d,]+\.?\d*',
            r'£[\d,]+\.?\d*'
        ]

        text = soup.get_text()
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                product_info['prices'] = matches[:3]  # 最多3个价格
                break

        # 提取产品名称（从标题）
        title = self._extract_title(soup)
        if title:
            product_info['name'] = title

        # 提取特性/卖点（查找包含特定关键词的列表）
        features = []
        for ul in soup.find_all(['ul', 'ol']):
            items = ul.find_all('li')
            if 2 <= len(items) <= 10:  # 合理的特性列表长度
                feature_texts = [item.get_text().strip() for item in items]
                # 检查是否像产品特性（不太长，不太短）
                if all(10 < len(text) < 200 for text in feature_texts):
                    features.extend(feature_texts[:5])  # 最多5个特性
                    break

        if features:
            product_info['features'] = features

        # 提取规格参数（查找表格）
        specs = {}
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows[:10]:  # 最多10行
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    if key and value and len(key) < 50 and len(value) < 200:
                        specs[key] = value

        if specs:
            product_info['specs'] = specs

        return product_info

    async def crawl_entire_website(
        self,
        url: str,
        max_pages: int = 50,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        爬取整个网站的内容

        Args:
            url: 起始URL
            max_pages: 最多爬取页面数
            max_depth: 最大爬取深度

        Returns:
            聚合后的网站内容
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls.clear()

        logger.info(f"🕷️ 开始爬取网站: {url}")
        logger.info(f"   最大页面数: {max_pages}, 最大深度: {max_depth}")

        # 1. 尝试从sitemap获取所有URL
        sitemap_urls = await self._get_urls_from_sitemap(url)

        if sitemap_urls:
            logger.info(f"✅ 从sitemap找到 {len(sitemap_urls)} 个URL")
            urls_to_crawl = sitemap_urls[:max_pages]
        else:
            logger.info("⚠️ 未找到sitemap，使用递归爬取")
            # 2. 递归爬取链接
            urls_to_crawl = await self._crawl_links_recursive(url, depth=0)

        logger.info(f"📊 准备爬取 {len(urls_to_crawl)} 个页面")

        # 3. 并行提取所有页面内容
        all_contents = await self._extract_multiple_pages(urls_to_crawl)

        # 4. 聚合内容
        aggregated_content = self._aggregate_contents(all_contents, url)

        logger.info(f"✅ 网站爬取完成，共处理 {len(all_contents)} 个页面")

        return aggregated_content

    async def _get_urls_from_sitemap(self, base_url: str) -> List[str]:
        """从sitemap.xml获取所有URL"""
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"

        # 常见的sitemap位置
        sitemap_urls = [
            f"{base_domain}/sitemap.xml",
            f"{base_domain}/sitemap_index.xml",
            f"{base_domain}/sitemap-index.xml",
            f"{base_domain}/robots.txt"  # 从robots.txt中查找sitemap
        ]

        all_urls = []

        try:
            async with aiohttp.ClientSession() as session:
                for sitemap_url in sitemap_urls:
                    try:
                        async with session.get(sitemap_url, headers=self.headers, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()

                                # 如果是robots.txt，提取sitemap URL
                                if 'robots.txt' in sitemap_url:
                                    sitemap_matches = re.findall(r'Sitemap:\s*(.+)', content, re.IGNORECASE)
                                    for match in sitemap_matches:
                                        sitemap_content_url = match.strip()
                                        urls = await self._parse_sitemap(sitemap_content_url, session)
                                        all_urls.extend(urls)
                                else:
                                    # 直接解析sitemap
                                    urls = await self._parse_sitemap_content(content, session)
                                    all_urls.extend(urls)

                                if all_urls:
                                    logger.info(f"✅ 从 {sitemap_url} 找到 {len(all_urls)} 个URL")
                                    break

                    except Exception as e:
                        logger.debug(f"无法访问 {sitemap_url}: {e}")
                        continue

        except Exception as e:
            logger.error(f"获取sitemap失败: {e}")

        return list(set(all_urls))  # 去重

    async def _parse_sitemap(self, sitemap_url: str, session: aiohttp.ClientSession) -> List[str]:
        """解析sitemap URL"""
        try:
            async with session.get(sitemap_url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    return await self._parse_sitemap_content(content, session)
        except Exception as e:
            logger.debug(f"解析sitemap失败 {sitemap_url}: {e}")

        return []

    async def _parse_sitemap_content(self, content: str, session: aiohttp.ClientSession) -> List[str]:
        """解析sitemap内容"""
        urls = []

        try:
            # 解析XML
            root = ET.fromstring(content)

            # 处理sitemap index（包含多个sitemap）
            for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None and loc.text:
                    # 递归解析子sitemap
                    sub_urls = await self._parse_sitemap(loc.text, session)
                    urls.extend(sub_urls)

            # 处理URL列表
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None and loc.text:
                    urls.append(loc.text)

        except ET.ParseError as e:
            logger.debug(f"XML解析失败: {e}")

        return urls

    async def _crawl_links_recursive(
        self,
        url: str,
        depth: int = 0
    ) -> List[str]:
        """递归爬取链接"""
        if depth > self.max_depth or len(self.visited_urls) >= self.max_pages:
            return []

        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)
        urls = [url]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status != 200:
                        return urls

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 提取所有链接
                    links = self._extract_internal_links(soup, url)

                    # 递归爬取（限制并发数）
                    if depth < self.max_depth:
                        tasks = []
                        for link in links[:10]:  # 每页最多爬取10个链接
                            if len(self.visited_urls) < self.max_pages:
                                tasks.append(self._crawl_links_recursive(link, depth + 1))

                        if tasks:
                            results = await asyncio.gather(*tasks, return_exceptions=True)
                            for result in results:
                                if isinstance(result, list):
                                    urls.extend(result)

        except Exception as e:
            logger.debug(f"爬取链接失败 {url}: {e}")

        return urls

    def _extract_internal_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取页面内的内部链接"""
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # 转换为绝对URL
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)

            # 只保留同域名的链接
            if parsed.netloc == base_domain:
                # 移除fragment和query参数（可选）
                clean_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    '',  # params
                    '',  # query
                    ''   # fragment
                ))

                # 过滤掉文件下载链接
                if not self._is_file_url(clean_url):
                    links.append(clean_url)

        return list(set(links))  # 去重

    def _is_file_url(self, url: str) -> bool:
        """检查是否是文件下载链接"""
        file_extensions = [
            '.pdf', '.zip', '.rar', '.exe', '.dmg',
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.mp4', '.avi', '.mov', '.mp3', '.wav'
        ]

        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in file_extensions)

    async def _extract_multiple_pages(self, urls: List[str]) -> List[Dict[str, Any]]:
        """并行提取多个页面的内容"""
        # 限制并发数为10
        semaphore = asyncio.Semaphore(10)

        async def extract_with_semaphore(url: str) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    content = await self.extract_content_from_url(url, max_images=5)
                    return content if content else None
                except Exception as e:
                    logger.debug(f"提取页面失败 {url}: {e}")
                    return None

        tasks = [extract_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤掉失败的结果
        valid_contents = []
        for result in results:
            if isinstance(result, dict) and result:
                valid_contents.append(result)

        return valid_contents

    def _aggregate_contents(self, contents: List[Dict[str, Any]], base_url: str) -> Dict[str, Any]:
        """聚合多个页面的内容"""
        if not contents:
            return {}

        # 使用第一个页面作为基础
        aggregated = {
            "base_url": base_url,
            "total_pages": len(contents),
            "title": contents[0].get('title', ''),
            "description": contents[0].get('description', ''),
            "og_data": contents[0].get('og_data', {}),
        }

        # 聚合所有图片
        all_images = []
        for content in contents:
            images = content.get('images', [])
            all_images.extend(images)

        # 去重图片（基于URL）
        seen_urls = set()
        unique_images = []
        for img in all_images:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)

        aggregated['images'] = unique_images[:50]  # 最多50张图片

        # 聚合主要内容
        all_content = []
        for content in contents:
            main_content = content.get('main_content', '')
            if main_content:
                all_content.append(f"## {content.get('title', 'Page')}\n\n{main_content}")

        aggregated['main_content'] = '\n\n---\n\n'.join(all_content)

        # 聚合产品信息
        all_features = []
        all_prices = []
        all_specs = {}

        for content in contents:
            product_info = content.get('product_info', {})

            if 'features' in product_info:
                all_features.extend(product_info['features'])

            if 'prices' in product_info:
                all_prices.extend(product_info['prices'])

            if 'specs' in product_info:
                all_specs.update(product_info['specs'])

        aggregated['product_info'] = {
            'name': contents[0].get('product_info', {}).get('name', aggregated['title']),
            'features': list(set(all_features))[:20],  # 去重，最多20个特性
            'prices': list(set(all_prices))[:5],  # 去重，最多5个价格
            'specs': dict(list(all_specs.items())[:20])  # 最多20个规格
        }

        # 添加页面列表
        aggregated['pages'] = [
            {
                'url': content.get('url', ''),
                'title': content.get('title', ''),
                'description': content.get('description', '')
            }
            for content in contents
        ]

        return aggregated


async def test_extractor():
    """测试提取器"""
    print("🧪 测试网页内容提取器")
    print("=" * 80)

    extractor = WebContentExtractor()

    # 测试单页提取
    print("\n📄 测试单页提取")
    print("-" * 80)
    test_url = "https://www.apple.com/iphone/"

    content = await extractor.extract_content_from_url(test_url, max_images=5)
    print(f"标题: {content.get('title', 'N/A')}")
    print(f"描述: {content.get('description', 'N/A')[:100]}...")
    print(f"图片数量: {len(content.get('images', []))}")

    # 测试全站爬取
    print("\n\n🕷️ 测试全站爬取")
    print("-" * 80)

    crawl_url = "https://www.apple.com/iphone/"
    aggregated = await extractor.crawl_entire_website(
        crawl_url,
        max_pages=10,  # 限制为10页用于测试
        max_depth=2
    )

    print(f"\n📊 爬取结果:")
    print(f"  总页面数: {aggregated.get('total_pages', 0)}")
    print(f"  总图片数: {len(aggregated.get('images', []))}")
    print(f"  产品特性数: {len(aggregated.get('product_info', {}).get('features', []))}")

    print(f"\n📄 爬取的页面:")
    for i, page in enumerate(aggregated.get('pages', [])[:5], 1):
        print(f"  {i}. {page.get('title', 'N/A')}")
        print(f"     {page.get('url', 'N/A')}")

    print("\n" + "=" * 80)
    print("✅ 测试完成")


async def test_with_custom_url(url: str):
    """使用自定义URL测试"""
    print(f"🧪 测试URL: {url}")
    print("=" * 80)

    extractor = WebContentExtractor()

    # 测试全站爬取
    print("\n🕷️ 开始爬取...")
    aggregated = await extractor.crawl_entire_website(
        url,
        max_pages=20,
        max_depth=2
    )

    print(f"\n📊 爬取结果:")
    print(f"  基础URL: {aggregated.get('base_url', 'N/A')}")
    print(f"  总页面数: {aggregated.get('total_pages', 0)}")
    print(f"  标题: {aggregated.get('title', 'N/A')}")
    print(f"  描述: {aggregated.get('description', 'N/A')[:200]}...")
    print(f"  总图片数: {len(aggregated.get('images', []))}")

    product_info = aggregated.get('product_info', {})
    print(f"\n📦 产品信息:")
    print(f"  产品名称: {product_info.get('name', 'N/A')}")
    print(f"  特性数量: {len(product_info.get('features', []))}")
    print(f"  价格: {', '.join(product_info.get('prices', []))}")

    if product_info.get('features'):
        print(f"\n  核心特性:")
        for i, feature in enumerate(product_info.get('features', [])[:5], 1):
            print(f"    {i}. {feature}")

    print(f"\n📄 爬取的页面列表:")
    for i, page in enumerate(aggregated.get('pages', []), 1):
        print(f"  {i}. {page.get('title', 'N/A')}")
        print(f"     {page.get('url', 'N/A')}")

    print("\n" + "=" * 80)
    print("✅ 测试完成")

    return aggregated


if __name__ == "__main__":
    asyncio.run(test_extractor())
