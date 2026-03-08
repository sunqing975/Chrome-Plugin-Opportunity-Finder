#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版本和更新时间的提取
"""

import asyncio
import re
from playwright.async_api import async_playwright


async def test_version_update():
    """
    测试版本和更新时间的提取
    """
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
            
            print(f"\n总行数: {len(lines)}")
            
            # 查找包含版本相关关键词的行
            print("\n查找版本相关信息:")
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['version', '版本', 'updated', '更新']):
                    print(f"  行{i}: {line}")
            
            # 尝试不同的版本匹配模式
            print("\n尝试匹配版本号:")
            patterns = [
                r'[Vv]ersion\s+([\d.]+)',
                r'版本\s*[:：]?\s*([\d.]+)',
                r'Version\s*[:：]?\s*([\d.]+)',
                r'v([\d.]+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, body_text)
                if matches:
                    print(f"  模式 '{pattern}': {matches[:3]}")
            
            # 尝试不同的更新时间匹配模式
            print("\n尝试匹配更新时间:")
            update_patterns = [
                r'[Uu]pdated\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'[Uu]pdated\s+([A-Za-z]+\s+\d{1,2})',
                r'更新于\s*(\d{4}年\d{1,2}月\d{1,2}日)',
                r'更新[:：]?\s*(\d{4}-\d{2}-\d{2})',
                r'Updated\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            ]
            
            for pattern in update_patterns:
                matches = re.findall(pattern, body_text)
                if matches:
                    print(f"  模式 '{pattern}': {matches[:3]}")
            
            # 查找包含数字和日期格式的行
            print("\n可能的日期格式:")
            for i, line in enumerate(lines):
                if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}', line):
                    print(f"  行{i}: {line}")
                if re.search(r'\d{4}年\d{1,2}月', line):
                    print(f"  行{i}: {line}")
            
            # 查找包含数字和点号的行（可能是版本号）
            print("\n可能的版本号:")
            for i, line in enumerate(lines):
                if re.search(r'^\d+\.\d+\.?\d*$', line):
                    print(f"  行{i}: {line}")
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


if __name__ == "__main__":
    print("="*80)
    print("版本和更新时间提取测试")
    print("="*80)
    asyncio.run(test_version_update())
