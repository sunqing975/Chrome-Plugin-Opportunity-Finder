#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Chrome Web Store列表页结构 - 完整信息提取
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
    """分析列表页结构并提取完整信息"""
    print("正在分析Chrome Web Store列表页...")
    
    url = "https://chromewebstore.google.com/category/extensions/productivity/tools?hl=zh-CN"
    driver = get_chrome_driver()
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # 滚动页面加载更多
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        print(f"页面标题: {driver.title}\n")
        
        # 获取所有插件链接
        detail_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/detail/"]')
        print(f"找到 {len(detail_links)} 个插件链接\n")
        
        plugins = []
        seen_urls = set()
        
        for link in detail_links:
            try:
                href = link.get_attribute('href')
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # 获取链接的文本内容
                link_text = link.text.strip()
                
                # 获取祖父元素（包含完整卡片信息）
                try:
                    # 向上查找2-3层父元素
                    grandparent = link
                    for _ in range(3):
                        grandparent = grandparent.find_element(By.XPATH, '..')
                    
                    card_text = grandparent.text.strip()
                except:
                    card_text = link_text
                
                # 解析卡片文本
                lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                
                if len(lines) < 2:
                    continue
                
                plugin_info = {
                    'name': lines[0][:100],
                    'rating': 0.0,
                    'review_count': 0,
                    'users': 0,
                    'description': '',
                    'url': href
                }
                
                # 解析每一行
                for line in lines[1:]:
                    # 查找评分 (如 "4.4★" 或 "4.4 ★")
                    rating_match = re.search(r'(\d+\.\d+)\s*★', line)
                    if rating_match:
                        plugin_info['rating'] = float(rating_match.group(1))
                    
                    # 查找评论数 (如 "(163 个评分)" 或 "163 个评分")
                    review_match = re.search(r'[(]?(\d+)\s*个评分[)]?', line)
                    if review_match:
                        plugin_info['review_count'] = int(review_match.group(1))
                    
                    # 查找用户数 (如 "8,000,000 用户")
                    user_match = re.search(r'([\d,]+)\s*用户', line)
                    if user_match:
                        plugin_info['users'] = int(user_match.group(1).replace(',', ''))
                    
                    # 描述通常是较长的一行
                    if len(line) > 20 and '★' not in line and '用户' not in line and '个评分' not in line:
                        plugin_info['description'] = line[:200]
                
                plugins.append(plugin_info)
                
            except Exception as e:
                continue
        
        # 显示结果
        print(f"成功解析 {len(plugins)} 个插件信息:\n")
        print(f"{'名称':<40} {'评分':<6} {'评论':<6} {'用户':<12} {'描述':<30}")
        print("=" * 100)
        
        for plugin in plugins[:15]:
            name = plugin['name'][:38]
            rating = plugin['rating']
            reviews = plugin['review_count']
            users = plugin['users']
            desc = plugin['description'][:28]
            print(f"{name:<40} {rating:<6} {reviews:<6} {users:<12} {desc:<30}")
        
        return plugins
        
    finally:
        driver.quit()


if __name__ == "__main__":
    analyze_list_page()
