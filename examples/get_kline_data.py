import okx.MarketData as MarketData
import pandas as pd

flag = "0"  # 实盘:0 , 模拟盘：1

marketDataAPI =  MarketData.MarketAPI(flag=flag)

# 获取交易产品K线数据
result = marketDataAPI.get_candlesticks(
    instId="BTC-USDT",
    bar = "15m",
    limit = 100 # type: ignore
)

#检查是否成功

if result['code'] != '0':
    print("获取K线数据失败")
else:
    print("获取K线数据成功")

    klines = result['data']

    #转换为DataFrame
    df = pd.DataFrame(klines, columns=[
        'timeStart' , 'openPrice' , 'High' , 'Low' , 'closePrice' , 'volume' , 'volume(coin)' , 'volume(currency)' , 'confirmed'
    ])

    #转换为数值格式
    for col in ['openPrice' , 'High' , 'Low' , 'closePrice' , 'volume' , 'volume(coin)' , 'volume(currency)']:
        df[col] = pd.to_numeric(df[col])
    
    #转换时间戳为日期时间格式
    df['timeStart'] = pd.to_datetime(df['timeStart'].astype(int), unit='ms')

    # ✅ 新增：设置时区为 UTC，然后转换为 UTC+8（北京时间）
    df['timeStart'] = df['timeStart'].dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')  #type: ignore

    # 按时间正序排列（API 默认是倒序：最新在前）
    df = df.sort_values("timeStart").reset_index(drop=True)

    #计算MACD指标
    shoupan = df['closePrice']

    #快线
    ema12 = shoupan.ewm(span=12, adjust=False).mean()
    ema26 = shoupan.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26

    #信号线
    sig = dif.ewm(span=9, adjust=False).mean()

    #柱状图 = 快线-信号线
    hist = dif - sig

    #保存到df
    df['macd_dif'] = dif
    df['macd_sig'] = sig
    df['macd_hist'] = hist


    #打印结果
    print("最近100条K线数据及MACD指标：")
    print(df[['timeStart', 'closePrice', 'macd_dif', 'macd_sig', 'macd_hist']].head(100).to_markdown(
        index=False,
        headers=['timeStart', 'closePrice', 'MACD_DIF', 'MACD_SIG', 'MACD_HIST'],
        tablefmt='grid',
        stralign='center',
        floatfmt='.4f'
    ))

