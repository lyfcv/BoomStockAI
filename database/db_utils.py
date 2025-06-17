"""
数据库连接和常用操作工具类
"""
import os
import yaml
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from loguru import logger
from dotenv import load_dotenv

from .models import Base

# 加载环境变量
load_dotenv()


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化数据库连接"""
        self.config = self._load_config(config_path)
        self.engine = None
        self.SessionLocal = None
        self._init_engine()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 替换环境变量
            db_config = config['database']
            db_config['password'] = os.getenv('POSTGRES_PASSWORD', db_config.get('password', ''))
            db_config['host'] = os.getenv('POSTGRES_HOST', db_config.get('host', 'localhost'))
            db_config['port'] = int(os.getenv('POSTGRES_PORT', db_config.get('port', 5432)))
            db_config['name'] = os.getenv('POSTGRES_DB', db_config.get('name', 'boomstock_ai'))
            db_config['user'] = os.getenv('POSTGRES_USER', db_config.get('user', 'postgres'))
            
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def _init_engine(self):
        """初始化数据库引擎"""
        try:
            db_config = self.config['database']
            
            # 构建数据库连接URL
            db_url = (
                f"postgresql://{db_config['user']}:{db_config['password']}@"
                f"{db_config['host']}:{db_config['port']}/{db_config['name']}"
            )
            
            # 创建引擎
            self.engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=db_config.get('pool_size', 20),
                max_overflow=db_config.get('max_overflow', 40),
                pool_pre_ping=True,
                echo=db_config.get('echo', False)
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("数据库连接初始化成功")
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """获取数据库会话上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"数据库表删除失败: {e}")
            raise
    
    def execute_sql(self, sql: str, params: Optional[Dict] = None) -> Any:
        """执行SQL语句"""
        try:
            with self.get_session() as session:
                result = session.execute(text(sql), params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"SQL执行失败: {sql}, 错误: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False


class StockDataDAO:
    """股票数据访问对象"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        """根据股票代码获取股票信息"""
        try:
            with self.db_manager.get_session() as session:
                from .models import Stock
                stock = session.query(Stock).filter(Stock.code == code).first()
                if stock:
                    return {
                        'id': stock.id,
                        'code': stock.code,
                        'name': stock.name,
                        'market': stock.market,
                        'industry': stock.industry,
                        'sector': stock.sector,
                        'is_active': stock.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None
    
    def get_stock_prices(self, stock_id: int, start_date: str, end_date: str) -> List[Dict]:
        """获取股票价格数据"""
        try:
            with self.db_manager.get_session() as session:
                from .models import StockPrice
                prices = session.query(StockPrice).filter(
                    StockPrice.stock_id == stock_id,
                    StockPrice.trade_date >= start_date,
                    StockPrice.trade_date <= end_date
                ).order_by(StockPrice.trade_date).all()
                
                return [{
                    'trade_date': price.trade_date,
                    'open_price': price.open_price,
                    'high_price': price.high_price,
                    'low_price': price.low_price,
                    'close_price': price.close_price,
                    'volume': price.volume,
                    'amount': price.amount
                } for price in prices]
        except Exception as e:
            logger.error(f"获取股票价格数据失败: {e}")
            return []
    
    def get_latest_analysis(self, stock_id: int, strategy_name: str = None) -> Optional[Dict]:
        """获取最新的分析结果"""
        try:
            with self.db_manager.get_session() as session:
                from .models import StockAnalysis
                query = session.query(StockAnalysis).filter(
                    StockAnalysis.stock_id == stock_id
                )
                
                if strategy_name:
                    query = query.filter(StockAnalysis.strategy_name == strategy_name)
                
                analysis = query.order_by(StockAnalysis.analysis_date.desc()).first()
                
                if analysis:
                    return {
                        'analysis_date': analysis.analysis_date,
                        'strategy_name': analysis.strategy_name,
                        'technical_score': analysis.technical_score,
                        'fundamental_score': analysis.fundamental_score,
                        'sentiment_score': analysis.sentiment_score,
                        'total_score': analysis.total_score,
                        'recommendation': analysis.recommendation,
                        'confidence': analysis.confidence,
                        'ai_analysis': analysis.ai_analysis
                    }
                return None
        except Exception as e:
            logger.error(f"获取分析结果失败: {e}")
            return None
    
    def get_top_stocks(self, limit: int = 10, strategy_name: str = None) -> List[Dict]:
        """获取评分最高的股票"""
        try:
            with self.db_manager.get_session() as session:
                from .models import StockAnalysis, Stock
                query = session.query(StockAnalysis, Stock).join(Stock)
                
                if strategy_name:
                    query = query.filter(StockAnalysis.strategy_name == strategy_name)
                
                # 获取每只股票的最新分析结果
                subquery = query.order_by(
                    StockAnalysis.stock_id,
                    StockAnalysis.analysis_date.desc()
                ).distinct(StockAnalysis.stock_id).subquery()
                
                top_stocks = session.query(subquery).order_by(
                    subquery.c.total_score.desc()
                ).limit(limit).all()
                
                return [{
                    'stock_code': stock.code,
                    'stock_name': stock.name,
                    'total_score': stock.total_score,
                    'recommendation': stock.recommendation,
                    'confidence': stock.confidence,
                    'analysis_date': stock.analysis_date
                } for stock in top_stocks]
        except Exception as e:
            logger.error(f"获取Top股票失败: {e}")
            return []


class NewsDataDAO:
    """新闻数据访问对象"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_recent_news(self, stock_code: str = None, limit: int = 20) -> List[Dict]:
        """获取最近的新闻"""
        try:
            with self.db_manager.get_session() as session:
                from .models import NewsArticle
                query = session.query(NewsArticle)
                
                if stock_code:
                    query = query.filter(NewsArticle.stock_codes.contains([stock_code]))
                
                news = query.order_by(NewsArticle.publish_time.desc()).limit(limit).all()
                
                return [{
                    'title': article.title,
                    'content': article.content[:200] + '...' if len(article.content) > 200 else article.content,
                    'source': article.source,
                    'publish_time': article.publish_time,
                    'sentiment_score': article.sentiment_score,
                    'sentiment_label': article.sentiment_label,
                    'stock_codes': article.stock_codes
                } for article in news]
        except Exception as e:
            logger.error(f"获取新闻数据失败: {e}")
            return []
    
    def get_sentiment_summary(self, stock_code: str, days: int = 7) -> Dict:
        """获取情感分析汇总"""
        try:
            with self.db_manager.get_session() as session:
                from .models import NewsArticle
                from datetime import datetime, timedelta
                
                start_date = datetime.now() - timedelta(days=days)
                
                news = session.query(NewsArticle).filter(
                    NewsArticle.stock_codes.contains([stock_code]),
                    NewsArticle.publish_time >= start_date
                ).all()
                
                if not news:
                    return {'count': 0, 'average_sentiment': 0, 'positive_count': 0, 'negative_count': 0}
                
                total_sentiment = sum(article.sentiment_score for article in news if article.sentiment_score)
                positive_count = sum(1 for article in news if article.sentiment_score and article.sentiment_score > 0)
                negative_count = sum(1 for article in news if article.sentiment_score and article.sentiment_score < 0)
                
                return {
                    'count': len(news),
                    'average_sentiment': total_sentiment / len(news) if news else 0,
                    'positive_count': positive_count,
                    'negative_count': negative_count
                }
        except Exception as e:
            logger.error(f"获取情感分析汇总失败: {e}")
            return {'count': 0, 'average_sentiment': 0, 'positive_count': 0, 'negative_count': 0}


class MarketIndexDAO:
    """市场指数数据访问对象"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_index_by_code(self, code: str) -> Optional[Dict]:
        """根据指数代码获取指数信息"""
        try:
            with self.db_manager.get_session() as session:
                from .models import MarketIndex
                index = session.query(MarketIndex).filter(MarketIndex.code == code).first()
                if index:
                    return {
                        'id': index.id,
                        'code': index.code,
                        'name': index.name,
                        'market': index.market,
                        'category': index.category,
                        'description': index.description,
                        'is_active': index.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"获取指数信息失败: {e}")
            return None
    
    def get_index_prices(self, index_id: int, start_date: str, end_date: str) -> List[Dict]:
        """获取指数价格数据"""
        try:
            with self.db_manager.get_session() as session:
                from .models import MarketIndexPrice
                prices = session.query(MarketIndexPrice).filter(
                    MarketIndexPrice.index_id == index_id,
                    MarketIndexPrice.trade_date >= start_date,
                    MarketIndexPrice.trade_date <= end_date
                ).order_by(MarketIndexPrice.trade_date).all()
                
                return [{
                    'trade_date': price.trade_date,
                    'open_price': price.open_price,
                    'high_price': price.high_price,
                    'low_price': price.low_price,
                    'close_price': price.close_price,
                    'preclose_price': price.preclose_price,
                    'volume': price.volume,
                    'amount': price.amount,
                    'pct_chg': price.pct_chg
                } for price in prices]
        except Exception as e:
            logger.error(f"获取指数价格数据失败: {e}")
            return []
    
    def get_latest_index_price(self, index_id: int) -> Optional[Dict]:
        """获取最新指数价格"""
        try:
            with self.db_manager.get_session() as session:
                from .models import MarketIndexPrice
                price = session.query(MarketIndexPrice).filter(
                    MarketIndexPrice.index_id == index_id
                ).order_by(MarketIndexPrice.trade_date.desc()).first()
                
                if price:
                    return {
                        'trade_date': price.trade_date,
                        'close_price': price.close_price,
                        'pct_chg': price.pct_chg,
                        'volume': price.volume,
                        'amount': price.amount
                    }
                return None
        except Exception as e:
            logger.error(f"获取最新指数价格失败: {e}")
            return None
    
    def save_index_basic_info(self, index_list: List[Dict]) -> int:
        """保存指数基本信息"""
        try:
            count = 0
            with self.db_manager.get_session() as session:
                from .models import MarketIndex
                
                for index_info in index_list:
                    # 检查指数是否已存在
                    existing_index = session.query(MarketIndex).filter(
                        MarketIndex.code == index_info['code']
                    ).first()
                    
                    if existing_index:
                        # 更新现有指数信息
                        existing_index.name = index_info['name']
                        existing_index.market = index_info['market']
                        existing_index.category = index_info.get('category')
                        existing_index.description = index_info.get('description')
                        existing_index.is_active = index_info.get('is_active', True)
                        existing_index.updated_at = datetime.utcnow()
                    else:
                        # 创建新指数记录
                        new_index = MarketIndex(
                            code=index_info['code'],
                            name=index_info['name'],
                            market=index_info['market'],
                            category=index_info.get('category'),
                            description=index_info.get('description'),
                            is_active=index_info.get('is_active', True)
                        )
                        session.add(new_index)
                    
                    count += 1
                
                session.commit()
                logger.info(f"指数基本信息保存完成，共 {count} 个指数")
                return count
                
        except Exception as e:
            logger.error(f"保存指数基本信息失败: {e}")
            return 0
    
    def save_index_price_data(self, index_id: int, price_data: List[Dict]) -> int:
        """保存指数价格数据"""
        try:
            count = 0
            with self.db_manager.get_session() as session:
                from .models import MarketIndexPrice
                
                for data in price_data:
                    # 检查记录是否已存在
                    existing_record = session.query(MarketIndexPrice).filter(
                        MarketIndexPrice.index_id == index_id,
                        MarketIndexPrice.trade_date == data['trade_date']
                    ).first()
                    
                    if existing_record:
                        # 更新现有记录
                        existing_record.open_price = data['open_price']
                        existing_record.high_price = data['high_price']
                        existing_record.low_price = data['low_price']
                        existing_record.close_price = data['close_price']
                        existing_record.preclose_price = data['preclose_price']
                        existing_record.volume = data['volume']
                        existing_record.amount = data['amount']
                        existing_record.pct_chg = data['pct_chg']
                    else:
                        # 创建新记录
                        new_record = MarketIndexPrice(
                            index_id=index_id,
                            trade_date=data['trade_date'],
                            open_price=data['open_price'],
                            high_price=data['high_price'],
                            low_price=data['low_price'],
                            close_price=data['close_price'],
                            preclose_price=data['preclose_price'],
                            volume=data['volume'],
                            amount=data['amount'],
                            pct_chg=data['pct_chg']
                        )
                        session.add(new_record)
                    
                    count += 1
                    
                    # 每1000条记录提交一次
                    if count % 1000 == 0:
                        session.commit()
                        logger.info(f"已保存 {count} 条指数价格数据")
                
                session.commit()
                logger.info(f"指数价格数据保存完成，共 {count} 条记录")
                return count
                
        except Exception as e:
            logger.error(f"保存指数价格数据失败: {e}")
            return 0


class ThsDataDAO:
    """同花顺数据访问对象"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_ths_hot_list(self, hot_list_data: List[Dict], market_type: str) -> int:
        """
        保存同花顺热榜数据
        :param hot_list_data: 热榜数据列表
        :param market_type: 热榜类型
        :return: 成功保存的记录数
        """
        if not hot_list_data:
            return 0
        
        from .models import ThsHotList
        
        try:
            with self.db_manager.get_session() as session:
                # 获取交易日期并删除旧数据
                trade_date = hot_list_data[0].get('trade_date')
                if trade_date:
                    session.query(ThsHotList).filter(
                        ThsHotList.trade_date == trade_date,
                        ThsHotList.market_type == market_type
                    ).delete(synchronize_session=False)

                # 准备新数据
                new_records = []
                for item in hot_list_data:
                    record = ThsHotList(
                        trade_date=item.get('trade_date'),
                        market_type=market_type,
                        ts_code=item.get('ts_code'),
                        ts_name=item.get('ts_name'),
                        rank=item.get('rank'),
                        pct_change=item.get('pct_change'),
                        current_price=item.get('current_price'),
                        concept=str(item.get('concept')), # Ensure concept is string
                        rank_reason=item.get('rank_reason'),
                        hot=item.get('hot'),
                        rank_time=item.get('rank_time')
                    )
                    new_records.append(record)
                
                # 批量插入
                session.bulk_save_objects(new_records)
                logger.info(f"成功保存 {len(new_records)} 条同花顺热榜数据 ({market_type})")
                return len(new_records)
        except Exception as e:
            logger.error(f"保存同花顺热榜数据失败: {e}")
            return 0

    def get_ths_hot_list(self, market_type: str, trade_date: str) -> List[Dict]:
        """
        获取指定日期和类型的同花顺热榜数据
        """
        try:
            with self.db_manager.get_session() as session:
                from .models import ThsHotList
                query = session.query(ThsHotList).filter(
                    ThsHotList.market_type == market_type,
                    ThsHotList.trade_date == trade_date
                ).order_by(ThsHotList.rank)
                
                results = query.all()
                return [{
                    'ts_code': r.ts_code,
                    'ts_name': r.ts_name,
                    'rank': r.rank,
                    'pct_change': r.pct_change,
                    'current_price': r.current_price,
                    'concept': r.concept,
                    'rank_reason': r.rank_reason,
                    'hot': r.hot,
                    'rank_time': r.rank_time,
                } for r in results]

        except Exception as e:
            logger.error(f"获取同花顺热榜数据失败: {e}")
            return []


# 全局数据库管理器实例
db_manager = DatabaseManager()
stock_dao = StockDataDAO(db_manager)
news_dao = NewsDataDAO(db_manager)
index_dao = MarketIndexDAO(db_manager)
ths_data_dao = ThsDataDAO(db_manager) 