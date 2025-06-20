import baostock as bs
import pandas as pd
from datetime import datetime, timedelta


def get_stock_kline_30days(stock_code):
    """
    获取股票近30个交易日的K线数据
    
    Args:
        stock_code: 股票代码，如 '000001', '600000', 'sz.000001', 'sh.600000'
    
    Returns:
        pandas.DataFrame: K线数据，如果获取失败返回空DataFrame
    """
    
    #### 登陆系统 ####
    lg = bs.login()
    print('login respond error_code:' + lg.error_code)
    print('login respond error_msg:' + lg.error_msg)
    
    if lg.error_code != '0':
        print('登录失败，无法获取数据')
        return pd.DataFrame()
    
    try:
        # 标准化股票代码
        if not stock_code.startswith(('sh.', 'sz.')):
            if stock_code.startswith('6'):
                stock_code = f'sh.{stock_code}'
            else:
                stock_code = f'sz.{stock_code}'
        
        # 计算日期范围（获取更多天数确保有30个交易日）
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=50)).strftime('%Y-%m-%d')
        
        print(f'获取股票 {stock_code} 的K线数据，时间范围: {start_date} - {end_date}')
        
        #### 获取沪深A股历史K线数据 ####
        rs = bs.query_history_k_data_plus(stock_code,
            "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
            start_date=start_date, end_date=end_date,
            frequency="d", adjustflag="3")
        
        print('query_history_k_data_plus respond error_code:' + rs.error_code)
        print('query_history_k_data_plus respond error_msg:' + rs.error_msg)
        
        if rs.error_code != '0':
            print('查询数据失败')
            return pd.DataFrame()
        
        #### 获取结果集 ####
        data_list = []
        while (rs.error_code == '0') & rs.next():
            # 获取一条记录，将记录合并在一起
            data_list.append(rs.get_row_data())
        
        if not data_list:
            print('未获取到任何数据')
            return pd.DataFrame()
        
        result = pd.DataFrame(data_list, columns=rs.fields)
        
        # 数据类型转换
        numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors='coerce')
        
        # 转换日期
        result['date'] = pd.to_datetime(result['date'])
        
        # 按日期排序并取最近30个交易日
        result = result.sort_values('date').tail(30).reset_index(drop=True)
        
        print(f'成功获取 {len(result)} 条K线数据')
        return result
        
    except Exception as e:
        print(f'获取数据时出错: {e}')
        return pd.DataFrame()
    
    finally:
        #### 登出系统 ####
        bs.logout()
        print('已登出系统')


def format_kline_for_analysis(df_or_stock_code, stock_code=None):
    """
    格式化K线数据为适合大模型分析的格式
    
    Args:
        df_or_stock_code: 可以是DataFrame或股票代码字符串
        stock_code: 当第一个参数是DataFrame时，需要提供股票代码
    
    Returns:
        str: 格式化后的分析文本
    """
    # 如果第一个参数是字符串，说明是股票代码，需要先获取数据
    if isinstance(df_or_stock_code, str):
        stock_code = df_or_stock_code
        df = get_stock_kline_30days(stock_code)
    else:
        # 第一个参数是DataFrame
        df = df_or_stock_code
        if stock_code is None:
            stock_code = "未知"
    
    if df.empty:
        return f"股票代码 {stock_code} 的K线数据获取失败"
    
    # 计算统计数据
    latest_price = df['close'].iloc[-1]
    highest_price = df['close'].max()
    lowest_price = df['close'].min()
    first_price = df['close'].iloc[0]
    total_change = latest_price - first_price
    total_change_pct = (total_change / first_price) * 100 if first_price != 0 else 0
    
    # 构建分析文本
    analysis_text = f"""
股票代码: {stock_code}
数据时间: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')} (共{len(df)}个交易日)
价格区间: {lowest_price:.2f} - {highest_price:.2f}
当前价格: {latest_price:.2f}
期间涨跌: {total_change:+.2f} ({total_change_pct:+.2f}%)

完整30日K线数据 (Markdown表格):
| 日期 | 开盘价 | 最高价 | 最低价 | 收盘价 | 成交量 | 涨跌幅(%) | 趋势 |
|------|--------|--------|--------|--------|--------|-----------|------|"""
    
    # 添加每日数据
    for i, row in df.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        open_price = row['open']
        high_price = row['high'] 
        low_price = row['low']
        close_price = row['close']
        volume = row['volume']
        pct_chg = row['pctChg']
        
        # 涨跌趋势标识
        if pd.notna(pct_chg):
            if pct_chg > 0:
                trend_symbol = "📈"
                pct_chg_str = f"+{pct_chg:.2f}"
            elif pct_chg < 0:
                trend_symbol = "📉"
                pct_chg_str = f"{pct_chg:.2f}"
            else:
                trend_symbol = "➡️"
                pct_chg_str = "0.00"
        else:
            trend_symbol = "❓"
            pct_chg_str = "N/A"
        
        volume_str = f"{volume:,.0f}" if pd.notna(volume) else "N/A"
        analysis_text += f"\n| {date_str} | {open_price:.2f} | {high_price:.2f} | {low_price:.2f} | {close_price:.2f} | {volume_str} | {pct_chg_str} | {trend_symbol} |"
    
    return analysis_text


def analyze_stock_kline(stock_code):
    """
    分析股票K线数据 - 适合API调用
    
    Args:
        stock_code: 股票代码
        
    Returns:
        dict: 包含原始数据和分析文本的字典
    """
    df = get_stock_kline_30days(stock_code)
    analysis_text = format_kline_for_analysis(df, stock_code)
    
    return {
        'stock_code': stock_code,
        'success': not df.empty,
        'data': df.to_dict('records') if not df.empty else [],
        'analysis_text': analysis_text,
        'summary': {
            'latest_price': df['close'].iloc[-1] if not df.empty else None,
            'highest_price': df['close'].max() if not df.empty else None,
            'lowest_price': df['close'].min() if not df.empty else None,
            'total_change_pct': ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100) if not df.empty and df['close'].iloc[0] != 0 else 0,
            'trading_days': len(df) if not df.empty else 0
        }
    }


def main():
    """主函数，支持命令行参数和交互式使用"""
    import sys
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
        print(f"🚀 获取股票 {stock_code} 的K线数据...")
    else:
        # 交互式输入
        print("🎯 K线数据获取器")
        print("═" * 50)
        print("📌 支持格式: 000001, 600000, sz.000001, sh.600000")
        print("📊 自动获取近30个交易日数据")
        print("═" * 50)
        
        stock_code = input("💡 请输入股票代码: ").strip()
        
        if not stock_code:
            print("❌ 股票代码不能为空")
            return
    
    # 获取分析结果
    result = analyze_stock_kline(stock_code)
    
    if result['success']:
        print(result['analysis_text'])
    else:
        print("❌ 获取数据失败，请检查股票代码是否正确")
        print("💡 提示：请确认股票代码格式正确（如：000001, 600000）")


if __name__ == "__main__":
    main() 