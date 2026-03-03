import pandas as pd
import json

filenames = ['btcdata' , 'ethdata' , 'soldata' ]

def convert_to_parquet(filenames):
    for file in filenames:
        with open(file) as f:
            data = json.load(f)
            
        df = pd.DataFrame(data ,columns = ['ts' , 'open' , 'high' , 'low' , 'close' , 'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm'])
        cols = ['ts' , 'open' , 'high' , 'low' , 'close' , 'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm']
        df = df[cols].apply(pd.to_numeric , errors = 'coerce')
        df['datetime'] = pd.to_datetime(df['ts'] , unit = 'ms' , utc = True).dt.tz_convert('Asia/Shanghai')
        df = df[::-1].reset_index(drop=True)

        print(df.head(20))
        df.to_parquet(f'{file}.parquet' ,engine = 'pyarrow')
        
convert_to_parquet(filenames)
