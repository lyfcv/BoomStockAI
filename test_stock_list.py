#!/usr/bin/env python3
"""
测试股票列表获取
"""
import baostock as bs
from datetime import datetime

def test_stock_list():
    """测试获取股票列表"""
    print("开始测试股票列表获取...")
    
    # 登录
    lg = bs.login()
    print(f"登录结果: {lg.error_code}, {lg.error_msg}")
    
    if lg.error_code != '0':
        print("登录失败")
        return
    
    try:
        # 获取股票列表
        print("\n1. 测试获取所有股票列表...")
        rs = bs.query_all_stock()
        print(f"查询结果: {rs.error_code}, {rs.error_msg}")
        
        if rs.error_code == '0':
            count = 0
            while rs.next():
                row = rs.get_row_data()
                count += 1
                if count <= 10:
                    print(f"股票 {count}: {row}")
                if count >= 20:  # 只获取前20个测试
                    break
            print(f"总共获取到 {count} 只股票")
        
        # 测试指定日期
        print("\n2. 测试指定日期获取股票列表...")
        date_str = "2024-12-17"  # 指定一个具体日期
        rs2 = bs.query_all_stock(day=date_str)
        print(f"查询结果 ({date_str}): {rs2.error_code}, {rs2.error_msg}")
        
        if rs2.error_code == '0':
            count2 = 0
            while rs2.next():
                row = rs2.get_row_data()
                count2 += 1
                if count2 <= 5:
                    print(f"股票 {count2}: {row}")
                if count2 >= 10:
                    break
            print(f"指定日期总共获取到 {count2} 只股票")
        
        # 手动添加一些测试股票
        print("\n3. 手动创建测试股票数据...")
        test_stocks = [
            {'code': 'sh.600000', 'name': '浦发银行', 'market': 'SH', 'industry': '银行', 'is_active': True},
            {'code': 'sh.600036', 'name': '招商银行', 'market': 'SH', 'industry': '银行', 'is_active': True},
            {'code': 'sz.000001', 'name': '平安银行', 'market': 'SZ', 'industry': '银行', 'is_active': True},
            {'code': 'sz.000002', 'name': '万科A', 'market': 'SZ', 'industry': '房地产', 'is_active': True},
            {'code': 'sh.600519', 'name': '贵州茅台', 'market': 'SH', 'industry': '食品饮料', 'is_active': True}
        ]
        
        # 保存测试股票到数据库
        from database.stock_database_manager import StockDatabaseManager
        db_manager = StockDatabaseManager()
        saved_count = db_manager.baostock_api.save_stock_basic_to_db(test_stocks)
        print(f"手动保存了 {saved_count} 只测试股票")
        db_manager.close()
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        bs.logout()
        print("已登出")

if __name__ == "__main__":
    test_stock_list() 