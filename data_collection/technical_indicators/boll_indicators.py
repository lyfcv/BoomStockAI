"""
布林带指标计算模块

布林带(Bollinger Bands)是一种技术分析工具，包含：
- 中轨：移动平均线
- 上轨：中轨 + N倍标准差
- 下轨：中轨 - N倍标准差
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_boll(data: pd.DataFrame, price_column: str = 'close', period: int = 20, std_multiplier: float = 2.0) -> pd.DataFrame:
    """
    计算布林带指标 (Bollinger Bands)
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        period (int): 计算周期，默认20
        std_multiplier (float): 标准差倍数，默认2.0
    
    Returns:
        pd.DataFrame: 包含原始数据和布林带指标的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    if result[price_column].dtype == 'object':
        result[price_column] = pd.to_numeric(result[price_column], errors='coerce')
    
    # 确保数据按日期升序排序（最早的在前面）
    if 'date' in result.columns:
        result = result.sort_values('date').reset_index(drop=True)
    
    # 计算中轨（移动平均线）
    result['BOLL_MID'] = result[price_column].rolling(window=period, min_periods=1).mean()
    
    # 计算标准差
    rolling_std = result[price_column].rolling(window=period, min_periods=1).std()
    
    # 计算上轨和下轨
    result['BOLL_UPPER'] = result['BOLL_MID'] + (rolling_std * std_multiplier)
    result['BOLL_LOWER'] = result['BOLL_MID'] - (rolling_std * std_multiplier)
    
    # 计算布林带宽度（上轨与下轨的差值）
    result['BOLL_WIDTH'] = result['BOLL_UPPER'] - result['BOLL_LOWER']
    
    # 计算价格在布林带中的位置（%B指标）
    result['BOLL_PB'] = (result[price_column] - result['BOLL_LOWER']) / (result['BOLL_UPPER'] - result['BOLL_LOWER'])
    
    return result


def get_boll_signals(data: pd.DataFrame, price_column: str = 'close') -> pd.DataFrame:
    """
    基于布林带生成交易信号
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
    
    Returns:
        pd.DataFrame: 包含布林带信号的DataFrame
    """
    result = calculate_boll(data, price_column)
    
    # 初始化信号列
    result['BOLL_Signal'] = 0
    result['BOLL_Position'] = 'MIDDLE'
    
    # 价格位置判断
    result.loc[result[price_column] >= result['BOLL_UPPER'], 'BOLL_Position'] = 'UPPER'
    result.loc[result[price_column] <= result['BOLL_LOWER'], 'BOLL_Position'] = 'LOWER'
    
    # 生成交易信号
    # 价格触及下轨：买入信号
    result.loc[result[price_column] <= result['BOLL_LOWER'], 'BOLL_Signal'] = 1
    # 价格触及上轨：卖出信号
    result.loc[result[price_column] >= result['BOLL_UPPER'], 'BOLL_Signal'] = -1
    
    # 检测突破信号
    result['BOLL_Breakout'] = 0
    
    # 向上突破上轨
    upper_breakout = (result[price_column] > result['BOLL_UPPER']) & (result[price_column].shift(1) <= result['BOLL_UPPER'].shift(1))
    result.loc[upper_breakout, 'BOLL_Breakout'] = 1
    
    # 向下突破下轨
    lower_breakout = (result[price_column] < result['BOLL_LOWER']) & (result[price_column].shift(1) >= result['BOLL_LOWER'].shift(1))
    result.loc[lower_breakout, 'BOLL_Breakout'] = -1
    
    return result


def calculate_boll_squeeze(data: pd.DataFrame, price_column: str = 'close', period: int = 20, squeeze_threshold: float = 0.1) -> pd.DataFrame:
    """
    检测布林带收缩（Bollinger Band Squeeze）
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        period (int): 计算周期，默认20
        squeeze_threshold (float): 收缩阈值，默认0.1
    
    Returns:
        pd.DataFrame: 包含布林带收缩指标的DataFrame
    """
    result = calculate_boll(data, price_column, period)
    
    # 计算布林带宽度的移动平均
    result['BOLL_WIDTH_MA'] = result['BOLL_WIDTH'].rolling(window=period).mean()
    
    # 计算相对宽度
    result['BOLL_WIDTH_RATIO'] = result['BOLL_WIDTH'] / result['BOLL_WIDTH_MA']
    
    # 检测收缩状态
    result['BOLL_Squeeze'] = result['BOLL_WIDTH_RATIO'] < squeeze_threshold
    
    # 检测收缩结束（可能的突破信号）
    squeeze_end = (~result['BOLL_Squeeze']) & (result['BOLL_Squeeze'].shift(1))
    result['BOLL_Squeeze_End'] = squeeze_end
    
    return result


def analyze_boll_pattern(data: pd.DataFrame, price_column: str = 'close') -> pd.DataFrame:
    """
    分析布林带形态
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
    
    Returns:
        pd.DataFrame: 包含布林带形态分析的DataFrame
    """
    result = get_boll_signals(data, price_column)
    
    # 分析价格与布林带的关系
    result['BOLL_Trend'] = 'SIDEWAYS'
    
    # 判断趋势
    mid_trend = result['BOLL_MID'] - result['BOLL_MID'].shift(5)
    result.loc[mid_trend > 0, 'BOLL_Trend'] = 'UPTREND'
    result.loc[mid_trend < 0, 'BOLL_Trend'] = 'DOWNTREND'
    
    # 计算布林带斜率
    result['BOLL_UPPER_SLOPE'] = result['BOLL_UPPER'] - result['BOLL_UPPER'].shift(1)
    result['BOLL_LOWER_SLOPE'] = result['BOLL_LOWER'] - result['BOLL_LOWER'].shift(1)
    result['BOLL_MID_SLOPE'] = result['BOLL_MID'] - result['BOLL_MID'].shift(1)
    
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
        print("计算布林带指标...")
        
        # 计算布林带
        boll_data = calculate_boll(data)
        print(f"\n布林带计算结果（前5行）:")
        print(boll_data[['date', 'close', 'BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER', 'BOLL_PB']].head())
        
        # 生成交易信号
        signal_data = get_boll_signals(data)
        print(f"\n布林带交易信号（前10行）:")
        print(signal_data[['date', 'close', 'BOLL_Position', 'BOLL_Signal', 'BOLL_Breakout']].head(10))
        
        # 检测布林带收缩
        squeeze_data = calculate_boll_squeeze(data)
        print(f"\n布林带收缩检测（前10行）:")
        print(squeeze_data[['date', 'close', 'BOLL_WIDTH_RATIO', 'BOLL_Squeeze', 'BOLL_Squeeze_End']].head(10))
    else:
        print("数据获取失败") 