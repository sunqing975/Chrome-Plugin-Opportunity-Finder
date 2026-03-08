#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品机会生成模块
负责基于评论分析结果生成产品机会，并对机会进行评分
支持DeepSeek、百炼方舟、OpenAI等多个提供商
"""

import sys
import os
import json
import re
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.logger import CrawlerLogger
from storage.db_manager import DBManager


class ProductOpportunityGenerator:
    """
    产品机会生成器类
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        初始化产品机会生成器
        
        Args:
            provider (str, optional): LLM提供商名称
        """
        self.llm_client = LLMClient(provider=provider)
        self.db = DBManager()
        self.logger = CrawlerLogger()
    
    def generate_opportunity_for_plugin(self, plugin_id: int) -> Optional[Dict]:
        """
        为单个插件生成产品机会
        
        Args:
            plugin_id (int): 插件的数据库ID
        
        Returns:
            dict: 产品机会信息
        """
        # 获取插件信息
        plugin = self.db.get_plugin(plugin_id)
        if not plugin:
            print(f"未找到插件ID: {plugin_id}")
            return None
        
        # 获取分析结果
        analysis = self.db.get_analysis_result(plugin_id)
        if not analysis:
            print(f"插件 {plugin['name']} 没有分析结果，请先运行评论分析")
            return None
        
        print(f"\n开始生成产品机会: {plugin['name']}")
        
        # 执行生成
        opportunity = self._generate_with_llm(plugin, analysis)
        
        if opportunity:
            # 存储产品机会
            self.db.insert_opportunity(plugin_id, opportunity)
            # 更新生成状态
            self.db.update_analysis_status(plugin_id, opportunity_generated=True)
            
            print(f"✓ 产品机会生成并保存")
            self.logger.log_llm_call(
                provider=self.llm_client.provider,
                model=self.llm_client.model,
                prompt=f"为插件 {plugin['name']} 生成产品机会",
                response=str(opportunity)[:200]
            )
        
        return opportunity
    
    def _generate_with_llm(self, plugin: Dict, analysis: Dict) -> Optional[Dict]:
        """
        使用LLM生成产品机会
        
        Args:
            plugin (dict): 插件信息
            analysis (dict): 评论分析结果
        
        Returns:
            dict: 产品机会信息
        """
        # 构建分析结果文本
        pain_points = "\n".join([f"  - {point}" for point in analysis.get('pain_points', [])])
        missing_features = "\n".join([f"  - {feature}" for feature in analysis.get('missing_features', [])])
        feature_requests = "\n".join([f"  - {request}" for request in analysis.get('feature_requests', [])])
        improvement_opportunities = "\n".join([f"  - {opportunity}" for opportunity in analysis.get('improvement_opportunities', [])])
        
        analysis_text = f"""
【插件基本信息】
- 名称: {plugin.get('name', '')}
- 分类: {plugin.get('category', '')}
- 评分: {plugin.get('rating', 0)}
- 用户数: {plugin.get('install_count', 0)}
- 评论数: {plugin.get('review_count', 0)}

【用户痛点】
{pain_points if pain_points else '  无'}

【缺失功能】
{missing_features if missing_features else '  无'}

【功能请求】
{feature_requests if feature_requests else '  无'}

【改进机会】
{improvement_opportunities if improvement_opportunities else '  无'}
"""
        
        # 构建prompt
        prompt = f"""你是一个经验丰富的产品经理和创业顾问。基于以下Chrome插件的用户反馈分析，设计一个更好的产品机会。

{analysis_text}

请生成一个创新的产品机会，包含以下维度：

1. **产品想法 (idea)**: 用一句话描述产品核心价值主张
2. **核心功能 (features)**: 列出3-5个关键功能，每个功能用一句话描述
3. **目标用户 (target_users)**: 列出3-5个目标用户群体
4. **商业模式 (business_model)**: 描述如何盈利（如：免费增值、订阅、广告等）
5. **开发难度 (difficulty)**: 评估为"简单"、"中等"或"困难"
6. **市场机会评分 (scores)**:
   - market_demand (1-10): 市场需求程度
   - competition (1-10): 竞争激烈程度（分数越高竞争越小）
   - ease_of_building (1-10): 开发容易程度
   - monetization_potential (1-10): 盈利潜力
   - overall_score (1-10): 综合评分（基于以上四项）
7. **成功因素 (success_factors)**: 列出3-5个关键成功因素
8. **风险提示 (risks)**: 列出2-3个潜在风险

请以JSON格式输出，格式如下：
{{
    "idea": "产品想法",
    "features": ["功能1", "功能2", ...],
    "target_users": ["用户群体1", "用户群体2", ...],
    "business_model": "商业模式描述",
    "difficulty": "简单/中等/困难",
    "scores": {{
        "market_demand": 8,
        "competition": 6,
        "ease_of_building": 7,
        "monetization_potential": 8,
        "overall_score": 7.3
    }},
    "success_factors": ["因素1", "因素2", ...],
    "risks": ["风险1", "风险2", ...]
}}

注意：
- 产品想法要创新且可行
- 评分要客观合理（1-10分）
- 综合评分是四个维度的平均值
- 避免与原插件完全相同，要有所改进"""
        
        try:
            # 调用LLM API
            messages = [
                {
                    "role": "system",
                    "content": "你是一个经验丰富的产品经理和创业顾问，擅长基于用户反馈分析发现产品机会。你的分析应该创新、务实、可执行。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            print(f"  正在调用LLM生成产品机会...")
            response = self.llm_client.chat_completion(messages, max_tokens=2000)
            
            if not response:
                print(f"  ✗ LLM返回空响应")
                return None
            
            # 解析JSON响应
            opportunity = self._parse_llm_response(response, plugin.get('name', ''))
            
            return opportunity
            
        except Exception as e:
            print(f"  ✗ LLM生成失败: {e}")
            self.logger.log_error('LLMGenerationError', str(e), {'plugin_name': plugin.get('name', '')})
            return None
    
    def _parse_llm_response(self, response: str, plugin_name: str) -> Dict:
        """
        解析LLM的JSON响应
        
        Args:
            response (str): LLM响应文本
            plugin_name (str): 插件名称
        
        Returns:
            dict: 解析后的产品机会
        """
        default_result = {
            'idea': f'改进版{plugin_name}',
            'features': [],
            'target_users': [],
            'business_model': '订阅模式',
            'difficulty': '中等',
            'scores': {
                'market_demand': 5,
                'competition': 5,
                'ease_of_building': 5,
                'monetization_potential': 5,
                'overall_score': 5
            },
            'success_factors': [],
            'risks': []
        }
        
        try:
            # 尝试提取JSON部分
            json_block_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_block_match:
                json_str = json_block_match.group(1)
            else:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response
            
            # 清理JSON字符串
            json_str = json_str.strip()
            
            # 解析JSON
            result = json.loads(json_str)
            
            # 确保所有字段都存在
            if 'idea' not in result:
                result['idea'] = default_result['idea']
            if 'features' not in result:
                result['features'] = default_result['features']
            if 'target_users' not in result:
                result['target_users'] = default_result['target_users']
            if 'business_model' not in result:
                result['business_model'] = default_result['business_model']
            if 'difficulty' not in result:
                result['difficulty'] = default_result['difficulty']
            if 'scores' not in result:
                result['scores'] = default_result['scores']
            else:
                # 确保scores中所有字段都存在
                for key in ['market_demand', 'competition', 'ease_of_building', 'monetization_potential', 'overall_score']:
                    if key not in result['scores']:
                        result['scores'][key] = default_result['scores'][key]
            
            # 确保根级别也有overall_score字段（用于数据库存储）
            if 'overall_score' not in result and 'scores' in result:
                result['overall_score'] = result['scores'].get('overall_score', 5)
            elif 'overall_score' not in result:
                result['overall_score'] = default_result['overall_score']
            
            if 'success_factors' not in result:
                result['success_factors'] = default_result['success_factors']
            if 'risks' not in result:
                result['risks'] = default_result['risks']
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON解析失败: {e}")
            return default_result
        
        except Exception as e:
            print(f"  ✗ 解析响应失败: {e}")
            return default_result
    
    def generate_all_pending_plugins(self) -> int:
        """
        为所有待生成机会的插件生成产品机会
        
        Returns:
            int: 成功生成的插件数量
        """
        # 获取所有已分析但未生成机会的插件
        plugins = self.db.get_plugins_by_status(reviews_fetched=True, review_analyzed=True, opportunity_generated=False)
        
        if not plugins:
            print("没有待生成产品机会的插件")
            return 0
        
        print(f"\n{'='*60}")
        print(f"开始批量生成产品机会，共 {len(plugins)} 个插件")
        print(f"{'='*60}")
        
        success_count = 0
        for plugin in plugins:
            result = self.generate_opportunity_for_plugin(plugin['id'])
            if result:
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"批量生成完成: {success_count}/{len(plugins)} 个插件生成成功")
        print(f"{'='*60}")
        
        return success_count
    
    def get_opportunity(self, plugin_id: int) -> Optional[Dict]:
        """
        获取插件的产品机会
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            dict: 产品机会信息
        """
        return self.db.get_opportunity(plugin_id)
    
    def get_top_opportunities(self, limit: int = 10) -> List[Dict]:
        """
        获取评分最高的产品机会
        
        Args:
            limit (int): 返回数量限制
        
        Returns:
            list: 产品机会列表
        """
        return self.db.get_top_opportunities(limit=limit)


# 兼容函数，用于直接调用
def generate_product_opportunity(plugin_id: int, provider: Optional[str] = None) -> Optional[Dict]:
    """
    生成产品机会（兼容函数）
    
    Args:
        plugin_id (int): 插件ID
        provider (str, optional): LLM提供商
    
    Returns:
        dict: 产品机会信息
    """
    generator = ProductOpportunityGenerator(provider=provider)
    return generator.generate_opportunity_for_plugin(plugin_id)


def generate_all_opportunities(provider: Optional[str] = None) -> int:
    """
    生成所有待分析插件的产品机会（兼容函数）
    
    Args:
        provider (str, optional): LLM提供商
    
    Returns:
        int: 成功生成的插件数量
    """
    generator = ProductOpportunityGenerator(provider=provider)
    return generator.generate_all_pending_plugins()
