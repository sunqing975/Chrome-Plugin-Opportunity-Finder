#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试页面 - 使用非headless模式查看实际页面
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def get_chrome_driver():
    """获取Chrome浏览器驱动（非headless模式）"""
    chrome_options = Options()
    # 不使用headless模式以便查看
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1400,900')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    
    return driver


def debug_page():
    """调试页面"""
    print("正在打开Chrome Web Store...")
    print("请观察浏览器窗口，查看页面是否正确加载")
    print("10秒后将自动关闭\n")
    
    url = "https://chromewebstore.google.com/category/extensions/productivity/tools?hl=zh-CN"
    driver = get_chrome_driver()
    
    try:
        driver.get(url)
        time.sleep(5)
        
        print(f"页面标题: {driver.title}")
        print(f"当前URL: {driver.current_url}")
        
        # 查找页面上的所有div元素
        divs = driver.find_elements(By.TAG_NAME, 'div')
        print(f"\n页面上的div元素数量: {len(divs)}")
        
        # 查找所有a标签
        links = driver.find_elements(By.TAG_NAME, 'a')
        print(f"页面上的a标签数量: {len(links)}")
        
        # 查找包含detail的链接
        detail_links = [l for l in links if '/detail/' in (l.get_attribute('href') or '')]
        print(f"包含/detail/的链接数量: {len(detail_links)}")
        
        # 显示前5个链接的文本
        print("\n前5个插件链接:")
        for link in detail_links[:5]:
            href = link.get_attribute('href')
            text = link.text.strip()[:50]
            print(f"  - {text}")
            print(f"    URL: {href[:80]}...")
        
        # 等待10秒让用户观察
        print("\n等待10秒...")
        time.sleep(10)
        
    finally:
        driver.quit()
        print("\n浏览器已关闭")


if __name__ == "__main__":
    debug_page()
