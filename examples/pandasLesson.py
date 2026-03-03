import random
import pandas as pd
import random


x = pd.Series(list(range(100,110)), index = list(range(1,11)))

x.loc[[1,2,3]]= 99

hh1 = x.index.get_indexer([1 , 8] , method='bfill')              #type: ignore
hh2 = x[x.isin([104 , 105])].index
hh3 = hh2.get_indexer([5 ,6] , method='bfill')                   #type: ignore

print(x)

print(hh1)
print(hh2)
print(hh3)

print(x.loc[[2,8]])
print(x.iloc[[-1 , -2]])                                         #type: ignore