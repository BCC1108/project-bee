import json
import pandas as pd

filename = '数据用例'

with open(filename) as databook:
    data = json.load(databook)
    
df = pd.DataFrame(data , columns = ['ts' , 'open' , 'high' , 'low' , 'close' , 'vol' ,'volBTC' , 'volUSDT' ,'confirm' ])
df = df[::-1].reset_index(drop=True)
df['ts'] = pd.to_datetime(df['ts'], unit='ms')
#df['dateread'] = pd.to_datetime(df['datetime'], unit='ms')   #新增一列

numeric_cols = ['open', 'high', 'low', 'close', 'vol', 'volBTC', 'volUSDT']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

#df = df.apply(pd.to_numeric)
#df = pd.to_numeric(numeric_lines)


numeric_df = df[numeric_cols]
print("Sum:\n", numeric_df.sum())
print("Mean:\n", numeric_df.mean())
print("Describe:\n", numeric_df.describe())

print(df)


print("最早时间:", df['ts'].min())
print("最晚时间:", df['ts'].max())
print("总行数:", len(df))