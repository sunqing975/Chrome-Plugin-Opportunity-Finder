#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的版本和更新时间提取
"""

import asyncio
import re
from playwright.async_api import async_playwright


async def test_fixed_extraction():
    """
    测试修复后的版本和更新时间提取
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
            
            info = {
                'version': '',
                'last_updated': ''
            }
            
            # 提取版本号
            for i, line in enumerate(lines):
                if line.lower() == 'version' or line == '版本':
                    if i + 1 < len(lines):
                        version_line = lines[i + 1]
                        version_match = re.search(r'^[\d.]+$', version_line)
                        if version_match:
                            info['version'] = version_line[:20]
                            break
            
            # 提取更新日期
            for i, line in enumerate(lines):
                if line.lower() == 'updated' or line == '更新':
                    if i + 1 < len(lines):
                        update_line = lines[i + 1]
                        date_match = re.search(r'^([A-Za-z]+\s+\d{1,2},?\s+\d{4})$', update_line)
                        if date_match:
                            info['last_updated'] = date_match.group(1)
                            break
                        date_match_cn = re.search(r'^(\d{4}年\d{1,2}月\d{1,2}日)$', update_line)
                        if date_match_cn:
                            info['last_updated'] = date_match_cn.group(1)
                            break
            
            print(f"\n提取结果:")
            print(f"  版本号: {info['version'] or '未提取到'}")
            print(f"  更新时间: {info['last_updated'] or '未提取到'}")
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


if __name__ == "__main__":
    print("="*80)
    print("修复后的版本和更新时间提取测试")
    print("="*80)
    asyncio.run(test_fixed_extraction())
