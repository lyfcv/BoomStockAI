"""
BoomStockAI - 智能选股系统
版本: 1.0.0
作者: BoomStockAI Team
"""

__version__ = "1.0.0"
__author__ = "BoomStockAI Team"
__email__ = "support@boomstockai.com"
__description__ = "智能选股+量化研究一体化解决方案"

# 项目元信息
PROJECT_NAME = "BoomStockAI"
PROJECT_VERSION = __version__
PROJECT_DESCRIPTION = __description__

# 导入主要模块
try:
    from database.db_utils import db_manager, stock_dao, news_dao
    from data_collection.market_data.baostock_api import baostock_api
    
    __all__ = [
        'db_manager',
        'stock_dao', 
        'news_dao',
        'baostock_api'
    ]
except ImportError:
    # 如果导入失败，说明依赖未安装
    __all__ = [] 