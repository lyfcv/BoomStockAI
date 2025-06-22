"""
综合技术指标计算器

提供一站式的技术指标计算服务，包括MA、BOLL、MACD、KDJ、RSI等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union

from .ma_indicators import calculate_ma, calculate_ema, get_ma_signals
from .boll_indicators import calculate_boll, get_boll_signals
from .macd_indicators import calculate_macd, get_macd_signals
from .kdj_indicators import calculate_kdj, get_kdj_signals
from .rsi_indicators import calculate_rsi, get_rsi_signals


class TechnicalIndicatorCalculator:
    """技术指标计算器类"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化技术指标计算器
        
        Args:
            data (pd.DataFrame): 包含OHLCV数据的DataFrame
        """
        self.data = data.copy()
        self.indicators = {}
        
    def calculate_all_indicators(self, ma_periods: List[int] = [5, 10, 20, 30],
                               ema_periods: List[int] = [12, 26],
                               boll_period: int = 20, boll_std: float = 2.0,
                               macd_fast: int = 12, macd_slow: int = 26, macd_signal: int = 9,
                               kdj_k: int = 9, kdj_d: int = 3, kdj_j: int = 3,
                               rsi_period: int = 14) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            ma_periods: MA周期列表
            ema_periods: EMA周期列表
            boll_period: 布林带周期
            boll_std: 布林带标准差倍数
            macd_fast: MACD快线周期
            macd_slow: MACD慢线周期
            macd_signal: MACD信号线周期
            kdj_k: KDJ K值周期
            kdj_d: KDJ D值周期
            kdj_j: KDJ J值周期
            rsi_period: RSI周期
        
        Returns:
            pd.DataFrame: 包含所有技术指标的DataFrame
        """
        result = self.data.copy()
        
        # 计算MA指标
        ma_data = calculate_ma(result, periods=ma_periods)
        for period in ma_periods:
            result[f'MA{period}'] = ma_data[f'MA{period}']
        
        # 计算EMA指标
        ema_data = calculate_ema(result, periods=ema_periods)
        for period in ema_periods:
            result[f'EMA{period}'] = ema_data[f'EMA{period}']
        
        # 计算布林带
        boll_data = calculate_boll(result, period=boll_period, std_multiplier=boll_std)
        for col in ['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER', 'BOLL_WIDTH', 'BOLL_PB']:
            result[col] = boll_data[col]
        
        # 计算MACD
        macd_data = calculate_macd(result, fast_period=macd_fast, slow_period=macd_slow, signal_period=macd_signal)
        for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']:
            result[col] = macd_data[col]
        
        # 计算KDJ
        kdj_data = calculate_kdj(result, k_period=kdj_k, d_period=kdj_d, j_period=kdj_j)
        for col in ['K', 'D', 'J']:
            result[col] = kdj_data[col]
        
        # 计算RSI
        rsi_data = calculate_rsi(result, period=rsi_period)
        result['RSI'] = rsi_data['RSI']
        
        self.indicators = result
        return result
    
    def get_trading_signals(self) -> pd.DataFrame:
        """
        获取所有技术指标的交易信号
        
        Returns:
            pd.DataFrame: 包含交易信号的DataFrame
        """
        if self.indicators.empty:
            raise ValueError("请先调用 calculate_all_indicators() 计算指标")
        
        result = self.indicators.copy()
        
        # 获取各指标的交易信号
        ma_signals = get_ma_signals(self.data)
        boll_signals = get_boll_signals(self.data)
        macd_signals = get_macd_signals(self.data)
        kdj_signals = get_kdj_signals(self.data)
        rsi_signals = get_rsi_signals(self.data)
        
        # 合并信号
        signal_columns = {
            'MA_Signal': ma_signals['MA_Signal'],
            'MA_Cross': ma_signals['MA_Cross'],
            'BOLL_Signal': boll_signals['BOLL_Signal'],
            'BOLL_Position': boll_signals['BOLL_Position'],
            'MACD_Cross': macd_signals['MACD_Cross'],
            'MACD_Position': macd_signals['MACD_Position'],
            'KDJ_Cross': kdj_signals['KDJ_Cross'],
            'KDJ_Position': kdj_signals['KDJ_Position'],
            'RSI_Signal': rsi_signals['RSI_Signal'],
            'RSI_Position': rsi_signals['RSI_Position']
        }
        
        for col, data in signal_columns.items():
            result[col] = data
        
        return result
    
    def get_comprehensive_signals(self, min_signals: int = 2) -> pd.DataFrame:
        """
        获取综合交易信号（多个指标确认）
        
        Args:
            min_signals: 最少需要的确认信号数量
        
        Returns:
            pd.DataFrame: 包含综合信号的DataFrame
        """
        signals_data = self.get_trading_signals()
        result = signals_data.copy()
        
        # 统计买入信号数量
        buy_signals = 0
        buy_signals += (result['MA_Cross'] == 1).astype(int)
        buy_signals += (result['BOLL_Signal'] == 1).astype(int)
        buy_signals += (result['MACD_Cross'] == 1).astype(int)
        buy_signals += (result['KDJ_Cross'] == 1).astype(int)
        buy_signals += (result['RSI_Signal'] == 1).astype(int)
        
        # 统计卖出信号数量
        sell_signals = 0
        sell_signals += (result['MA_Cross'] == -1).astype(int)
        sell_signals += (result['BOLL_Signal'] == -1).astype(int)
        sell_signals += (result['MACD_Cross'] == -1).astype(int)
        sell_signals += (result['KDJ_Cross'] == -1).astype(int)
        sell_signals += (result['RSI_Signal'] == -1).astype(int)
        
        # 生成综合信号
        result['Buy_Signal_Count'] = buy_signals
        result['Sell_Signal_Count'] = sell_signals
        result['Comprehensive_Signal'] = 0
        
        # 当买入信号数量达到阈值时
        result.loc[buy_signals >= min_signals, 'Comprehensive_Signal'] = 1
        # 当卖出信号数量达到阈值时
        result.loc[sell_signals >= min_signals, 'Comprehensive_Signal'] = -1
        
        return result
    
    def analyze_trend_strength(self) -> pd.DataFrame:
        """
        分析趋势强度
        
        Returns:
            pd.DataFrame: 包含趋势强度分析的DataFrame
        """
        if self.indicators.empty:
            raise ValueError("请先调用 calculate_all_indicators() 计算指标")
        
        result = self.indicators.copy()
        
        # 趋势强度评分
        result['Trend_Score'] = 0
        
        # MA趋势评分
        if 'MA5' in result.columns and 'MA20' in result.columns:
            result['Trend_Score'] += (result['MA5'] > result['MA20']).astype(int) * 2 - 1
        
        # MACD趋势评分
        if 'MACD' in result.columns and 'MACD_Signal' in result.columns:
            result['Trend_Score'] += (result['MACD'] > result['MACD_Signal']).astype(int) * 2 - 1
        
        # RSI趋势评分
        if 'RSI' in result.columns:
            result['Trend_Score'] += (result['RSI'] > 50).astype(int) * 2 - 1
        
        # KDJ趋势评分
        if 'K' in result.columns and 'D' in result.columns:
            result['Trend_Score'] += (result['K'] > result['D']).astype(int) * 2 - 1
        
        # 趋势强度分类
        result['Trend_Strength'] = 'NEUTRAL'
        result.loc[result['Trend_Score'] >= 3, 'Trend_Strength'] = 'STRONG_BULL'
        result.loc[result['Trend_Score'] == 2, 'Trend_Strength'] = 'BULL'
        result.loc[result['Trend_Score'] == 1, 'Trend_Strength'] = 'WEAK_BULL'
        result.loc[result['Trend_Score'] == -1, 'Trend_Strength'] = 'WEAK_BEAR'
        result.loc[result['Trend_Score'] == -2, 'Trend_Strength'] = 'BEAR'
        result.loc[result['Trend_Score'] <= -3, 'Trend_Strength'] = 'STRONG_BEAR'
        
        return result
    
    def get_indicator_summary(self) -> Dict:
        """
        获取指标摘要信息
        
        Returns:
            Dict: 指标摘要字典
        """
        if self.indicators.empty:
            raise ValueError("请先调用 calculate_all_indicators() 计算指标")
        
        latest = self.indicators.iloc[-1]
        
        summary = {
            'date': latest.get('date', 'N/A'),
            'close': float(latest.get('close', 0)),
            'indicators': {
                'MA5': float(latest.get('MA5', 0)) if 'MA5' in latest else None,
                'MA20': float(latest.get('MA20', 0)) if 'MA20' in latest else None,
                'BOLL_UPPER': float(latest.get('BOLL_UPPER', 0)) if 'BOLL_UPPER' in latest else None,
                'BOLL_LOWER': float(latest.get('BOLL_LOWER', 0)) if 'BOLL_LOWER' in latest else None,
                'MACD': float(latest.get('MACD', 0)) if 'MACD' in latest else None,
                'MACD_Signal': float(latest.get('MACD_Signal', 0)) if 'MACD_Signal' in latest else None,
                'RSI': float(latest.get('RSI', 0)) if 'RSI' in latest else None,
                'K': float(latest.get('K', 0)) if 'K' in latest else None,
                'D': float(latest.get('D', 0)) if 'D' in latest else None,
                'J': float(latest.get('J', 0)) if 'J' in latest else None,
            }
        }
        
        return summary


def calculate_technical_indicators(data: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    便捷函数：计算技术指标
    
    Args:
        data: K线数据
        **kwargs: 指标参数
    
    Returns:
        pd.DataFrame: 包含技术指标的数据
    """
    calculator = TechnicalIndicatorCalculator(data)
    return calculator.calculate_all_indicators(**kwargs)


def get_trading_signals(data: pd.DataFrame) -> pd.DataFrame:
    """
    便捷函数：获取交易信号
    
    Args:
        data: K线数据
    
    Returns:
        pd.DataFrame: 包含交易信号的数据
    """
    calculator = TechnicalIndicatorCalculator(data)
    calculator.calculate_all_indicators()
    return calculator.get_trading_signals()


if __name__ == "__main__":
    # 示例用法
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from data_collection.market_data.history_k_data import get_k_data
    
    # 获取测试数据
    print("获取测试数据...")
    data = get_k_data('sh.600000', 100, 'd')
    
    if data is not None:
        print("创建技术指标计算器...")
        calculator = TechnicalIndicatorCalculator(data)
        
        # 计算所有指标
        indicators = calculator.calculate_all_indicators()
        print(f"\n技术指标计算完成，共 {len(indicators)} 条数据")
        
        # 显示最新指标值
        summary = calculator.get_indicator_summary()
        print(f"\n最新指标摘要:")
        print(f"日期: {summary['date']}")
        print(f"收盘价: {summary['close']:.2f}")
        print(f"MA5: {summary['indicators']['MA5']:.2f}")
        print(f"MA20: {summary['indicators']['MA20']:.2f}")
        print(f"RSI: {summary['indicators']['RSI']:.2f}")
        print(f"MACD: {summary['indicators']['MACD']:.4f}")
        print(f"K: {summary['indicators']['K']:.2f}")
        print(f"D: {summary['indicators']['D']:.2f}")
        
        # 获取交易信号
        signals = calculator.get_trading_signals()
        recent_signals = signals[
            (signals['MA_Cross'] != 0) | 
            (signals['MACD_Cross'] != 0) | 
            (signals['KDJ_Cross'] != 0) |
            (signals['RSI_Signal'] != 0)
        ].tail(10)
        
        if not recent_signals.empty:
            print(f"\n最近的交易信号:")
            print(recent_signals[['date', 'close', 'MA_Cross', 'MACD_Cross', 'KDJ_Cross', 'RSI_Signal']])
        
        # 获取综合信号
        comprehensive = calculator.get_comprehensive_signals(min_signals=2)
        comp_signals = comprehensive[comprehensive['Comprehensive_Signal'] != 0].tail(5)
        
        if not comp_signals.empty:
            print(f"\n综合交易信号:")
            print(comp_signals[['date', 'close', 'Buy_Signal_Count', 'Sell_Signal_Count', 'Comprehensive_Signal']])
        
        # 分析趋势强度
        trend_analysis = calculator.analyze_trend_strength()
        print(f"\n最新趋势强度: {trend_analysis.iloc[-1]['Trend_Strength']}")
        print(f"趋势评分: {trend_analysis.iloc[-1]['Trend_Score']}")
        
    else:
        print("数据获取失败") 