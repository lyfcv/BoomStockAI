import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import ths_data_dao
from loguru import logger

def show_ths_hot_list_page():
    """
    显示同花顺热榜页面
    """
    st.markdown("## 🔥 同花顺热榜")
    st.markdown("每日更新的市场热点，助您把握投资脉搏。")

    # 筛选条件
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        selected_date = st.date_input("选择日期", datetime.now() - timedelta(days=1))
        trade_date_str = selected_date.strftime('%Y%m%d')

    with col2:
        market_types = ['热股', 'ETF', '可转债', '行业板块', '概念板块', '期货', '港股', '热基', '美股']
        selected_market = st.selectbox("选择榜单类型", market_types)

    with col3:
        st.write("") # for alignment
        st.write("") # for alignment
        if st.button("🔄 更新今日热榜", use_container_width=True):
            update_hot_list_data()

    # 获取并显示数据
    try:
        hot_list_data = ths_data_dao.get_ths_hot_list(
            market_type=selected_market,
            trade_date=trade_date_str
        )

        if hot_list_data:
            df = pd.DataFrame(hot_list_data)
            
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "ts_code": st.column_config.TextColumn("代码"),
                    "ts_name": st.column_config.TextColumn("名称"),
                    "rank": st.column_config.NumberColumn("排名", format="%d"),
                    "current_price": st.column_config.NumberColumn(
                        "当前价格",
                        format="%.2f"
                    ),
                    "pct_change": st.column_config.NumberColumn(
                        "涨跌幅(%)",
                        format="%.2f%%"
                    ),
                    "hot": st.column_config.NumberColumn(
                        "热度值",
                        format="%d"
                    ),
                    "concept": st.column_config.TextColumn("相关概念"),
                    "rank_reason": st.column_config.TextColumn("上榜原因"),
                    "rank_time": st.column_config.TextColumn("更新时间"),
                }
            )
            st.info(f"数据更新于: {df['rank_time'].max() if 'rank_time' in df.columns and not df.empty else 'N/A'}")

        else:
            st.warning(f"在 {trade_date_str} 没有找到 {selected_market} 的热榜数据。请尝试更新数据或选择其他日期。")

    except Exception as e:
        logger.error(f"获取同花顺热榜数据失败: {e}")
        st.error("加载数据时发生错误，请稍后再试。")

def update_hot_list_data():
    """
    调用脚本更新同花顺热榜数据
    """
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'update_ths_hot_list.py')
    
    with st.spinner("正在更新同花顺热榜数据，请稍候..."):
        try:
            # 使用 st.progress 来显示进度
            progress_bar = st.progress(0, text="开始更新...")
            
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # 更新进度条
            progress_bar.progress(30, text="正在从Tushare获取数据...")

            stdout, stderr = process.communicate()
            
            progress_bar.progress(90, text="正在将数据存入数据库...")

            if process.returncode == 0:
                progress_bar.progress(100, text="更新完成！")
                st.success("同花顺热榜数据更新成功！")
                logger.info("同花顺热榜数据更新成功。")
                st.rerun() # 重新加载页面以显示新数据
            else:
                st.error("数据更新失败。")
                st.text_area("错误详情:", stderr, height=200)
                logger.error(f"同花顺热榜数据更新失败: {stderr}")

        except Exception as e:
            st.error(f"执行更新脚本时发生错误: {e}")
            logger.error(f"执行更新脚本时发生错误: {e}") 