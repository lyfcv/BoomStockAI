"""
BoomStockAI Streamlit前端主应用
智能选股系统Web界面
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yaml
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import db_manager, stock_dao, news_dao
from frontend.dashboard import show_dashboard
from frontend.stock_detail import show_stock_detail
from frontend.backtest_view import show_backtest_results
from frontend.ths_hot_list_view import show_ths_hot_list_page
from frontend.stock_ai_agent import main as show_ai_agent_page

# 页面配置
st.set_page_config(
    page_title="BoomStockAI - 智能选股系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF6B6B;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #FF6B6B;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    
    .sidebar-header {
        font-size: 1.5rem;
        color: #333;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .stock-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f9f9f9;
    }
    
    .positive {
        color: #28a745;
        font-weight: bold;
    }
    
    .negative {
        color: #dc3545;
        font-weight: bold;
    }
    
    .warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def load_config():
    """加载配置文件"""
    try:
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"配置文件加载失败: {e}")
        return {}


def init_database():
    """初始化数据库连接"""
    try:
        if db_manager.test_connection():
            return True
        else:
            st.error("数据库连接失败，请检查配置")
            return False
    except Exception as e:
        st.error(f"数据库初始化失败: {e}")
        return False


def show_sidebar():
    """显示侧边栏"""
    st.sidebar.markdown('<div class="sidebar-header">🚀 BoomStockAI</div>', unsafe_allow_html=True)
    
    # 导航菜单
    pages = {
        "📊 市场概览": "dashboard",
        "🤖 AI分析师": "ai_agent",
        "🔥 同花顺热榜": "ths_hot_list",
        "🔍 个股分析": "stock_detail", 
        "📈 回测结果": "backtest",
        "📰 新闻资讯": "news",
        "⚙️ 系统设置": "settings"
    }
    
    selected_page = st.sidebar.selectbox(
        "选择功能页面",
        list(pages.keys()),
        index=0
    )
    
    # 系统状态
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 系统状态")
    
    # 数据库连接状态
    db_status = "🟢 已连接" if db_manager.test_connection() else "🔴 连接失败"
    st.sidebar.markdown(f"**数据库**: {db_status}")
    
    # 最后更新时间
    st.sidebar.markdown(f"**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 快速统计
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 快速统计")
    
    try:
        # 获取股票总数
        with db_manager.get_session() as session:
            from database.models import Stock, NewsArticle
            stock_count = session.query(Stock).filter(Stock.is_active == True).count()
            news_count = session.query(NewsArticle).filter(
                NewsArticle.created_at >= datetime.now() - timedelta(days=7)
            ).count()
        
        st.sidebar.metric("活跃股票", f"{stock_count:,}", "只")
        st.sidebar.metric("本周新闻", f"{news_count:,}", "条")
        
    except Exception as e:
        st.sidebar.error(f"统计数据获取失败: {e}")
    
    # 快速操作
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ 快速操作")
    
    if st.sidebar.button("🔄 刷新数据", use_container_width=True):
        st.rerun()
    
    if st.sidebar.button("📊 更新股价", use_container_width=True):
        with st.spinner("正在更新股价数据..."):
            # 这里可以调用数据更新接口
            st.success("股价数据更新完成！")
    
    if st.sidebar.button("📰 抓取新闻", use_container_width=True):
        with st.spinner("正在抓取最新新闻..."):
            # 这里可以调用新闻爬虫
            st.success("新闻数据更新完成！")
    
    return pages[selected_page]


def show_main_header():
    """显示主标题"""
    st.markdown(
        '<div class="main-header">📈 BoomStockAI 智能选股系统</div>', 
        unsafe_allow_html=True
    )


def show_news_page():
    """显示新闻资讯页面"""
    st.header("📰 财经新闻资讯")
    
    # 新闻筛选
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stock_code = st.text_input("股票代码筛选", placeholder="如: 000001")
    
    with col2:
        days = st.selectbox("时间范围", [1, 3, 7, 15, 30], index=2)
    
    with col3:
        source = st.selectbox("新闻来源", ["全部", "东方财富", "新浪财经", "腾讯财经"])
    
    # 获取新闻数据
    try:
        news_list = news_dao.get_recent_news(
            stock_code=stock_code if stock_code else None,
            limit=50
        )
        
        if news_list:
            st.success(f"共找到 {len(news_list)} 条相关新闻")
            
            # 显示新闻列表
            for news in news_list:
                with st.expander(f"📰 {news['title']}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**来源**: {news['source']}")
                        st.write(f"**时间**: {news['publish_time']}")
                        if news['stock_codes']:
                            st.write(f"**相关股票**: {', '.join(news['stock_codes'])}")
                        st.write(news['content'])
                    
                    with col2:
                        # 情感分析结果
                        if news['sentiment_score'] is not None:
                            sentiment_text = "积极" if news['sentiment_score'] > 0 else "消极" if news['sentiment_score'] < 0 else "中性"
                            sentiment_color = "positive" if news['sentiment_score'] > 0 else "negative" if news['sentiment_score'] < 0 else "warning"
                            st.markdown(f'<div class="{sentiment_color}">情感: {sentiment_text}</div>', unsafe_allow_html=True)
                            st.metric("情感得分", f"{news['sentiment_score']:.2f}")
        else:
            st.info("暂无相关新闻数据")
            
    except Exception as e:
        st.error(f"新闻数据获取失败: {e}")


def show_settings_page():
    """显示系统设置页面"""
    st.header("⚙️ 系统设置")
    
    # 数据源设置
    st.subheader("📡 数据源配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("启用BaoStock", value=True)
        st.checkbox("启用AKShare", value=True)
        st.number_input("数据更新频率(分钟)", min_value=1, max_value=1440, value=30)
    
    with col2:
        st.checkbox("启用新闻爬虫", value=True)
        st.number_input("新闻更新频率(分钟)", min_value=1, max_value=1440, value=15)
        st.number_input("爬虫延时(秒)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
    
    # 策略设置
    st.subheader("🧠 策略配置")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.checkbox("技术指标策略", value=True)
        st.multiselect("技术指标", ["RSI", "MACD", "MA", "BOLL", "KDJ"], default=["RSI", "MACD"])
    
    with col2:
        st.checkbox("基本面策略", value=True)
        st.multiselect("基本面因子", ["PE", "PB", "ROE", "营收增长率"], default=["PE", "PB"])
    
    with col3:
        st.checkbox("情感分析策略", value=True)
        st.slider("情感权重", 0.0, 1.0, 0.3, 0.1)
    
    # 风险控制
    st.subheader("🛡️ 风险控制")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.slider("单股最大仓位", 0.01, 0.5, 0.1, 0.01)
        st.slider("最大回撤限制", 0.05, 0.5, 0.15, 0.01)
    
    with col2:
        st.slider("止损比例", 0.01, 0.2, 0.08, 0.01)
        st.slider("止盈比例", 0.05, 1.0, 0.2, 0.01)
    
    # 保存设置
    if st.button("💾 保存设置", use_container_width=True):
        st.success("设置保存成功！")


def main():
    """主函数"""
    # 初始化数据库
    if not init_database():
        st.stop()
    
    # 显示侧边栏并获取选中页面
    selected_page = show_sidebar()
    
    # 显示主标题
    show_main_header()
    
    # 根据选中页面显示内容
    try:
        if selected_page == "dashboard":
            show_dashboard()
        elif selected_page == "ai_agent":
            show_ai_agent_page()
        elif selected_page == "stock_detail":
            show_stock_detail()
        elif selected_page == "backtest":
            show_backtest_results()
        elif selected_page == "news":
            show_news_page()
        elif selected_page == "ths_hot_list":
            show_ths_hot_list_page()
        elif selected_page == "settings":
            show_settings_page()
        else:
            show_dashboard()
            
    except Exception as e:
        st.error(f"页面加载失败: {e}")
        st.exception(e)


if __name__ == "__main__":
    main() 