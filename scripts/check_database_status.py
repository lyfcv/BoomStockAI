#!/usr/bin/env python3
"""
数据库状态检查脚本
快速检查数据库连接、数据完整性等
"""
import os
import sys
from datetime import datetime, timedelta
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_database_connection():
    """检查数据库连接"""
    try:
        from database.db_utils import DatabaseManager
        db_manager = DatabaseManager()
        
        if db_manager.test_connection():
            print("✅ 数据库连接正常")
            return True
        else:
            print("❌ 数据库连接失败")
            return False
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        return False

def check_tables_exist():
    """检查表是否存在"""
    try:
        from database.db_utils import DatabaseManager
        db_manager = DatabaseManager()
        
        tables = ['stocks', 'stock_prices', 'market_indices', 'market_index_prices']
        
        with db_manager.get_session() as session:
            for table in tables:
                result = session.execute(
                    f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'"
                ).fetchone()
                
                if result[0] > 0:
                    print(f"✅ 表 {table} 存在")
                else:
                    print(f"❌ 表 {table} 不存在")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        return False

def check_data_freshness():
    """检查数据新鲜度"""
    try:
        from database.stock_database_manager import StockDatabaseManager
        db_manager = StockDatabaseManager()
        
        stats = db_manager.get_database_stats()
        
        if stats.get('price_data', {}).get('latest_date'):
            latest_date = stats['price_data']['latest_date']
            days_old = (datetime.now().date() - latest_date.date()).days
            
            print(f"📅 最新数据日期: {latest_date}")
            
            if days_old <= 1:
                print("✅ 数据很新鲜")
            elif days_old <= 3:
                print("⚠️  数据稍微有点旧")
            else:
                print("❌ 数据过期，需要更新")
                return False
        else:
            print("❌ 没有找到价格数据")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 检查数据新鲜度失败: {e}")
        return False

def show_database_stats():
    """显示数据库统计信息"""
    try:
        from database.stock_database_manager import StockDatabaseManager
        db_manager = StockDatabaseManager()
        
        stats = db_manager.get_database_stats()
        
        print("\n📊 数据库统计信息:")
        print(f"  股票总数: {stats.get('stocks', {}).get('total', 0)}")
        print(f"  活跃股票: {stats.get('stocks', {}).get('active', 0)}")
        print(f"  价格数据记录: {stats.get('price_data', {}).get('total_records', 0)}")
        print(f"  指数总数: {stats.get('indices', {}).get('total', 0)}")
        print(f"  指数价格记录: {stats.get('indices', {}).get('price_records', 0)}")
        
        db_manager.close()
        return True
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        return False

def check_baostock_api():
    """检查BaoStock API连接"""
    try:
        from data_collection.market_data.baostock_api import BaoStockAPI
        api = BaoStockAPI()
        
        # 尝试获取一条测试数据
        test_data = api.get_stock_history_data(
            'sh.600000', 
            (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            datetime.now().strftime('%Y-%m-%d')
        )
        
        if test_data:
            print("✅ BaoStock API连接正常")
            api.logout()
            return True
        else:
            print("❌ BaoStock API无法获取数据")
            api.logout()
            return False
    except Exception as e:
        print(f"❌ BaoStock API连接失败: {e}")
        return False

def main():
    """主检查流程"""
    print("🔍 开始检查数据库状态...\n")
    
    all_checks_passed = True
    
    # 1. 检查数据库连接
    print("1. 检查数据库连接")
    if not check_database_connection():
        all_checks_passed = False
    
    # 2. 检查表结构
    print("\n2. 检查表结构")
    if not check_tables_exist():
        all_checks_passed = False
    
    # 3. 检查数据新鲜度
    print("\n3. 检查数据新鲜度")
    if not check_data_freshness():
        all_checks_passed = False
    
    # 4. 检查API连接
    print("\n4. 检查BaoStock API")
    if not check_baostock_api():
        all_checks_passed = False
    
    # 5. 显示统计信息
    print("\n5. 数据库统计")
    show_database_stats()
    
    # 总结
    print("\n" + "="*50)
    if all_checks_passed:
        print("🎉 所有检查都通过了！数据库状态良好。")
    else:
        print("⚠️  发现一些问题，请检查上面的错误信息。")
        print("\n建议的修复步骤:")
        print("1. 如果数据库连接失败，请检查PostgreSQL服务状态")
        print("2. 如果表不存在，请运行: python database/stock_database_manager.py --init")
        print("3. 如果数据过期，请运行: python database/stock_database_manager.py --update-stocks")
        print("4. 如果API连接失败，请检查网络连接")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 