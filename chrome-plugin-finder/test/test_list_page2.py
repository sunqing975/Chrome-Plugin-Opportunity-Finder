#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Chrome Web Store列表页结构 - 使用Selenium直接获取元素
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def get_chrome_driver():
    """获取Chrome浏览器驱动"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    
    return driver


def analyze_list_page():
    """分析列表页结构"""
    print("正在分析Chrome Web Store列表页...")
    
    url = "https://chromewebstore.google.com/category/extensions/productivity/tools?hl=zh-CN"
    driver = get_chrome_driver()
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # 滚动页面
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        print(f"页面标题: {driver.title}")
        print()
        
        # 获取所有插件卡片
        # 从截图看，每个插件在一个卡片中，包含图标、名称、评分、描述
        
        # 方法1: 查找所有包含评分符号的元素
        print("方法1: 查找评分元素...")
        rating_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '★')]")
        print(f"  找到 {len(rating_elements)} 个包含★的元素")
        
        for elem in rating_elements[:5]:
            text = elem.text.strip()
            if text:
                print(f"    - {text}")
        
        # 方法2: 获取整个页面的文本内容
        print("\n方法2: 从页面文本中提取信息...")
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # 提取评分 (如 "4.9★")
        ratings = re.findall(r'(\d+\.\d+)\s*★', page_text)
        print(f"  找到 {len(ratings)} 个评分: {ratings[:10]}")
        
        # 提取用户数 (如 "8,000,000 用户")
        users = re.findall(r'([\d,]+)\s*用户', page_text)
        print(f"  找到 {len(users)} 个用户数: {users[:10]}")
        
        # 提取插件名称 - 通常是在评分前面的文本
        print("\n方法3: 查找插件名称...")
        # 查找所有文本节点
        all_texts = driver.find_elements(By.XPATH, "//div[string-length(text()) > 0]")
        print(f"  找到 {len(all_texts)} 个文本元素")
        
        # 过滤出可能是插件名称的文本（长度适中，不包含特殊字符）
        plugin_names = []
        for elem in all_texts[:50]:
            text = elem.text.strip()
            if text and 5 < len(text) < 60 and '★' not in text and '用户' not in text:
                plugin_names.append(text)
        
        print(f"  可能的插件名称 ({len(plugin_names)} 个):")
        for name in plugin_names[:10]:
            print(f"    - {name}")
        
        # 方法4: 通过链接找到插件
        print("\n方法4: 通过链接分析...")
        detail_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/detail/"]')
        print(f"  找到 {len(detail_links)} 个插件链接")
        
        plugins = []
        for link in detail_links[:10]:
            try:
                href = link.get_attribute('href')
                # 获取链接周围的文本（父元素）
                parent = link.find_element(By.XPATH, '..')
                parent_text = parent.text.strip()
                
                if parent_text and len(parent_text) > 10:
                    # 解析文本提取信息
                    lines = parent_text.split('\n')
                    if len(lines) >= 2:
                        plugin_info = {
                            'name': lines[0][:50],
                            'rating': 0,
                            'users': 0,
                            'url': href
                        }
                        
                        # 查找评分
                        for line in lines:
                            rating_match = re.search(r'(\d+\.\d+)\s*★', line)
                            if rating_match:
                                plugin_info['rating'] = float(rating_match.group(1))
                            
                            user_match = re.search(r'([\d,]+)\s*用户', line)
                            if user_match:
                                plugin_info['users'] = int(user_match.group(1).replace(',', ''))
                        
                        plugins.append(plugin_info)
                        print(f"    - {plugin_info['name'][:30]} | 评分:{plugin_info['rating']} | 用户:{plugin_info['users']}")
            except Exception as e:
                continue
        
        print(f"\n成功解析 {len(plugins)} 个插件信息")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    analyze_list_page()
