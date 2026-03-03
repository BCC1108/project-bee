import okx.MarketData as MarketData
from datetime import datetime , timezone
import time
from tqdm import tqdm
import os
import pandas as pd


#====全局变量====
tokenlist = ['BTC-USDT-SWAP' , 'ETH-USDT-SWAP' , 'SOL-USDT-SWAP']   #欲下载的币种列表
downloadperiod = 500              #天计


flag = "0"  # 实盘:0 , 模拟盘：1
marketDataAPI =  MarketData.MarketAPI(flag=flag)


# 获取交易产品历史K线数据
def get_candles(instId: str , bar: str = '1m' , after: str = '' , limit: str = '300' ):
    try:
        result = marketDataAPI.get_history_candlesticks(
            instId= instId,
            bar = bar,
            after = after,
            limit = limit
        )
        
        datapart = result.get('data')
        time.sleep(0.1)
        return datapart
    
    except Exception as e:
        pbar.write(f"❌ 获取 OKX K 线失败: {e}")
        return 'Failed'
    
    
'''创建文件夹'''
# 指定你想存放数据的文件夹名，例如 'data'
data_folder = 'datas'

# 创建文件夹（exist_ok=True 表示如果已存在就不报错）
os.makedirs(data_folder, exist_ok=True)         

'''开始循环获取''' 
for token in tokenlist:
    instId = token
    savefilename = f'{token.split('-')[0].lower()}dataMin'       
    ph = 24 * downloadperiod
    pms = ph * 60 * 60 * 1000

    now = datetime.now(timezone.utc)
    ts_now = int(time.time()) * 1000

    ts_run = ts_now
    ms_left = pms

    data = []
    pbar = tqdm(desc = f'正在下载{instId}币类{downloadperiod}日数据' ,
                total = pms , 
                position= 0 , 
                unit = 'ms' , 
                leave = True ,
                bar_format='{desc}: {percentage:.2f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')

    while ms_left >= 300000 :
        datapart = get_candles(instId = instId , after = str(ts_run))
        
        if datapart == 'Failed':
            pbar.write('重新获取')
            time.sleep(1)
            datapart = get_candles(instId=instId ,after = str(ts_run))
            continue
        
        elif datapart is None:
            pbar.write('没有如此早的数据')
            break 
        
        elif datapart:
            if len(datapart) < 288:
                pbar.write('没有更旧的数据了')
                break
            
            else:
                data.extend(datapart)
                pbar.update(300000*60) 
                
                ts_run = ts_run - 300000*60
                ms_left = ms_left - 300000*60
                

    pbar.close()
    
    print(f'成功下载 {len(data)} 条kline数据.')
    
    '''df&parquet处理'''
    df = pd.DataFrame(data , columns= ['ts' , 'open' , 'high' , 'low' , 'close' , 'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm'])
    cols = ['ts' , 'open' , 'high' , 'low' , 'close' , 'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm']
    df = df[cols].apply(pd.to_numeric , errors = 'coerce')
    df['datetime'] = pd.to_datetime(df['ts'] , unit = 'ms' , utc = True).dt.tz_convert('Asia/Shanghai')
    df = df[::-1].reset_index(drop=True)
    
    print('数据样例')
    print(df)
    file_path = os.path.join(data_folder, f'{savefilename}.parquet')
    df.to_parquet(file_path ,engine = 'pyarrow')
    print(f'结果已成功保存至{savefilename}.parquet')

input("\n按回车键退出...")

