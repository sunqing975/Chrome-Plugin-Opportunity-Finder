#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证评论数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db_manager import DBManager


def verify_reviews():
    """
    验证评论数据
    """
    db = DBManager()
    
    # 查询评论总数
    cursor = db.conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM reviews')
    count = cursor.fetchone()[0]
    print(f'总评论数: {count}')
    
    # 显示几条评论
    print('\n前5条评论:')
    cursor.execute('SELECT r.review_text, p.name FROM reviews r JOIN plugins p ON r.plugin_id = p.id LIMIT 5')
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f'\n{i}. 插件: {row[1]}')
        print(f'   评论: {row[0][:100]}...')
    
    db.close()


if __name__ == "__main__":
    print("="*80)
    print("评论数据验证")
    print("="*80)
    verify_reviews()
