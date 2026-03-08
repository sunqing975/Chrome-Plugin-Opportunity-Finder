#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试爬虫脚本
用于验证Chrome插件市场的页面结构
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_chrome_driver():
    """获取Chrome浏览器驱动"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    
    return driver


def test_plugin_page():
    """测试插件详情页"""
    print("正在测试插件详情页...")
    
    # 测试一个已知的插件URL
    test_url = "https://chromewebstore.google.com/detail/grammarly-ai-writing-assi/kbfnbcaeplbcioakkpcpgfkobkghlhen"
    
    driver = get_chrome_driver()
    
    try:
        driver.get(test_url)
        time.sleep(5)  # 等待页面完全加载
        
        print("\n页面标题:", driver.title)
        print("\n查找插件名称...")
        
        # 尝试多种可能的选择器
        selectors = [
            'h1',
            '[role="heading"]',
            'header h1',
            '[class*="title"]',
        ]
        
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    print(f"  选择器 '{selector}' 找到: {element.text.strip()[:50]}")
            except:
                print(f"  选择器 '{selector}' 未找到")
        
        # 获取页面源码
        page_source = driver.page_source
        
        # 查找包含插件名称的文本
        print("\n在页面源码中搜索 'Grammarly'...")
        if 'Grammarly' in page_source:
            print("  找到 'Grammarly' 文本")
        
        # 保存页面源码用于分析
        with open('test_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("\n页面源码已保存到 test_page.html")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    test_plugin_page()
