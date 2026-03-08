#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评论分析模块
负责使用LLM API分析用户评论，提取痛点、缺失功能、改进机会等
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


class CommentAnalyzer:
    """
    评论分析器类
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        初始化评论分析器
        
        Args:
            provider (str, optional): LLM提供商名称
        """
        self.llm_client = LLMClient(provider=provider)
        self.db = DBManager()
        self.logger = CrawlerLogger()
    
    def analyze_plugin_reviews(self, plugin_id: int) -> Optional[Dict]:
        """
        分析单个插件的评论
        
        Args:
            plugin_id (int): 插件的数据库ID
        
        Returns:
            dict: 分析结果，包含痛点、缺失功能、改进机会等
        """
        # 获取插件信息
        plugin = self.db.get_plugin(plugin_id)
        if not plugin:
            print(f"未找到插件ID: {plugin_id}")
            return None
        
        # 获取评论
        reviews = self.db.get_reviews(plugin_id)
        if not reviews:
            print(f"插件 {plugin['name']} 没有评论数据")
            return None
        
        print(f"\n开始分析插件: {plugin['name']}")
        print(f"评论数量: {len(reviews)}")
        
        # 执行分析
        analysis_result = self._analyze_with_llm(plugin['name'], reviews)
        
        if analysis_result:
            # 存储分析结果
            self.db.insert_analysis_result(plugin_id, analysis_result)
            # 更新分析状态
            self.db.update_analysis_status(plugin_id, review_analyzed=True)
            
            print(f"✓ 分析完成并保存")
            self.logger.log_llm_call(
                provider=self.llm_client.provider,
                model=self.llm_client.model,
                prompt=f"分析插件 {plugin['name']} 的评论",
                response=str(analysis_result)[:200]
            )
        
        return analysis_result
    
    def _analyze_with_llm(self, plugin_name: str, reviews: List[Dict]) -> Optional[Dict]:
        """
        使用LLM分析评论
        
        Args:
            plugin_name (str): 插件名称
            reviews (list): 评论列表
        
        Returns:
            dict: 分析结果
        """
        # 构建评论文本（最多分析20条评论）
        review_texts = []
        for i, review in enumerate(reviews[:20]):
            review_text = f"[{i+1}] 评分: {review.get('rating', 'N/A')}\n内容: {review.get('review_text', '')}"
            review_texts.append(review_text)
        
        reviews_str = "\n\n".join(review_texts)
        
        # 构建prompt
        prompt = f"""请分析以下关于 "{plugin_name}" 插件的用户评论，提取关键信息：

{reviews_str}

请从以下维度进行分析：

1. **用户痛点 (Pain Points)**: 用户在使用插件时遇到的主要问题、困扰或不满意的点
2. **缺失功能 (Missing Features)**: 用户期望有但实际没有的功能
3. **功能请求 (Feature Requests)**: 用户明确提出的功能改进建议
4. **改进机会 (Improvement Opportunities)**: 基于评论分析，可以改进产品的具体方向

请以JSON格式输出，格式如下：
{{
    "pain_points": ["痛点1", "痛点2", ...],
    "missing_features": ["缺失功能1", "缺失功能2", ...],
    "feature_requests": ["功能请求1", "功能请求2", ...],
    "improvement_opportunities": ["改进机会1", "改进机会2", ...]
}}

注意：
- 每个类别提取3-5个最重要的点
- 使用简洁的语言描述
- 基于评论内容，不要编造
- 如果没有某类信息，返回空数组"""
        
        try:
            # 调用LLM API
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的产品分析师，擅长分析用户评论并提取有价值的产品洞察。你的分析应该客观、具体、可操作。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            print(f"  正在调用LLM分析...")
            response = self.llm_client.chat_completion(messages, max_tokens=1500)
            
            if not response:
                print(f"  ✗ LLM返回空响应")
                return None
            
            # 解析JSON响应
            analysis_result = self._parse_llm_response(response)
            
            return analysis_result
            
        except Exception as e:
            print(f"  ✗ LLM分析失败: {e}")
            self.logger.log_error('LLMAnalysisError', str(e), {'plugin_name': plugin_name})
            return None
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        解析LLM的JSON响应
        
        Args:
            response (str): LLM响应文本
        
        Returns:
            dict: 解析后的分析结果
        """
        default_result = {
            'pain_points': [],
            'missing_features': [],
            'feature_requests': [],
            'improvement_opportunities': []
        }
        
        try:
            # 尝试提取JSON部分
            # 首先尝试找到JSON代码块
            json_block_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_block_match:
                json_str = json_block_match.group(1)
            else:
                # 尝试找到花括号包裹的内容
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
            for key in default_result.keys():
                if key not in result:
                    result[key] = []
                elif not isinstance(result[key], list):
                    result[key] = [str(result[key])]
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON解析失败: {e}")
            # 尝试从文本中提取信息
            return self._extract_from_text(response)
        
        except Exception as e:
            print(f"  ✗ 解析响应失败: {e}")
            return default_result
    
    def _extract_from_text(self, text: str) -> Dict:
        """
        从非JSON格式的文本中提取信息
        
        Args:
            text (str): 文本内容
        
        Returns:
            dict: 提取的分析结果
        """
        result = {
            'pain_points': [],
            'missing_features': [],
            'feature_requests': [],
            'improvement_opportunities': []
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测章节标题
            lower_line = line.lower()
            if 'pain' in lower_line or '痛点' in line:
                current_section = 'pain_points'
                continue
            elif 'missing' in lower_line or '缺失' in line:
                current_section = 'missing_features'
                continue
            elif 'request' in lower_line or '请求' in line:
                current_section = 'feature_requests'
                continue
            elif 'improvement' in lower_line or '改进' in line or '机会' in line:
                current_section = 'improvement_opportunities'
                continue
            
            # 提取列表项
            if current_section and (line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)):
                item = re.sub(r'^[-*\d.\s]+', '', line).strip()
                if item and len(item) > 5:
                    result[current_section].append(item)
        
        return result
    
    def analyze_all_pending_plugins(self) -> int:
        """
        分析所有待分析的插件
        
        Returns:
            int: 成功分析的插件数量
        """
        # 获取所有已获取评论但未分析的插件
        plugins = self.db.get_plugins_by_status(reviews_fetched=True, review_analyzed=False)
        
        if not plugins:
            print("没有待分析的插件")
            return 0
        
        print(f"\n{'='*60}")
        print(f"开始批量分析，共 {len(plugins)} 个插件")
        print(f"{'='*60}")
        
        success_count = 0
        for plugin in plugins:
            result = self.analyze_plugin_reviews(plugin['id'])
            if result:
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"批量分析完成: {success_count}/{len(plugins)} 个插件分析成功")
        print(f"{'='*60}")
        
        return success_count
    
    def get_analysis_result(self, plugin_id: int) -> Optional[Dict]:
        """
        获取插件的分析结果
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            dict: 分析结果
        """
        return self.db.get_analysis_result(plugin_id)


# 兼容函数，用于直接调用
def analyze_plugin_reviews(plugin_id: int, provider: Optional[str] = None) -> Optional[Dict]:
    """
    分析插件评论（兼容函数）
    
    Args:
        plugin_id (int): 插件ID
        provider (str, optional): LLM提供商
    
    Returns:
        dict: 分析结果
    """
    analyzer = CommentAnalyzer(provider=provider)
    return analyzer.analyze_plugin_reviews(plugin_id)


def analyze_all_pending(provider: Optional[str] = None) -> int:
    """
    分析所有待分析的插件（兼容函数）
    
    Args:
        provider (str, optional): LLM提供商
    
    Returns:
        int: 成功分析的插件数量
    """
    analyzer = CommentAnalyzer(provider=provider)
    return analyzer.analyze_all_pending_plugins()
