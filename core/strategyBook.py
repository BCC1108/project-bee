from sklearn import base
import vectorbt as vbt
import pandas as pd
import numpy as np
import os
from joblib import Parallel , delayed
from .commonFunctions import memory , generate_signals_for_scanner , make_df , getdf
from .plotFunction import plot_backtest
import gc
import time

'''
在此处定义策略集类
'''

class Strategy():
    def __init__(self, name , description="" , params = {}):
        self.name = name
        self.original_freq = '1min'
        
        self.description = description
        self.params = params
        self.tPrate = 0.08
        self.sLrate = 0.08
        self.cash = 10000
        self.slippage = 0.0005
        self.fees = 0.0005
        
        
    def generate_signals(self , filename , resampleperiod = '1H'):
        from .commonFunctions import make_df  , resamplesig2origion , resampledf
        
        print(f'\n正在加载数据文件 {filename} ...')
        df = make_df(filename)
        
        dfc = resampledf(df , resampleperiod)
        print(f'数据文件 {filename} 加载完成，共 {len(df)} 根K线，重采样后 {len(dfc)} 根K线.')
        
        if self.name == 'hq3':
            print(f'正在生成 {self.name} 策略信号...') 
            window = self.params.get('window' , 20)
            stddev = self.params.get('stddev' , 2)         
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
            
            print(f'{self.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif self.name == 'hq3.5':
            print(f'\n正在生成{self.name}策略信号...')
            window = self.params.get('window' , 20)
            stddev = self.params.get('stddev' , 2)
            bandwithmax = self.params.get('bandwidthmax' , 0.2)
            bandwithmin = self.params.get('bandwidthmin' , 0.05)
            
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
            
            print(f'{self.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif self.name == 'hq3.5.1':
            print(f'\n正在生成{self.name}策略信号...')
            window = self.params.get('window' , 20)
            stddev = self.params.get('stddev' , 2)
            
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
            
            print(f'{self.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif self.name == 'hq3.5.2':
            print(f'\n正在生成{self.name}策略信号...')
            window = self.params.get('window' , 20)
            stddev = self.params.get('stddev' , 2)
            
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
            
            print(f'{self.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif self.name == 'hq2':
            print(f'\n正在生成 {self.name} 策略信号...')
            window = self.params.get('window' , 20)
            stddev = self.params.get('stddev' , 2)
            
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
            
            print(f'{self.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif self.name == 'hq4':
            print(f'\n正在生成 {self.name} 策略信号...')
            
            fast = self.params.get('fast' , 12)
            slow = self.params.get('slow' , 26)
            signal = self.params.get('signal' , 9)
           
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
            
            print(f'{self.name} 策略信号生成完毕.')
            return df , long_entries , long_exits , short_entries , short_exits
        
        elif self.name == 'hq5':
            print(f'\n正在生成 {self.name} 策略信号...')
            #短期周期
            X1 = self.params.get('x1' , 3)
            X2 = self.params.get('x2' , 6)
            X3 = self.params.get('x3' , 12)
            X4 = self.params.get('x4' , 24)
            #长期周期
            X5 = self.params.get('x5' , 10)
            X6 = self.params.get('x6' , 20)
            X7 = self.params.get('x7' , 30)
            X8 = self.params.get('x8' , 60)
            
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
            print(f'{self.name} 策略信号生成完毕.')
            return df, long_entries , long_exits , short_entries , short_exits
    
                    
    def vbt_backtest(self, df, long_entries, long_exits, short_entries, short_exits , plot = False ):
        print(f'\n正在运行 {self.name} 策略回测... ,当前使用默认参数{self.params}')
        #print(f'\n调试信息： {self.cash} , {self.fees} , {self.slippage} , {self.tPrate} ,{self.sLrate}')
        pf = vbt.Portfolio.from_signals(
            close=df['close'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            entries = long_entries.fillna(False).astype(bool),
            exits = long_exits.fillna(False).astype(bool),
            short_entries= short_entries.fillna(False).astype(bool),
            short_exits= short_exits.fillna(False).astype(bool),
            
            init_cash=self.cash,
            fees=self.fees,
            slippage=self.slippage,
            freq=self.original_freq,
            sl_stop=self.sLrate,
            tp_stop=self.tPrate,
            #direction= 'both',
            upon_opposite_entry= 'reverse',
        )

        #print("原始 close dtype:", df['close'].dtype)
        
        result = pf.stats()
        
        print('策略回测完毕.')
        print(f'\n===================== {self.name}回测结果 =====================')
        print(result)
    
        # 打印订单和交易明细
        print(f'\n前20笔订单明细\n{pf.orders.records_readable.drop(columns =['Order Id' , 'Column']).set_index('Timestamp').head(20)}')                      #type: ignore
        print(f'\n前20笔交易记录明细\n{pf.trades.records_readable.drop(columns =['Exit Trade Id' , 'Column']).set_index('Entry Timestamp').head(20)}')           #type: ignore
        
        if plot == True:
            '''绘图的开始'''
            print(f'\n=================== 存储绘图数据 ===================')
            df = pf.orders.records_readable.drop(columns =['Order Id' , 'Column'])                 #type: ignore
            orders_path = os.path.join('database/plotdatas', 'ordersplotting.parquet')
            df.to_parquet(orders_path ,engine = 'pyarrow')
            df1 = pf.trades.records_readable.drop(columns =['Exit Trade Id' , 'Column'])           #type: ignore
            trades_path = os.path.join('database/plotdatas', 'tradesplotting.parquet')
            df1.to_parquet(trades_path ,engine = 'pyarrow')
            print(f'\n=================== 绘图数据存储完毕 ===================')
               
        return pf
    
    def plotlastbacktest(self, lastfilename):
        print(f'\n=================== 启动回测可视化 ===================')
        price_file_path = os.path.join('database/rowdatas', lastfilename)
        orders_file_path = os.path.join('database/plotdatas', 'ordersplotting.parquet')
        trades_file_path = os.path.join('database/plotdatas', 'tradesplotting.parquet')
        plot_backtest(
            price_file  = price_file_path,
            orders_file = orders_file_path,
            trades_file = trades_file_path,
            debug = False
        )
    
       
    def runbacktest(self , filename , resampleperiod = '1h' , plot = False):
        signals = self.generate_signals(filename=filename , resampleperiod=resampleperiod)
        self.vbt_backtest(*signals , plot = plot)         #type: ignore
        if plot == True:
            self.plotlastbacktest(filename)
            
            
    
    
    #参数扫描部分
    def runparamscanner(self , cpunum , paramlist:list=[] , tokens:list=['btcdata.parquet']):
        #memory.clear()

        def run_single_scan(token , resamplenum , tPrate , sLrate , window=None , stddev=None , bandwidthmax=None , bandwidthmin=None):
            strat_params = self.params.copy()
            if window is not None:
                strat_params['window'] = window
            if stddev is not None:
                strat_params['stddev'] = stddev
            if bandwidthmax is not None:
                strat_params['bandwidthmax'] = bandwidthmax
            if bandwidthmin is not None:
                strat_params['bandwidthmin'] = bandwidthmin
                
            try:
                df, long_entries, long_exits, short_entries, short_exits = generate_signals_for_scanner(self.name , token , resamplenum , strat_params) #type: ignore
                pf = vbt.Portfolio.from_signals(
                    close=df['close'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    entries = long_entries.fillna(False).astype(bool),
                    exits = long_exits.fillna(False).astype(bool),
                    short_entries= short_entries.fillna(False).astype(bool),
                    short_exits= short_exits.fillna(False).astype(bool),
                    
                    init_cash = self.cash,
                    fees = self.fees,
                    slippage = self.slippage,
                    freq = self.original_freq,
                    sl_stop = sLrate,
                    tp_stop = tPrate,
                    #direction= 'both',
                    upon_opposite_entry= 'reverse',
                )
                
                
                if len(pf.get_trades()) == 0:
                    print(f'当前{token} @ {resamplenum} 无交易产生')
                    return {
                            'tokenname': token,
                            'resampleperiod': resamplenum,
                            'tPrate': tPrate,
                            'sLrate': sLrate,
                            'total_return': 0.0,
                            'sharpe_ratio': 0.0,
                            'max_drawdown': 0.0,
                            'win_rate': 0.0,
                            'total_trades': 0
                        }
                    
                if pf.stats() is not None:
                    stats = pf.stats()
                    return{
                        'tokenname': token,
                        'resampleperiod': resamplenum,
                        'tPrate': tPrate,
                        'sLrate': sLrate,                  
                        'window': window if window is not None else self.params.get('window', 'N/A'),
                        'stddev': stddev if stddev is not None else self.params.get('stddev', 'N/A'),
                        'bandwidthmax': bandwidthmax if bandwidthmax is not None else self.params.get('bandwidthmax', 'N/A'),
                        'bandwidthmin': bandwidthmin if bandwidthmin is not None else self.params.get('bandwidthmin', 'N/A'),
                        
                        'total_return': float(pf.total_return()),
                        'sharpe_ratio': float(stats['Sharpe Ratio']),                #type: ignore                 
                        'max_drawdown': float(stats['Max Drawdown [%]']),            #type: ignore
                        'win_rate': float(stats['Win Rate [%]']),                    #type: ignore
                        'total_trades': int(stats['Total Trades'])                   #type: ignore
                    }
                else:
                    print(f'当前{token} @ {resamplenum} 无交易数据产生')
                    return {
                            'tokenname': token,
                            'resampleperiod': resamplenum,
                            'tPrate': tPrate,
                            'sLrate': sLrate,
                            'window': window if window is not None else self.params.get('window', 'N/A'),
                            'stddev': stddev if stddev is not None else self.params.get('stddev', 'N/A'),
                            'bandwidthmax': bandwidthmax if bandwidthmax is not None else self.params.get('bandwidthmax', 'N/A'),
                            'bandwidthmin': bandwidthmin if bandwidthmin is not None else self.params.get('bandwidthmin', 'N/A'),
                            'sharpe_ratio': 0.0,
                            'max_drawdown': 0.0,
                            'total_return': 0.0,
                            'win_rate': 0.0,
                            'total_trades': 0
                        }
            
            except Exception as e:
                print(f'{e}')
                return {
                            'tokenname': token,
                            'resampleperiod': resamplenum,
                            'tPrate': tPrate,
                            'sLrate': sLrate,
                            'window': window if window is not None else self.params.get('window', 'N/A'),
                            'stddev': stddev if stddev is not None else self.params.get('stddev', 'N/A'),
                            'bandwidthmax': bandwidthmax if bandwidthmax is not None else self.params.get('bandwidthmax', 'N/A'),
                            'bandwidthmin': bandwidthmin if bandwidthmin is not None else self.params.get('bandwidthmin', 'N/A'),
                            'total_return': 0.0,
                            'sharpe_ratio': 0.0,
                            'max_drawdown': 0.0,
                            'win_rate': 0.0,
                            'total_trades': 0
                        }  
        
        #并行部分       
        parabro = Parallel(n_jobs = cpunum, 
                        verbose = 10 , 
                        #backend="threading" , 
                        max_nbytes=None,                        #max_nbytes表示总是尝试共享内存
                        pre_dispatch='10*n_jobs'                #预先分配的任务数量，'10*n_jobs'表示预先分配10倍于CPU核心数的任务，以减少等待时间
                        )   
        
        _ = [make_df(token) for token in tokens] #预热 
        gc.collect()
        _ = [getdf(t, tf) for t, tf in set((token, tf) for token, tf, *_ in paramlist)]
        gc.collect()
        
        siglist = [(item[0], item[1], item[4], item[5], item[6], item[7]) for item in paramlist]
        uniquesets = set(siglist)
        defaultparams = self.params.copy()
        genFunction = generate_signals_for_scanner
        stratName = self.name
        
        # 将默认参数组合和需要并行生成的组合分开，避免在循环中重复对所有组合并行生成
        defaults = []
        others = []
        for t, tf, w, s, bmax, bmin in uniquesets:
            if w is None and s is None and bmax is None and bmin is None:
                defaults.append((t, tf))
            else:
                others.append((t, tf, w, s, bmax, bmin))

        # 先同步生成默认参数的信号（如果有）
        for t, tf in defaults:
            _ = genFunction(stratName, t, tf, defaultparams)
            gc.collect()

        # 并行生成其余组合（只执行一次）
        if others:
            print(f'信号组合生成中...预计需要处理{len(others)}组')
            _ = parabro(
                delayed(genFunction)(stratName, t, tf, {'window': w, 'stddev': s, 'bandwidthmax': bmax, 'bandwidthmin': bmin})
                for t, tf, w, s, bmax, bmin in others
            )
            print('信号生成完毕')
            time.sleep(2)
            gc.collect()
            
    
        results = parabro(
            delayed(run_single_scan)(token = t , resamplenum = r , tPrate = p , sLrate = l , window = w , stddev = s , bandwidthmax = bmax , bandwidthmin = bmin)
            for t , r , p , l , w , s , bmax , bmin in paramlist          
        )


        #=====输出结果=====
        #输出结果
        if results:
            rdf = pd.DataFrame(results).sort_values('total_return', ascending=False)        #asending = False 表示降序排列 ， 默认True升序   #type: ignore
            print("\n=== 最优参数组合 ===")
            print(rdf.head(30))
            # 保存结果
            rdf.to_csv(f'回测扫描结果/{self.name}扫描结果.csv', index=False)
            print(f"\n结果已保存至 回测扫描结果/{self.name}扫描结果.csv")
        else:
            print('没有产生任何result , 这不正常')
        
        
        
        