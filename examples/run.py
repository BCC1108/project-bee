from strategyBook import Strategy
from commonFunctions import convert_to_parquet
from itertools import product
import os
import numpy as np
import time


'''
现在引入策略集合驱动回测，但是仍在整理中
当前可用下面的方法对现有3个策略进行一次快速vbt回测
teststrat是根据策略集创建的实例, 可以是任何名字
如果你想修改信号生成逻辑, 可以直接编辑strategyBook.py中的对应策略部分
'''

'''==================================================第零步, 先将现有的数据转换为更轻更快的parquet格式============================================'''
'''现在使用parquet文件进行回测, 所以先将原数据文件转换成parquet格式'''
#cvtfilename = ['soldata2' ]             #此处换成自己的文件名，不需要后缀'''
#convert_to_parquet(cvtfilename)         #不是每一次都需要转换，转换完后记得注释掉这2行代码，不然每次运行都会重新转换，比较麻烦
'''此时会生成带parquet后缀的文件, 接下来就可以用这些文件进行回测了'''


'''==================================================第一步，在此处选择生成一个策略实例==========================================================='''
'''想用的策略取消注释就行，当前不能同时进行'''
#teststrat = Strategy(name='hq2' , description='基于BBands指标的策略' , params={'window':20 , 'stddev':2})
#teststrat = Strategy(name='hq3' , description='基于BBands指标的另一个策略' , params={'window':20 , 'stddev':2})
teststrat = Strategy(name='hq3.5' , description='hq3变种, 矩形平仓' , params={'window':20 , 'stddev':2, 'bandwidthmax':0.2 , 'bandwidthmin':0.05})
#teststrat = Strategy(name='hq3.5.1' , description='hq3变种, 秒k平仓' , params={'window':20 , 'stddev':2})
#teststrat = Strategy(name='hq3.5.2' , description='hq3变种, 同向持仓先平后开' , params={'window':20 , 'stddev':2})
#teststrat = Strategy(name='hq4' , description='基于MACD指标的新策略' , params={'fast':12 , 'slow':26 , 'signal':9})
#teststrat = Strategy(name='hq5' , description='bbi快慢线策略' , params={'x1':3 , 'x2':6 , 'x3':12 , 'x4':24 , 'x5':10 , 'x6':20 , 'x7':30 , 'x8':60})


'''==================================================第二步，策略带有默认参数，可在此进行调整====================================================='''
teststrat.original_freq = '1min'    #原始数据周期

teststrat.tPrate = 0.03             #设置止盈比例
teststrat.sLrate = 0.08             #设置止损比例
#teststrat.cash = 10000             #设置初始资金
#teststrat.fees = 0.0005            #设置手续费
teststrat.slippage = 0              #设置滑点


'''==================================================第三步, run这个回测========================================================================='''
'''现在可以对回测传入 plot 参数， True 代表绘图， False 代表不绘图，默认是 False'''
#teststrat.runbacktest(filename='soldataMin.parquet' , resampleperiod='1h' , plot=False)  #此处选择要回测的文件和重采样周期，手动一下，逻辑还在完善 


'''==================================================可选, 重绘图上一次回测======================================================================='''
'''在此可以重绘上一次的回测结果, 因为文件是新的覆盖旧的，所以只能重绘上一次，需要手动传输上一次的文件名'''
'''如果仅仅重绘上次回测，为何不把上面的回测代码注释掉呢'''
'''当然，在不需要重绘时也需要注释掉'''

#teststrat.plotlastbacktest('btcdata.parquet')   #此处选择要绘图的文件


'''======================================================参数扫描功能============================================================================='''
#参数矩阵，当前仅支持这些
#策略参数
windows = list(range(10, 31 , 5))                     #窗口期，10到30，步长5
stddevs = [1.5 , 2 , 2.5]                             #标准差倍数，三个选项
bandwidthmaxs = list(np.arange(0.15,0.25,0.01))       #带宽上限，0.15到0.25，步长0.01
bandwidthmins = list(np.arange(0.02,0.08,0.01))
strateparamlist = list(product(windows , stddevs , bandwidthmaxs , bandwidthmins))  

#基础参数
tokens = ['btcdataMin.parquet']
resamplenums = ['1h']
tPoptions = [0.08]
sLoptions = [0.08]
basicparamlist = list(product(tokens, resamplenums , tPoptions , sLoptions))

#最终组合
paramlist = list(product(tokens, resamplenums , tPoptions , sLoptions , windows or [None] , stddevs or [None] , bandwidthmaxs or [None] , bandwidthmins or [None]))


#运行后需要选择使用的核心数，不是越多越好，如果cpu 或 ram 占用持续100%速度反而变慢，建议三分之一
cpunum = input(f'选择使用的核心数，当前可用核心数: {os.cpu_count()}\n')
print(f"预计参数组合总数: {len(paramlist):,} 组")
time.sleep(2)
teststrat.runparamscanner(cpunum , paramlist , tokens) #此行启动参数扫描，启动时第二步的止盈止损应注销，否则永远都是指定值，但也不一定，不用的时候记得注释

