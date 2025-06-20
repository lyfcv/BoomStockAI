"""
BaoStock数据获取API
用于获取股票基础数据、价格数据等
"""
import baostock as bs
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import time
import yaml
import os

from database.db_utils import db_manager, stock_dao
from database.models import Stock, StockPrice


class BaoStockAPI:
    """BaoStock数据API封装类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化BaoStock API"""
        self.config = self._load_config(config_path)
        self.is_logged_in = False
        self._login()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('data_sources', {}).get('baostock', {})
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {'enabled': True, 'retry_times': 3, 'timeout': 30}
    
    def _login(self):
        """登录BaoStock"""
        try:
            lg = bs.login()
            if lg.error_code == '0':
                self.is_logged_in = True
                logger.info("BaoStock登录成功")
            else:
                logger.error(f"BaoStock登录失败: {lg.error_msg}")
                raise Exception(f"BaoStock登录失败: {lg.error_msg}")
        except Exception as e:
            logger.error(f"BaoStock登录异常: {e}")
            raise
    
    def logout(self):
        """登出BaoStock"""
        if self.is_logged_in:
            bs.logout()
            self.is_logged_in = False
            logger.info("BaoStock登出成功")
    
    def __del__(self):
        """析构函数，确保登出"""
        try:
            self.logout()
        except:
            pass
    
    def get_stock_basic_info(self, date: str = None) -> List[Dict]:
        """
        获取股票基本信息
        
        Args:
            date: 查询日期，格式为YYYY-MM-DD，默认为None(查询最新数据)
            
        Returns:
            股票基本信息列表
        """
        if not self.is_logged_in:
            self._login()
        
        try:
            logger.info(f"开始获取股票基本信息，日期: {date or '最新交易日'}")
            
            # 获取沪深A股列表
            rs = bs.query_all_stock(day=date)
            
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                stock_info = {
                    'code': row[0],
                    'name': row[1],
                    'market': 'SH' if row[0].startswith('sh') else 'SZ',
                    'industry': row[2] if len(row) > 2 else None,
                    'is_active': True
                }
                stock_list.append(stock_info)
            
            logger.info(f"获取股票基本信息成功，共{len(stock_list)}只股票")
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            return []
    
    def get_stock_history_data(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        frequency: str = "d",
        adjustflag: str = "3"
    ) -> List[Dict]:
        """
        获取股票历史数据
        
        Args:
            code: 股票代码，如sh.600000
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            frequency: 数据频率，d=日k线，w=周，m=月，5=5分钟，15=15分钟，30=30分钟，60=60分钟
            adjustflag: 复权类型，1=后复权，2=前复权，3=不复权
            
        Returns:
            股票历史数据列表
        """
        if not self.is_logged_in:
            self._login()
        
        try:
            logger.info(f"开始获取股票历史数据: {code}, {start_date} - {end_date}")
            
            # 确保代码格式正确
            if not code.startswith(('sh.', 'sz.')):
                if code.startswith('6'):
                    code = f'sh.{code}'
                else:
                    code = f'sz.{code}'
            
            rs = bs.query_history_k_data_plus(
                code, 
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=start_date, 
                end_date=end_date,
                frequency=frequency, 
                adjustflag=adjustflag
            )
            
            if rs.error_code != '0':
                logger.error(f"查询历史数据失败: {rs.error_msg}")
                return []
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                if row[0] and row[0] != '':  # 确保日期不为空
                    try:
                        # 根据官方文档，字段顺序为：
                        # date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST
                        data_dict = {
                            'trade_date': datetime.strptime(row[0], '%Y-%m-%d'),  # 0: date
                            'code': row[1],  # 1: code
                            'open_price': float(row[2]) if row[2] and row[2] != '' else None,  # 2: open
                            'high_price': float(row[3]) if row[3] and row[3] != '' else None,  # 3: high
                            'low_price': float(row[4]) if row[4] and row[4] != '' else None,  # 4: low
                            'close_price': float(row[5]) if row[5] and row[5] != '' else None,  # 5: close
                            'preclose_price': float(row[6]) if row[6] and row[6] != '' else None,  # 6: preclose
                            'volume': int(float(row[7])) if row[7] and row[7] != '' else None,  # 7: volume
                            'amount': float(row[8]) if row[8] and row[8] != '' else None,  # 8: amount
                            'turnover_rate': float(row[10]) if row[10] and row[10] != '' else None,  # 10: turn
                            'trade_status': int(row[11]) if row[11] and row[11] != '' else None,  # 11: tradestatus
                            'pct_chg': float(row[12]) if row[12] and row[12] != '' else None,  # 12: pctChg
                            'pe_ratio': float(row[13]) if row[13] and row[13] != '' else None,  # 13: peTTM
                            'pb_ratio': float(row[14]) if row[14] and row[14] != '' else None,  # 14: pbMRQ
                            'ps_ratio': float(row[15]) if row[15] and row[15] != '' else None,  # 15: psTTM
                            'pcf_ratio': float(row[16]) if row[16] and row[16] != '' else None,  # 16: pcfNcfTTM
                            'is_st': row[17] == '1' if len(row) > 17 and row[17] else False  # 17: isST
                        }
                        data_list.append(data_dict)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"数据转换错误: {row}, 错误: {e}")
                        continue
            
            logger.info(f"获取股票历史数据成功: {code}, 共{len(data_list)}条记录")
            return data_list
            
        except Exception as e:
            logger.error(f"获取股票历史数据失败 {code}: {e}")
            return []
    
    def get_industry_data(self, date: str = None) -> List[Dict]:
        """
        获取行业分类数据
        
        Args:
            date: 查询日期，格式为YYYY-MM-DD
            
        Returns:
            行业分类数据列表
        """
        if not self.is_logged_in:
            self._login()
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            logger.info(f"开始获取行业分类数据，日期: {date}")
            
            rs = bs.query_stock_industry()
            
            industry_list = []
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                industry_info = {
                    'code': row[0],
                    'code_name': row[1],
                    'industry': row[2],
                    'industry_classification': row[3]
                }
                industry_list.append(industry_info)
            
            logger.info(f"获取行业分类数据成功，共{len(industry_list)}条记录")
            return industry_list
            
        except Exception as e:
            logger.error(f"获取行业分类数据失败: {e}")
            return []
    
    def get_profit_data(self, code: str, year: int, quarter: int) -> Dict:
        """
        获取季频盈利能力数据
        
        Args:
            code: 股票代码
            year: 年份
            quarter: 季度(1,2,3,4)
            
        Returns:
            盈利能力数据字典
        """
        if not self.is_logged_in:
            self._login()
        
        try:
            # 确保代码格式正确
            if not code.startswith(('sh.', 'sz.')):
                if code.startswith('6'):
                    code = f'sh.{code}'
                else:
                    code = f'sz.{code}'
            
            rs = bs.query_profit_data(code=code, year=year, quarter=quarter)
            
            if rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                return {
                    'code': row[0],
                    'pub_date': row[1],
                    'stat_date': row[2],
                    'roe': float(row[3]) if row[3] else None,  # 净资产收益率
                    'roa': float(row[4]) if row[4] else None,  # 总资产收益率
                    'gross_profit_margin': float(row[5]) if row[5] else None,  # 销售毛利率
                    'net_profit_margin': float(row[6]) if row[6] else None,  # 销售净利率
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"获取盈利能力数据失败 {code}: {e}")
            return {}
    
    def save_stock_basic_to_db(self, stock_list: List[Dict]) -> int:
        """
        将股票基本信息保存到数据库
        
        Args:
            stock_list: 股票信息列表
            
        Returns:
            保存成功的股票数量
        """
        try:
            count = 0
            with db_manager.get_session() as session:
                for stock_info in stock_list:
                    # 检查股票是否已存在
                    existing_stock = session.query(Stock).filter(
                        Stock.code == stock_info['code']
                    ).first()
                    
                    if existing_stock:
                        # 更新现有股票信息
                        existing_stock.name = stock_info['name']
                        existing_stock.market = stock_info['market']
                        existing_stock.industry = stock_info['industry']
                        existing_stock.is_active = stock_info['is_active']
                        existing_stock.updated_at = datetime.utcnow()
                    else:
                        # 创建新股票记录
                        new_stock = Stock(
                            code=stock_info['code'],
                            name=stock_info['name'],
                            market=stock_info['market'],
                            industry=stock_info['industry'],
                            is_active=stock_info['is_active']
                        )
                        session.add(new_stock)
                    
                    count += 1
                    
                    # 每100条记录提交一次
                    if count % 100 == 0:
                        session.commit()
                        logger.info(f"已保存 {count} 只股票信息")
            
            logger.info(f"股票基本信息保存完成，共 {count} 只股票")
            return count
            
        except Exception as e:
            logger.error(f"保存股票基本信息失败: {e}")
            return 0
    
    def save_price_data_to_db(self, stock_id: int, price_data: List[Dict]) -> int:
        """
        将价格数据保存到数据库
        
        Args:
            stock_id: 股票ID
            price_data: 价格数据列表
            
        Returns:
            保存成功的记录数
        """
        try:
            count = 0
            with db_manager.get_session() as session:
                for data in price_data:
                    # 检查记录是否已存在
                    existing_record = session.query(StockPrice).filter(
                        StockPrice.stock_id == stock_id,
                        StockPrice.trade_date == data['trade_date']
                    ).first()
                    
                    if existing_record:
                        # 更新现有记录
                        existing_record.open_price = data['open_price']
                        existing_record.high_price = data['high_price']
                        existing_record.low_price = data['low_price']
                        existing_record.close_price = data['close_price']
                        existing_record.volume = data['volume']
                        existing_record.amount = data['amount']
                        existing_record.turnover_rate = data['turnover_rate']
                        existing_record.pe_ratio = data['pe_ratio']
                        existing_record.pb_ratio = data['pb_ratio']
                        # 注意：其他字段如preclose_price, trade_status, pct_chg, ps_ratio, pcf_ratio, is_st
                        # 在当前数据库模型中不存在，如果需要可以后续添加到数据库模型中
                    else:
                        # 创建新记录
                        new_record = StockPrice(
                            stock_id=stock_id,
                            trade_date=data['trade_date'],
                            open_price=data['open_price'],
                            high_price=data['high_price'],
                            low_price=data['low_price'],
                            close_price=data['close_price'],
                            volume=data['volume'],
                            amount=data['amount'],
                            turnover_rate=data['turnover_rate'],
                            pe_ratio=data['pe_ratio'],
                            pb_ratio=data['pb_ratio']
                        )
                        session.add(new_record)
                    
                    count += 1
                    
                    # 每1000条记录提交一次
                    if count % 1000 == 0:
                        session.commit()
                        logger.info(f"已保存 {count} 条价格数据")
            
            logger.info(f"价格数据保存完成，共 {count} 条记录")
            return count
            
        except Exception as e:
            logger.error(f"保存价格数据失败: {e}")
            return 0
    
    def batch_update_stock_data(self, codes: List[str], days: int = 30) -> Dict:
        """
        批量更新股票数据
        
        Args:
            codes: 股票代码列表
            days: 更新最近多少天的数据
            
        Returns:
            更新结果统计
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'total_records': 0,
            'failed_codes': []
        }
        
        for code in codes:
            try:
                # 获取股票ID
                stock_info = stock_dao.get_stock_by_code(code)
                if not stock_info:
                    logger.warning(f"股票代码不存在: {code}")
                    results['failed_count'] += 1
                    results['failed_codes'].append(code)
                    continue
                
                # 获取价格数据
                price_data = self.get_stock_history_data(code, start_date, end_date)
                if not price_data:
                    logger.warning(f"未获取到价格数据: {code}")
                    results['failed_count'] += 1
                    results['failed_codes'].append(code)
                    continue
                
                # 保存到数据库
                saved_count = self.save_price_data_to_db(stock_info['id'], price_data)
                results['success_count'] += 1
                results['total_records'] += saved_count
                
                # 避免请求过于频繁
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"更新股票数据失败 {code}: {e}")
                results['failed_count'] += 1
                results['failed_codes'].append(code)
        
        logger.info(f"批量更新完成: 成功{results['success_count']}只，失败{results['failed_count']}只")
        return results
    
    def get_index_data(self, index_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取指数数据
        
        Args:
            index_code: 指数代码，如sh.000001（上证指数）
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            
        Returns:
            指数数据列表
        """
        if not self.is_logged_in:
            self._login()
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            logger.info(f"开始获取指数数据: {index_code}, {start_date} - {end_date}")
            
            rs = bs.query_history_k_data_plus(
                index_code,
                "date,code,open,high,low,close,preclose,volume,amount,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"
            )
            
            if rs.error_code != '0':
                logger.error(f"查询指数数据失败: {rs.error_msg}")
                return []
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                if row[0] and row[0] != '':
                    try:
                        # 指数数据字段顺序：date,code,open,high,low,close,preclose,volume,amount,pctChg
                        data_dict = {
                            'trade_date': datetime.strptime(row[0], '%Y-%m-%d'),  # 0: date
                            'code': row[1],  # 1: code
                            'open_price': float(row[2]) if row[2] and row[2] != '' else None,  # 2: open
                            'high_price': float(row[3]) if row[3] and row[3] != '' else None,  # 3: high
                            'low_price': float(row[4]) if row[4] and row[4] != '' else None,  # 4: low
                            'close_price': float(row[5]) if row[5] and row[5] != '' else None,  # 5: close
                            'preclose_price': float(row[6]) if row[6] and row[6] != '' else None,  # 6: preclose
                            'volume': int(float(row[7])) if row[7] and row[7] != '' and row[7] != '0' else None,  # 7: volume
                            'amount': float(row[8]) if row[8] and row[8] != '' else None,  # 8: amount
                            'pct_chg': float(row[9]) if row[9] and row[9] != '' else None  # 9: pctChg
                        }
                        data_list.append(data_dict)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"指数数据转换错误: {row}, 错误: {e}")
                        continue
            
            logger.info(f"获取指数数据成功: {index_code}, 共{len(data_list)}条记录")
            return data_list
            
        except Exception as e:
            logger.error(f"获取指数数据失败 {index_code}: {e}")
            return []
    
    def get_latest_index_info(self, index_codes: List[str]) -> Dict[str, Dict]:
        """
        获取最新指数信息
        
        Args:
            index_codes: 指数代码列表
            
        Returns:
            指数信息字典
        """
        result = {}
        
        for code in index_codes:
            try:
                # 获取最近5天的数据用于计算涨跌
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
                data = self.get_index_data(code, start_date, end_date)
                if len(data) >= 2:
                    latest = data[-1]  # 最新数据
                    previous = data[-2] if len(data) > 1 else latest  # 前一日数据
                    
                    # 计算涨跌
                    current_price = latest['close_price']
                    previous_price = previous['close_price']
                    change = current_price - previous_price
                    change_pct = (change / previous_price) * 100 if previous_price else 0
                    
                    result[code] = {
                        'current_price': current_price,
                        'change': change,
                        'change_pct': change_pct,
                        'date': latest['trade_date']
                    }
                else:
                    logger.warning(f"指数数据不足: {code}")
                    
            except Exception as e:
                logger.error(f"获取指数信息失败 {code}: {e}")
        
        return result
    
    def save_index_basic_to_db(self, index_list: List[Dict]) -> int:
        """
        将指数基本信息保存到数据库
        
        Args:
            index_list: 指数信息列表
            
        Returns:
            保存成功的指数数量
        """
        try:
            from database.db_utils import index_dao
            return index_dao.save_index_basic_info(index_list)
        except Exception as e:
            logger.error(f"保存指数基本信息失败: {e}")
            return 0
    
    def save_index_price_to_db(self, index_id: int, price_data: List[Dict]) -> int:
        """
        将指数价格数据保存到数据库
        
        Args:
            index_id: 指数ID
            price_data: 价格数据列表
            
        Returns:
            保存成功的记录数
        """
        try:
            from database.db_utils import index_dao
            return index_dao.save_index_price_data(index_id, price_data)
        except Exception as e:
            logger.error(f"保存指数价格数据失败: {e}")
            return 0
    
    def batch_update_index_data(self, index_codes: List[str], days: int = 30) -> Dict:
        """
        批量更新指数数据
        
        Args:
            index_codes: 指数代码列表
            days: 更新最近多少天的数据
            
        Returns:
            更新结果统计
        """
        from database.db_utils import index_dao
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'total_records': 0,
            'failed_codes': []
        }
        
        # 指数名称映射
        index_names = {
            'sh.000001': '上证指数',
            'sz.399001': '深证成指',
            'sz.399006': '创业板指',
            'sh.000688': '科创50'
        }
        
        for code in index_codes:
            try:
                # 确保指数基本信息存在
                index_info = index_dao.get_index_by_code(code)
                if not index_info:
                    # 创建指数基本信息
                    name = index_names.get(code, code)
                    market = 'SH' if code.startswith('sh.') else 'SZ'
                    new_index = [{
                        'code': code,
                        'name': name,
                        'market': market,
                        'category': '综合指数',
                        'is_active': True
                    }]
                    index_dao.save_index_basic_info(new_index)
                    index_info = index_dao.get_index_by_code(code)
                    
                    if not index_info:
                        logger.error(f"创建指数信息失败: {code}")
                        results['failed_count'] += 1
                        results['failed_codes'].append(code)
                        continue
                
                # 获取价格数据
                price_data = self.get_index_data(code, start_date, end_date)
                if not price_data:
                    logger.warning(f"未获取到指数价格数据: {code}")
                    results['failed_count'] += 1
                    results['failed_codes'].append(code)
                    continue
                
                # 保存到数据库
                saved_count = self.save_index_price_to_db(index_info['id'], price_data)
                results['success_count'] += 1
                results['total_records'] += saved_count
                
                # 避免请求过于频繁
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"更新指数数据失败 {code}: {e}")
                results['failed_count'] += 1
                results['failed_codes'].append(code)
        
        logger.info(f"批量更新指数数据完成: 成功{results['success_count']}个，失败{results['failed_count']}个")
        return results


# 创建全局实例
baostock_api = BaoStockAPI()

def test_baostock_api():
    """
    测试BaoStock API功能
    """
    try:
        # 测试获取股票历史数据
        print("测试获取股票历史数据...")
        test_code = "sh.600000"  # 浦发银行
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        stock_data = baostock_api.get_stock_history_data(test_code, start_date, end_date)
        if stock_data:
            print(f"✓ 成功获取股票数据: {len(stock_data)} 条记录")
            print(f"  示例数据: {stock_data[0] if stock_data else 'None'}")
        else:
            print("✗ 获取股票数据失败")
        
        # 测试获取指数数据
        print("\n测试获取指数数据...")
        index_data = baostock_api.get_index_data("sh.000001", start_date, end_date)
        if index_data:
            print(f"✓ 成功获取指数数据: {len(index_data)} 条记录")
            print(f"  示例数据: {index_data[0] if index_data else 'None'}")
        else:
            print("✗ 获取指数数据失败")
        
        # 测试获取股票基本信息
        print("\n测试获取股票基本信息...")
        basic_info = baostock_api.get_stock_basic_info()
        if basic_info:
            print(f"✓ 成功获取股票基本信息: {len(basic_info)} 只股票")
            print(f"  示例数据: {basic_info[0] if basic_info else 'None'}")
        else:
            print("✗ 获取股票基本信息失败")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        baostock_api.logout()

if __name__ == "__main__":
    test_baostock_api()
