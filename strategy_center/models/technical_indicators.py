"""
技术指标计算模块
包含平台突破策略所需的各种技术指标
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from loguru import logger


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame, periods: List[int] = [5, 10, 20, 30]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 包含价格数据的DataFrame
            periods: 移动平均周期列表
            
        Returns:
            添加了移动平均线的DataFrame
        """
        result_df = df.copy()
        
        for period in periods:
            result_df[f'ma_{period}'] = result_df['close_price'].rolling(window=period).mean()
        
        return result_df
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """
        计算布林带
        
        Args:
            df: 包含价格数据的DataFrame
            period: 计算周期
            std_dev: 标准差倍数
            
        Returns:
            添加了布林带的DataFrame
        """
        result_df = df.copy()
        
        # 中轨（移动平均线）
        result_df['bb_middle'] = result_df['close_price'].rolling(window=period).mean()
        
        # 标准差
        rolling_std = result_df['close_price'].rolling(window=period).std()
        
        # 上轨和下轨
        result_df['bb_upper'] = result_df['bb_middle'] + (rolling_std * std_dev)
        result_df['bb_lower'] = result_df['bb_middle'] - (rolling_std * std_dev)
        
        # 布林带宽度（用于判断收敛）
        result_df['bb_width'] = (result_df['bb_upper'] - result_df['bb_lower']) / result_df['bb_middle']
        
        return result_df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算RSI相对强弱指标
        
        Args:
            df: 包含价格数据的DataFrame
            period: 计算周期
            
        Returns:
            添加了RSI的DataFrame
        """
        result_df = df.copy()
        
        # 计算价格变化
        delta = result_df['close_price'].diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # 计算RSI
        rs = gain / loss
        result_df['rsi'] = 100 - (100 / (1 + rs))
        
        return result_df
    
    @staticmethod
    def calculate_kdj(df: pd.DataFrame, k_period: int = 9, d_period: int = 3, j_period: int = 3) -> pd.DataFrame:
        """
        计算KDJ指标
        
        Args:
            df: 包含价格数据的DataFrame
            k_period: K值计算周期
            d_period: D值平滑周期
            j_period: J值计算周期
            
        Returns:
            添加了KDJ的DataFrame
        """
        result_df = df.copy()
        
        # 计算最高价和最低价的滚动窗口
        low_min = result_df['low_price'].rolling(window=k_period).min()
        high_max = result_df['high_price'].rolling(window=k_period).max()
        
        # 计算RSV
        rsv = (result_df['close_price'] - low_min) / (high_max - low_min) * 100
        
        # 计算K值
        result_df['k'] = rsv.ewm(alpha=1/d_period).mean()
        
        # 计算D值
        result_df['d'] = result_df['k'].ewm(alpha=1/d_period).mean()
        
        # 计算J值
        result_df['j'] = 3 * result_df['k'] - 2 * result_df['d']
        
        return result_df
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """
        计算MACD指标
        
        Args:
            df: 包含价格数据的DataFrame
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            添加了MACD的DataFrame
        """
        result_df = df.copy()
        
        # 计算EMA
        ema_fast = result_df['close_price'].ewm(span=fast_period).mean()
        ema_slow = result_df['close_price'].ewm(span=slow_period).mean()
        
        # 计算MACD线
        result_df['macd'] = ema_fast - ema_slow
        
        # 计算信号线
        result_df['macd_signal'] = result_df['macd'].ewm(span=signal_period).mean()
        
        # 计算MACD柱状图
        result_df['macd_histogram'] = result_df['macd'] - result_df['macd_signal']
        
        return result_df
    
    @staticmethod
    def calculate_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算成交量相关指标
        
        Args:
            df: 包含价格和成交量数据的DataFrame
            
        Returns:
            添加了成交量指标的DataFrame
        """
        result_df = df.copy()
        
        # 成交量移动平均
        result_df['volume_ma_5'] = result_df['volume'].rolling(window=5).mean()
        result_df['volume_ma_10'] = result_df['volume'].rolling(window=10).mean()
        result_df['volume_ma_20'] = result_df['volume'].rolling(window=20).mean()
        
        # 量比（当日成交量/近期平均成交量）
        result_df['volume_ratio'] = result_df['volume'] / result_df['volume_ma_20']
        
        # 价量配合度（价格涨跌与成交量的关系）
        price_change = result_df['close_price'].pct_change()
        volume_change = result_df['volume'].pct_change()
        result_df['price_volume_correlation'] = price_change.rolling(window=10).corr(volume_change)
        
        return result_df
    
    @staticmethod
    def detect_platform_consolidation(df: pd.DataFrame, window: int = 20, max_volatility: float = 0.15) -> pd.DataFrame:
        """
        检测平台整理形态
        
        Args:
            df: 包含价格数据的DataFrame
            window: 检测窗口期
            max_volatility: 最大波动率阈值
            
        Returns:
            添加了平台检测结果的DataFrame
        """
        result_df = df.copy()
        
        # 计算滚动窗口内的最高价和最低价
        rolling_high = result_df['high_price'].rolling(window=window).max()
        rolling_low = result_df['low_price'].rolling(window=window).min()
        
        # 计算波动率
        volatility = (rolling_high - rolling_low) / rolling_low
        
        # 判断是否为平台整理
        result_df['is_platform'] = volatility <= max_volatility
        
        # 计算平台上沿和下沿
        result_df['platform_high'] = rolling_high
        result_df['platform_low'] = rolling_low
        result_df['platform_volatility'] = volatility
        
        # 计算均线乖离率（判断均线粘合）
        if 'ma_5' in result_df.columns and 'ma_10' in result_df.columns and 'ma_20' in result_df.columns:
            ma_5_deviation = abs(result_df['ma_5'] - result_df['ma_10']) / result_df['ma_10']
            ma_10_deviation = abs(result_df['ma_10'] - result_df['ma_20']) / result_df['ma_20']
            result_df['ma_convergence'] = (ma_5_deviation < 0.03) & (ma_10_deviation < 0.03)
        
        return result_df
    
    @staticmethod
    def detect_breakout_signals(df: pd.DataFrame, volume_threshold: float = 2.0, price_threshold: float = 0.03) -> pd.DataFrame:
        """
        检测突破信号
        
        Args:
            df: 包含价格、成交量和平台数据的DataFrame
            volume_threshold: 成交量放大倍数阈值
            price_threshold: 价格涨幅阈值
            
        Returns:
            添加了突破信号的DataFrame
        """
        result_df = df.copy()
        
        # 初始化信号列
        result_df['breakout_signal'] = False
        result_df['breakout_strength'] = 0.0
        
        # 检查必要的列是否存在
        required_columns = ['platform_high', 'volume_ratio', 'close_price', 'open_price']
        if not all(col in result_df.columns for col in required_columns):
            logger.warning("缺少必要的列进行突破检测")
            return result_df
        
        # 突破条件
        # 1. 收盘价突破平台上沿
        price_breakout = result_df['close_price'] > result_df['platform_high']
        
        # 2. 成交量放大
        volume_breakout = result_df['volume_ratio'] >= volume_threshold
        
        # 3. 实体阳线（涨幅超过阈值）
        daily_return = (result_df['close_price'] - result_df['open_price']) / result_df['open_price']
        strong_candle = daily_return >= price_threshold
        
        # 4. 收盘价高于开盘价（阳线）
        bullish_candle = result_df['close_price'] > result_df['open_price']
        
        # 综合判断突破信号
        result_df['breakout_signal'] = price_breakout & volume_breakout & strong_candle & bullish_candle
        
        # 计算突破强度（0-100分）
        strength_score = 0
        strength_score += np.where(price_breakout, 25, 0)  # 价格突破25分
        strength_score += np.where(volume_breakout, 25, 0)  # 成交量突破25分
        strength_score += np.where(strong_candle, 25, 0)    # 强势K线25分
        strength_score += np.where(daily_return >= 0.05, 25, np.where(daily_return >= price_threshold, 15, 0))  # 涨幅加分
        
        result_df['breakout_strength'] = strength_score
        
        return result_df
    
    @staticmethod
    def calculate_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算趋势确认指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了趋势指标的DataFrame
        """
        result_df = df.copy()
        
        # 均线多头排列检测
        if all(col in result_df.columns for col in ['ma_5', 'ma_10', 'ma_20']):
            result_df['bullish_alignment'] = (result_df['ma_5'] > result_df['ma_10']) & (result_df['ma_10'] > result_df['ma_20'])
        
        # 价格相对于均线的位置
        if 'ma_20' in result_df.columns:
            result_df['price_above_ma20'] = result_df['close_price'] > result_df['ma_20']
        
        # 趋势强度（基于价格动量）
        result_df['momentum_5'] = result_df['close_price'] / result_df['close_price'].shift(5) - 1
        result_df['momentum_10'] = result_df['close_price'] / result_df['close_price'].shift(10) - 1
        
        # 趋势一致性（多个周期动量方向一致）
        result_df['trend_consistency'] = (result_df['momentum_5'] > 0) & (result_df['momentum_10'] > 0)
        
        return result_df


class PlatformBreakoutAnalyzer:
    """平台突破分析器"""
    
    def __init__(self, window: int = 20, max_volatility: float = 0.15, volume_threshold: float = 2.0):
        """
        初始化分析器
        
        Args:
            window: 平台检测窗口期
            max_volatility: 最大波动率阈值
            volume_threshold: 成交量放大倍数阈值
        """
        self.window = window
        self.max_volatility = max_volatility
        self.volume_threshold = volume_threshold
        self.indicators = TechnicalIndicators()
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        完整的平台突破分析
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            分析结果字典
        """
        try:
            # 确保数据足够
            if len(df) < self.window + 10:
                return {
                    'success': False,
                    'message': f'数据不足，需要至少{self.window + 10}条记录',
                    'data': None
                }
            
            # 计算所有技术指标
            result_df = df.copy()
            result_df = self.indicators.calculate_moving_averages(result_df)
            result_df = self.indicators.calculate_bollinger_bands(result_df)
            result_df = self.indicators.calculate_rsi(result_df)
            result_df = self.indicators.calculate_kdj(result_df)
            result_df = self.indicators.calculate_macd(result_df)
            result_df = self.indicators.calculate_volume_indicators(result_df)
            result_df = self.indicators.detect_platform_consolidation(result_df, self.window, self.max_volatility)
            result_df = self.indicators.detect_breakout_signals(result_df, self.volume_threshold)
            result_df = self.indicators.calculate_trend_indicators(result_df)
            
            # 获取最新数据
            latest = result_df.iloc[-1]
            
            # 分析结果
            analysis_result = {
                'success': True,
                'timestamp': latest.get('trade_date', pd.Timestamp.now()),
                'platform_analysis': {
                    'is_platform': bool(latest.get('is_platform', False)),
                    'platform_high': float(latest.get('platform_high', 0)),
                    'platform_low': float(latest.get('platform_low', 0)),
                    'volatility': float(latest.get('platform_volatility', 0)),
                    'ma_convergence': bool(latest.get('ma_convergence', False))
                },
                'breakout_analysis': {
                    'has_breakout': bool(latest.get('breakout_signal', False)),
                    'breakout_strength': float(latest.get('breakout_strength', 0)),
                    'volume_ratio': float(latest.get('volume_ratio', 0)),
                    'price_change': float((latest.get('close_price', 0) - latest.get('open_price', 0)) / latest.get('open_price', 1))
                },
                'trend_analysis': {
                    'bullish_alignment': bool(latest.get('bullish_alignment', False)),
                    'price_above_ma20': bool(latest.get('price_above_ma20', False)),
                    'trend_consistency': bool(latest.get('trend_consistency', False)),
                    'rsi': float(latest.get('rsi', 50)),
                    'k_value': float(latest.get('k', 50)),
                    'd_value': float(latest.get('d', 50))
                },
                'recommendation': self._generate_recommendation(latest),
                'data': result_df
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"平台突破分析失败: {e}")
            return {
                'success': False,
                'message': f'分析失败: {str(e)}',
                'data': None
            }
    
    def _generate_recommendation(self, latest_data: pd.Series) -> Dict:
        """
        生成投资建议
        
        Args:
            latest_data: 最新数据
            
        Returns:
            投资建议字典
        """
        score = 0
        reasons = []
        
        # 平台突破得分
        if latest_data.get('breakout_signal', False):
            score += 40
            reasons.append(f"放量突破平台，突破强度: {latest_data.get('breakout_strength', 0):.0f}分")
        elif latest_data.get('is_platform', False):
            score += 20
            reasons.append("处于平台整理阶段，等待突破")
        
        # 趋势确认得分
        if latest_data.get('bullish_alignment', False):
            score += 20
            reasons.append("均线多头排列")
        
        if latest_data.get('trend_consistency', False):
            score += 15
            reasons.append("多周期趋势一致向上")
        
        # 技术指标得分
        rsi = latest_data.get('rsi', 50)
        if 60 <= rsi <= 80:
            score += 10
            reasons.append(f"RSI处于强势区间({rsi:.1f})")
        elif rsi > 80:
            score -= 10
            reasons.append(f"RSI过热({rsi:.1f})")
        
        k_value = latest_data.get('k', 50)
        d_value = latest_data.get('d', 50)
        if k_value > d_value and k_value > 70:
            score += 10
            reasons.append("KDJ金叉且处于强势区")
        
        # 成交量确认
        volume_ratio = latest_data.get('volume_ratio', 1)
        if volume_ratio >= 2:
            score += 15
            reasons.append(f"成交量显著放大({volume_ratio:.1f}倍)")
        
        # 生成建议
        if score >= 80:
            recommendation = "强烈买入"
            confidence = min(score / 100, 0.95)
        elif score >= 60:
            recommendation = "买入"
            confidence = min(score / 100, 0.85)
        elif score >= 40:
            recommendation = "关注"
            confidence = min(score / 100, 0.75)
        else:
            recommendation = "观望"
            confidence = max(score / 100, 0.3)
        
        return {
            'action': recommendation,
            'score': score,
            'confidence': confidence,
            'reasons': reasons
        } 