import streamlit as st
import os
import json
from datetime import datetime
from typing import Dict, Any

# 页面配置在main.py中已设置，这里不需要重复设置

# 导入Agent模块
try:
    import sys
    import os
    # 添加项目根目录到路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    
    from strategy_center.analysis_agent.stock_analysis_agent import StockAnalysisAgent, create_stock_agent
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.error("请确保已安装必要的依赖包：pip install openai langchain langchain-openai langchain-community")
    st.stop()


def init_session_state():
    """初始化会话状态"""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []


def create_agent_instance(api_key: str, base_url: str) -> StockAnalysisAgent:
    """创建Agent实例"""
    try:
        agent = create_stock_agent(api_key=api_key, base_url=base_url)
        return agent
    except Exception as e:
        st.error(f"创建Agent失败: {e}")
        return None


def display_analysis_result(result: Dict[str, Any]):
    """显示分析结果"""
    if result['success']:
        st.success("✅ 分析完成")
        
        # 显示基本信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("股票代码", result['stock_code'])
        with col2:
            st.metric("分析时间", result['timestamp'][:19])
        with col3:
            st.metric("状态", "成功" if result['success'] else "失败")
        
        # 显示分析内容
        st.markdown("### 📊 AI分析报告")
        st.markdown(result['analysis'])
        
        # 保存到历史记录
        st.session_state.analysis_history.append(result)
        
    else:
        st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")


def display_chat_message(message: str, is_user: bool = True):
    """显示聊天消息"""
    if is_user:
        with st.chat_message("user"):
            st.write(message)
    else:
        with st.chat_message("assistant"):
            st.write(message)


def main():
    """主函数"""
    init_session_state()
    
    # 页面标题
    st.title("🤖 股票AI分析师")
    st.markdown("---")
    st.markdown("### 基于 ChatGPT-4o + LangChain 的智能股票分析系统")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置设置")
        
        # API配置
        st.subheader("🔑 API配置")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="请输入您的OpenAI API密钥"
        )
        
        base_url = st.text_input(
            "API中转地址",
            value="https://aihubmix.com/v1",
            help="API中转服务地址"
        )
        
        # 创建Agent按钮
        if st.button("🚀 初始化AI分析师", type="primary"):
            if api_key:
                with st.spinner("正在初始化AI分析师..."):
                    agent = create_agent_instance(api_key, base_url)
                    if agent:
                        st.session_state.agent = agent
                        st.success("✅ AI分析师初始化成功！")
                    else:
                        st.error("❌ 初始化失败，请检查API配置")
            else:
                st.error("请先输入API Key")
        
        # 显示Agent状态
        if st.session_state.agent:
            st.success("🟢 AI分析师已就绪")
        else:
            st.warning("🟡 请先初始化AI分析师")
        
        st.markdown("---")
        
        # 功能选择
        st.subheader("📋 功能选择")
        mode = st.radio(
            "选择使用模式",
            ["股票分析", "智能对话", "分析历史"],
            help="选择不同的功能模式"
        )
    
    # 主界面内容
    if not st.session_state.agent:
        st.info("👈 请先在侧边栏配置API并初始化AI分析师")
        
        # 显示功能介绍
        st.markdown("### 🌟 功能特色")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 📊 智能分析
            - 30日K线数据分析
            - 技术指标计算
            - 趋势判断
            - 成交量分析
            """)
        
        with col2:
            st.markdown("""
            #### 🤖 AI对话
            - 自然语言交互
            - 专业投资建议
            - 风险评估
            - 个性化分析
            """)
        
        with col3:
            st.markdown("""
            #### 📈 数据支持
            - 实时K线数据
            - 多种股票代码格式
            - 历史数据回顾
            - 可视化展示
            """)
        
        return
    
    # 根据模式显示不同界面
    if mode == "股票分析":
        display_stock_analysis_interface()
    elif mode == "智能对话":
        display_chat_interface()
    elif mode == "分析历史":
        display_history_interface()


def display_stock_analysis_interface():
    """显示股票分析界面"""
    st.header("📊 股票技术分析")
    
    # 输入区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        stock_code = st.text_input(
            "股票代码",
            placeholder="请输入股票代码，如：000001、600000、sz.000001",
            help="支持多种格式的股票代码"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 添加间距
        analyze_btn = st.button("🔍 开始分析", type="primary")
    
    # 高级选项
    with st.expander("🔧 高级选项"):
        analysis_type = st.selectbox(
            "分析类型",
            ["全面分析", "技术指标分析", "趋势分析", "风险评估"],
            help="选择特定的分析类型"
        )
        
        custom_query = st.text_area(
            "自定义分析需求",
            placeholder="例如：重点分析该股票的短期走势和支撑阻力位...",
            help="可以输入特定的分析需求"
        )
    
    # 执行分析
    if analyze_btn and stock_code:
        if st.session_state.agent:
            with st.spinner("🤖 AI分析师正在分析中..."):
                # 构建查询
                if custom_query:
                    query = custom_query
                else:
                    query_map = {
                        "全面分析": None,
                        "技术指标分析": "请重点分析技术指标，包括移动平均线、成交量等指标",
                        "趋势分析": "请重点分析价格趋势，判断短期和中期走势",
                        "风险评估": "请重点分析投资风险，包括价格波动风险和市场风险"
                    }
                    query = query_map.get(analysis_type)
                
                # 执行分析
                result = st.session_state.agent.analyze_stock(stock_code, query)
                display_analysis_result(result)
        else:
            st.error("请先初始化AI分析师")
    elif analyze_btn and not stock_code:
        st.warning("请输入股票代码")


def display_chat_interface():
    """显示聊天界面"""
    st.header("💬 智能对话")
    
    # 显示聊天历史
    chat_container = st.container()
    
    with chat_container:
        for i, (msg, is_user) in enumerate(st.session_state.chat_history):
            display_chat_message(msg, is_user)
    
    # 聊天输入
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "与AI分析师对话",
            placeholder="例如：帮我分析一下平安银行最近的走势...",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            send_btn = st.form_submit_button("发送", type="primary")
        with col2:
            clear_btn = st.form_submit_button("清空历史")
    
    # 处理用户输入
    if send_btn and user_input:
        if st.session_state.agent:
            # 添加用户消息到历史
            st.session_state.chat_history.append((user_input, True))
            
            with st.spinner("🤖 AI分析师思考中..."):
                # 获取AI回复
                result = st.session_state.agent.chat(user_input)
                
                if result['success']:
                    # 添加AI回复到历史
                    st.session_state.chat_history.append((result['response'], False))
                else:
                    error_msg = f"抱歉，出现了错误：{result.get('error', '未知错误')}"
                    st.session_state.chat_history.append((error_msg, False))
            
            # 刷新页面显示新消息
            st.rerun()
        else:
            st.error("请先初始化AI分析师")
    
    # 清空历史
    if clear_btn:
        st.session_state.chat_history = []
        st.rerun()


def display_history_interface():
    """显示历史记录界面"""
    st.header("📚 分析历史")
    
    if not st.session_state.analysis_history:
        st.info("暂无分析历史记录")
        return
    
    # 显示历史记录统计
    st.subheader("📊 统计信息")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总分析次数", len(st.session_state.analysis_history))
    
    with col2:
        success_count = sum(1 for h in st.session_state.analysis_history if h['success'])
        st.metric("成功分析", success_count)
    
    with col3:
        unique_stocks = len(set(h['stock_code'] for h in st.session_state.analysis_history))
        st.metric("分析股票数", unique_stocks)
    
    st.markdown("---")
    
    # 显示历史记录列表
    st.subheader("📋 历史记录")
    
    for i, record in enumerate(reversed(st.session_state.analysis_history)):
        with st.expander(
            f"📊 {record['stock_code']} - {record['timestamp'][:19]} "
            f"{'✅' if record['success'] else '❌'}"
        ):
            if record['success']:
                st.markdown("**查询：**")
                st.text(record['query'])
                st.markdown("**分析结果：**")
                st.markdown(record['analysis'])
            else:
                st.error(f"分析失败: {record.get('error', '未知错误')}")
    
    # 清空历史按钮
    if st.button("🗑️ 清空历史记录", type="secondary"):
        st.session_state.analysis_history = []
        st.rerun()


if __name__ == "__main__":
    main() 