from core.commonFunctions import make_df , resampledf , resamplesig2origion
import pandas as pd
from core.strategyBook import Strategy
import vectorbt as vbt
import sys
from contextlib import redirect_stdout
from tqdm import tqdm

df = make_df('soldata.parquet')

print(df)
print(df['datetime'].dtype)


#提取日期部分
df['date'] = df['datetime'].dt.date

# 获取所有唯一日期（已排序）
unique_dates = pd.Series(sorted(df['date'].unique()))
print(f"总天数: {len(unique_dates)}")  # 应该是 500

window_days = 10
step_days = 10

rolling_dfs = []

for i in range(0 , len(unique_dates) - window_days + 1 , step_days):   # 注意：range(start, stop, step)
    start_date = unique_dates.iloc[i]
    end_date = unique_dates.iloc[i + window_days - 1]
    
    mask = (df['date']>=start_date) & (df['date']<=end_date)
    chunk = df[mask].copy()
    
    rolling_dfs.append(chunk)

#del rolling_dfs[0]
#del rolling_dfs[-1]
print(f'成功生成{len(rolling_dfs)}个滚动窗口')

# 第一个窗口
first = rolling_dfs[0]
print("First window:")
print(f"  Date range: {first['date'].min()} to {first['date'].max()}")
print(f"  Time range: {first['datetime'].min()} to {first['datetime'].max()}")
print(f"  Rows: {len(first)}")

second = rolling_dfs[1]
print("\nSecond window:")
print(f"  Date range: {second['date'].min()} to {second['date'].max()}")
print(f"  Time range: {second['datetime'].min()} to {second['datetime'].max()}")
print(f"  Rows: {len(second)}")

# 最后一个窗口
last = rolling_dfs[-1]
print("\nLast window:")
print(f"  Date range: {last['date'].min()} to {last['date'].max()}")
print(f"  Time range: {last['datetime'].min()} to {last['datetime'].max()}")
print(f"  Rows: {len(last)}")

# 检查是否真的是 10 天
#assert len(rolling_dfs) == len(rolling_dfs)-10+1-2, f"Expected {len(rolling_dfs)-10+1-2} windows, got {len(rolling_dfs)}"




    
#逐个回测
teststrat = Strategy(name='hq3.5' , description='hq3变种, 矩形平仓' , params={'window':20 , 'stddev':2})
teststrat.original_freq = '1s'    #原始数据周期
teststrat.sLrate = 0.08
teststrat.tPrate = 0.08

def generatesigstt(df,dfc):
        print(f'\n正在生成{teststrat.name}策略信号...')
        window = teststrat.params.get('window' , 20)
        stddev = teststrat.params.get('stddev' , 2)
        
        #indicators might be used will be defined here
        bbands = vbt.BBANDS.run(dfc['close'],window=window,alpha=stddev)           
        upperband = bbands.upper                                    #type: ignore
        middleband = bbands.middle                                  #type: ignore
        lowerband = bbands.lower                                    #type: ignore
        
        buysignal = (
            (dfc['low'].shift(2) < lowerband.shift(2)) &                # 第一根下破下轨
            (dfc['close'].shift(1) >  dfc['open'].shift(1)) &           # 第二根是绿线（阳线）
            (dfc['volume'].shift(1) < dfc['volume'].shift(2))           # 第二根缩量
            
        )

        sellsignal = (
            (dfc['high'].shift(2) > upperband.shift(2)) &               # 第一根上穿上轨
            (dfc['close'].shift(1) <  dfc['open'].shift(1)) &           # 第二根是红线（阴线）
            (dfc['volume'].shift(1) <  dfc['volume'].shift(2))          # 第二根缩量
        )
        
        low_oc = dfc[['open' , 'close']].min(axis=1)
        high_oc = dfc[['open' , 'close']].max(axis=1)
        cross =  middleband.between(low_oc , high_oc)
        cLongsig =  cross.shift(1)
        cShortsig = cross.shift(1)
        
        long_entries = resamplesig2origion(buysignal, df.index)       #type: ignore
        long_exits = resamplesig2origion(cLongsig, df.index)          #type: ignore
        short_entries = resamplesig2origion(sellsignal, df.index)     #type: ignore
        short_exits = resamplesig2origion(cShortsig, df.index)        #type: ignore
        
        print(f'{teststrat.name} 策略信号生成完毕.')
        return df , long_entries , long_exits , short_entries , short_exits

pbar = tqdm(desc = f'正在分段回测数据' ,
                total = len(rolling_dfs) , 
                position= 0 , 
                unit = '组' , 
                leave = True ,
                bar_format='{desc}: {percentage:.2f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
with open('output.txt' , 'w' , encoding='utf-8') as f:
        with redirect_stdout(f):
            for df in rolling_dfs:
                df = df
                dfc = resampledf(df , '1h')
                sigs = generatesigstt(df,dfc)
                teststrat.vbt_backtest(*sigs , plot = False)         #type: ignore
                
                pbar.update(1)
    
pbar.close()
