"""
BoomStockAI 数据库模型定义
包含股票数据、新闻数据、分析结果等表结构
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, comment='股票代码')
    name = Column(String(100), nullable=False, comment='股票名称')
    market = Column(String(10), nullable=False, comment='市场标识(SH/SZ)')
    industry = Column(String(50), comment='所属行业')
    sector = Column(String(50), comment='所属板块')
    is_active = Column(Boolean, default=True, comment='是否有效')
    list_date = Column(DateTime, comment='上市日期')
    delist_date = Column(DateTime, comment='退市日期')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    price_data = relationship("StockPrice", back_populates="stock")
    fundamental_data = relationship("StockFundamental", back_populates="stock")
    analysis_results = relationship("StockAnalysis", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock(code='{self.code}', name='{self.name}')>"


class StockPrice(Base):
    """股票价格数据表"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    trade_date = Column(DateTime, nullable=False, comment='交易日期')
    open_price = Column(Float, comment='开盘价')
    high_price = Column(Float, comment='最高价')
    low_price = Column(Float, comment='最低价')
    close_price = Column(Float, comment='收盘价')
    preclose_price = Column(Float, comment='前收盘价')
    volume = Column(BigInteger, comment='成交量')
    amount = Column(Float, comment='成交金额')
    turnover_rate = Column(Float, comment='换手率')
    trade_status = Column(Integer, comment='交易状态(1:正常 0:停牌)')
    pct_chg = Column(Float, comment='涨跌幅(%)')
    pe_ratio = Column(Float, comment='市盈率(TTM)')
    pb_ratio = Column(Float, comment='市净率(MRQ)')
    ps_ratio = Column(Float, comment='市销率(TTM)')
    pcf_ratio = Column(Float, comment='市现率(TTM)')
    is_st = Column(Boolean, default=False, comment='是否ST股票')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    stock = relationship("Stock", back_populates="price_data")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_date', 'stock_id', 'trade_date'),
    )
    
    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, date={self.trade_date})>"


class MarketIndex(Base):
    """市场指数基本信息表"""
    __tablename__ = 'market_indices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, comment='指数代码')
    name = Column(String(100), nullable=False, comment='指数名称')
    market = Column(String(10), nullable=False, comment='市场标识(SH/SZ)')
    category = Column(String(50), comment='指数类别')
    description = Column(Text, comment='指数描述')
    base_date = Column(DateTime, comment='基准日期')
    base_point = Column(Float, comment='基准点数')
    is_active = Column(Boolean, default=True, comment='是否有效')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    price_data = relationship("MarketIndexPrice", back_populates="index")
    
    def __repr__(self):
        return f"<MarketIndex(code='{self.code}', name='{self.name}')>"


class MarketIndexPrice(Base):
    """市场指数价格数据表"""
    __tablename__ = 'market_index_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    index_id = Column(Integer, ForeignKey('market_indices.id'), nullable=False)
    trade_date = Column(DateTime, nullable=False, comment='交易日期')
    open_price = Column(Float, comment='开盘点数')
    high_price = Column(Float, comment='最高点数')
    low_price = Column(Float, comment='最低点数')
    close_price = Column(Float, comment='收盘点数')
    preclose_price = Column(Float, comment='前收盘点数')
    volume = Column(BigInteger, comment='成交量')
    amount = Column(Float, comment='成交金额')
    pct_chg = Column(Float, comment='涨跌幅(%)')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    index = relationship("MarketIndex", back_populates="price_data")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_index_date', 'index_id', 'trade_date'),
    )
    
    def __repr__(self):
        return f"<MarketIndexPrice(index_id={self.index_id}, date={self.trade_date})>"


class StockFundamental(Base):
    """股票基本面数据表"""
    __tablename__ = 'stock_fundamentals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    report_date = Column(DateTime, nullable=False, comment='报告期')
    total_assets = Column(Float, comment='总资产')
    total_equity = Column(Float, comment='股东权益')
    revenue = Column(Float, comment='营业收入')
    net_profit = Column(Float, comment='净利润')
    eps = Column(Float, comment='每股收益')
    roe = Column(Float, comment='净资产收益率')
    roa = Column(Float, comment='总资产收益率')
    gross_margin = Column(Float, comment='毛利率')
    net_margin = Column(Float, comment='净利率')
    debt_ratio = Column(Float, comment='资产负债率')
    current_ratio = Column(Float, comment='流动比率')
    quick_ratio = Column(Float, comment='速动比率')
    revenue_growth = Column(Float, comment='营收增长率')
    profit_growth = Column(Float, comment='净利润增长率')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    stock = relationship("Stock", back_populates="fundamental_data")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_report', 'stock_id', 'report_date'),
    )


class NewsArticle(Base):
    """新闻文章表"""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, comment='标题')
    content = Column(Text, comment='内容')
    source = Column(String(100), comment='来源')
    author = Column(String(100), comment='作者')
    publish_time = Column(DateTime, comment='发布时间')
    url = Column(String(1000), comment='原文链接')
    sentiment_score = Column(Float, comment='情感得分')
    sentiment_label = Column(String(20), comment='情感标签')
    keywords = Column(JSON, comment='关键词')
    stock_codes = Column(JSON, comment='相关股票代码')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:50]}...')>"


class StockAnalysis(Base):
    """股票分析结果表"""
    __tablename__ = 'stock_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    analysis_date = Column(DateTime, nullable=False, comment='分析日期')
    strategy_name = Column(String(100), nullable=False, comment='策略名称')
    
    # 技术指标分析
    technical_score = Column(Float, comment='技术分析得分')
    technical_signals = Column(JSON, comment='技术指标信号')
    
    # 基本面分析
    fundamental_score = Column(Float, comment='基本面得分')
    fundamental_metrics = Column(JSON, comment='基本面指标')
    
    # 情感分析
    sentiment_score = Column(Float, comment='情感分析得分')
    news_count = Column(Integer, comment='相关新闻数量')
    
    # 综合评分
    total_score = Column(Float, nullable=False, comment='综合得分')
    recommendation = Column(String(20), comment='投资建议(买入/持有/卖出)')
    confidence = Column(Float, comment='置信度')
    
    # AI分析结果
    ai_analysis = Column(Text, comment='AI分析报告')
    risk_factors = Column(JSON, comment='风险因素')
    opportunity_factors = Column(JSON, comment='机会因素')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    stock = relationship("Stock", back_populates="analysis_results")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_analysis_date', 'stock_id', 'analysis_date'),
        Index('idx_strategy_date', 'strategy_name', 'analysis_date'),
    )


class BacktestResult(Base):
    """回测结果表"""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False, comment='策略名称')
    start_date = Column(DateTime, nullable=False, comment='回测开始日期')
    end_date = Column(DateTime, nullable=False, comment='回测结束日期')
    initial_capital = Column(Float, nullable=False, comment='初始资金')
    final_capital = Column(Float, comment='最终资金')
    total_return = Column(Float, comment='总收益率')
    annual_return = Column(Float, comment='年化收益率')
    max_drawdown = Column(Float, comment='最大回撤')
    sharpe_ratio = Column(Float, comment='夏普比率')
    win_rate = Column(Float, comment='胜率')
    total_trades = Column(Integer, comment='总交易次数')
    config_params = Column(JSON, comment='策略参数')
    performance_metrics = Column(JSON, comment='详细业绩指标')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BacktestResult(strategy='{self.strategy_name}', return={self.total_return:.2%})>"


class TradingSignal(Base):
    """交易信号表"""
    __tablename__ = 'trading_signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    signal_date = Column(DateTime, nullable=False, comment='信号日期')
    signal_type = Column(String(20), nullable=False, comment='信号类型(买入/卖出)')
    strategy_name = Column(String(100), nullable=False, comment='策略名称')
    price = Column(Float, comment='信号价格')
    volume = Column(Integer, comment='建议成交量')
    confidence = Column(Float, comment='信号置信度')
    reason = Column(Text, comment='信号原因')
    is_executed = Column(Boolean, default=False, comment='是否已执行')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    stock = relationship("Stock")
    
    # 创建索引
    __table_args__ = (
        Index('idx_signal_date', 'signal_date'),
        Index('idx_stock_signal', 'stock_id', 'signal_date'),
    )


class ThsHotList(Base):
    """同花顺热榜数据表"""
    __tablename__ = 'ths_hot_list'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(String(10), nullable=False, comment='交易日期')
    market_type = Column(String(20), nullable=False, comment='热榜类型')
    ts_code = Column(String(20), nullable=False, comment='TS代码')
    ts_name = Column(String(100), comment='名称')
    rank = Column(Integer, comment='排名')
    pct_change = Column(Float, comment='涨跌幅')
    current_price = Column(Float, comment='当前价格')
    concept = Column(Text, comment='标签')
    rank_reason = Column(Text, comment='上榜原因')
    hot = Column(Float, comment='热度值')
    rank_time = Column(String(20), comment='排行获取时间')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ths_hot_date_market', 'trade_date', 'market_type'),
    )

    def __repr__(self):
        return f"<ThsHotList(trade_date='{self.trade_date}', market='{self.market_type}', code='{self.ts_code}', name='{self.ts_name}')>"


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_level = Column(String(20), nullable=False, comment='日志级别')
    module = Column(String(100), comment='模块名称')
    message = Column(Text, nullable=False, comment='日志消息')
    extra_data = Column(JSON, comment='额外数据')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='时间戳')
    
    # 创建索引
    __table_args__ = (
        Index('idx_log_timestamp', 'timestamp'),
        Index('idx_log_level', 'log_level'),
    ) 