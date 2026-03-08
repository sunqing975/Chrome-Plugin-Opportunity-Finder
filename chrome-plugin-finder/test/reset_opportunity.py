#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置产品机会并重新生成
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db_manager import DBManager


def reset_opportunity():
    """
    重置插件ID 1的产品机会
    """
    print("="*80)
    print("重置产品机会")
    print("="*80)
    
    db = DBManager()
    
    # 删除插件ID 1的产品机会
    plugin_id = 1
    db.cursor.execute('DELETE FROM opportunities WHERE plugin_id = ?', (plugin_id,))
    db.conn.commit()
    
    # 重置分析状态
    db.cursor.execute('UPDATE analysis_status SET opportunity_generated = FALSE WHERE plugin_id = ?', (plugin_id,))
    db.conn.commit()
    
    print(f"✓ 已重置插件ID {plugin_id} 的产品机会")
    
    db.close()


if __name__ == "__main__":
    reset_opportunity()
