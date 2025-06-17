"""
个股分析页面
显示单只股票的详细分析信息
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import stock_dao, news_dao


def show_stock_selector():
    """显示股票选择器"""
    st.subheader("🔍 选择股票")
    
    # 股票代码输入
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_code = st.text_input(
            "请输入股票代码", 
            placeholder="如: 000001, 600000",
            help="输入6位股票代码"
        )
    
    with col2:
        if st.button("🔍 分析", use_container_width=True):
            if stock_code:
                return stock_code.strip()
    
    # 热门股票快速选择
    st.write("**快速选择:**")
    popular_stocks = {
        "000001": "平安银行",
        "000002": "万科A", 
        "600000": "浦发银行",
        "600036": "招商银行",
        "000858": "五粮液",
        "002415": "海康威视",
        "000725": "京东方A",
        "002594": "比亚迪"
    }
    
    cols = st.columns(4)
    for i, (code, name) in enumerate(popular_stocks.items()):
        with cols[i % 4]:
            if st.button(f"{code}\n{name}", key=f"stock_{code}"):
                return code
    
    return None


def show_stock_basic_info(stock_code):
    """显示股票基本信息"""
    try:
        stock_info = stock_dao.get_stock_by_code(stock_code)
        
        if not stock_info:
            st.error(f"未找到股票代码: {stock_code}")
            return None
        
        st.subheader(f"📊 {stock_info['name']} ({stock_info['code']})")
        
        # 基本信息卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("市场", stock_info['market'])
        
        with col2:
            st.metric("行业", stock_info.get('industry', '未知'))
        
        with col3:
            st.metric("状态", "正常" if stock_info['is_active'] else "停牌")
        
        with col4:
            # 模拟当前价格
            st.metric("当前价格", "12.34", "0.56 (4.8%)")
        
        return stock_info
        
    except Exception as e:
        st.error(f"获取股票信息失败: {e}")
        return None


def show_price_chart(stock_id, stock_name):
    """显示价格走势图"""
    st.subheader("📈 价格走势")
    
    try:
        # 获取价格数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        price_data = stock_dao.get_stock_prices(stock_id, start_date, end_date)
        
        if not price_data:
            st.info("暂无价格数据，请先更新股票数据")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame(price_data)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')
        
        # 创建K线图
        fig = go.Figure()
        
        # 添加K线
        fig.add_trace(go.Candlestick(
            x=df['trade_date'],
            open=df['open_price'],
            high=df['high_price'],
            low=df['low_price'],
            close=df['close_price'],
            name=stock_name
        ))
        
        # 添加成交量
        fig.add_trace(go.Bar(
            x=df['trade_date'],
            y=df['volume'],
            name='成交量',
            yaxis='y2',
            opacity=0.3
        ))
        
        # 设置双Y轴
        fig.update_layout(
            title=f"{stock_name} - 价格走势图",
            yaxis=dict(title="价格", side="left"),
            yaxis2=dict(title="成交量", side="right", overlaying="y"),
            xaxis_title="日期",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示最近几天的数据表格
        st.subheader("📋 最近交易数据")
        recent_data = df.tail(10)[['trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']].copy()
        recent_data.columns = ['日期', '开盘', '最高', '最低', '收盘', '成交量']
        recent_data = recent_data.iloc[::-1]  # 倒序显示
        st.dataframe(recent_data, use_container_width=True)
        
    except Exception as e:
        st.error(f"获取价格数据失败: {e}")


def show_analysis_result(stock_id, stock_name):
    """显示分析结果"""
    st.subheader("🧠 AI分析结果")
    
    try:
        # 获取最新分析结果
        analysis = stock_dao.get_latest_analysis(stock_id)
        
        if not analysis:
            st.info("暂无分析数据，请先运行分析策略")
            return
        
        # 分析结果概览
        col1, col2, col3 = st.columns(3)
        
        with col1:
            score_color = "normal" if analysis['total_score'] >= 70 else "inverse"
            st.metric(
                "综合评分", 
                f"{analysis['total_score']:.1f}",
                delta=None,
                delta_color=score_color
            )
        
        with col2:
            st.metric("投资建议", analysis['recommendation'])
        
        with col3:
            st.metric("置信度", f"{analysis['confidence']:.1%}")
        
        # 详细评分
        st.subheader("📊 详细评分")
        
        scores = {
            '技术分析': analysis.get('technical_score', 0),
            '基本面分析': analysis.get('fundamental_score', 0),
            '情感分析': analysis.get('sentiment_score', 0)
        }
        
        # 雷达图
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=stock_name
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="多维分析评分",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # AI分析报告
        if analysis.get('ai_analysis'):
            st.subheader("📝 AI分析报告")
            st.write(analysis['ai_analysis'])
        
    except Exception as e:
        st.error(f"获取分析结果失败: {e}")


def show_related_news(stock_code):
    """显示相关新闻"""
    st.subheader("📰 相关新闻")
    
    try:
        # 获取相关新闻
        news_list = news_dao.get_recent_news(stock_code=stock_code, limit=10)
        
        if not news_list:
            st.info("暂无相关新闻")
            return
        
        # 情感分析汇总
        sentiment_summary = news_dao.get_sentiment_summary(stock_code, days=7)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("新闻数量", sentiment_summary['count'])
        with col2:
            avg_sentiment = sentiment_summary['average_sentiment']
            sentiment_label = "积极" if avg_sentiment > 0.1 else "消极" if avg_sentiment < -0.1 else "中性"
            st.metric("平均情感", sentiment_label)
        with col3:
            st.metric("积极新闻", sentiment_summary['positive_count'])
        with col4:
            st.metric("消极新闻", sentiment_summary['negative_count'])
        
        # 新闻列表
        for news in news_list:
            with st.expander(f"📄 {news['title']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**来源**: {news['source']}")
                    st.write(f"**时间**: {news['publish_time']}")
                    st.write(news['content'])
                
                with col2:
                    if news['sentiment_score'] is not None:
                        sentiment_emoji = "😊" if news['sentiment_score'] > 0 else "😔" if news['sentiment_score'] < 0 else "😐"
                        st.metric(
                            f"{sentiment_emoji} 情感",
                            f"{news['sentiment_score']:.2f}"
                        )
        
    except Exception as e:
        st.error(f"获取相关新闻失败: {e}")


def show_stock_detail():
    """显示个股详细分析页面"""
    st.header("🔍 个股分析")
    
    # 股票选择器
    selected_stock = show_stock_selector()
    
    if selected_stock:
        # 显示股票基本信息
        stock_info = show_stock_basic_info(selected_stock)
        
        if stock_info:
            stock_id = stock_info['id']
            stock_name = stock_info['name']
            
            st.markdown("---")
            
            # 创建标签页
            tab1, tab2, tab3 = st.tabs(["📈 价格走势", "🧠 分析结果", "📰 相关新闻"])
            
            with tab1:
                show_price_chart(stock_id, stock_name)
            
            with tab2:
                show_analysis_result(stock_id, stock_name)
            
            with tab3:
                show_related_news(selected_stock)
    
    else:
        # 显示使用说明
        st.info("""
        ### 📋 使用说明
        
        1. **输入股票代码**: 在上方输入框中输入6位股票代码
        2. **快速选择**: 点击热门股票按钮快速选择
        3. **查看分析**: 系统将显示详细的技术分析、基本面分析和新闻情感分析
        
        ### 📊 功能特色
        
        - **实时价格**: K线图显示价格走势
        - **AI分析**: 多维度智能分析评分
        - **新闻追踪**: 相关新闻和情感分析
        - **投资建议**: 基于AI模型的投资建议
        """)
        
        # 显示示例图表
        st.subheader("📈 示例分析图表")
        
        # 创建示例数据
        import numpy as np
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        prices = 10 + np.cumsum(np.random.randn(30) * 0.1)
        
        fig = px.line(
            x=dates, 
            y=prices, 
            title="股票价格走势示例",
            labels={'x': '日期', 'y': '价格'}
        )
        st.plotly_chart(fig, use_container_width=True) 