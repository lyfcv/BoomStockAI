"""
RSI指标计算模块

RSI (Relative Strength Index) 相对强弱指标，用于衡量价格变动的速度和变化
"""

import pandas as pd
import numpy as np


def calculate_rsi(data: pd.DataFrame, price_column: str = 'close', period: int = 14) -> pd.DataFrame:
    """
    计算RSI指标 (Relative Strength Index)
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        period (int): 计算周期，默认14
    
    Returns:
        pd.DataFrame: 包含原始数据和RSI指标的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    if result[price_column].dtype == 'object':
        result[price_column] = pd.to_numeric(result[price_column], errors='coerce')
    
    # 计算价格变化
    price_change = result[price_column].diff()
    
    # 分离涨跌
    gain = price_change.where(price_change > 0, 0)
    loss = -price_change.where(price_change < 0, 0)
    
    # 计算平均涨跌幅（使用指数移动平均）
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    # 计算相对强度
    rs = avg_gain / avg_loss
    
    # 计算RSI
    result['RSI'] = 100 - (100 / (1 + rs))
    
    # 保存中间计算结果
    result['Price_Change'] = price_change
    result['Gain'] = gain
    result['Loss'] = loss
    result['Avg_Gain'] = avg_gain
    result['Avg_Loss'] = avg_loss
    result['RS'] = rs
    
    return result


def get_rsi_signals(data: pd.DataFrame, price_column: str = 'close', 
                   overbought: float = 70, oversold: float = 30) -> pd.DataFrame:
    """
    基于RSI生成交易信号
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        overbought (float): 超买阈值，默认70
        oversold (float): 超卖阈值，默认30
    
    Returns:
        pd.DataFrame: 包含RSI信号的DataFrame
    """
    result = calculate_rsi(data, price_column)
    
    # 初始化信号列
    result['RSI_Signal'] = 0
    result['RSI_Position'] = 'NEUTRAL'
    result['RSI_Overbought'] = False
    result['RSI_Oversold'] = False
    
    # 判断超买超卖
    result.loc[result['RSI'] >= overbought, 'RSI_Overbought'] = True
    result.loc[result['RSI'] <= oversold, 'RSI_Oversold'] = True
    
    # 判断位置
    result.loc[result['RSI'] >= overbought, 'RSI_Position'] = 'OVERBOUGHT'
    result.loc[result['RSI'] <= oversold, 'RSI_Position'] = 'OVERSOLD'
    result.loc[(result['RSI'] > oversold) & (result['RSI'] < overbought), 'RSI_Position'] = 'NEUTRAL'
    
    # 生成交易信号
    # 从超卖区域向上突破30：买入信号
    rsi_buy = (result['RSI'] > oversold) & (result['RSI'].shift(1) <= oversold)
    result.loc[rsi_buy, 'RSI_Signal'] = 1
    
    # 从超买区域向下突破70：卖出信号
    rsi_sell = (result['RSI'] < overbought) & (result['RSI'].shift(1) >= overbought)
    result.loc[rsi_sell, 'RSI_Signal'] = -1
    
    # RSI中线(50)交叉信号
    result['RSI_Midline_Cross'] = 0
    midline_cross_up = (result['RSI'] > 50) & (result['RSI'].shift(1) <= 50)
    midline_cross_down = (result['RSI'] < 50) & (result['RSI'].shift(1) >= 50)
    
    result.loc[midline_cross_up, 'RSI_Midline_Cross'] = 1
    result.loc[midline_cross_down, 'RSI_Midline_Cross'] = -1
    
    return result


def analyze_rsi_divergence(data: pd.DataFrame, price_column: str = 'close', lookback: int = 5) -> pd.DataFrame:
    """
    分析RSI背离
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        lookback (int): 回看周期，默认5
    
    Returns:
        pd.DataFrame: 包含RSI背离分析的DataFrame
    """
    result = calculate_rsi(data, price_column)
    
    # 初始化背离信号
    result['RSI_Bullish_Divergence'] = False
    result['RSI_Bearish_Divergence'] = False
    
    # 计算价格和RSI的局部极值
    price_high = result[price_column].rolling(window=lookback*2+1, center=True).max()
    price_low = result[price_column].rolling(window=lookback*2+1, center=True).min()
    rsi_high = result['RSI'].rolling(window=lookback*2+1, center=True).max()
    rsi_low = result['RSI'].rolling(window=lookback*2+1, center=True).min()
    
    # 找到局部高点和低点
    is_price_high = result[price_column] == price_high
    is_price_low = result[price_column] == price_low
    is_rsi_high = result['RSI'] == rsi_high
    is_rsi_low = result['RSI'] == rsi_low
    
    # 标记局部极值点
    result['Price_High'] = is_price_high
    result['Price_Low'] = is_price_low
    result['RSI_High'] = is_rsi_high
    result['RSI_Low'] = is_rsi_low
    
    # 简化的背离检测
    for i in range(lookback, len(result) - lookback):
        # 检测看涨背离：价格创新低，RSI未创新低
        if is_price_low.iloc[i]:
            prev_low_idx = None
            for j in range(i - lookback, max(0, i - lookback*3), -1):
                if is_price_low.iloc[j]:
                    prev_low_idx = j
                    break
            
            if prev_low_idx is not None:
                if (result[price_column].iloc[i] < result[price_column].iloc[prev_low_idx] and
                    result['RSI'].iloc[i] > result['RSI'].iloc[prev_low_idx]):
                    result.loc[result.index[i], 'RSI_Bullish_Divergence'] = True
        
        # 检测看跌背离：价格创新高，RSI未创新高
        if is_price_high.iloc[i]:
            prev_high_idx = None
            for j in range(i - lookback, max(0, i - lookback*3), -1):
                if is_price_high.iloc[j]:
                    prev_high_idx = j
                    break
            
            if prev_high_idx is not None:
                if (result[price_column].iloc[i] > result[price_column].iloc[prev_high_idx] and
                    result['RSI'].iloc[i] < result['RSI'].iloc[prev_high_idx]):
                    result.loc[result.index[i], 'RSI_Bearish_Divergence'] = True
    
    return result


def calculate_multi_timeframe_rsi(data: pd.DataFrame, price_column: str = 'close', 
                                 periods: list = [6, 14, 21]) -> pd.DataFrame:
    """
    计算多周期RSI
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
        periods (list): RSI周期列表，默认[6, 14, 21]
    
    Returns:
        pd.DataFrame: 包含多周期RSI的DataFrame
    """
    result = data.copy()
    
    # 确保价格列为数值类型
    if result[price_column].dtype == 'object':
        result[price_column] = pd.to_numeric(result[price_column], errors='coerce')
    
    # 计算各个周期的RSI
    for period in periods:
        rsi_data = calculate_rsi(data, price_column, period)
        result[f'RSI{period}'] = rsi_data['RSI']
    
    # 计算RSI平均值
    rsi_columns = [f'RSI{period}' for period in periods]
    result['RSI_Average'] = result[rsi_columns].mean(axis=1)
    
    # 判断RSI共振
    result['RSI_Bullish_Resonance'] = True
    result['RSI_Bearish_Resonance'] = True
    
    for period in periods:
        rsi_col = f'RSI{period}'
        # 多头共振：所有周期RSI都大于50
        result['RSI_Bullish_Resonance'] &= (result[rsi_col] > 50)
        # 空头共振：所有周期RSI都小于50
        result['RSI_Bearish_Resonance'] &= (result[rsi_col] < 50)
    
    return result


def calculate_rsi_trend_strength(data: pd.DataFrame, price_column: str = 'close') -> pd.DataFrame:
    """
    计算RSI趋势强度
    
    Args:
        data (pd.DataFrame): 包含价格数据的DataFrame
        price_column (str): 价格列名，默认为'close'
    
    Returns:
        pd.DataFrame: 包含RSI趋势强度分析的DataFrame
    """
    result = calculate_rsi(data, price_column)
    
    # 计算RSI变化率
    result['RSI_Change'] = result['RSI'] - result['RSI'].shift(1)
    result['RSI_Momentum'] = result['RSI_Change'] - result['RSI_Change'].shift(1)
    
    # 计算RSI平滑线
    result['RSI_MA5'] = result['RSI'].rolling(window=5).mean()
    result['RSI_MA10'] = result['RSI'].rolling(window=10).mean()
    
    # 判断RSI趋势
    result['RSI_Trend'] = 'SIDEWAYS'
    
    # RSI上升趋势
    rsi_uptrend = (result['RSI'] > result['RSI_MA5']) & (result['RSI_MA5'] > result['RSI_MA10'])
    result.loc[rsi_uptrend, 'RSI_Trend'] = 'UPTREND'
    
    # RSI下降趋势
    rsi_downtrend = (result['RSI'] < result['RSI_MA5']) & (result['RSI_MA5'] < result['RSI_MA10'])
    result.loc[rsi_downtrend, 'RSI_Trend'] = 'DOWNTREND'
    
    # 判断趋势强度
    result['RSI_Strength'] = 'WEAK'
    
    # 强势上涨：RSI > 70 且持续上涨
    strong_bull = (result['RSI'] > 70) & (result['RSI_Change'] > 0) & (result['RSI_Momentum'] > 0)
    result.loc[strong_bull, 'RSI_Strength'] = 'STRONG_BULL'
    
    # 强势下跌：RSI < 30 且持续下跌
    strong_bear = (result['RSI'] < 30) & (result['RSI_Change'] < 0) & (result['RSI_Momentum'] < 0)
    result.loc[strong_bear, 'RSI_Strength'] = 'STRONG_BEAR'
    
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
        print("计算RSI指标...")
        
        # 计算RSI
        rsi_data = calculate_rsi(data)
        print(f"\nRSI计算结果（前5行）:")
        print(rsi_data[['date', 'close', 'RSI']].head())
        
        # 生成交易信号
        signal_data = get_rsi_signals(data)
        print(f"\nRSI交易信号（前10行）:")
        signals = signal_data[signal_data['RSI_Signal'] != 0]
        if not signals.empty:
            print(signals[['date', 'close', 'RSI', 'RSI_Signal', 'RSI_Position']].head(10))
        else:
            print("当前数据中未发现RSI交易信号")
        
        # 计算多周期RSI
        multi_rsi_data = calculate_multi_timeframe_rsi(data)
        print(f"\n多周期RSI（前5行）:")
        print(multi_rsi_data[['date', 'close', 'RSI6', 'RSI14', 'RSI21', 'RSI_Average']].head())
        
        # 分析RSI趋势强度
        trend_data = calculate_rsi_trend_strength(data)
        print(f"\nRSI趋势强度（前5行）:")
        print(trend_data[['date', 'close', 'RSI', 'RSI_Trend', 'RSI_Strength']].head())
    else:
        print("数据获取失败") 