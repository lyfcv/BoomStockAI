# 📈 平台突破选股策略使用指南

## 🎯 策略概述

平台突破选股策略是BoomStockAI系统的核心策略之一，专门用于识别股票在经历平台整理后的放量突破形态，捕捉可能进入主升浪的交易机会。

### ✨ 策略特点

- 🔍 **智能识别**: 自动识别平台整理形态
- 📊 **多维分析**: 结合价格、成交量、技术指标进行综合分析
- 🎯 **精准筛选**: 基于评分系统筛选高质量突破信号
- 📈 **实时监控**: 支持定时执行和实时监控
- 💾 **数据持久化**: 所有分析结果和交易信号自动保存

## 📋 策略逻辑

### 1️⃣ 平台整理识别

| 条件 | 说明 | 默认值 |
|------|------|--------|
| 区间振幅 | 最近N日最高价与最低价的振幅 ≤ 15% | 15% |
| 检测窗口 | 平台检测的时间窗口 | 20天 |
| 均线粘合 | 5日/10日/20日均线趋于靠拢（乖离率 < 3%） | 3% |
| 最小平台天数 | 横盘时间要求 | 15天 |

### 2️⃣ 突破信号确认

| 条件 | 说明 | 默认值 |
|------|------|--------|
| 价格突破 | 当前收盘价 > 平台上沿 | - |
| 成交量放大 | 当日成交量 > 平台期内平均成交量 × 2 | 2倍 |
| 实体阳线 | 当日涨幅 ≥ 3%，收盘价 > 开盘价 | 3% |
| K线形态 | 实体阳线，下影线不长 | - |

### 3️⃣ 趋势确认

| 指标 | 说明 | 权重 |
|------|------|------|
| 均线多头排列 | 5日线 > 10日线 > 20日线 | 20分 |
| RSI强势区 | RSI在60-80区间 | 10分 |
| KDJ金叉 | K > D 且 K > 70 | 10分 |
| 成交量确认 | 成交量显著放大 | 15分 |

## 🚀 使用方法

### 方法一：命令行执行

```bash
# 基本执行
python scripts/run_platform_breakout.py

# 指定股票池
python scripts/run_platform_breakout.py --stocks sh.600000 sz.000001 sz.300001

# 不保存结果（仅查看）
python scripts/run_platform_breakout.py --no-save

# 详细输出
python scripts/run_platform_breakout.py --verbose
```

### 方法二：Web界面

1. 启动Streamlit应用：
```bash
streamlit run frontend/main.py
```

2. 访问平台突破策略页面：
```
http://localhost:8501/platform_breakout
```

3. 在侧边栏配置策略参数并执行

### 方法三：Python代码调用

```python
from strategy_center.strategy_executor import run_platform_breakout_strategy

# 执行策略
result = run_platform_breakout_strategy()

# 查看结果
print(f"筛选出 {result['result']['qualified_stocks']} 只股票")
print(f"生成 {result['result']['trading_signals']} 个交易信号")

# 获取Top推荐
top_picks = result['result']['top_picks']
for pick in top_picks[:5]:
    stock_info = pick['stock_info']
    recommendation = pick['recommendation']
    print(f"{stock_info['name']} ({stock_info['code']}): {recommendation['score']:.0f}分")
```

### 方法四：定时执行

```python
from strategy_center.strategy_executor import strategy_executor

# 设置定时任务
strategy_executor.schedule_strategies()

# 运行调度器
strategy_executor.run_scheduler()
```

## ⚙️ 配置参数

### 核心参数

```yaml
# 平台检测参数
platform_window: 20          # 平台检测窗口期（天）
max_volatility: 0.15         # 最大波动率（15%）
min_platform_days: 15        # 最小平台天数

# 突破信号参数
volume_threshold: 2.0        # 成交量放大倍数
price_threshold: 0.03        # 价格涨幅阈值（3%）

# 过滤条件
min_price: 5.0               # 最低股价
max_price: 200.0             # 最高股价
exclude_st: true             # 排除ST股票
rsi_range: [30, 80]          # RSI范围
score_threshold: 60          # 最低评分阈值
```

### 自定义配置

```python
# 创建自定义配置
custom_config = {
    'platform_window': 25,
    'max_volatility': 0.12,
    'volume_threshold': 2.5,
    'score_threshold': 70
}

# 使用自定义配置
from strategy_center.strategies.platform_breakout_strategy import create_platform_breakout_strategy
strategy = create_platform_breakout_strategy(custom_config)
result = strategy.run_strategy()
```

## 📊 结果解读

### 评分系统

策略使用100分制评分系统：

- **80-100分**: 强烈买入 - 多个条件完美符合
- **60-79分**: 买入 - 主要条件符合
- **40-59分**: 关注 - 部分条件符合
- **0-39分**: 观望 - 条件不足

### 输出结果

```python
{
    'strategy_name': 'platform_breakout',
    'execution_time': 45.2,
    'qualified_stocks': 15,
    'trading_signals': 8,
    'top_picks': [
        {
            'stock_info': {'code': 'sh.600000', 'name': '浦发银行'},
            'latest_price': 12.50,
            'recommendation': {
                'action': '买入',
                'score': 75,
                'confidence': 0.82,
                'reasons': ['放量突破平台', '均线多头排列', 'RSI处于强势区间']
            },
            'platform_analysis': {
                'platform_high': 12.30,
                'platform_low': 11.80,
                'volatility': 0.12
            },
            'breakout_analysis': {
                'has_breakout': True,
                'breakout_strength': 85,
                'volume_ratio': 2.8
            }
        }
    ]
}
```

## 📈 实战建议

### 1. 最佳执行时间

- **盘前**: 9:00-9:25，分析前一日收盘数据
- **盘中**: 11:30、14:00，实时监控突破信号
- **盘后**: 15:30，复盘当日表现

### 2. 风险控制

```python
# 建议的风险控制参数
risk_params = {
    'max_position_size': 0.1,    # 单只股票最大仓位10%
    'stop_loss': 0.08,           # 止损8%
    'take_profit': 0.20,         # 止盈20%
    'max_daily_trades': 5        # 每日最大交易数
}
```

### 3. 组合使用

```python
# 与其他策略组合使用
from strategy_center.strategy_executor import run_all_strategies

# 执行所有策略
results = run_all_strategies()

# 综合分析结果
for strategy_name, result in results['results'].items():
    print(f"{strategy_name}: {result['result']['trading_signals']} 个信号")
```

## 🔧 故障排除

### 常见问题

1. **数据不足错误**
   ```
   解决方案：确保数据库中有足够的历史价格数据（至少60天）
   ```

2. **无符合条件股票**
   ```
   解决方案：降低score_threshold或调整其他过滤条件
   ```

3. **执行时间过长**
   ```
   解决方案：使用自定义股票池或增加过滤条件
   ```

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 单只股票测试
result = run_platform_breakout_strategy(stock_pool=['sh.600000'])
```

## 📚 扩展开发

### 添加自定义指标

```python
from strategy_center.models.technical_indicators import TechnicalIndicators

class CustomIndicators(TechnicalIndicators):
    @staticmethod
    def calculate_custom_indicator(df):
        # 自定义指标计算
        df['custom_signal'] = your_calculation(df)
        return df
```

### 自定义评分逻辑

```python
def custom_scoring(latest_data):
    score = 0
    reasons = []
    
    # 自定义评分逻辑
    if your_condition:
        score += 20
        reasons.append("自定义条件满足")
    
    return {'score': score, 'reasons': reasons}
```

## 📞 技术支持

如有问题，请通过以下方式获取支持：

- 📧 邮箱: support@boomstockai.com
- 💬 微信群: 扫码加入技术交流群
- 📖 文档: [https://docs.boomstockai.com](https://docs.boomstockai.com)
- 🐛 Bug报告: GitHub Issues

---

**⚠️ 风险提示**: 本策略仅供参考，不构成投资建议。股市有风险，投资需谨慎。 