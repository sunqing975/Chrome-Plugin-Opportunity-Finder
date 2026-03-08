#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库优化模块
添加索引、统计表等优化功能
"""

import sqlite3
import json
from datetime import datetime


class DBOptimizer:
    """
    数据库优化类
    """
    
    def __init__(self, db_path='plugin_opportunities.db'):
        """
        初始化数据库优化器
        
        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def add_indexes(self):
        """
        添加索引以提高查询性能
        """
        indexes = [
            # 插件表索引
            'CREATE INDEX IF NOT EXISTS idx_plugins_rating ON plugins(rating)',
            'CREATE INDEX IF NOT EXISTS idx_plugins_review_count ON plugins(review_count)',
            'CREATE INDEX IF NOT EXISTS idx_plugins_install_count ON plugins(install_count)',
            'CREATE INDEX IF NOT EXISTS idx_plugins_category ON plugins(category)',
            'CREATE INDEX IF NOT EXISTS idx_plugins_created_at ON plugins(created_at)',
            
            # 评论表索引
            'CREATE INDEX IF NOT EXISTS idx_reviews_plugin_id ON reviews(plugin_id)',
            'CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at)',
            
            # 分析结果表索引
            'CREATE INDEX IF NOT EXISTS idx_analysis_results_plugin_id ON analysis_results(plugin_id)',
            'CREATE INDEX IF NOT EXISTS idx_analysis_results_analyzed_at ON analysis_results(analyzed_at)',
            
            # 机会表索引
            'CREATE INDEX IF NOT EXISTS idx_opportunities_plugin_id ON opportunities(plugin_id)',
            'CREATE INDEX IF NOT EXISTS idx_opportunities_overall_score ON opportunities(overall_score)',
            'CREATE INDEX IF NOT EXISTS idx_opportunities_generated_at ON opportunities(generated_at)',
            
            # 分析状态表索引
            'CREATE INDEX IF NOT EXISTS idx_analysis_status_reviews_fetched ON analysis_status(reviews_fetched)',
            'CREATE INDEX IF NOT EXISTS idx_analysis_status_review_analyzed ON analysis_status(review_analyzed)',
            'CREATE INDEX IF NOT EXISTS idx_analysis_status_opportunity_generated ON analysis_status(opportunity_generated)',
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
                print(f"✓ 创建索引: {index_sql.split('ON ')[1]}")
            except Exception as e:
                print(f"✗ 创建索引失败: {e}")
        
        self.conn.commit()
    
    def create_crawler_stats_table(self):
        """
        创建爬虫统计表
        """
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawler_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            plugins_crawled INTEGER,
            reviews_crawled INTEGER,
            errors_count INTEGER,
            status TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_crawler_stats_run_id ON crawler_stats(run_id)
        ''')
        
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_crawler_stats_start_time ON crawler_stats(start_time)
        ''')
        
        self.conn.commit()
        print("✓ 创建爬虫统计表")
    
    def create_error_log_table(self):
        """
        创建错误日志表
        """
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT,
            error_message TEXT,
            context TEXT,
            plugin_id INTEGER,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_error_logs_error_type ON error_logs(error_type)
        ''')
        
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_error_logs_plugin_id ON error_logs(plugin_id)
        ''')
        
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at)
        ''')
        
        self.conn.commit()
        print("✓ 创建错误日志表")
    
    def add_plugin_stats_fields(self):
        """
        为插件表添加统计字段
        """
        fields = [
            'ALTER TABLE plugins ADD COLUMN last_review_fetch_date TIMESTAMP',
            'ALTER TABLE plugins ADD COLUMN last_analysis_date TIMESTAMP',
            'ALTER TABLE plugins ADD COLUMN last_opportunity_date TIMESTAMP',
            'ALTER TABLE plugins ADD COLUMN total_reviews_fetched INTEGER DEFAULT 0',
        ]
        
        for field_sql in fields:
            try:
                self.cursor.execute(field_sql)
                print(f"✓ 添加字段: {field_sql.split('ADD COLUMN ')[1]}")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f"⊙ 字段已存在: {field_sql.split('ADD COLUMN ')[1]}")
                else:
                    print(f"✗ 添加字段失败: {e}")
        
        self.conn.commit()
    
    def get_stats(self):
        """
        获取数据库统计信息
        """
        stats = {}
        
        # 插件统计
        self.cursor.execute('SELECT COUNT(*) FROM plugins')
        stats['total_plugins'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM plugins WHERE rating < 4')
        stats['low_rating_plugins'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM plugins WHERE review_count > 200')
        stats['high_review_plugins'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM plugins WHERE install_count > 10000')
        stats['high_install_plugins'] = self.cursor.fetchone()[0]
        
        # 评论统计
        self.cursor.execute('SELECT COUNT(*) FROM reviews')
        stats['total_reviews'] = self.cursor.fetchone()[0]
        
        # 分析统计
        self.cursor.execute('SELECT COUNT(*) FROM analysis_results')
        stats['analyzed_plugins'] = self.cursor.fetchone()[0]
        
        # 机会统计
        self.cursor.execute('SELECT COUNT(*) FROM opportunities')
        stats['opportunities_generated'] = self.cursor.fetchone()[0]
        
        # 爬虫统计
        self.cursor.execute('SELECT COUNT(*) FROM crawler_stats')
        stats['crawler_runs'] = self.cursor.fetchone()[0]
        
        return stats
    
    def print_stats(self):
        """
        打印数据库统计信息
        """
        stats = self.get_stats()
        
        print("\n" + "="*80)
        print("数据库统计信息")
        print("="*80)
        print(f"\n插件统计:")
        print(f"  总插件数: {stats['total_plugins']}")
        print(f"  低评分插件 (<4.0): {stats['low_rating_plugins']}")
        print(f"  高评论插件 (>200): {stats['high_review_plugins']}")
        print(f"  高安装插件 (>10000): {stats['high_install_plugins']}")
        
        print(f"\n评论统计:")
        print(f"  总评论数: {stats['total_reviews']}")
        
        print(f"\n分析统计:")
        print(f"  已分析插件: {stats['analyzed_plugins']}")
        print(f"  生成机会: {stats['opportunities_generated']}")
        
        print(f"\n爬虫统计:")
        print(f"  爬虫运行次数: {stats['crawler_runs']}")
        
        print("\n" + "="*80)
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.conn:
            self.conn.close()


def optimize_database(db_path='plugin_opportunities.db'):
    """
    优化数据库
    
    Args:
        db_path (str): 数据库文件路径
    """
    print("="*80)
    print("数据库优化")
    print("="*80)
    
    optimizer = DBOptimizer(db_path)
    
    print("\n1. 添加索引...")
    optimizer.add_indexes()
    
    print("\n2. 创建爬虫统计表...")
    optimizer.create_crawler_stats_table()
    
    print("\n3. 创建错误日志表...")
    optimizer.create_error_log_table()
    
    print("\n4. 添加插件统计字段...")
    optimizer.add_plugin_stats_fields()
    
    print("\n5. 数据库统计信息...")
    optimizer.print_stats()
    
    optimizer.close()
    
    print("\n✓ 数据库优化完成！")


if __name__ == "__main__":
    optimize_database()
