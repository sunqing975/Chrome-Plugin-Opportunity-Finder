#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯Playwright爬虫
使用Playwright获取列表页ID和详情页信息
"""

import asyncio
import re
from playwright.async_api import async_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PLUGIN_FILTER, CRAWLER_CONFIG
from storage.db_manager import DBManager


class PlaywrightFullCrawler:
    """
    纯Playwright爬虫类
    """
    
    def __init__(self):
        """
        初始化爬虫
        """
        self.db = DBManager()
        
    def __del__(self):
        """
        析构函数
        """
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
    async def get_plugin_ids_from_category(self, page, category, max_plugins=10):
        """
        从分类页面获取插件ID列表
        
        Args:
            page: Playwright Page对象
            category: 分类名称
            max_plugins: 最大获取数量
            
        Returns:
            list: 插件信息列表
        """
        plugin_ids = []
        url = f"https://chromewebstore.google.com/category/extensions/{category}?hl=zh-CN"
        
        try:
            print(f"  访问分类页面: {category}")
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
                    
                    # 提取插件ID
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
        
        return plugin_ids
    
    async def get_plugin_details(self, page, plugin_id):
        """
        从详情页获取插件信息
        
        Args:
            page: Playwright Page对象
            plugin_id: 插件ID
            
        Returns:
            dict: 插件详情
        """
        url = f"https://chromewebstore.google.com/detail/{plugin_id}"
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            # 获取页面文本
            body_text = await page.inner_text('body')
            
            # 解析信息
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
            
            # 提取名称 - 从页面标题
            title = await page.title()
            if title and 'Chrome' in title:
                info['name'] = title.split('-')[0].strip()[:100]
            
            # 从body文本提取其他信息
            lines = [l.strip() for l in body_text.split('\n') if l.strip()]
            
            # 提取评分 (如 "4.4★")
            for line in lines:
                rating_match = re.search(r'(\d+\.\d+)\s*★', line)
                if rating_match:
                    info['rating'] = float(rating_match.group(1))
                    break
            
            # 提取评论数
            for line in lines:
                review_match = re.search(r'(\d+)\s*个评分', line)
                if review_match:
                    info['review_count'] = int(review_match.group(1))
                    break
            
            # 提取用户数
            for line in lines:
                user_match = re.search(r'([\d,]+)\s*用户', line)
                if user_match:
                    info['install_count'] = int(user_match.group(1).replace(',', ''))
                    break
            
            # 提取描述（较长的文本行）
            for line in lines:
                if len(line) > 30 and len(line) < 300 and '★' not in line:
                    info['description'] = line[:500]
                    break
            
            return info
            
        except Exception as e:
            print(f"    获取详情失败: {e}")
            return None
    
    async def crawl_category(self, browser, category, max_plugins=5):
        """
        爬取单个分类
        
        Args:
            browser: Playwright Browser对象
            category: 分类名称
            max_plugins: 最大插件数
            
        Returns:
            list: 插件信息列表
        """
        print(f"\n{'='*60}")
        print(f"爬取分类: {category}")
        print(f"{'='*60}")
        
        # 创建新页面获取列表
        list_page = await browser.new_page()
        plugin_ids = await self.get_plugin_ids_from_category(list_page, category, max_plugins)
        await list_page.close()
        
        print(f"找到 {len(plugin_ids)} 个插件ID")
        
        results = []
        
        # 创建详情页
        detail_page = await browser.new_page()
        
        for i, plugin_id in enumerate(plugin_ids):
            print(f"\n  [{i+1}/{len(plugin_ids)}] 处理 ID: {plugin_id}")
            
            # 获取插件详情
            details = await self.get_plugin_details(detail_page, plugin_id)
            
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
        
        await detail_page.close()
        return results
    
    async def run(self):
        """
        运行爬虫
        """
        print("="*80)
        print("Chrome插件爬虫 - 纯Playwright版")
        print("="*80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                all_plugins = []
                
                for category in PLUGIN_FILTER['categories'][:2]:  # 先测试前2个分类
                    plugins = await self.crawl_category(browser, category, max_plugins=3)
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
                        
            finally:
                await browser.close()


async def main():
    """
    主函数
    """
    crawler = PlaywrightFullCrawler()
    await crawler.run()


if __name__ == "__main__":
    asyncio.run(main())
