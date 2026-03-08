#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能爬虫 - 使用多种策略提取Chrome Web Store数据
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
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CRAWLER_CONFIG


def get_driver():
    """获取配置好的WebDriver"""
    options = Options()
    if CRAWLER_CONFIG['headless']:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def extract_plugins_from_page(driver):
    """从当前页面提取所有插件信息"""
    plugins = []
    
    # 策略1: 通过链接查找
    links = driver.find_elements(By.TAG_NAME, 'a')
    for link in links:
        try:
            href = link.get_attribute('href')
            if href and '/detail/' in href:
                # 获取链接文本
                text = link.text.strip()
                if text and len(text) > 3:
                    plugins.append({
                        'url': href,
                        'name': text.split('\n')[0][:100]
                    })
        except:
            continue
    
    # 去重
    seen = set()
    unique = []
    for p in plugins:
        if p['url'] not in seen:
            seen.add(p['url'])
            unique.append(p)
    
    return unique


def get_plugin_details(driver, url):
    """获取插件详情"""
    driver.get(url)
    time.sleep(3)
    
    info = {'name': '', 'rating': 0, 'users': 0, 'reviews': 0}
    
    # 获取所有文本
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        text = body.text
        
        # 提取名称（通常是第一个非空行）
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:10]:
            if len(line) > 3 and len(line) < 100 and '★' not in line:
                info['name'] = line
                break
        
        # 提取评分
        rating_match = re.search(r'(\d+\.\d+)\s*★', text)
        if rating_match:
            info['rating'] = float(rating_match.group(1))
        
        # 提取用户数
        user_match = re.search(r'([\d,]+)\s*用户', text)
        if user_match:
            info['users'] = int(user_match.group(1).replace(',', ''))
        
        # 提取评论数
        review_match = re.search(r'(\d+)\s*个评分', text)
        if review_match:
            info['reviews'] = int(review_match.group(1))
            
    except Exception as e:
        print(f"提取详情失败: {e}")
    
    return info


def crawl_category(driver, category):
    """爬取单个分类"""
    url = f"https://chromewebstore.google.com/category/extensions/{category}?hl=zh-CN"
    print(f"\n访问: {url}")
    
    driver.get(url)
    time.sleep(5)
    
    # 滚动加载
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
    
    # 提取插件
    plugins = extract_plugins_from_page(driver)
    print(f"找到 {len(plugins)} 个插件")
    
    # 获取前5个插件的详情
    results = []
    for i, plugin in enumerate(plugins[:5]):
        print(f"  [{i+1}/5] {plugin['name'][:40]}...")
        details = get_plugin_details(driver, plugin['url'])
        plugin.update(details)
        results.append(plugin)
        time.sleep(2)
    
    return results


def main():
    """主函数"""
    print("="*80)
    print("Chrome插件智能爬虫")
    print("="*80)
    
    driver = get_driver()
    all_plugins = []
    
    categories = ['productivity', 'marketing', 'SEO']
    
    try:
        for category in categories:
            plugins = crawl_category(driver, category)
            all_plugins.extend(plugins)
            print(f"分类 {category} 完成，获取 {len(plugins)} 个插件")
    finally:
        driver.quit()
    
    # 显示结果
    print("\n" + "="*80)
    print("爬取结果")
    print("="*80)
    print(f"{'名称':<45} {'评分':<6} {'用户':<12} {'评论':<6}")
    print("-"*80)
    
    for p in all_plugins:
        name = p['name'][:43] if p['name'] else 'N/A'
        rating = p['rating'] if p['rating'] else '-'
        users = p['users'] if p['users'] else '-'
        reviews = p['reviews'] if p['reviews'] else '-'
        print(f"{name:<45} {rating:<6} {users:<12} {reviews:<6}")
    
    print(f"\n总计: {len(all_plugins)} 个插件")


if __name__ == "__main__":
    main()
