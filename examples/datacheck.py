import json
import pandas as pd


filename = '数据用例'

with open(filename) as databook:
    data = json.load(databook)
    
df = pd.DataFrame(data , columns=['ts' , 'open' , 'high' , 'low' , 'close' , 'vol' ,'volBTC' , 'volUSDT' ,'confirm']) 

target_ts = "1769260106000"
count = (df['ts'] == target_ts).sum()

print(f"时间戳 {target_ts} 出现了 {count} 次")