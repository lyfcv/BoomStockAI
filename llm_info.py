from data_collection.market_data.history_k_data import get_k_data
from data_collection.technical_indicators.macd_indicators import calculate_macd
from data_collection.technical_indicators.boll_indicators import calculate_boll
from data_collection.technical_indicators.ma_indicators import calculate_ma
import pandas as pd


def main():
    """获取K线数据并计算MACD、布林带和均线指标"""
    # 支持多种输入格式，现在get_k_data已经支持自动识别
    stock_code = '300739'  # 可以直接输入6位代码，get_k_data会自动识别
    
    # 1. 获取日线数据（get_k_data已经支持自动识别股票代码）
    print("\n1. 获取日线数据（包含估值指标）:")
    daily_data = get_k_data(stock_code, 150, "d", include_valuation=True)  # 增加到150天
    
    if daily_data is not None:
        print(f"原始数据字段: {list(daily_data.columns)}")
        print(f"数据行数: {len(daily_data)}")
        
        # 2. 计算MACD指标
        print("\n2. 计算MACD指标...")
        macd_data = calculate_macd(daily_data, price_column='close')
        
        # 3. 计算布林带指标
        print("\n3. 计算布林带指标...")
        # 在MACD数据基础上计算布林带
        boll_data = calculate_boll(macd_data, price_column='close')
        
        # 4. 计算均线指标（现在使用正确的最小周期要求）
        print("\n4. 计算均线指标（使用正确的最小周期要求）...")
        ma_periods = [5, 10, 20, 30, 60]
        combined_data = calculate_ma(boll_data, price_column='close', periods=ma_periods)
        
        # 5. 显示合并后的数据
        print("\n5. 合并后的数据字段:")
        print(f"所有字段: {list(combined_data.columns)}")
        
        # 检查各均线的有效数据点数量
        print(f"\n6. 各均线有效数据统计:")
        for period in ma_periods:
            ma_col = f'MA{period}'
            valid_count = combined_data[ma_col].notna().sum()
            total_count = len(combined_data)
            print(f"   - {ma_col}: {valid_count}/{total_count} 个有效数据点")
        
        # 选择关键字段显示
        key_columns = [
            'date', 'open', 'high', 'low', 'close', 'volume',
            'MA5', 'MA10', 'MA20', 'MA30', 'MA60',
            'MACD', 'MACD_Signal', 'MACD_Histogram',
            'BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER', 'BOLL_PB'
        ]
        
        # 确保选择的列都存在
        available_columns = [col for col in key_columns if col in combined_data.columns]
        
        print(f"\n7. 关键指标数据（最近10条）:")
        print(combined_data[available_columns].tail(10).to_string(index=False))
        
        # 8. 保存到CSV文件（按日期降序排列）
        # 从combined_data中获取实际的股票代码
        actual_stock_code = combined_data['code'].iloc[0].replace('.', '_')
        output_file = f"{actual_stock_code}_with_all_indicators.csv"
        # 按日期降序排列后保存
        combined_data_sorted = combined_data.sort_values('date', ascending=False)
        combined_data_sorted.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n8. 数据已保存到: {output_file} (按日期降序排列)")
        
        # 9. 显示统计信息
        print(f"\n9. 数据统计信息:")
        print(f"   - 总记录数: {len(combined_data)}")
        print(f"   - 日期范围: {combined_data['date'].min()} 到 {combined_data['date'].max()}")
        print(f"   - 收盘价范围: {combined_data['close'].min():.2f} - {combined_data['close'].max():.2f}")
        
        # 只显示有有效数据的均线统计
        for period in [5, 20, 60]:
            ma_col = f'MA{period}'
            if combined_data[ma_col].notna().any():
                print(f"   - {ma_col}范围: {combined_data[ma_col].min():.2f} - {combined_data[ma_col].max():.2f}")
            else:
                print(f"   - {ma_col}: 无有效数据（数据不足{period}天）")
        
        print(f"   - MACD范围: {combined_data['MACD'].min():.4f} - {combined_data['MACD'].max():.4f}")
        print(f"   - 布林带宽度范围: {(combined_data['BOLL_UPPER'] - combined_data['BOLL_LOWER']).min():.2f} - {(combined_data['BOLL_UPPER'] - combined_data['BOLL_LOWER']).max():.2f}")
        
        # 10. 显示均线排列情况（最新数据）- 只显示有效的均线
        latest_data = combined_data.iloc[-1]
        print(f"\n10. 最新均线排列情况 ({latest_data['date']}):")
        print(f"    - 收盘价: {latest_data['close']:.2f}")
        
        valid_mas = []
        for period in ma_periods:
            ma_col = f'MA{period}'
            if pd.notna(latest_data[ma_col]):
                print(f"    - {ma_col}:   {latest_data[ma_col]:.2f}")
                valid_mas.append((period, latest_data[ma_col]))
            else:
                print(f"    - {ma_col}:   N/A (数据不足{period}天)")
        
        # 判断均线排列（只使用有效的均线）
        if len(valid_mas) >= 4:
            # 按周期排序
            valid_mas.sort(key=lambda x: x[0])
            values = [x[1] for x in valid_mas[:4]]  # 取前4个均线
            
            if all(values[i] > values[i+1] for i in range(len(values)-1)):
                print("    - 均线排列: 多头排列 📈")
            elif all(values[i] < values[i+1] for i in range(len(values)-1)):
                print("    - 均线排列: 空头排列 📉")
            else:
                print("    - 均线排列: 混乱排列 ↔️")
        else:
            print("    - 均线排列: 数据不足，无法判断")
        
        return combined_data
        
    else:
        print("获取数据失败!")
        return None


def test_multiple_stocks():
    """测试多个股票的技术指标计算"""
    test_stocks = ['600000', '000001', '300787', '688001']
    
    print("=== 测试多个股票的技术指标计算 ===")
    for stock in test_stocks:
        print(f"\n{'='*50}")
        print(f"正在处理股票: {stock}")
        print(f"{'='*50}")
        
        # 临时修改stock_code进行测试
        global stock_code
        original_code = '300787'  # 保存原值
        
        # 这里可以调用main函数的逻辑，但为了简化，只获取数据
        data = get_k_data(stock, 10, "d", include_valuation=True)
        if data is not None:
            print(f"✅ 成功获取 {stock} 的数据，共 {len(data)} 条记录")
        else:
            print(f"❌ 获取 {stock} 的数据失败")


if __name__ == "__main__":
    # 运行主程序
    result = main()
    
    # 可选：测试多个股票
    # test_multiple_stocks()