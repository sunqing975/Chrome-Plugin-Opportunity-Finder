#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试评论分析功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.comment_analyzer import CommentAnalyzer


def test_analyze_plugin():
    """
    测试单个插件的评论分析
    """
    print("="*80)
    print("测试评论分析功能")
    print("="*80)
    
    # 创建分析器
    analyzer = CommentAnalyzer()
    
    # 分析插件ID 1
    plugin_id = 1
    
    print(f"\n开始分析插件ID: {plugin_id}")
    result = analyzer.analyze_plugin_reviews(plugin_id)
    
    if result:
        print("\n" + "="*80)
        print("分析结果:")
        print("="*80)
        
        # 显示痛点
        if result.get('pain_points'):
            print("\n【用户痛点】")
            for i, point in enumerate(result['pain_points'], 1):
                print(f"  {i}. {point}")
        
        # 显示缺失功能
        if result.get('missing_features'):
            print("\n【缺失功能】")
            for i, feature in enumerate(result['missing_features'], 1):
                print(f"  {i}. {feature}")
        
        # 显示功能请求
        if result.get('feature_requests'):
            print("\n【功能请求】")
            for i, request in enumerate(result['feature_requests'], 1):
                print(f"  {i}. {request}")
        
        # 显示改进机会
        if result.get('improvement_opportunities'):
            print("\n【改进机会】")
            for i, opportunity in enumerate(result['improvement_opportunities'], 1):
                print(f"  {i}. {opportunity}")
        
        print("\n" + "="*80)
        print("✓ 分析完成!")
        print("="*80)
    else:
        print("✗ 分析失败")


if __name__ == "__main__":
    test_analyze_plugin()
