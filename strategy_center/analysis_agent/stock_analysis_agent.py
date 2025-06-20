import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferWindowMemory

from .kline_get import analyze_stock_kline, format_kline_for_analysis


class StockAnalysisAgent:
    """
    基于LangChain和ChatGPT-4o的股票分析Agent
    """
    
    def __init__(self, api_key: str, base_url: str = "https://aihubmix.com/v1"):
        """
        初始化股票分析Agent
        
        Args:
            api_key: OpenAI API密钥
            base_url: API中转地址，默认使用aihubmix.com
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # 初始化ChatGPT-4o模型
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,
            max_tokens=4000
        )
        
        # 创建工具
        self.tools = self._create_tools()
        
        # 创建Agent
        self.agent = self._create_agent()
        
        # 创建记忆
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10
        )
        
        # 创建Agent执行器
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5
        )
    
    def _create_tools(self) -> List[Tool]:
        """创建分析工具"""
        
        def get_stock_kline_data(stock_code: str) -> str:
            """获取股票K线数据工具"""
            try:
                result = analyze_stock_kline(stock_code)
                if result['success']:
                    return result['analysis_text']
                else:
                    return f"获取股票 {stock_code} 数据失败"
            except Exception as e:
                return f"获取数据时出错: {str(e)}"
        
        def get_stock_summary(stock_code: str) -> str:
            """获取股票摘要信息工具"""
            try:
                result = analyze_stock_kline(stock_code)
                if result['success']:
                    summary = result['summary']
                    return json.dumps({
                        '股票代码': stock_code,
                        '最新价格': summary['latest_price'],
                        '最高价': summary['highest_price'],
                        '最低价': summary['lowest_price'],
                        '期间涨跌幅': f"{summary['total_change_pct']:.2f}%",
                        '交易日数': summary['trading_days']
                    }, ensure_ascii=False, indent=2)
                else:
                    return f"获取股票 {stock_code} 摘要失败"
            except Exception as e:
                return f"获取摘要时出错: {str(e)}"
        
        def calculate_technical_indicators(stock_code: str) -> str:
            """计算技术指标工具"""
            try:
                result = analyze_stock_kline(stock_code)
                if result['success']:
                    data = result['data']
                    if len(data) >= 5:
                        # 计算简单移动平均线
                        recent_5 = [item['close'] for item in data[-5:]]
                        recent_10 = [item['close'] for item in data[-10:]] if len(data) >= 10 else recent_5
                        
                        ma5 = sum(recent_5) / len(recent_5)
                        ma10 = sum(recent_10) / len(recent_10)
                        
                        current_price = data[-1]['close']
                        
                        # 简单趋势判断
                        trend = "上升" if current_price > ma5 > ma10 else "下降" if current_price < ma5 < ma10 else "震荡"
                        
                        return json.dumps({
                            '当前价格': current_price,
                            'MA5': round(ma5, 2),
                            'MA10': round(ma10, 2),
                            '趋势判断': trend,
                            '价格位置': '高位' if current_price > ma5 else '低位'
                        }, ensure_ascii=False, indent=2)
                    else:
                        return "数据不足，无法计算技术指标"
                else:
                    return f"获取股票 {stock_code} 数据失败"
            except Exception as e:
                return f"计算技术指标时出错: {str(e)}"
        
        return [
            Tool(
                name="get_stock_kline_data",
                description="获取股票的30日K线数据，包含完整的OHLCV数据和涨跌幅信息。输入股票代码（如000001、600000）",
                func=get_stock_kline_data
            ),
            Tool(
                name="get_stock_summary",
                description="获取股票的摘要信息，包含最新价格、价格区间、涨跌幅等关键指标。输入股票代码",
                func=get_stock_summary
            ),
            Tool(
                name="calculate_technical_indicators",
                description="计算股票的技术指标，包含移动平均线、趋势判断等。输入股票代码",
                func=calculate_technical_indicators
            )
        ]
    
    def _create_agent(self):
        """创建Agent"""
        
        system_prompt = """你是一个专业的股票分析师AI助手，具备以下能力：

1. **数据分析**：能够获取和分析股票的K线数据、价格走势、成交量等
2. **技术分析**：掌握各种技术指标的计算和解读
3. **趋势判断**：基于历史数据判断股票的短期和中期趋势
4. **风险评估**：识别投资风险并给出合理建议

**分析原则**：
- 基于真实数据进行客观分析
- 提供多角度的分析视角
- 明确指出分析的局限性
- 强调投资有风险，决策需谨慎

**回答风格**：
- 使用中文回答
- 条理清晰，逻辑严谨
- 适当使用emoji增强可读性
- 避免给出绝对的买卖建议

当用户询问股票分析时，请：
1. 首先获取股票的基本数据
2. 分析价格走势和成交量
3. 计算相关技术指标
4. 给出综合分析结论
5. 提醒投资风险

记住：你的分析仅供参考，投资决策应该基于更全面的信息和个人风险承受能力。"""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    def analyze_stock(self, stock_code: str, query: str = None) -> Dict[str, Any]:
        """
        分析股票
        
        Args:
            stock_code: 股票代码
            query: 具体的分析需求，如果为空则进行全面分析
            
        Returns:
            分析结果字典
        """
        try:
            if query is None:
                query = f"请对股票 {stock_code} 进行全面的技术分析，包括价格走势、成交量分析、技术指标分析，并给出投资建议。"
            else:
                query = f"股票代码：{stock_code}。{query}"
            
            # 执行分析
            result = self.agent_executor.invoke({"input": query})
            
            return {
                "success": True,
                "stock_code": stock_code,
                "query": query,
                "analysis": result["output"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "stock_code": stock_code,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def chat(self, message: str) -> Dict[str, Any]:
        """
        与Agent对话
        
        Args:
            message: 用户消息
            
        Returns:
            对话结果
        """
        try:
            result = self.agent_executor.invoke({"input": message})
            
            return {
                "success": True,
                "message": message,
                "response": result["output"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": message,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_analysis_template(self, stock_code: str) -> str:
        """获取分析模板"""
        return f"""
# 股票分析报告 - {stock_code}

## 📊 基本信息
- 股票代码：{stock_code}
- 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 价格走势分析
[待分析]

## 📊 成交量分析  
[待分析]

## 🔍 技术指标分析
[待分析]

## 💡 投资建议
[待分析]

## ⚠️ 风险提示
投资有风险，入市需谨慎。本分析仅供参考，不构成投资建议。
"""


# 便捷函数
def create_stock_agent(api_key: str, base_url: str = "https://aihubmix.com/v1") -> StockAnalysisAgent:
    """创建股票分析Agent的便捷函数"""
    return StockAnalysisAgent(api_key=api_key, base_url=base_url)


if __name__ == "__main__":
    # 测试示例
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("请设置OPENAI_API_KEY环境变量")
        exit(1)
    
    # 创建Agent
    agent = create_stock_agent(api_key)
    
    # 测试分析
    result = agent.analyze_stock("000001")
    print("分析结果：")
    print(result["analysis"] if result["success"] else result["error"]) 