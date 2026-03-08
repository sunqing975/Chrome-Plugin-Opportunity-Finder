#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统模块
记录爬虫请求、返回值、大模型调用等信息
"""

import logging
import json
import os
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional


class CrawlerLogger:
    """
    爬虫日志类
    """
    
    def __init__(self, log_dir='logs'):
        """
        初始化日志系统
        
        Args:
            log_dir (str): 日志目录
        """
        self.log_dir = log_dir
        self._ensure_log_dir()
        
        # 创建不同级别的日志记录器
        self.crawler_logger = self._setup_logger('crawler', 'crawler.log')
        self.request_logger = self._setup_logger('request', 'request.log')
        self.response_logger = self._setup_logger('response', 'response.log')
        self.llm_logger = self._setup_logger('llm', 'llm.log')
        self.error_logger = self._setup_logger('error', 'error.log')
    
    def _ensure_log_dir(self):
        """
        确保日志目录存在
        """
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        """
        设置日志记录器
        
        Args:
            name (str): 日志记录器名称
            filename (str): 日志文件名
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, filename),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_request(self, url: str, method: str = 'GET', 
                   params: Optional[Dict] = None, 
                   headers: Optional[Dict] = None,
                   data: Optional[Dict] = None):
        """
        记录HTTP请求
        
        Args:
            url (str): 请求URL
            method (str): 请求方法
            params (Dict): 请求参数
            headers (Dict): 请求头
            data (Dict): 请求数据
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'method': method,
            'params': params,
            'headers': self._sanitize_headers(headers),
            'data': data
        }
        self.request_logger.info(json.dumps(log_data, ensure_ascii=False, indent=2))
    
    def log_response(self, url: str, status_code: int, 
                     response_data: Optional[Any] = None,
                     response_time: float = 0.0):
        """
        记录HTTP响应
        
        Args:
            url (str): 请求URL
            status_code (int): 状态码
            response_data (Any): 响应数据
            response_time (float): 响应时间（秒）
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'status_code': status_code,
            'response_time': response_time,
            'response_data': self._truncate_data(response_data)
        }
        self.response_logger.info(json.dumps(log_data, ensure_ascii=False, indent=2))
    
    def log_llm_call(self, provider: str, model: str, 
                    prompt: str, response: str,
                    tokens_used: Optional[int] = None,
                    cost: Optional[float] = None):
        """
        记录大模型调用
        
        Args:
            provider (str): 服务提供商（deepseek, bailing等）
            model (str): 模型名称
            prompt (str): 提示词
            response (str): 响应内容
            tokens_used (int): 使用的token数
            cost (float): 成本
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'model': model,
            'prompt': prompt,
            'response': response,
            'tokens_used': tokens_used,
            'cost': cost
        }
        self.llm_logger.info(json.dumps(log_data, ensure_ascii=False, indent=2))
    
    def log_crawler_action(self, action: str, details: Dict):
        """
        记录爬虫动作
        
        Args:
            action (str): 动作名称
            details (Dict): 详细信息
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        self.crawler_logger.info(json.dumps(log_data, ensure_ascii=False, indent=2))
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Optional[Dict] = None):
        """
        记录错误
        
        Args:
            error_type (str): 错误类型
            error_message (str): 错误信息
            context (Dict): 上下文信息
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context
        }
        self.error_logger.error(json.dumps(log_data, ensure_ascii=False, indent=2))
    
    def _sanitize_headers(self, headers: Optional[Dict]) -> Optional[Dict]:
        """
        清理敏感的请求头信息
        
        Args:
            headers (Dict): 原始请求头
            
        Returns:
            Dict: 清理后的请求头
        """
        if not headers:
            return None
        
        sensitive_keys = ['authorization', 'cookie', 'api-key', 'x-api-key']
        sanitized = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = '***REDACTED***'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _truncate_data(self, data: Any, max_length: int = 1000) -> Any:
        """
        截断过长的数据
        
        Args:
            data (Any): 原始数据
            max_length (int): 最大长度
            
        Returns:
            Any: 截断后的数据
        """
        if isinstance(data, str):
            if len(data) > max_length:
                return data[:max_length] + '...[TRUNCATED]'
        elif isinstance(data, (dict, list)):
            data_str = json.dumps(data, ensure_ascii=False)
            if len(data_str) > max_length:
                return data_str[:max_length] + '...[TRUNCATED]'
        
        return data


# 全局日志实例
logger = CrawlerLogger()


def log_function_call(logger_instance: CrawlerLogger):
    """
    函数调用日志装饰器
    
    Args:
        logger_instance (CrawlerLogger): 日志实例
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger_instance.log_crawler_action(
                f'function_call:{func_name}',
                {
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }
            )
            try:
                result = func(*args, **kwargs)
                logger_instance.log_crawler_action(
                    f'function_success:{func_name}',
                    {'result': str(result)[:200]}
                )
                return result
            except Exception as e:
                logger_instance.log_error(
                    f'function_error:{func_name}',
                    str(e),
                    {'args': str(args)[:200], 'kwargs': str(kwargs)[:200]}
                )
                raise
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试日志系统
    print("测试日志系统...")
    
    # 测试请求日志
    logger.log_request(
        url='https://example.com/api',
        method='GET',
        params={'page': 1},
        headers={'User-Agent': 'Test', 'Authorization': 'secret'}
    )
    
    # 测试响应日志
    logger.log_response(
        url='https://example.com/api',
        status_code=200,
        response_data={'data': 'test'},
        response_time=1.5
    )
    
    # 测试LLM日志
    logger.log_llm_call(
        provider='deepseek',
        model='deepseek-chat',
        prompt='分析这个评论',
        response='这是一个很好的评论',
        tokens_used=100,
        cost=0.01
    )
    
    # 测试爬虫动作日志
    logger.log_crawler_action(
        'crawl_plugin',
        {'plugin_id': 'test123', 'name': 'Test Plugin'}
    )
    
    # 测试错误日志
    logger.log_error(
        'ConnectionError',
        '无法连接到服务器',
        {'url': 'https://example.com'}
    )
    
    print("日志已写入 logs/ 目录")
