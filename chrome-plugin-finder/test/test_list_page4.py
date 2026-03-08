#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Chrome Web Store列表页结构 - 使用JavaScript获取内容
"""

import time
import re
import json
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
        
        print(f"页面标题: {driver.title}\n")
        
        # 使用JavaScript获取所有包含插件信息的元素
        script = """
        const plugins = [];
        const links = document.querySelectorAll('a[href*="/detail/"]');
        
        links.forEach(link => {
            const href = link.href;
            if (!href.includes('/detail/')) return;
            
            // 获取链接文本
            const text = link.innerText || link.textContent;
            if (!text || text.trim().length < 5) return;
            
            // 获取父元素
            let parent = link.parentElement;
            let cardText = text;
            
            // 向上查找3层，获取卡片完整文本
            for (let i = 0; i < 3 && parent; i++) {
                const parentText = parent.innerText || parent.textContent;
                if (parentText && parentText.length > cardText.length) {
                    cardText = parentText;
                }
                parent = parent.parentElement;
            }
            
            plugins.push({
                url: href,
                text: text.trim(),
                cardText: cardText.trim()
            });
        });
        
        return JSON.stringify(plugins);
        """
        
        result = driver.execute_script(script)
        plugins_data = json.loads(result)
        
        print(f"找到 {len(plugins_data)} 个插件\n")
        
        # 解析每个插件的信息
        plugins = []
        seen_urls = set()
        
        for data in plugins_data[:20]:
            url = data['url']
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            card_text = data['cardText']
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                continue
            
            plugin_info = {
                'name': lines[0][:100],
                'rating': 0.0,
                'review_count': 0,
                'users': 0,
                'description': '',
                'url': url
            }
            
            # 解析每一行
            for line in lines[1:]:
                # 评分
                rating_match = re.search(r'(\d+\.\d+)\s*★', line)
                if rating_match:
                    plugin_info['rating'] = float(rating_match.group(1))
                
                # 评论数
                review_match = re.search(r'[(]?(\d+)\s*个评分[)]?', line)
                if review_match:
                    plugin_info['review_count'] = int(review_match.group(1))
                
                # 用户数
                user_match = re.search(r'([\d,]+)\s*用户', line)
                if user_match:
                    plugin_info['users'] = int(user_match.group(1).replace(',', ''))
                
                # 描述
                if len(line) > 15 and '★' not in line and '用户' not in line and '个评分' not in line:
                    if not plugin_info['description']:
                        plugin_info['description'] = line[:200]
            
            plugins.append(plugin_info)
        
        # 显示结果
        print(f"成功解析 {len(plugins)} 个插件:\n")
        print(f"{'名称':<45} {'评分':<6} {'评论':<6} {'用户':<12}")
        print("=" * 75)
        
        for plugin in plugins[:15]:
            name = plugin['name'][:43]
            rating = plugin['rating'] if plugin['rating'] > 0 else '-'
            reviews = plugin['review_count'] if plugin['review_count'] > 0 else '-'
            users = plugin['users'] if plugin['users'] > 0 else '-'
            print(f"{name:<45} {rating:<6} {reviews:<6} {users:<12}")
        
        # 显示详细信息
        print("\n\n详细信息 (前5个):")
        print("=" * 75)
        for plugin in plugins[:5]:
            print(f"\n名称: {plugin['name']}")
            print(f"评分: {plugin['rating']}")
            print(f"评论数: {plugin['review_count']}")
            print(f"用户数: {plugin['users']}")
            print(f"描述: {plugin['description'][:100]}...")
            print(f"URL: {plugin['url'][:80]}...")
            print("-" * 75)
        
        return plugins
        
    finally:
        driver.quit()


if __name__ == "__main__":
    analyze_list_page()
