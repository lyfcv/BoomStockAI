# 技术指标计算模块使用文档

## 📖 概述

本模块提供了完整的技术指标计算功能，支持常用的技术分析指标，包括MA、BOLL、MACD、KDJ、RSI等。所有指标都基于K线数据计算，并提供交易信号生成功能。

## 🚀 快速开始

### 基本使用

```python
from data_collection.market_data.history_k_data import get_k_data
from data_collection.technical_indicators.indicator_calculator import TechnicalIndicatorCalculator

# 获取K线数据
data = get_k_data('sh.600000', 100, 'd')

# 创建技术指标计算器
calculator = TechnicalIndicatorCalculator(data)

# 计算所有技术指标
indicators = calculator.calculate_all_indicators()

# 获取交易信号
signals = calculator.get_trading_signals()
```

## 📊 支持的技术指标

### 1. 移动平均线 (MA/EMA)

#### 功能特点
- 简单移动平均线 (SMA)
- 指数移动平均线 (EMA)
- 多周期支持
- 金叉死叉信号检测

#### 使用示例

```python
from data_collection.technical_indicators.ma_indicators import calculate_ma, calculate_ema, get_ma_signals

# 计算多周期MA
ma_data = calculate_ma(data, periods=[5, 10, 20, 30])

# 计算EMA
ema_data = calculate_ema(data, periods=[12, 26])

# 获取MA交易信号
ma_signals = get_ma_signals(data, short_period=5, long_period=20)
```

#### 输出字段
- `MA{period}`: 对应周期的移动平均值
- `EMA{period}`: 对应周期的指数移动平均值
- `MA_Signal`: 交易信号 (1: 买入, -1: 卖出, 0: 无信号)
- `MA_Cross`: 交叉信号 (1: 金叉, -1: 死叉, 0: 无交叉)

### 2. 布林带 (BOLL)

#### 功能特点
- 中轨、上轨、下轨计算
- 布林带宽度和%B指标
- 超买超卖信号
- 布林带收缩检测

#### 使用示例

```python
from data_collection.technical_indicators.boll_indicators import calculate_boll, get_boll_signals

# 计算布林带
boll_data = calculate_boll(data, period=20, std_multiplier=2.0)

# 获取布林带交易信号
boll_signals = get_boll_signals(data)
```

#### 输出字段
- `BOLL_UPPER`: 布林带上轨
- `BOLL_MID`: 布林带中轨
- `BOLL_LOWER`: 布林带下轨
- `BOLL_WIDTH`: 布林带宽度
- `BOLL_PB`: %B指标
- `BOLL_Signal`: 交易信号
- `BOLL_Position`: 价格位置 ('UPPER', 'MIDDLE', 'LOWER')

### 3. MACD指标

#### 功能特点
- MACD线、Signal线、Histogram
- 金叉死叉信号
- 零轴交叉信号
- 背离分析

#### 使用示例

```python
from data_collection.technical_indicators.macd_indicators import calculate_macd, get_macd_signals

# 计算MACD
macd_data = calculate_macd(data, fast_period=12, slow_period=26, signal_period=9)

# 获取MACD交易信号
macd_signals = get_macd_signals(data)
```

#### 输出字段
- `MACD`: MACD线
- `MACD_Signal`: Signal线
- `MACD_Histogram`: MACD柱状图
- `MACD_Cross`: 交叉信号 (1: 金叉, -1: 死叉)
- `MACD_Zero_Cross`: 零轴交叉 (1: 向上, -1: 向下)
- `MACD_Position`: 位置状态 ('BULLISH', 'BEARISH', 'NEUTRAL')

### 4. KDJ指标

#### 功能特点
- K、D、J三线计算
- 超买超卖区域判断
- 金叉死叉信号
- 极值信号检测

#### 使用示例

```python
from data_collection.technical_indicators.kdj_indicators import calculate_kdj, get_kdj_signals

# 计算KDJ
kdj_data = calculate_kdj(data, k_period=9, d_period=3, j_period=3)

# 获取KDJ交易信号
kdj_signals = get_kdj_signals(data, overbought=80, oversold=20)
```

#### 输出字段
- `K`: K值
- `D`: D值
- `J`: J值
- `KDJ_Cross`: K线与D线交叉 (1: 金叉, -1: 死叉)
- `KDJ_Position`: 位置状态 ('OVERBOUGHT', 'OVERSOLD', 'NEUTRAL')
- `KDJ_J_Extreme`: J值极值信号

### 5. RSI指标

#### 功能特点
- 相对强弱指标计算
- 超买超卖信号
- 中线交叉信号
- 多周期RSI

#### 使用示例

```python
from data_collection.technical_indicators.rsi_indicators import calculate_rsi, get_rsi_signals

# 计算RSI
rsi_data = calculate_rsi(data, period=14)

# 获取RSI交易信号
rsi_signals = get_rsi_signals(data, overbought=70, oversold=30)
```

#### 输出字段
- `RSI`: RSI值
- `RSI_Signal`: 交易信号
- `RSI_Position`: 位置状态 ('OVERBOUGHT', 'OVERSOLD', 'NEUTRAL')
- `RSI_Midline_Cross`: 中线交叉信号

## 🔧 综合技术指标计算器

### TechnicalIndicatorCalculator类

这是一个综合的技术指标计算器，提供一站式的指标计算和信号分析功能。

#### 主要方法

```python
# 初始化
calculator = TechnicalIndicatorCalculator(data)

# 计算所有指标
indicators = calculator.calculate_all_indicators()

# 获取交易信号
signals = calculator.get_trading_signals()

# 获取综合信号（多指标确认）
comprehensive = calculator.get_comprehensive_signals(min_signals=2)

# 分析趋势强度
trend_analysis = calculator.analyze_trend_strength()

# 获取指标摘要
summary = calculator.get_indicator_summary()
```

### 综合信号功能

综合信号通过统计多个指标的买入/卖出信号数量，当达到设定阈值时生成确认信号：

```python
# 获取需要至少2个指标确认的综合信号
comprehensive = calculator.get_comprehensive_signals(min_signals=2)

# 查看综合信号
comp_signals = comprehensive[comprehensive['Comprehensive_Signal'] != 0]
print(comp_signals[['date', 'Buy_Signal_Count', 'Sell_Signal_Count', 'Comprehensive_Signal']])
```

### 趋势强度分析

趋势强度分析综合多个指标的状态，给出整体趋势评分：

```python
trend_analysis = calculator.analyze_trend_strength()

# 趋势强度等级
# STRONG_BULL: 强烈看涨
# BULL: 看涨  
# WEAK_BULL: 弱看涨
# NEUTRAL: 中性
# WEAK_BEAR: 弱看跌
# BEAR: 看跌
# STRONG_BEAR: 强烈看跌
```

## 💡 实际应用示例

### 1. 单一指标分析

```python
from data_collection.market_data.history_k_data import get_k_data
from data_collection.technical_indicators.ma_indicators import get_ma_signals

# 获取数据
data = get_k_data('sh.600000', 50, 'd')

# 分析MA信号
ma_signals = get_ma_signals(data)
recent_signals = ma_signals[ma_signals['MA_Cross'] != 0].tail(5)
print("最近的MA交叉信号:")
print(recent_signals[['date', 'close', 'MA5', 'MA20', 'MA_Cross']])
```

### 2. 多指标综合分析

```python
# 创建综合分析
calculator = TechnicalIndicatorCalculator(data)
indicators = calculator.calculate_all_indicators()

# 获取最新指标状态
summary = calculator.get_indicator_summary()
print(f"当前价格: {summary['close']}")
print(f"MA5: {summary['indicators']['MA5']:.2f}")
print(f"RSI: {summary['indicators']['RSI']:.2f}")
print(f"MACD: {summary['indicators']['MACD']:.4f}")

# 分析趋势
trend = calculator.analyze_trend_strength()
latest_trend = trend.iloc[-1]
print(f"趋势强度: {latest_trend['Trend_Strength']}")
print(f"趋势评分: {latest_trend['Trend_Score']}")
```

### 3. 交易信号筛选

```python
# 获取综合交易信号
signals = calculator.get_trading_signals()

# 筛选强信号（多个指标同时发出信号）
strong_buy = signals[
    (signals['MA_Cross'] == 1) & 
    (signals['MACD_Cross'] == 1) & 
    (signals['RSI_Position'] == 'OVERSOLD')
]

strong_sell = signals[
    (signals['MA_Cross'] == -1) & 
    (signals['MACD_Cross'] == -1) & 
    (signals['RSI_Position'] == 'OVERBOUGHT')
]

print("强买入信号:")
print(strong_buy[['date', 'close', 'MA_Cross', 'MACD_Cross', 'RSI_Position']])
```

### 4. 批量股票分析

```python
def analyze_stock(stock_code):
    """分析单只股票的技术指标"""
    data = get_k_data(stock_code, 100, 'd')
    if data is None:
        return None
    
    calculator = TechnicalIndicatorCalculator(data)
    calculator.calculate_all_indicators()
    
    # 获取综合信号
    comprehensive = calculator.get_comprehensive_signals(min_signals=2)
    latest_signal = comprehensive.iloc[-1]
    
    # 获取趋势分析
    trend = calculator.analyze_trend_strength()
    latest_trend = trend.iloc[-1]
    
    return {
        'stock_code': stock_code,
        'date': latest_signal['date'],
        'close': float(latest_signal['close']),
        'comprehensive_signal': latest_signal['Comprehensive_Signal'],
        'buy_signals': latest_signal['Buy_Signal_Count'],
        'sell_signals': latest_signal['Sell_Signal_Count'],
        'trend_strength': latest_trend['Trend_Strength'],
        'trend_score': latest_trend['Trend_Score']
    }

# 分析多只股票
stocks = ['sh.600000', 'sh.600036', 'sz.000001', 'sz.000002']
results = []

for stock in stocks:
    result = analyze_stock(stock)
    if result:
        results.append(result)

# 显示结果
import pandas as pd
df_results = pd.DataFrame(results)
print(df_results)
```

## ⚠️ 注意事项

### 1. 数据要求
- 需要包含 `date`, `open`, `high`, `low`, `close`, `volume` 字段
- 数据应按时间顺序排列
- 建议至少50条数据以获得准确的指标计算

### 2. 参数调整
- 不同市场和时间周期可能需要调整指标参数
- 建议根据历史回测结果优化参数
- 超买超卖阈值可根据股票特性调整

### 3. 信号使用
- 技术指标有滞后性，应结合基本面分析
- 单一指标信号可能产生假信号，建议多指标确认
- 综合信号的阈值可根据风险偏好调整

### 4. 性能考虑
- 大量数据计算可能较慢，可考虑并行处理
- 实时应用中建议缓存计算结果
- 可根据需要只计算必要的指标

## 📈 扩展功能

### 自定义指标
可以继承现有模块添加自定义指标：

```python
def calculate_custom_indicator(data, period=10):
    """自定义指标示例"""
    result = data.copy()
    # 自定义计算逻辑
    result['Custom'] = result['close'].rolling(window=period).mean()
    return result
```

### 指标组合策略
可以组合多个指标创建交易策略：

```python
def custom_strategy(data):
    """自定义策略示例"""
    calculator = TechnicalIndicatorCalculator(data)
    indicators = calculator.calculate_all_indicators()
    
    # 自定义策略逻辑
    buy_condition = (
        (indicators['MA5'] > indicators['MA20']) &
        (indicators['RSI'] < 70) &
        (indicators['MACD'] > indicators['MACD_Signal'])
    )
    
    indicators['Custom_Signal'] = 0
    indicators.loc[buy_condition, 'Custom_Signal'] = 1
    
    return indicators
```

## 📞 技术支持

如有问题或建议，请参考：
- 查看各指标模块的详细文档
- 运行模块中的示例代码
- 联系开发团队获取支持 