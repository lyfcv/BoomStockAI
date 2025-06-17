"""
财经新闻爬虫模块
从各大财经网站获取股票相关新闻
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import yaml
import random
from urllib.parse import urljoin, urlparse
import jieba
import jieba.analyse

from database.db_utils import db_manager
from database.models import NewsArticle


class NewsCrawler:
    """新闻爬虫基类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化爬虫"""
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        })
        
        # 设置代理（如果需要）
        if self.config.get('proxy'):
            self.session.proxies.update(self.config['proxy'])
        
        # 初始化jieba分词
        jieba.load_userdict('data/stock_dict.txt')  # 加载股票词典
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('crawler', {})
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'request_delay': 1.0,
                'max_retries': 3,
                'timeout': 30
            }
    
    def _get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """获取网页内容"""
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url, 
                    timeout=self.config.get('timeout', 30)
                )
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
                
            except Exception as e:
                logger.warning(f"获取网页失败 (尝试 {attempt + 1}/{retries}): {url}, 错误: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(1, 3))
                else:
                    logger.error(f"获取网页最终失败: {url}")
                    return None
    
    def _extract_stock_codes(self, text: str) -> List[str]:
        """从文本中提取股票代码"""
        # 匹配股票代码模式
        patterns = [
            r'([036]\d{5})',  # 6位数字，3开头、0开头、6开头
            r'([0-9]{6})',    # 6位数字
            r'(\d{6}\.SH)',   # 上海股票代码
            r'(\d{6}\.SZ)',   # 深圳股票代码
        ]
        
        stock_codes = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 6 and match.isdigit():
                    stock_codes.add(match)
                elif '.' in match:
                    stock_codes.add(match)
        
        return list(stock_codes)
    
    def _extract_keywords(self, text: str, topk: int = 10) -> List[str]:
        """提取关键词"""
        try:
            keywords = jieba.analyse.extract_tags(text, topK=topk, withWeight=False)
            return keywords
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        
        return text.strip()
    
    def save_to_database(self, articles: List[Dict]) -> int:
        """保存新闻到数据库"""
        try:
            count = 0
            with db_manager.get_session() as session:
                for article in articles:
                    # 检查是否已存在
                    existing = session.query(NewsArticle).filter(
                        NewsArticle.url == article.get('url')
                    ).first()
                    
                    if not existing:
                        news_article = NewsArticle(
                            title=article.get('title', ''),
                            content=article.get('content', ''),
                            source=article.get('source', ''),
                            author=article.get('author', ''),
                            publish_time=article.get('publish_time'),
                            url=article.get('url', ''),
                            keywords=article.get('keywords', []),
                            stock_codes=article.get('stock_codes', [])
                        )
                        session.add(news_article)
                        count += 1
                        
                        if count % 50 == 0:
                            session.commit()
                            logger.info(f"已保存 {count} 条新闻")
            
            logger.info(f"新闻保存完成，共 {count} 条新闻")
            return count
            
        except Exception as e:
            logger.error(f"保存新闻失败: {e}")
            return 0


class EastMoneyCrawler(NewsCrawler):
    """东方财富新闻爬虫"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        super().__init__(config_path)
        self.base_url = "https://finance.eastmoney.com"
        self.news_api_url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
    
    def crawl_news_list(self, pages: int = 5) -> List[Dict]:
        """爬取新闻列表"""
        news_list = []
        
        try:
            for page in range(1, pages + 1):
                logger.info(f"爬取东方财富新闻第 {page} 页")
                
                # 构建API请求URL
                params = {
                    'sr': -1,
                    'page_size': 50,
                    'page_index': page,
                    'ann_type': 'A',
                    'client_source': 'web'
                }
                
                response = self.session.get(self.news_api_url, params=params)
                if response.status_code != 200:
                    logger.warning(f"获取新闻列表失败: {response.status_code}")
                    continue
                
                data = response.json()
                if 'data' not in data or 'list' not in data['data']:
                    logger.warning("返回数据格式异常")
                    continue
                
                for item in data['data']['list']:
                    try:
                        news_item = {
                            'title': item.get('title', ''),
                            'url': item.get('art_url', ''),
                            'publish_time': datetime.fromtimestamp(item.get('notice_date', 0) / 1000),
                            'source': '东方财富',
                            'stock_code': item.get('codes', []),
                            'content': ''
                        }
                        
                        # 获取详细内容
                        content = self._get_article_content(news_item['url'])
                        if content:
                            news_item['content'] = content
                            news_item['keywords'] = self._extract_keywords(content)
                            news_item['stock_codes'] = self._extract_stock_codes(content)
                            news_list.append(news_item)
                        
                        # 随机延时
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        logger.warning(f"处理新闻项失败: {e}")
                        continue
                
                # 页面间延时
                time.sleep(random.uniform(1, 2))
        
        except Exception as e:
            logger.error(f"爬取东方财富新闻失败: {e}")
        
        logger.info(f"东方财富新闻爬取完成，共 {len(news_list)} 条")
        return news_list
    
    def _get_article_content(self, url: str) -> Optional[str]:
        """获取文章详细内容"""
        try:
            soup = self._get_page(url)
            if not soup:
                return None
            
            # 尝试不同的内容选择器
            content_selectors = [
                '.news-content',
                '.content',
                '.article-content',
                '#content',
                '.txt-content'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text(strip=True)
                    return self._clean_text(content)
            
            return None
            
        except Exception as e:
            logger.warning(f"获取文章内容失败: {url}, 错误: {e}")
            return None


class SinaFinanceCrawler(NewsCrawler):
    """新浪财经新闻爬虫"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        super().__init__(config_path)
        self.base_url = "https://finance.sina.com.cn"
        self.news_urls = [
            "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=1686&k=&num=50&page=1",
            "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=1687&k=&num=50&page=1"
        ]
    
    def crawl_news_list(self, pages: int = 5) -> List[Dict]:
        """爬取新浪财经新闻列表"""
        news_list = []
        
        try:
            for api_url in self.news_urls:
                for page in range(1, pages + 1):
                    logger.info(f"爬取新浪财经新闻第 {page} 页")
                    
                    # 修改URL中的页码
                    current_url = api_url.replace('page=1', f'page={page}')
                    
                    response = self.session.get(current_url)
                    if response.status_code != 200:
                        continue
                    
                    data = response.json()
                    if 'result' not in data or 'data' not in data['result']:
                        continue
                    
                    for item in data['result']['data']:
                        try:
                            news_item = {
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'publish_time': datetime.fromtimestamp(int(item.get('ctime', 0))),
                                'source': '新浪财经',
                                'content': ''
                            }
                            
                            # 获取详细内容
                            content = self._get_article_content(news_item['url'])
                            if content:
                                news_item['content'] = content
                                news_item['keywords'] = self._extract_keywords(content)
                                news_item['stock_codes'] = self._extract_stock_codes(content)
                                news_list.append(news_item)
                            
                            time.sleep(random.uniform(0.5, 1.5))
                            
                        except Exception as e:
                            logger.warning(f"处理新闻项失败: {e}")
                            continue
                    
                    time.sleep(random.uniform(1, 2))
        
        except Exception as e:
            logger.error(f"爬取新浪财经新闻失败: {e}")
        
        logger.info(f"新浪财经新闻爬取完成，共 {len(news_list)} 条")
        return news_list
    
    def _get_article_content(self, url: str) -> Optional[str]:
        """获取文章内容"""
        try:
            soup = self._get_page(url)
            if not soup:
                return None
            
            # 新浪财经的内容选择器
            content_selectors = [
                '.article',
                '.content',
                '#artibody',
                '.art-content'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text(strip=True)
                    return self._clean_text(content)
            
            return None
            
        except Exception as e:
            logger.warning(f"获取文章内容失败: {url}, 错误: {e}")
            return None


class TencentFinanceCrawler(NewsCrawler):
    """腾讯财经新闻爬虫"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        super().__init__(config_path)
        self.base_url = "https://finance.qq.com"
        self.api_url = "https://r.inews.qq.com/getQQNewsUnreadList"
    
    def crawl_news_list(self, pages: int = 5) -> List[Dict]:
        """爬取腾讯财经新闻"""
        news_list = []
        
        try:
            for page in range(pages):
                logger.info(f"爬取腾讯财经新闻第 {page + 1} 页")
                
                params = {
                    'chlid': 'finance',
                    'page': page,
                    'num': 20
                }
                
                response = self.session.get(self.api_url, params=params)
                if response.status_code != 200:
                    continue
                
                data = response.json()
                if 'data' not in data:
                    continue
                
                for item in data['data']:
                    try:
                        news_item = {
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'publish_time': datetime.fromtimestamp(int(item.get('time', 0))),
                            'source': '腾讯财经',
                            'content': ''
                        }
                        
                        # 获取详细内容
                        content = self._get_article_content(news_item['url'])
                        if content:
                            news_item['content'] = content
                            news_item['keywords'] = self._extract_keywords(content)
                            news_item['stock_codes'] = self._extract_stock_codes(content)
                            news_list.append(news_item)
                        
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        logger.warning(f"处理新闻项失败: {e}")
                        continue
                
                time.sleep(random.uniform(1, 2))
        
        except Exception as e:
            logger.error(f"爬取腾讯财经新闻失败: {e}")
        
        logger.info(f"腾讯财经新闻爬取完成，共 {len(news_list)} 条")
        return news_list
    
    def _get_article_content(self, url: str) -> Optional[str]:
        """获取文章内容"""
        try:
            soup = self._get_page(url)
            if not soup:
                return None
            
            # 腾讯财经的内容选择器
            content_selectors = [
                '.content-article',
                '.qq_article',
                '#Cnt-Main-Article-QQ',
                '.article-content'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text(strip=True)
                    return self._clean_text(content)
            
            return None
            
        except Exception as e:
            logger.warning(f"获取文章内容失败: {url}, 错误: {e}")
            return None


class NewsManager:
    """新闻管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.crawlers = {
            '东方财富': EastMoneyCrawler(config_path),
            '新浪财经': SinaFinanceCrawler(config_path),
            '腾讯财经': TencentFinanceCrawler(config_path)
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('crawler', {})
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}
    
    def crawl_all_news(self, pages_per_source: int = 3) -> Dict:
        """爬取所有新闻源"""
        results = {
            'total_news': 0,
            'saved_news': 0,
            'source_stats': {}
        }
        
        for source_name, crawler in self.crawlers.items():
            try:
                logger.info(f"开始爬取 {source_name} 新闻")
                
                # 检查是否启用
                source_config = next(
                    (s for s in self.config.get('news_sources', []) if s['name'] == source_name),
                    None
                )
                
                if not source_config or not source_config.get('enabled', True):
                    logger.info(f"{source_name} 已禁用，跳过")
                    continue
                
                # 爬取新闻
                news_list = crawler.crawl_news_list(pages_per_source)
                
                # 保存到数据库
                saved_count = crawler.save_to_database(news_list)
                
                results['total_news'] += len(news_list)
                results['saved_news'] += saved_count
                results['source_stats'][source_name] = {
                    'crawled': len(news_list),
                    'saved': saved_count
                }
                
                logger.info(f"{source_name} 爬取完成: 爬取{len(news_list)}条，保存{saved_count}条")
                
            except Exception as e:
                logger.error(f"爬取 {source_name} 新闻失败: {e}")
                results['source_stats'][source_name] = {
                    'crawled': 0,
                    'saved': 0,
                    'error': str(e)
                }
        
        logger.info(f"全部新闻爬取完成: 总计爬取{results['total_news']}条，保存{results['saved_news']}条")
        return results
    
    def crawl_stock_related_news(self, stock_codes: List[str], pages_per_source: int = 5) -> Dict:
        """爬取特定股票相关新闻"""
        # 这里可以实现针对特定股票的新闻搜索
        # 暂时使用通用爬取方法，后续可以优化
        return self.crawl_all_news(pages_per_source)


# 创建全局新闻管理器实例
news_manager = NewsManager() 