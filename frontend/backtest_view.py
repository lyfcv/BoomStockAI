"""
回测结果展示页面
显示策略回测的详细结果和分析
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def show_backtest_config():
    """显示回测配置"""
    st.subheader("⚙️ 回测配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 时间范围设置
        st.write("**时间范围**")
        start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now()
        )
        
        end_date = st.date_input(
            "结束日期",
            value=datetime.now(),
            max_value=datetime.now()
        )
        
        # 初始资金
        initial_capital = st.number_input(
            "初始资金 (万元)",
            min_value=1.0,
            max_value=1000.0,
            value=10.0,
            step=1.0
        )
    
    with col2:
        # 策略选择
        st.write("**策略选择**")
        strategy = st.selectbox(
            "选择策略",
            ["AI智能选股", "技术分析策略", "基本面策略", "情感分析策略", "组合策略"]
        )
        
        # 风险设置
        max_position = st.slider(
            "单只股票最大仓位 (%)",
            min_value=5,
            max_value=50,
            value=20
        )
        
        stop_loss = st.slider(
            "止损线 (%)",
            min_value=5,
            max_value=30,
            value=10
        )
    
    if st.button("🚀 开始回测", use_container_width=True):
        return {
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital * 10000,  # 转换为元
            'strategy': strategy,
            'max_position': max_position / 100,
            'stop_loss': stop_loss / 100
        }
    
    return None


def generate_mock_backtest_data(config):
    """生成模拟回测数据"""
    start_date = pd.to_datetime(config['start_date'])
    end_date = pd.to_datetime(config['end_date'])
    
    # 生成日期序列
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = dates[dates.weekday < 5]  # 只保留工作日
    
    # 生成模拟收益率数据
    np.random.seed(42)  # 确保可重复
    
    # 基础收益率（年化8%）
    daily_return_base = 0.08 / 252
    
    # 根据策略调整收益率
    strategy_multiplier = {
        "AI智能选股": 1.5,
        "技术分析策略": 1.2,
        "基本面策略": 1.1,
        "情感分析策略": 1.3,
        "组合策略": 1.4
    }
    
    multiplier = strategy_multiplier.get(config['strategy'], 1.0)
    
    # 生成随机收益率
    returns = np.random.normal(
        daily_return_base * multiplier, 
        0.02,  # 波动率
        len(dates)
    )
    
    # 计算累计收益
    portfolio_values = [config['initial_capital']]
    for return_rate in returns:
        new_value = portfolio_values[-1] * (1 + return_rate)
        portfolio_values.append(new_value)
    
    # 生成同期沪深300指数数据作为基准
    benchmark_returns = np.random.normal(0.06/252, 0.015, len(dates))
    benchmark_values = [config['initial_capital']]
    for return_rate in benchmark_returns:
        new_value = benchmark_values[-1] * (1 + return_rate)
        benchmark_values.append(new_value)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'date': [start_date] + list(dates),
        'portfolio_value': portfolio_values,
        'benchmark_value': benchmark_values
    })
    
    # 计算收益率
    df['portfolio_return'] = df['portfolio_value'].pct_change()
    df['benchmark_return'] = df['benchmark_value'].pct_change()
    
    return df


def show_performance_overview(backtest_data, config):
    """显示业绩概览"""
    st.subheader("📊 业绩概览")
    
    # 计算关键指标
    final_value = backtest_data['portfolio_value'].iloc[-1]
    initial_value = config['initial_capital']
    total_return = (final_value / initial_value - 1) * 100
    
    benchmark_final = backtest_data['benchmark_value'].iloc[-1]
    benchmark_return = (benchmark_final / initial_value - 1) * 100
    
    excess_return = total_return - benchmark_return
    
    # 计算年化收益率
    days = len(backtest_data)
    annualized_return = ((final_value / initial_value) ** (252 / days) - 1) * 100
    
    # 计算夏普比率
    returns = backtest_data['portfolio_return'].dropna()
    if len(returns) > 0:
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
    else:
        sharpe_ratio = 0
    
    # 计算最大回撤
    rolling_max = backtest_data['portfolio_value'].expanding().max()
    drawdown = (backtest_data['portfolio_value'] / rolling_max - 1) * 100
    max_drawdown = drawdown.min()
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总收益率",
            f"{total_return:.2f}%",
            f"vs 基准: {excess_return:+.2f}%"
        )
    
    with col2:
        st.metric("年化收益率", f"{annualized_return:.2f}%")
    
    with col3:
        st.metric("夏普比率", f"{sharpe_ratio:.2f}")
    
    with col4:
        st.metric("最大回撤", f"{max_drawdown:.2f}%")
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown
    }


def show_equity_curve(backtest_data):
    """显示资产曲线"""
    st.subheader("📈 资产曲线")
    
    fig = go.Figure()
    
    # 策略收益曲线
    fig.add_trace(go.Scatter(
        x=backtest_data['date'],
        y=backtest_data['portfolio_value'],
        mode='lines',
        name='策略收益',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # 基准收益曲线
    fig.add_trace(go.Scatter(
        x=backtest_data['date'],
        y=backtest_data['benchmark_value'],
        mode='lines',
        name='沪深300基准',
        line=dict(color='#ff7f0e', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="策略 vs 基准收益对比",
        xaxis_title="日期",
        yaxis_title="资产价值 (元)",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_returns_analysis(backtest_data):
    """显示收益分析"""
    st.subheader("📊 收益分析")
    
    # 计算月度收益
    monthly_data = backtest_data.set_index('date').resample('M').last()
    monthly_returns = monthly_data['portfolio_value'].pct_change().dropna() * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 月度收益分布
        fig = px.histogram(
            x=monthly_returns,
            nbins=20,
            title="月度收益分布",
            labels={'x': '月度收益率 (%)', 'y': '频次'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 收益统计信息
        st.write("**收益统计**")
        stats_df = pd.DataFrame({
            '指标': ['平均收益', '收益标准差', '偏度', '峰度', '胜率'],
            '数值': [
                f"{monthly_returns.mean():.2f}%",
                f"{monthly_returns.std():.2f}%",
                f"{monthly_returns.skew():.2f}",
                f"{monthly_returns.kurtosis():.2f}",
                f"{(monthly_returns > 0).mean() * 100:.1f}%"
            ]
        })
        st.dataframe(stats_df, hide_index=True)


def show_drawdown_analysis(backtest_data):
    """显示回撤分析"""
    st.subheader("📉 回撤分析")
    
    # 计算回撤
    rolling_max = backtest_data['portfolio_value'].expanding().max()
    drawdown = (backtest_data['portfolio_value'] / rolling_max - 1) * 100
    
    fig = go.Figure()
    
    # 回撤曲线
    fig.add_trace(go.Scatter(
        x=backtest_data['date'],
        y=drawdown,
        mode='lines',
        name='回撤',
        fill='tonexty',
        line=dict(color='red')
    ))
    
    fig.update_layout(
        title="历史回撤曲线",
        xaxis_title="日期",
        yaxis_title="回撤 (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 回撤统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("最大回撤", f"{drawdown.min():.2f}%")
    
    with col2:
        # 计算回撤持续天数
        in_drawdown = drawdown < -1  # 回撤超过1%
        if in_drawdown.any():
            max_duration = max(len(list(g)) for k, g in 
                              groupby(in_drawdown) if k)
        else:
            max_duration = 0
        st.metric("最长回撤期", f"{max_duration}天")
    
    with col3:
        # 回撤频次
        drawdown_periods = sum(1 for k, g in groupby(drawdown < -1) if k)
        st.metric("回撤次数", f"{drawdown_periods}次")


def show_risk_metrics(backtest_data, performance_metrics):
    """显示风险指标"""
    st.subheader("⚠️ 风险指标")
    
    returns = backtest_data['portfolio_return'].dropna()
    
    # 计算VaR和CVaR
    var_95 = np.percentile(returns, 5) * 100
    cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100
    
    # 计算beta值（相对于基准）
    benchmark_returns = backtest_data['benchmark_return'].dropna()
    if len(returns) > 1 and len(benchmark_returns) > 1:
        covariance = np.cov(returns[1:], benchmark_returns[1:])[0][1]
        benchmark_variance = np.var(benchmark_returns[1:])
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 1
    else:
        beta = 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("VaR (95%)", f"{var_95:.2f}%")
    
    with col2:
        st.metric("CVaR (95%)", f"{cvar_95:.2f}%")
    
    with col3:
        st.metric("Beta系数", f"{beta:.2f}")
    
    with col4:
        volatility = returns.std() * np.sqrt(252) * 100
        st.metric("年化波动率", f"{volatility:.2f}%")


def show_mock_positions():
    """显示模拟持仓"""
    st.subheader("💼 模拟持仓明细")
    
    # 生成模拟持仓数据
    positions_data = {
        '股票代码': ['000001', '000002', '600036', '002415', '000858'],
        '股票名称': ['平安银行', '万科A', '招商银行', '海康威视', '五粮液'],
        '持仓数量': [1000, 800, 1200, 600, 400],
        '成本价': [12.34, 25.67, 45.23, 38.92, 189.45],
        '现价': [13.45, 24.89, 46.78, 41.25, 195.32],
        '市值': [13450, 19912, 56136, 24750, 78128],
        '盈亏': [1110, -624, 1860, 1398, 2348],
        '盈亏比例': [9.0, -3.0, 3.4, 6.0, 3.6]
    }
    
    df = pd.DataFrame(positions_data)
    
    # 添加颜色标记
    def highlight_pnl(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
        return ''
    
    styled_df = df.style.applymap(highlight_pnl, subset=['盈亏', '盈亏比例'])
    st.dataframe(styled_df, use_container_width=True)
    
    # 持仓分布饼图
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(
            values=df['市值'],
            names=df['股票名称'],
            title="持仓分布"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 盈亏统计
        total_cost = sum(df['持仓数量'] * df['成本价'])
        total_market_value = sum(df['市值'])
        total_pnl = total_market_value - total_cost
        
        st.metric("总市值", f"¥{total_market_value:,.0f}")
        st.metric("总盈亏", f"¥{total_pnl:,.0f}", f"{total_pnl/total_cost*100:+.2f}%")


def show_backtest_results():
    """显示回测结果页面"""
    st.header("📊 回测结果")
    
    # 显示配置区域
    config = show_backtest_config()
    
    if config:
        st.success(f"回测配置: {config['strategy']} | "
                  f"{config['start_date']} 至 {config['end_date']} | "
                  f"初始资金: ¥{config['initial_capital']:,.0f}")
        
        # 生成回测数据
        with st.spinner("正在运行回测..."):
            backtest_data = generate_mock_backtest_data(config)
        
        st.success("回测完成!")
        
        # 显示结果
        performance_metrics = show_performance_overview(backtest_data, config)
        
        st.markdown("---")
        
        # 创建标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 资产曲线", "📊 收益分析", "📉 回撤分析", "⚠️ 风险指标", "💼 持仓明细"
        ])
        
        with tab1:
            show_equity_curve(backtest_data)
        
        with tab2:
            show_returns_analysis(backtest_data)
        
        with tab3:
            show_drawdown_analysis(backtest_data)
        
        with tab4:
            show_risk_metrics(backtest_data, performance_metrics)
        
        with tab5:
            show_mock_positions()
    
    else:
        # 显示说明信息
        st.info("""
        ### 📋 回测说明
        
        回测功能可以帮助您：
        
        1. **验证策略**: 在历史数据上测试投资策略的有效性
        2. **风险评估**: 了解策略的风险收益特征
        3. **参数优化**: 找到最优的策略参数组合
        4. **业绩归因**: 分析收益来源和风险因素
        
        ### 🚀 开始使用
        
        1. 选择回测时间范围
        2. 设置初始资金和风险参数
        3. 选择要测试的策略
        4. 点击"开始回测"按钮
        
        ### 📊 分析维度
        
        - **收益分析**: 总收益、年化收益、夏普比率
        - **风险分析**: 最大回撤、VaR、波动率
        - **持仓分析**: 持仓分布、换手率、集中度
        """)
        
        # 显示示例图表
        st.subheader("📈 示例回测结果")
        
        # 创建示例数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        values = 100000 * (1 + np.cumsum(np.random.randn(100) * 0.01))
        
        fig = px.line(
            x=dates,
            y=values,
            title="策略收益曲线示例",
            labels={'x': '日期', 'y': '资产价值'}
        )
        st.plotly_chart(fig, use_container_width=True)


# 导入groupby用于回撤分析
from itertools import groupby 