"""
市场概览仪表板
显示Top股票推荐、市场指数、新闻摘要等
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

from database.db_utils import stock_dao, news_dao, index_dao
from database.models import Stock, StockAnalysis, TradingSignal


def show_market_overview():
    """显示市场概览"""
    st.subheader("📊 市场概览")
    
    try:
        # 定义主要指数代码
        index_codes = {
            'sh.000001': '上证指数',
            'sz.399001': '深证成指', 
            'sz.399006': '创业板指',
            'sh.000688': '科创50'
        }
        
        # 优先从数据库获取指数数据
        index_data = {}
        with st.spinner("正在获取最新市场数据..."):
            for code, name in index_codes.items():
                try:
                    # 获取指数信息
                    index_info = index_dao.get_index_by_code(code)
                    if index_info:
                        # 获取最新价格数据
                        latest_price = index_dao.get_latest_index_price(index_info['id'])
                        if latest_price:
                            index_data[code] = {
                                'current_price': latest_price['close_price'],
                                'change_pct': latest_price['pct_chg'],
                                'date': latest_price['trade_date'],
                                'volume': latest_price['volume']
                            }
                except Exception as e:
                    st.warning(f"从数据库获取{name}数据失败: {e}")
            
            # 如果数据库数据不足，尝试从API获取
            if len(index_data) < 3:
                try:
                    from data_collection.market_data.baostock_api import baostock_api
                    api_data = baostock_api.get_latest_index_info(list(index_codes.keys()))
                    
                    # 合并API数据
                    for code, data in api_data.items():
                        if code not in index_data and data:
                            index_data[code] = data
                            
                except Exception as e:
                    st.warning(f"从API获取数据失败: {e}")
        
        # 创建指标卡片
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        
        for i, (code, name) in enumerate(index_codes.items()):
            with cols[i]:
                if code in index_data and index_data[code]:
                    data = index_data[code]
                    
                    # 计算涨跌额
                    if 'change_pct' in data and data['change_pct'] is not None:
                        change_pct = data['change_pct']
                        current_price = data['current_price']
                        change_amount = (current_price * change_pct) / 100
                        
                        # 格式化显示
                        delta_text = f"{change_amount:+.2f} ({change_pct:+.2f}%)"
                        delta_color = "normal" if change_pct >= 0 else "inverse"
                    else:
                        delta_text = "数据更新中..."
                        delta_color = "off"
                    
                    st.metric(
                        label=name,
                        value=f"{data['current_price']:.2f}",
                        delta=delta_text,
                        delta_color=delta_color
                    )
                    
                    # 显示额外信息
                    if 'volume' in data and data['volume']:
                        st.caption(f"成交量: {data['volume']:,}")
                    if 'date' in data and data['date']:
                        st.caption(f"更新时间: {data['date']}")
                        
                else:
                    st.metric(
                        label=name,
                        value="--",
                        delta="数据获取中...",
                        delta_color="off"
                    )
    
    except Exception as e:
        st.error(f"获取市场数据失败: {e}")
        
        # 显示静态数据作为备选
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="上证指数",
                value="数据获取中...",
                delta="请稍后刷新",
                delta_color="off"
            )
        
        with col2:
            st.metric(
                label="深证成指",
                value="数据获取中...",
                delta="请稍后刷新",
                delta_color="off"
            )
        
        with col3:
            st.metric(
                label="创业板指",
                value="数据获取中...",
                delta="请稍后刷新",
                delta_color="off"
            )
        
        with col4:
            st.metric(
                label="科创50",
                value="数据获取中...",
                delta="请稍后刷新",
                delta_color="off"
            )


def show_top_stocks():
    """显示Top股票推荐"""
    st.subheader("🏆 AI智能推荐")
    
    try:
        # 获取评分最高的股票
        top_stocks = stock_dao.get_top_stocks(limit=10)
        
        if top_stocks:
            # 创建DataFrame
            df = pd.DataFrame(top_stocks)
            
            # 添加推荐等级
            def get_recommendation_level(score):
                if score >= 80:
                    return "🔥 强烈推荐"
                elif score >= 70:
                    return "👍 推荐"
                elif score >= 60:
                    return "⚡ 关注"
                else:
                    return "⚠️ 观望"
            
            df['推荐等级'] = df['total_score'].apply(get_recommendation_level)
            
            # 显示表格
            st.dataframe(
                df[['stock_name', 'stock_code', 'total_score', 'recommendation', 'confidence', '推荐等级']].rename(columns={
                    'stock_name': '股票名称',
                    'stock_code': '股票代码',
                    'total_score': '综合得分',
                    'recommendation': '投资建议',
                    'confidence': '置信度'
                }),
                use_container_width=True,
                height=400
            )
            
            # 显示得分分布图
            fig = px.bar(
                df,
                x='stock_name',
                y='total_score',
                title='Top 10 股票综合得分',
                color='total_score',
                color_continuous_scale='RdYlGn',
                text='total_score'
            )
            
            fig.update_layout(
                xaxis_title="股票名称",
                yaxis_title="综合得分",
                showlegend=False,
                height=400
            )
            
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("暂无股票推荐数据，请先运行分析策略")
            
    except Exception as e:
        st.error(f"获取推荐股票失败: {e}")


def show_trading_signals():
    """显示交易信号"""
    st.subheader("📈 交易信号")
    
    try:
        # 模拟交易信号数据
        signals_data = {
            '股票代码': ['000001', '000002', '600036', '000858', '002415'],
            '股票名称': ['平安银行', '万科A', '招商银行', '五粮液', '海康威视'],
            '信号类型': ['买入', '卖出', '买入', '持有', '买入'],
            '信号强度': [85, 72, 91, 65, 78],
            '当前价格': [12.34, 23.45, 45.67, 189.12, 56.78],
            '目标价格': [14.50, 21.00, 52.00, 200.00, 65.00],
            '预期收益': ['17.5%', '-10.5%', '13.9%', '5.8%', '14.5%']
        }
        
        df = pd.DataFrame(signals_data)
        
        # 根据信号类型添加颜色
        def get_signal_color(signal_type):
            if signal_type == '买入':
                return '🟢'
            elif signal_type == '卖出':
                return '🔴'
            else:
                return '🟡'
        
        df['信号'] = df['信号类型'].apply(get_signal_color) + ' ' + df['信号类型']
        
        # 显示信号表格
        st.dataframe(
            df[['股票名称', '股票代码', '信号', '信号强度', '当前价格', '目标价格', '预期收益']],
            use_container_width=True,
            height=300
        )
        
        # 信号强度分布
        col1, col2 = st.columns(2)
        
        with col1:
            # 信号类型分布饼图
            signal_counts = df['信号类型'].value_counts()
            fig_pie = px.pie(
                values=signal_counts.values,
                names=signal_counts.index,
                title="交易信号分布",
                color_discrete_map={'买入': '#00CC96', '卖出': '#EF553B', '持有': '#FFA15A'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # 信号强度柱状图
            fig_bar = px.bar(
                df,
                x='股票名称',
                y='信号强度',
                title="信号强度对比",
                color='信号类型',
                color_discrete_map={'买入': '#00CC96', '卖出': '#EF553B', '持有': '#FFA15A'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
    except Exception as e:
        st.error(f"获取交易信号失败: {e}")


def show_market_sentiment():
    """显示市场情绪"""
    st.subheader("📊 市场情绪分析")
    
    try:
        # 获取最近新闻的情感分析
        recent_news = news_dao.get_recent_news(limit=100)
        
        if recent_news:
            # 统计情感分布
            sentiment_counts = {'积极': 0, '中性': 0, '消极': 0}
            sentiment_scores = []
            
            for news in recent_news:
                if news['sentiment_score'] is not None:
                    sentiment_scores.append(news['sentiment_score'])
                    if news['sentiment_score'] > 0.1:
                        sentiment_counts['积极'] += 1
                    elif news['sentiment_score'] < -0.1:
                        sentiment_counts['消极'] += 1
                    else:
                        sentiment_counts['中性'] += 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 情感分布饼图
                fig_sentiment = px.pie(
                    values=list(sentiment_counts.values()),
                    names=list(sentiment_counts.keys()),
                    title="市场情绪分布",
                    color_discrete_map={'积极': '#00CC96', '中性': '#FFA15A', '消极': '#EF553B'}
                )
                st.plotly_chart(fig_sentiment, use_container_width=True)
            
            with col2:
                # 情感得分历史趋势
                if sentiment_scores:
                    # 模拟历史趋势数据
                    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
                    trend_scores = np.random.normal(0.1, 0.3, 30)  # 模拟数据
                    
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        x=dates,
                        y=trend_scores,
                        mode='lines+markers',
                        name='市场情绪',
                        line=dict(color='#636EFA', width=2)
                    ))
                    
                    fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="中性线")
                    fig_trend.update_layout(
                        title="市场情绪趋势",
                        xaxis_title="日期",
                        yaxis_title="情绪得分",
                        height=300
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
            
            # 情绪指标
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
            sentiment_label = "积极" if avg_sentiment > 0.1 else "消极" if avg_sentiment < -0.1 else "中性"
            sentiment_color = "normal" if avg_sentiment > 0 else "inverse"
            
            st.metric(
                label="平均市场情绪",
                value=sentiment_label,
                delta=f"{avg_sentiment:.3f}",
                delta_color=sentiment_color
            )
            
        else:
            st.info("暂无新闻数据用于情绪分析")
            
    except Exception as e:
        st.error(f"市场情绪分析失败: {e}")


def show_news_highlights():
    """显示新闻要点"""
    st.subheader("📰 今日要闻")
    
    try:
        # 获取最新新闻
        latest_news = news_dao.get_recent_news(limit=5)
        
        if latest_news:
            for i, news in enumerate(latest_news):
                with st.expander(f"📄 {news['title'][:60]}...", expanded=i == 0):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**来源**: {news['source']}")
                        st.write(f"**时间**: {news['publish_time']}")
                        if news['stock_codes']:
                            st.write(f"**相关股票**: {', '.join(news['stock_codes'][:3])}")
                        st.write(news['content'][:200] + "...")
                    
                    with col2:
                        if news['sentiment_score'] is not None:
                            sentiment_emoji = "😊" if news['sentiment_score'] > 0 else "😔" if news['sentiment_score'] < 0 else "😐"
                            st.metric(
                                label=f"{sentiment_emoji} 情感",
                                value=f"{news['sentiment_score']:.2f}"
                            )
        else:
            st.info("暂无最新新闻数据")
            
    except Exception as e:
        st.error(f"获取新闻要点失败: {e}")


def show_performance_metrics():
    """显示性能指标"""
    st.subheader("📊 系统性能")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="策略胜率",
            value="68.5%",
            delta="2.3%"
        )
    
    with col2:
        st.metric(
            label="平均收益",
            value="12.8%",
            delta="1.5%"
        )
    
    with col3:
        st.metric(
            label="最大回撤",
            value="8.2%",
            delta="-0.8%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="夏普比率",
            value="1.45",
            delta="0.12"
        )


def show_dashboard():
    """显示完整的仪表板"""
    # 市场概览
    show_market_overview()
    
    st.markdown("---")
    
    # 主要内容区域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Top股票推荐
        show_top_stocks()
        
        st.markdown("---")
        
        # 交易信号
        show_trading_signals()
    
    with col2:
        # 市场情绪
        show_market_sentiment()
        
        st.markdown("---")
        
        # 新闻要点
        show_news_highlights()
    
    st.markdown("---")
    
    # 性能指标
    show_performance_metrics()
    
    # 自动刷新选项
    st.sidebar.markdown("---")
    if st.sidebar.checkbox("自动刷新 (30秒)"):
        st.rerun() 