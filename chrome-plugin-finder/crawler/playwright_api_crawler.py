#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright + API 爬虫
流程：Playwright获取plugin id → API拉取详情和评论
"""

import asyncio
import re
import aiohttp
from playwright.async_api import async_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PLUGIN_FILTER, CRAWLER_CONFIG
from storage.db_manager import DBManager


class PlaywrightAPICrawler:
    """
    Playwright + API 爬虫类
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
            category: 分类名称
            max_plugins: 最大获取数量
            
        Returns:
            list: 插件ID列表
        """
        plugin_ids = []
        url = f"https://chromewebstore.google.com/category/extensions/{category}?hl=zh-CN"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                print(f"  访问分类页面...")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)
                
                # 滚动页面
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                
                # 获取所有插件链接
                links = await page.query_selector_all('a[href*="/detail/"]')
                
                seen_ids = set()
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        if not href:
                            continue
                        
                        # 提取插件ID (24-32位字符)
                        match = re.search(r'/detail/[^/]+/([a-z]{24,32})', href)
                        if match:
                            plugin_id = match.group(1)
                            
                            if plugin_id in seen_ids:
                                continue
                            seen_ids.add(plugin_id)
                            plugin_ids.append(plugin_id)
                            
                            if len(plugin_ids) >= max_plugins:
                                break
                    except:
                        continue
                        
            except Exception as e:
                print(f"  获取插件列表失败: {e}")
            finally:
                await browser.close()
        
        return plugin_ids
    
    async def get_plugin_details_from_api(self, plugin_id):
        """
        从Chrome Web Store API获取插件详情
        使用chrome-webstore-api或其他可用API
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            dict: 插件详情
        """
        # 方法1: 尝试使用ChromeStats API (需要API key)
        # 方法2: 直接请求详情页并解析
        
        url = f"https://chromewebstore.google.com/detail/{plugin_id}"
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # 解析基本信息
                info = {
                    'id': plugin_id,
                    'name': '',
                    'description': '',
                    'rating': 0.0,
                    'review_count': 0,
                    'install_count': 0,
                    'developer': '',
                    'category': '',
                    'url': url
                }
                
                # 提取名称
                name_match = re.search(r'<title>(.*?)\s*-\s*Chrome', html)
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
                
                return info
                
        except Exception as e:
            print(f"    API请求失败: {e}")
            return None
    
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
        plugin_ids = await self.get_plugin_ids_from_category(category, max_plugins)
        print(f"找到 {len(plugin_ids)} 个插件ID")
        
        results = []
        
        for i, plugin_id in enumerate(plugin_ids):
            print(f"\n  [{i+1}/{len(plugin_ids)}] 处理 ID: {plugin_id}")
            
            # 2. 获取插件详情
            details = await self.get_plugin_details_from_api(plugin_id)
            
            if details and details['name']:
                print(f"    名称: {details['name'][:50]}")
                print(f"    评分: {details['rating']} | 评论: {details['review_count']} | 用户: {details['install_count']}")
                
                results.append(details)
                
                # 存储到数据库
                try:
                    db_plugin_id = self.db.insert_plugin(details)
                    print(f"    ✓ 已存储 (ID: {db_plugin_id})")
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
        
        for category in PLUGIN_FILTER['categories'][:3]:
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
    async with PlaywrightAPICrawler() as crawler:
        await crawler.run()


if __name__ == "__main__":
    asyncio.run(main())
