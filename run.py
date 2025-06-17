#!/usr/bin/env python3
"""
BoomStockAI 启动脚本
支持多种启动模式：Web界面、数据更新、回测等
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_web_app(port=8501, debug=False):
    """启动Streamlit Web应用"""
    print(f"🚀 启动BoomStockAI Web界面...")
    print(f"📡 访问地址: http://localhost:{port}")
    
    cmd = [
        "streamlit", "run", "frontend/main.py",
        "--server.port", str(port),
        "--server.headless", "true"
    ]
    
    if debug:
        cmd.extend(["--logger.level", "debug"])
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Web应用启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在关闭应用...")
        sys.exit(0)


def init_database():
    """初始化数据库"""
    print("🔧 正在初始化数据库...")
    
    try:
        from database.db_utils import db_manager
        
        # 测试数据库连接
        if not db_manager.test_connection():
            print("❌ 数据库连接失败，请检查配置")
            return False
        
        # 创建数据库表
        db_manager.create_tables()
        print("✅ 数据库初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


def update_stock_data():
    """更新股票数据"""
    print("📊 正在更新股票数据...")
    
    try:
        from data_collection.market_data.baostock_api import baostock_api
        
        # 获取股票基本信息
        print("获取股票基本信息...")
        stocks = baostock_api.get_stock_basic_info()
        if stocks:
            saved_count = baostock_api.save_stock_basic_to_db(stocks)
            print(f"✅ 更新股票基本信息完成，共{saved_count}只股票")
        
        # 更新热门股票的价格数据
        print("更新热门股票价格数据...")
        popular_stocks = ['sh.600000', 'sz.000001', 'sz.000002', 'sh.600036', 'sz.000858']
        results = baostock_api.batch_update_stock_data(popular_stocks, days=30)
        print(f"✅ 价格数据更新完成: 成功{results['success_count']}只，失败{results['failed_count']}只")
        
        # 更新并保存指数数据到数据库
        print("更新指数数据并保存到数据库...")
        index_codes = ['sh.000001', 'sz.399001', 'sz.399006', 'sh.000688']
        try:
            # 批量更新指数数据到数据库
            index_results = baostock_api.batch_update_index_data(index_codes, days=30)
            print(f"✅ 指数数据保存完成: 成功{index_results['success_count']}个，失败{index_results['failed_count']}个")
            print(f"   共保存{index_results['total_records']}条指数价格记录")
            
            # 显示最新指数信息（用于验证）
            latest_data = baostock_api.get_latest_index_info(index_codes)
            if latest_data:
                print("📈 最新指数行情:")
                for code, data in latest_data.items():
                    if data:
                        name = {'sh.000001': '上证指数', 'sz.399001': '深证成指', 
                               'sz.399006': '创业板指', 'sh.000688': '科创50'}.get(code, code)
                        print(f"   {name}: {data['current_price']:.2f} ({data['change_pct']:+.2f}%)")
            
        except Exception as e:
            print(f"⚠️ 指数数据更新失败: {e}")
        
    except Exception as e:
        print(f"❌ 股票数据更新失败: {e}")


def update_news_data():
    """更新新闻数据"""
    print("📰 正在更新新闻数据...")
    
    try:
        from data_collection.news_crawler.crawler import news_manager
        
        results = news_manager.crawl_all_news(pages_per_source=3)
        print(f"✅ 新闻数据更新完成: 爬取{results['total_news']}条，保存{results['saved_news']}条")
        
    except Exception as e:
        print(f"❌ 新闻数据更新失败: {e}")


def run_backtest():
    """运行回测"""
    print("📈 正在运行策略回测...")
    
    try:
        # 这里可以添加回测逻辑
        print("⚠️ 回测功能开发中...")
        
    except Exception as e:
        print(f"❌ 回测运行失败: {e}")


def check_dependencies():
    """检查依赖项"""
    print("🔍 检查系统依赖...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'psycopg2',
        'sqlalchemy',
        'baostock',
        'requests',
        'bs4',  # beautifulsoup4导入名称是bs4
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖项检查通过")
    return True


def show_system_info():
    """显示系统信息"""
    print("=" * 50)
    print("📈 BoomStockAI 智能选股系统")
    print("=" * 50)
    print(f"🔗 项目路径: {project_root}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"💻 操作系统: {os.name}")
    
    # 检查配置文件
    config_file = project_root / "config" / "config.yaml"
    env_file = project_root / ".env"
    
    print(f"⚙️ 配置文件: {'✅' if config_file.exists() else '❌'}")
    print(f"🔐 环境变量: {'✅' if env_file.exists() else '❌'}")
    
    # 检查数据库连接
    try:
        from database.db_utils import db_manager
        db_status = "✅" if db_manager.test_connection() else "❌"
    except:
        db_status = "❌"
    
    print(f"🗄️ 数据库连接: {db_status}")
    print("=" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="BoomStockAI 智能选股系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run.py web                    # 启动Web界面
  python run.py web --port 8502        # 指定端口启动
  python run.py init                   # 初始化数据库
  python run.py update-stock           # 更新股票数据
  python run.py update-news            # 更新新闻数据
  python run.py backtest               # 运行回测
  python run.py info                   # 显示系统信息
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # Web界面命令
    web_parser = subparsers.add_parser('web', help='启动Web界面')
    web_parser.add_argument('--port', type=int, default=8501, help='Web服务端口')
    web_parser.add_argument('--debug', action='store_true', help='调试模式')
    
    # 初始化数据库命令
    subparsers.add_parser('init', help='初始化数据库')
    
    # 数据更新命令
    subparsers.add_parser('update-stock', help='更新股票数据')
    subparsers.add_parser('update-news', help='更新新闻数据')
    subparsers.add_parser('update-all', help='更新所有数据')
    
    # 回测命令
    subparsers.add_parser('backtest', help='运行策略回测')
    
    # 系统信息命令
    subparsers.add_parser('info', help='显示系统信息')
    
    # 检查依赖命令
    subparsers.add_parser('check', help='检查系统依赖')
    
    args = parser.parse_args()
    
    # 显示系统信息
    show_system_info()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应命令
    if args.command == 'web':
        if check_dependencies():
            run_web_app(port=args.port, debug=args.debug)
    
    elif args.command == 'init':
        init_database()
    
    elif args.command == 'update-stock':
        update_stock_data()
    
    elif args.command == 'update-news':
        update_news_data()
    
    elif args.command == 'update-all':
        update_stock_data()
        update_news_data()
    
    elif args.command == 'backtest':
        run_backtest()
    
    elif args.command == 'info':
        pass  # 系统信息已经显示
    
    elif args.command == 'check':
        check_dependencies()


if __name__ == "__main__":
    main() 