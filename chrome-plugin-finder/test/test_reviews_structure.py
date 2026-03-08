#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试评论页面结构
分析评论在页面上的位置和格式
"""

import asyncio
import re
from playwright.async_api import async_playwright


async def test_reviews_structure():
    """
    测试评论页面结构
    """
    # 使用一个评论较多的插件
    plugin_id = "aapbdbdomjkkjkaonfhkkikfgjllcleb"  # Google Translate
    url = f"https://chromewebstore.google.com/detail/{plugin_id}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"访问: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            # 获取body文本
            body_text = await page.inner_text('body')
            lines = [l.strip() for l in body_text.split('\n') if l.strip()]
            
            # 查找包含"评价"或"review"的行
            print("\n查找评论相关文本:")
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['评价', 'review', 'comment', '评分']):
                    print(f"  行{i}: {line}")
            
            # 查找可能的评论内容（较长的文本，不包含特殊关键词）
            print("\n\n可能的评论内容:")
            comment_candidates = []
            for line in lines:
                # 评论通常是较长的句子，不包含这些关键词
                if len(line) > 30 and len(line) < 500:
                    if not any(keyword in line.lower() for keyword in [
                        'chrome', 'web store', 'extension', 'users', 'ratings',
                        'add to chrome', 'sign in', 'developer', 'privacy'
                    ]):
                        comment_candidates.append(line)
            
            # 显示前10个候选
            for i, comment in enumerate(comment_candidates[:10]):
                print(f"\n候选{i+1}:")
                print(f"  {comment[:100]}...")
            
            # 查找所有按钮文本
            print("\n\n查找按钮:")
            buttons = await page.query_selector_all('button, a')
            for button in buttons[:20]:
                text = await button.inner_text()
                if text and len(text) < 50:
                    print(f"  按钮: {text.strip()}")
            
            # 尝试点击"查看所有评价"
            print("\n\n尝试点击'查看所有评价'...")
            
            # 查找包含"评价"的链接或按钮
            review_links = await page.query_selector_all('text=/评价|reviews/i')
            print(f"找到 {len(review_links)} 个评价相关元素")
            
            for i, link in enumerate(review_links[:5]):
                text = await link.inner_text()
                print(f"  元素{i}: {text}")
                
                # 点击第一个
                if i == 0:
                    try:
                        await link.click()
                        await asyncio.sleep(3)
                        
                        # 获取点击后的页面内容
                        new_body = await page.inner_text('body')
                        print(f"\n点击后页面内容长度: {len(new_body)}")
                        
                        # 查找新的评论
                        new_lines = [l.strip() for l in new_body.split('\n') if l.strip()]
                        print("\n点击后可能的评论:")
                        for line in new_lines[:50]:
                            if len(line) > 30 and len(line) < 300:
                                if not any(keyword in line.lower() for keyword in [
                                    'chrome', 'web store', 'extension', 'users', 'ratings',
                                    'add to chrome', 'sign in'
                                ]):
                                    print(f"  - {line[:80]}...")
                                    
                    except Exception as e:
                        print(f"点击失败: {e}")
                    break
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


if __name__ == "__main__":
    print("="*80)
    print("评论页面结构测试")
    print("="*80)
    asyncio.run(test_reviews_structure())
