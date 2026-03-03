import okx.MarketData as MarketData
from datetime import datetime , timezone
import time
import pandas as pd


flag = "0"  # 实盘:0 , 模拟盘：1
marketDataAPI =  MarketData.MarketAPI(flag=flag)

# 获取交易产品历史K线数据
def get_candles(instId: str = 'BTC-USDT-SWAP' , bar: str = '1s' , after: str = '' , limit: str = '300' ):
    result = marketDataAPI.get_history_candlesticks(
        instId= instId,
        bar = bar,
        after = after,
        limit = limit
    )
    
    datapart = result.get('data')
    return datapart

time_now_utc = datetime.now(timezone.utc)
ts_now = int(time.time()) * 1000

ph = 0.25
pms = ph * 60 * 60 * 1000
ts_run = ts_now

n = 1
an = pms / 300000

data = []
while an - n >= 0:
    print(f'正在进行第{n}/{an}次获取')
    dp = get_candles(after = str(ts_run))
    ts_run = ts_run - 300000
    n = n + 1
    data.extend(dp) 
        
df = pd.DataFrame(data , columns=['ts' , 'open' , 'high' , 'low' , 'close' , 'vol' ,'volBTC' , 'volUSDT' ,'confirm'])
colums = ['ts' , 'open' , 'high' , 'low' , 'close' , 'vol' ,'volBTC' , 'volUSDT' ,'confirm']
df = df[colums].apply(pd.to_numeric , errors='coerce')
df['ts'] = pd.to_datetime(df['ts'], unit='ms')
df = df[::-1].reset_index(drop=True)

print(df)