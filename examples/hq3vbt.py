import json
import pandas as pd
import vectorbt as vbt
from commonFunctions import make_df , resampledf , resamplesig2origion

#===全局变量===
filename = 'soldataMin.parquet'
resamplenum = '1h'
tPrate = 0.10
sLrate = 0.03
    
#vectorbt部分
print("正在加载数据...")
df = make_df(filename)
print(f"数据加载完成，共 {len(df)} 根K线")

dfresample = resampledf(df , resamplenum)
print(f"数据重采样完成，共 {len(dfresample)} 根K线 @ {resamplenum}")


price = df[['open','high','low','close']]
pricec = dfresample['close']
pcopen =dfresample['open']
pchigh = dfresample['high']
pclow = dfresample['low']
pcvol = dfresample['volume']

bbands = vbt.BBANDS.run(pricec,window=20,alpha=2)
upperband = bbands.upper                                    #type: ignore
middleband = bbands.middle                                  #type: ignore
lowerband = bbands.lower                                    #type: ignore


buysignal = (
    (pclow.shift(2) < lowerband.shift(2)) &                 # 第一根破下轨
    (pricec.shift(1) > pcopen.shift(1)) &                   # 第二根收阳线
    (pcvol.shift(1) < pcvol.shift(2))                       # 第二根缩量
) 

sellsignal = (
    (pchigh.shift(2) > upperband.shift(2)) &                # 第一根破上轨
    (pricec.shift(1) < pcopen.shift(1)) &                   # 第二根收阴
    (pcvol.shift(1) < pcvol.shift(2))                       #第二根缩量
)

cLongsig =  ( pricec.shift(2) >= middleband.shift(2) ) & ( pricec.shift(1) < middleband.shift(1) )    #价格回穿中轨 
cShortsig = ( pricec.shift(2) <= middleband.shift(2) ) & ( pricec.shift(1) > middleband.shift(1) )    #价格回穿中轨


long_entries = resamplesig2origion(buysignal, price.index)       #type: ignore
long_exits = resamplesig2origion(cLongsig, price.index)          #type: ignore
short_entries = resamplesig2origion(sellsignal, price.index)     #type: ignore
short_exits =resamplesig2origion(cShortsig, price.index)         #type: ignore
  

#开始计算
pf = vbt.Portfolio.from_signals(
    close=price['close'],
    open=price['open'],
    high=price['high'],
    low=price['low'],
    entries = long_entries.fillna(False).astype(bool),
    exits = long_exits.fillna(False).astype(bool),
    short_entries= short_entries.fillna(False).astype(bool),
    short_exits= short_exits.fillna(False).astype(bool),
    
    init_cash=10000,
    #size=0.95,
    #size_type='percent',
    fees=0.0005,
    slippage=0.0005,
    freq='1min',
    sl_stop=sLrate,
    tp_stop=tPrate,
    #direction= 'both',
    upon_opposite_entry= 'reverse',
)

print("原始 close dtype:", df['close'].dtype)
print("重采样后 close dtype:", dfresample['close'].dtype)

print(f'\n=================== {filename}回测结果 ===================')

#print(pf.stats(column='close'))
print(pf.stats())
#print(pf.init_cash)
# 打印订单和交易明细
#print(f'\n前20笔订单明细\n{pf.orders.records_readable.drop(columns =['Order Id' , 'Column']).set_index('Timestamp').head(20)}')                       #type: ignore
print(f'\n前20笔交易记录明细\n{pf.trades.records_readable.drop(columns =['Exit Trade Id' , 'Column']).set_index('Entry Timestamp').head(40)}')         #type: ignore
#pf.plot().show()    #现在依然无法处理超过200w条数据，所以先注释掉                                                                                    #type: ignore
