#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库中的产品机会数据
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db_manager import DBManager


def test_opportunity_db():
    """
    测试数据库中的产品机会
    """
    print("="*80)
    print("检查数据库中的产品机会")
    print("="*80)
    
    db = DBManager()
    
    # 获取插件ID 1的产品机会
    plugin_id = 1
    opportunity = db.get_opportunity(plugin_id)
    
    if opportunity:
        print(f"\n插件ID: {plugin_id}")
        print(f"\n原始数据:")
        print(json.dumps(opportunity, indent=2, ensure_ascii=False))
        
        print(f"\n\n解析后的数据:")
        print(f"产品想法: {opportunity.get('idea', 'N/A')}")
        print(f"核心功能数量: {len(opportunity.get('features', []))}")
        print(f"目标用户数量: {len(opportunity.get('target_users', []))}")
        print(f"商业模式: {opportunity.get('business_model', 'N/A')}")
        print(f"开发难度: {opportunity.get('difficulty', 'N/A')}")
        
        scores = opportunity.get('scores', {})
        if isinstance(scores, str):
            try:
                scores = json.loads(scores)
            except:
                scores = {}
        
        print(f"\n评分:")
        print(f"  市场需求: {scores.get('market_demand', 'N/A')}")
        print(f"  竞争情况: {scores.get('competition', 'N/A')}")
        print(f"  构建难度: {scores.get('ease_of_building', 'N/A')}")
        print(f"  盈利潜力: {scores.get('monetization_potential', 'N/A')}")
        print(f"  综合评分: {opportunity.get('overall_score', 'N/A')}")
    else:
        print(f"未找到插件ID {plugin_id} 的产品机会")
    
    db.close()


if __name__ == "__main__":
    test_opportunity_db()
