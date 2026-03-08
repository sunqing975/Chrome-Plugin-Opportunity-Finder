#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评论爬虫模块
从Chrome Web Store评论页面提取评论内容
支持分页爬取所有评论
"""

import asyncio
import re
import sys
import os
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.anti_block import anti_block


class ReviewCrawler:
    """
    评论爬虫类
    """
    
    def __init__(self):
        """
        初始化评论爬虫
        """
        pass
    
    async def get_reviews(self, plugin_id, max_reviews=None, load_all=False):
        """
        获取插件评论
        
        Args:
            plugin_id: 插件ID
            max_reviews: 最大获取评论数，None表示获取所有
            load_all: 是否加载所有评论（通过点击Load more）
            
        Returns:
            list: 评论列表，每个评论包含text和rating
        """
        reviews = []
        url = f"https://chromewebstore.google.com/detail/{plugin_id}/reviews"
        
        logger.log_crawler_action(
            'start_fetch_reviews',
            {
                'plugin_id': plugin_id,
                'max_reviews': max_reviews,
                'load_all': load_all
            }
        )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # 访问评论页面
                logger.log_request(url, method='GET')
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)
                
                # 如果需要加载所有评论，不断点击Load more
                if load_all:
                    await self._load_all_reviews(page, max_reviews)
                
                # 获取body文本
                body_text = await page.inner_text('body')
                lines = [l.strip() for l in body_text.split('\n') if l.strip()]
                
                # 提取评论
                reviews = self._extract_reviews_from_lines(lines, max_reviews)
                
                logger.log_response(
                    url,
                    status_code=200,
                    response_data={'review_count': len(reviews)},
                    response_time=0
                )
                
            except Exception as e:
                logger.log_error(
                    'ReviewFetchError',
                    str(e),
                    {'plugin_id': plugin_id, 'url': url}
                )
            finally:
                await browser.close()
        
        logger.log_crawler_action(
            'finish_fetch_reviews',
            {
                'plugin_id': plugin_id,
                'review_count': len(reviews)
            }
        )
        
        return reviews
    
    async def _load_all_reviews(self, page, max_reviews=None):
        """
        通过点击Load more按钮加载所有评论
        
        Args:
            page: Playwright Page对象
            max_reviews: 最大评论数限制
        """
        max_clicks = 20  # 最多点击20次，防止无限循环
        click_count = 0
        
        while click_count < max_clicks:
            # 查找Load more按钮
            load_more_buttons = await page.query_selector_all('text=/Load more|加载更多/i')
            
            if not load_more_buttons:
                # 没有更多按钮了
                break
            
            # 点击第一个Load more按钮
            try:
                await load_more_buttons[0].click()
                click_count += 1
                
                # 随机延迟
                delay = anti_block.random_delay()
                
                # 检查是否达到最大评论数
                if max_reviews:
                    body_text = await page.inner_text('body')
                    lines = [l.strip() for l in body_text.split('\n') if l.strip()]
                    current_reviews = self._extract_reviews_from_lines(lines, max_reviews)
                    if len(current_reviews) >= max_reviews:
                        break
                
                logger.log_crawler_action(
                    'load_more_reviews',
                    {
                        'click_count': click_count,
                        'delay': delay
                    }
                )
                
            except Exception as e:
                logger.log_error(
                    'LoadMoreError',
                    str(e),
                    {'click_count': click_count}
                )
                break
    
    def _extract_reviews_from_lines(self, lines, max_reviews=None):
        """
        从文本行中提取评论
        
        Args:
            lines: 文本行列表
            max_reviews: 最大评论数
            
        Returns:
            list: 评论列表
        """
        reviews = []
        
        # 评论特征：
        # 1. 长度在40-500字符之间
        # 2. 不包含特定关键词（如chrome, web store等）
        # 3. 通常是完整的句子
        
        excluded_keywords = [
            'chrome', 'web store', 'extension', 'add to chrome',
            'sign in', 'developer', 'privacy', 'learn more',
            'users', 'ratings', 'gordon house', 'barrow street',
            'dublin', 'this developer', 'eu', 'trader',
            'filter by', 'sort by', 'all reviews', 'load more',
            '加载更多', '筛选', '排序', '所有评价'
        ]
        
        for line in lines:
            # 检查长度
            if len(line) < 40 or len(line) > 500:
                continue
            
            # 检查是否包含排除关键词
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in excluded_keywords):
                continue
            
            # 检查是否是完整句子（以标点符号结尾）
            if not line[-1] in '.。!！?？':
                # 如果不是，可能是句子的一部分，也接受
                pass
            
            # 这是一个可能的评论
            reviews.append({
                'text': line,
                'rating': 0  # 暂时无法获取单个评论的评分
            })
            
            # 检查是否达到最大评论数
            if max_reviews and len(reviews) >= max_reviews:
                break
        
        return reviews


async def test_review_crawler():
    """
    测试评论爬虫
    """
    print("="*80)
    print("评论爬虫测试")
    print("="*80)
    
    crawler = ReviewCrawler()
    
    # 测试获取所有评论
    plugin_id = "aapbdbdomjkkjkaonfhkkikfgjllcleb"  # Google Translate
    
    print(f"\n获取插件 {plugin_id} 的所有评论...")
    reviews = await crawler.get_reviews(plugin_id, max_reviews=None, load_all=True)
    
    print(f"获取到 {len(reviews)} 条评论\n")
    
    # 显示前10条评论
    for i, review in enumerate(reviews[:10], 1):
        print(f"评论{i}:")
        print(f"  {review['text'][:150]}...")
        print()


# 兼容函数，用于main.py导入
def crawl_reviews(plugin_ids=None, db_manager=None, max_reviews_per_plugin=50):
    """
    爬取评论（兼容函数）
    
    Args:
        plugin_ids: 插件ID列表，None表示爬取所有插件的评论
        db_manager: 数据库管理器
        max_reviews_per_plugin: 每个插件最大评论数
    """
    async def _crawl():
        crawler = ReviewCrawler()
        
        # 如果没有指定plugin_ids，从数据库获取
        if plugin_ids is None and db_manager:
            cursor = db_manager.conn.cursor()
            cursor.execute('SELECT id, url FROM plugins')
            plugins = cursor.fetchall()
            plugin_ids = [p[1].split('/')[-1] for p in plugins]
        
        if not plugin_ids:
            print("没有需要爬取评论的插件")
            return
        
        print(f"开始爬取 {len(plugin_ids)} 个插件的评论...")
        
        for plugin_id in plugin_ids:
            print(f"\n爬取插件 {plugin_id} 的评论...")
            reviews = await crawler.get_reviews(
                plugin_id, 
                max_reviews=max_reviews_per_plugin,
                load_all=False
            )
            print(f"获取到 {len(reviews)} 条评论")
            
            # 存储到数据库
            if db_manager and reviews:
                # 获取插件的数据库ID
                cursor = db_manager.conn.cursor()
                cursor.execute('SELECT id FROM plugins WHERE url LIKE ?', (f'%{plugin_id}%',))
                result = cursor.fetchone()
                
                if result:
                    db_plugin_id = result[0]
                    db_reviews = [{
                        'review_text': r['text'],
                        'rating': r.get('rating', 0),
                        'date': r.get('date', '')
                    } for r in reviews]
                    db_manager.insert_reviews(db_plugin_id, db_reviews)
                    print(f"已存储 {len(reviews)} 条评论到数据库")
    
    asyncio.run(_crawl())


if __name__ == "__main__":
    asyncio.run(test_review_crawler())
