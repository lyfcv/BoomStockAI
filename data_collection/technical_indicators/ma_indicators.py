"""
移动平均线指标计算模块

包含简单移动平均线(SMA)和指数移动平均线(EMA)的计算
"""

import pandas as pd
import numpy as np
from typing import Union, List


def calculate_ma(data: pd.DataFrame, price_column: str = 'close', periods: Union[int, List[int]] = [5, 10, 20, 30]) -> pd.DataFrame:
    """
    计算简单移动平均线 (Simple Moving Average, SMA)
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        periods (Union[int, List[int]]): 计算周期，可以是单个数字或数字列表
    
    Returns:
        pd.DataFrame: 包含原始数据和MA指标的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    if result[price_column].dtype == 'object':
        result[price_column] = pd.to_numeric(result[price_column], errors='coerce')
    
    # 处理单个周期的情况
    if isinstance(periods, int):
        periods = [periods]
    
    # 计算各个周期的移动平均线
    for period in periods:
        ma_column = f'MA{period}'
        result[ma_column] = result[price_column].rolling(window=period, min_periods=period).mean()
    
    return result


def calculate_ema(data: pd.DataFrame, price_column: str = 'close', periods: Union[int, List[int]] = [12, 26]) -> pd.DataFrame:
    """
    计算指数移动平均线 (Exponential Moving Average, EMA)
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        periods (Union[int, List[int]]): 计算周期，可以是单个数字或数字列表
    
    Returns:
        pd.DataFrame: 包含原始数据和EMA指标的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    if result[price_column].dtype == 'object':
        result[price_column] = pd.to_numeric(result[price_column], errors='coerce')
    
    # 处理单个周期的情况
    if isinstance(periods, int):
        periods = [periods]
    
    # 计算各个周期的指数移动平均线
    for period in periods:
        ema_column = f'EMA{period}'
        result[ema_column] = result[price_column].ewm(span=period, adjust=False).mean()
    
    return result


def calculate_multi_ma(data: pd.DataFrame, price_column: str = 'close') -> pd.DataFrame:
    """
    计算多周期移动平均线组合
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
    
    Returns:
        pd.DataFrame: 包含多个周期MA的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    if result[price_column].dtype == 'object':
        result[price_column] = pd.to_numeric(result[price_column], errors='coerce')
    
    # 常用的移动平均线周期
    periods = [5, 10, 20, 30, 60, 120, 250]
    
    for period in periods:
        ma_column = f'MA{period}'
        result[ma_column] = result[price_column].rolling(window=period, min_periods=period).mean()
    
    return result


def get_ma_signals(data: pd.DataFrame, short_period: int = 5, long_period: int = 20) -> pd.DataFrame:
    """
    基于移动平均线生成交易信号
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        short_period (int): 短期MA周期
        long_period (int): 长期MA周期
    
    Returns:
        pd.DataFrame: 包含MA信号的DataFrame
    """
    result = calculate_ma(data, periods=[short_period, long_period])
    
    short_ma = f'MA{short_period}'
    long_ma = f'MA{long_period}'
    
    # 生成交易信号
    result['MA_Signal'] = 0
    result.loc[result[short_ma] > result[long_ma], 'MA_Signal'] = 1  # 买入信号
    result.loc[result[short_ma] < result[long_ma], 'MA_Signal'] = -1  # 卖出信号
    
    # 检测金叉和死叉
    result['MA_Cross'] = 0
    ma_diff = result[short_ma] - result[long_ma]
    ma_diff_prev = ma_diff.shift(1)
    
    # 金叉：短期MA从下方穿越长期MA
    result.loc[(ma_diff > 0) & (ma_diff_prev <= 0), 'MA_Cross'] = 1
    # 死叉：短期MA从上方穿越长期MA
    result.loc[(ma_diff < 0) & (ma_diff_prev >= 0), 'MA_Cross'] = -1
    
    return result


if __name__ == "__main__":
    # 示例用法
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from data_collection.market_data.history_k_data import get_k_data
    
    # 获取测试数据
    print("获取测试数据...")
    data = get_k_data('sh.600000', 50, 'd')
    
    if data is not None:
        print("计算移动平均线...")
        
        # 计算MA
        ma_data = calculate_ma(data, periods=[5, 10, 20])
        print(f"\nMA计算结果（前5行）:")
        print(ma_data[['date', 'close', 'MA5', 'MA10', 'MA20']].head())
        
        # 计算EMA
        ema_data = calculate_ema(data, periods=[12, 26])
        print(f"\nEMA计算结果（前5行）:")
        print(ema_data[['date', 'close', 'EMA12', 'EMA26']].head())
        
        # 生成交易信号
        signal_data = get_ma_signals(data)
        print(f"\nMA交易信号（前10行）:")
        print(signal_data[['date', 'close', 'MA5', 'MA20', 'MA_Signal', 'MA_Cross']].head(10))
    else:
        print("数据获取失败") 