#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试评论分页结构
"""

import asyncio
from playwright.async_api import async_playwright


async def test_reviews_pagination():
    """
    测试评论分页结构
    """
    plugin_id = "aapbdbdomjkkjkaonfhkkikfgjllcleb"  # Google Translate
    
    # 尝试不同的URL模式
    urls = [
        f"https://chromewebstore.google.com/detail/{plugin_id}/reviews",
        f"https://chromewebstore.google.com/detail/{plugin_id}/reviews?hl=zh-CN",
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for url in urls:
            try:
                print(f"\n{'='*80}")
                print(f"访问: {url}")
                print(f"{'='*80}")
                
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)
                
                # 获取页面HTML
                html = await page.content()
                print(f"HTML长度: {len(html)}")
                
                # 查找分页相关元素
                print("\n查找分页按钮:")
                
                # 查找所有按钮
                buttons = await page.query_selector_all('button')
                print(f"找到 {len(buttons)} 个按钮")
                
                for i, button in enumerate(buttons[:20]):
                    text = await button.inner_text()
                    if text and len(text) < 50:
                        print(f"  按钮{i}: {text.strip()}")
                
                # 查找包含数字的按钮（可能是分页）
                print("\n包含数字的按钮:")
                for i, button in enumerate(buttons):
                    text = await button.inner_text()
                    if text and text.strip().isdigit():
                        print(f"  按钮{i}: {text.strip()}")
                
                # 尝试滚动页面
                print("\n尝试滚动页面...")
                for i in range(3):
                    await page.evaluate('window.scrollBy(0, 1000)')
                    await asyncio.sleep(1)
                    
                    # 检查是否有新内容加载
                    new_html = await page.content()
                    if len(new_html) > len(html):
                        print(f"  滚动{i+1}: 检测到新内容 ({len(new_html) - len(html)} 字符)")
                        html = new_html
                
                # 检查是否有"加载更多"按钮
                print("\n查找'加载更多'按钮:")
                load_more_buttons = await page.query_selector_all('text=/加载更多|Load more|Show more/i')
                print(f"找到 {len(load_more_buttons)} 个加载更多按钮")
                
                for i, btn in enumerate(load_more_buttons):
                    text = await btn.inner_text()
                    print(f"  按钮{i}: {text}")
                    
                    # 尝试点击
                    if i == 0:
                        try:
                            await btn.click()
                            await asyncio.sleep(3)
                            
                            new_html = await page.content()
                            print(f"  点击后HTML长度: {len(new_html)}")
                            print(f"  新增内容: {len(new_html) - len(html)} 字符")
                        except Exception as e:
                            print(f"  点击失败: {e}")
                
            except Exception as e:
                print(f"错误: {e}")
        
        await browser.close()


if __name__ == "__main__":
    print("="*80)
    print("评论分页结构测试")
    print("="*80)
    asyncio.run(test_reviews_pagination())
