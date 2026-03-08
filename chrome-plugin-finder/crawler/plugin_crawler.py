#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome插件爬虫模块
负责从Chrome插件市场抓取插件列表和基本信息
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
    
    Returns:
        webdriver.Chrome: Chrome浏览器驱动实例
    """
    chrome_options = Options()
    if CRAWLER_CONFIG['headless']:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(CRAWLER_CONFIG['timeout'])
    
    return driver


def get_plugin_list(category=None):
    """
    获取插件列表
    
    Args:
        category (str, optional): 插件分类. Defaults to None.
    
    Returns:
        list: 插件URL列表
    """
    plugin_urls = []
    base_url = "https://chromewebstore.google.com"
    
    # 根据分类构建URL
    if category:
        url = f"{base_url}/category/{category}?hl=en"
    else:
        url = f"{base_url}/search?hl=en"
    
    driver = get_chrome_driver()
    
    try:
        driver.get(url)
        time.sleep(CRAWLER_CONFIG['sleep_time'])
        
        # 滚动页面加载更多插件
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(CRAWLER_CONFIG['sleep_time'])
        
        # 解析页面获取插件链接
        # 尝试多种可能的选择器
        selectors = [
            'a[href*="/detail/"]',
            'a[href*="chromewebstore.google.com/detail"]',
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    href = element.get_attribute('href')
                    if href and '/detail/' in href:
                        # 确保URL格式正确
                        if not href.startswith('http'):
                            href = base_url + href
                        plugin_urls.append(href)
            except Exception as e:
                print(f"选择器 {selector} 失败: {e}")
                continue
        
        # 去重
        plugin_urls = list(set(plugin_urls))
        
    except Exception as e:
        print(f"获取插件列表失败: {e}")
    finally:
        driver.quit()
    
    return plugin_urls[:20]  # 限制数量


def get_plugin_info(plugin_url):
    """
    获取插件详细信息
    
    Args:
        plugin_url (str): 插件页面URL
    
    Returns:
        dict: 插件信息字典
    """
    driver = get_chrome_driver()
    plugin_info = {}
    
    try:
        driver.get(plugin_url)
        time.sleep(CRAWLER_CONFIG['sleep_time'])
        
        # 等待页面加载完成
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            pass  # 继续执行
        
        # 提取插件名称 - 使用h1标签
        try:
            name_element = driver.find_element(By.TAG_NAME, 'h1')
            plugin_info['name'] = name_element.text.strip()
        except:
            plugin_info['name'] = ""
        
        # 提取插件描述 - 尝试多种方式
        try:
            # 方法1: 查找包含"description"或"Description"的元素
            desc_selectors = [
                '[class*="description" i]',
                '[class*="Description" i]',
                'div[role="region"]',
            ]
            for selector in desc_selectors:
                try:
                    desc_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_element and len(desc_element.text.strip()) > 20:
                        plugin_info['description'] = desc_element.text.strip()[:500]
                        break
                except:
                    continue
            else:
                plugin_info['description'] = ""
        except:
            plugin_info['description'] = ""
        
        # 提取评分 - 从页面文本中搜索
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            # 查找评分模式 (如 "4.5" 或 "4.5 stars")
            rating_match = re.search(r'(\d+\.\d+)\s*(?:stars?|★)', page_text, re.IGNORECASE)
            if rating_match:
                plugin_info['rating'] = float(rating_match.group(1))
            else:
                plugin_info['rating'] = 0.0
        except:
            plugin_info['rating'] = 0.0
        
        # 提取评论数
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            # 查找评论数模式 (如 "1,234 reviews" 或 "123 reviews")
            review_match = re.search(r'([\d,]+)\s+reviews?', page_text, re.IGNORECASE)
            if review_match:
                review_text = review_match.group(1).replace(',', '')
                plugin_info['review_count'] = int(review_text)
            else:
                plugin_info['review_count'] = 0
        except:
            plugin_info['review_count'] = 0
        
        # 提取安装数
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            # 查找安装数模式 (如 "100,000+ users" 或 "1,000,000+")
            install_match = re.search(r'([\d,]+)\+?\s*(?:users?|installs?)', page_text, re.IGNORECASE)
            if install_match:
                install_text = install_match.group(1).replace(',', '')
                plugin_info['install_count'] = int(install_text)
            else:
                plugin_info['install_count'] = 0
        except:
            plugin_info['install_count'] = 0
        
        # 提取开发者
        try:
            # 尝试从页面文本中提取开发者信息
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            # 查找 "Offered by:" 或 "Developer:" 后面的文本
            dev_match = re.search(r'(?:Offered by|Developer|Publisher)[:\s]+([^\n]+)', page_text, re.IGNORECASE)
            if dev_match:
                plugin_info['developer'] = dev_match.group(1).strip()
            else:
                plugin_info['developer'] = ""
        except:
            plugin_info['developer'] = ""
        
        # 提取分类 - 从URL中推断
        try:
            if '/category/' in plugin_url:
                category = plugin_url.split('/category/')[1].split('/')[0]
                plugin_info['category'] = category.replace('-', ' ').title()
            else:
                plugin_info['category'] = ""
        except:
            plugin_info['category'] = ""
        
        # 添加插件URL
        plugin_info['url'] = plugin_url
        
    except Exception as e:
        print(f"获取插件信息失败 {plugin_url}: {e}")
    finally:
        driver.quit()
    
    return plugin_info


def filter_plugins(plugins):
    """
    根据筛选条件过滤插件
    
    Args:
        plugins (list): 插件信息列表
    
    Returns:
        list: 过滤后的插件列表
    """
    filtered_plugins = []
    
    for plugin in plugins:
        # 检查用户数
        if plugin.get('install_count', 0) < PLUGIN_FILTER['min_users']:
            continue
        
        # 检查评分
        if plugin.get('rating', 0) < PLUGIN_FILTER['min_rating']:
            continue
        
        # 检查评论数
        if plugin.get('review_count', 0) < PLUGIN_FILTER['min_reviews']:
            continue
        
        # 检查分类
        category = plugin.get('category', '').lower()
        if not any(cat.lower() in category for cat in PLUGIN_FILTER['categories']):
            continue
        
        filtered_plugins.append(plugin)
    
    return filtered_plugins


def crawl_plugins():
    """
    爬取插件信息的主函数
    
    Returns:
        list: 符合条件的插件信息列表
    """
    # 初始化数据库管理器
    db = DBManager()
    
    # 按分类爬取插件
    for category in PLUGIN_FILTER['categories']:
        print(f"正在爬取 {category} 分类的插件...")
        plugin_urls = get_plugin_list(category)
        print(f"  找到 {len(plugin_urls)} 个插件URL")
        
        for url in plugin_urls[:20]:  # 每个分类最多爬取20个插件
            try:
                plugin_info = get_plugin_info(url)
                if plugin_info and plugin_info.get('name'):  # 确保有名称才存储
                    # 存储到数据库
                    plugin_id = db.insert_plugin(plugin_info)
                    print(f"  已存储: {plugin_info['name'][:30]}... (评分:{plugin_info.get('rating', 0)}, 用户:{plugin_info.get('install_count', 0)})")
                else:
                    print(f"  跳过: 无法获取插件信息")
            except Exception as e:
                print(f"  处理插件失败: {e}")
            
            time.sleep(CRAWLER_CONFIG['sleep_time'])
    
    # 关闭数据库连接
    db.close()
    
    # 重新连接数据库获取所有插件
    db = DBManager()
    plugins = db.get_plugins()
    db.close()
    
    print(f"\n共找到 {len(plugins)} 个插件")
    
    return plugins


if __name__ == "__main__":
    # 测试爬虫
    print("测试插件爬虫...")
    plugins = crawl_plugins()
    print(f"爬取完成，共 {len(plugins)} 个插件")
