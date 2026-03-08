#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试从页面提取JSON数据
"""

import asyncio
import re
import json
from playwright.async_api import async_playwright


async def test_extract_json():
    """
    测试从详情页提取JSON数据
    """
    plugin_id = "aapbdbdomjkkjkaonfhkkikfgjllcleb"
    url = f"https://chromewebstore.google.com/detail/{plugin_id}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"访问: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            # 获取页面HTML
            html = await page.content()
            print(f"\nHTML长度: {len(html)}")
            
            # 查找JSON数据模式
            patterns = [
                r'"detail":\s*(\{[^}]*"name"[^}]*\})',
                r'AF_initDataCallback\((\{.*?\})\);',
                r'data\s*=\s*(\{.*?\});',
                r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
            ]
            
            for i, pattern in enumerate(patterns):
                print(f"\n尝试模式 {i+1}: {pattern[:50]}...")
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    print(f"  找到 {len(matches)} 个匹配")
                    try:
                        data = json.loads(matches[0])
                        print(f"  解析成功!")
                        print(f"  数据类型: {type(data)}")
                        print(f"  前500字符: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                    except json.JSONDecodeError as e:
                        print(f"  JSON解析失败: {e}")
                else:
                    print(f"  未找到匹配")
            
            # 查找所有JSON对象
            print(f"\n查找所有JSON对象...")
            json_pattern = r'\{[^{}]*"[^{}]*"[^{}]*\}'
            json_matches = re.findall(json_pattern, html)
            print(f"  找到 {len(json_matches)} 个可能的JSON对象")
            
            # 显示页面标题
            title = await page.title()
            print(f"\n页面标题: {title}")
            
            # 显示body文本前500字符
            body_text = await page.inner_text('body')
            print(f"\nBody文本前500字符:\n{body_text[:500]}")
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_extract_json())
