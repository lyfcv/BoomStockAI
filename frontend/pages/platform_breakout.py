"""
平台突破策略前端页面
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from strategy_center.strategy_executor import run_platform_breakout_strategy, strategy_executor
from database.db_utils import db_manager, stock_dao
from database.models import StockAnalysis, TradingSignal


def main():
    """主页面"""
    st.set_page_config(
        page_title="平台突破选股策略",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 平台突破选股策略")
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 策略配置")
        
        # 策略参数配置
        st.subheader("策略参数")
        platform_window = st.slider("平台检测窗口期", 10, 30, 20)
        max_volatility = st.slider("最大波动率", 0.05, 0.25, 0.15, 0.01)
        volume_threshold = st.slider("成交量放大倍数", 1.5, 5.0, 2.0, 0.1)
        score_threshold = st.slider("最低评分阈值", 40, 90, 60)
        
        # 过滤条件
        st.subheader("过滤条件")
        min_price = st.number_input("最低股价", 1.0, 50.0, 5.0)
        max_price = st.number_input("最高股价", 50.0, 500.0, 200.0)
        exclude_st = st.checkbox("排除ST股票", True)
        
        # 股票池选择
        st.subheader("股票池")
        use_custom_pool = st.checkbox("使用自定义股票池")
        custom_stocks = []
        if use_custom_pool:
            stock_input = st.text_area("输入股票代码（每行一个）", placeholder="sh.600000\nsz.000001")
            if stock_input:
                custom_stocks = [code.strip() for code in stock_input.split('\n') if code.strip()]
        
        # 执行按钮
        if st.button("🚀 执行策略", type="primary"):
            execute_strategy(
                platform_window, max_volatility, volume_threshold, score_threshold,
                min_price, max_price, exclude_st, custom_stocks if use_custom_pool else None
            )
    
    # 主内容区域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 策略执行结果
        if 'strategy_result' in st.session_state:
            display_strategy_results()
        else:
            st.info("👈 请在左侧配置策略参数并点击执行")
    
    with col2:
        # 策略状态和历史
        display_strategy_status()
        display_execution_history()


def execute_strategy(platform_window, max_volatility, volume_threshold, score_threshold,
                    min_price, max_price, exclude_st, custom_stocks):
    """执行策略"""
    try:
        # 构建策略配置
        config = {
            'platform_window': platform_window,
            'max_volatility': max_volatility,
            'volume_threshold': volume_threshold,
            'score_threshold': score_threshold,
            'min_price': min_price,
            'max_price': max_price,
            'exclude_st': exclude_st,
            'lookback_days': 60,
            'min_volume': 10000000,
            'rsi_range': [30, 80]
        }
        
        with st.spinner("🔍 正在执行平台突破策略..."):
            # 更新策略配置
            strategy_executor.strategies['platform_breakout'].config.update(config)
            
            # 执行策略
            result = run_platform_breakout_strategy(stock_pool=custom_stocks)
            
            # 保存结果到session state
            st.session_state['strategy_result'] = result
            st.session_state['execution_time'] = datetime.now()
        
        if result.get('success', True):
            st.success("✅ 策略执行成功！")
        else:
            st.error(f"❌ 策略执行失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"❌ 策略执行异常: {str(e)}")


def display_strategy_results():
    """显示策略执行结果"""
    result = st.session_state.get('strategy_result', {})
    
    if not result.get('success', True):
        st.error(f"策略执行失败: {result.get('error', 'Unknown error')}")
        return
    
    strategy_result = result.get('result', {})
    
    # 执行统计
    st.subheader("📊 执行统计")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("执行时间", f"{strategy_result.get('execution_time', 0):.2f}秒")
    with col2:
        st.metric("分析股票", f"{strategy_result.get('total_analyzed', 0)}只")
    with col3:
        st.metric("符合条件", f"{strategy_result.get('qualified_stocks', 0)}只")
    with col4:
        st.metric("交易信号", f"{strategy_result.get('trading_signals', 0)}个")
    
    # Top推荐股票
    top_picks = strategy_result.get('top_picks', [])
    if top_picks:
        st.subheader("🎯 Top推荐股票")
        
        # 构建数据表
        data = []
        for i, pick in enumerate(top_picks, 1):
            stock_info = pick.get('stock_info', {})
            recommendation = pick.get('recommendation', {})
            platform_analysis = pick.get('platform_analysis', {})
            breakout_analysis = pick.get('breakout_analysis', {})
            
            data.append({
                '排名': i,
                '股票代码': stock_info.get('code', ''),
                '股票名称': stock_info.get('name', ''),
                '当前价': pick.get('latest_price', 0),
                '评分': recommendation.get('score', 0),
                '建议': recommendation.get('action', ''),
                '置信度': recommendation.get('confidence', 0),
                '平台高点': platform_analysis.get('platform_high', 0),
                '平台低点': platform_analysis.get('platform_low', 0),
                '突破强度': breakout_analysis.get('breakout_strength', 0),
                '成交量倍数': breakout_analysis.get('volume_ratio', 0)
            })
        
        df = pd.DataFrame(data)
        
        # 格式化显示
        st.dataframe(
            df.style.format({
                '当前价': '{:.2f}',
                '评分': '{:.0f}',
                '置信度': '{:.2f}',
                '平台高点': '{:.2f}',
                '平台低点': '{:.2f}',
                '突破强度': '{:.0f}',
                '成交量倍数': '{:.1f}'
            }).background_gradient(subset=['评分', '置信度'], cmap='RdYlGn'),
            use_container_width=True
        )
        
        # 评分分布图
        if len(df) > 1:
            st.subheader("📈 评分分布")
            fig = px.histogram(df, x='评分', nbins=10, title="股票评分分布")
            st.plotly_chart(fig, use_container_width=True)
    
    # 交易信号详情
    signals = strategy_result.get('all_signals', [])
    if signals:
        st.subheader("📈 交易信号详情")
        
        for i, signal in enumerate(signals[:5], 1):
            with st.expander(f"🔥 信号 {i}: {signal.get('stock_name', '')} ({signal.get('stock_code', '')})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**价格**: {signal.get('price', 0):.2f}")
                    st.write(f"**评分**: {signal.get('score', 0):.0f}")
                    st.write(f"**置信度**: {signal.get('confidence', 0):.2f}")
                    st.write(f"**突破强度**: {signal.get('breakout_strength', 0):.0f}")
                
                with col2:
                    st.write(f"**成交量放大**: {signal.get('volume_ratio', 0):.1f}倍")
                    st.write(f"**平台区间**: {signal.get('platform_low', 0):.2f} - {signal.get('platform_high', 0):.2f}")
                    st.write(f"**信号时间**: {signal.get('signal_date', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}")
                
                reasons = signal.get('reasons', [])
                if reasons:
                    st.write("**分析理由**:")
                    for reason in reasons:
                        st.write(f"• {reason}")


def display_strategy_status():
    """显示策略状态"""
    st.subheader("📊 策略状态")
    
    try:
        status = strategy_executor.get_strategy_status()
        
        st.write(f"**总策略数**: {status.get('total_strategies', 0)}")
        st.write(f"**启用策略**: {', '.join(status.get('enabled_strategies', []))}")
        
        last_execution = status.get('last_execution')
        if last_execution:
            st.write(f"**最后执行**: {last_execution['strategy_name']}")
            st.write(f"**执行时间**: {last_execution['time'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**执行状态**: {'✅ 成功' if last_execution['success'] else '❌ 失败'}")
        
    except Exception as e:
        st.error(f"获取策略状态失败: {str(e)}")


def display_execution_history():
    """显示执行历史"""
    st.subheader("📜 执行历史")
    
    try:
        history = strategy_executor.get_execution_history(limit=10)
        
        if history:
            history_data = []
            for record in history:
                history_data.append({
                    '策略': record['strategy_name'],
                    '时间': record['start_time'].strftime('%m-%d %H:%M'),
                    '耗时': f"{record['duration']:.1f}s",
                    '状态': '✅' if record['success'] else '❌'
                })
            
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无执行历史")
            
    except Exception as e:
        st.error(f"获取执行历史失败: {str(e)}")


def display_historical_signals():
    """显示历史信号"""
    st.subheader("📊 历史信号统计")
    
    try:
        with db_manager.get_session() as session:
            # 查询最近30天的信号
            start_date = datetime.now() - timedelta(days=30)
            
            signals = session.query(TradingSignal).filter(
                TradingSignal.strategy_name == 'platform_breakout',
                TradingSignal.signal_date >= start_date
            ).all()
            
            if signals:
                # 按日期统计
                daily_stats = {}
                for signal in signals:
                    date_key = signal.signal_date.strftime('%Y-%m-%d')
                    if date_key not in daily_stats:
                        daily_stats[date_key] = 0
                    daily_stats[date_key] += 1
                
                # 创建图表
                dates = list(daily_stats.keys())
                counts = list(daily_stats.values())
                
                fig = go.Figure(data=go.Scatter(x=dates, y=counts, mode='lines+markers'))
                fig.update_layout(
                    title="每日信号数量",
                    xaxis_title="日期",
                    yaxis_title="信号数量"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.write(f"**总信号数**: {len(signals)}")
                st.write(f"**平均置信度**: {sum(s.confidence for s in signals) / len(signals):.2f}")
            else:
                st.info("暂无历史信号数据")
                
    except Exception as e:
        st.error(f"获取历史信号失败: {str(e)}")


if __name__ == "__main__":
    main() 