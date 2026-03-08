#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM客户端模块
支持多个LLM提供商：DeepSeek、百炼方舟、OpenAI
"""

import os
import openai
from dotenv import load_dotenv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_CONFIG

# 加载环境变量
load_dotenv()


class LLMClient:
    """
    LLM客户端类，支持多个LLM提供商
    """
    
    def __init__(self, provider=None):
        """
        初始化LLM客户端
        
        Args:
            provider (str, optional): LLM提供商. Defaults to None.
        """
        self.provider = provider or LLM_CONFIG.get('provider', 'deepseek')
        self.config = LLM_CONFIG.get(self.provider, {})
        
        # 设置API密钥
        api_key = self.config.get('api_key')
        if not api_key or api_key.startswith('your_'):
            # 尝试从环境变量获取
            env_key = f"{self.provider.upper()}_API_KEY"
            api_key = os.getenv(env_key)
        
        self.api_key = api_key
        self.base_url = self.config.get('base_url')
        self.model = self.config.get('model')
        self.temperature = self.config.get('temperature', 0.7)
        
        # 初始化OpenAI客户端
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat_completion(self, messages, max_tokens=1000):
        """
        调用LLM进行对话
        
        Args:
            messages (list): 消息列表
            max_tokens (int): 最大token数
        
        Returns:
            str: LLM响应内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"调用{self.provider} API时出错: {e}")
            return ""
    
    def get_provider_info(self):
        """
        获取提供商信息
        
        Returns:
            dict: 提供商信息
        """
        return {
            'provider': self.provider,
            'model': self.model,
            'base_url': self.base_url
        }
