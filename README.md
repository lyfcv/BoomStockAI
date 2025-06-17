# 📈 BoomStockAI - 智能选股系统

## 🚀 项目概述

BoomStockAI 是一套"**智能选股 + 量化研究**"一体化解决方案，专为个人投资者打造。系统自动化地从全市场数据中发现具备高增长潜力（翻倍可能）的股票，并保存全部数据以便事后复盘与策略迭代。

### ✨ 核心特性

- 🔍 **智能选股**: 基于AI和量化模型的自动化选股系统
- 📊 **多维分析**: 技术指标、基本面、新闻情感三重分析
- 📰 **实时资讯**: 自动抓取财经新闻并进行情感分析
- 🎯 **交易信号**: 智能生成买入/卖出信号
- 📈 **回测验证**: 完整的策略回测与性能评估
- 🌐 **Web界面**: 基于Streamlit的现代化Web UI
- 💾 **数据持久化**: PostgreSQL数据库存储所有关键数据

## 🏗️ 技术架构

```
BoomStockAI/
├── data_collection/             # 数据获取模块
│   ├── market_data/             # 股票行情数据(baostock, akshare)
│   └── news_crawler/            # 新闻爬虫与情感分析
├── strategy_center/             # 量化和AI分析核心
│   ├── models/                  # 量化因子模型
│   ├── analysis_agent/          # AI分析引擎
│   ├── strategies/              # 策略实现
│   └── backtest/                # 回测引擎
├── database/                    # 数据库层
├── frontend/                    # Streamlit前端界面
├── config/                      # 配置管理
└── tests/                       # 测试代码
```

### 🛠️ 技术栈

- **后端**: Python 3.8+
- **数据库**: PostgreSQL 13+
- **前端**: Streamlit
- **数据源**: BaoStock, AKShare, Tushare, 新闻爬虫
- **AI分析**: OpenAI GPT, 本地情感分析模型
- **量化库**: pandas, numpy, ta-lib, backtrader
- **可视化**: plotly, matplotlib

## 📦 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-username/BoomStockAI.git
cd BoomStockAI

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库配置

```bash
# 安装PostgreSQL
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE boomstock_ai;
CREATE USER boomstock_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE boomstock_ai TO boomstock_user;
\q
```

### 3. 环境变量配置

```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件，填入实际配置
nano .env
```

在`.env`文件中配置以下必要参数：

```env
# 数据库配置
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=boomstock_ai
POSTGRES_USER=boomstock_user

# OpenAI API配置(可选)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Redis配置(可选)
REDIS_PASSWORD=your_redis_password
```

### 4. 初始化数据库

```bash
# 创建数据库表
python -c "
from database.db_utils import db_manager
db_manager.create_tables()
print('数据库初始化完成!')
"
```

### 5. 初始化数据 (重要)

在首次运行系统前，需要初始化股票列表和历史价格数据。

```bash
# 执行全量数据初始化脚本
python scripts/update_stock_data.py --mode=full
```

**⚠️ 注意:** 此脚本会下载所有A股近10年的历史数据，根据网络情况，可能需要**数小时**才能完成。请耐心等待。脚本执行完成后，数据库才包含策略分析所需的数据。

### 6. 启动系统

```bash
# 启动Streamlit Web界面
streamlit run frontend/main.py

# 或者指定端口
streamlit run frontend/main.py --server.port 8501
```

访问 `http://localhost:8501` 即可使用系统。

## 📊 功能模块

### 1. 数据获取模块

#### 股票数据获取
```python
from data_collection.market_data.baostock_api import baostock_api

# 获取股票基本信息
stocks = baostock_api.get_stock_basic_info()

# 获取历史价格数据
price_data = baostock_api.get_stock_history_data(
    code='sh.600000',
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

#### 新闻数据抓取
```python
from data_collection.news_crawler.crawler import news_manager

# 抓取所有新闻源
results = news_manager.crawl_all_news(pages_per_source=5)
print(f"共抓取 {results['total_news']} 条新闻")
```

### 2. 智能分析模块

#### 技术指标分析
```python
from strategy_center.models.trend_factors import TechnicalAnalyzer

analyzer = TechnicalAnalyzer()
signals = analyzer.analyze_stock('000001', period=30)
```

#### AI分析引擎
```python
from strategy_center.analysis_agent.llm_interface import AIAnalyzer

ai_analyzer = AIAnalyzer()
analysis = ai_analyzer.analyze_stock_fundamentals('000001')
```

### 3. 回测系统

```python
from strategy_center.backtest.backtest_engine import BacktestEngine

engine = BacktestEngine()
results = engine.run_backtest(
    strategy_name='momentum_strategy',
    start_date='2023-01-01',
    end_date='2024-01-01',
    initial_capital=1000000
)
```

## 🔧 配置说明

### 系统配置文件 (`config/config.yaml`)

```yaml
# 数据源配置
data_sources:
  baostock:
    enabled: true
    retry_times: 3
  akshare:
    enabled: true
    timeout: 30

# 策略配置
strategies:
  technical:
    enabled: true
    indicators: ["RSI", "MACD", "MA"]
  fundamental:
    enabled: true
    factors: ["PE", "PB", "ROE"]

# 风险控制
risk_control:
  max_position_size: 0.1
  stop_loss: 0.08
  take_profit: 0.20
```

## 📈 使用示例

### 1. 平台突破选股策略

快速执行平台突破选股策略：

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

### 2. 获取Top推荐股票

通过Web界面或API获取AI推荐的高潜力股票：

```python
from database.db_utils import stock_dao

# 获取评分最高的10只股票
top_stocks = stock_dao.get_top_stocks(limit=10)
for stock in top_stocks:
    print(f"{stock['stock_name']}: {stock['total_score']:.2f}分")
```

### 3. 查看交易信号

```python
# 获取最新交易信号
signals = trading_signal_dao.get_latest_signals(limit=20)
for signal in signals:
    print(f"{signal['stock_name']}: {signal['signal_type']} - 置信度: {signal['confidence']:.2f}")
```

### 4. 情感分析

```python
from database.db_utils import news_dao

# 获取特定股票的情感分析
sentiment = news_dao.get_sentiment_summary('000001', days=7)
print(f"平均情感得分: {sentiment['average_sentiment']:.3f}")
```

## 🔄 定时任务

系统支持定时自动更新数据：

```bash
# 设置crontab定时任务
crontab -e

# 每天9:00增量更新股价数据 (近60天)
0 9 * * 1-5 cd /path/to/BoomStockAI && python scripts/update_stock_data.py --mode=daily

# 每小时抓取新闻 (待实现)
# 0 * * * * cd /path/to/BoomStockAI && python scripts/update_news.py

# 每天17:00更新同花顺热榜
0 17 * * * cd /path/to/BoomStockAI && python scripts/update_ths_hot_list.py

# 每天9:30执行平台突破策略
30 9 * * 1-5 cd /path/to/BoomStockAI && python scripts/run_platform_breakout.py
```

## 🚨 注意事项

1. **数据源限制**: BaoStock和AKShare都有请求频率限制，请适当设置延时
2. **API配额**: OpenAI API需要付费，请根据需求配置
3. **存储空间**: 历史数据会占用较大存储空间，建议定期清理
4. **网络环境**: 部分数据源可能需要稳定的网络环境

## 🤝 贡献指南

欢迎贡献代码! 请遵循以下步骤:

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 技术支持

- 📧 邮箱: support@boomstockai.com
- 💬 微信群: 扫码加入技术交流群
- 📖 文档: [https://docs.boomstockai.com](https://docs.boomstockai.com)

## 🔥 更新日志

### v1.0.0 (2024-12-15)
- ✅ 完成核心框架搭建
- ✅ 实现BaoStock数据获取
- ✅ 完成新闻爬虫模块
- ✅ 实现Streamlit前端界面
- ✅ 完成数据库设计

### v1.1.0 (2024-12-16) - 新增平台突破策略
- ✅ 完成平台突破选股策略
- ✅ 实现技术指标计算模块
- ✅ 添加策略执行器和定时任务
- ✅ 完成Streamlit前端界面
- ✅ 支持自定义配置和参数调优

### 即将推出
- 🔄 AKShare数据源集成
- 🤖 更多AI分析模型
- 📊 高级回测功能
- 📱 移动端支持

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star! ⭐** 