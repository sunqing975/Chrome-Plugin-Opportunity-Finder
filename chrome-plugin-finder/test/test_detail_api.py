#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试detail API
"""

import requests
import json

plugin_id = "aapbdbdomjkkjkaonfhkkikfgjllcleb"  # 一个已知的插件ID

# 测试不同的API端点
endpoints = [
    "https://chrome.google.com/webstore/ajax/detail",
    "https://chromewebstore.google.com/webstore/ajax/detail",
    "https://clients2.google.com/webstore/ajax/detail",
]

params = {
    'hl': 'zh-CN',
    'gl': 'CN',
    'pv': '20210820',
    'mce': 'atf,ciif',
    'ids': plugin_id
}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
})

for endpoint in endpoints:
    print(f"\n测试端点: {endpoint}")
    try:
        response = session.get(endpoint, params=params, timeout=10)
        print(f"  状态码: {response.status_code}")
        print(f"  URL: {response.url}")
        
        if response.status_code == 200:
            text = response.text
            print(f"  响应长度: {len(text)}")
            print(f"  前200字符: {text[:200]}")
            
            # 尝试解析
            if text.startswith(")]}'"):
                text = text[4:]
            
            try:
                data = json.loads(text)
                print(f"  解析成功: {type(data)}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"  第一个元素: {json.dumps(data[0], indent=2, ensure_ascii=False)[:500]}")
            except json.JSONDecodeError as e:
                print(f"  JSON解析失败: {e}")
        else:
            print(f"  响应: {response.text[:200]}")
            
    except Exception as e:
        print(f"  错误: {e}")
