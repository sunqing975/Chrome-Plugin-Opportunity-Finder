#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品机会生成模块
负责基于评论分析结果生成产品机会，并对机会进行评分
支持DeepSeek、百炼方舟、OpenAI等多个提供商
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from storage.db_manager import DBManager


def generate_opportunity(plugin_name, analysis):
    """
    基于评论分析结果生成产品机会
    
    Args:
        plugin_name (str): 插件名称
        analysis (dict): 评论分析结果
    
    Returns:
        dict: 产品机会信息
    """
    # 构建分析结果文本
    pain_points = "\n".join([f"- {point}" for point in analysis.get('pain_points', [])])
    missing_features = "\n".join([f"- {feature}" for feature in analysis.get('missing_features', [])])
    feature_requests = "\n".join([f"- {request}" for request in analysis.get('feature_requests', [])])
    improvement_opportunities = "\n".join([f"- {opportunity}" for opportunity in analysis.get('improvement_opportunities', [])])
    
    analysis_text = f"""
    插件名称: {plugin_name}
    
    用户痛点:
    {pain_points}
    
    缺失功能:
    {missing_features}
    
    用户请求的功能:
    {feature_requests}
    
    改进机会:
    {improvement_opportunities}
    """
    
    # 构建prompt
    prompt = f"""
    基于以下插件的用户评论分析结果，生成一个更好的产品想法：
    
    {analysis_text}
    
    请生成：
    1. 产品想法（product idea）
    2. 核心功能（core features）
    3. 目标用户（target users）
    4. 商业模式（business model）
    5. 开发难度（difficulty）
    6. 市场需求评分（1-10）
    7. 竞争情况评分（1-10）
    8. 构建难度评分（1-10）
    9. 盈利潜力评分（1-10）
    10. 综合评分（1-10）
    
    请以JSON格式输出，包含以下字段：
    - idea: 产品想法
    - features: 核心功能列表
    - target_users: 目标用户列表
    - business_model: 商业模式
    - difficulty: 开发难度
    - scores: 包含各维度评分的字典
    - overall_score: 综合评分
    """
    
    try:
        # 初始化LLM客户端
        llm_client = LLMClient()
        
        # 调用LLM API
        messages = [
            {"role": "system", "content": "你是一个专业的产品经理，擅长基于用户反馈生成创新的产品想法。"},
            {"role": "user", "content": prompt}
        ]
        
        opportunity = llm_client.chat_completion(messages, max_tokens=1500)
        
        # 提取JSON部分
        import json
        import re
        
        json_match = re.search(r'\{[\s\S]*\}', opportunity)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认格式
                return {
                    'idea': f"改进版{plugin_name}",
                    'features': [],
                    'target_users': [],
                    'business_model': "订阅模式",
                    'difficulty': "中等",
                    'scores': {
                        'market_demand': 5,
                        'competition': 5,
                        'ease_of_building': 5,
                        'monetization_potential': 5
                    },
                    'overall_score': 5
                }
        else:
            # 如果没有找到JSON，返回默认格式
            return {
                'idea': f"改进版{plugin_name}",
                'features': [],
                'target_users': [],
                'business_model': "订阅模式",
                'difficulty': "中等",
                'scores': {
                    'market_demand': 5,
                    'competition': 5,
                    'ease_of_building': 5,
                    'monetization_potential': 5
                },
                'overall_score': 5
            }
    
    except Exception as e:
        print(f"生成产品机会时出错: {e}")
        return {
            'idea': f"改进版{plugin_name}",
            'features': [],
            'target_users': [],
            'business_model': "订阅模式",
            'difficulty': "中等",
            'scores': {
                'market_demand': 5,
                'competition': 5,
                'ease_of_building': 5,
                'monetization_potential': 5
            },
            'overall_score': 5
        }


def generate_opportunities(plugins):
    """
    为多个插件生成产品机会
    
    Args:
        plugins (list): 插件信息列表
    
    Returns:
        list: 包含产品机会的插件信息列表
    """
    # 初始化数据库管理器
    db = DBManager()
    
    for plugin in plugins:
        print(f"正在为 {plugin['name']} 生成产品机会...")
        
        # 从数据库读取分析结果
        plugin_id = plugin.get('id')
        analysis = db.get_analysis_result(plugin_id) if plugin_id else plugin.get('analysis', {})
        
        # 生成产品机会
        opportunity = generate_opportunity(plugin['name'], analysis)
        
        # 存储产品机会到数据库
        if plugin_id:
            db.insert_opportunity(plugin_id, opportunity)
            print(f"已存储产品机会")
        
        plugin['opportunity'] = opportunity
    
    # 关闭数据库连接
    db.close()
    
    # 按综合评分排序
    plugins.sort(key=lambda x: x['opportunity'].get('overall_score', 0), reverse=True)
    
    return plugins
