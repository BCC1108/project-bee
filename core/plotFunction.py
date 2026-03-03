from dash import Dash, dcc, html, callback, Output, Input
import plotly.graph_objects as go
import pandas as pd
import pyarrow.parquet as pq
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc


PRICE_FILE = None
ORDERS_FILE = None
TRADES_FILE = None


def create_app():
    #Initialize the App
    external_stylesheets = [dbc.themes.CERULEAN]
    app = Dash(__name__, external_stylesheets=external_stylesheets)

    #set the layout
    app.layout = dbc.Container([
        dbc.Row([
            html.Div([
                dcc.Graph(
                    id='k Lines Graph',
                    config={'scrollZoom': False},  # True允许用户鼠标缩放
                    figure={},                    # 初始为空，靠回调填充
                    style={'height': '1000px'} 
                )])
        ])
    ],fluid = True)

    #装饰器
    @callback(
        Output('k Lines Graph', 'figure'),
        Input('k Lines Graph', 'relayoutData'),            #relayoutData记录当前看到的时间方位
        prevent_initial_call=False                         # 允许页面加载时触发一次
    )

    #更新图表
    def update_chart(relayout_data):
        '''优先计算最近7天范围'''
        end_ms = pd.read_parquet(PRICE_FILE, columns=['ts'])['ts'].iloc[-1]           #type: ignore
        start_ms = pd.read_parquet(PRICE_FILE, columns=['ts'])['ts'].iloc[0]          #type: ignore

        if relayout_data and 'xaxis.range[0]' in relayout_data:   

            start_str = relayout_data['xaxis.range[0]']
            end_str = relayout_data['xaxis.range[1]']

            #print(start_str)
            #print(end_str)
            
            # 转换为 pandas Timestamp
            start_ts = pd.to_datetime(start_str).tz_localize('Asia/Shanghai')
            end_ts = pd.to_datetime(end_str).tz_localize('Asia/Shanghai')
            
            # 获取毫秒时间戳
            start_ms = int(start_ts.timestamp() * 1000)
            end_ms = int(end_ts.timestamp() * 1000)

            #print(start_ms)
            #print(end_ms)

        try:
            df_slice = pd.read_parquet(
                PRICE_FILE,                             #type: ignore
                filters=[
                    ('ts', '>=', start_ms),
                    ('ts', '<=', end_ms)
                ],
                columns=['datetime' , 'open', 'high', 'low', 'close', 'volSWAP']
            )
        
        except Exception as e:
            print("❌ Parquet 读取失败:", e)
            return go.Figure()

        if df_slice.empty:
            print("⚠️ 间距过小")
            return go.Figure()

        MAX_POINTS = 400
        if len(df_slice) > MAX_POINTS:
            temp_df = df_slice.copy()
            temp_df.set_index('datetime', inplace=True)
            total_seconds = (temp_df.index.max() - temp_df.index.min()).total_seconds()
            convert_dict = [60 , 300 , 1800 , 10800 , 86400]
            ideal_freq = total_seconds / MAX_POINTS

            freq = 86400
            for period in convert_dict:
                if period >= ideal_freq:
                    freq = period
                    break
                
            rule = f'{freq}s'
            agg_df = temp_df.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volSWAP': 'sum'
            }).reset_index()
        
            plot_df = agg_df
        else:
            plot_df = df_slice

        '''开始绘图'''         
        fig = make_subplots(
            rows = 3,
            cols = 1,
            shared_xaxes = True,
            vertical_spacing = 0.02,
            row_heights = [0.7, 0.2, 0.1]
        )
        
        '''绘制k线图'''
        fig.add_trace(
            go.Candlestick(
                x=plot_df['datetime'],
                open=plot_df['open'],
                high=plot_df['high'],
                low=plot_df['low'],
                close=plot_df['close'],
                
                name='K线',
                line=dict(width=2)
            ),
                row = 1 , col = 1
            )
        
        '''添加成交量子图'''
        fig.add_trace(
            go.Bar(
                x = plot_df['datetime'],
                y = plot_df['volSWAP'],
                name = '成交量(合约张数)' ,
                marker_color = 'blue'
            ),  row = 2 , col = 1 )

        '''在此处添加订单买卖点'''
        orders = pd.read_parquet(ORDERS_FILE)          #type: ignore

        buys = orders[(orders['Side'] == 'Buy') & 
                    (orders['Timestamp'] >= plot_df['datetime'].min()) &
                    (orders['Timestamp'] <= plot_df['datetime'].max())]
        sells = orders[(orders['Side'] == 'Sell') & 
                    (orders['Timestamp'] >= plot_df['datetime'].min()) &
                    (orders['Timestamp'] <= plot_df['datetime'].max())]

        if not buys.empty:
            fig.add_trace(
                go.Scatter(
                    x=buys['Timestamp'],
                    y=buys['Price'],
                    mode='markers',
                    marker=dict(color='purple', size=12, symbol='triangle-up'),
                    name='Buy'
            ),      row = 1 , col = 1 )

        if not sells.empty:
            fig.add_trace(
                go.Scatter(
                    x=sells['Timestamp'],
                    y=sells['Price'],
                    mode='markers',
                    marker=dict(color='blue', size=12, symbol='triangle-down'),
                    name='Sell'
            ),      row = 1 , col = 1 )

        '''添加净值曲线变化图'''
        trade_df = pd.read_parquet(TRADES_FILE)           #type: ignore
 
        mask = (trade_df['Exit Timestamp'] >= plot_df['datetime'].min()) & \
        (trade_df['Exit Timestamp'] <= plot_df['datetime'].max())
        filtered_trades = trade_df[mask]

        colors = ['orangered' if pnl < 0 else 'royalblue' for pnl in filtered_trades['PnL']]
        fig.add_trace(
            go.Scatter(
                x=filtered_trades['Exit Timestamp'],
                y=filtered_trades['PnL'],  # 或 filtered_trades['PnL']
                mode='markers',
                name='PnL',
                marker=dict(
                    color=colors,  # 使用颜色列表
                    line=dict(width=1, color='DarkSlateGrey'))
                ), row=3, col=1 )
        

        fig.update_layout(
            xaxis_rangeslider_visible=False,  
            uirevision='none'
        )
        
        return fig
    
    return app


def plot_backtest(price_file, orders_file, trades_file, port=8050, debug=False):
    """
    启动 Dash 可视化服务器，展示回测结果。
    
    参数:
        price_file (str): 行情数据文件路径（含 datetime, open, high, low, close, volSWAP, ts)
        orders_file (str): 订单文件路径（含 Timestamp, Price, Side)
        trades_file (str): 交易记录文件路径（含 Exit Timestamp, PnL)
        port (int): Web 服务端口，默认 8050
        debug (bool): 是否开启调试模式
    """
    global PRICE_FILE, ORDERS_FILE, TRADES_FILE
    PRICE_FILE = price_file
    ORDERS_FILE = orders_file
    TRADES_FILE = trades_file

    app = create_app()
    print(f"🚀 正在绘图....")
    app.run(debug=debug, port=port)
    

if __name__ == '__main__':
    # 示例：用默认文件启动
    plot_backtest(
        price_file='database/rowdatas/ethdata.parquet',
        orders_file='database/plotdatas/ordersplotting.parquet',
        trades_file='database/plotdatas/tradesplotting.parquet',
        debug=False
    )