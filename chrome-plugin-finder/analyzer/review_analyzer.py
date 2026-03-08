#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM评论分析模块
负责使用LLM API分析用户评论，提取痛点和改进机会
支持DeepSeek、百炼方舟、OpenAI等多个提供商
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from storage.db_manager import DBManager


def analyze_reviews(plugin_name, reviews):
    """
    分析插件的用户评论
    
    Args:
        plugin_name (str): 插件名称
        reviews (list): 评论列表
    
    Returns:
        dict: 分析结果
    """
    if not reviews:
        return {
            'pain_points': [],
            'missing_features': [],
            'feature_requests': [],
            'improvement_opportunities': []
        }
    
    # 构建评论文本
    review_texts = []
    for review in reviews:
        review_text = f"Rating: {review['rating']}\nText: {review['review_text']}"
        review_texts.append(review_text)
    
    reviews_str = "\n\n".join(review_texts[:10])  # 最多分析10条评论
    
    # 构建prompt
    prompt = f"""
    分析以下关于 {plugin_name} 插件的用户评论：
    
    {reviews_str}
    
    请提取：
    1. 最常见的用户痛点（pain points）
    2. 缺失的功能（missing features）
    3. 用户请求的功能（feature requests）
    4. 改进机会（improvement opportunities）
    
    请以JSON格式输出，包含以下字段：
    - pain_points: 痛点列表
    - missing_features: 缺失功能列表
    - feature_requests: 功能请求列表
    - improvement_opportunities: 改进机会列表
    """
    
    try:
        # 初始化LLM客户端
        llm_client = LLMClient()
        
        # 调用LLM API
        messages = [
            {"role": "system", "content": "你是一个专业的产品分析师，擅长分析用户评论并提取有价值的信息。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = llm_client.chat_completion(messages, max_tokens=1000)
        
        # 提取JSON部分
        import json
        import re
        
        json_match = re.search(r'\{[\s\S]*\}', analysis)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认格式
                return {
                    'pain_points': [],
                    'missing_features': [],
                    'feature_requests': [],
                    'improvement_opportunities': []
                }
        else:
            # 如果没有找到JSON，返回默认格式
            return {
                'pain_points': [],
                'missing_features': [],
                'feature_requests': [],
                'improvement_opportunities': []
            }
    
    except Exception as e:
        print(f"分析评论时出错: {e}")
        return {
            'pain_points': [],
            'missing_features': [],
            'feature_requests': [],
            'improvement_opportunities': []
        }


def analyze_plugins(plugins):
    """
    分析多个插件的评论
    
    Args:
        plugins (list): 插件信息列表
    
    Returns:
        list: 包含分析结果的插件信息列表
    """
    # 初始化数据库管理器
    db = DBManager()
    
    for plugin in plugins:
        print(f"正在分析 {plugin['name']} 的评论...")
        
        # 从数据库读取评论
        plugin_id = plugin.get('id')
        reviews = db.get_reviews(plugin_id) if plugin_id else plugin.get('reviews', [])
        
        # 分析评论
        analysis = analyze_reviews(plugin['name'], reviews)
        
        # 存储分析结果到数据库
        if plugin_id:
            db.insert_analysis_result(plugin_id, analysis)
            print(f"已存储分析结果")
        
        plugin['analysis'] = analysis
    
    # 关闭数据库连接
    db.close()
    
    return plugins
