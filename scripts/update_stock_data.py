"""
脚本：更新股票基础信息和历史价格数据
"""
import sys
import os
import argparse
from datetime import datetime, timedelta

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.market_data.baostock_api import BaoStockAPI
from database.db_utils import stock_dao, db_manager
from database.models import Stock
from loguru import logger

def update_stock_basic_info():
    """
    更新所有股票的基本信息到数据库
    """
    try:
        api = BaoStockAPI()
        logger.info("开始更新股票基本信息...")
        
        # 获取所有A股股票基本信息
        stock_list = api.get_stock_basic_info()
        
        if not stock_list:
            logger.warning("未能获取到股票基本信息，请检查网络或BaoStock API状态")
            return
        
        # 保存到数据库
        saved_count = api.save_stock_basic_to_db(stock_list)
        logger.info(f"股票基本信息更新完成，共处理 {saved_count} 只股票")
        
    except Exception as e:
        logger.error(f"更新股票基本信息失败: {e}")
    finally:
        api.logout()

def update_stock_history_data(days: int = None):
    """
    更新所有股票的历史日K线数据
    
    Args:
        days: 更新最近N天的数据. 如果为None, 则进行全量更新 (从2015-01-01开始).
    """
    try:
        api = BaoStockAPI()
        
        if days:
            end_date = datetime.now()
            start_date = (end_date - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = end_date.strftime('%Y-%m-%d')
            logger.info(f"开始更新最近 {days} 天的股票历史K线数据...")
        else:
            start_date = '2015-01-01'
            end_date = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"开始全量更新所有股票的历史K线数据，起始日期: {start_date}...")

        # 从数据库获取所有股票代码
        with db_manager.get_session() as session:
            all_stocks = session.query(Stock).filter(Stock.is_active == True).all()
            stock_codes = [(stock.id, stock.code) for stock in all_stocks]
        
        if not stock_codes:
            logger.warning("数据库中没有股票信息，请先运行 update_stock_basic_info()")
            return
            
        total_stocks = len(stock_codes)
        logger.info(f"将要更新 {total_stocks} 只股票的历史数据...")
        
        for i, (stock_id, stock_code) in enumerate(stock_codes):
            try:
                if i % 100 == 0:
                    logger.info(f"进度: {i}/{total_stocks}")
                
                # 获取历史数据
                price_data = api.get_stock_history_data(stock_code, start_date, end_date)
                
                if price_data:
                    # 保存到数据库
                    api.save_price_data_to_db(stock_id, price_data)
                else:
                    logger.warning(f"未能获取到股票 {stock_code} 的历史数据")
            
            except Exception as e:
                logger.error(f"更新股票 {stock_code} 数据时出错: {e}")
                continue
        
        logger.info("所有股票历史K线数据更新完成")
        
    except Exception as e:
        logger.error(f"更新所有股票历史数据失败: {e}")
    finally:
        api.logout()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="更新股票数据脚本")
    parser.add_argument('--mode', type=str, default='full', choices=['full', 'daily'], help="模式: 'full' for 全量更新, 'daily' for 增量更新 (最近60天)")
    args = parser.parse_args()

    log_file = f"logs/update_stock_data_{args.mode}_{{time}}.log"
    logger.add(log_file, rotation="10 MB")
    
    if args.mode == 'full':
        logger.info("执行全量数据更新...")
        # 1. 更新基础信息
        update_stock_basic_info()
        # 2. 更新全部历史K线 (自2015年起)
        update_stock_history_data(days=None)
        logger.info("全量数据更新完成.")
    elif args.mode == 'daily':
        logger.info("执行日度增量更新...")
        # 只更新最近60天的数据，保证数据连续性并补充周末节假日可能缺失的数据
        update_stock_history_data(days=60)
        logger.info("日度增量更新完成.")
    else:
        logger.warning("无效的模式参数。请使用 'full' 或 'daily'.") 