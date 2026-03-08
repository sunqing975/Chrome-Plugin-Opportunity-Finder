#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确的Chrome Web Store爬虫
流程：Playwright获取插件ID → detail API → review API
"""

import asyncio
import re
import json
import requests
from playwright.async_api import async_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PLUGIN_FILTER, CRAWLER_CONFIG
from storage.db_manager import DBManager


class CorrectCrawler:
    """
    正确的Chrome Web Store爬虫
    使用Playwright获取ID，通过API获取详情和评论
    """
    
    def __init__(self):
        """
        初始化爬虫
        """
        self.db = DBManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def __del__(self):
        """
        析构函数
        """
        if hasattr(self, 'db') and self.db:
            self.db.close()
        if hasattr(self, 'session'):
            self.session.close()
    
    async def get_plugin_ids_from_category(self, page, category, max_plugins=10):
        """
        使用Playwright从分类页面获取插件ID列表
        
        Args:
            page: Playwright Page对象
            category: 分类名称
            max_plugins: 最大获取数量
            
        Returns:
            list: 插件ID列表
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
                    
                    # 提取插件ID (24-32位小写字母)
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
    
    def get_plugin_details_from_api(self, plugin_id):
        """
        从Chrome Web Store detail API获取插件详情
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            dict: 插件详情
        """
        # Chrome Web Store detail API
        url = "https://chrome.google.com/webstore/ajax/detail"
        params = {
            'hl': 'zh-CN',
            'gl': 'CN',
            'pv': '20210820',
            'mce': 'atf,ciif',
            'ids': plugin_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"    API请求失败: {response.status_code}")
                return None
            
            # 返回数据前面有 )]}' 需要去掉
            text = response.text
            if text.startswith(")]}'"):
                text = text[4:]
            
            data = json.loads(text)
            
            # data是一个数组，第一个元素包含插件信息
            if not data or len(data) == 0:
                return None
            
            plugin_data = data[0]
            
            # 解析插件信息
            info = {
                'id': plugin_id,
                'name': plugin_data.get('name', ''),
                'description': plugin_data.get('description', ''),
                'rating': float(plugin_data.get('rating', 0)),
                'review_count': int(plugin_data.get('ratingCount', 0)),
                'install_count': int(plugin_data.get('userCount', 0)),
                'developer': plugin_data.get('developer', {}).get('name', ''),
                'category': plugin_data.get('category', ''),
                'url': f"https://chromewebstore.google.com/detail/{plugin_id}"
            }
            
            return info
            
        except Exception as e:
            print(f"    解析详情失败: {e}")
            return None
    
    def get_reviews_from_api(self, plugin_id, max_reviews=50):
        """
        从Chrome Web Store review API获取评论
        
        Args:
            plugin_id: 插件ID
            max_reviews: 最大评论数
            
        Returns:
            list: 评论列表
        """
        # Chrome Web Store review API
        url = "https://chrome.google.com/webstore/ajax/review"
        params = {
            'hl': 'zh-CN',
            'gl': 'CN',
            'pv': '20210820',
            'mce': 'atf,ciif',
            'id': plugin_id,
            'sortBy': '0',  # 0=最新, 1=最有帮助
            'numResults': max_reviews,
            'startIndex': '0'
        }
        
        reviews = []
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return reviews
            
            # 返回数据前面有 )]}' 需要去掉
            text = response.text
            if text.startswith(")]}'"):
                text = text[4:]
            
            data = json.loads(text)
            
            # data是一个数组，包含评论信息
            if not data or len(data) == 0:
                return reviews
            
            # 解析评论
            for review_data in data:
                try:
                    review = {
                        'text': review_data.get('body', ''),
                        'rating': float(review_data.get('rating', 0)),
                        'date': review_data.get('date', ''),
                        'user': review_data.get('userName', '')
                    }
                    
                    if review['text']:
                        reviews.append(review)
                except:
                    continue
                    
        except Exception as e:
            print(f"    获取评论失败: {e}")
        
        return reviews
    
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
        
        # 创建列表页
        list_page = await browser.new_page()
        plugin_ids = await self.get_plugin_ids_from_category(list_page, category, max_plugins)
        await list_page.close()
        
        print(f"找到 {len(plugin_ids)} 个插件ID")
        
        results = []
        
        for i, plugin_id in enumerate(plugin_ids):
            print(f"\n  [{i+1}/{len(plugin_ids)}] 处理 ID: {plugin_id}")
            
            # 1. 获取插件详情
            details = self.get_plugin_details_from_api(plugin_id)
            
            if details and details['name']:
                print(f"    名称: {details['name'][:50]}")
                print(f"    评分: {details['rating']} | 评论: {details['review_count']} | 用户: {details['install_count']}")
                
                # 2. 获取评论
                if details['review_count'] > 0:
                    print(f"    正在获取评论...")
                    reviews = self.get_reviews_from_api(plugin_id, max_reviews=20)
                    print(f"    获取到 {len(reviews)} 条评论")
                    details['reviews'] = reviews
                
                results.append(details)
                
                # 3. 存储到数据库
                try:
                    db_plugin_id = self.db.insert_plugin(details)
                    print(f"    ✓ 已存储 (ID: {db_plugin_id})")
                    
                    # 存储评论
                    if 'reviews' in details:
                        for review in details['reviews']:
                            self.db.insert_review(db_plugin_id, review)
                            
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
        print("Chrome插件爬虫 - 正确API版")
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
    crawler = CorrectCrawler()
    await crawler.run()


if __name__ == "__main__":
    asyncio.run(main())
