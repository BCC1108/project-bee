import pandas as pd
import vectorbt as vbt
from joblib import Memory
import numpy as np
import os


location = 'jlmemory2'
memory = Memory(location , verbose=1)

# 确保 datas 文件夹存在
data_dir = 'datas'
os.makedirs(data_dir, exist_ok=True)

'''=== 信号映射函数==='''
def resamplesig2origion(resamplesig: pd.Series, originalIndex: pd.DatetimeIndex) -> pd.Series:
    
    resamplesig = resamplesig.fillna(False).astype(bool)
    # 提取所有为 True 的信号时间戳
    triggerpoints = resamplesig[resamplesig].index
    if len(triggerpoints) == 0:
        return pd.Series(False, index=originalIndex)

    positions = originalIndex.get_indexer(triggerpoints, method='bfill')
    
    # 过滤掉未匹配项（理论上不会出现，但安全起见）
    valid_positions = positions[positions != -1]
    
    # 构造结果序列
    result = pd.Series(False, index=originalIndex)
    result.iloc[valid_positions] = True
    
    return result


'''======构造df函数===='''
@memory.cache
def make_df(datafilename):
    #print(f"🔍 DEBUG: make_df 正在执行！读取 {datafilename}")  # 只有真正执行时才打印
    data_dir = 'datas'  # 和保存时一致
    full_path = os.path.join(data_dir, datafilename)
    df = pd.read_parquet(full_path ,columns = ['datetime' , 'open' , 'high' , 'low' , 'close' , 'volSWAP'])
    numeric_cols = df.select_dtypes(include=['float64']).columns
    df[numeric_cols] = df[numeric_cols].astype('float32')
    df.rename(columns={'volSWAP': 'volume'} , inplace = True)
    #df = df[::30]
    #df = df[df['datetime'] >= (df['datetime'].max() - pd.Timedelta(days=80))]
    print(df)
    return df


'''======重采样df函数===='''
def resampledf(df: pd.DataFrame, resampleperiod: str) -> pd.DataFrame:
    df.set_index('datetime' , inplace = True)
    dfc = df.resample(resampleperiod).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    return dfc



'''======转换json为parquet函数===='''
def convert_to_parquet(filenames):
    import pandas as pd
    import json

    for file in filenames:
        with open(file) as f:
            data = json.load(f)
            
        df = pd.DataFrame(data ,columns = ['ts' , 'open' , 'high' , 'low' , 'close' , 'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm'])
        cols = ['ts' , 'open' , 'high' , 'low' , 'close' , 'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm']
        df = df[cols].apply(pd.to_numeric , errors = 'coerce')
        df['datetime'] = pd.to_datetime(df['ts'] , unit = 'ms' , utc = True).dt.tz_convert('Asia/Shanghai')
        df = df[::-1].reset_index(drop=True)

        print(df.head(20))
        file_path = os.path.join('datas', f'{file}.parquet')
        df.to_parquet(file_path ,engine = 'pyarrow')





''''易于缓存的数据生成'''
@memory.cache
def getdf(token , resamplenum):
    df = make_df(token)
    dfc = resampledf(df , resamplenum)
    
    return df , dfc



'''信号生成'''
@memory.cache
def generate_signals_for_scanner(stratname:str = 'hq5', filename:str = 'soldata2.parquet' , resampleperiod = '1h' , stratparam:dict = {}):

        name = stratname
        params = stratparam
        df , dfc = getdf(filename, resampleperiod)

        if name == 'hq3':
            #print(f'正在生成 {.name} 策略信号...') 
            window = params.get('window' , 20)
            stddev = params.get('stddev' , 2)         
            #indicators might be used will be defined here
            bbands = vbt.BBANDS.run(dfc['close'],window=20,alpha=2)           
            upperband = bbands.upper                                    #type: ignore
            middleband = bbands.middle                                  #type: ignore
            lowerband = bbands.lower                                    #type: ignore
            
            buysignal = (
                (dfc['low'].shift(2) < lowerband.shift(2)) &           # 第一根下破下轨
                (dfc['close'].shift(1) >  dfc['open'].shift(1)) &           # 第二根是绿线（阳线）
                (dfc['volume'].shift(1) < dfc['volume'].shift(2))           # 第二根缩量
                
            )

            sellsignal = (
                (dfc['high'].shift(2) > upperband.shift(2)) &          # 第一根上穿上轨
                (dfc['close'].shift(1) <  dfc['open'].shift(1)) &           # 第二根是红线（阴线）
                (dfc['volume'].shift(1) <  dfc['volume'].shift(2))          # 第二根缩量
            )
            
            cLongsig =  (dfc['close'].shift(2) >= middleband.shift(2)) & (dfc['close'].shift(1)< middleband.shift(1))    #当前收盘价下穿BOLL中轨
            cShortsig = (dfc['close'].shift(2) <= middleband.shift(2)) & (dfc['close'].shift(1) > middleband.shift(1))    #当前收盘价上破BOLL中轨
            
            long_entries = resamplesig2origion(buysignal, df.index)       #type: ignore
            long_exits = resamplesig2origion(cLongsig, df.index)          #type: ignore
            short_entries = resamplesig2origion(sellsignal, df.index)     #type: ignore
            short_exits = resamplesig2origion(cShortsig, df.index)        #type: ignore
            
            #print(f'{.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif name == 'hq2':
            #print(f'\n正在生成 {.name} 策略信号...')
            window = params.get('window' , 20)
            stddev = params.get('stddev' , 2)
            
            #indicators might be used will be defined here
            bbands = vbt.BBANDS.run(dfc['close'],window=window,alpha=stddev)           
            upperband = bbands.upper                                    #type: ignore
            middleband = bbands.middle                                  #type: ignore
            lowerband = bbands.lower                                    #type: ignore
            
            buysignal = (
                (dfc['low'].shift(2) < lowerband.shift(2)) &                # 第一根下破下轨
                (dfc['close'].shift(1) >  dfc['open'].shift(1)) &           # 第二根是绿线（阳线）
                (dfc['volume'].shift(1) <  dfc['volume'].shift(2))          # 第二根缩量
            )

            sellsignal = (
                (dfc['high'].shift(2) > upperband.shift(2)) &               # 第一根上穿上轨
                (dfc['close'].shift(1) <  dfc['open'].shift(1)) &           # 第二根是红线（阴线）
                (dfc['volume'].shift(1) <  dfc['volume'].shift(2))          # 第二根缩量
            )
            
            cLongsig = sellsignal
            cShortsig = buysignal
            
            long_entries = resamplesig2origion(buysignal, df.index)       #type: ignore
            long_exits = resamplesig2origion(cLongsig, df.index)          #type: ignore
            short_entries = resamplesig2origion(sellsignal, df.index)     #type: ignore
            short_exits = resamplesig2origion(cShortsig, df.index)        #type: ignore
            
            #print(f'{.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif name == 'hq4':
            #print(f'\n正在生成 {.name} 策略信号...')
            
            fast = params.get('fast' , 12)
            slow = params.get('slow' , 26)
            signal = params.get('signal' , 9)
           
            #ema200 = df["close"].ewm(span=200, adjust=False).mean()
            fastema = dfc["close"].ewm(span=fast, adjust=False).mean()
            slowema = dfc["close"].ewm(span=slow, adjust=False).mean()
            macd = fastema - slowema
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            #hist = macd - signal_line
            
            buysignal = (
                (signal_line.shift(2) > macd.shift(2)) &
                (signal_line.shift(1) < macd.shift(1)) &
                (dfc['volume'].shift(1) < dfc['volume'].shift(2))
            )
                
            sellsignal = (
                (signal_line.shift(2) < macd.shift(2)) &
                (signal_line.shift(1) > macd.shift(1)) &
                (dfc['volume'].shift(1) > dfc['volume'].shift(2))
            )
            
            cLongsig = sellsignal
            cShortsig = buysignal
            
            long_entries = resamplesig2origion(buysignal, df.index)          #type: ignore
            long_exits = resamplesig2origion(cLongsig, df.index)             #type: ignore
            short_entries = resamplesig2origion(sellsignal, df.index)        #type: ignore
            short_exits = resamplesig2origion(cShortsig, df.index)           #type: ignore
            
            #print(f'{.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif name == 'hq5':
            #print(f'\n正在生成 {.name} 策略信号...')
            #短期周期
            X1 = params.get('x1' , 3)
            X2 = params.get('x2' , 6)
            X3 = params.get('x3' , 12)
            X4 = params.get('x4' , 24)
            #长期周期
            X5 = params.get('x5' , 10)
            X6 = params.get('x6' , 20)
            X7 = params.get('x7' , 30)
            X8 = params.get('x8' , 60)
            
            # 计算移动平均
            ma1 = dfc['close'].rolling(window=X1).mean()
            ma2 = dfc['close'].rolling(window=X2).mean()
            ma3 = dfc['close'].rolling(window=X3).mean()
            ma4 = dfc['close'].rolling(window=X4).mean()
            
            ma5 = dfc['close'].rolling(window=X5).mean()
            ma6 = dfc['close'].rolling(window=X6).mean()
            ma7 = dfc['close'].rolling(window=X7).mean()
            ma8 = dfc['close'].rolling(window=X8).mean()
            
            # 计算BBI指标
            dfc['S_BBI'] = (ma1 + ma2 + ma3 + ma4) / 4  # 短期BBI
            dfc['M_BBI'] = (ma5 + ma6 + ma7 + ma8) / 4  # 中期BBI
            
            # 计算趋势
            dfc['S_trend'] = np.sign(dfc['S_BBI'].diff())  # 1:上, -1:下
            dfc['M_trend'] = np.sign(dfc['M_BBI'].diff())
            
            # 计算位置关系
            dfc['S_above_M'] = dfc['S_BBI'] > dfc['M_BBI']
            dfc['S_above_M_prev'] = dfc['S_above_M'].shift(1)
            
            # 买点条件
            buysignal = (
                (dfc['S_trend'].shift(1) == 1) &           # 细线向上
                (dfc['M_trend'].shift(1) == 1) &           # 粗线向上
                (dfc['S_above_M'].shift(1) == True) &      # 细线在粗线上方
                (dfc['S_above_M_prev'].shift(1) == False)  # 之前细线在粗线下方
            )
            
            # 卖点条件
            sellsignal = (
                (dfc['S_trend'].shift(1) == -1) &          # 细线向下
                (dfc['M_trend'].shift(1) == -1) &          # 粗线向下
                (dfc['S_above_M'].shift(1) == False) &     # 细线在粗线下方
                (dfc['S_above_M_prev'].shift(1) == True)   # 之前细线在粗线上方
            )
            
            cLongsig = sellsignal
            cShortsig = buysignal
            
            long_entries = resamplesig2origion(buysignal, df.index)          #type: ignore
            long_exits = resamplesig2origion(cLongsig, df.index)             #type: ignore
            short_entries = resamplesig2origion(sellsignal, df.index)        #type: ignore
            short_exits = resamplesig2origion(cShortsig, df.index)           #type: ignore  
            #print(f'{.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif name == 'hq3.5':
            window = params.get('window' , 20)
            stddev = params.get('stddev' , 2)
            bandwithmax = params.get('bandwidthmax' , 0.2)
            bandwithmin = params.get('bandwidthmin' , 0.05)
            
            #indicators might be used will be defined here
            bbands = vbt.BBANDS.run(dfc['close'],window=window,alpha=stddev)           
            upperband = bbands.upper                                    #type: ignore
            middleband = bbands.middle                                  #type: ignore
            lowerband = bbands.lower                                    #type: ignore
            width = (upperband - lowerband) / middleband                #type: ignore
            
            
            buysignal = (
                (dfc['low'].shift(2) < lowerband.shift(2)) &                # 第一根下破下轨
                (dfc['close'].shift(1) >  dfc['open'].shift(1)) &           # 第二根是绿线（阳线）
                (dfc['volume'].shift(1) < dfc['volume'].shift(2))&          # 第二根缩量
                (width.shift(1) < bandwithmax)&                             # 带宽限制
                (width.shift(1) > bandwithmin)                              # 带宽限制
            )

            sellsignal = (
                (dfc['high'].shift(2) > upperband.shift(2)) &               # 第一根上穿上轨
                (dfc['close'].shift(1) <  dfc['open'].shift(1)) &           # 第二根是红线（阴线）
                (dfc['volume'].shift(1) <  dfc['volume'].shift(2))&         # 第二根缩量
                (width.shift(1) < bandwithmax) &                            # 带宽限制
                (width.shift(1) > bandwithmin)                              # 带宽限制
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
            
        
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif name == 'hq3.5.1':
            window = params.get('window' , 20)
            stddev = params.get('stddev' , 2)
            
            #indicators might be used will be defined here
            bbands = vbt.BBANDS.run(dfc['close'],window=window,alpha=stddev)
            bbandss = vbt.BBANDS.run(df['close'],window=window,alpha=stddev)           
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
            
            #low_oc = dfc[['open' , 'close']].min(axis=1)
            #high_oc = dfc[['open' , 'close']].max(axis=1)
            #cross =  middleband.between(low_oc , high_oc)
            cLongsig =  (df['close'].shift(2) >= bbandss.middle.shift(2)) & (df['close'].shift(1) < bbandss.middle.shift(1))    #当前收盘价下穿BOLL中轨  #type: ignore
            cShortsig = (df['close'].shift(2) <= bbandss.middle.shift(2)) & (df['close'].shift(1) > bbandss.middle.shift(1))    #当前收盘价上破BOLL中轨  #type: ignore
            
            long_entries = resamplesig2origion(buysignal, df.index)       #type: ignore
            long_exits = resamplesig2origion(cLongsig, df.index)          #type: ignore
            short_entries = resamplesig2origion(sellsignal, df.index)     #type: ignore
            short_exits = resamplesig2origion(cShortsig, df.index)        #type: ignore
            
            return df , long_entries , long_exits , short_entries , short_exits

        elif name == 'hq3.5.2':
            window = params.get('window' , 20)
            stddev = params.get('stddev' , 2)
            
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
            
            cLongsig =  ((dfc['close'].shift(2) >= middleband.shift(2)) & (dfc['close'].shift(1)< middleband.shift(1)))      #当前收盘价下穿BOLL中轨
            cShortsig = ((dfc['close'].shift(2) <= middleband.shift(2)) & (dfc['close'].shift(1) > middleband.shift(1)))     #当前收盘价上破BOLL中轨
            
            long_entries = resamplesig2origion(buysignal, df.index)       #type: ignore
            long_exits = resamplesig2origion(cLongsig, df.index)          #type: ignore
            short_entries = resamplesig2origion(sellsignal, df.index)     #type: ignore
            short_exits = resamplesig2origion(cShortsig, df.index)        #type: ignore
            
            long_exits = long_exits | long_entries.shift(-1)
            short_exits = short_exits | short_entries.shift(-1)
            
            return df , long_entries , long_exits , short_entries , short_exits