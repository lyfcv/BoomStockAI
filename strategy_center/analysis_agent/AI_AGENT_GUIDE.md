# 🤖 AI股票分析师使用指南

## 📋 概述

AI股票分析师是基于ChatGPT-4o和LangChain开发的智能股票分析系统，能够：
- 📊 自动获取股票K线数据
- 🔍 进行技术指标分析
- 💬 提供自然语言对话交互
- 🎯 生成专业的投资分析报告

## 🚀 快速开始

### 1. 环境配置

#### 安装依赖
```bash
pip install openai>=1.0.0 langchain>=0.1.0 langchain-openai>=0.1.0 langchain-community>=0.1.0
```

#### 配置API密钥
创建`.env`文件并添加：
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://aihubmix.com/v1
```

### 2. 使用方式

#### 方式1：前端界面
```bash
# 启动前端应用
streamlit run frontend/main.py

# 在浏览器中选择 "🤖 AI分析师" 页面
```

#### 方式2：Python API
```python
from strategy_center.analysis_agent.stock_analysis_agent import create_stock_agent

# 创建Agent
agent = create_stock_agent(api_key="your_api_key")

# 股票分析
result = agent.analyze_stock("000001")
print(result['analysis'])

# 智能对话
chat_result = agent.chat("帮我分析一下平安银行的走势")
print(chat_result['response'])
```

#### 方式3：命令行测试
```bash
cd strategy_center/analysis_agent
python test_agent.py
```

## 🛠️ 功能详解

### 📊 股票分析功能

#### 数据获取工具
- `get_stock_kline_data`: 获取30日K线数据
- `get_stock_summary`: 获取股票摘要信息
- `calculate_technical_indicators`: 计算技术指标

#### 分析类型
1. **全面分析**: 综合技术分析报告
2. **技术指标分析**: 重点分析MA、RSI等指标
3. **趋势分析**: 判断短期和中期走势
4. **风险评估**: 分析投资风险

#### 支持的股票代码格式
- `000001` (深圳股票)
- `600000` (上海股票)
- `sz.000001` (带前缀格式)
- `sh.600000` (带前缀格式)

### 💬 智能对话功能

#### 对话能力
- 自然语言理解
- 专业术语解释
- 个性化分析建议
- 上下文记忆

#### 示例对话
```
用户: 帮我分析一下平安银行最近的走势
AI: 我来为您分析平安银行(000001)的最近走势...

用户: 这只股票适合长期持有吗？
AI: 基于技术分析，从长期投资角度来看...
```

## 🎯 前端界面功能

### 配置页面
- **API配置**: 设置OpenAI API密钥和中转地址
- **Agent初始化**: 一键创建AI分析师实例
- **状态显示**: 实时显示Agent运行状态

### 分析页面
- **股票代码输入**: 支持多种格式
- **分析类型选择**: 全面分析、技术指标、趋势分析等
- **自定义查询**: 输入特定分析需求
- **结果展示**: 结构化显示分析报告

### 对话页面
- **聊天界面**: 类似ChatGPT的对话体验
- **历史记录**: 自动保存对话历史
- **消息管理**: 支持清空历史记录

### 历史记录页面
- **分析统计**: 显示使用统计信息
- **历史查看**: 查看所有分析记录
- **记录管理**: 支持清空历史记录

## 🔧 技术架构

### 核心组件
```
StockAnalysisAgent
├── ChatGPT-4o (大语言模型)
├── LangChain (Agent框架)
├── Tools (分析工具)
│   ├── get_stock_kline_data
│   ├── get_stock_summary
│   └── calculate_technical_indicators
└── Memory (对话记忆)
```

### 数据流程
```
用户输入 → Agent → 工具调用 → 数据获取 → AI分析 → 结果输出
```

## 📈 使用示例

### 示例1：技术分析
```python
agent = create_stock_agent(api_key)
result = agent.analyze_stock("000001", "请分析技术指标")
```

### 示例2：风险评估
```python
result = agent.analyze_stock("600000", "请评估投资风险")
```

### 示例3：对话交互
```python
response = agent.chat("什么是MACD指标？")
```

## ⚠️ 注意事项

### API配置
1. 确保API密钥有效且有足够余额
2. 中转地址`https://aihubmix.com/v1`需要网络可达
3. 建议设置合理的请求频率限制

### 数据准确性
1. K线数据来源于BaoStock，具有一定延迟
2. 技术指标计算基于历史数据
3. AI分析仅供参考，不构成投资建议

### 性能优化
1. Agent初始化需要时间，建议复用实例
2. 大量请求时注意API限流
3. 对话历史会影响响应时间

## 🔍 故障排除

### 常见问题

#### 1. API密钥错误
```
错误: Invalid API key
解决: 检查.env文件中的OPENAI_API_KEY配置
```

#### 2. 网络连接失败
```
错误: Connection timeout
解决: 检查网络连接和中转地址可用性
```

#### 3. 数据获取失败
```
错误: 获取股票数据失败
解决: 检查股票代码格式和BaoStock服务状态
```

#### 4. 导入模块失败
```
错误: ModuleNotFoundError
解决: 确保安装了所有依赖包
```

### 调试方法
1. 启用Agent的verbose模式查看详细日志
2. 使用test_agent.py进行功能测试
3. 检查网络连接和API服务状态

## 📚 扩展开发

### 添加新工具
```python
def custom_analysis_tool(stock_code: str) -> str:
    # 自定义分析逻辑
    return analysis_result

# 添加到工具列表
tools.append(Tool(
    name="custom_analysis",
    description="自定义分析工具",
    func=custom_analysis_tool
))
```

### 自定义Agent提示词
```python
system_prompt = """
你是一个专业的股票分析师...
[自定义提示词内容]
"""
```

### 集成其他数据源
```python
def get_news_data(stock_code: str) -> str:
    # 获取新闻数据
    return news_data
```

## 📞 支持与反馈

如果您在使用过程中遇到问题或有改进建议，请：
1. 查看本文档的故障排除部分
2. 检查项目的GitHub Issues
3. 提交详细的错误报告

---

**⚠️ 免责声明**: 本AI分析师提供的所有分析和建议仅供参考，不构成投资建议。投资有风险，入市需谨慎。请在做出投资决策前咨询专业的投资顾问。 