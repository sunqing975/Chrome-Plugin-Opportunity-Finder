#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Chrome Web Store列表页结构
"""

import time
import re
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
    # 不使用headless模式以便调试
    # chrome_options.add_argument('--headless')
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
    
    # 使用中文语言环境
    url = "https://chromewebstore.google.com/category/extensions/productivity/tools?hl=zh-CN"
    driver = get_chrome_driver()
    
    try:
        driver.get(url)
        
        # 等待页面加载完成
        print("等待页面加载...")
        time.sleep(8)
        
        # 滚动页面以加载更多内容
        print("滚动页面加载内容...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        print(f"\n页面标题: {driver.title}")
        
        # 查找所有插件卡片
        print("\n查找插件卡片...")
        
        # 尝试多种可能的选择器
        card_selectors = [
            'div[role="listitem"]',
            'div[class*="item"]',
            'div[class*="card"]',
            'a[href*="/detail/"]',
        ]
        
        for selector in card_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  选择器 '{selector}' 找到 {len(elements)} 个元素")
                
                if elements and len(elements) > 5:
                    # 分析第一个元素
                    first = elements[0]
                    text = first.text
                    print(f"    第一个元素文本预览: {text[:300]}")
                    
                    # 查找链接
                    links = first.find_elements(By.TAG_NAME, 'a')
                    if links:
                        for link in links[:2]:
                            href = link.get_attribute('href')
                            if href and '/detail/' in href:
                                print(f"    插件链接: {href}")
                                break
                    
                    break
            except Exception as e:
                print(f"  选择器 '{selector}' 失败: {e}")
        
        # 从页面文本中搜索评分模式
        print("\n从页面文本中搜索评分信息...")
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # 查找评分模式 (如 "4.4 ★" 或 "4.4 stars")
        rating_pattern = r'(\d+\.\d+)\s*[★☆]'
        ratings = re.findall(rating_pattern, page_text)
        print(f"  找到 {len(ratings)} 个评分: {ratings[:10]}")
        
        # 查找用户数模式 (如 "8,000,000 用户")
        user_pattern = r'([\d,]+)\s*用户'
        users = re.findall(user_pattern, page_text)
        print(f"  找到 {len(users)} 个用户数: {users[:10]}")
        
        # 查找评论数模式 (如 "163 个评分")
        review_pattern = r'(\d+)\s*个评分'
        reviews = re.findall(review_pattern, page_text)
        print(f"  找到 {len(reviews)} 个评论数: {reviews[:10]}")
        
        # 查找插件名称
        print("\n查找插件名称...")
        # 尝试找到所有插件标题
        title_selectors = [
            'h3',
            '[class*="title"]',
            'a[href*="/detail/"]',
        ]
        
        for selector in title_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  选择器 '{selector}' 找到 {len(elements)} 个元素")
                    for elem in elements[:5]:
                        text = elem.text.strip()
                        if text and len(text) < 100:  # 过滤掉过长的文本
                            print(f"    - {text[:50]}")
                    break
            except:
                continue
        
        # 保存页面截图
        driver.save_screenshot('list_page.png')
        print("\n页面截图已保存到 list_page.png")
        
        # 保存页面源码
        with open('list_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("页面源码已保存到 list_page.html")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    analyze_list_page()
