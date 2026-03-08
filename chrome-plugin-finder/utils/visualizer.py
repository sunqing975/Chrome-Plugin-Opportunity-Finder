#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据可视化模块
负责生成各种数据可视化图表
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import sys
import os
from wordcloud import WordCloud

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 确保输出目录存在
os.makedirs('visualizations', exist_ok=True)


class DataVisualizer:
    """数据可视化类"""
    
    def __init__(self, db_manager):
        """
        初始化数据可视化器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def get_plugins_data(self):
        """
        获取插件数据
        
        Returns:
            pd.DataFrame: 插件数据
        """
        plugins = self.db.get_plugins()
        data = []
        
        for plugin in plugins:
            data.append({
                'name': plugin.get('name', ''),
                'category': plugin.get('category', ''),
                'rating': plugin.get('rating', 0),
                'install_count': plugin.get('install_count', 0),
                'review_count': plugin.get('review_count', 0),
                'last_updated': plugin.get('last_updated', '')
            })
        
        return pd.DataFrame(data)
    
    def get_opportunities_data(self):
        """
        获取产品机会数据
        
        Returns:
            pd.DataFrame: 产品机会数据
        """
        plugins = self.db.get_plugins()
        data = []
        
        for plugin in plugins:
            plugin_id = plugin.get('id')
            if plugin_id:
                opportunity = self.db.get_opportunity(plugin_id)
                if opportunity:
                    data.append({
                        'plugin_name': plugin.get('name', ''),
                        'overall_score': opportunity.get('overall_score', 0),
                        'market_demand': opportunity.get('scores', {}).get('market_demand', 0),
                        'competition': opportunity.get('scores', {}).get('competition', 0),
                        'ease_of_building': opportunity.get('scores', {}).get('ease_of_building', 0),
                        'monetization_potential': opportunity.get('scores', {}).get('monetization_potential', 0),
                        'difficulty': opportunity.get('difficulty', '')
                    })
        
        return pd.DataFrame(data)
    
    def get_analysis_data(self):
        """
        获取分析结果数据
        
        Returns:
            dict: 分析结果数据
        """
        plugins = self.db.get_plugins()
        pain_points = []
        missing_features = []
        
        for plugin in plugins:
            plugin_id = plugin.get('id')
            if plugin_id:
                analysis = self.db.get_analysis_result(plugin_id)
                if analysis:
                    pain_points.extend(analysis.get('pain_points', []))
                    missing_features.extend(analysis.get('missing_features', []))
        
        return {
            'pain_points': pain_points,
            'missing_features': missing_features
        }
    
    def plot_rating_distribution(self):
        """
        绘制评分分布直方图
        """
        df = self.get_plugins_data()
        
        plt.figure(figsize=(10, 6))
        sns.histplot(df['rating'], bins=20, kde=True, color='skyblue')
        plt.title('插件评分分布', fontsize=16)
        plt.xlabel('评分', fontsize=12)
        plt.ylabel('插件数量', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        
        output_file = 'visualizations/rating_distribution.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 评分分布图已保存: {output_file}")
    
    def plot_install_distribution(self):
        """
        绘制安装数分布箱线图
        """
        df = self.get_plugins_data()
        
        # 对安装数取对数（因为安装数差异很大）
        df['log_install'] = df['install_count'].apply(lambda x: max(1, x)).apply(lambda x: np.log10(x))
        
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='log_install', data=df, color='lightgreen')
        plt.title('插件安装数分布（对数尺度）', fontsize=16)
        plt.xlabel('安装数（log10）', fontsize=12)
        plt.grid(axis='x', alpha=0.3)
        
        output_file = 'visualizations/install_distribution.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 安装数分布图已保存: {output_file}")
    
    def plot_review_distribution(self):
        """
        绘制评论数分布直方图
        """
        df = self.get_plugins_data()
        
        # 过滤掉评论数为0的插件
        df = df[df['review_count'] > 0]
        
        # 对评论数取对数
        df['log_review'] = df['review_count'].apply(lambda x: max(1, x)).apply(lambda x: np.log10(x))
        
        plt.figure(figsize=(10, 6))
        sns.histplot(df['log_review'], bins=20, kde=True, color='lightcoral')
        plt.title('插件评论数分布（对数尺度）', fontsize=16)
        plt.xlabel('评论数（log10）', fontsize=12)
        plt.ylabel('插件数量', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        
        output_file = 'visualizations/review_distribution.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 评论数分布图已保存: {output_file}")
    
    def plot_opportunity_scores(self):
        """
        绘制产品机会评分分布
        """
        df = self.get_opportunities_data()
        
        if df.empty:
            print("⚠️  没有产品机会数据")
            return
        
        plt.figure(figsize=(12, 8))
        
        # 绘制评分分布图
        plt.subplot(2, 2, 1)
        sns.histplot(df['overall_score'], bins=10, kde=True, color='purple')
        plt.title('综合评分分布', fontsize=14)
        plt.xlabel('评分', fontsize=10)
        plt.ylabel('产品机会数', fontsize=10)
        plt.grid(axis='y', alpha=0.3)
        
        # 绘制市场需求分布
        plt.subplot(2, 2, 2)
        sns.histplot(df['market_demand'], bins=10, kde=True, color='blue')
        plt.title('市场需求评分分布', fontsize=14)
        plt.xlabel('评分', fontsize=10)
        plt.ylabel('产品机会数', fontsize=10)
        plt.grid(axis='y', alpha=0.3)
        
        # 绘制竞争情况分布
        plt.subplot(2, 2, 3)
        sns.histplot(df['competition'], bins=10, kde=True, color='green')
        plt.title('竞争情况评分分布', fontsize=14)
        plt.xlabel('评分', fontsize=10)
        plt.ylabel('产品机会数', fontsize=10)
        plt.grid(axis='y', alpha=0.3)
        
        # 绘制盈利潜力分布
        plt.subplot(2, 2, 4)
        sns.histplot(df['monetization_potential'], bins=10, kde=True, color='orange')
        plt.title('盈利潜力评分分布', fontsize=14)
        plt.xlabel('评分', fontsize=10)
        plt.ylabel('产品机会数', fontsize=10)
        plt.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        output_file = 'visualizations/opportunity_scores.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 产品机会评分分布图已保存: {output_file}")
    
    def plot_top_opportunities(self, top_n=10):
        """
        绘制Top N产品机会
        
        Args:
            top_n (int): 显示前N个产品机会
        """
        df = self.get_opportunities_data()
        
        if df.empty:
            print("⚠️  没有产品机会数据")
            return
        
        # 按综合评分排序
        df = df.sort_values('overall_score', ascending=False).head(top_n)
        
        plt.figure(figsize=(12, 8))
        sns.barplot(x='overall_score', y='plugin_name', data=df, palette='viridis')
        plt.title(f'Top {top_n} 产品机会（按综合评分）', fontsize=16)
        plt.xlabel('综合评分', fontsize=12)
        plt.ylabel('插件名称', fontsize=12)
        plt.xlim(0, 10)
        plt.grid(axis='x', alpha=0.3)
        
        output_file = f'visualizations/top_{top_n}_opportunities.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Top {top_n} 产品机会图已保存: {output_file}")
    
    def plot_pain_points_wordcloud(self):
        """
        绘制痛点词云
        """
        analysis_data = self.get_analysis_data()
        pain_points = analysis_data.get('pain_points', [])
        
        if not pain_points:
            print("⚠️  没有痛点数据")
            return
        
        # 合并所有痛点
        text = ' '.join(pain_points)
        
        # 创建词云
        wordcloud = WordCloud(
            width=800,
            height=600,
            background_color='white',
            max_words=100,
            max_font_size=100,
            random_state=42
        ).generate(text)
        
        plt.figure(figsize=(12, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('用户痛点词云', fontsize=16)
        
        output_file = 'visualizations/pain_points_wordcloud.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 痛点词云已保存: {output_file}")
    
    def plot_missing_features_wordcloud(self):
        """
        绘制缺失功能词云
        """
        analysis_data = self.get_analysis_data()
        missing_features = analysis_data.get('missing_features', [])
        
        if not missing_features:
            print("⚠️  没有缺失功能数据")
            return
        
        # 合并所有缺失功能
        text = ' '.join(missing_features)
        
        # 创建词云
        wordcloud = WordCloud(
            width=800,
            height=600,
            background_color='white',
            max_words=100,
            max_font_size=100,
            random_state=42
        ).generate(text)
        
        plt.figure(figsize=(12, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('缺失功能词云', fontsize=16)
        
        output_file = 'visualizations/missing_features_wordcloud.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 缺失功能词云已保存: {output_file}")
    
    def generate_all_visualizations(self):
        """
        生成所有可视化图表
        """
        print("\n开始生成数据可视化...")
        
        # 插件数据可视化
        self.plot_rating_distribution()
        self.plot_install_distribution()
        self.plot_review_distribution()
        
        # 产品机会可视化
        self.plot_opportunity_scores()
        self.plot_top_opportunities()
        
        # 分析结果可视化
        self.plot_pain_points_wordcloud()
        self.plot_missing_features_wordcloud()
        
        print("\n✓ 所有可视化图表已生成完成！")
        print("\n图表保存位置: visualizations/")


# 导入numpy
import numpy as np


def generate_visualizations():
    """
    生成可视化图表的主函数
    """
    # 导入数据库管理器
    from storage.db_manager import DBManager
    
    db = DBManager()
    visualizer = DataVisualizer(db)
    
    try:
        visualizer.generate_all_visualizations()
    finally:
        db.close()


if __name__ == "__main__":
    generate_visualizations()