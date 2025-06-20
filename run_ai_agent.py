#!/usr/bin/env python3
"""
BoomStockAI - AI股票分析师启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'openai',
        'langchain',
        'langchain-openai', 
        'langchain-community',
        'streamlit',
        'pandas',
        'baostock'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        
        print("\n📦 请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def check_env_config():
    """检查环境配置"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("⚠️  未找到.env文件")
        print("📝 请复制env.example为.env并配置API密钥:")
        print("   cp env.example .env")
        print("   然后编辑.env文件，设置OPENAI_API_KEY")
        return False
    
    # 检查API密钥
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key.startswith('your_') or api_key.startswith('sk-your_'):
        print("⚠️  请在.env文件中设置有效的OPENAI_API_KEY")
        return False
    
    return True


def run_streamlit_app():
    """启动Streamlit应用"""
    try:
        print("🚀 启动BoomStockAI前端应用...")
        print("📱 应用将在浏览器中打开，请选择 '🤖 AI分析师' 页面")
        print("🔗 如果浏览器未自动打开，请访问: http://localhost:8501")
        print("=" * 60)
        
        # 启动streamlit应用
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'frontend/main.py',
            '--server.headless', 'false',
            '--server.runOnSave', 'true',
            '--browser.gatherUsageStats', 'false'
        ])
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


def run_test_mode():
    """运行测试模式"""
    try:
        print("🧪 启动AI分析师测试模式...")
        subprocess.run([
            sys.executable, 
            'strategy_center/analysis_agent/test_agent.py'
        ])
    except Exception as e:
        print(f"❌ 测试模式启动失败: {e}")


def main():
    """主函数"""
    print("🤖 BoomStockAI - AI股票分析师")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    print("✅ 依赖包检查通过")
    
    # 检查环境配置
    if not check_env_config():
        return
    
    print("✅ 环境配置检查通过")
    
    # 选择运行模式
    print("\n🎯 请选择运行模式:")
    print("1. 🌐 启动前端应用 (推荐)")
    print("2. 🧪 命令行测试模式")
    print("3. 📖 查看使用说明")
    print("4. ❌ 退出")
    
    while True:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            run_streamlit_app()
            break
        elif choice == '2':
            run_test_mode()
            break
        elif choice == '3':
            print("\n📖 使用说明:")
            print("1. 前端应用提供完整的Web界面，支持股票分析和智能对话")
            print("2. 测试模式提供命令行交互，适合快速测试")
            print("3. 详细文档请查看: strategy_center/analysis_agent/AI_AGENT_GUIDE.md")
            print("4. 示例用法:")
            print("   - 输入股票代码如 000001 进行分析")
            print("   - 输入自然语言问题进行对话")
            print("   - 支持的股票代码格式: 000001, 600000, sz.000001, sh.600000")
        elif choice == '4':
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请输入1-4")


if __name__ == "__main__":
    main() 