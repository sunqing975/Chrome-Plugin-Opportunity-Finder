#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反封策略模块
提供随机延迟、User-Agent轮换等反封策略
"""

import random
import time
from typing import List, Optional
from fake_useragent import UserAgent


class AntiBlockStrategy:
    """
    反封策略类
    """
    
    # 常用的User-Agent列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """
        初始化反封策略
        
        Args:
            min_delay (float): 最小延迟时间（秒）
            max_delay (float): 最大延迟时间（秒）
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.ua = UserAgent()
    
    def random_delay(self, extra_delay: float = 0.0):
        """
        随机延迟
        
        Args:
            extra_delay (float): 额外延迟时间（秒）
        """
        delay = random.uniform(self.min_delay, self.max_delay) + extra_delay
        time.sleep(delay)
        return delay
    
    def get_random_user_agent(self) -> str:
        """
        获取随机User-Agent
        
        Returns:
            str: User-Agent字符串
        """
        try:
            # 优先使用fake_useragent
            return self.ua.random
        except:
            # 如果失败，使用预设列表
            return random.choice(self.USER_AGENTS)
    
    def get_random_headers(self, base_headers: Optional[dict] = None) -> dict:
        """
        获取随机请求头
        
        Args:
            base_headers (dict): 基础请求头
            
        Returns:
            dict: 包含随机User-Agent的请求头
        """
        headers = base_headers.copy() if base_headers else {}
        headers['User-Agent'] = self.get_random_user_agent()
        return headers
    
    def exponential_backoff(self, attempt: int, base_delay: float = 1.0, 
                           max_delay: float = 60.0):
        """
        指数退避策略
        
        Args:
            attempt (int): 重试次数
            base_delay (float): 基础延迟时间
            max_delay (float): 最大延迟时间
            
        Returns:
            float: 实际延迟时间
        """
        delay = min(base_delay * (2 ** attempt), max_delay)
        # 添加随机抖动
        jitter = random.uniform(0, delay * 0.1)
        time.sleep(delay + jitter)
        return delay + jitter
    
    def adaptive_delay(self, success_rate: float, base_delay: float = 2.0):
        """
        自适应延迟策略
        
        Args:
            success_rate (float): 成功率（0-1）
            base_delay (float): 基础延迟时间
            
        Returns:
            float: 实际延迟时间
        """
        # 成功率越低，延迟越长
        if success_rate > 0.9:
            delay = base_delay * 0.5
        elif success_rate > 0.7:
            delay = base_delay
        elif success_rate > 0.5:
            delay = base_delay * 2
        else:
            delay = base_delay * 4
        
        # 添加随机性
        delay = random.uniform(delay * 0.8, delay * 1.2)
        time.sleep(delay)
        return delay


class RequestLimiter:
    """
    请求限流器
    """
    
    def __init__(self, max_requests_per_minute: int = 30):
        """
        初始化请求限流器
        
        Args:
            max_requests_per_minute (int): 每分钟最大请求数
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times = []
    
    def wait_if_needed(self):
        """
        如果需要，等待以符合限流要求
        """
        current_time = time.time()
        
        # 移除超过1分钟的请求记录
        self.request_times = [
            t for t in self.request_times 
            if current_time - t < 60
        ]
        
        # 如果达到限制，等待
        if len(self.request_times) >= self.max_requests_per_minute:
            oldest_request = min(self.request_times)
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                time.sleep(wait_time)
        
        # 记录当前请求
        self.request_times.append(current_time)


# 全局反封策略实例
anti_block = AntiBlockStrategy(min_delay=2.0, max_delay=5.0)
request_limiter = RequestLimiter(max_requests_per_minute=30)


if __name__ == "__main__":
    # 测试反封策略
    print("测试反封策略...")
    
    # 测试随机延迟
    print("\n1. 测试随机延迟:")
    for i in range(3):
        delay = anti_block.random_delay()
        print(f"  延迟{i+1}: {delay:.2f}秒")
    
    # 测试随机User-Agent
    print("\n2. 测试随机User-Agent:")
    for i in range(3):
        ua = anti_block.get_random_user_agent()
        print(f"  UA{i+1}: {ua[:80]}...")
    
    # 测试指数退避
    print("\n3. 测试指数退避:")
    for i in range(5):
        delay = anti_block.exponential_backoff(i)
        print(f"  重试{i+1}: 延迟{delay:.2f}秒")
    
    # 测试自适应延迟
    print("\n4. 测试自适应延迟:")
    for success_rate in [0.95, 0.8, 0.6, 0.4]:
        delay = anti_block.adaptive_delay(success_rate)
        print(f"  成功率{success_rate}: 延迟{delay:.2f}秒")
    
    print("\n测试完成！")
