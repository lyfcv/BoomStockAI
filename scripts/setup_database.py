#!/usr/bin/env python3
"""
数据库安装和配置脚本
自动安装PostgreSQL并配置股票数据库
"""
import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import yaml
from loguru import logger
import getpass

def check_postgresql_installed():
    """检查PostgreSQL是否已安装"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"PostgreSQL已安装: {result.stdout.strip()}")
            return True
        return False
    except FileNotFoundError:
        return False

def install_postgresql():
    """安装PostgreSQL"""
    logger.info("开始安装PostgreSQL...")
    
    # 检测操作系统
    if sys.platform.startswith('linux'):
        # Ubuntu/Debian
        if os.path.exists('/etc/debian_version'):
            commands = [
                'sudo apt update',
                'sudo apt install -y postgresql postgresql-contrib python3-psycopg2'
            ]
        # CentOS/RHEL
        elif os.path.exists('/etc/redhat-release'):
            commands = [
                'sudo yum install -y postgresql postgresql-server postgresql-contrib python3-psycopg2',
                'sudo postgresql-setup initdb',
                'sudo systemctl enable postgresql',
                'sudo systemctl start postgresql'
            ]
        else:
            logger.error("不支持的Linux发行版")
            return False
            
    elif sys.platform == 'darwin':
        # macOS
        commands = [
            'brew install postgresql',
            'brew services start postgresql'
        ]
    else:
        logger.error("不支持的操作系统")
        return False
    
    # 执行安装命令
    for cmd in commands:
        logger.info(f"执行: {cmd}")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            logger.error(f"命令执行失败: {cmd}")
            return False
    
    logger.info("PostgreSQL安装完成")
    return True

def create_database_and_user():
    """创建数据库和用户"""
    logger.info("开始创建数据库和用户...")
    
    # 获取管理员密码
    admin_password = getpass.getpass("请输入PostgreSQL管理员密码: ")
    
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'admin_user': 'postgres',
        'admin_password': admin_password,
        'db_name': 'boomstock_ai',
        'db_user': 'boomstock_user',
        'db_password': getpass.getpass("请设置数据库用户密码: ")
    }
    
    try:
        # 连接到PostgreSQL
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['admin_user'],
            password=db_config['admin_password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 创建用户
        logger.info(f"创建用户: {db_config['db_user']}")
        cursor.execute(f"""
            CREATE USER {db_config['db_user']} WITH PASSWORD '{db_config['db_password']}';
        """)
        
        # 创建数据库
        logger.info(f"创建数据库: {db_config['db_name']}")
        cursor.execute(f"""
            CREATE DATABASE {db_config['db_name']} 
            OWNER {db_config['db_user']} 
            ENCODING 'UTF8' 
            LC_COLLATE = 'en_US.UTF-8' 
            LC_CTYPE = 'en_US.UTF-8';
        """)
        
        # 授权
        cursor.execute(f"""
            GRANT ALL PRIVILEGES ON DATABASE {db_config['db_name']} TO {db_config['db_user']};
        """)
        
        cursor.close()
        conn.close()
        
        logger.info("数据库和用户创建完成")
        return db_config
        
    except psycopg2.Error as e:
        logger.error(f"数据库创建失败: {e}")
        return None

def create_env_file(db_config):
    """创建环境变量文件"""
    logger.info("创建环境变量文件...")
    
    env_content = f"""# BoomStockAI 环境变量配置
# 数据库配置
POSTGRES_HOST={db_config['host']}
POSTGRES_PORT={db_config['port']}
POSTGRES_DB={db_config['db_name']}
POSTGRES_USER={db_config['db_user']}
POSTGRES_PASSWORD={db_config['db_password']}

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API密钥
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logger.info("环境变量文件创建完成: .env")

def update_config_file(db_config):
    """更新配置文件"""
    logger.info("更新配置文件...")
    
    config_path = 'config/config.yaml'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 更新数据库配置
        config['database'].update({
            'host': db_config['host'],
            'port': db_config['port'],
            'name': db_config['db_name'],
            'user': db_config['db_user'],
            'password': f"${{POSTGRES_PASSWORD}}"
        })
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("配置文件更新完成")
        
    except Exception as e:
        logger.error(f"配置文件更新失败: {e}")

def install_python_dependencies():
    """安装Python依赖"""
    logger.info("安装Python依赖...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        logger.info("Python依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Python依赖安装失败: {e}")
        return False

def test_database_connection(db_config):
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['db_user'],
            password=db_config['db_password'],
            database=db_config['db_name']
        )
        conn.close()
        logger.info("数据库连接测试成功")
        return True
    except psycopg2.Error as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

def main():
    """主安装流程"""
    logger.info("开始安装BoomStockAI数据库...")
    
    # 1. 检查PostgreSQL是否已安装
    if not check_postgresql_installed():
        logger.info("PostgreSQL未安装，开始安装...")
        if not install_postgresql():
            logger.error("PostgreSQL安装失败")
            return False
    
    # 2. 创建数据库和用户
    db_config = create_database_and_user()
    if not db_config:
        logger.error("数据库创建失败")
        return False
    
    # 3. 创建环境变量文件
    create_env_file(db_config)
    
    # 4. 更新配置文件
    update_config_file(db_config)
    
    # 5. 安装Python依赖
    if not install_python_dependencies():
        logger.error("Python依赖安装失败")
        return False
    
    # 6. 测试数据库连接
    if not test_database_connection(db_config):
        logger.error("数据库连接测试失败")
        return False
    
    logger.info("数据库安装完成！")
    logger.info("接下来可以运行以下命令初始化数据库:")
    logger.info("python database/stock_database_manager.py --init")
    
    return True

if __name__ == "__main__":
    if not main():
        sys.exit(1) 