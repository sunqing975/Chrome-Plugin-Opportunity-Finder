#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright + Chrome Web Store API 爬虫
流程：Playwright获取plugin id → API拉取详情 → API拉取评论
"""

import asyncio
import re
import json
import aiohttp
from playwright.async_api import async_playwright
from playwright_stealth import stealth
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PLUGIN_FILTER, CRAWLER_CONFIG
from storage.db_manager import DBManager


class ChromeWebStoreCrawler:
    """
    Chrome Web Store爬虫类
    使用Playwright获取插件ID，通过API获取详情和评论
    """
    
    def __init__(self):
        """
        初始化爬虫
        """
        self.db = DBManager()
        self.session = None
        
    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        """
        if self.session:
            await self.session.close()
        self.db.close()
        
    async def get_plugin_ids_from_category(self, category, max_plugins=10):
        """
        使用Playwright从分类页面获取插件ID列表
        
        Args:
            category: 分类名称（如'productivity'）
            max_plugins: 最大获取数量
            
        Returns:
            list: 插件信息列表，包含id、name、url
        """
        plugins = []
        url = f"https://chromewebstore.google.com/category/extensions/{category}?hl=zh-CN"
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # 使用stealth模式隐藏自动化特征
            await stealth(page)
            
            try:
                print(f"  访问分类页面: {category}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # 等待页面加载
                await asyncio.sleep(3)
                
                # 滚动页面加载更多
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                
                # 获取所有插件链接
                links = await page.query_selector_all('a[href*="/detail/"]')
                
                seen_ids = set()
                for link in links[:max_plugins * 2]:  # 多获取一些，去重后可能不够
                    try:
                        href = await link.get_attribute('href')
                        if not href or '/detail/' not in href:
                            continue
                            
                        # 提取插件ID
                        # URL格式: https://chromewebstore.google.com/detail/xxx/PLUGIN_ID
                        match = re.search(r'/detail/[^/]+/([a-z]+)', href)
                        if match:
                            plugin_id = match.group(1)
                            
                            if plugin_id in seen_ids:
                                continue
                            seen_ids.add(plugin_id)
                            
                            # 获取插件名称
                            text = await link.inner_text()
                            name = text.split('\n')[0][:100] if text else ''
                            
                            plugins.append({
                                'id': plugin_id,
                                'name': name,
                                'url': href
                            })
                            
                            if len(plugins) >= max_plugins:
                                break
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"  获取插件列表失败: {e}")
            finally:
                await browser.close()
                
        return plugins
    
    async def get_plugin_details_from_api(self, plugin_id):
        """
        从Chrome Web Store API获取插件详情
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            dict: 插件详情
        """
        # Chrome Web Store API端点
        api_url = f"https://chrome.google.com/webstore/detail/{plugin_id}"
        
        try:
            async with self.session.get(api_url, timeout=10) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                
                # 从HTML中提取JSON数据
                # Chrome Web Store在页面中嵌入了JSON数据
                match = re.search(r'"detail":\s*(\{.*?\}),\s*"relatedExtensions"', html, re.DOTALL)
                if not match:
                    # 尝试其他模式
                    match = re.search(r'data\s*=\s*(\{.*?\});', html, re.DOTALL)
                
                if match:
                    try:
                        data = json.loads(match.group(1))
                        return self._parse_plugin_data(data, plugin_id)
                    except json.JSONDecodeError:
                        pass
                
                # 如果JSON解析失败，从HTML中提取基本信息
                return self._extract_basic_info_from_html(html, plugin_id)
                
        except Exception as e:
            print(f"    API请求失败: {e}")
            return None
    
    def _parse_plugin_data(self, data, plugin_id):
        """
        解析API返回的插件数据
        
        Args:
            data: JSON数据
            plugin_id: 插件ID
            
        Returns:
            dict: 解析后的插件信息
        """
        try:
            detail = data.get('detail', data)  # 兼容不同格式
            
            return {
                'id': plugin_id,
                'name': detail.get('name', ''),
                'description': detail.get('description', ''),
                'rating': detail.get('rating', 0),
                'review_count': detail.get('ratingCount', 0),
                'install_count': detail.get('installCount', 0),
                'developer': detail.get('developer', {}).get('name', ''),
                'category': detail.get('category', ''),
                'url': f"https://chromewebstore.google.com/detail/{plugin_id}"
            }
        except Exception as e:
            print(f"    解析数据失败: {e}")
            return None
    
    def _extract_basic_info_from_html(self, html, plugin_id):
        """
        从HTML中提取基本信息（备用方法）
        
        Args:
            html: HTML内容
            plugin_id: 插件ID
            
        Returns:
            dict: 插件基本信息
        """
        info = {
            'id': plugin_id,
            'name': '',
            'description': '',
            'rating': 0,
            'review_count': 0,
            'install_count': 0,
            'developer': '',
            'category': '',
            'url': f"https://chromewebstore.google.com/detail/{plugin_id}"
        }
        
        try:
            # 提取名称
            name_match = re.search(r'<title>(.*?)\s*-.*?Chrome', html)
            if name_match:
                info['name'] = name_match.group(1).strip()
            
            # 提取评分
            rating_match = re.search(r'(\d+\.\d+)\s*out of\s*5', html)
            if rating_match:
                info['rating'] = float(rating_match.group(1))
            
            # 提取评论数
            review_match = re.search(r'(\d+)\s*reviews?', html, re.IGNORECASE)
            if review_match:
                info['review_count'] = int(review_match.group(1))
            
            # 提取用户数
            user_match = re.search(r'([\d,]+)\s*users?', html, re.IGNORECASE)
            if user_match:
                info['install_count'] = int(user_match.group(1).replace(',', ''))
                
        except Exception as e:
            print(f"    HTML解析失败: {e}")
            
        return info
    
    async def get_reviews_from_api(self, plugin_id, max_reviews=50):
        """
        从API获取插件评论
        
        Args:
            plugin_id: 插件ID
            max_reviews: 最大评论数
            
        Returns:
            list: 评论列表
        """
        reviews = []
        
        # Chrome Web Store评论API
        # 注意：这是一个非官方API，可能会变化
        api_url = f"https://chrome.google.com/webstore/reviews/{plugin_id}"
        
        try:
            async with self.session.get(api_url, timeout=10) as response:
                if response.status != 200:
                    return reviews
                    
                html = await response.text()
                
                # 从HTML中提取评论
                # 评论通常在特定的JSON结构中
                review_pattern = r'"review":\s*\{[^}]*"text":\s*"([^"]*)"[^}]*"rating":\s*(\d+)'
                matches = re.findall(review_pattern, html)
                
                for text, rating in matches[:max_reviews]:
                    reviews.append({
                        'text': text,
                        'rating': int(rating)
                    })
                    
        except Exception as e:
            print(f"    获取评论失败: {e}")
            
        return reviews
    
    async def crawl_category(self, category, max_plugins=5):
        """
        爬取单个分类
        
        Args:
            category: 分类名称
            max_plugins: 最大插件数
            
        Returns:
            list: 插件信息列表
        """
        print(f"\n{'='*60}")
        print(f"爬取分类: {category}")
        print(f"{'='*60}")
        
        # 1. 获取插件ID列表
        plugins = await self.get_plugin_ids_from_category(category, max_plugins)
        print(f"找到 {len(plugins)} 个插件")
        
        results = []
        
        for i, plugin in enumerate(plugins):
            print(f"\n  [{i+1}/{len(plugins)}] 处理: {plugin['name'][:40]}...")
            print(f"    ID: {plugin['id']}")
            
            # 2. 获取插件详情
            details = await self.get_plugin_details_from_api(plugin['id'])
            
            if details:
                # 合并信息
                if not details['name']:
                    details['name'] = plugin['name']
                
                print(f"    名称: {details['name'][:50]}")
                print(f"    评分: {details['rating']} | 评论: {details['review_count']} | 用户: {details['install_count']}")
                
                # 3. 获取评论
                if details['review_count'] > 0:
                    print(f"    正在获取评论...")
                    reviews = await self.get_reviews_from_api(plugin['id'])
                    print(f"    获取到 {len(reviews)} 条评论")
                    details['reviews'] = reviews
                
                results.append(details)
                
                # 存储到数据库
                try:
                    plugin_id = self.db.insert_plugin(details)
                    print(f"    ✓ 已存储 (ID: {plugin_id})")
                    
                    # 存储评论
                    if 'reviews' in details:
                        for review in details['reviews']:
                            self.db.insert_review(plugin_id, review)
                            
                except Exception as e:
                    print(f"    ✗ 存储失败: {e}")
            else:
                print(f"    ✗ 获取详情失败")
            
            await asyncio.sleep(CRAWLER_CONFIG['sleep_time'])
        
        return results
    
    async def run(self):
        """
        运行爬虫
        """
        print("="*80)
        print("Chrome插件爬虫 - Playwright + API版")
        print("="*80)
        
        all_plugins = []
        
        for category in PLUGIN_FILTER['categories'][:3]:  # 先测试前3个分类
            plugins = await self.crawl_category(category, max_plugins=5)
            all_plugins.extend(plugins)
        
        # 显示结果
        print("\n" + "="*80)
        print(f"爬取完成！共获取 {len(all_plugins)} 个插件")
        print("="*80)
        
        if all_plugins:
            print(f"\n{'名称':<50} {'评分':<6} {'评论':<6} {'用户':<12}")
            print("-"*80)
            
            for p in all_plugins:
                name = p['name'][:48] if p['name'] else 'N/A'
                rating = p['rating'] if p['rating'] else '-'
                reviews = p['review_count'] if p['review_count'] else '-'
                users = p['install_count'] if p['install_count'] else '-'
                print(f"{name:<50} {rating:<6} {reviews:<6} {users:<12}")


async def main():
    """
    主函数
    """
    async with ChromeWebStoreCrawler() as crawler:
        await crawler.run()


if __name__ == "__main__":
    asyncio.run(main())
