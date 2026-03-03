from core.strategyBook import Strategy
from joblib import Parallel , delayed
import os
import time




'''==================================================第一步，在此处选择生成一个策略实例==========================================================='''
'''想用的策略取消注释就行，当前不能同时进行'''
teststrat = Strategy(name='hq2' , description='基于BBands指标的策略' , params={'window':20 , 'stddev':2})
#teststrat = Strategy(name='hq3' , description='基于BBands指标的另一个策略' , params={'window':20 , 'stddev':2})
#teststrat = Strategy(name='hq4' , description='基于MACD指标的新策略' , params={'fast':12 , 'slow':26 , 'signal':9})
#teststrat = Strategy(name='hq5' , description='bbi快慢线策略' , params={'x1':3 , 'x2':6 , 'x3':12 , 'x4':24 , 'x5':10 , 'x6':20 , 'x7':30 , 'x8':60})


'''==================================================第二步，策略带有默认参数，可在此进行调整====================================================='''
teststrat.tPrate = 0.08            #设置止盈比例
teststrat.sLrate = 0.08           #设置止损比例

teststrat.cash = 10000             #设置初始资金
teststrat.fees = 0.0005            #设置手续费
teststrat.slippage = 0.0005        #设置滑点

time1 = time.time()
'''==================================================第三步, run这个回测========================================================================='''
'''现在可以对回测传入 plot 参数， True 代表绘图， False 代表不绘图，默认是 False'''
#teststrat.runbacktest(filename='soldata.parquet' , resampleperiod='1h' , plot=False)  #此处选择要回测的文件和重采样周期，手动一下，逻辑还在完善 
#teststrat.runbacktest(filename='soldata2.parquet' , resampleperiod='1h' , plot=False)
#teststrat.runbacktest(filename='btcdata.parquet' , resampleperiod='1h' , plot=False)
#teststrat.runbacktest(filename='ethdata.parquet' , resampleperiod='1h' , plot=False)
#teststrat.runbacktest(filename='xrpdata.parquet' , resampleperiod='1h' , plot=False)



params = [
    ('soldata.parquet', '1h'),
    ('soldata2.parquet', '1h'),
    ('btcdata.parquet', '1h'),
    ('ethdata.parquet', '1h'),
    ('xrpdata.parquet', '1h')
]



parabro = Parallel(n_jobs = 12 , verbose = 10 , backend="threading" ,return_as = 'generator') #type: ignore

op = parabro(
    delayed(teststrat.runbacktest)(filename= f , resampleperiod= t , plot=False) 
    for f , t in params
)

list(op)


time2 = time.time()
print(f'耗时{time2-time1}s')