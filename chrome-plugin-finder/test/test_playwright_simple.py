#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Playwright测试 - 不使用stealth
"""

import asyncio
import re
from playwright.async_api import async_playwright


async def test_get_plugin_ids():
    """
    测试从分类页面获取插件ID
    """
    url = "https://chromewebstore.google.com/category/extensions/productivity?hl=zh-CN"
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f"访问: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 滚动页面
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                print(f"  滚动 {i+1}/3")
            
            # 获取所有插件链接
            print("\n获取插件链接...")
            links = await page.query_selector_all('a[href*="/detail/"]')
            print(f"找到 {len(links)} 个链接")
            
            # 提取插件信息
            plugins = []
            seen_ids = set()
            
            for link in links[:10]:
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    # 提取插件ID - Chrome Web Store ID通常是24个字符
                    # URL格式: https://chromewebstore.google.com/detail/name/ID
                    match = re.search(r'/detail/[^/]+/([a-z]{24,32})', href)
                    if match:
                        plugin_id = match.group(1)
                        
                        if plugin_id in seen_ids:
                            continue
                        seen_ids.add(plugin_id)
                        
                        # 获取文本
                        text = await link.inner_text()
                        name = text.split('\n')[0][:50] if text else 'Unknown'
                        
                        plugins.append({
                            'id': plugin_id,
                            'name': name,
                            'url': href
                        })
                except Exception as e:
                    continue
            
            # 显示结果
            print(f"\n成功提取 {len(plugins)} 个插件:\n")
            print(f"{'ID':<30} {'名称':<50}")
            print("-" * 85)
            
            for p in plugins[:10]:
                print(f"{p['id']:<30} {p['name']:<50}")
                
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


if __name__ == "__main__":
    print("="*85)
    print("Playwright简化版测试")
    print("="*85)
    asyncio.run(test_get_plugin_ids())
