# 股票数据库建设完整指南

## 概述

本指南将帮助您建立一个完整的股票数据库系统，包括数据库设计、数据采集、自动更新、备份恢复等全套功能。

## 🏗️ 系统架构

```
BoomStockAI 股票数据库系统
├── 数据库层 (PostgreSQL)
│   ├── 股票基本信息表 (stocks)
│   ├── 股票价格数据表 (stock_prices)
│   ├── 市场指数表 (market_indices)
│   ├── 指数价格数据表 (market_index_prices)
│   ├── 基本面数据表 (stock_fundamentals)
│   └── 新闻数据表 (news_articles)
├── 数据采集层
│   ├── BaoStock API (主要数据源)
│   ├── 同花顺爬虫 (热榜数据)
│   └── 新闻爬虫 (财经新闻)
├── 数据管理层
│   ├── 数据库管理器 (StockDatabaseManager)
│   ├── 定时更新调度器 (DataUpdateScheduler)
│   └── 数据验证和清理
└── 应用层
    ├── Web界面 (Streamlit)
    ├── API接口
    └── 策略分析工具
```

## 📊 数据库设计

### 核心表结构

#### 1. 股票基本信息表 (stocks)
```sql
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,           -- 股票代码 (如: sh.600000)
    name VARCHAR(100) NOT NULL,                 -- 股票名称
    market VARCHAR(10) NOT NULL,                -- 市场标识 (SH/SZ)
    industry VARCHAR(50),                       -- 所属行业
    sector VARCHAR(50),                         -- 所属板块
    is_active BOOLEAN DEFAULT TRUE,             -- 是否有效
    list_date TIMESTAMP,                        -- 上市日期
    delist_date TIMESTAMP,                      -- 退市日期
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. 股票价格数据表 (stock_prices)
```sql
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    trade_date TIMESTAMP NOT NULL,              -- 交易日期
    open_price FLOAT,                           -- 开盘价
    high_price FLOAT,                           -- 最高价
    low_price FLOAT,                            -- 最低价
    close_price FLOAT,                          -- 收盘价
    preclose_price FLOAT,                       -- 前收盘价
    volume BIGINT,                              -- 成交量
    amount FLOAT,                               -- 成交金额
    turnover_rate FLOAT,                        -- 换手率
    trade_status INTEGER,                       -- 交易状态
    pct_chg FLOAT,                              -- 涨跌幅(%)
    pe_ratio FLOAT,                             -- 市盈率(TTM)
    pb_ratio FLOAT,                             -- 市净率(MRQ)
    ps_ratio FLOAT,                             -- 市销率(TTM)
    pcf_ratio FLOAT,                            -- 市现率(TTM)
    is_st BOOLEAN DEFAULT FALSE,                -- 是否ST股票
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stock_date ON stock_prices(stock_id, trade_date);
```

#### 3. 市场指数表 (market_indices)
```sql
CREATE TABLE market_indices (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,           -- 指数代码
    name VARCHAR(100) NOT NULL,                 -- 指数名称
    market VARCHAR(10) NOT NULL,                -- 市场标识
    category VARCHAR(50),                       -- 指数类别
    description TEXT,                           -- 指数描述
    base_date TIMESTAMP,                        -- 基准日期
    base_point FLOAT,                           -- 基准点数
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. 自动安装数据库

```bash
# 运行自动安装脚本
python scripts/setup_database.py
```

该脚本将自动：
- 检查并安装PostgreSQL
- 创建数据库和用户
- 生成配置文件
- 测试连接

### 3. 初始化数据库

```bash
# 初始化数据库表和基础数据
python database/stock_database_manager.py --init

# 查看数据库统计
python database/stock_database_manager.py --stats
```

### 4. 数据更新

```bash
# 更新股票数据（最近30天）
python database/stock_database_manager.py --update-stocks --days 30

# 更新指数数据
python database/stock_database_manager.py --update-indices --days 30

# 启动自动更新调度器
python scripts/data_update_scheduler.py --daemon
```

## 📋 详细操作指南

### 数据库管理命令

```bash
# 初始化数据库（强制重建）
python database/stock_database_manager.py --init --force

# 更新指定股票数据
python -c "
from database.stock_database_manager import StockDatabaseManager
db = StockDatabaseManager()
db.update_stock_data(['sh.600000', 'sz.000001'], days=10)
db.close()
"

# 导出数据到CSV
python database/stock_database_manager.py --export data_export/

# 清理90天前的旧数据
python database/stock_database_manager.py --cleanup 90

# 备份数据库
python database/stock_database_manager.py --backup backup/manual_backup.sql
```

### 定时任务管理

```bash
# 启动调度器（交互模式）
python scripts/data_update_scheduler.py

# 后台运行调度器
python scripts/data_update_scheduler.py --daemon

# 手动触发更新
python scripts/data_update_scheduler.py --manual all

# 查看调度状态
python scripts/data_update_scheduler.py --status
```

### 数据查询示例

```python
from database.db_utils import DatabaseManager, StockDataDAO

# 初始化
db_manager = DatabaseManager()
stock_dao = StockDataDAO(db_manager)

# 获取股票信息
stock_info = stock_dao.get_stock_by_code('sh.600000')
print(f"股票信息: {stock_info}")

# 获取价格数据
prices = stock_dao.get_stock_prices(
    stock_info['id'], 
    '2024-01-01', 
    '2024-12-31'
)
print(f"价格数据: {len(prices)} 条记录")

# 获取最新分析结果
analysis = stock_dao.get_latest_analysis(stock_info['id'])
print(f"分析结果: {analysis}")
```

## 🔧 高级配置

### 数据库性能优化

```sql
-- 创建额外索引
CREATE INDEX idx_stock_prices_date ON stock_prices(trade_date);
CREATE INDEX idx_stock_prices_close ON stock_prices(close_price);
CREATE INDEX idx_stocks_industry ON stocks(industry);

-- 分区表（按日期分区）
CREATE TABLE stock_prices_2024 PARTITION OF stock_prices
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 环境变量配置

创建 `.env` 文件：
```bash
# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=boomstock_ai
POSTGRES_USER=boomstock_user
POSTGRES_PASSWORD=your_secure_password

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API密钥
OPENAI_API_KEY=your_openai_api_key
```

### 配置文件定制

编辑 `config/config.yaml`：
```yaml
# 数据更新频率
data_update:
  price_update_frequency: 30      # 分钟
  fundamental_update_frequency: 24 # 小时
  news_update_frequency: 15       # 分钟

# 数据源配置
data_sources:
  baostock:
    enabled: true
    retry_times: 3
    timeout: 30
  
# 股票池配置
stock_pool:
  indices:
    - "sh.000001"  # 上证指数
    - "sz.399001"  # 深证成指
    - "sz.399006"  # 创业板指
  
  market_cap:
    min: 1000000000    # 10亿
    max: 500000000000  # 5000亿
```

## 📈 数据监控和维护

### 数据质量检查

```python
def check_data_quality():
    """检查数据质量"""
    with db_manager.get_session() as session:
        # 检查缺失数据
        missing_data = session.execute("""
            SELECT s.code, s.name, 
                   COUNT(sp.id) as price_records,
                   MAX(sp.trade_date) as latest_date
            FROM stocks s
            LEFT JOIN stock_prices sp ON s.id = sp.stock_id
            WHERE s.is_active = true
            GROUP BY s.id, s.code, s.name
            HAVING COUNT(sp.id) < 100
            ORDER BY price_records ASC
        """).fetchall()
        
        return missing_data
```

### 性能监控

```python
def get_performance_stats():
    """获取性能统计"""
    stats = {
        'table_sizes': {},
        'index_usage': {},
        'query_performance': {}
    }
    
    # 表大小统计
    with db_manager.get_session() as session:
        table_sizes = session.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """).fetchall()
        
        stats['table_sizes'] = table_sizes
    
    return stats
```

## 🔄 备份和恢复

### 自动备份策略

```bash
# 创建备份脚本
cat > backup_script.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/stock_db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/stock_db_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# 创建备份
pg_dump -h localhost -U boomstock_user -d boomstock_ai > $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_FILE.gz"
EOF

chmod +x backup_script.sh

# 添加到crontab（每天凌晨2点备份）
echo "0 2 * * * /path/to/backup_script.sh" | crontab -
```

### 数据恢复

```bash
# 从备份恢复
gunzip -c backup/stock_db_backup_20241218_020000.sql.gz | \
psql -h localhost -U boomstock_user -d boomstock_ai_new
```

## 🚨 故障排除

### 常见问题

1. **连接超时**
   ```bash
   # 检查PostgreSQL状态
   sudo systemctl status postgresql
   
   # 重启服务
   sudo systemctl restart postgresql
   ```

2. **磁盘空间不足**
   ```bash
   # 检查磁盘使用
   df -h
   
   # 清理旧数据
   python database/stock_database_manager.py --cleanup 365
   ```

3. **数据更新失败**
   ```bash
   # 检查网络连接
   ping baoquant.com
   
   # 手动测试API
   python -c "
   from data_collection.market_data.baostock_api import BaoStockAPI
   api = BaoStockAPI()
   data = api.get_stock_history_data('sh.600000', '2024-01-01', '2024-01-02')
   print(len(data))
   "
   ```

### 日志分析

```bash
# 查看应用日志
tail -f logs/boomstock_ai.log

# 查看PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-*.log

# 过滤错误日志
grep -i error logs/boomstock_ai.log
```

## 📚 API文档

### 数据库管理API

```python
# 初始化管理器
db_manager = StockDatabaseManager()

# 初始化数据库
db_manager.init_database(force_recreate=False)

# 更新数据
db_manager.update_stock_data(codes=['sh.600000'], days=30)
db_manager.update_index_data(days=30)

# 获取统计信息
stats = db_manager.get_database_stats()

# 导出数据
db_manager.export_data('export_dir')

# 清理数据
db_manager.cleanup_old_data(days_to_keep=365)

# 备份数据库
db_manager.backup_database('backup_path.sql')
```

### 调度器API

```python
# 初始化调度器
scheduler = DataUpdateScheduler()

# 启动调度器
scheduler.start()

# 手动更新
scheduler.manual_update('stocks')  # 'stocks', 'indices', 'all'

# 获取下次运行时间
next_runs = scheduler.get_next_runs()

# 停止调度器
scheduler.stop()
```

## 🎯 最佳实践

1. **数据完整性**
   - 定期检查数据缺失
   - 验证数据逻辑一致性
   - 监控数据更新频率

2. **性能优化**
   - 合理使用索引
   - 定期分析表统计信息
   - 考虑数据分区

3. **安全性**
   - 使用强密码
   - 限制数据库访问权限
   - 定期更新系统补丁

4. **可扩展性**
   - 设计合理的表结构
   - 预留扩展字段
   - 考虑分布式部署

## 📞 技术支持

如果您在使用过程中遇到问题，可以：

1. 查看日志文件排查问题
2. 运行诊断命令检查系统状态
3. 参考故障排除章节
4. 提交Issue到项目仓库

---

**注意**: 请确保在生产环境中使用前进行充分测试，并制定完善的备份策略。 