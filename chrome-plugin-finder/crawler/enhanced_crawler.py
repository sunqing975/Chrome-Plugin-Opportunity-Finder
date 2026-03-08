#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Chrome插件爬虫
使用Selenium直接获取页面元素文本，提取完整信息
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

from config import PLUGIN_FILTER, CRAWLER_CONFIG
from storage.db_manager import DBManager


def get_chrome_driver():
    """
    获取Chrome浏览器驱动
    """
    chrome_options = Options()
    if CRAWLER_CONFIG['headless']:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    
    # 执行JavaScript隐藏webdriver属性
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def get_plugin_cards_from_list(driver, category_url):
    """
    从列表页获取所有插件卡片信息
    
    Args:
        driver: Selenium WebDriver
        category_url: 分类页面URL
    
    Returns:
        list: 插件信息列表
    """
    print(f"正在访问: {category_url}")
    driver.get(category_url)
    
    # 等待页面加载
    time.sleep(5)
    
    # 滚动页面加载更多插件
    print("滚动页面加载插件...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    # 获取所有插件卡片
    print("提取插件信息...")
    
    # 使用JavaScript获取所有插件信息
    script = """
    const plugins = [];
    
    // 查找所有可能包含插件信息的容器
    const containers = document.querySelectorAll('div, article, section');
    
    containers.forEach(container => {
        // 查找包含插件链接的元素
        const links = container.querySelectorAll('a[href*="/detail/"]');
        
        links.forEach(link => {
            const href = link.href;
            if (!href || !href.includes('/detail/')) return;
            
            // 获取容器内所有文本
            const text = container.innerText || container.textContent;
            if (!text || text.length < 10) return;
            
            // 检查是否包含评分符号（★）
            if (text.includes('★')) {
                plugins.push({
                    url: href,
                    cardText: text.trim()
                });
            }
        });
    });
    
    // 去重
    const uniquePlugins = [];
    const seenUrls = new Set();
    plugins.forEach(p => {
        if (!seenUrls.has(p.url)) {
            seenUrls.add(p.url);
            uniquePlugins.push(p);
        }
    });
    
    return uniquePlugins;
    """
    
    try:
        result = driver.execute_script(script)
        print(f"找到 {len(result)} 个插件卡片")
        return result
    except Exception as e:
        print(f"执行JavaScript失败: {e}")
        return []


def parse_plugin_card(card_text, url):
    """
    解析插件卡片文本，提取信息
    
    Args:
        card_text: 卡片文本内容
        url: 插件URL
    
    Returns:
        dict: 插件信息
    """
    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
    
    if len(lines) < 2:
        return None
    
    plugin_info = {
        'name': lines[0][:100],
        'description': '',
        'rating': 0.0,
        'review_count': 0,
        'users': 0,
        'url': url
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
        
        # 描述通常是较长的一行，不包含特殊标记
        if len(line) > 15 and '★' not in line and '用户' not in line and '个评分' not in line:
            if not plugin_info['description']:
                plugin_info['description'] = line[:500]
    
    return plugin_info


def get_plugin_detail_info(driver, plugin_url):
    """
    从详情页获取插件详细信息
    
    Args:
        driver: Selenium WebDriver
        plugin_url: 插件详情页URL
    
    Returns:
        dict: 插件详细信息
    """
    print(f"  访问详情页: {plugin_url[:60]}...")
    driver.get(plugin_url)
    time.sleep(3)
    
    plugin_info = {
        'name': '',
        'description': '',
        'rating': 0.0,
        'review_count': 0,
        'users': 0,
        'developer': '',
        'category': '',
        'url': plugin_url
    }
    
    try:
        # 使用JavaScript提取页面信息
        script = """
        const info = {};
        
        // 获取页面标题
        info.pageTitle = document.title;
        
        // 获取h1标签（通常是插件名称）
        const h1 = document.querySelector('h1');
        info.name = h1 ? h1.innerText.trim() : '';
        
        // 获取页面所有文本
        info.pageText = document.body.innerText;
        
        // 查找开发者信息
        const devElements = document.querySelectorAll('*');
        for (let elem of devElements) {
            const text = elem.innerText || elem.textContent;
            if (text && text.includes('提供者') || text.includes('Developer') || text.includes('Offered by')) {
                info.developerHint = text.trim();
                break;
            }
        }
        
        return info;
        """
        
        result = driver.execute_script(script)
        
        # 解析名称
        if result.get('name'):
            plugin_info['name'] = result['name'][:100]
        
        # 从页面文本中提取信息
        page_text = result.get('pageText', '')
        
        # 提取评分
        rating_match = re.search(r'(\d+\.\d+)\s*★', page_text)
        if rating_match:
            plugin_info['rating'] = float(rating_match.group(1))
        
        # 提取评论数
        review_match = re.search(r'(\d+)\s*个评分', page_text)
        if review_match:
            plugin_info['review_count'] = int(review_match.group(1))
        
        # 提取用户数
        user_match = re.search(r'([\d,]+)\s*用户', page_text)
        if user_match:
            plugin_info['users'] = int(user_match.group(1).replace(',', ''))
        
        # 提取描述（通常是较长的文本块）
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]
        for line in lines:
            if len(line) > 50 and len(line) < 500 and '★' not in line:
                plugin_info['description'] = line[:500]
                break
        
        # 提取开发者
        if result.get('developerHint'):
            dev_text = result['developerHint']
            dev_match = re.search(r'(?:提供者|Developer|Offered by)[:\s]+([^\n]+)', dev_text, re.IGNORECASE)
            if dev_match:
                plugin_info['developer'] = dev_match.group(1).strip()[:100]
        
        # 从URL提取分类
        if '/category/' in plugin_url:
            category = plugin_url.split('/category/')[1].split('/')[0]
            plugin_info['category'] = category.replace('-', ' ').title()
        
    except Exception as e:
        print(f"    提取详情失败: {e}")
    
    return plugin_info


def crawl_plugins_enhanced():
    """
    增强版爬虫主函数
    """
    print("=" * 80)
    print("开始爬取Chrome插件信息（增强版）")
    print("=" * 80)
    
    db = DBManager()
    driver = get_chrome_driver()
    
    try:
        total_plugins = 0
        
        for category in PLUGIN_FILTER['categories']:
            print(f"\n{'='*80}")
            print(f"正在爬取分类: {category}")
            print(f"{'='*80}")
            
            category_url = f"https://chromewebstore.google.com/category/extensions/{category}?hl=zh-CN"
            
            # 从列表页获取插件卡片
            cards = get_plugin_cards_from_list(driver, category_url)
            print(f"找到 {len(cards)} 个插件")
            
            # 解析每个插件
            for i, card in enumerate(cards[:10]):  # 每个分类最多处理10个
                try:
                    print(f"\n[{i+1}/{min(len(cards), 10)}] 处理插件...")
                    
                    # 先尝试从列表页解析
                    plugin_info = parse_plugin_card(card['cardText'], card['url'])
                    
                    if plugin_info and plugin_info['name']:
                        print(f"  列表页获取: {plugin_info['name'][:40]}")
                        print(f"    评分: {plugin_info['rating']}, 评论: {plugin_info['review_count']}, 用户: {plugin_info['users']}")
                        
                        # 如果列表页数据不完整，进入详情页补充
                        if plugin_info['rating'] == 0 or plugin_info['users'] == 0:
                            print(f"  列表页数据不完整，进入详情页...")
                            detail_info = get_plugin_detail_info(driver, card['url'])
                            
                            # 合并信息（优先使用列表页的数据，如果存在）
                            if detail_info['name']:
                                plugin_info['name'] = detail_info['name']
                            if detail_info['rating'] > 0:
                                plugin_info['rating'] = detail_info['rating']
                            if detail_info['review_count'] > 0:
                                plugin_info['review_count'] = detail_info['review_count']
                            if detail_info['users'] > 0:
                                plugin_info['users'] = detail_info['users']
                            if detail_info['description']:
                                plugin_info['description'] = detail_info['description']
                            plugin_info['developer'] = detail_info['developer']
                            plugin_info['category'] = detail_info['category']
                        
                        # 存储到数据库
                        plugin_id = db.insert_plugin(plugin_info)
                        print(f"  ✓ 已存储到数据库 (ID: {plugin_id})")
                        total_plugins += 1
                        
                    time.sleep(CRAWLER_CONFIG['sleep_time'])
                    
                except Exception as e:
                    print(f"  ✗ 处理失败: {e}")
                    continue
        
        print(f"\n{'='*80}")
        print(f"爬取完成！共存储 {total_plugins} 个插件")
        print(f"{'='*80}")
        
    finally:
        driver.quit()
        db.close()


if __name__ == "__main__":
    crawl_plugins_enhanced()
