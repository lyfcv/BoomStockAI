#!/usr/bin/env python3
"""
数据更新定时任务调度器
自动定时更新股票数据、指数数据等
"""
import os
import sys
import time
import schedule
from datetime import datetime, timedelta
from loguru import logger
import threading

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.stock_database_manager import StockDatabaseManager


class DataUpdateScheduler:
    """数据更新调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.db_manager = StockDatabaseManager()
        self.is_running = False
        self.update_thread = None
        
    def start(self):
        """启动调度器"""
        logger.info("启动数据更新调度器...")
        
        # 设置定时任务
        self._setup_schedules()
        
        # 启动调度器线程
        self.is_running = True
        self.update_thread = threading.Thread(target=self._run_scheduler)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        logger.info("数据更新调度器已启动")
    
    def stop(self):
        """停止调度器"""
        logger.info("停止数据更新调度器...")
        self.is_running = False
        if self.update_thread:
            self.update_thread.join()
        self.db_manager.close()
        logger.info("数据更新调度器已停止")
    
    def _setup_schedules(self):
        """设置定时任务"""
        
        # 工作日市场开盘前更新数据 (早上8:30)
        schedule.every().monday.at("08:30").do(self._morning_update)
        schedule.every().tuesday.at("08:30").do(self._morning_update)
        schedule.every().wednesday.at("08:30").do(self._morning_update)
        schedule.every().thursday.at("08:30").do(self._morning_update)
        schedule.every().friday.at("08:30").do(self._morning_update)
        
        # 工作日收盘后更新数据 (下午16:00)
        schedule.every().monday.at("16:00").do(self._evening_update)
        schedule.every().tuesday.at("16:00").do(self._evening_update)
        schedule.every().wednesday.at("16:00").do(self._evening_update)
        schedule.every().thursday.at("16:00").do(self._evening_update)
        schedule.every().friday.at("16:00").do(self._evening_update)
        
        # 每天凌晨2点清理过期数据
        schedule.every().day.at("02:00").do(self._cleanup_data)
        
        # 每周日凌晨1点进行数据库备份
        schedule.every().sunday.at("01:00").do(self._backup_database)
        
        # 每小时检查数据完整性
        schedule.every().hour.do(self._check_data_integrity)
        
        logger.info("定时任务设置完成")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器运行错误: {e}")
                time.sleep(60)
    
    def _morning_update(self):
        """早盘前数据更新"""
        logger.info("开始早盘前数据更新...")
        
        try:
            # 更新指数数据
            self.db_manager.update_index_data(days=5)
            
            # 更新主要股票数据（限制数量避免过长时间）
            active_codes = self.db_manager._get_active_stock_codes(limit=500)
            if active_codes:
                self.db_manager.update_stock_data(codes=active_codes, days=5)
            
            logger.info("早盘前数据更新完成")
            
        except Exception as e:
            logger.error(f"早盘前数据更新失败: {e}")
    
    def _evening_update(self):
        """收盘后数据更新"""
        logger.info("开始收盘后数据更新...")
        
        try:
            # 更新指数数据
            self.db_manager.update_index_data(days=2)
            
            # 更新所有活跃股票数据
            self.db_manager.update_stock_data(days=2)
            
            logger.info("收盘后数据更新完成")
            
        except Exception as e:
            logger.error(f"收盘后数据更新失败: {e}")
    
    def _cleanup_data(self):
        """清理过期数据"""
        logger.info("开始清理过期数据...")
        
        try:
            # 保留2年的数据
            self.db_manager.cleanup_old_data(days_to_keep=730)
            logger.info("过期数据清理完成")
            
        except Exception as e:
            logger.error(f"过期数据清理失败: {e}")
    
    def _backup_database(self):
        """备份数据库"""
        logger.info("开始数据库备份...")
        
        try:
            backup_dir = "backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{backup_dir}/stock_db_backup_{timestamp}.sql"
            
            self.db_manager.backup_database(backup_path)
            logger.info("数据库备份完成")
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
    
    def _check_data_integrity(self):
        """检查数据完整性"""
        try:
            stats = self.db_manager.get_database_stats()
            
            # 检查是否有最新数据
            if stats.get('price_data', {}).get('latest_date'):
                latest_date = stats['price_data']['latest_date']
                days_old = (datetime.now().date() - latest_date.date()).days
                
                if days_old > 3:  # 数据超过3天没更新
                    logger.warning(f"数据可能过期，最新数据日期: {latest_date}")
                    # 触发数据更新
                    self._evening_update()
            
            # 记录统计信息
            logger.info(f"数据完整性检查 - 股票: {stats.get('stocks', {}).get('active', 0)}, "
                       f"价格记录: {stats.get('price_data', {}).get('total_records', 0)}")
                       
        except Exception as e:
            logger.error(f"数据完整性检查失败: {e}")
    
    def manual_update(self, update_type: str = 'all'):
        """手动触发更新"""
        logger.info(f"手动触发更新: {update_type}")
        
        try:
            if update_type in ['all', 'stocks']:
                self.db_manager.update_stock_data(days=5)
            
            if update_type in ['all', 'indices']:
                self.db_manager.update_index_data(days=5)
            
            logger.info("手动更新完成")
            
        except Exception as e:
            logger.error(f"手动更新失败: {e}")
    
    def get_next_runs(self):
        """获取下次运行时间"""
        jobs = schedule.get_jobs()
        next_runs = []
        
        for job in jobs:
            next_runs.append({
                'job': str(job.job_func),
                'next_run': job.next_run
            })
        
        return sorted(next_runs, key=lambda x: x['next_run'])


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据更新调度器')
    parser.add_argument('--daemon', action='store_true', help='后台运行')
    parser.add_argument('--manual', choices=['all', 'stocks', 'indices'], help='手动更新')
    parser.add_argument('--status', action='store_true', help='显示调度状态')
    
    args = parser.parse_args()
    
    scheduler = DataUpdateScheduler()
    
    try:
        if args.manual:
            scheduler.manual_update(args.manual)
            return
        
        if args.status:
            next_runs = scheduler.get_next_runs()
            print("\n=== 调度器状态 ===")
            for run in next_runs[:5]:  # 显示前5个任务
                print(f"{run['job']}: {run['next_run']}")
            return
        
        # 启动调度器
        scheduler.start()
        
        if args.daemon:
            # 后台运行
            logger.info("调度器在后台运行...")
            try:
                while True:
                    time.sleep(3600)  # 每小时检查一次
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在停止...")
        else:
            # 交互模式
            print("\n=== 数据更新调度器 ===")
            print("命令:")
            print("  status - 显示状态")
            print("  update [stocks|indices|all] - 手动更新")
            print("  quit - 退出")
            
            while True:
                try:
                    cmd = input("\n> ").strip().lower()
                    
                    if cmd == 'quit':
                        break
                    elif cmd == 'status':
                        stats = scheduler.db_manager.get_database_stats()
                        print(f"股票总数: {stats['stocks']['total']}")
                        print(f"活跃股票: {stats['stocks']['active']}")
                        print(f"价格记录: {stats['price_data']['total_records']}")
                        print(f"最新数据: {stats['price_data']['latest_date']}")
                    elif cmd.startswith('update'):
                        parts = cmd.split()
                        update_type = parts[1] if len(parts) > 1 else 'all'
                        scheduler.manual_update(update_type)
                    else:
                        print("未知命令")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"命令执行错误: {e}")
    
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main() 