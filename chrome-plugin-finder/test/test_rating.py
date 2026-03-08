#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试评分提取
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def get_driver():
    """获取WebDriver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def test_rating_extraction():
    """测试评分提取"""
    url = "https://chromewebstore.google.com/detail/web-highlights/lblnbldkfhllndlndfnbnkfndmnllogj?hl=zh-CN"
    
    driver = get_driver()
    try:
        print(f"访问: {url}")
        driver.get(url)
        time.sleep(5)
        
        # 获取页面文本
        body = driver.find_element(By.TAG_NAME, 'body')
        text = body.text
        
        print("\n页面文本前2000字符:")
        print(text[:2000])
        print("\n" + "="*80)
        
        # 搜索评分相关文本
        print("\n搜索评分模式...")
        
        # 查找包含★的行
        lines = text.split('\n')
        for i, line in enumerate(lines[:50]):
            if '★' in line or '星' in line or '评分' in line:
                print(f"  行{i}: {line.strip()}")
        
        # 测试各种正则表达式
        print("\n测试正则表达式:")
        
        patterns = [
            r'(\d+\.\d+)\s*★',
            r'(\d+)\s*★',
            r'评分[:\s]*(\d+\.\d+)',
            r'(\d+\.\d+)\s*stars?',
            r'(\d+\.\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"  模式 '{pattern}': {matches[:5]}")
        
        # 查找数字后面跟着中文字符的模式
        print("\n查找数字+中文字符:")
        chinese_pattern = r'(\d+\.?\d*)\s*([\u4e00-\u9fff]+)'
        matches = re.findall(chinese_pattern, text)
        for num, char in matches[:20]:
            print(f"  {num} {char}")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    test_rating_extraction()
