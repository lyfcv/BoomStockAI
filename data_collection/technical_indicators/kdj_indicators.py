"""
KDJ指标计算模块

KDJ指标是随机指标的扩展，包含：
- K值：快速随机指标
- D值：慢速随机指标  
- J值：3*K - 2*D
"""

import pandas as pd
import numpy as np


def calculate_kdj(data: pd.DataFrame, high_column: str = 'high', low_column: str = 'low', 
                 close_column: str = 'close', k_period: int = 9, d_period: int = 3, j_period: int = 3) -> pd.DataFrame:
    """
    计算KDJ指标 (KDJ Stochastic Oscillator)
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        high_column (str): 最高价列名，默认为'high'
        low_column (str): 最低价列名，默认为'low'
        close_column (str): 收盘价列名，默认为'close'
        k_period (int): K值计算周期，默认9
        d_period (int): D值平滑周期，默认3
        j_period (int): J值平滑周期，默认3
    
    Returns:
        pd.DataFrame: 包含原始数据和KDJ指标的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    for col in [high_column, low_column, close_column]:
        if result[col].dtype == 'object':
            result[col] = pd.to_numeric(result[col], errors='coerce')
    
    # 计算最高价和最低价的滚动窗口
    highest_high = result[high_column].rolling(window=k_period, min_periods=1).max()
    lowest_low = result[low_column].rolling(window=k_period, min_periods=1).min()
    
    # 计算RSV (Raw Stochastic Value)
    rsv = (result[close_column] - lowest_low) / (highest_high - lowest_low) * 100
    rsv = rsv.fillna(50)  # 填充NaN值为50
    
    # 计算K值（使用指数移动平均）
    result['K'] = rsv.ewm(alpha=1/d_period, adjust=False).mean()
    
    # 计算D值（K值的指数移动平均）
    result['D'] = result['K'].ewm(alpha=1/j_period, adjust=False).mean()
    
    # 计算J值
    result['J'] = 3 * result['K'] - 2 * result['D']
    
    # 保存RSV用于分析
    result['RSV'] = rsv
    result['Highest_High'] = highest_high
    result['Lowest_Low'] = lowest_low
    
    return result


def get_kdj_signals(data: pd.DataFrame, high_column: str = 'high', low_column: str = 'low', 
                   close_column: str = 'close', overbought: float = 80, oversold: float = 20) -> pd.DataFrame:
    """
    基于KDJ生成交易信号
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        high_column (str): 最高价列名
        low_column (str): 最低价列名
        close_column (str): 收盘价列名
        overbought (float): 超买阈值，默认80
        oversold (float): 超卖阈值，默认20
    
    Returns:
        pd.DataFrame: 包含KDJ信号的DataFrame
    """
    result = calculate_kdj(data, high_column, low_column, close_column)
    
    # 初始化信号列
    result['KDJ_Signal'] = 0
    result['KDJ_Position'] = 'NEUTRAL'
    result['KDJ_Cross'] = 0
    result['KDJ_Overbought'] = False
    result['KDJ_Oversold'] = False
    
    # 判断超买超卖
    result.loc[result['K'] >= overbought, 'KDJ_Overbought'] = True
    result.loc[result['K'] <= oversold, 'KDJ_Oversold'] = True
    
    # 判断位置
    result.loc[result['K'] >= overbought, 'KDJ_Position'] = 'OVERBOUGHT'
    result.loc[result['K'] <= oversold, 'KDJ_Position'] = 'OVERSOLD'
    result.loc[(result['K'] > oversold) & (result['K'] < overbought), 'KDJ_Position'] = 'NEUTRAL'
    
    # K线与D线交叉信号
    k_cross_d_up = (result['K'] > result['D']) & (result['K'].shift(1) <= result['D'].shift(1))
    k_cross_d_down = (result['K'] < result['D']) & (result['K'].shift(1) >= result['D'].shift(1))
    
    # 金叉：K线从下方穿越D线
    result.loc[k_cross_d_up, 'KDJ_Cross'] = 1
    result.loc[k_cross_d_up & (result['K'] <= oversold), 'KDJ_Signal'] = 1  # 低位金叉买入
    
    # 死叉：K线从上方穿越D线
    result.loc[k_cross_d_down, 'KDJ_Cross'] = -1
    result.loc[k_cross_d_down & (result['K'] >= overbought), 'KDJ_Signal'] = -1  # 高位死叉卖出
    
    # J值极值信号
    result['KDJ_J_Extreme'] = 0
    result.loc[result['J'] >= 100, 'KDJ_J_Extreme'] = 1  # J值超过100，极度超买
    result.loc[result['J'] <= 0, 'KDJ_J_Extreme'] = -1   # J值低于0，极度超卖
    
    return result


def analyze_kdj_divergence(data: pd.DataFrame, high_column: str = 'high', low_column: str = 'low', 
                          close_column: str = 'close', lookback: int = 5) -> pd.DataFrame:
    """
    分析KDJ背离
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        high_column (str): 最高价列名
        low_column (str): 最低价列名
        close_column (str): 收盘价列名
        lookback (int): 回看周期，默认5
    
    Returns:
        pd.DataFrame: 包含KDJ背离分析的DataFrame
    """
    result = calculate_kdj(data, high_column, low_column, close_column)
    
    # 初始化背离信号
    result['KDJ_Bullish_Divergence'] = False
    result['KDJ_Bearish_Divergence'] = False
    
    # 计算价格和KDJ的局部极值
    price_high = result[close_column].rolling(window=lookback*2+1, center=True).max()
    price_low = result[close_column].rolling(window=lookback*2+1, center=True).min()
    k_high = result['K'].rolling(window=lookback*2+1, center=True).max()
    k_low = result['K'].rolling(window=lookback*2+1, center=True).min()
    
    # 找到局部高点和低点
    is_price_high = result[close_column] == price_high
    is_price_low = result[close_column] == price_low
    is_k_high = result['K'] == k_high
    is_k_low = result['K'] == k_low
    
    # 标记局部极值点
    result['Price_High'] = is_price_high
    result['Price_Low'] = is_price_low
    result['K_High'] = is_k_high
    result['K_Low'] = is_k_low
    
    # 简化的背离检测
    for i in range(lookback, len(result) - lookback):
        # 检测看涨背离：价格创新低，K值未创新低
        if is_price_low.iloc[i]:
            prev_low_idx = None
            for j in range(i - lookback, max(0, i - lookback*3), -1):
                if is_price_low.iloc[j]:
                    prev_low_idx = j
                    break
            
            if prev_low_idx is not None:
                if (result[close_column].iloc[i] < result[close_column].iloc[prev_low_idx] and
                    result['K'].iloc[i] > result['K'].iloc[prev_low_idx]):
                    result.loc[result.index[i], 'KDJ_Bullish_Divergence'] = True
        
        # 检测看跌背离：价格创新高，K值未创新高
        if is_price_high.iloc[i]:
            prev_high_idx = None
            for j in range(i - lookback, max(0, i - lookback*3), -1):
                if is_price_high.iloc[j]:
                    prev_high_idx = j
                    break
            
            if prev_high_idx is not None:
                if (result[close_column].iloc[i] > result[close_column].iloc[prev_high_idx] and
                    result['K'].iloc[i] < result['K'].iloc[prev_high_idx]):
                    result.loc[result.index[i], 'KDJ_Bearish_Divergence'] = True
    
    return result


def calculate_kdj_trend(data: pd.DataFrame, high_column: str = 'high', low_column: str = 'low', 
                       close_column: str = 'close') -> pd.DataFrame:
    """
    分析KDJ趋势强度
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        high_column (str): 最高价列名
        low_column (str): 最低价列名
        close_column (str): 收盘价列名
    
    Returns:
        pd.DataFrame: 包含KDJ趋势分析的DataFrame
    """
    result = calculate_kdj(data, high_column, low_column, close_column)
    
    # 计算KDJ变化率
    result['K_Change'] = result['K'] - result['K'].shift(1)
    result['D_Change'] = result['D'] - result['D'].shift(1)
    result['J_Change'] = result['J'] - result['J'].shift(1)
    
    # 计算KDJ平均值
    result['KDJ_Average'] = (result['K'] + result['D'] + result['J']) / 3
    
    # 判断KDJ趋势
    result['KDJ_Trend'] = 'SIDEWAYS'
    
    # 强势上涨：K、D、J都在上涨
    strong_up = (result['K_Change'] > 0) & (result['D_Change'] > 0) & (result['J_Change'] > 0)
    result.loc[strong_up, 'KDJ_Trend'] = 'STRONG_UP'
    
    # 强势下跌：K、D、J都在下跌
    strong_down = (result['K_Change'] < 0) & (result['D_Change'] < 0) & (result['J_Change'] < 0)
    result.loc[strong_down, 'KDJ_Trend'] = 'STRONG_DOWN'
    
    # 判断KDJ共振
    result['KDJ_Resonance'] = False
    
    # 多头共振：K > D > J 且都在上涨
    bull_resonance = (result['K'] > result['D']) & (result['D'] > result['J']) & strong_up
    result.loc[bull_resonance, 'KDJ_Resonance'] = True
    
    # 空头共振：K < D < J 且都在下跌
    bear_resonance = (result['K'] < result['D']) & (result['D'] < result['J']) & strong_down
    result.loc[bear_resonance, 'KDJ_Resonance'] = True
    
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
        print("计算KDJ指标...")
        
        # 计算KDJ
        kdj_data = calculate_kdj(data)
        print(f"\nKDJ计算结果（前5行）:")
        print(kdj_data[['date', 'close', 'K', 'D', 'J']].head())
        
        # 生成交易信号
        signal_data = get_kdj_signals(data)
        print(f"\nKDJ交易信号（前10行）:")
        signals = signal_data[signal_data['KDJ_Cross'] != 0]
        if not signals.empty:
            print(signals[['date', 'close', 'K', 'D', 'KDJ_Cross', 'KDJ_Position']].head(10))
        else:
            print("当前数据中未发现KDJ交叉信号")
        
        # 分析KDJ趋势
        trend_data = calculate_kdj_trend(data)
        print(f"\nKDJ趋势分析（前5行）:")
        print(trend_data[['date', 'close', 'KDJ_Average', 'KDJ_Trend', 'KDJ_Resonance']].head())
    else:
        print("数据获取失败") 