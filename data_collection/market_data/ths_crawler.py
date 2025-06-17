import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from loguru import logger
import random
import re

class ThsCrawler:
    """同花顺热榜数据爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://dq.10jqka.com.cn/',
        })
        
        # 热榜类型映射 - 使用更准确的参数
        self.market_type_mapping = {
            '热股': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'a', 'type': 'hour', 'list_type': 'normal'}},
            'ETF': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'a', 'type': 'hour', 'list_type': 'etf'}},
            '可转债': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'a', 'type': 'hour', 'list_type': 'cb'}},
            '行业板块': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'a', 'type': 'hour', 'list_type': 'industry'}},
            '概念板块': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'a', 'type': 'hour', 'list_type': 'concept'}},
            '期货': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'futures', 'type': 'hour', 'list_type': 'normal'}},
            '港股': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'hk', 'type': 'hour', 'list_type': 'normal'}},
            '热基': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'fund', 'type': 'hour', 'list_type': 'normal'}},
            '美股': {'url': 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock', 'params': {'stock_type': 'us', 'type': 'hour', 'list_type': 'normal'}},
        }
    
    def get_hot_list_from_web(self, market_type: str = '热股', limit: int = 100) -> List[Dict]:
        """
        从网页版获取热榜数据（备用方法）
        """
        try:
            # 使用网页版接口
            if market_type == '热股':
                url = 'https://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/1/ajax/1/'
            else:
                logger.warning(f"网页版暂不支持{market_type}类型")
                return []
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析HTML内容
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            processed_data = []
            current_time = datetime.now()
            trade_date = current_time.strftime('%Y%m%d')
            
            # 查找股票数据表格
            table = soup.find('table', class_='m-table')
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                
                for i, row in enumerate(rows[:limit]):
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 6:
                            stock_code = cells[1].get_text(strip=True)
                            stock_name = cells[2].get_text(strip=True)
                            current_price = cells[3].get_text(strip=True)
                            pct_change = cells[4].get_text(strip=True)
                            
                            processed_item = {
                                'trade_date': trade_date,
                                'market_type': market_type,
                                'ts_code': stock_code,
                                'ts_name': stock_name,
                                'rank': i + 1,
                                'pct_change': float(pct_change.replace('%', '')) if pct_change and pct_change != '--' else None,
                                'current_price': float(current_price) if current_price and current_price != '--' else None,
                                'concept': '',
                                'rank_reason': '网页版数据',
                                'hot': None,
                                'rank_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                            }
                            processed_data.append(processed_item)
                    except Exception as e:
                        logger.warning(f"处理第{i+1}行数据时出错: {e}")
                        continue
            
            logger.info(f"从网页版成功获取{market_type}热榜数据 {len(processed_data)} 条")
            return processed_data
            
        except Exception as e:
            logger.error(f"从网页版获取{market_type}热榜数据失败: {e}")
            return []
    
    def get_hot_list(self, market_type: str = '热股', limit: int = 100) -> List[Dict]:
        """
        获取同花顺热榜数据
        
        Args:
            market_type: 热榜类型 ('热股', 'ETF', '可转债', '行业板块', '概念板块', '期货', '港股', '热基', '美股')
            limit: 获取数量限制
            
        Returns:
            热榜数据列表
        """
        try:
            if market_type not in self.market_type_mapping:
                logger.error(f"不支持的热榜类型: {market_type}")
                return []
            
            mapping = self.market_type_mapping[market_type]
            
            logger.info(f"正在获取{market_type}热榜数据...")
            
            # 添加随机延时避免被限制
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(mapping['url'], params=mapping['params'], timeout=30)
            response.raise_for_status()
            
            # 尝试解析JSON数据
            try:
                data = response.json()
                
                # 添加调试信息（可选）
                # logger.debug(f"API返回数据结构: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                
                if data.get('status_code') != 0:
                    logger.warning(f"API返回错误: {data.get('status_msg', '未知错误')}，尝试使用备用方法")
                    return self.get_hot_list_from_web(market_type, limit)
                
                hot_list_data = data.get('data', {}).get('stock_list', [])
                
                # 如果没有stock_list，尝试其他可能的字段
                if not hot_list_data:
                    hot_list_data = data.get('data', {}).get('list', [])
                if not hot_list_data:
                    hot_list_data = data.get('data', [])
                if not hot_list_data and isinstance(data, list):
                    hot_list_data = data
                
                logger.debug(f"解析到的热榜数据条数: {len(hot_list_data)}")
                if hot_list_data:
                    logger.debug(f"第一条数据示例: {json.dumps(hot_list_data[0], ensure_ascii=False)}")
                
            except json.JSONDecodeError:
                logger.warning(f"JSON解析失败，尝试使用备用方法")
                return self.get_hot_list_from_web(market_type, limit)
            
            # 处理数据格式
            processed_data = []
            current_time = datetime.now()
            trade_date = current_time.strftime('%Y%m%d')
            
            for i, item in enumerate(hot_list_data[:limit]):
                try:
                    # 根据实际API返回的字段名进行映射
                    stock_code = item.get('code', '')
                    stock_name = item.get('name', '')
                    change_rate = item.get('rise_and_fall', 0)  # 涨跌幅
                    hot_value = item.get('rate', 0)  # 热度值
                    
                    # 处理概念标签
                    concept_list = []
                    tag_info = item.get('tag', {})
                    if tag_info:
                        concept_tags = tag_info.get('concept_tag', [])
                        popularity_tag = tag_info.get('popularity_tag', '')
                        if concept_tags:
                            concept_list.extend(concept_tags)
                        if popularity_tag:
                            concept_list.append(popularity_tag)
                    
                    processed_item = {
                        'trade_date': trade_date,
                        'market_type': market_type,
                        'ts_code': stock_code,
                        'ts_name': stock_name,
                        'rank': i + 1,
                        'pct_change': float(change_rate) if change_rate else None,
                        'current_price': None,  # API中没有当前价格字段
                        'concept': json.dumps(concept_list, ensure_ascii=False) if concept_list else '',
                        'rank_reason': tag_info.get('popularity_tag', '') if tag_info else '',
                        'hot': float(hot_value) if hot_value else None,
                        'rank_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    processed_data.append(processed_item)
                except Exception as e:
                    logger.warning(f"处理第{i+1}条数据时出错: {e}")
                    continue
            
            logger.info(f"成功获取{market_type}热榜数据 {len(processed_data)} 条")
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            # 尝试备用方法
            return self.get_hot_list_from_web(market_type, limit)
        except Exception as e:
            logger.error(f"获取{market_type}热榜数据失败: {e}")
            return []
    
    def get_all_hot_lists(self, limit: int = 50) -> Dict[str, List[Dict]]:
        """
        获取所有类型的热榜数据
        
        Args:
            limit: 每个榜单的数量限制
            
        Returns:
            所有热榜数据的字典
        """
        all_data = {}
        
        # 优先获取热股数据，其他类型可能需要不同的接口
        priority_types = ['热股']
        other_types = [t for t in self.market_type_mapping.keys() if t not in priority_types]
        
        for market_type in priority_types + other_types:
            try:
                data = self.get_hot_list(market_type, limit)
                all_data[market_type] = data
                
                # 添加延时避免请求过快
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"获取{market_type}数据失败: {e}")
                all_data[market_type] = []
        
        return all_data
    
    def get_stock_hot_detail(self, stock_code: str) -> Dict:
        """
        获取个股热度详情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            个股热度详情
        """
        try:
            url = f"https://eq.10jqka.com.cn/earlyInterpret/index.php"
            params = {
                'con': 'index',
                'act': 'getIndexData',
                'stockCode': stock_code,
                'date': datetime.now().strftime('%Y%m%d')
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                stock_info = data.get('data', {}).get('stockInfo', {})
                return {
                    'stock_code': stock_code,
                    'price': stock_info.get('price'),
                    'hot_rank': stock_info.get('hotRank'),
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                logger.warning(f"获取股票{stock_code}热度详情失败: {data.get('msg', '未知错误')}")
                return {}
                
        except Exception as e:
            logger.error(f"获取股票{stock_code}热度详情失败: {e}")
            return {}

# 创建全局实例
ths_crawler = ThsCrawler()

if __name__ == "__main__":
    # 测试代码
    crawler = ThsCrawler()
    
    # 测试获取热股榜单
    hot_stocks = crawler.get_hot_list('热股', 20)
    print(f"热股榜单数据: {len(hot_stocks)} 条")
    if hot_stocks:
        print("前3条数据:")
        for i, stock in enumerate(hot_stocks[:3]):
            print(f"{i+1}. {stock['ts_name']} ({stock['ts_code']}) - 涨跌幅: {stock['pct_change']}%")
    
    # 只测试热股，避免其他类型的错误
    print("\n只获取热股数据...")
    hot_data = {'热股': crawler.get_hot_list('热股', 10)}
    for market_type, data in hot_data.items():
        print(f"{market_type}: {len(data)} 条数据") 