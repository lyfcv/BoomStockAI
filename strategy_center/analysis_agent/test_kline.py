from kline_get import get_stock_kline_30days, analyze_stock_kline, format_kline_for_analysis

# 方法1: 直接获取DataFrame
print("=" * 80)
print("方法1: 直接获取DataFrame数据")
print("=" * 80)
df = get_stock_kline_30days('000001')
print(f"获取到 {len(df)} 条数据")
print(df.head())

# 方法2: 获取适合API的完整分析结果
print("\n" + "=" * 80)
print("方法2: API接口格式 - 完整分析结果")
print("=" * 80)
result = analyze_stock_kline('000001')
print(f"成功: {result['success']}")
print(f"股票代码: {result['stock_code']}")
print(f"交易日数: {result['summary']['trading_days']}")
print(f"最新价格: {result['summary']['latest_price']}")
print(f"期间涨跌: {result['summary']['total_change_pct']:.2f}%")

# 方法3a: 使用已有DataFrame获取分析文本
print("\n" + "=" * 80)
print("方法3a: 大模型分析格式 - 使用已有DataFrame")
print("=" * 80)
analysis_text = format_kline_for_analysis(df, '000001')
print(analysis_text[:200] + "...")  # 只显示前200个字符

# 方法3b: 直接使用股票代码获取分析文本（独立使用）
print("\n" + "=" * 80)
print("方法3b: 大模型分析格式 - 直接使用股票代码（独立）")
print("=" * 80)
analysis_text_direct = format_kline_for_analysis('600000')  # 浦发银行
print(analysis_text_direct)