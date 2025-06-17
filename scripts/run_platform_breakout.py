#!/usr/bin/env python3
"""
运行平台突破选股策略脚本
"""
import sys
import os
import argparse
from datetime import datetime
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_center.strategy_executor import run_platform_breakout_strategy, strategy_executor
from database.db_utils import db_manager


def setup_logging():
    """设置日志"""
    log_file = f"logs/platform_breakout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )


def print_results(result: dict):
    """打印策略执行结果"""
    print("\n" + "="*80)
    print("🚀 平台突破选股策略执行结果")
    print("="*80)
    
    if not result.get('success', True):
        print(f"❌ 策略执行失败: {result.get('error', 'Unknown error')}")
        return
    
    strategy_result = result.get('result', {})
    
    print(f"📊 执行统计:")
    print(f"   • 策略名称: {strategy_result.get('strategy_name', 'platform_breakout')}")
    print(f"   • 执行时间: {strategy_result.get('execution_time', 0):.2f} 秒")
    print(f"   • 分析股票: {strategy_result.get('total_analyzed', 0)} 只")
    print(f"   • 符合条件: {strategy_result.get('qualified_stocks', 0)} 只")
    print(f"   • 交易信号: {strategy_result.get('trading_signals', 0)} 个")
    print(f"   • 保存分析: {strategy_result.get('saved_analysis', 0)} 条")
    print(f"   • 保存信号: {strategy_result.get('saved_signals', 0)} 条")
    
    # 显示Top推荐股票
    top_picks = strategy_result.get('top_picks', [])
    if top_picks:
        print(f"\n🎯 Top {len(top_picks)} 推荐股票:")
        print("-" * 80)
        print(f"{'排名':<4} {'股票代码':<12} {'股票名称':<12} {'当前价':<8} {'评分':<6} {'建议':<8} {'置信度':<8}")
        print("-" * 80)
        
        for i, pick in enumerate(top_picks[:10], 1):
            stock_info = pick.get('stock_info', {})
            recommendation = pick.get('recommendation', {})
            
            print(f"{i:<4} {stock_info.get('code', ''):<12} {stock_info.get('name', ''):<12} "
                  f"{pick.get('latest_price', 0):<8.2f} {recommendation.get('score', 0):<6.0f} "
                  f"{recommendation.get('action', ''):<8} {recommendation.get('confidence', 0):<8.2f}")
    
    # 显示交易信号
    signals = strategy_result.get('all_signals', [])
    if signals:
        print(f"\n📈 交易信号详情:")
        print("-" * 80)
        
        for signal in signals[:5]:  # 只显示前5个信号
            print(f"🔥 {signal.get('stock_name', '')} ({signal.get('stock_code', '')})")
            print(f"   价格: {signal.get('price', 0):.2f} | 评分: {signal.get('score', 0):.0f} | 置信度: {signal.get('confidence', 0):.2f}")
            print(f"   突破强度: {signal.get('breakout_strength', 0):.0f} | 成交量放大: {signal.get('volume_ratio', 0):.1f}倍")
            print(f"   平台区间: {signal.get('platform_low', 0):.2f} - {signal.get('platform_high', 0):.2f}")
            
            reasons = signal.get('reasons', [])
            if reasons:
                print(f"   理由: {'; '.join(reasons[:3])}")  # 只显示前3个理由
            print()
        
        if len(signals) > 5:
            print(f"   ... 还有 {len(signals) - 5} 个信号，详情请查看数据库")
    
    print("="*80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行平台突破选股策略')
    parser.add_argument('--stocks', nargs='+', help='指定股票池（股票代码列表）')
    parser.add_argument('--no-save', action='store_true', help='不保存结果到数据库')
    parser.add_argument('--config', help='策略配置文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    if args.verbose:
        logger.info("启用详细输出模式")
    
    try:
        # 测试数据库连接
        if not db_manager.test_connection():
            print("❌ 数据库连接失败，请检查配置")
            return 1
        
        print("🔍 开始执行平台突破选股策略...")
        print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.stocks:
            print(f"📋 指定股票池: {len(args.stocks)} 只股票")
        else:
            print("📋 使用全市场股票池")
        
        # 更新策略配置（如果指定）
        if args.config:
            # 这里可以加载自定义配置
            logger.info(f"使用配置文件: {args.config}")
        
        # 执行策略
        result = run_platform_breakout_strategy(stock_pool=args.stocks)
        
        # 打印结果
        print_results(result)
        
        # 如果有错误，返回错误码
        if not result.get('success', True):
            return 1
        
        print("✅ 策略执行完成！")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断执行")
        return 130
    except Exception as e:
        logger.error(f"策略执行异常: {e}")
        print(f"❌ 策略执行失败: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 