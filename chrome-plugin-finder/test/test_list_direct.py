#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试列表页内容提取
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


def test_list_page():
    """测试列表页"""
    url = "https://chromewebstore.google.com/category/extensions/productivity?hl=zh-CN"
    
    driver = get_driver()
    try:
        print(f"访问: {url}")
        driver.get(url)
        time.sleep(5)
        
        # 滚动页面
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
        
        # 获取页面文本
        body = driver.find_element(By.TAG_NAME, 'body')
        text = body.text
        
        print("\n页面文本前3000字符:")
        print(text[:3000])
        print("\n" + "="*80)
        
        # 搜索评分相关文本
        print("\n搜索包含★的行:")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '★' in line:
                print(f"  行{i}: {line.strip()}")
        
        # 搜索包含"用户"的行
        print("\n搜索包含'用户'的行:")
        for i, line in enumerate(lines):
            if '用户' in line:
                print(f"  行{i}: {line.strip()}")
        
        # 搜索包含"评分"的行
        print("\n搜索包含'评分'的行:")
        for i, line in enumerate(lines):
            if '评分' in line:
                print(f"  行{i}: {line.strip()}")
        
        # 查找所有数字
        print("\n查找所有数字模式:")
        numbers = re.findall(r'\d+\.?\d*', text)
        print(f"  找到 {len(numbers)} 个数字: {numbers[:30]}")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    test_list_page()
