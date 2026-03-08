#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据预览工具模块
提供数据的预览和查看功能
"""

import sys
import os
from tabulate import tabulate

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db_manager import DBManager


class DataViewer:
    """
    数据预览类
    """
    
    def __init__(self):
        """
        初始化数据预览器
        """
        self.db = DBManager()
    
    def show_plugins(self, limit=10, plugin_id=None):
        """
        显示插件信息
        
        Args:
            limit (int): 显示数量限制
            plugin_id (int, optional): 特定插件ID
        """
        if plugin_id:
            plugins = [self.db.get_plugin(plugin_id)]
            if not plugins[0]:
                print(f"未找到插件ID: {plugin_id}")
                return
        else:
            plugins = self.db.get_plugins(limit=limit)
        
        if not plugins:
            print("没有找到插件数据")
            return
        
        # 准备表格数据
        headers = ['ID', '插件ID', '名称', '分类', '评分', '用户数', '评论数', '开发者', '版本', '最后更新', '采集时间']
        table_data = []
        
        for plugin in plugins:
            table_data.append([
                plugin['id'],
                plugin.get('plugin_id', '')[:15],
                plugin['name'][:25] if plugin['name'] else '',
                plugin['category'][:15] if plugin['category'] else '',
                plugin['rating'],
                plugin['install_count'],
                plugin['review_count'],
                plugin['developer'][:15] if plugin['developer'] else '',
                plugin.get('version', '')[:10],
                plugin.get('last_updated', '')[:12],
                plugin.get('last_crawled_at', '')[:16] if plugin.get('last_crawled_at') else ''
            ])
        
        print(f"\n{'='*80}")
        print(f"插件信息 (显示 {len(plugins)} 个插件)")
        print(f"{'='*80}")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print(f"{'='*80}\n")
    
    def show_reviews(self, plugin_id, limit=10):
        """
        显示插件评论
        
        Args:
            plugin_id (int): 插件ID
            limit (int): 显示数量限制
        """
        reviews = self.db.get_reviews(plugin_id)
        
        if not reviews:
            print(f"插件ID {plugin_id} 没有评论数据")
            return
        
        plugin = self.db.get_plugin(plugin_id)
        plugin_name = plugin['name'] if plugin else '未知'
        
        # 准备表格数据
        headers = ['ID', '评分', '评论内容', '日期']
        table_data = []
        
        for review in reviews[:limit]:
            # 截断过长的评论
            review_text = review['review_text']
            if len(review_text) > 50:
                review_text = review_text[:50] + '...'
            
            table_data.append([
                review['id'],
                review['rating'],
                review_text,
                review['date'][:10] if review['date'] else ''
            ])
        
        print(f"\n{'='*80}")
        print(f"插件评论: {plugin_name} (显示 {min(len(reviews), limit)} 条评论)")
        print(f"{'='*80}")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print(f"{'='*80}\n")
    
    def show_analysis(self, plugin_id):
        """
        显示分析结果
        
        Args:
            plugin_id (int): 插件ID
        """
        analysis = self.db.get_analysis_result(plugin_id)
        
        if not analysis:
            print(f"插件ID {plugin_id} 没有分析结果")
            return
        
        plugin = self.db.get_plugin(plugin_id)
        plugin_name = plugin['name'] if plugin else '未知'
        
        print(f"\n{'='*80}")
        print(f"分析结果: {plugin_name}")
        print(f"{'='*80}")
        
        # 显示痛点
        if analysis.get('pain_points'):
            print("\n【用户痛点】")
            for i, point in enumerate(analysis['pain_points'], 1):
                print(f"  {i}. {point}")
        
        # 显示缺失功能
        if analysis.get('missing_features'):
            print("\n【缺失功能】")
            for i, feature in enumerate(analysis['missing_features'], 1):
                print(f"  {i}. {feature}")
        
        # 显示功能请求
        if analysis.get('feature_requests'):
            print("\n【功能请求】")
            for i, request in enumerate(analysis['feature_requests'], 1):
                print(f"  {i}. {request}")
        
        # 显示改进机会
        if analysis.get('improvement_opportunities'):
            print("\n【改进机会】")
            for i, opportunity in enumerate(analysis['improvement_opportunities'], 1):
                print(f"  {i}. {opportunity}")
        
        print(f"\n{'='*80}\n")
    
    def show_opportunity(self, plugin_id):
        """
        显示产品机会
        
        Args:
            plugin_id (int): 插件ID
        """
        opportunity = self.db.get_opportunity(plugin_id)
        
        if not opportunity:
            print(f"插件ID {plugin_id} 没有产品机会")
            return
        
        plugin = self.db.get_plugin(plugin_id)
        plugin_name = plugin['name'] if plugin else '未知'
        
        print(f"\n{'='*80}")
        print(f"产品机会: {plugin_name}")
        print(f"{'='*80}")
        
        # 显示产品想法
        print(f"\n【产品想法】")
        print(f"  {opportunity.get('idea', '无')}")
        
        # 显示核心功能
        if opportunity.get('features'):
            print(f"\n【核心功能】")
            for i, feature in enumerate(opportunity['features'], 1):
                print(f"  {i}. {feature}")
        
        # 显示目标用户
        if opportunity.get('target_users'):
            print(f"\n【目标用户】")
            for i, user in enumerate(opportunity['target_users'], 1):
                print(f"  {i}. {user}")
        
        # 显示商业模式
        print(f"\n【商业模式】")
        print(f"  {opportunity.get('business_model', '无')}")
        
        # 显示开发难度
        print(f"\n【开发难度】")
        print(f"  {opportunity.get('difficulty', '无')}")
        
        # 显示评分
        scores = opportunity.get('scores', {})
        print(f"\n【评分】")
        print(f"  市场需求: {scores.get('market_demand', 0)}/10")
        print(f"  竞争情况: {scores.get('competition', 0)}/10")
        print(f"  构建难度: {scores.get('ease_of_building', 0)}/10")
        print(f"  盈利潜力: {scores.get('monetization_potential', 0)}/10")
        print(f"  综合评分: {scores.get('overall_score', 0)}/10")
        
        # 显示成功因素
        if opportunity.get('success_factors'):
            print(f"\n【成功因素】")
            for i, factor in enumerate(opportunity['success_factors'], 1):
                print(f"  {i}. {factor}")
        
        # 显示风险
        if opportunity.get('risks'):
            print(f"\n【风险提示】")
            for i, risk in enumerate(opportunity['risks'], 1):
                print(f"  {i}. {risk}")
        
        print(f"\n{'='*80}\n")
    
    def show_plugin_details(self, plugin_id):
        """
        显示插件的完整信息，包括评论、分析结果和产品机会
        
        Args:
            plugin_id (int): 插件ID
        """
        # 显示插件基本信息
        self.show_plugins(limit=1, plugin_id=plugin_id)
        
        # 显示评论
        self.show_reviews(plugin_id, limit=5)
        
        # 显示分析结果
        self.show_analysis(plugin_id)
        
        # 显示产品机会
        self.show_opportunity(plugin_id)
    
    def show_top_opportunities(self, limit=10):
        """
        显示评分最高的产品机会
        
        Args:
            limit (int): 显示数量限制
        """
        # 获取所有插件
        plugins = self.db.get_plugins()
        
        # 筛选有产品机会的插件
        plugins_with_opportunities = []
        for plugin in plugins:
            opportunity = self.db.get_opportunity(plugin['id'])
            if opportunity:
                plugin['opportunity'] = opportunity
                plugins_with_opportunities.append(plugin)
        
        # 按综合评分排序
        plugins_with_opportunities.sort(
            key=lambda x: x['opportunity'].get('overall_score', 0), 
            reverse=True
        )
        
        if not plugins_with_opportunities:
            print("没有找到产品机会数据")
            return
        
        # 准备表格数据
        headers = ['排名', '插件名称', '产品想法', '综合评分', '市场需求', '盈利潜力']
        table_data = []
        
        for i, plugin in enumerate(plugins_with_opportunities[:limit], 1):
            opportunity = plugin['opportunity']
            table_data.append([
                i,
                plugin['name'][:20] if plugin['name'] else '',
                opportunity.get('idea', '')[:30] if opportunity.get('idea') else '',
                opportunity.get('overall_score', 0),
                opportunity.get('scores', {}).get('market_demand', 0),
                opportunity.get('scores', {}).get('monetization_potential', 0)
            ])
        
        print(f"\n{'='*80}")
        print(f"最佳产品机会 (显示 {len(table_data)} 个机会)")
        print(f"{'='*80}")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print(f"{'='*80}\n")
    
    def close(self):
        """
        关闭数据库连接
        """
        self.db.close()
