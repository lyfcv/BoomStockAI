#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MD表格转换器使用示例
演示如何将K线数据转换为Markdown表格
"""

from history_k_data import get_k_data
from md_table_converter import MDTableConverter


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 1. 获取K线数据
    stock_code = 'sh.600873'  # 梅花生物
    df = get_k_data(stock_code, 5, "d", include_valuation=True)
    
    if df is None:
        print("获取数据失败")
        return
    
    # 2. 创建转换器
    converter = MDTableConverter()
    
    # 3. 转换为Markdown表格
    md_content = converter.convert_k_data_to_md(df, stock_code, "d")
    
    # 4. 输出结果
    print(md_content)


def example_custom_fields():
    """自定义字段示例"""
    print("=== 自定义字段示例 ===")
    
    # 获取数据
    stock_code = 'sh.600873'
    df = get_k_data(stock_code, 10, "d", include_valuation=True)
    
    if df is None:
        print("获取数据失败")
        return
    
    # 创建转换器
    converter = MDTableConverter()
    
    # 只显示核心价格和成交量数据
    selected_fields = [
        'date', 'open', 'high', 'low', 'close', 
        'volume', 'pctChg', 'turn'
    ]
    
    md_content = converter.convert_k_data_to_md(
        df, stock_code, "d",
        selected_fields=selected_fields,
        max_rows=7
    )
    
    print(md_content)


def example_save_to_file():
    """保存到文件示例"""
    print("=== 保存到文件示例 ===")
    
    # 获取数据
    stock_code = 'sh.600873'
    df = get_k_data(stock_code, 15, "d", include_valuation=False)
    
    if df is None:
        print("获取数据失败")
        return
    
    # 创建转换器
    converter = MDTableConverter()
    
    # 生成文件名
    filename = f"reports/{stock_code.replace('.', '_')}_daily_report.md"
    
    # 转换并保存
    md_content = converter.convert_k_data_to_md(
        df, stock_code, "d",
        save_file=filename,
        max_rows=10
    )
    
    print(f"报告已保存到: {filename}")
    print("预览:")
    print(md_content[:500] + "...")


def example_different_frequencies():
    """不同频率数据示例"""
    print("=== 不同频率数据示例 ===")
    
    stock_code = 'sh.600873'
    converter = MDTableConverter()
    
    # 周线数据
    print("\n--- 周线数据 ---")
    weekly_df = get_k_data(stock_code, 4, "w")
    if weekly_df is not None:
        md_content = converter.convert_k_data_to_md(
            weekly_df, stock_code, "w",
            selected_fields=['date', 'open', 'high', 'low', 'close', 'volume'],
            max_rows=4
        )
        print(md_content)
    
    # 月线数据  
    print("\n--- 月线数据 ---")
    monthly_df = get_k_data(stock_code, 3, "m")
    if monthly_df is not None:
        md_content = converter.convert_k_data_to_md(
            monthly_df, stock_code, "m",
            selected_fields=['date', 'open', 'high', 'low', 'close', 'volume'],
            max_rows=3
        )
        print(md_content)


def example_direct_dataframe_conversion():
    """直接DataFrame转换示例"""
    print("=== 直接DataFrame转换示例 ===")
    
    # 获取数据
    stock_code = 'sh.600873'
    df = get_k_data(stock_code, 8, "d")
    
    if df is None:
        print("获取数据失败")
        return
    
    # 创建转换器
    converter = MDTableConverter()
    
    # 直接使用dataframe_to_md_table方法
    md_content = converter.dataframe_to_md_table(
        df,
        title="自定义标题 - 股票数据分析",
        selected_fields=['date', 'close', 'volume', 'pctChg'],
        max_rows=5
    )
    
    print(md_content)


if __name__ == "__main__":
    # 创建reports目录（如果不存在）
    import os
    os.makedirs("reports", exist_ok=True)
    
    # 运行所有示例
    example_basic_usage()
    print("\n" + "="*60 + "\n")
    
    example_custom_fields()
    print("\n" + "="*60 + "\n")
    
    example_save_to_file()
    print("\n" + "="*60 + "\n")
    
    example_different_frequencies()
    print("\n" + "="*60 + "\n")
    
    example_direct_dataframe_conversion()
    
    print("\n=== 所有示例运行完成 ===") 