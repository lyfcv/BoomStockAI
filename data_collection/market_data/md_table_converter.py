import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime


class MDTableConverter:
    """
    Markdown表格转换器
    用于将股票K线数据转换为Markdown表格格式
    """
    
    def __init__(self):
        # 字段中文映射
        self.field_mapping = {
            'date': '日期',
            'time': '时间',
            'code': '代码',
            'open': '开盘价',
            'high': '最高价',
            'low': '最低价',
            'close': '收盘价',
            'preclose': '前收盘价',
            'volume': '成交量',
            'amount': '成交金额',
            'adjustflag': '复权状态',
            'turn': '换手率(%)',
            'tradestatus': '交易状态',
            'pctChg': '涨跌幅(%)',
            'isST': 'ST状态',
            'peTTM': 'PE(TTM)',
            'psTTM': 'PS(TTM)',
            'pcfNcfTTM': 'PCF(TTM)',
            'pbMRQ': 'PB(MRQ)'
        }
        
        # 数值字段格式化配置
        self.format_config = {
            'open': '{:.4f}',
            'high': '{:.4f}',
            'low': '{:.4f}',
            'close': '{:.4f}',
            'preclose': '{:.4f}',
            'volume': '{:,.0f}',
            'amount': '{:,.2f}',
            'turn': '{:.2f}',
            'pctChg': '{:.2f}',
            'peTTM': '{:.2f}',
            'psTTM': '{:.2f}',
            'pcfNcfTTM': '{:.2f}',
            'pbMRQ': '{:.2f}'
        }
    
    def format_value(self, field: str, value: Any) -> str:
        """
        格式化字段值
        
        Args:
            field (str): 字段名
            value (Any): 字段值
            
        Returns:
            str: 格式化后的值
        """
        if pd.isna(value) or value == '' or value is None:
            return '-'
        
        # 特殊字段处理
        if field == 'adjustflag':
            adjust_map = {'1': '前复权', '2': '后复权', '3': '不复权'}
            return adjust_map.get(str(value), str(value))
        elif field == 'tradestatus':
            status_map = {'1': '正常交易', '0': '停牌'}
            return status_map.get(str(value), str(value))
        elif field == 'isST':
            return 'ST' if str(value) == '1' else '正常'
        
        # 数值格式化
        if field in self.format_config:
            try:
                return self.format_config[field].format(float(value))
            except (ValueError, TypeError):
                return str(value)
        
        return str(value)
    
    def dataframe_to_md_table(self, df: pd.DataFrame, 
                             title: Optional[str] = None,
                             selected_fields: Optional[List[str]] = None,
                             max_rows: Optional[int] = None) -> str:
        """
        将DataFrame转换为Markdown表格
        
        Args:
            df (pd.DataFrame): 要转换的数据
            title (str, optional): 表格标题
            selected_fields (List[str], optional): 选择要显示的字段，None表示显示所有字段
            max_rows (int, optional): 最大显示行数，None表示显示所有行
            
        Returns:
            str: Markdown表格字符串
        """
        if df is None or df.empty:
            return "**数据为空**\n"
        
        # 复制数据避免修改原始数据
        data = df.copy()
        
        # 选择字段
        if selected_fields:
            available_fields = [field for field in selected_fields if field in data.columns]
            if not available_fields:
                return "**所选字段不存在**\n"
            data = data[available_fields]
        
        # 限制行数
        if max_rows and len(data) > max_rows:
            data = data.head(max_rows)
        
        # 构建Markdown表格
        md_lines = []
        
        # 添加标题
        if title:
            md_lines.append(f"## {title}\n")
        
        # 添加数据信息
        total_rows = len(df)
        showing_rows = len(data)
        if max_rows and total_rows > max_rows:
            md_lines.append(f"*显示前 {showing_rows} 条，共 {total_rows} 条数据*\n")
        else:
            md_lines.append(f"*共 {total_rows} 条数据*\n")
        
        # 构建表头
        headers = []
        for col in data.columns:
            chinese_name = self.field_mapping.get(col, col)
            headers.append(chinese_name)
        
        # Markdown表格头部
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # 添加数据行
        for _, row in data.iterrows():
            formatted_row = []
            for col in data.columns:
                formatted_value = self.format_value(col, row[col])
                formatted_row.append(formatted_value)
            md_lines.append("| " + " | ".join(formatted_row) + " |")
        
        return "\n".join(md_lines) + "\n"
    
    def save_to_file(self, md_content: str, filename: str) -> bool:
        """
        将Markdown内容保存到文件
        
        Args:
            md_content (str): Markdown内容
            filename (str): 文件名
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"Markdown表格已保存到: {filename}")
            return True
        except Exception as e:
            print(f"保存文件失败: {str(e)}")
            return False
    
    def convert_k_data_to_md(self, df: pd.DataFrame, 
                           stock_code: str,
                           frequency: str = "d",
                           save_file: Optional[str] = None,
                           selected_fields: Optional[List[str]] = None,
                           max_rows: Optional[int] = 20) -> str:
        """
        将K线数据转换为Markdown表格（便捷方法）
        
        Args:
            df (pd.DataFrame): K线数据
            stock_code (str): 股票代码
            frequency (str): 数据频率
            save_file (str, optional): 保存文件路径
            selected_fields (List[str], optional): 选择显示的字段
            max_rows (int, optional): 最大显示行数
            
        Returns:
            str: Markdown内容
        """
        # 频率映射
        freq_names = {
            "d": "日线", "w": "周线", "m": "月线",
            "5": "5分钟线", "15": "15分钟线", 
            "30": "30分钟线", "60": "60分钟线"
        }
        freq_name = freq_names.get(frequency.lower(), f"{frequency}线")
        
        # 生成标题
        title = f"{stock_code} {freq_name}数据"
        
        # 转换为Markdown
        md_content = self.dataframe_to_md_table(
            df, title=title, 
            selected_fields=selected_fields,
            max_rows=max_rows
        )
        
        # 添加生成时间
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md_content += f"\n*生成时间: {timestamp}*\n"
        
        # 保存文件
        if save_file:
            self.save_to_file(md_content, save_file)
        
        return md_content


def demo_usage():
    """
    演示MD表格转换器的使用
    """
    from history_k_data import get_k_data
    
    print("=== MD表格转换器演示 ===")
    
    # 获取测试数据
    stock_code = 'sh.600000'
    df = get_k_data(stock_code, 10, "d", include_valuation=True)
    
    if df is None:
        print("无法获取测试数据")
        return
    
    # 创建转换器
    converter = MDTableConverter()
    
    # 1. 基本转换
    print("\n1. 基本转换（显示所有字段）:")
    md_content = converter.convert_k_data_to_md(df, stock_code, "d")
    print(md_content)
    
    # # 2. 选择字段转换
    # print("\n2. 选择字段转换:")
    # selected_fields = ['date', 'open', 'high', 'low', 'close', 'volume', 'pctChg']
    # md_content = converter.convert_k_data_to_md(
    #     df, stock_code, "d", 
    #     selected_fields=selected_fields,
    #     max_rows=5
    # )
    # print(md_content)
    
    # # 3. 保存到文件
    # print("\n3. 保存到文件:")
    # filename = f"{stock_code.replace('.', '_')}_k_data.md"
    # converter.convert_k_data_to_md(
    #     df, stock_code, "d",
    #     save_file=filename,
    #     max_rows=10
    # )


if __name__ == "__main__":
    demo_usage() 