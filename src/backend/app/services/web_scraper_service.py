"""
增强的网页抓取服务
整合 MCP 工具提供强大的网页内容获取能力
"""
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class WebScraperService:
    """
    网页抓取服务 - 支持多种抓取策略

    功能：
    1. 基础抓取：简单静态网页（aiohttp + BeautifulSoup）
    2. 高级抓取：JavaScript渲染网页（MCP Fetch）
    3. 浏览器抓取：复杂交互网页（MCP Puppeteer）
    """

    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        # 支持的抓取策略
        self.strategies = {
            'basic': self._scrape_basic,
            'advanced': self._scrape_with_mcp_fetch,
            'browser': self._scrape_with_puppeteer
        }

    async def scrape_url(
        self,
        url: str,
        strategy: str = 'auto',
        max_length: int = 50000,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        抓取网页内容

        Args:
            url: 网页URL
            strategy: 抓取策略 ('auto', 'basic', 'advanced', 'browser')
            max_length: 最大内容长度
            options: 抓取选项

        Returns:
            {
                'success': bool,
                'url': str,
                'title': str,
                'content': str,
                'metadata': dict,
                'strategy_used': str,
                'error': str (if failed)
            }
        """
        options = options or {}

        try:
            # 自动选择策略
            if strategy == 'auto':
                strategy = self._detect_best_strategy(url)

            if strategy not in self.strategies:
                return {
                    'success': False,
                    'url': url,
                    'error': f"不支持的策略: {strategy}"
                }

            logger.info(f"开始抓取网页: {url} (策略: {strategy})")

            # 执行抓取
            scrape_func = self.strategies[strategy]
            result = await scrape_func(url, max_length, options)

            result['strategy_used'] = strategy
            return result

        except Exception as e:
            logger.error(f"网页抓取失败 {url}: {str(e)}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'strategy_used': strategy
            }

    def _detect_best_strategy(self, url: str) -> str:
        """
        根据URL自动检测最佳抓取策略

        规则：
        - 新闻/博客网站 → basic
        - SPA应用/现代网站 → advanced
        - 需要登录/交互 → browser
        """
        domain = urlparse(url).netloc.lower()

        # JavaScript 重度依赖的网站
        js_heavy_domains = [
            'twitter.com', 'x.com', 'facebook.com', 'instagram.com',
            'linkedin.com', 'medium.com', 'notion.so', 'github.com'
        ]

        for js_domain in js_heavy_domains:
            if js_domain in domain:
                return 'advanced'

        # 默认使用基础策略
        return 'basic'

    async def _scrape_basic(
        self,
        url: str,
        max_length: int,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基础抓取策略：使用 aiohttp + BeautifulSoup
        适用于静态网页
        """
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }

            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'url': url,
                            'error': f"HTTP {response.status}"
                        }

                    html_content = await response.text()

            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除脚本和样式
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

            # 提取标题
            title = soup.title.string if soup.title else urlparse(url).path

            # 提取主要内容
            content = self._extract_main_content(soup)

            # 清理和限制长度
            content = self._clean_text(content)
            if len(content) > max_length:
                content = content[:max_length] + "..."

            # 提取元数据
            metadata = self._extract_metadata(soup, url)

            return {
                'success': True,
                'url': url,
                'title': title.strip() if title else "Untitled",
                'content': content,
                'metadata': metadata,
                'length': len(content)
            }

        except Exception as e:
            logger.error(f"基础抓取失败: {str(e)}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }

    async def _scrape_with_mcp_fetch(
        self,
        url: str,
        max_length: int,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        高级抓取策略：使用 MCP Fetch 工具
        支持 JavaScript 渲染和图片提取

        注意：此方法需要 MCP fetch 服务器可用
        如果不可用，会降级到基础策略
        """
        try:
            # 尝试导入 MCP 工具（如果可用）
            # 注意：这里需要根据实际的 MCP 集成方式调整
            # 当前实现为占位符，展示如何使用 MCP

            logger.info(f"使用 MCP Fetch 抓取: {url}")

            # TODO: 实际调用 MCP fetch 工具
            # 当前降级到基础策略
            logger.warning("MCP Fetch 暂未集成，降级到基础策略")
            return await self._scrape_basic(url, max_length, options)

        except Exception as e:
            logger.error(f"MCP Fetch 抓取失败，降级到基础策略: {str(e)}")
            return await self._scrape_basic(url, max_length, options)

    async def _scrape_with_puppeteer(
        self,
        url: str,
        max_length: int,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        浏览器抓取策略：使用 MCP Puppeteer 工具
        支持完整的浏览器交互和JavaScript执行

        注意：此方法需要 MCP puppeteer 服务器可用
        如果不可用，会降级到高级策略
        """
        try:
            logger.info(f"使用 MCP Puppeteer 抓取: {url}")

            # TODO: 实际调用 MCP puppeteer 工具
            # 当前降级到高级策略
            logger.warning("MCP Puppeteer 暂未集成，降级到高级策略")
            return await self._scrape_with_mcp_fetch(url, max_length, options)

        except Exception as e:
            logger.error(f"MCP Puppeteer 抓取失败，降级到高级策略: {str(e)}")
            return await self._scrape_with_mcp_fetch(url, max_length, options)

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取网页主要内容"""

        # 优先查找常见的主内容容器
        main_selectors = [
            'article', 'main', '[role="main"]',
            '.content', '.post-content', '.article-content',
            '#content', '#main-content', '.main-content'
        ]

        for selector in main_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                return content_element.get_text(separator='\n', strip=True)

        # 如果没有找到，提取所有段落
        paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
        return '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

    def _clean_text(self, text: str) -> str:
        """清理提取的文本"""
        # 移除多余的空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()
        return text

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """提取网页元数据"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc
        }

        # 提取 meta 标签
        meta_tags = {
            'description': ['description', 'og:description', 'twitter:description'],
            'keywords': ['keywords'],
            'author': ['author', 'article:author'],
            'publish_date': ['article:published_time', 'publish_date']
        }

        for key, tag_names in meta_tags.items():
            for tag_name in tag_names:
                meta = soup.find('meta', attrs={'name': tag_name}) or \
                       soup.find('meta', attrs={'property': tag_name})
                if meta and meta.get('content'):
                    metadata[key] = meta.get('content')
                    break

        return metadata

    async def batch_scrape(
        self,
        urls: List[str],
        strategy: str = 'auto',
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量抓取多个URL

        Args:
            urls: URL列表
            strategy: 抓取策略
            max_concurrent: 最大并发数

        Returns:
            抓取结果列表
        """
        import asyncio

        results = []

        # 分批处理
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]

            tasks = [
                self.scrape_url(url, strategy=strategy)
                for url in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results.append({
                        'success': False,
                        'url': url,
                        'error': str(result)
                    })
                else:
                    results.append(result)

        logger.info(f"批量抓取完成: 总数 {len(urls)}, 成功 {sum(1 for r in results if r.get('success'))}")
        return results
