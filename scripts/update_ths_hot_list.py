import sys
import os
from datetime import datetime

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from data_collection.market_data.ths_crawler import ths_crawler
from database.db_utils import ths_data_dao, db_manager
from loguru import logger

def update_all_ths_hot_lists():
    """
    使用爬虫获取所有同花顺热榜数据并保存到数据库
    """
    logger.info("开始更新同花顺热榜数据...")
    
    total_saved = 0
    
    try:
        # 确保数据库表存在
        db_manager.create_tables()
        
        # 使用爬虫获取所有热榜数据
        logger.info("正在获取所有热榜数据...")
        all_hot_lists = ths_crawler.get_all_hot_lists(limit=100)
        
        for market_type, hot_list_data in all_hot_lists.items():
            try:
                if hot_list_data and len(hot_list_data) > 0:
                    # 保存到数据库
                    saved_count = ths_data_dao.save_ths_hot_list(hot_list_data, market_type)
                    total_saved += saved_count
                    logger.info(f"{market_type}热榜数据保存成功，共{saved_count}条")
                else:
                    logger.warning(f"{market_type}热榜数据为空")
                    
            except Exception as e:
                logger.error(f"保存{market_type}热榜数据失败: {e}")
                continue
        
        logger.info(f"同花顺热榜数据更新完成，共保存{total_saved}条数据")
        return total_saved
        
    except Exception as e:
        logger.error(f"更新同花顺热榜数据失败: {e}")
        return 0

def update_single_hot_list(market_type: str, limit: int = 50):
    """
    更新单个热榜类型的数据
    
    Args:
        market_type: 热榜类型
        limit: 获取数量限制
    """
    try:
        logger.info(f"开始更新{market_type}热榜数据...")
        
        # 确保数据库表存在
        db_manager.create_tables()
        
        # 获取热榜数据
        hot_list_data = ths_crawler.get_hot_list(market_type, limit)
        
        if hot_list_data and len(hot_list_data) > 0:
            # 保存到数据库
            saved_count = ths_data_dao.save_ths_hot_list(hot_list_data, market_type)
            logger.info(f"{market_type}热榜数据更新成功，共保存{saved_count}条")
            return saved_count
        else:
            logger.warning(f"{market_type}热榜数据为空")
            return 0
            
    except Exception as e:
        logger.error(f"更新{market_type}热榜数据失败: {e}")
        return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='更新同花顺热榜数据')
    parser.add_argument('--market', type=str, help='指定热榜类型 (热股, ETF, 可转债, 行业板块, 概念板块, 期货, 港股, 热基, 美股)')
    parser.add_argument('--limit', type=int, default=50, help='获取数量限制')
    
    args = parser.parse_args()
    
    if args.market:
        # 更新单个热榜
        update_single_hot_list(args.market, args.limit)
    else:
        # 更新所有热榜
        update_all_ths_hot_lists() 