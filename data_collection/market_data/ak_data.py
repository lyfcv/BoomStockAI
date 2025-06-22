import akshare as ak


"""创新高和新低的股票数量
接口: stock_a_high_low_statistics

目标地址: https://www.legulegu.com/stockdata/high-low-statistics

描述: 不同市场的创新高和新低的股票数量

限量: 单次获取指定 market 的近两年的历史数据

输入参数

名称	类型	描述
symbol	str	symbol="all"; {"all": "全部A股", "sz50": "上证50", "hs300": "沪深300", "zz500": "中证500"}
"""
stock_a_high_low_statistics_df = ak.stock_a_high_low_statistics(symbol="all")
print(stock_a_high_low_statistics_df)


"""股票热度-东财
人气榜-A股
接口: stock_hot_rank_em

目标地址: http://guba.eastmoney.com/rank/

描述: 东方财富网站-股票热度

限量: 单次返回当前交易日前 100 个股票的人气排名数据

输入参数

名称	类型	描述
-	-	-"""
stock_hot_rank_em_df = ak.stock_hot_rank_em()
print(stock_hot_rank_em_df)