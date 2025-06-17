#!/usr/bin/env python3
"""
平台突破策略测试脚本
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_center.models.technical_indicators import TechnicalIndicators, PlatformBreakoutAnalyzer
from strategy_center.strategies.platform_breakout_strategy import create_platform_breakout_strategy


def create_test_data():
    """创建测试数据"""
    # 生成60天的测试数据
    dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
    
    # 模拟股价数据（包含平台整理和突破）
    base_price = 10.0
    prices = []
    volumes = []
    
    for i, date in enumerate(dates):
        if i < 20:
            # 前20天：正常波动
            price = base_price + np.random.normal(0, 0.2)
        elif i < 45:
            # 中间25天：平台整理（小幅波动）
            price = base_price + np.random.normal(0, 0.1)
        else:
            # 后15天：突破上涨
            price = base_price + (i - 44) * 0.1 + np.random.normal(0, 0.15)
        
        prices.append(max(price, 1.0))  # 确保价格为正
        
        # 模拟成交量（突破时放大）
        if i >= 45:
            volume = np.random.randint(20000000, 50000000)  # 突破时放量
        else:
            volume = np.random.randint(5000000, 15000000)   # 平时成交量
        
        volumes.append(volume)
    
    # 创建OHLC数据
    data = []
    for i, (date, close, volume) in enumerate(zip(dates, prices, volumes)):
        # 简单模拟开高低价
        open_price = close + np.random.normal(0, 0.05)
        high_price = max(open_price, close) + abs(np.random.normal(0, 0.1))
        low_price = min(open_price, close) - abs(np.random.normal(0, 0.1))
        
        data.append({
            'trade_date': date,
            'open_price': max(open_price, 0.1),
            'high_price': max(high_price, 0.1),
            'low_price': max(low_price, 0.1),
            'close_price': max(close, 0.1),
            'volume': volume,
            'amount': volume * close
        })
    
    return pd.DataFrame(data)


def test_technical_indicators():
    """测试技术指标计算"""
    print("🧪 测试技术指标计算...")
    
    # 创建测试数据
    df = create_test_data()
    indicators = TechnicalIndicators()
    
    # 测试移动平均线
    df = indicators.calculate_moving_averages(df)
    assert 'ma_5' in df.columns, "移动平均线计算失败"
    assert 'ma_10' in df.columns, "移动平均线计算失败"
    assert 'ma_20' in df.columns, "移动平均线计算失败"
    print("✅ 移动平均线计算正常")
    
    # 测试布林带
    df = indicators.calculate_bollinger_bands(df)
    assert 'bb_upper' in df.columns, "布林带计算失败"
    assert 'bb_lower' in df.columns, "布林带计算失败"
    print("✅ 布林带计算正常")
    
    # 测试RSI
    df = indicators.calculate_rsi(df)
    assert 'rsi' in df.columns, "RSI计算失败"
    print("✅ RSI计算正常")
    
    # 测试KDJ
    df = indicators.calculate_kdj(df)
    assert 'k' in df.columns, "KDJ计算失败"
    assert 'd' in df.columns, "KDJ计算失败"
    print("✅ KDJ计算正常")
    
    # 测试成交量指标
    df = indicators.calculate_volume_indicators(df)
    assert 'volume_ratio' in df.columns, "成交量指标计算失败"
    print("✅ 成交量指标计算正常")
    
    # 测试平台检测
    df = indicators.detect_platform_consolidation(df)
    assert 'is_platform' in df.columns, "平台检测失败"
    assert 'platform_high' in df.columns, "平台检测失败"
    print("✅ 平台检测正常")
    
    # 测试突破信号
    df = indicators.detect_breakout_signals(df)
    assert 'breakout_signal' in df.columns, "突破信号检测失败"
    print("✅ 突破信号检测正常")
    
    return df


def test_platform_breakout_analyzer():
    """测试平台突破分析器"""
    print("\n🧪 测试平台突破分析器...")
    
    # 创建测试数据
    df = create_test_data()
    analyzer = PlatformBreakoutAnalyzer()
    
    # 执行分析
    result = analyzer.analyze(df)
    
    # 验证结果
    assert result['success'], f"分析失败: {result.get('message', 'Unknown error')}"
    assert 'platform_analysis' in result, "缺少平台分析结果"
    assert 'breakout_analysis' in result, "缺少突破分析结果"
    assert 'trend_analysis' in result, "缺少趋势分析结果"
    assert 'recommendation' in result, "缺少投资建议"
    
    print("✅ 平台突破分析器正常")
    
    # 打印分析结果
    platform_analysis = result['platform_analysis']
    breakout_analysis = result['breakout_analysis']
    recommendation = result['recommendation']
    
    print(f"📊 分析结果:")
    print(f"   平台整理: {'是' if platform_analysis['is_platform'] else '否'}")
    print(f"   平台区间: {platform_analysis['platform_low']:.2f} - {platform_analysis['platform_high']:.2f}")
    print(f"   波动率: {platform_analysis['volatility']:.3f}")
    print(f"   突破信号: {'是' if breakout_analysis['has_breakout'] else '否'}")
    print(f"   突破强度: {breakout_analysis['breakout_strength']:.0f}")
    print(f"   成交量倍数: {breakout_analysis['volume_ratio']:.1f}")
    print(f"   投资建议: {recommendation['action']}")
    print(f"   评分: {recommendation['score']:.0f}")
    print(f"   置信度: {recommendation['confidence']:.2f}")
    
    return result


def test_strategy_creation():
    """测试策略创建"""
    print("\n🧪 测试策略创建...")
    
    # 创建默认策略
    strategy = create_platform_breakout_strategy()
    assert strategy is not None, "策略创建失败"
    assert strategy.strategy_name == "platform_breakout", "策略名称错误"
    print("✅ 默认策略创建正常")
    
    # 创建自定义配置策略
    custom_config = {
        'platform_window': 15,
        'max_volatility': 0.12,
        'volume_threshold': 2.5,
        'score_threshold': 70
    }
    
    custom_strategy = create_platform_breakout_strategy(custom_config)
    assert custom_strategy.config['platform_window'] == 15, "自定义配置未生效"
    assert custom_strategy.config['max_volatility'] == 0.12, "自定义配置未生效"
    print("✅ 自定义策略创建正常")
    
    return strategy


def test_data_validation():
    """测试数据验证"""
    print("\n🧪 测试数据验证...")
    
    analyzer = PlatformBreakoutAnalyzer()
    
    # 测试数据不足的情况
    small_df = create_test_data().head(10)
    result = analyzer.analyze(small_df)
    assert not result['success'], "应该检测到数据不足"
    print("✅ 数据不足检测正常")
    
    # 测试空数据
    empty_df = pd.DataFrame()
    result = analyzer.analyze(empty_df)
    assert not result['success'], "应该检测到空数据"
    print("✅ 空数据检测正常")
    
    # 测试缺少必要列的数据
    incomplete_df = pd.DataFrame({
        'trade_date': pd.date_range('2024-01-01', periods=30),
        'close_price': np.random.randn(30)
        # 缺少其他必要列
    })
    
    try:
        result = analyzer.analyze(incomplete_df)
        # 应该能处理缺少列的情况，但可能结果不完整
        print("✅ 不完整数据处理正常")
    except Exception as e:
        print(f"⚠️  不完整数据处理异常: {e}")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行平台突破策略测试...")
    print("=" * 60)
    
    try:
        # 测试技术指标
        test_df = test_technical_indicators()
        
        # 测试分析器
        analysis_result = test_platform_breakout_analyzer()
        
        # 测试策略创建
        strategy = test_strategy_creation()
        
        # 测试数据验证
        test_data_validation()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("✅ 平台突破策略功能正常")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 