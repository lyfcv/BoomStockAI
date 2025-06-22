"""
MACD指标计算模块

MACD (Moving Average Convergence Divergence) 指数平滑移动平均线，包含：
- MACD线：快线EMA - 慢线EMA
- Signal线：MACD线的EMA
- Histogram：MACD线 - Signal线
"""

import pandas as pd
import numpy as np


def calculate_macd(data: pd.DataFrame, price_column: str = 'close', 
                  fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    计算MACD指标 (Moving Average Convergence Divergence)
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        fast_period (int): 快线EMA周期，默认12
        slow_period (int): 慢线EMA周期，默认26
        signal_period (int): 信号线EMA周期，默认9
    
    Returns:
        pd.DataFrame: 包含原始数据和MACD指标的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    if result[price_column].dtype == 'object':
        result[price_column] = pd.to_numeric(result[price_column], errors='coerce')
    
    # 计算快线和慢线EMA
    ema_fast = result[price_column].ewm(span=fast_period, adjust=False).mean()
    ema_slow = result[price_column].ewm(span=slow_period, adjust=False).mean()
    
    # 计算MACD线
    result['MACD'] = ema_fast - ema_slow
    
    # 计算Signal线（MACD的EMA）
    result['MACD_Signal'] = result['MACD'].ewm(span=signal_period, adjust=False).mean()
    
    # 计算Histogram（MACD柱状图）
    result['MACD_Histogram'] = result['MACD'] - result['MACD_Signal']
    
    # 保存EMA值用于分析
    result[f'EMA{fast_period}'] = ema_fast
    result[f'EMA{slow_period}'] = ema_slow
    
    return result


def get_macd_signals(data: pd.DataFrame, price_column: str = 'close') -> pd.DataFrame:
    """
    基于MACD生成交易信号
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
    
    Returns:
        pd.DataFrame: 包含MACD信号的DataFrame
    """
    result = calculate_macd(data, price_column)
    
    # 初始化信号列
    result['MACD_Buy_Signal'] = 0
    result['MACD_Sell_Signal'] = 0
    result['MACD_Cross'] = 0
    result['MACD_Position'] = 'NEUTRAL'
    
    # MACD线与Signal线的交叉
    macd_cross_up = (result['MACD'] > result['MACD_Signal']) & (result['MACD'].shift(1) <= result['MACD_Signal'].shift(1))
    macd_cross_down = (result['MACD'] < result['MACD_Signal']) & (result['MACD'].shift(1) >= result['MACD_Signal'].shift(1))
    
    # 金叉：MACD线从下方穿越Signal线
    result.loc[macd_cross_up, 'MACD_Cross'] = 1
    result.loc[macd_cross_up, 'MACD_Buy_Signal'] = 1
    
    # 死叉：MACD线从上方穿越Signal线
    result.loc[macd_cross_down, 'MACD_Cross'] = -1
    result.loc[macd_cross_down, 'MACD_Sell_Signal'] = 1
    
    # 判断MACD位置
    result.loc[result['MACD'] > result['MACD_Signal'], 'MACD_Position'] = 'BULLISH'
    result.loc[result['MACD'] < result['MACD_Signal'], 'MACD_Position'] = 'BEARISH'
    
    # 零轴交叉信号
    result['MACD_Zero_Cross'] = 0
    zero_cross_up = (result['MACD'] > 0) & (result['MACD'].shift(1) <= 0)
    zero_cross_down = (result['MACD'] < 0) & (result['MACD'].shift(1) >= 0)
    
    result.loc[zero_cross_up, 'MACD_Zero_Cross'] = 1
    result.loc[zero_cross_down, 'MACD_Zero_Cross'] = -1
    
    return result


def analyze_macd_divergence(data: pd.DataFrame, price_column: str = 'close', lookback: int = 5) -> pd.DataFrame:
    """
    分析MACD背离
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        lookback (int): 回看周期，默认5
    
    Returns:
        pd.DataFrame: 包含MACD背离分析的DataFrame
    """
    result = calculate_macd(data, price_column)
    
    # 初始化背离信号
    result['MACD_Bullish_Divergence'] = False
    result['MACD_Bearish_Divergence'] = False
    
    # 计算价格和MACD的局部极值
    price_high = result[price_column].rolling(window=lookback*2+1, center=True).max()
    price_low = result[price_column].rolling(window=lookback*2+1, center=True).min()
    macd_high = result['MACD'].rolling(window=lookback*2+1, center=True).max()
    macd_low = result['MACD'].rolling(window=lookback*2+1, center=True).min()
    
    # 找到局部高点和低点
    is_price_high = result[price_column] == price_high
    is_price_low = result[price_column] == price_low
    is_macd_high = result['MACD'] == macd_high
    is_macd_low = result['MACD'] == macd_low
    
    # 标记局部极值点
    result['Price_High'] = is_price_high
    result['Price_Low'] = is_price_low
    result['MACD_High'] = is_macd_high
    result['MACD_Low'] = is_macd_low
    
    # 简化的背离检测（实际应用中可能需要更复杂的逻辑）
    for i in range(lookback, len(result) - lookback):
        # 检测看涨背离：价格创新低，MACD未创新低
        if is_price_low.iloc[i]:
            prev_low_idx = None
            for j in range(i - lookback, max(0, i - lookback*3), -1):
                if is_price_low.iloc[j]:
                    prev_low_idx = j
                    break
            
            if prev_low_idx is not None:
                if (result[price_column].iloc[i] < result[price_column].iloc[prev_low_idx] and
                    result['MACD'].iloc[i] > result['MACD'].iloc[prev_low_idx]):
                    result.loc[result.index[i], 'MACD_Bullish_Divergence'] = True
        
        # 检测看跌背离：价格创新高，MACD未创新高
        if is_price_high.iloc[i]:
            prev_high_idx = None
            for j in range(i - lookback, max(0, i - lookback*3), -1):
                if is_price_high.iloc[j]:
                    prev_high_idx = j
                    break
            
            if prev_high_idx is not None:
                if (result[price_column].iloc[i] > result[price_column].iloc[prev_high_idx] and
                    result['MACD'].iloc[i] < result['MACD'].iloc[prev_high_idx]):
                    result.loc[result.index[i], 'MACD_Bearish_Divergence'] = True
    
    return result


def calculate_macd_momentum(data: pd.DataFrame, price_column: str = 'close') -> pd.DataFrame:
    """
    计算MACD动量指标
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
    
    Returns:
        pd.DataFrame: 包含MACD动量分析的DataFrame
    """
    result = calculate_macd(data, price_column)
    
    # 计算MACD变化率
    result['MACD_Change'] = result['MACD'] - result['MACD'].shift(1)
    result['MACD_Signal_Change'] = result['MACD_Signal'] - result['MACD_Signal'].shift(1)
    result['MACD_Histogram_Change'] = result['MACD_Histogram'] - result['MACD_Histogram'].shift(1)
    
    # 计算MACD加速度
    result['MACD_Acceleration'] = result['MACD_Change'] - result['MACD_Change'].shift(1)
    
    # 判断MACD趋势强度
    result['MACD_Strength'] = 'WEAK'
    
    # 强势上涨
    strong_up = (result['MACD'] > result['MACD_Signal']) & (result['MACD_Change'] > 0) & (result['MACD_Acceleration'] > 0)
    result.loc[strong_up, 'MACD_Strength'] = 'STRONG_UP'
    
    # 强势下跌
    strong_down = (result['MACD'] < result['MACD_Signal']) & (result['MACD_Change'] < 0) & (result['MACD_Acceleration'] < 0)
    result.loc[strong_down, 'MACD_Strength'] = 'STRONG_DOWN'
    
    return result


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
        print("计算MACD指标...")
        
        # 计算MACD
        macd_data = calculate_macd(data)
        print(f"\nMACD计算结果（前5行）:")
        print(macd_data[['date', 'close', 'MACD', 'MACD_Signal', 'MACD_Histogram']].head())
        
        # 生成交易信号
        signal_data = get_macd_signals(data)
        print(f"\nMACD交易信号（前10行）:")
        signals = signal_data[signal_data['MACD_Cross'] != 0]
        if not signals.empty:
            print(signals[['date', 'close', 'MACD', 'MACD_Signal', 'MACD_Cross', 'MACD_Position']].head(10))
        else:
            print("当前数据中未发现MACD交叉信号")
        
        # 分析MACD动量
        momentum_data = calculate_macd_momentum(data)
        print(f"\nMACD动量分析（前5行）:")
        print(momentum_data[['date', 'close', 'MACD_Change', 'MACD_Acceleration', 'MACD_Strength']].head())
    else:
        print("数据获取失败") 