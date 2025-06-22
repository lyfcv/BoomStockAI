from data_collection.market_data.history_k_data import get_k_data
from data_collection.technical_indicators.indicator_calculator import TechnicalIndicatorCalculator

# 获取数据
data = get_k_data('sh.600000', 100, 'd')

# 创建计算器
calculator = TechnicalIndicatorCalculator(data)

# 计算所有指标
indicators = calculator.calculate_all_indicators()

# 获取交易信号
signals = calculator.get_trading_signals()

# 获取综合信号
comprehensive = calculator.get_comprehensive_signals(min_signals=2)

# 分析趋势强度
trend = calculator.analyze_trend_strength()