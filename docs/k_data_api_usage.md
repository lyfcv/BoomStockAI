# K线数据获取API使用文档

## 📖 概述

本模块提供了获取股票K线数据的API接口，支持多种频率的数据获取，包括日线、分钟线、周线、月线等。基于baostock数据源，保持原始数据格式输出。

## 🚀 快速开始

### 安装依赖

```bash
pip install baostock pandas
```

### 基本使用

```python
from data_collection.market_data.history_k_data import get_k_data

# 获取浦发银行最近20个交易日的数据
data = get_k_data('sh.600000', 20)
print(data.head())
```

## 📋 API参考

### 主要函数：get_k_data()

```python
def get_k_data(stock_code: str, count: int, frequency: str = "d", include_valuation: bool = True) -> Optional[pd.DataFrame]
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `stock_code` | str | - | 股票代码，格式：'sh.600000'（上海）或 'sz.000001'（深圳） |
| `count` | int | - | 需要获取的K线数据条数 |
| `frequency` | str | "d" | 数据频率类型，支持："d"、"w"、"m"、"5"、"15"、"30"、"60" |
| `include_valuation` | bool | True | 是否包含估值指标（仅日线支持） |

#### 频率类型说明

| 频率代码 | 说明 | 支持估值指标 |
|----------|------|--------------|
| "d" | 日K线 | ✅ |
| "w" | 周K线 | ❌ |
| "m" | 月K线 | ❌ |
| "5" | 5分钟K线 | ❌ |
| "15" | 15分钟K线 | ❌ |
| "30" | 30分钟K线 | ❌ |
| "60" | 60分钟K线 | ❌ |

#### 返回值

- **成功**: 返回 `pandas.DataFrame`，包含K线数据（原始字符串格式）
- **失败**: 返回 `None`

### 兼容函数：get_daily_k_data()

```python
def get_daily_k_data(stock_code: str, trading_days: int, include_valuation: bool = True) -> Optional[pd.DataFrame]
```

专门用于获取日线数据的简化接口，内部调用 `get_k_data(stock_code, trading_days, "d", include_valuation)`。

## 📊 数据字段说明

### 日线数据字段

| 字段名 | 说明 | 格式 |
|--------|------|------|
| date | 交易所行情日期 | YYYY-MM-DD |
| code | 证券代码 | sh.600000 |
| open | 今开盘价格 | 字符串，精度4位小数 |
| high | 最高价 | 字符串，精度4位小数 |
| low | 最低价 | 字符串，精度4位小数 |
| close | 今收盘价 | 字符串，精度4位小数 |
| preclose | 昨日收盘价 | 字符串，精度4位小数 |
| volume | 成交数量 | 字符串，单位：股 |
| amount | 成交金额 | 字符串，精度4位小数，单位：元 |
| adjustflag | 复权状态 | 字符串 |
| turn | 换手率 | 字符串，精度6位小数，单位：% |
| tradestatus | 交易状态 | 1：正常交易，0：停牌 |
| pctChg | 涨跌幅 | 字符串，精度6位小数，单位：% |
| isST | 是否ST | 1：是，0：否 |

### 估值指标字段（仅日线）

| 字段名 | 说明 | 格式 |
|--------|------|------|
| peTTM | 滚动市盈率 | 字符串，精度6位小数 |
| psTTM | 滚动市销率 | 字符串，精度6位小数 |
| pcfNcfTTM | 滚动市现率 | 字符串，精度6位小数 |
| pbMRQ | 市净率 | 字符串，精度6位小数 |

### 分钟线数据字段

| 字段名 | 说明 | 格式 |
|--------|------|------|
| date | 日期 | YYYY-MM-DD |
| time | 时间 | HHMMSS000 |
| code | 证券代码 | sh.600000 |
| open | 开盘价 | 字符串 |
| high | 最高价 | 字符串 |
| low | 最低价 | 字符串 |
| close | 收盘价 | 字符串 |
| volume | 成交数量 | 字符串 |
| amount | 成交金额 | 字符串 |
| adjustflag | 复权状态 | 字符串 |

### 周月线数据字段

| 字段名 | 说明 | 格式 |
|--------|------|------|
| date | 日期 | YYYY-MM-DD |
| code | 证券代码 | sh.600000 |
| open | 开盘价 | 字符串 |
| high | 最高价 | 字符串 |
| low | 最低价 | 字符串 |
| close | 收盘价 | 字符串 |
| volume | 成交数量 | 字符串 |
| amount | 成交金额 | 字符串 |
| adjustflag | 复权状态 | 字符串 |
| turn | 换手率 | 字符串 |
| pctChg | 涨跌幅 | 字符串 |

## 💡 使用示例

### 1. 获取日线数据

```python
from data_collection.market_data.history_k_data import get_k_data

# 获取浦发银行最近20个交易日数据（包含估值指标）
data = get_k_data('sh.600000', 20, 'd', include_valuation=True)
print(f"获取到 {len(data)} 条日线数据")
print(f"数据字段: {list(data.columns)}")
print(data.head())

# 获取日线数据（不含估值指标）
data_basic = get_k_data('sh.600000', 20, 'd', include_valuation=False)
```

### 2. 获取分钟线数据

```python
# 获取5分钟线数据
minute_5_data = get_k_data('sh.600000', 100, '5')
print(f"获取到 {len(minute_5_data)} 条5分钟线数据")

# 获取15分钟线数据
minute_15_data = get_k_data('sh.600000', 50, '15')

# 获取30分钟线数据
minute_30_data = get_k_data('sh.600000', 30, '30')

# 获取60分钟线数据
minute_60_data = get_k_data('sh.600000', 20, '60')
```

### 3. 获取周线和月线数据

```python
# 获取周线数据
weekly_data = get_k_data('sh.600000', 20, 'w')
print(f"获取到 {len(weekly_data)} 条周线数据")

# 获取月线数据
monthly_data = get_k_data('sh.600000', 12, 'm')
print(f"获取到 {len(monthly_data)} 条月线数据")
```

### 4. 使用兼容函数

```python
from data_collection.market_data.history_k_data import get_daily_k_data

# 专门获取日线数据的简化接口
daily_data = get_daily_k_data('sh.600000', 20, include_valuation=True)
```

### 5. 数据处理示例

```python
import pandas as pd

# 获取数据
data = get_k_data('sh.600000', 30, 'd')

if data is not None:
    # 转换数据类型（如需要）
    data['close'] = pd.to_numeric(data['close'])
    data['volume'] = pd.to_numeric(data['volume'])
    
    # 计算简单移动平均线
    data['ma5'] = data['close'].rolling(window=5).mean()
    
    # 保存到CSV文件
    data.to_csv('stock_data.csv', index=False)
    
    # 基本统计信息
    print(f"最高价: {data['high'].astype(float).max()}")
    print(f"最低价: {data['low'].astype(float).min()}")
    print(f"平均成交量: {data['volume'].astype(float).mean():.0f}")
```

## ⚠️ 注意事项

### 1. 数据格式
- 所有返回数据均为**字符串格式**，保持baostock原始输出
- 如需数值计算，请使用 `pd.to_numeric()` 转换

### 2. 估值指标限制
- 估值指标（PE、PS、PCF、PB）**仅日线数据支持**
- 分钟线、周线、月线会忽略 `include_valuation` 参数

### 3. 时间范围
- 函数会自动计算合适的查询时间范围
- 日线：`count * 2` 天
- 周线：`count * 10` 天
- 月线：`count * 40` 天
- 分钟线：`count // 50 + 10` 天

### 4. 数据排序
- 所有数据按时间**降序排列**（最新数据在前）
- 分钟线按 `[date, time]` 排序
- 其他频率按 `date` 排序

### 5. 错误处理
- 网络错误或数据获取失败时返回 `None`
- 建议在使用前检查返回值是否为 `None`

## 🔧 常见问题

### Q: 如何获取指数数据？
A: 指数代码格式与股票相同，如上证指数：`sh.000001`，深证成指：`sz.399001`。注意指数没有分钟线数据。

### Q: 复权类型如何选择？
A: 目前固定使用后复权（adjustflag="3"），如需其他复权类型，可修改源码中的 `adjustflag` 参数。

### Q: 数据更新频率如何？
A: 数据来源于baostock，通常T+1更新（即当日数据次日可获取）。

### Q: 如何处理停牌数据？
A: 停牌期间的数据 `tradestatus` 字段为 "0"，正常交易为 "1"。

## 📝 更新日志

- **v1.0**: 初始版本，支持日线数据获取
- **v2.0**: 扩展支持多频率K线数据（分钟线、周线、月线）
- **v2.1**: 优化时间范围计算和数据排序逻辑

## 📞 技术支持

如有问题或建议，请联系开发团队或提交Issue。 