#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel数据存储模块
负责将分析结果和产品机会导出到Excel文件中
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import EXCEL_CONFIG
from storage.db_manager import DBManager


def create_opportunity_report(plugins):
    """
    创建产品机会报告
    
    Args:
        plugins (list): 包含产品机会的插件信息列表
    
    Returns:
        pd.DataFrame: 机会报告数据框
    """
    report_data = []
    
    for plugin in plugins:
        opportunity = plugin.get('opportunity', {})
        analysis = plugin.get('analysis', {})
        
        # 构建报告数据
        data = {
            'Plugin Name': plugin.get('name', ''),
            'Category': plugin.get('category', ''),
            'Rating': plugin.get('rating', 0),
            'Installs': plugin.get('install_count', 0),
            'Reviews': plugin.get('review_count', 0),
            'Pain Points': '; '.join(analysis.get('pain_points', [])) if analysis else '',
            'Missing Features': '; '.join(analysis.get('missing_features', [])) if analysis else '',
            'Product Idea': opportunity.get('idea', '') if opportunity else '',
            'Core Features': '; '.join(opportunity.get('features', [])) if opportunity else '',
            'Target Users': '; '.join(opportunity.get('target_users', [])) if opportunity else '',
            'Business Model': opportunity.get('business_model', '') if opportunity else '',
            'Difficulty': opportunity.get('difficulty', '') if opportunity else '',
            'Market Demand': opportunity.get('scores', {}).get('market_demand', 0) if opportunity else 0,
            'Competition': opportunity.get('scores', {}).get('competition', 0) if opportunity else 0,
            'Ease of Building': opportunity.get('scores', {}).get('ease_of_building', 0) if opportunity else 0,
            'Monetization Potential': opportunity.get('scores', {}).get('monetization_potential', 0) if opportunity else 0,
            'Overall Score': opportunity.get('overall_score', 0) if opportunity else 0,
            'Plugin URL': plugin.get('url', '')
        }
        
        report_data.append(data)
    
    # 创建数据框
    df = pd.DataFrame(report_data)
    
    # 按综合评分排序
    df = df.sort_values('Overall Score', ascending=False)
    
    return df


def save_to_excel(plugins=None, output_file=None):
    """
    将分析结果保存到Excel文件
    
    Args:
        plugins (list, optional): 包含产品机会的插件信息列表. Defaults to None.
        output_file (str, optional): 输出文件路径. Defaults to None.
    
    Returns:
        str: 保存的文件路径
    """
    if output_file is None:
        output_file = EXCEL_CONFIG['output_file']
    
    # 如果没有提供插件列表，从数据库读取
    if plugins is None:
        db = DBManager()
        plugins = db.get_plugins()
        
        # 为每个插件加载分析结果和产品机会
        for plugin in plugins:
            plugin_id = plugin.get('id')
            if plugin_id:
                plugin['analysis'] = db.get_analysis_result(plugin_id)
                plugin['opportunity'] = db.get_opportunity(plugin_id)
        
        db.close()
    
    # 创建机会报告
    df = create_opportunity_report(plugins)
    
    # 保存到Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=EXCEL_CONFIG['sheet_name'], index=False)
        
        # 调整列宽
        worksheet = writer.sheets[EXCEL_CONFIG['sheet_name']]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"报告已保存到: {output_file}")
    return output_file
