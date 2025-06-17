"""
平台突破选股策略
基于平台整理后的放量突破形态进行选股
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from database.db_utils import db_manager, stock_dao
from database.models import Stock, StockPrice, StockAnalysis, TradingSignal
from data_collection.market_data.baostock_api import BaoStockAPI
from strategy_center.models.technical_indicators import PlatformBreakoutAnalyzer


class PlatformBreakoutStrategy:
    """平台突破选股策略"""
    
    def __init__(self, config: Dict = None):
        """
        初始化策略
        
        Args:
            config: 策略配置参数
        """
        self.strategy_name = "platform_breakout"
        self.config = config or self._get_default_config()
        
        # 初始化分析器
        self.analyzer = PlatformBreakoutAnalyzer(
            window=self.config['platform_window'],
            max_volatility=self.config['max_volatility'],
            volume_threshold=self.config['volume_threshold']
        )
        
        # 初始化数据API
        self.data_api = BaoStockAPI()
        
        logger.info(f"平台突破策略初始化完成，配置: {self.config}")
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'platform_window': 20,          # 平台检测窗口期
            'max_volatility': 0.15,         # 最大波动率（15%）
            'volume_threshold': 2.0,        # 成交量放大倍数
            'price_threshold': 0.03,        # 价格涨幅阈值（3%）
            'min_platform_days': 15,        # 最小平台天数
            'lookback_days': 60,            # 数据回看天数
            'min_price': 5.0,               # 最低股价过滤
            'max_price': 200.0,             # 最高股价过滤
            'min_market_cap': 50,           # 最小市值（亿元）
            'exclude_st': True,             # 排除ST股票
            'min_volume': 10000000,         # 最小成交量（元）
            'rsi_range': [30, 80],          # RSI范围
            'score_threshold': 60           # 最低评分阈值
        }
    
    def screen_stocks(self, stock_pool: List[str] = None) -> List[Dict]:
        """
        执行选股筛选
        
        Args:
            stock_pool: 股票池，如果为None则使用全市场
            
        Returns:
            筛选结果列表
        """
        try:
            logger.info("开始执行平台突破选股...")
            
            # 获取股票池
            if stock_pool is None:
                stock_pool = self._get_stock_universe()
            
            logger.info(f"股票池大小: {len(stock_pool)}")
            
            # 批量分析股票
            results = []
            total_stocks = len(stock_pool)
            
            for i, stock_code in enumerate(stock_pool):
                try:
                    if i % 50 == 0:
                        logger.info(f"分析进度: {i}/{total_stocks} ({i/total_stocks*100:.1f}%)")
                    
                    # 分析单只股票
                    analysis_result = self._analyze_single_stock(stock_code)
                    
                    if analysis_result and analysis_result['recommendation']['score'] >= self.config['score_threshold']:
                        results.append(analysis_result)
                        
                except Exception as e:
                    logger.warning(f"分析股票 {stock_code} 失败: {e}")
                    continue
            
            # 按评分排序
            results.sort(key=lambda x: x['recommendation']['score'], reverse=True)
            
            logger.info(f"平台突破选股完成，共筛选出 {len(results)} 只股票")
            
            return results
            
        except Exception as e:
            logger.error(f"平台突破选股失败: {e}")
            return []
    
    def _get_stock_universe(self) -> List[str]:
        """获取股票池"""
        try:
            with db_manager.get_session() as session:
                # 查询活跃股票
                stocks = session.query(Stock).filter(
                    Stock.is_active == True
                ).all()
                
                stock_codes = []
                for stock in stocks:
                    # 基础过滤
                    if self.config['exclude_st'] and 'ST' in stock.name:
                        continue
                    
                    # 只选择主板和创业板股票
                    if stock.code.startswith(('sh.6', 'sz.00', 'sz.30')):
                        stock_codes.append(stock.code)
                
                return stock_codes
                
        except Exception as e:
            logger.error(f"获取股票池失败: {e}")
            return []
    
    def _analyze_single_stock(self, stock_code: str) -> Optional[Dict]:
        """
        分析单只股票
        
        Args:
            stock_code: 股票代码
            
        Returns:
            分析结果字典
        """
        try:
            # 获取股票基本信息
            stock_info = stock_dao.get_stock_by_code(stock_code)
            if not stock_info:
                return None
            
            # 获取历史价格数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=self.config['lookback_days'])).strftime('%Y-%m-%d')
            
            price_data = stock_dao.get_stock_prices(stock_info['id'], start_date, end_date)
            
            if len(price_data) < self.config['platform_window'] + 10:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(price_data)
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 基础过滤
            latest_price = df.iloc[-1]['close_price']
            latest_volume = df.iloc[-1]['amount'] if 'amount' in df.columns else 0
            
            if (latest_price < self.config['min_price'] or 
                latest_price > self.config['max_price'] or
                latest_volume < self.config['min_volume']):
                return None
            
            # 执行技术分析
            analysis_result = self.analyzer.analyze(df)
            
            if not analysis_result['success']:
                return None
            
            # 添加股票基本信息
            analysis_result['stock_info'] = stock_info
            analysis_result['latest_price'] = latest_price
            analysis_result['latest_volume'] = latest_volume
            
            # 额外的过滤条件
            if not self._additional_filters(analysis_result):
                return None
            
            return analysis_result
            
        except Exception as e:
            logger.warning(f"分析股票 {stock_code} 失败: {e}")
            return None
    
    def _additional_filters(self, analysis_result: Dict) -> bool:
        """
        额外的过滤条件
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            是否通过过滤
        """
        try:
            trend_analysis = analysis_result.get('trend_analysis', {})
            
            # RSI过滤
            rsi = trend_analysis.get('rsi', 50)
            if not (self.config['rsi_range'][0] <= rsi <= self.config['rsi_range'][1]):
                return False
            
            # 平台形态确认
            platform_analysis = analysis_result.get('platform_analysis', {})
            if not platform_analysis.get('is_platform', False) and not analysis_result.get('breakout_analysis', {}).get('has_breakout', False):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"额外过滤失败: {e}")
            return False
    
    def generate_trading_signals(self, analysis_results: List[Dict]) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            交易信号列表
        """
        signals = []
        
        for result in analysis_results:
            try:
                stock_info = result['stock_info']
                recommendation = result['recommendation']
                breakout_analysis = result['breakout_analysis']
                
                # 生成买入信号
                if recommendation['action'] in ['买入', '强烈买入'] and breakout_analysis.get('has_breakout', False):
                    signal = {
                        'stock_code': stock_info['code'],
                        'stock_name': stock_info['name'],
                        'signal_type': '买入',
                        'strategy_name': self.strategy_name,
                        'price': result['latest_price'],
                        'confidence': recommendation['confidence'],
                        'score': recommendation['score'],
                        'reasons': recommendation['reasons'],
                        'breakout_strength': breakout_analysis['breakout_strength'],
                        'volume_ratio': breakout_analysis['volume_ratio'],
                        'signal_date': datetime.now(),
                        'platform_high': result['platform_analysis']['platform_high'],
                        'platform_low': result['platform_analysis']['platform_low']
                    }
                    signals.append(signal)
                
            except Exception as e:
                logger.warning(f"生成交易信号失败: {e}")
                continue
        
        return signals
    
    def save_analysis_results(self, analysis_results: List[Dict]) -> int:
        """
        保存分析结果到数据库
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            保存的记录数
        """
        saved_count = 0
        
        try:
            with db_manager.get_session() as session:
                for result in analysis_results:
                    try:
                        stock_info = result['stock_info']
                        
                        # 创建分析记录
                        analysis = StockAnalysis(
                            stock_id=stock_info['id'],
                            analysis_date=datetime.now(),
                            strategy_name=self.strategy_name,
                            technical_score=result['recommendation']['score'],
                            technical_signals={
                                'platform_analysis': result['platform_analysis'],
                                'breakout_analysis': result['breakout_analysis'],
                                'trend_analysis': result['trend_analysis']
                            },
                            total_score=result['recommendation']['score'],
                            recommendation=result['recommendation']['action'],
                            confidence=result['recommendation']['confidence'],
                            ai_analysis='\n'.join(result['recommendation']['reasons'])
                        )
                        
                        session.add(analysis)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"保存分析结果失败: {e}")
                        continue
                
                session.commit()
                
        except Exception as e:
            logger.error(f"批量保存分析结果失败: {e}")
        
        logger.info(f"保存分析结果完成，共保存 {saved_count} 条记录")
        return saved_count
    
    def save_trading_signals(self, signals: List[Dict]) -> int:
        """
        保存交易信号到数据库
        
        Args:
            signals: 交易信号列表
            
        Returns:
            保存的信号数
        """
        saved_count = 0
        
        try:
            with db_manager.get_session() as session:
                for signal in signals:
                    try:
                        # 获取股票ID
                        stock_info = stock_dao.get_stock_by_code(signal['stock_code'])
                        if not stock_info:
                            continue
                        
                        # 创建交易信号记录
                        trading_signal = TradingSignal(
                            stock_id=stock_info['id'],
                            signal_date=signal['signal_date'],
                            signal_type=signal['signal_type'],
                            strategy_name=signal['strategy_name'],
                            price=signal['price'],
                            confidence=signal['confidence'],
                            reason=f"平台突破信号 - 评分: {signal['score']:.0f}分, 突破强度: {signal['breakout_strength']:.0f}分, 成交量放大: {signal['volume_ratio']:.1f}倍"
                        )
                        
                        session.add(trading_signal)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"保存交易信号失败: {e}")
                        continue
                
                session.commit()
                
        except Exception as e:
            logger.error(f"批量保存交易信号失败: {e}")
        
        logger.info(f"保存交易信号完成，共保存 {saved_count} 条记录")
        return saved_count
    
    def run_strategy(self, stock_pool: List[str] = None, save_results: bool = True) -> Dict:
        """
        运行完整的策略流程
        
        Args:
            stock_pool: 股票池
            save_results: 是否保存结果
            
        Returns:
            策略运行结果
        """
        try:
            start_time = datetime.now()
            logger.info("开始运行平台突破策略...")
            
            # 1. 执行选股
            analysis_results = self.screen_stocks(stock_pool)
            
            # 2. 生成交易信号
            trading_signals = self.generate_trading_signals(analysis_results)
            
            # 3. 保存结果（可选）
            saved_analysis = 0
            saved_signals = 0
            
            if save_results:
                saved_analysis = self.save_analysis_results(analysis_results)
                saved_signals = self.save_trading_signals(trading_signals)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 统计结果
            result_summary = {
                'strategy_name': self.strategy_name,
                'execution_time': duration,
                'total_analyzed': len(stock_pool) if stock_pool else 0,
                'qualified_stocks': len(analysis_results),
                'trading_signals': len(trading_signals),
                'saved_analysis': saved_analysis,
                'saved_signals': saved_signals,
                'top_picks': analysis_results[:10],  # 前10只股票
                'all_signals': trading_signals
            }
            
            logger.info(f"平台突破策略运行完成，耗时: {duration:.2f}秒")
            logger.info(f"筛选出 {len(analysis_results)} 只符合条件的股票")
            logger.info(f"生成 {len(trading_signals)} 个交易信号")
            
            return result_summary
            
        except Exception as e:
            logger.error(f"平台突破策略运行失败: {e}")
            return {
                'strategy_name': self.strategy_name,
                'error': str(e),
                'success': False
            }
    
    def get_strategy_performance(self, days: int = 30) -> Dict:
        """
        获取策略历史表现
        
        Args:
            days: 回看天数
            
        Returns:
            策略表现统计
        """
        try:
            with db_manager.get_session() as session:
                # 查询历史信号
                start_date = datetime.now() - timedelta(days=days)
                
                signals = session.query(TradingSignal).filter(
                    TradingSignal.strategy_name == self.strategy_name,
                    TradingSignal.signal_date >= start_date
                ).all()
                
                if not signals:
                    return {'message': '暂无历史信号数据'}
                
                # 统计信号表现
                total_signals = len(signals)
                avg_confidence = sum(s.confidence for s in signals) / total_signals
                
                # 按日期分组统计
                daily_stats = {}
                for signal in signals:
                    date_key = signal.signal_date.strftime('%Y-%m-%d')
                    if date_key not in daily_stats:
                        daily_stats[date_key] = []
                    daily_stats[date_key].append(signal)
                
                return {
                    'total_signals': total_signals,
                    'avg_confidence': avg_confidence,
                    'daily_signals': len(daily_stats),
                    'avg_daily_signals': total_signals / len(daily_stats),
                    'date_range': f"{start_date.strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}"
                }
                
        except Exception as e:
            logger.error(f"获取策略表现失败: {e}")
            return {'error': str(e)}


def create_platform_breakout_strategy(config: Dict = None) -> PlatformBreakoutStrategy:
    """
    创建平台突破策略实例
    
    Args:
        config: 策略配置
        
    Returns:
        策略实例
    """
    return PlatformBreakoutStrategy(config) 