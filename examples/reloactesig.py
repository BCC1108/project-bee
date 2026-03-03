from dis import Positions
import pandas as pd
import numpy as np

data5s = pd.date_range('2026-01-01' , periods = 10 , freq= '5s')

df = pd.DataFrame(columns=list(range(1,3)) , index=data5s)

series1 = pd.Series(np.random.uniform(100 , 151 , size=10) , index = data5s)
series2 = pd.Series(np.random.randint(100, 200, size=10 ), index = data5s)
df[1] = series1
df[2] = series2
df.rename(columns={1:'randomfloat' , 2 : 'randomint'} ,inplace= True )         #inpalce = True  直接替换原列， 否则创建新对象

dfc = df.resample('20s').agg({'randomfloat':'first' , 'randomint':'last'}).dropna()

print(data5s)
print(df)

buysig = dfc['randomint'].shift(1) < 150   #buysig是一个布尔序列  boll pd series

print(buysig)

print(dfc)

def min2s(sig , original_df):
    replace_time_index = sig[sig].index       #意思是提取序列中为True的index   , 取出来的是不同行           
    
    if len(replace_time_index) == 0:
        return pd.Series(False ,index = original_df.index)
    
    positions = df.index.get_indexer(replace_time_index , method='bfill')                #get_indexer返回行号
    
    validpos = positions[positions != -1]       #-1表示找不到
    
    result = pd.Series(False , index=original_df.index)
    
    result.iloc[validpos] = True                #iloc取行号

    return result

dfwtsig = min2s(buysig , df)


print(dfwtsig)

