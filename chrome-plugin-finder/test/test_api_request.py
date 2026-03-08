#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API请求
"""

import asyncio
import aiohttp
import re


async def test_api():
    """
    测试API请求
    """
    plugin_id = "fonaoompfjljjllgccccgjnhnoghohgc"
    url = f"https://chromewebstore.google.com/detail/{plugin_id}"
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"请求: {url}")
            async with session.get(url, timeout=10) as response:
                print(f"状态码: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"HTML长度: {len(html)}")
                    
                    # 查找标题
                    title_match = re.search(r'<title>(.*?)</title>', html)
                    if title_match:
                        print(f"标题: {title_match.group(1)}")
                    
                    # 查找评分
                    rating_match = re.search(r'(\d+\.\d+)\s*out of\s*5', html)
                    if rating_match:
                        print(f"评分: {rating_match.group(1)}")
                    else:
                        print("未找到评分")
                    
                    # 查找评论数
                    review_match = re.search(r'(\d+)\s*reviews?', html, re.IGNORECASE)
                    if review_match:
                        print(f"评论数: {review_match.group(1)}")
                    else:
                        print("未找到评论数")
                    
                    # 显示前500字符
                    print(f"\nHTML前500字符:\n{html[:500]}")
                else:
                    print(f"请求失败: {response.status}")
                    
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api())
