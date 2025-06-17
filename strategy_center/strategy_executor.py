"""
策略执行器
用于管理和执行各种选股策略
"""
import asyncio
import schedule
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger
import yaml
import os

from strategy_center.strategies.platform_breakout_strategy import create_platform_breakout_strategy
from database.db_utils import db_manager


class StrategyExecutor:
    """策略执行器"""
    
    def __init__(self, config_path: str = "config/strategy_config.yaml"):
        """
        初始化策略执行器
        
        Args:
            config_path: 策略配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.strategies = {}
        self.execution_history = []
        
        # 初始化策略
        self._initialize_strategies()
        
        logger.info("策略执行器初始化完成")
    
    def _load_config(self) -> Dict:
        """加载策略配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                # 使用默认配置
                config = self._get_default_config()
                self._save_default_config()
            
            return config
            
        except Exception as e:
            logger.error(f"加载策略配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认策略配置"""
        return {
            'strategies': {
                'platform_breakout': {
                    'enabled': True,
                    'schedule': {
                        'daily': '09:30',  # 每日9:30执行
                        'enabled': True
                    },
                    'config': {
                        'platform_window': 20,
                        'max_volatility': 0.15,
                        'volume_threshold': 2.0,
                        'price_threshold': 0.03,
                        'min_platform_days': 15,
                        'lookback_days': 60,
                        'min_price': 5.0,
                        'max_price': 200.0,
                        'exclude_st': True,
                        'min_volume': 10000000,
                        'rsi_range': [30, 80],
                        'score_threshold': 60
                    }
                }
            },
            'execution': {
                'max_concurrent': 3,
                'timeout': 3600,  # 1小时超时
                'retry_times': 2,
                'save_results': True
            },
            'notification': {
                'enabled': False,
                'webhook_url': '',
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'username': '',
                    'password': '',
                    'recipients': []
                }
            }
        }
    
    def _save_default_config(self):
        """保存默认配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"默认策略配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"保存默认配置失败: {e}")
    
    def _initialize_strategies(self):
        """初始化所有策略"""
        try:
            strategies_config = self.config.get('strategies', {})
            
            # 初始化平台突破策略
            if strategies_config.get('platform_breakout', {}).get('enabled', False):
                strategy_config = strategies_config['platform_breakout'].get('config', {})
                self.strategies['platform_breakout'] = create_platform_breakout_strategy(strategy_config)
                logger.info("平台突破策略已初始化")
            
            # 这里可以添加更多策略的初始化
            # if strategies_config.get('momentum_strategy', {}).get('enabled', False):
            #     self.strategies['momentum_strategy'] = create_momentum_strategy(...)
            
            logger.info(f"共初始化 {len(self.strategies)} 个策略")
            
        except Exception as e:
            logger.error(f"策略初始化失败: {e}")
    
    def execute_strategy(self, strategy_name: str, stock_pool: List[str] = None) -> Dict:
        """
        执行指定策略
        
        Args:
            strategy_name: 策略名称
            stock_pool: 股票池
            
        Returns:
            执行结果
        """
        try:
            if strategy_name not in self.strategies:
                return {
                    'success': False,
                    'message': f'策略 {strategy_name} 不存在或未启用'
                }
            
            logger.info(f"开始执行策略: {strategy_name}")
            start_time = datetime.now()
            
            # 执行策略
            strategy = self.strategies[strategy_name]
            save_results = self.config.get('execution', {}).get('save_results', True)
            
            result = strategy.run_strategy(stock_pool=stock_pool, save_results=save_results)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录执行历史
            execution_record = {
                'strategy_name': strategy_name,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'success': result.get('success', True),
                'result': result
            }
            
            self.execution_history.append(execution_record)
            
            # 发送通知（如果启用）
            if self.config.get('notification', {}).get('enabled', False):
                self._send_notification(execution_record)
            
            logger.info(f"策略 {strategy_name} 执行完成，耗时: {duration:.2f}秒")
            
            return {
                'success': True,
                'strategy_name': strategy_name,
                'execution_time': duration,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"执行策略 {strategy_name} 失败: {e}")
            return {
                'success': False,
                'strategy_name': strategy_name,
                'error': str(e)
            }
    
    def execute_all_strategies(self, stock_pool: List[str] = None) -> Dict:
        """
        执行所有启用的策略
        
        Args:
            stock_pool: 股票池
            
        Returns:
            执行结果汇总
        """
        try:
            logger.info("开始执行所有策略...")
            start_time = datetime.now()
            
            results = {}
            total_signals = 0
            
            for strategy_name in self.strategies:
                try:
                    result = self.execute_strategy(strategy_name, stock_pool)
                    results[strategy_name] = result
                    
                    if result.get('success', False):
                        strategy_result = result.get('result', {})
                        total_signals += strategy_result.get('trading_signals', 0)
                        
                except Exception as e:
                    logger.error(f"执行策略 {strategy_name} 失败: {e}")
                    results[strategy_name] = {
                        'success': False,
                        'error': str(e)
                    }
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            summary = {
                'total_strategies': len(self.strategies),
                'successful_strategies': sum(1 for r in results.values() if r.get('success', False)),
                'total_signals': total_signals,
                'execution_time': duration,
                'results': results
            }
            
            logger.info(f"所有策略执行完成，耗时: {duration:.2f}秒，共生成 {total_signals} 个信号")
            
            return summary
            
        except Exception as e:
            logger.error(f"执行所有策略失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def schedule_strategies(self):
        """设置策略定时执行"""
        try:
            strategies_config = self.config.get('strategies', {})
            
            for strategy_name, strategy_config in strategies_config.items():
                if not strategy_config.get('enabled', False):
                    continue
                
                schedule_config = strategy_config.get('schedule', {})
                if not schedule_config.get('enabled', False):
                    continue
                
                # 设置每日定时执行
                if 'daily' in schedule_config:
                    daily_time = schedule_config['daily']
                    schedule.every().day.at(daily_time).do(
                        self._scheduled_execution, strategy_name
                    )
                    logger.info(f"策略 {strategy_name} 已设置每日 {daily_time} 执行")
                
                # 设置每周定时执行
                if 'weekly' in schedule_config:
                    weekly_config = schedule_config['weekly']
                    day = weekly_config.get('day', 'monday')
                    time_str = weekly_config.get('time', '09:30')
                    
                    getattr(schedule.every(), day).at(time_str).do(
                        self._scheduled_execution, strategy_name
                    )
                    logger.info(f"策略 {strategy_name} 已设置每周{day} {time_str} 执行")
            
            logger.info("策略定时任务设置完成")
            
        except Exception as e:
            logger.error(f"设置策略定时任务失败: {e}")
    
    def _scheduled_execution(self, strategy_name: str):
        """定时执行策略的包装函数"""
        try:
            logger.info(f"定时执行策略: {strategy_name}")
            result = self.execute_strategy(strategy_name)
            
            if result.get('success', False):
                logger.info(f"定时策略 {strategy_name} 执行成功")
            else:
                logger.error(f"定时策略 {strategy_name} 执行失败: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"定时执行策略 {strategy_name} 异常: {e}")
    
    def run_scheduler(self):
        """运行定时调度器"""
        try:
            logger.info("启动策略定时调度器...")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
        except KeyboardInterrupt:
            logger.info("定时调度器已停止")
        except Exception as e:
            logger.error(f"定时调度器运行异常: {e}")
    
    def get_execution_history(self, limit: int = 50) -> List[Dict]:
        """
        获取执行历史
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            执行历史列表
        """
        return self.execution_history[-limit:]
    
    def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        try:
            status = {
                'total_strategies': len(self.strategies),
                'enabled_strategies': [],
                'last_execution': None,
                'next_scheduled': []
            }
            
            # 获取启用的策略
            strategies_config = self.config.get('strategies', {})
            for strategy_name, config in strategies_config.items():
                if config.get('enabled', False):
                    status['enabled_strategies'].append(strategy_name)
            
            # 获取最后执行时间
            if self.execution_history:
                last_execution = max(self.execution_history, key=lambda x: x['start_time'])
                status['last_execution'] = {
                    'strategy_name': last_execution['strategy_name'],
                    'time': last_execution['start_time'],
                    'success': last_execution['success']
                }
            
            # 获取下次执行时间
            jobs = schedule.jobs
            for job in jobs:
                status['next_scheduled'].append({
                    'job': str(job.job_func),
                    'next_run': job.next_run
                })
            
            return status
            
        except Exception as e:
            logger.error(f"获取策略状态失败: {e}")
            return {'error': str(e)}
    
    def _send_notification(self, execution_record: Dict):
        """发送执行结果通知"""
        try:
            notification_config = self.config.get('notification', {})
            
            if not notification_config.get('enabled', False):
                return
            
            # 构建通知消息
            strategy_name = execution_record['strategy_name']
            success = execution_record['success']
            duration = execution_record['duration']
            
            if success:
                result = execution_record['result']
                signals_count = result.get('trading_signals', 0)
                message = f"策略 {strategy_name} 执行成功\n执行时间: {duration:.2f}秒\n生成信号: {signals_count}个"
            else:
                error = execution_record.get('error', 'Unknown error')
                message = f"策略 {strategy_name} 执行失败\n错误信息: {error}"
            
            # 发送Webhook通知
            webhook_url = notification_config.get('webhook_url')
            if webhook_url:
                self._send_webhook_notification(webhook_url, message)
            
            # 发送邮件通知
            email_config = notification_config.get('email', {})
            if email_config.get('enabled', False):
                self._send_email_notification(email_config, message)
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    def _send_webhook_notification(self, webhook_url: str, message: str):
        """发送Webhook通知"""
        try:
            import requests
            
            payload = {
                'text': message,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Webhook通知发送成功")
            
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
    
    def _send_email_notification(self, email_config: Dict, message: str):
        """发送邮件通知"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['Subject'] = "BoomStockAI 策略执行通知"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP(email_config['smtp_server'], 587)
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            
            for recipient in email_config['recipients']:
                msg['To'] = recipient
                server.send_message(msg)
            
            server.quit()
            logger.info("邮件通知发送成功")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")


# 全局策略执行器实例
strategy_executor = StrategyExecutor()


def run_platform_breakout_strategy(stock_pool: List[str] = None) -> Dict:
    """
    运行平台突破策略的便捷函数
    
    Args:
        stock_pool: 股票池
        
    Returns:
        执行结果
    """
    return strategy_executor.execute_strategy('platform_breakout', stock_pool)


def run_all_strategies(stock_pool: List[str] = None) -> Dict:
    """
    运行所有策略的便捷函数
    
    Args:
        stock_pool: 股票池
        
    Returns:
        执行结果
    """
    return strategy_executor.execute_all_strategies(stock_pool)


if __name__ == "__main__":
    # 设置定时任务
    strategy_executor.schedule_strategies()
    
    # 运行调度器
    strategy_executor.run_scheduler() 