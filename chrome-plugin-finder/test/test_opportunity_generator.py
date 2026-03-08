#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试产品机会生成功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.product_opportunity_generator import ProductOpportunityGenerator


def test_generate_opportunity():
    """
    测试单个插件的产品机会生成
    """
    print("="*80)
    print("测试产品机会生成功能")
    print("="*80)
    
    # 创建生成器
    generator = ProductOpportunityGenerator()
    
    # 生成插件ID 1的产品机会
    plugin_id = 1
    
    print(f"\n开始生成产品机会: 插件ID {plugin_id}")
    result = generator.generate_opportunity_for_plugin(plugin_id)
    
    if result:
        print("\n" + "="*80)
        print("产品机会生成结果:")
        print("="*80)
        
        # 显示产品想法
        print(f"\n【产品想法】")
        print(f"  {result.get('idea', '无')}")
        
        # 显示核心功能
        if result.get('features'):
            print(f"\n【核心功能】")
            for i, feature in enumerate(result['features'], 1):
                print(f"  {i}. {feature}")
        
        # 显示目标用户
        if result.get('target_users'):
            print(f"\n【目标用户】")
            for i, user in enumerate(result['target_users'], 1):
                print(f"  {i}. {user}")
        
        # 显示商业模式
        print(f"\n【商业模式】")
        print(f"  {result.get('business_model', '无')}")
        
        # 显示开发难度
        print(f"\n【开发难度】")
        print(f"  {result.get('difficulty', '无')}")
        
        # 显示评分
        scores = result.get('scores', {})
        print(f"\n【评分】")
        print(f"  市场需求: {scores.get('market_demand', 0)}/10")
        print(f"  竞争情况: {scores.get('competition', 0)}/10")
        print(f"  构建难度: {scores.get('ease_of_building', 0)}/10")
        print(f"  盈利潜力: {scores.get('monetization_potential', 0)}/10")
        print(f"  综合评分: {scores.get('overall_score', 0)}/10")
        
        # 显示成功因素
        if result.get('success_factors'):
            print(f"\n【成功因素】")
            for i, factor in enumerate(result['success_factors'], 1):
                print(f"  {i}. {factor}")
        
        # 显示风险
        if result.get('risks'):
            print(f"\n【风险提示】")
            for i, risk in enumerate(result['risks'], 1):
                print(f"  {i}. {risk}")
        
        print("\n" + "="*80)
        print("✓ 产品机会生成完成!")
        print("="*80)
    else:
        print("✗ 产品机会生成失败")


if __name__ == "__main__":
    test_generate_opportunity()
