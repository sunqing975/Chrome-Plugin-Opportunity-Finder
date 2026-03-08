#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可工作的Chrome Web Store爬虫
流程：Playwright获取插件ID → 访问详情页 → 提取body文本
"""

import asyncio
import re
from playwright.async_api import async_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PLUGIN_FILTER, CRAWLER_CONFIG
from storage.db_manager import DBManager
from crawler.review_crawler import ReviewCrawler
from utils.logger import logger
from utils.anti_block import anti_block, request_limiter


class WorkingCrawler:
    """
    可工作的Chrome Web Store爬虫
    """
    
    def __init__(self):
        """
        初始化爬虫
        """
        self.db = DBManager()
        self.review_crawler = ReviewCrawler()
        
    def __del__(self):
        """
        析构函数
        """
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
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
        
        # 限流检查
        request_limiter.wait_if_needed()
        
        # 记录请求
        logger.log_request(url, method='GET')
        
        try:
            print(f"  访问分类页面: {category}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 随机延迟
            anti_block.random_delay()
            
            # 滚动页面
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                anti_block.random_delay()
            
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
            logger.log_error('CategoryFetchError', str(e), {'category': category, 'url': url})
        
        # 记录响应
        logger.log_response(url, status_code=200, response_data={'plugin_count': len(plugin_ids)})
        
        return plugin_ids
    
    async def get_plugin_details_from_page(self, page, plugin_id):
        """
        从详情页body文本提取插件信息
        
        Args:
            page: Playwright Page对象
            plugin_id: 插件ID
            
        Returns:
            dict: 插件详情
        """
        url = f"https://chromewebstore.google.com/detail/{plugin_id}"
        
        # 限流检查
        request_limiter.wait_if_needed()
        
        # 记录请求
        logger.log_request(url, method='GET')
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 随机延迟
            anti_block.random_delay()
            
            # 获取body文本
            body_text = await page.inner_text('body')
            
            # 获取body文本
            body_text = await page.inner_text('body')
            
            # 解析信息
            info = {
                'id': plugin_id,
                'plugin_id': plugin_id,
                'name': '',
                'description': '',
                'rating': 0.0,
                'review_count': 0,
                'install_count': 0,
                'developer': '',
                'developer_url': '',
                'category': '',
                'version': '',
                'last_updated': '',
                'url': url,
                'icon_url': '',
                'screenshots': []
            }
            
            # 按行分割
            lines = [l.strip() for l in body_text.split('\n') if l.strip()]
            
            # 提取名称 - 从页面标题
            title = await page.title()
            if title and 'Chrome' in title:
                info['name'] = title.split('-')[0].strip()[:100]
            
            # 提取评分 (如 "4.2")
            for line in lines:
                rating_match = re.search(r'^(\d+\.\d+)$', line)
                if rating_match:
                    info['rating'] = float(rating_match.group(1))
                    break
            
            # 提取评论数 (如 "44.7K ratings")
            for line in lines:
                review_match = re.search(r'([\d.]+K?)\s*ratings?', line, re.IGNORECASE)
                if review_match:
                    review_text = review_match.group(1)
                    # 处理K单位
                    if 'K' in review_text:
                        info['review_count'] = int(float(review_text.replace('K', '')) * 1000)
                    else:
                        info['review_count'] = int(float(review_text))
                    break
            
            # 提取用户数 (如 "40,000,000 users")
            for line in lines:
                user_match = re.search(r'([\d,]+)\s*users?', line, re.IGNORECASE)
                if user_match:
                    info['install_count'] = int(user_match.group(1).replace(',', ''))
                    break
            
            # 提取开发者
            for i, line in enumerate(lines):
                if 'developer' in line.lower() or '提供者' in line or '开发者' in line:
                    # 开发者通常在下一行
                    if i + 1 < len(lines):
                        info['developer'] = lines[i + 1][:100]
                    break
            
            # 提取版本号
            # 版本号通常在"Version"标签的下一行
            for i, line in enumerate(lines):
                if line.lower() == 'version' or line == '版本':
                    # 版本号在下一行
                    if i + 1 < len(lines):
                        version_line = lines[i + 1]
                        # 匹配版本号格式 (如 "2.0.16" 或 "1.2.3")
                        version_match = re.search(r'^[\d.]+$', version_line)
                        if version_match:
                            info['version'] = version_line[:20]
                            break
            
            # 提取更新日期
            # 更新日期通常在"Updated"标签的下一行
            for i, line in enumerate(lines):
                if line.lower() == 'updated' or line == '更新':
                    # 更新日期在下一行
                    if i + 1 < len(lines):
                        update_line = lines[i + 1]
                        # 匹配英文日期格式 (如 "September 6, 2024")
                        date_match = re.search(r'^([A-Za-z]+\s+\d{1,2},?\s+\d{4})$', update_line)
                        if date_match:
                            info['last_updated'] = date_match.group(1)
                            break
                        # 匹配中文日期格式
                        date_match_cn = re.search(r'^(\d{4}年\d{1,2}月\d{1,2}日)$', update_line)
                        if date_match_cn:
                            info['last_updated'] = date_match_cn.group(1)
                            break
            
            # 提取描述（较长的文本行，通常是第一个较长的文本）
            for line in lines:
                if len(line) > 50 and len(line) < 500:
                    # 排除包含特殊标记的行
                    if not any(marker in line for marker in ['users', 'ratings', 'Sign in', 'Add to Chrome', 'Version', 'Updated']):
                        info['description'] = line[:500]
                        break
            
            # 记录响应
            logger.log_response(url, status_code=200, response_data={'name': info['name'], 'rating': info['rating']})
            
            return info
            
        except Exception as e:
            print(f"    获取详情失败: {e}")
            logger.log_error('PluginDetailError', str(e), {'plugin_id': plugin_id, 'url': url})
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
        
        # 创建列表页
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
            details = await self.get_plugin_details_from_page(detail_page, plugin_id)
            
            if details and details['name']:
                # 填充分类信息
                details['category'] = category
                
                print(f"    名称: {details['name'][:50]}")
                print(f"    分类: {category}")
                print(f"    评分: {details['rating']} | 评论: {details['review_count']} | 用户: {details['install_count']}")
                print(f"    开发者: {details['developer'][:30] if details['developer'] else 'N/A'}")
                print(f"    版本: {details['version'] or 'N/A'} | 更新: {details['last_updated'] or 'N/A'}")
                
                # 获取评论（使用分页爬取所有评论）
                if details['review_count'] > 0:
                    print(f"    正在获取评论...")
                    # 根据评论数量决定是否加载所有评论
                    load_all = details['review_count'] <= 100  # 评论数<=100时加载所有
                    max_reviews = 50 if details['review_count'] > 100 else None
                    reviews = await self.review_crawler.get_reviews(plugin_id, max_reviews=max_reviews, load_all=load_all)
                    print(f"    获取到 {len(reviews)} 条评论")
                    details['reviews'] = reviews
                
                results.append(details)
                
                # 存储到数据库
                try:
                    db_plugin_id = self.db.insert_plugin(details)
                    print(f"    ✓ 已存储插件 (ID: {db_plugin_id})")
                    
                    # 存储评论
                    if 'reviews' in details and details['reviews']:
                        # 转换评论格式
                        db_reviews = []
                        for review in details['reviews']:
                            db_reviews.append({
                                'review_text': review['text'],
                                'rating': review.get('rating', 0),
                                'date': review.get('date', '')
                            })
                        self.db.insert_reviews(db_plugin_id, db_reviews)
                        print(f"    ✓ 已存储 {len(details['reviews'])} 条评论")
                        
                        # 记录爬虫动作
                        logger.log_crawler_action(
                            'plugin_crawled',
                            {
                                'plugin_id': plugin_id,
                                'name': details['name'],
                                'rating': details['rating'],
                                'review_count': len(details['reviews'])
                            }
                        )
                        
                except Exception as e:
                    print(f"    ✗ 存储失败: {e}")
                    logger.log_error('DatabaseError', str(e), {'plugin_id': plugin_id})
            else:
                print(f"    ✗ 获取详情失败")
            
            # 使用反封策略的随机延迟
            anti_block.random_delay()
        
        await detail_page.close()
        return results
    
    async def run(self):
        """
        运行爬虫
        """
        print("="*80)
        print("Chrome插件爬虫 - 可工作版")
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
    crawler = WorkingCrawler()
    await crawler.run()


if __name__ == "__main__":
    asyncio.run(main())
