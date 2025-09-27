from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import tushare as ts
import pandas as pd
import json
import numpy as np
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 设置tushare API token
TUSHARE_TOKEN = "21ac6ac27ce237f8f39ffc245fc44039df36a8f2e79bb586f0ed5d2d"
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

def get_stock_basic_info():
    """获取股票基本信息"""
    try:
        # 获取股票基本信息
        stock_basic = pro.stock_basic(exchange='',
                                    list_status='L',
                                    fields='ts_code,symbol,name,area,industry,list_date')
        return stock_basic
    except Exception as e:
        print(f"获取股票基本信息失败: {e}")
        return None

def get_latest_trade_date():
    """获取最近的交易日"""
    try:
        # 获取最近10天，找到有数据的交易日
        for i in range(10):
            test_date = (datetime.now() - pd.Timedelta(days=i)).strftime('%Y%m%d')
            try:
                # 测试获取任意一只股票的数据
                test_df = pro.daily(ts_code='000001.SZ', trade_date=test_date)
                if not test_df.empty:
                    return test_date
            except:
                continue
        return None
    except Exception as e:
        print(f"获取最近交易日失败: {e}")
        return None

def get_daily_data(ts_code, trade_date=None):
    """获取日行情数据"""
    try:
        if trade_date is None:
            trade_date = get_latest_trade_date()

        if trade_date is None:
            return None

        df = pro.daily(ts_code=ts_code, trade_date=trade_date)
        return df
    except Exception as e:
        print(f"获取日行情数据失败: {e}")
        return None

def get_stock_basic_stats(ts_code, trade_date=None):
    """获取股票基本统计数据"""
    try:
        if trade_date is None:
            trade_date = get_latest_trade_date()

        if trade_date is None:
            return None

        # 获取日线行情数据
        daily_df = pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
        return daily_df
    except Exception as e:
        print(f"获取基本统计数据失败: {e}")
        return None

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/stock_detail/<stock_code>')
def stock_detail(stock_code):
    """股票详情页"""
    return render_template('stock_detail.html', stock_code=stock_code)

@app.route('/api/stocks')
def get_all_stocks():
    """获取所有股票列表API"""
    try:
        # 获取最近的交易日
        latest_trade_date = get_latest_trade_date()
        if latest_trade_date is None:
            return jsonify({"error": "无法获取最近交易日数据"}), 500

        print(f"使用交易日期: {latest_trade_date}")

        # 获取股票基本信息
        stock_basic = get_stock_basic_info()
        if stock_basic is None or stock_basic.empty:
            return jsonify({"error": "无法获取股票基本信息"}), 500

        stocks_data = []

        try:
            # 批量获取所有股票的日行情数据
            print("正在获取批量日行情数据...")
            all_daily_df = pro.daily(trade_date=latest_trade_date)

            # 批量获取基本统计数据
            print("正在获取批量基本统计数据...")
            all_basic_df = pro.daily_basic(trade_date=latest_trade_date)

            # 将数据转换为字典以便快速查找
            daily_dict = {}
            if all_daily_df is not None and not all_daily_df.empty:
                for _, row in all_daily_df.iterrows():
                    daily_dict[row['ts_code']] = row

            basic_dict = {}
            if all_basic_df is not None and not all_basic_df.empty:
                for _, row in all_basic_df.iterrows():
                    basic_dict[row['ts_code']] = row

            # 获取所有A股的详细数据
            for idx, row in stock_basic.iterrows():
                ts_code = row['ts_code']

                try:
                    # 从批量数据中获取对应股票的数据
                    daily_row = daily_dict.get(ts_code)
                    basic_row = basic_dict.get(ts_code)

                    if daily_row is not None:
                        # 获取基本统计数据
                        market_value = 0
                        ttm = 0
                        volume_ratio = 0

                        if basic_row is not None:
                            market_value = basic_row.get('total_mv', 0)  # 总市值（万元）
                            ttm = basic_row.get('pe_ttm', 0)  # TTM市盈率
                            volume_ratio = basic_row.get('volume_ratio', 0)  # 量比

                        # 处理NaN值
                        def safe_float(value, default=0):
                            if pd.isna(value) or np.isnan(value) if isinstance(value, (int, float)) else False:
                                return default
                            return float(value) if value is not None else default

                        # 计算涨跌幅
                        change_pct = safe_float(daily_row.get('pct_chg', 0))

                        stock_info = {
                            'id': idx + 1,
                            'stock_code': row['symbol'],
                            'ts_code': ts_code,
                            'stock_name': row['name'],
                            'current_price': safe_float(daily_row.get('close', 0)),
                            'change_pct': change_pct,
                            'volume_ratio': safe_float(volume_ratio),
                            'market_value': safe_float(market_value),
                            'ttm': safe_float(ttm),
                            'is_up': change_pct > 0
                        }
                        stocks_data.append(stock_info)

                except Exception as e:
                    print(f"处理股票 {ts_code} 数据失败: {e}")
                    continue

        except Exception as e:
            print(f"批量获取数据失败: {e}")
            # 如果批量获取失败，返回基本信息
            for idx, row in stock_basic.iterrows():
                stock_info = {
                    'id': idx + 1,
                    'stock_code': row['symbol'],
                    'ts_code': row['ts_code'],
                    'stock_name': row['name'],
                    'current_price': 0,
                    'change_pct': 0,
                    'volume_ratio': 0,
                    'market_value': 0,
                    'ttm': 0,
                    'is_up': False
                }
                stocks_data.append(stock_info)

        return jsonify(stocks_data)

    except Exception as e:
        print(f"获取股票数据失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_stock/<keyword>')
def search_stock(keyword):
    """搜索股票API"""
    try:
        stock_basic = get_stock_basic_info()
        if stock_basic is None:
            return jsonify({"error": "无法获取股票信息"}), 500

        # 搜索股票代码或名称包含关键词的股票
        result = stock_basic[
            (stock_basic['symbol'].str.contains(keyword, na=False)) |
            (stock_basic['name'].str.contains(keyword, na=False))
        ]

        if result.empty:
            return jsonify({"message": "未找到相关股票"}), 404

        # 获取第一个匹配的股票详细信息
        stock_info = result.iloc[0]
        ts_code = stock_info['ts_code']

        # 获取最新交易日数据
        latest_trade_date = get_latest_trade_date()
        daily_df = get_daily_data(ts_code, latest_trade_date)
        basic_df = get_stock_basic_stats(ts_code, latest_trade_date)

        response_data = {
            'stock_code': stock_info['symbol'],
            'ts_code': ts_code,
            'stock_name': stock_info['name'],
            'industry': stock_info.get('industry', ''),
            'area': stock_info.get('area', ''),
        }

        # 处理NaN值的辅助函数
        def safe_float(value, default=0):
            if pd.isna(value) or np.isnan(value) if isinstance(value, (int, float)) else False:
                return default
            return float(value) if value is not None else default

        if daily_df is not None and not daily_df.empty:
            daily_row = daily_df.iloc[0]
            response_data.update({
                'current_price': safe_float(daily_row.get('close', 0)),
                'change_pct': safe_float(daily_row.get('pct_chg', 0)),
                'volume': safe_float(daily_row.get('vol', 0)),
                'amount': safe_float(daily_row.get('amount', 0)),
            })

        if basic_df is not None and not basic_df.empty:
            basic_row = basic_df.iloc[0]
            response_data.update({
                'market_value': safe_float(basic_row.get('total_mv', 0)),
                'ttm': safe_float(basic_row.get('pe_ttm', 0)),
                'volume_ratio': safe_float(basic_row.get('volume_ratio', 0)),
            })

        return jsonify(response_data)

    except Exception as e:
        print(f"搜索股票失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock_history/<ts_code>')
def get_stock_history(ts_code):
    """获取股票历史数据API（近20个交易日）"""
    try:
        # 获取近30天数据，确保有20个交易日
        df = pro.daily(ts_code=ts_code,
                      start_date=(datetime.now() - pd.Timedelta(days=30)).strftime('%Y%m%d'),
                      end_date=datetime.now().strftime('%Y%m%d'))

        if df is None or df.empty:
            return jsonify({"error": "无法获取历史数据"}), 500

        # 按日期排序并取最近20个交易日
        df = df.sort_values('trade_date').tail(20)

        history_data = []
        for _, row in df.iterrows():
            history_data.append({
                'date': row['trade_date'],
                'close': row['close'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'volume': row['vol'],
                'pct_chg': row.get('pct_chg', 0)  # 涨跌幅
            })

        return jsonify(history_data)

    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)