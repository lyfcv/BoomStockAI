import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def format_stock_code(code: str) -> str:
    """
    自动格式化股票代码，添加正确的市场前缀
    
    Args:
        code (str): 原始股票代码（如 '600000', '000001', '300787'）
    
    Returns:
        str: 格式化后的股票代码（如 'sh.600000', 'sz.000001', 'sz.300787'）
    """
    # 如果已经有前缀，直接返回
    if '.' in code and len(code) > 6:
        return code
    
    # 去除可能存在的前缀和空格
    clean_code = code.replace('sh.', '').replace('sz.', '').replace('bj.', '').strip()
    
    # 确保是6位数字
    if not clean_code.isdigit() or len(clean_code) != 6:
        raise ValueError(f"无效的股票代码: {code}，股票代码应为6位数字")
    
    # 根据代码规则判断市场
    if clean_code.startswith('6'):
        # 6开头：上海主板
        return f'sh.{clean_code}'
    elif clean_code.startswith('0'):
        # 0开头：深圳主板
        return f'sz.{clean_code}'
    elif clean_code.startswith('3'):
        # 3开头：创业板
        return f'sz.{clean_code}'
    elif clean_code.startswith('688'):
        # 688开头：科创板
        return f'sh.{clean_code}'
    elif clean_code.startswith('8'):
        # 8开头：北交所
        return f'bj.{clean_code}'
    else:
        # 其他情况默认深圳
        return f'sz.{clean_code}'


def get_stock_info(code: str) -> dict:
    """
    根据股票代码获取股票信息
    
    Args:
        code (str): 股票代码
    
    Returns:
        dict: 包含股票信息的字典
    """
    clean_code = code.replace('sh.', '').replace('sz.', '').replace('bj.', '').strip()
    
    if clean_code.startswith('6'):
        return {
            'market': '上海主板',
            'market_code': 'SH',
            'description': '上海证券交易所主板'
        }
    elif clean_code.startswith('0'):
        return {
            'market': '深圳主板',
            'market_code': 'SZ',
            'description': '深圳证券交易所主板'
        }
    elif clean_code.startswith('3'):
        return {
            'market': '创业板',
            'market_code': 'SZ',
            'description': '深圳证券交易所创业板'
        }
    elif clean_code.startswith('688'):
        return {
            'market': '科创板',
            'market_code': 'SH',
            'description': '上海证券交易所科创板'
        }
    elif clean_code.startswith('8'):
        return {
            'market': '北交所',
            'market_code': 'BJ',
            'description': '北京证券交易所'
        }
    else:
        return {
            'market': '未知',
            'market_code': 'UNKNOWN',
            'description': '未知市场'
        }


def get_k_data(stock_code: str, count: int, frequency: str = "d", include_valuation: bool = True) -> Optional[pd.DataFrame]:
    """
    获取股票的K线数据（支持多种频率，保持原始输出格式）
    支持自动识别股票代码市场前缀
    
    Args:
        stock_code (str): 股票代码，支持带前缀（'sh.600000'）或不带前缀（'600000'）
        count (int): 需要获取的K线数据条数
        frequency (str): 数据频率类型
            - "d": 日K线（默认）
            - "w": 周K线  
            - "m": 月K线
            - "5": 5分钟K线
            - "15": 15分钟K线
            - "30": 30分钟K线
            - "60": 60分钟K线
        include_valuation (bool): 是否包含估值指标（仅日线支持），默认为True
    
    Returns:
        pd.DataFrame: 包含K线数据的DataFrame（原始字符串格式），如果获取失败则返回None
        
    DataFrame包含的字段：
        日线字段：
        - date: 交易所行情日期
        - code: 证券代码
        - open, high, low, close, preclose: 价格数据
        - volume: 成交数量
        - amount: 成交金额
        - adjustflag: 复权状态
        - turn: 换手率
        - tradestatus: 交易状态
        - pctChg: 涨跌幅
        - isST: 是否ST
        - 估值指标（可选）: peTTM, psTTM, pcfNcfTTM, pbMRQ
        
        分钟线字段：
        - date: 日期
        - time: 时间
        - code: 证券代码
        - open, high, low, close: 价格数据
        - volume: 成交数量
        - amount: 成交金额
        - adjustflag: 复权状态
        
        周月线字段：
        - date: 日期
        - code: 证券代码
        - open, high, low, close: 价格数据
        - volume: 成交数量
        - amount: 成交金额
        - adjustflag: 复权状态
        - turn: 换手率
        - pctChg: 涨跌幅
    """
    
    # 自动格式化股票代码
    try:
        formatted_stock_code = format_stock_code(stock_code)
        stock_info = get_stock_info(formatted_stock_code)
        
        # 如果输入的是原始代码（不带前缀），显示识别信息
        if '.' not in stock_code:
            print(f"📊 自动识别股票: {stock_code} -> {formatted_stock_code} ({stock_info['market']})")
        
        stock_code = formatted_stock_code
        
    except ValueError as e:
        print(f"❌ 股票代码错误: {e}")
        return None
    
    # 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f'登录失败 error_code: {lg.error_code}, error_msg: {lg.error_msg}')
        return None
    
    try:
        # 根据频率类型确定时间范围和字段
        frequency_lower = frequency.lower()
        
        # 计算时间范围
        if frequency_lower == "d":
            # 日线：向前推算足够天数
            days_to_subtract = count * 2
        elif frequency_lower in ["w"]:
            # 周线：向前推算足够周数
            days_to_subtract = count * 10  # 大约每周7天，多留一些余量
        elif frequency_lower in ["m"]:
            # 月线：向前推算足够月数
            days_to_subtract = count * 40  # 大约每月30天，多留一些余量
        else:
            # 分钟线：向前推算足够天数（分钟线数据量大）
            days_to_subtract = count // 50 + 10  # 估算，每天约240个5分钟数据
        
        start_date = (datetime.now() - timedelta(days=days_to_subtract)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 根据频率类型构建查询字段
        if frequency_lower == "d":
            # 日线字段
            base_fields = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
            valuation_fields = "peTTM,psTTM,pcfNcfTTM,pbMRQ"
            
            if include_valuation:
                query_fields = f"{base_fields},{valuation_fields}"
            else:
                query_fields = base_fields
                
        elif frequency_lower in ["5", "15", "30", "60"]:
            # 分钟线字段（不包含指数，不支持估值指标）
            query_fields = "date,time,code,open,high,low,close,volume,amount,adjustflag"
            if include_valuation:
                print("注意：分钟线不支持估值指标，将忽略 include_valuation 参数")
                
        elif frequency_lower in ["w", "m"]:
            # 周月线字段（不支持估值指标）
            query_fields = "date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg"
            if include_valuation:
                print("注意：周月线不支持估值指标，将忽略 include_valuation 参数")
        else:
            print(f"不支持的频率类型: {frequency}")
            return None
        
        # 获取历史K线数据
        rs = bs.query_history_k_data_plus(
            stock_code,
            query_fields,
            start_date=start_date, 
            end_date=end_date,
            frequency=frequency,
            adjustflag="3"  # 后复权
        )
        
        if rs.error_code != '0':
            print(f'查询K线数据失败 error_code: {rs.error_code}, error_msg: {rs.error_msg}')
            return None
        
        # 收集数据
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            print('未获取到任何数据')
            return None
        
        # 转换为DataFrame（保持原始字符串格式）
        result = pd.DataFrame(data_list, columns=rs.fields)
        
        # 根据频率类型进行排序
        if frequency_lower in ["5", "15", "30", "60"]:
            # 分钟线按日期和时间排序（最新的在前）
            result = result.sort_values(['date', 'time'], ascending=False)
        else:
            # 日线、周线、月线按日期排序（最新的在前）
            result = result.sort_values('date', ascending=False)
        
        # 只返回指定的数据条数
        result = result.head(count)
        
        # 显示频率类型信息
        freq_names = {
            "d": "日线", "w": "周线", "m": "月线",
            "5": "5分钟线", "15": "15分钟线", 
            "30": "30分钟线", "60": "60分钟线"
        }
        freq_name = freq_names.get(frequency_lower, f"{frequency}线")
        
        print(f'成功获取 {stock_code} 最近 {len(result)} 条{freq_name}数据')
        return result
        
    except Exception as e:
        print(f'获取K线数据时发生错误: {str(e)}')
        return None
    
    finally:
        # 登出系统
        bs.logout()


# 为了向后兼容，保留原来的函数名
def get_daily_k_data(stock_code: str, trading_days: int, include_valuation: bool = True) -> Optional[pd.DataFrame]:
    """
    获取股票的日K线数据（向后兼容函数）
    
    Args:
        stock_code (str): 股票代码
        trading_days (int): 交易日天数
        include_valuation (bool): 是否包含估值指标
    
    Returns:
        pd.DataFrame: 日K线数据
    """
    return get_k_data(stock_code, trading_days, "d", include_valuation)


def demo_usage():
    """
    演示如何使用get_k_data函数
    """
    print("=== 演示获取不同频率的K线数据 ===")
    
    # 测试自动识别功能
    test_codes = ['600873', 'sh.600873', '300787', '000001']
    
    for stock_code in test_codes:
        print(f"\n测试股票代码: {stock_code}")
        
        # 1. 获取日线数据
        print("\n1. 获取日线数据（包含估值指标）:")
        daily_data = get_k_data(stock_code, 5, "d", include_valuation=True)
        if daily_data is not None:
            print(f"字段: {list(daily_data.columns)}")
            print(daily_data.head(2))
        
        break  # 只测试第一个代码


if __name__ == "__main__":
    demo_usage()