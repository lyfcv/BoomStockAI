#!/usr/bin/env python3
"""
股票分析Agent测试脚本
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from strategy_center.analysis_agent.stock_analysis_agent import create_stock_agent

def test_agent():
    """测试Agent功能"""
    
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 请设置OPENAI_API_KEY环境变量")
        print("   可以在项目根目录创建.env文件，添加：")
        print("   OPENAI_API_KEY=your_api_key_here")
        return False
    
    print("🚀 开始测试股票分析Agent...")
    print("=" * 60)
    
    try:
        # 创建Agent
        print("📝 正在创建Agent...")
        agent = create_stock_agent(api_key)
        print("✅ Agent创建成功！")
        
        # 测试1: 股票分析
        print("\n📊 测试1: 股票技术分析")
        print("-" * 40)
        
        stock_code = "000001"  # 平安银行
        print(f"正在分析股票: {stock_code}")
        
        result = agent.analyze_stock(stock_code, "请简要分析该股票的技术走势")
        
        if result['success']:
            print("✅ 分析成功！")
            print(f"股票代码: {result['stock_code']}")
            print(f"分析时间: {result['timestamp']}")
            print("分析结果:")
            print("-" * 30)
            print(result['analysis'])
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
            return False
        
        # 测试2: 对话功能
        print("\n💬 测试2: 智能对话")
        print("-" * 40)
        
        chat_message = "你好，请介绍一下你的功能"
        print(f"用户消息: {chat_message}")
        
        chat_result = agent.chat(chat_message)
        
        if chat_result['success']:
            print("✅ 对话成功！")
            print("AI回复:")
            print("-" * 30)
            print(chat_result['response'])
        else:
            print(f"❌ 对话失败: {chat_result.get('error', '未知错误')}")
            return False
        
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def interactive_test():
    """交互式测试"""
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ 请设置OPENAI_API_KEY环境变量")
        return
    
    print("🤖 股票分析Agent交互式测试")
    print("=" * 50)
    
    try:
        # 创建Agent
        agent = create_stock_agent(api_key)
        print("✅ Agent初始化成功！")
        print("💡 输入'quit'退出，输入'help'查看帮助")
        print("-" * 50)
        
        while True:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if user_input.lower() == 'help':
                print("""
📖 使用帮助:
- 直接输入股票代码进行分析，如: 000001
- 输入自然语言问题，如: 帮我分析一下平安银行
- 输入'quit'退出程序
- 输入'help'查看此帮助
                """)
                continue
            
            if not user_input:
                continue
            
            print("🤖 AI分析师正在思考...")
            
            # 判断是否为股票代码
            if user_input.isdigit() and len(user_input) == 6:
                # 股票分析
                result = agent.analyze_stock(user_input)
                if result['success']:
                    print(f"🤖 AI分析师: \n{result['analysis']}")
                else:
                    print(f"❌ 分析失败: {result.get('error', '未知错误')}")
            else:
                # 普通对话
                result = agent.chat(user_input)
                if result['success']:
                    print(f"🤖 AI分析师: \n{result['response']}")
                else:
                    print(f"❌ 对话失败: {result.get('error', '未知错误')}")
    
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序出现错误: {e}")


if __name__ == "__main__":
    print("🎯 股票分析Agent测试程序")
    print("=" * 60)
    
    mode = input("请选择测试模式:\n1. 自动测试\n2. 交互式测试\n请输入选择 (1/2): ").strip()
    
    if mode == "1":
        success = test_agent()
        if success:
            print("\n✅ 测试完成，Agent工作正常！")
        else:
            print("\n❌ 测试失败，请检查配置和网络连接")
    elif mode == "2":
        interactive_test()
    else:
        print("❌ 无效选择") 