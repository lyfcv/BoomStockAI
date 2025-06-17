#!/usr/bin/env python3
"""
创建市场指数相关数据库表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import db_manager
from database.models import Base, MarketIndex, MarketIndexPrice

def create_index_tables():
    """创建指数相关表"""
    try:
        print("🚀 开始创建指数数据库表...")
        
        # 获取数据库引擎
        engine = db_manager.engine
        
        # 只创建指数相关的表
        MarketIndex.__table__.create(engine, checkfirst=True)
        MarketIndexPrice.__table__.create(engine, checkfirst=True)
        
        print("✅ 指数数据库表创建成功!")
        
        # 插入默认指数数据
        default_indices = [
            {
                'code': 'sh.000001',
                'name': '上证指数',
                'market': 'SH',
                'category': '综合指数',
                'description': '上海证券综合指数',
                'is_active': True
            },
            {
                'code': 'sz.399001',
                'name': '深证成指',
                'market': 'SZ',
                'category': '综合指数',
                'description': '深证成份股指数',
                'is_active': True
            },
            {
                'code': 'sz.399006',
                'name': '创业板指',
                'market': 'SZ',
                'category': '板块指数',
                'description': '创业板指数',
                'is_active': True
            },
            {
                'code': 'sh.000688',
                'name': '科创50',
                'market': 'SH',
                'category': '板块指数',
                'description': '科创板50成份指数',
                'is_active': True
            }
        ]
        
        from database.db_utils import index_dao
        saved_count = index_dao.save_index_basic_info(default_indices)
        print(f"✅ 默认指数信息保存成功，共{saved_count}个指数")
        
    except Exception as e:
        print(f"❌ 创建指数表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_index_tables() 