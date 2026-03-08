#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的数据
"""

import sqlite3

conn = sqlite3.connect('plugin_opportunities.db')
cursor = conn.cursor()

print('查看前10条插件数据:')
cursor.execute('SELECT id, name, category, rating, install_count, review_count FROM plugins ORDER BY id DESC LIMIT 10')
for row in cursor.fetchall():
    print(f'  ID:{row[0]} | {row[1][:30]:30} | 分类:{row[2]:15} | 评分:{row[3]} | 用户:{row[4]} | 评论:{row[5]}')

conn.close()
