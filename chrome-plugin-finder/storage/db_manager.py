#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
负责SQLite数据库的创建和操作
"""

import sqlite3
import json
import os


class DBManager:
    """
    数据库管理类
    """
    
    def __init__(self, db_path='plugin_opportunities.db'):
        """
        初始化数据库管理器
        
        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._init_db()
    
    def _init_db(self):
        """
        初始化数据库，创建表结构
        """
        # 连接数据库
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建插件表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS plugins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plugin_id TEXT UNIQUE NOT NULL,  -- Chrome Web Store插件ID
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            rating REAL,
            review_count INTEGER,
            install_count INTEGER,
            developer TEXT,
            developer_url TEXT,  -- 开发者链接
            version TEXT,  -- 版本号
            last_updated TEXT,  -- 插件最后更新日期
            url TEXT UNIQUE,
            icon_url TEXT,  -- 图标URL
            screenshots TEXT,  -- 截图URL列表（JSON格式）
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_crawled_at TIMESTAMP,  -- 上次采集时间
            crawl_count INTEGER DEFAULT 0  -- 采集次数
        )
        ''')
        
        # 创建评论表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plugin_id INTEGER,
            review_text TEXT,
            rating REAL,
            date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plugin_id) REFERENCES plugins (id)
        )
        ''')
        
        # 创建分析结果表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plugin_id INTEGER,
            pain_points TEXT,  -- JSON格式存储列表
            missing_features TEXT,  -- JSON格式存储列表
            feature_requests TEXT,  -- JSON格式存储列表
            improvement_opportunities TEXT,  -- JSON格式存储列表
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plugin_id) REFERENCES plugins (id),
            UNIQUE (plugin_id)
        )
        ''')
        
        # 创建产品机会表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plugin_id INTEGER,
            idea TEXT,
            features TEXT,  -- JSON格式存储列表
            target_users TEXT,  -- JSON格式存储列表
            business_model TEXT,
            difficulty TEXT,
            market_demand INTEGER,
            competition INTEGER,
            ease_of_building INTEGER,
            monetization_potential INTEGER,
            overall_score INTEGER,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plugin_id) REFERENCES plugins (id),
            UNIQUE (plugin_id)
        )
        ''')
        
        # 创建分析状态表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_status (
            plugin_id INTEGER PRIMARY KEY,
            reviews_fetched BOOLEAN DEFAULT FALSE,
            review_analyzed BOOLEAN DEFAULT FALSE,
            opportunity_generated BOOLEAN DEFAULT FALSE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plugin_id) REFERENCES plugins (id)
        )
        ''')
        
        self.conn.commit()
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.conn:
            self.conn.close()
    
    def insert_plugin(self, plugin_data):
        """
        插入或更新插件数据
        
        Args:
            plugin_data (dict): 插件数据，必须包含plugin_id字段
        
        Returns:
            int: 插件ID
        """
        try:
            # 获取plugin_id（Chrome Web Store的插件ID）
            plugin_store_id = plugin_data.get('id') or plugin_data.get('plugin_id')
            if not plugin_store_id:
                # 从URL中提取
                url = plugin_data.get('url', '')
                if '/detail/' in url:
                    plugin_store_id = url.split('/detail/')[-1].split('/')[0]
                else:
                    raise ValueError("无法获取plugin_id")
            
            # 检查插件是否已存在
            self.cursor.execute('SELECT id FROM plugins WHERE plugin_id = ?', (plugin_store_id,))
            existing = self.cursor.fetchone()
            
            if existing:
                # 更新现有插件
                self.cursor.execute('''
                UPDATE plugins SET 
                    name = ?, description = ?, category = ?, rating = ?, 
                    review_count = ?, install_count = ?, developer = ?,
                    developer_url = ?, version = ?, last_updated = ?,
                    url = ?, icon_url = ?, screenshots = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    last_crawled_at = CURRENT_TIMESTAMP,
                    crawl_count = crawl_count + 1
                WHERE id = ?
                ''', (
                    plugin_data.get('name', ''),
                    plugin_data.get('description', ''),
                    plugin_data.get('category', ''),
                    plugin_data.get('rating', 0),
                    plugin_data.get('review_count', 0),
                    plugin_data.get('install_count', 0),
                    plugin_data.get('developer', ''),
                    plugin_data.get('developer_url', ''),
                    plugin_data.get('version', ''),
                    plugin_data.get('last_updated', ''),
                    plugin_data.get('url', ''),
                    plugin_data.get('icon_url', ''),
                    json.dumps(plugin_data.get('screenshots', [])),
                    existing[0]
                ))
                plugin_id = existing[0]
            else:
                # 插入新插件
                self.cursor.execute('''
                INSERT INTO plugins (
                    plugin_id, name, description, category, rating, review_count, 
                    install_count, developer, developer_url, version, last_updated,
                    url, icon_url, screenshots, last_crawled_at, crawl_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                ''', (
                    plugin_store_id,
                    plugin_data.get('name', ''),
                    plugin_data.get('description', ''),
                    plugin_data.get('category', ''),
                    plugin_data.get('rating', 0),
                    plugin_data.get('review_count', 0),
                    plugin_data.get('install_count', 0),
                    plugin_data.get('developer', ''),
                    plugin_data.get('developer_url', ''),
                    plugin_data.get('version', ''),
                    plugin_data.get('last_updated', ''),
                    plugin_data.get('url', ''),
                    plugin_data.get('icon_url', ''),
                    json.dumps(plugin_data.get('screenshots', []))
                ))
                plugin_id = self.cursor.lastrowid
            
            # 初始化分析状态
            self.cursor.execute('''
            INSERT OR IGNORE INTO analysis_status (plugin_id) VALUES (?)
            ''', (plugin_id,))
            
            self.conn.commit()
            return plugin_id
        except Exception as e:
            print(f"插入插件数据时出错: {e}")
            self.conn.rollback()
            return None
    
    def insert_reviews(self, plugin_id, reviews):
        """
        插入评论数据
        
        Args:
            plugin_id (int): 插件ID
            reviews (list): 评论列表
        """
        try:
            # 先删除现有评论
            self.cursor.execute('DELETE FROM reviews WHERE plugin_id = ?', (plugin_id,))
            
            # 插入新评论
            for review in reviews:
                self.cursor.execute('''
                INSERT INTO reviews (plugin_id, review_text, rating, date) 
                VALUES (?, ?, ?, ?)
                ''', (
                    plugin_id, review['review_text'], review['rating'], review['date']
                ))
            
            # 更新分析状态
            self.cursor.execute('''
            UPDATE analysis_status SET 
                reviews_fetched = TRUE, 
                last_updated = CURRENT_TIMESTAMP
            WHERE plugin_id = ?
            ''', (plugin_id,))
            
            self.conn.commit()
        except Exception as e:
            print(f"插入评论数据时出错: {e}")
            self.conn.rollback()
    
    def insert_analysis_result(self, plugin_id, analysis):
        """
        插入分析结果
        
        Args:
            plugin_id (int): 插件ID
            analysis (dict): 分析结果
        """
        try:
            # 插入或更新分析结果
            self.cursor.execute('''
            INSERT OR REPLACE INTO analysis_results 
            (plugin_id, pain_points, missing_features, feature_requests, improvement_opportunities) 
            VALUES (?, ?, ?, ?, ?)
            ''', (
                plugin_id,
                json.dumps(analysis.get('pain_points', [])),
                json.dumps(analysis.get('missing_features', [])),
                json.dumps(analysis.get('feature_requests', [])),
                json.dumps(analysis.get('improvement_opportunities', []))
            ))
            
            # 更新分析状态
            self.cursor.execute('''
            UPDATE analysis_status SET 
                review_analyzed = TRUE, 
                last_updated = CURRENT_TIMESTAMP
            WHERE plugin_id = ?
            ''', (plugin_id,))
            
            self.conn.commit()
        except Exception as e:
            print(f"插入分析结果时出错: {e}")
            self.conn.rollback()
    
    def insert_opportunity(self, plugin_id, opportunity):
        """
        插入产品机会
        
        Args:
            plugin_id (int): 插件ID
            opportunity (dict): 产品机会
        """
        try:
            # 插入或更新产品机会
            self.cursor.execute('''
            INSERT OR REPLACE INTO opportunities 
            (plugin_id, idea, features, target_users, business_model, difficulty, 
             market_demand, competition, ease_of_building, monetization_potential, overall_score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plugin_id,
                opportunity.get('idea', ''),
                json.dumps(opportunity.get('features', [])),
                json.dumps(opportunity.get('target_users', [])),
                opportunity.get('business_model', ''),
                opportunity.get('difficulty', ''),
                opportunity.get('scores', {}).get('market_demand', 0),
                opportunity.get('scores', {}).get('competition', 0),
                opportunity.get('scores', {}).get('ease_of_building', 0),
                opportunity.get('scores', {}).get('monetization_potential', 0),
                opportunity.get('overall_score', 0)
            ))
            
            # 更新分析状态
            self.cursor.execute('''
            UPDATE analysis_status SET 
                opportunity_generated = TRUE, 
                last_updated = CURRENT_TIMESTAMP
            WHERE plugin_id = ?
            ''', (plugin_id,))
            
            self.conn.commit()
        except Exception as e:
            print(f"插入产品机会时出错: {e}")
            self.conn.rollback()
    
    def get_plugin(self, plugin_id):
        """
        获取插件信息
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            dict: 插件信息
        """
        try:
            self.cursor.execute('''
            SELECT id, name, description, category, rating, review_count, 
                   install_count, developer, url, created_at, updated_at 
            FROM plugins WHERE id = ?
            ''', (plugin_id,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'category': row[3],
                    'rating': row[4],
                    'review_count': row[5],
                    'install_count': row[6],
                    'developer': row[7],
                    'url': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                }
            return None
        except Exception as e:
            print(f"获取插件信息时出错: {e}")
            return None
    
    def get_plugins(self, limit=None, offset=0):
        """
        获取插件列表
        
        Args:
            limit (int, optional): 限制数量
            offset (int, optional): 偏移量
        
        Returns:
            list: 插件列表
        """
        try:
            query = '''
            SELECT id, plugin_id, name, description, category, rating, review_count, 
                   install_count, developer, developer_url, version, last_updated,
                   url, icon_url, screenshots, created_at, updated_at, 
                   last_crawled_at, crawl_count
            FROM plugins 
            ORDER BY id DESC
            '''
            params = []
            
            if limit:
                query += ' LIMIT ? OFFSET ?'
                params.extend([limit, offset])
            elif offset > 0:
                query += ' OFFSET ?'
                params.append(offset)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            plugins = []
            for row in rows:
                plugins.append({
                    'id': row[0],
                    'plugin_id': row[1],
                    'name': row[2],
                    'description': row[3],
                    'category': row[4],
                    'rating': row[5],
                    'review_count': row[6],
                    'install_count': row[7],
                    'developer': row[8],
                    'developer_url': row[9],
                    'version': row[10],
                    'last_updated': row[11],
                    'url': row[12],
                    'icon_url': row[13],
                    'screenshots': row[14],
                    'created_at': row[15],
                    'updated_at': row[16],
                    'last_crawled_at': row[17],
                    'crawl_count': row[18]
                })
            
            return plugins
        except Exception as e:
            print(f"获取插件列表时出错: {e}")
            return []
    
    def get_reviews(self, plugin_id):
        """
        获取插件评论
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            list: 评论列表
        """
        try:
            self.cursor.execute('''
            SELECT id, review_text, rating, date 
            FROM reviews WHERE plugin_id = ?
            ''', (plugin_id,))
            rows = self.cursor.fetchall()
            
            reviews = []
            for row in rows:
                reviews.append({
                    'id': row[0],
                    'review_text': row[1],
                    'rating': row[2],
                    'date': row[3]
                })
            
            return reviews
        except Exception as e:
            print(f"获取评论时出错: {e}")
            return []
    
    def get_analysis_result(self, plugin_id):
        """
        获取分析结果
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            dict: 分析结果
        """
        try:
            self.cursor.execute('''
            SELECT pain_points, missing_features, feature_requests, improvement_opportunities 
            FROM analysis_results WHERE plugin_id = ?
            ''', (plugin_id,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'pain_points': json.loads(row[0]) if row[0] else [],
                    'missing_features': json.loads(row[1]) if row[1] else [],
                    'feature_requests': json.loads(row[2]) if row[2] else [],
                    'improvement_opportunities': json.loads(row[3]) if row[3] else []
                }
            return None
        except Exception as e:
            print(f"获取分析结果时出错: {e}")
            return None
    
    def get_opportunity(self, plugin_id):
        """
        获取产品机会
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            dict: 产品机会
        """
        try:
            self.cursor.execute('''
            SELECT idea, features, target_users, business_model, difficulty, 
                   market_demand, competition, ease_of_building, monetization_potential, overall_score 
            FROM opportunities WHERE plugin_id = ?
            ''', (plugin_id,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'idea': row[0],
                    'features': json.loads(row[1]) if row[1] else [],
                    'target_users': json.loads(row[2]) if row[2] else [],
                    'business_model': row[3],
                    'difficulty': row[4],
                    'scores': {
                        'market_demand': row[5],
                        'competition': row[6],
                        'ease_of_building': row[7],
                        'monetization_potential': row[8],
                        'overall_score': row[9]
                    },
                    'overall_score': row[9]
                }
            return None
        except Exception as e:
            print(f"获取产品机会时出错: {e}")
            return None
    
    def get_analysis_status(self, plugin_id):
        """
        获取分析状态
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            dict: 分析状态
        """
        try:
            self.cursor.execute('''
            SELECT reviews_fetched, review_analyzed, opportunity_generated, last_updated 
            FROM analysis_status WHERE plugin_id = ?
            ''', (plugin_id,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'reviews_fetched': bool(row[0]),
                    'review_analyzed': bool(row[1]),
                    'opportunity_generated': bool(row[2]),
                    'last_updated': row[3]
                }
            return None
        except Exception as e:
            print(f"获取分析状态时出错: {e}")
            return None
    
    def update_analysis_status(self, plugin_id, reviews_fetched=None, review_analyzed=None, opportunity_generated=None):
        """
        更新分析状态
        
        Args:
            plugin_id (int): 插件ID
            reviews_fetched (bool, optional): 评论是否已抓取
            review_analyzed (bool, optional): 评论是否已分析
            opportunity_generated (bool, optional): 产品机会是否已生成
        """
        try:
            # 先检查记录是否存在
            self.cursor.execute('SELECT plugin_id FROM analysis_status WHERE plugin_id = ?', (plugin_id,))
            existing = self.cursor.fetchone()
            
            if existing:
                # 更新现有记录
                updates = []
                params = []
                if reviews_fetched is not None:
                    updates.append('reviews_fetched = ?')
                    params.append(reviews_fetched)
                if review_analyzed is not None:
                    updates.append('review_analyzed = ?')
                    params.append(review_analyzed)
                if opportunity_generated is not None:
                    updates.append('opportunity_generated = ?')
                    params.append(opportunity_generated)
                
                if updates:
                    updates.append('last_updated = CURRENT_TIMESTAMP')
                    params.append(plugin_id)
                    query = f"UPDATE analysis_status SET {', '.join(updates)} WHERE plugin_id = ?"
                    self.cursor.execute(query, params)
            else:
                # 插入新记录
                self.cursor.execute('''
                INSERT INTO analysis_status (plugin_id, reviews_fetched, review_analyzed, opportunity_generated)
                VALUES (?, ?, ?, ?)
                ''', (plugin_id, reviews_fetched or False, review_analyzed or False, opportunity_generated or False))
            
            self.conn.commit()
        except Exception as e:
            print(f"更新分析状态时出错: {e}")
            self.conn.rollback()
    
    def get_plugins_by_status(self, reviews_fetched=None, review_analyzed=None, opportunity_generated=None):
        """
        根据分析状态获取插件
        
        Args:
            reviews_fetched (bool, optional): 评论是否已抓取
            review_analyzed (bool, optional): 评论是否已分析
            opportunity_generated (bool, optional): 产品机会是否已生成
        
        Returns:
            list: 插件列表
        """
        try:
            query = '''
            SELECT p.id, p.name, p.description, p.category, p.rating, p.review_count, 
                   p.install_count, p.developer, p.url, p.created_at, p.updated_at 
            FROM plugins p
            JOIN analysis_status s ON p.id = s.plugin_id
            WHERE 1=1
            '''
            params = []
            
            if reviews_fetched is not None:
                query += ' AND s.reviews_fetched = ?'
                params.append(1 if reviews_fetched else 0)
            
            if review_analyzed is not None:
                query += ' AND s.review_analyzed = ?'
                params.append(1 if review_analyzed else 0)
            
            if opportunity_generated is not None:
                query += ' AND s.opportunity_generated = ?'
                params.append(1 if opportunity_generated else 0)
            
            query += ' ORDER BY p.install_count DESC'
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            plugins = []
            for row in rows:
                plugins.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'category': row[3],
                    'rating': row[4],
                    'review_count': row[5],
                    'install_count': row[6],
                    'developer': row[7],
                    'url': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                })
            
            return plugins
        except Exception as e:
            print(f"根据状态获取插件时出错: {e}")
            return []
