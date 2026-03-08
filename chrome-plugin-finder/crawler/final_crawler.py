#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版Chrome插件爬虫
使用Selenium直接获取页面元素文本，提取完整信息
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CRAWLER_CONFIG
from storage.db_manager import DBManager


def get_driver():
    """
    获取配置好的WebDriver
    
    Returns:
        WebDriver: 配置好的Chrome WebDriver实例
    """
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


def extract_plugins_from_list(driver):
    """
    从列表页提取插件URL和基本信息
    
    Args:
        driver: Selenium WebDriver实例
    
    Returns:
        list: 包含插件URL和名称的列表
    """
    plugins = []
    
    # 查找所有包含/detail/的链接
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/detail/"]')
    
    for link in links:
        try:
            href = link.get_attribute('href')
            # 获取链接的完整文本内容
            text = link.text.strip()
            
            if href and text and len(text) > 3:
                # 获取第一行作为名称
                name = text.split('\n')[0][:100]
                plugins.append({
                    'url': href,
                    'name': name
                })
        except Exception as e:
            continue
    
    # 去重
    seen_urls = set()
    unique_plugins = []
    for p in plugins:
        if p['url'] not in seen_urls:
            seen_urls.add(p['url'])
            unique_plugins.append(p)
    
    return unique_plugins


def parse_detail_page_text(text):
    """
    解析详情页文本，提取插件信息
    
    Args:
        text: 页面文本内容
    
    Returns:
        dict: 包含插件详细信息的字典
    """
    info = {
        'name': '',
        'description': '',
        'rating': 0.0,
        'review_count': 0,
        'install_count': 0,  # 数据库使用install_count而不是users
        'developer': '',
        'category': ''
    }
    
    # 按行分割
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # 提取名称（通常是第一个有意义的行）
    for line in lines[:20]:
        # 跳过常见的非名称行
        if any(skip in line for skip in ['chrome', '应用商店', '扩展程序', '主题', '登录', '搜索']):
            continue
        if len(line) > 3 and len(line) < 100:
            info['name'] = line
            break
    
    # 提取评分（如 "4.4★" 或 "4★"）
    # 尝试多种评分格式
    rating_patterns = [
        r'(\d+\.\d+)\s*★',  # 4.4★
        r'(\d+)\s*★',        # 4★
        r'评分[:\s]*(\d+\.\d+)',  # 评分: 4.4
        r'(\d+\.\d+)\s*stars?',   # 4.4 stars
    ]
    for pattern in rating_patterns:
        rating_match = re.search(pattern, text, re.IGNORECASE)
        if rating_match:
            info['rating'] = float(rating_match.group(1))
            break
    
    # 提取评论数（如 "163 个评分"）
    review_match = re.search(r'(\d+)\s*个评分', text)
    if review_match:
        info['review_count'] = int(review_match.group(1))
    
    # 提取用户数（如 "8,000,000 用户"）
    user_match = re.search(r'([\d,]+)\s*用户', text)
    if user_match:
        info['install_count'] = int(user_match.group(1).replace(',', ''))
    
    # 提取开发者（查找包含"提供者"或类似关键词的行）
    for line in lines:
        if '提供者' in line or 'Offered by' in line:
            # 提取冒号后的内容
            parts = line.split(':', 1)
            if len(parts) > 1:
                info['developer'] = parts[1].strip()[:100]
            break
    
    # 提取描述（通常是较长的文本行）
    for line in lines:
        if len(line) > 30 and len(line) < 500:
            # 排除包含特殊标记的行
            if not any(marker in line for marker in ['★', '用户', '评分', '提供者']):
                info['description'] = line[:500]
                break
    
    return info


def get_plugin_detail(driver, url):
    """
    获取插件详情页信息
    
    Args:
        driver: Selenium WebDriver实例
        url: 插件详情页URL
    
    Returns:
        dict: 插件详细信息
    """
    driver.get(url)
    time.sleep(3)
    
    # 获取页面body的文本内容
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        text = body.text
        info = parse_detail_page_text(text)
        info['url'] = url
        return info
    except Exception as e:
        print(f"    获取详情失败: {e}")
        return {'url': url, 'name': '', 'description': '', 'rating': 0, 'review_count': 0, 'install_count': 0}


def crawl_category(driver, category, max_plugins=5):
    """
    爬取单个分类的插件
    
    Args:
        driver: Selenium WebDriver实例
        category: 分类名称
        max_plugins: 每个分类最多爬取的插件数量
    
    Returns:
        list: 插件信息列表
    """
    url = f"https://chromewebstore.google.com/category/extensions/{category}?hl=zh-CN"
    print(f"\n{'='*60}")
    print(f"爬取分类: {category}")
    print(f"{'='*60}")
    print(f"访问: {url}")
    
    driver.get(url)
    time.sleep(5)
    
    # 滚动页面加载更多内容
    print("滚动页面加载插件...")
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
    
    # 提取插件列表
    plugins = extract_plugins_from_list(driver)
    print(f"找到 {len(plugins)} 个插件")
    
    # 获取每个插件的详情
    results = []
    for i, plugin in enumerate(plugins[:max_plugins]):
        print(f"\n  [{i+1}/{min(len(plugins), max_plugins)}] 处理: {plugin['name'][:40]}...")
        detail = get_plugin_detail(driver, plugin['url'])
        
        # 合并信息
        if not detail['name']:
            detail['name'] = plugin['name']
        
        print(f"    名称: {detail['name'][:50]}")
        print(f"    评分: {detail['rating']} | 评论: {detail['review_count']} | 用户: {detail['install_count']}")
        
        results.append(detail)
        time.sleep(CRAWLER_CONFIG['sleep_time'])
    
    return results


def main():
    """
    爬虫主函数
    """
    print("="*80)
    print("Chrome插件爬虫 - 最终版")
    print("="*80)
    
    driver = get_driver()
    db = DBManager()
    all_plugins = []
    
    categories = ['productivity', 'marketing', 'SEO']
    
    try:
        for category in categories:
            plugins = crawl_category(driver, category, max_plugins=5)
            all_plugins.extend(plugins)
            
            # 存储到数据库
            for plugin in plugins:
                if plugin['name']:
                    try:
                        plugin_id = db.insert_plugin(plugin)
                        print(f"    ✓ 已存储 (ID: {plugin_id})")
                    except Exception as e:
                        print(f"    ✗ 存储失败: {e}")
        
        # 显示最终结果
        print("\n" + "="*80)
        print("爬取完成！")
        print("="*80)
        print(f"\n共获取 {len(all_plugins)} 个插件\n")
        
        print(f"{'名称':<50} {'评分':<6} {'评论':<6} {'用户':<12}")
        print("-"*80)
        
        for p in all_plugins:
            name = p['name'][:48] if p['name'] else 'N/A'
            rating = p['rating'] if p['rating'] else '-'
            reviews = p['review_count'] if p['review_count'] else '-'
            users = p['install_count'] if p['install_count'] else '-'
            print(f"{name:<50} {rating:<6} {reviews:<6} {users:<12}")
        
    finally:
        driver.quit()
        db.close()


if __name__ == "__main__":
    main()
