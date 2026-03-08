#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析状态管理模块
负责管理和查询插件的分析状态
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db_manager import DBManager


class StatusManager:
    """
    分析状态管理类
    """
    
    def __init__(self):
        """
        初始化状态管理器
        """
        self.db = DBManager()
    
    def get_status(self, plugin_id):
        """
        获取插件的分析状态
        
        Args:
            plugin_id (int): 插件ID
        
        Returns:
            dict: 分析状态
        """
        return self.db.get_analysis_status(plugin_id)
    
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
        return self.db.get_plugins_by_status(reviews_fetched, review_analyzed, opportunity_generated)
    
    def close(self):
        """
        关闭数据库连接
        """
        self.db.close()
    
    def get_pending_reviews(self):
        """
        获取待抓取评论的插件
        
        Returns:
            list: 插件列表
        """
        return self.get_plugins_by_status(reviews_fetched=False)
    
    def get_pending_analysis(self):
        """
        获取待分析评论的插件
        
        Returns:
            list: 插件列表
        """
        return self.get_plugins_by_status(reviews_fetched=True, review_analyzed=False)
    
    def get_pending_opportunities(self):
        """
        获取待生成产品机会的插件
        
        Returns:
            list: 插件列表
        """
        return self.get_plugins_by_status(reviews_fetched=True, review_analyzed=True, opportunity_generated=False)
    
    def get_completed_plugins(self):
        """
        获取已完成所有分析的插件
        
        Returns:
            list: 插件列表
        """
        return self.get_plugins_by_status(reviews_fetched=True, review_analyzed=True, opportunity_generated=True)
