#!/usr/bin/env python3
"""
股票数据库管理系统
提供完整的股票数据库初始化、数据导入、维护功能
"""
import os
import sys
import yaml
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import DatabaseManager, StockDataDAO
from database.models import Base, Stock, StockPrice, MarketIndex, MarketIndexPrice
from data_collection.market_data.baostock_api import BaoStockAPI


class StockDatabaseManager:
    """股票数据库管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化数据库管理器"""
        self.db_manager = DatabaseManager(config_path)
        self.stock_dao = StockDataDAO(self.db_manager)
        self.baostock_api = BaoStockAPI(config_path)
        
        # 主要指数代码
        self.major_indices = {
            'sh.000001': '上证指数',
            'sz.399001': '深证成指', 
            'sz.399006': '创业板指',
            'sh.000688': '科创50',
            'sz.399300': '沪深300',
            'sz.399905': '中证500'
        }
        
    def init_database(self, force_recreate: bool = False):
        """初始化数据库"""
        logger.info("开始初始化股票数据库...")
        
        try:
            # 测试数据库连接
            if not self.db_manager.test_connection():
                raise Exception("数据库连接失败")
            
            # 如果需要强制重建，先删除所有表
            if force_recreate:
                logger.warning("强制重建数据库表...")
                self.db_manager.drop_tables()
            
            # 创建所有表
            self.db_manager.create_tables()
            logger.info("数据库表创建完成")
            
            # 初始化基础数据
            self._init_basic_data()
            
            logger.info("股票数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _init_basic_data(self):
        """初始化基础数据"""
        logger.info("开始初始化基础数据...")
        
        # 初始化股票基本信息
        self._init_stock_basic_info()
        
        # 初始化指数基本信息
        self._init_index_basic_info()
        
        logger.info("基础数据初始化完成")
    
    def _init_stock_basic_info(self):
        """初始化股票基本信息"""
        logger.info("正在获取股票基本信息...")
        
        try:
            # 从BaoStock获取所有股票信息
            stock_list = self.baostock_api.get_stock_basic_info()
            if not stock_list:
                logger.warning("未获取到股票基本信息")
                return
            
            # 保存到数据库
            saved_count = self.baostock_api.save_stock_basic_to_db(stock_list)
            logger.info(f"股票基本信息初始化完成，共保存 {saved_count} 只股票")
            
        except Exception as e:
            logger.error(f"股票基本信息初始化失败: {e}")
    
    def _init_index_basic_info(self):
        """初始化指数基本信息"""
        logger.info("正在初始化指数基本信息...")
        
        try:
            index_list = []
            for code, name in self.major_indices.items():
                market = 'SH' if code.startswith('sh.') else 'SZ'
                index_list.append({
                    'code': code,
                    'name': name,
                    'market': market,
                    'category': '综合指数',
                    'is_active': True
                })
            
            # 保存指数基本信息
            saved_count = self.baostock_api.save_index_basic_to_db(index_list)
            logger.info(f"指数基本信息初始化完成，共保存 {saved_count} 个指数")
            
        except Exception as e:
            logger.error(f"指数基本信息初始化失败: {e}")
    
    def update_stock_data(self, codes: List[str] = None, days: int = 30):
        """更新股票价格数据"""
        logger.info(f"开始更新股票价格数据，回溯 {days} 天...")
        
        try:
            if codes is None:
                # 获取所有活跃股票代码
                codes = self._get_active_stock_codes()
            
            if not codes:
                logger.warning("没有找到需要更新的股票代码")
                return
            
            # 批量更新股票数据
            results = self.baostock_api.batch_update_stock_data(codes, days)
            
            logger.info(f"股票数据更新完成:")
            logger.info(f"  - 成功: {results['success_count']} 只")
            logger.info(f"  - 失败: {results['failed_count']} 只")
            logger.info(f"  - 总记录数: {results['total_records']} 条")
            
            if results['failed_codes']:
                logger.warning(f"更新失败的股票: {results['failed_codes'][:10]}...")
                
        except Exception as e:
            logger.error(f"股票数据更新失败: {e}")
    
    def update_index_data(self, days: int = 30):
        """更新指数数据"""
        logger.info(f"开始更新指数数据，回溯 {days} 天...")
        
        try:
            index_codes = list(self.major_indices.keys())
            results = self.baostock_api.batch_update_index_data(index_codes, days)
            
            logger.info(f"指数数据更新完成:")
            logger.info(f"  - 成功: {results['success_count']} 个")
            logger.info(f"  - 失败: {results['failed_count']} 个")
            logger.info(f"  - 总记录数: {results['total_records']} 条")
            
        except Exception as e:
            logger.error(f"指数数据更新失败: {e}")
    
    def _get_active_stock_codes(self, limit: int = None) -> List[str]:
        """获取活跃股票代码列表"""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Stock.code).filter(Stock.is_active == True)
                if limit:
                    query = query.limit(limit)
                
                codes = [row[0] for row in query.all()]
                logger.info(f"获取到 {len(codes)} 只活跃股票")
                return codes
                
        except Exception as e:
            logger.error(f"获取股票代码列表失败: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        stats = {}
        
        try:
            with self.db_manager.get_session() as session:
                # 股票统计
                stock_count = session.query(Stock).count()
                active_stock_count = session.query(Stock).filter(Stock.is_active == True).count()
                
                # 价格数据统计
                price_count = session.query(StockPrice).count()
                
                # 指数统计
                index_count = session.query(MarketIndex).count()
                index_price_count = session.query(MarketIndexPrice).count()
                
                # 最新数据日期
                latest_price_date = session.query(StockPrice.trade_date).order_by(
                    StockPrice.trade_date.desc()
                ).first()
                
                stats = {
                    'stocks': {
                        'total': stock_count,
                        'active': active_stock_count,
                        'inactive': stock_count - active_stock_count
                    },
                    'price_data': {
                        'total_records': price_count,
                        'latest_date': latest_price_date[0] if latest_price_date else None
                    },
                    'indices': {
                        'total': index_count,
                        'price_records': index_price_count
                    }
                }
                
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """清理旧数据"""
        logger.info(f"开始清理 {days_to_keep} 天前的数据...")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self.db_manager.get_session() as session:
                # 清理旧的价格数据
                deleted_prices = session.query(StockPrice).filter(
                    StockPrice.trade_date < cutoff_date
                ).delete()
                
                # 清理旧的指数数据
                deleted_index_prices = session.query(MarketIndexPrice).filter(
                    MarketIndexPrice.trade_date < cutoff_date
                ).delete()
                
                session.commit()
                
                logger.info(f"数据清理完成:")
                logger.info(f"  - 删除股价记录: {deleted_prices} 条")
                logger.info(f"  - 删除指数记录: {deleted_index_prices} 条")
                
        except Exception as e:
            logger.error(f"数据清理失败: {e}")
    
    def export_data(self, output_dir: str = "data_export"):
        """导出数据到CSV文件"""
        logger.info(f"开始导出数据到 {output_dir}...")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with self.db_manager.get_session() as session:
                # 导出股票基本信息
                stocks_df = pd.read_sql(
                    "SELECT * FROM stocks WHERE is_active = true",
                    self.db_manager.engine
                )
                stocks_df.to_csv(f"{output_dir}/stocks.csv", index=False, encoding='utf-8')
                
                # 导出最近30天的价格数据
                cutoff_date = datetime.now() - timedelta(days=30)
                prices_df = pd.read_sql(
                    f"SELECT sp.*, s.code, s.name FROM stock_prices sp "
                    f"JOIN stocks s ON sp.stock_id = s.id "
                    f"WHERE sp.trade_date >= '{cutoff_date.strftime('%Y-%m-%d')}'",
                    self.db_manager.engine
                )
                prices_df.to_csv(f"{output_dir}/stock_prices.csv", index=False, encoding='utf-8')
                
                # 导出指数数据
                indices_df = pd.read_sql("SELECT * FROM market_indices", self.db_manager.engine)
                indices_df.to_csv(f"{output_dir}/indices.csv", index=False, encoding='utf-8')
                
                index_prices_df = pd.read_sql(
                    f"SELECT mip.*, mi.code, mi.name FROM market_index_prices mip "
                    f"JOIN market_indices mi ON mip.index_id = mi.id "
                    f"WHERE mip.trade_date >= '{cutoff_date.strftime('%Y-%m-%d')}'",
                    self.db_manager.engine
                )
                index_prices_df.to_csv(f"{output_dir}/index_prices.csv", index=False, encoding='utf-8')
                
                logger.info(f"数据导出完成到 {output_dir}/")
                
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
    
    def backup_database(self, backup_path: str = None):
        """备份数据库"""
        if not backup_path:
            backup_path = f"backup/stock_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        logger.info(f"开始备份数据库到 {backup_path}...")
        
        try:
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 使用pg_dump进行备份
            db_config = self.db_manager.config['database']
            cmd = (
                f"pg_dump -h {db_config['host']} -p {db_config['port']} "
                f"-U {db_config['user']} -d {db_config['name']} "
                f"-f {backup_path}"
            )
            
            os.system(cmd)
            logger.info(f"数据库备份完成: {backup_path}")
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
    
    def close(self):
        """关闭连接"""
        try:
            self.baostock_api.logout()
            logger.info("数据库管理器已关闭")
        except:
            pass


def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票数据库管理工具')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--force', action='store_true', help='强制重建数据库')
    parser.add_argument('--update-stocks', action='store_true', help='更新股票数据')
    parser.add_argument('--update-indices', action='store_true', help='更新指数数据')
    parser.add_argument('--days', type=int, default=30, help='更新天数')
    parser.add_argument('--stats', action='store_true', help='显示数据库统计')
    parser.add_argument('--export', type=str, help='导出数据到指定目录')
    parser.add_argument('--cleanup', type=int, help='清理N天前的旧数据')
    parser.add_argument('--backup', type=str, help='备份数据库到指定路径')
    
    args = parser.parse_args()
    
    # 初始化管理器
    db_manager = StockDatabaseManager()
    
    try:
        if args.init:
            db_manager.init_database(force_recreate=args.force)
        
        if args.update_stocks:
            db_manager.update_stock_data(days=args.days)
        
        if args.update_indices:
            db_manager.update_index_data(days=args.days)
        
        if args.stats:
            stats = db_manager.get_database_stats()
            print("\n=== 数据库统计信息 ===")
            print(f"股票总数: {stats['stocks']['total']}")
            print(f"活跃股票: {stats['stocks']['active']}")
            print(f"价格数据记录: {stats['price_data']['total_records']}")
            print(f"最新数据日期: {stats['price_data']['latest_date']}")
            print(f"指数总数: {stats['indices']['total']}")
            print(f"指数价格记录: {stats['indices']['price_records']}")
        
        if args.export:
            db_manager.export_data(args.export)
        
        if args.cleanup:
            db_manager.cleanup_old_data(args.cleanup)
        
        if args.backup:
            db_manager.backup_database(args.backup)
            
    except KeyboardInterrupt:
        logger.info("操作被用户中断")
    except Exception as e:
        logger.error(f"操作失败: {e}")
    finally:
        db_manager.close()


if __name__ == "__main__":
    main() 