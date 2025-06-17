#!/usr/bin/env python3
"""
BoomStockAI 核心依赖安装脚本
确保与Python 3.11的兼容性
"""
import subprocess
import sys
import importlib

def check_package(package_name, import_name=None):
    """检查包是否已安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def install_package(package):
    """安装单个包"""
    try:
        print(f"🔄 安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 安装失败: {e}")
        return False

def main():
    """主安装函数"""
    print("=" * 50)
    print("📦 BoomStockAI 核心依赖安装")
    print("=" * 50)
    print(f"🐍 Python 版本: {sys.version}")
    
    # 核心依赖包列表 (package_name, import_name)
    core_packages = [
        ("streamlit", "streamlit"),
        ("pandas", "pandas"), 
        ("numpy", "numpy"),
        ("psycopg2-binary", "psycopg2"),
        ("sqlalchemy", "sqlalchemy"),
        ("python-dotenv", "dotenv"),
        ("pyyaml", "yaml"),
        ("loguru", "loguru"),
        ("plotly", "plotly"),
        ("requests", "requests"),
        ("beautifulsoup4", "bs4"),
        ("jieba", "jieba"),
        ("baostock", "baostock"),
        ("akshare", "akshare"),
        ("lxml", "lxml"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("yfinance", "yfinance"),
        ("tqdm", "tqdm"),
        ("schedule", "schedule"),
        ("textblob", "textblob")
    ]
    
    # 检查和安装
    failed_packages = []
    success_count = 0
    
    for package_name, import_name in core_packages:
        if check_package(package_name, import_name):
            print(f"✅ {package_name} 已安装")
            success_count += 1
        else:
            if install_package(package_name):
                success_count += 1
            else:
                failed_packages.append(package_name)
    
    print("\n" + "=" * 50)
    print("📊 安装总结")
    print("=" * 50)
    print(f"✅ 成功安装: {success_count} 个包")
    
    if failed_packages:
        print(f"❌ 安装失败: {len(failed_packages)} 个包")
        print("失败的包:", ", ".join(failed_packages))
        print("\n💡 建议手动安装失败的包:")
        for pkg in failed_packages:
            print(f"   pip install {pkg}")
    else:
        print("🎉 所有核心依赖安装完成!")
    
    print("\n🚀 您现在可以运行:")
    print("   python run.py web")

if __name__ == "__main__":
    main() 