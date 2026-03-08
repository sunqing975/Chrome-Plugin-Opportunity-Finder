#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接访问评论页面
Chrome Web Store的评论通常在/detail/ID/reviews路径
"""

import asyncio
import re
from playwright.async_api import async_playwright


async def test_reviews_direct():
    """
    直接访问评论页面
    """
    plugin_id = "aapbdbdomjkkjkaonfhkkikfgjllcleb"  # Google Translate
    
    # 尝试不同的评论页面URL
    urls = [
        f"https://chromewebstore.google.com/detail/{plugin_id}/reviews",
        f"https://chromewebstore.google.com/detail/{plugin_id}?hl=zh-CN#reviews",
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for url in urls:
            page = await browser.new_page()
            
            try:
                print(f"\n{'='*80}")
                print(f"访问: {url}")
                print(f"{'='*80}")
                
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)
                
                # 获取body文本
                body_text = await page.inner_text('body')
                lines = [l.strip() for l in body_text.split('\n') if l.strip()]
                
                print(f"页面内容长度: {len(body_text)}")
                print(f"总行数: {len(lines)}")
                
                # 查找可能的评论
                print("\n可能的评论内容:")
                comments = []
                for line in lines:
                    # 评论特征：较长文本，不包含特定关键词
                    if len(line) > 40 and len(line) < 500:
                        if not any(keyword in line.lower() for keyword in [
                            'chrome', 'web store', 'extension', 'add to chrome',
                            'sign in', 'developer', 'privacy', 'learn more',
                            'google translate', 'users', 'ratings'
                        ]):
                            comments.append(line)
                
                # 显示前15个
                for i, comment in enumerate(comments[:15]):
                    print(f"\n评论{i+1}:")
                    print(f"  {comment[:150]}...")
                
                # 查找包含"review"或"评价"的上下文
                print("\n\n包含'review'或'评价'的行:")
                for i, line in enumerate(lines):
                    if 'review' in line.lower() or '评价' in line:
                        # 显示前后几行
                        context = []
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            context.append(f"  {j}: {lines[j][:80]}")
                        print(f"\n位置{i}:")
                        print('\n'.join(context))
                        
            except Exception as e:
                print(f"错误: {e}")
            finally:
                await page.close()
        
        await browser.close()


if __name__ == "__main__":
    print("="*80)
    print("直接访问评论页面测试")
    print("="*80)
    asyncio.run(test_reviews_direct())
