#backtrader库
import sys
import os
from threading import main_thread

from numpy import long

sys.path.append(os.path.dirname(os.path.dirname(__file__))) 
from core.commonFunctions import make_df 
import backtrader as bt
import backtrader.indicators as btind


#别的库
import pandas as pd
from tqdm import tqdm 
import json
import time

#import multiprocessing

#===全局变量====
resamplenum = 60 * 60          #K线重聚和时间，秒计算
resamplenum2 = 60 * 15         #K线重聚和时间，秒计算
tradeMin = 0.01*0.001          #swapCcy * swapMin
datafilename = 'soldata.parquet'

#superTrend指标实现（基于ATR的趋势跟踪指标，具有自动调整止损功能）
class SuperTrend(bt.Indicator):
    lines = ('supertrend', 'direction')
    params = (('period', 10), ('multiplier', 3))

    def __init__(self):
        self.atr = bt.indicators.ATR(period=self.p.period)                   #type: ignore
        self.hl2 = (self.data.high + self.data.low) / 2.0
        self.upper = self.hl2 + self.p.multiplier * self.atr
        self.lower = self.hl2 - self.p.multiplier * self.atr

        # 初始化状态（第一根K线）
        self.initialized = False
    def next(self):
        if not self.initialized:
            self.lines.supertrend[0] = self.lower[0]                         #type: ignore
            self.lines.direction[0] = 1  # 1=多, -1=空                       #type: ignore
            self.initialized = True
            return
            
        prev_st = self.lines.supertrend[-1]                                  #type: ignore
        prev_dir = self.lines.direction[-1]                                  #type: ignore
        close = self.data.close[0]
        upper = self.upper[0]
        lower = self.lower[0]

        if prev_dir == 1:  # 当前是多头
            if close < prev_st:
                # 翻转为空头
                self.lines.supertrend[0] = upper                             #type: ignore
                self.lines.direction[0] = -1                                 #type: ignore
            else:
                # 维持多头，st 只能上移
                self.lines.supertrend[0] = max(lower, prev_st)               #type: ignore
        else:  # 当前是空头 
            if close > prev_st:
                # 翻转为多头
                self.lines.supertrend[0] = lower                             #type: ignore
                self.lines.direction[0] = 1                                  #type: ignore
            else:
                # 维持空头，st 只能下移
                self.lines.supertrend[0] = min(upper, prev_st)               #type: ignore

# Create a Stratey
class hqStrategy(bt.Strategy):
    params = (
        ('take_profit_rate' , 0.08),
        ('stop_loss_rate' , 0.08)
    )

    
    def __init__(self):
        #1h指标
        self.boll_60= btind.BollingerBands(self.data60, period =20 , devfactor = 2)                     #type: ignore
        self.rsi_60 = bt.ind.RSI(self.data60, period=14)                                                #type: ignore
        self.volRatio_60 = self.data60.volume / bt.ind.SMA(self.data60.volume, period=20)               #type: ignore
        # RAVI = (SMA(short) - SMA(long)) / SMA(long) * 100
        sma_short = bt.ind.SMA(self.data60.close, period=7)                                             #type: ignore
        sma_long = bt.ind.SMA(self.data60.close, period=65)                                             #type: ignore
        self.ravi_60 = (sma_short - sma_long) / sma_long * 100
        self.st_60 = SuperTrend(self.data60, period= 10 , multiplier=2.5)                               #type: ignore
        self.atr_60 = bt.ind.ATR(self.data60, period=10)                                                #type: ignore
        
        #辅助变量
        self.order = None 
        self.win_trades = 0
        self.total_trades = 0
        self.data60_len = 0  
    
    
    def pr(self, prtxt , dt=None):                             # dt = None  如果不传入参数，就自动使用当前k线的日期
        dt = dt or self.datas[0].datetime.datetime(0)          #self.data.datetime[0] 是完整的“日期+时间”（精确到秒/毫秒），而 self.data.datetime.date(0) 只取“日期部分”（年-月-日），去掉时分秒。
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        tqdm.write('%s, %s' % (time_str, prtxt))

    def notify_order(self, order):
        if order.status in [order.Submitted , order.Accepted]:
            return
        if order.status in [order.Completed]:
            self.pr('开盘价： %.2f  收盘价： %.2f'  %(self.data.open[0] , self.data.close[0]))
            current_value = self.broker.getvalue()
            if order.isbuy():
                self.pr('|买入成交| 价格：%.2f  成交总值：%.2f  手续费：%.2f  成交仓位：%.2f  实时身价：%.2f' %(order.executed.price , order.executed.value , order.executed.comm ,order.executed.size , current_value) )
                
            elif order.issell():
                self.pr('|卖出成交| 价格：%.2f  成交总值：%.2f  手续费：%.2f  成交仓位：%.2f  实时身价：%.2f' %(order.executed.price , order.executed.value , order.executed.comm ,order.executed.size , current_value) )
            
        elif order.status in [order.Canceled , order.Margin , order.Rejected]:
            self.pr('订单 取消/保证金不足/拒绝')
        
        self.order = None    # notify_order函数相当于买卖便签，无论买卖是否成功都应该擦掉便签
        
    def notify_trade(self, trade):
        self.pr('|经营利润| 毛利润: %.2f  净利润: %.2f 仓位数量：%.2f'%(trade.pnl , trade.pnlcomm , self.position.size))     #毛利润与净利润
        if trade.isclosed:
            self.total_trades += 1
            if trade.pnlcomm > 0:
                self.win_trades += 1
        if self.total_trades > 0:
            win_rate = self.win_trades / self.total_trades
            self.pr('实时胜率%.2f%%'%(win_rate*100))
    
    def next(self): 
        #self.pr(f"data_idx={len(self.data)}, total={self.data.buflen()}")
        pbar.update(1)
        
        if len(self.data60) < 60:   #确保有足够的历史数据来计算指标
            return
        
        if self.order:
            return
    
        #趋势计算
        condition1 =(
           (self.st_60.lines.direction[-2] == 1) and               #type: ignore 
           (self.st_60.lines.direction[-1] == 1) and               #type: ignore
           (self.st_60.lines.direction[0] == 1) and                #type: ignore
           (self.ravi_60[0] > 0.01)                                #type: ignore
        ) 
        condition2 = (
            (self.st_60.lines.direction[-2] == -1) and              #type: ignore
            (self.st_60.lines.direction[-1] == -1) and              #type: ignore
            (self.st_60.lines.direction[0] == -1) and               #type: ignore
            (self.ravi_60[0] < -0.01)                               #type: ignore
        )
        
        up_trend = condition1 
        down_trend = condition2
        upNdown = not (up_trend or down_trend)
        
        #买卖信号
        buysignal = False
        sellsignal = False
        
        #入场
        if upNdown:
            buysignal = (
                self.data60.low[0] < self.boll_60.lines.bot[0] and         #下破下轨           #type: ignore
                self.rsi_60[0] < 30                               and      #RSI进入超卖（<30） #type: ignore
                self.volRatio_60[0] < 0.5                                  #缩量
            )
                

            sellsignal = (
                self.data60.high[0] > self.boll_60.lines.top[0] and        #上破上轨            #type: ignore
                self.rsi_60[0] > 70                                and     #RSI进入超买（>70）  #type: ignore
                self.volRatio_60[0] < 0.5                                  #缩量     
                )
        
        elif up_trend:
            buysignal = (
                self.st_60.lines.direction[0] == 1 and                     # 当前处于多头趋势（绿线）   #type: ignore
                self.data60.low[0] < self.st_60.lines.supertrend[0] and    # 盘中跌破绿线               #type: ignore
                self.data60.close[0] > self.st_60.lines.supertrend[0] and  # 收盘站回线上（假跌破）     #type: ignore
                self.rsi_60[0] > 50 and self.rsi_60[-1] <= 50 and          # RSI 上穿 50                 #type: ignore
                self.volRatio_60[0] < 0.8)                                 # 量比 < 0.8（缩量）          #type: ignore
                                                                          
            
        
        elif down_trend:
            sellsignal = (
                self.st_60.lines.direction[0] == -1 and                    # 当前处于空头趋势（红线）   #type: ignore
                self.data60.high[0] > self.st_60.lines.supertrend[0] and   # 盘中突破红线               #type: ignore
                self.data60.close[0] < self.st_60.lines.supertrend[0] and  # 收盘压回线下（假突破）     #type: ignore
                self.rsi_60[0] < 50 and self.rsi_60[-1] >= 50 and          # RSI 下穿 50                 #type: ignore
                self.volRatio_60[0] < 0.8                                  # 量比 < 0.8（缩量）          #type: ignore                                                     
            )
        
        
        #出场信号
        cLongsig = False
        cShortsig = False
        
        slMulti = 1.5 if upNdown else 2.0
        pos = self.getposition(self.data)
        
        if pos.size > 0:
            if upNdown:
                cLongsig = (self.data60.close[-1] < self.boll_15min.lines.mid[-1]) and (self.data60.close[0] > self.boll_15min.lines.mid[0])          #type: ignore
                
            else:
                cLongsig = (
                    self.superTrend_15min.lines.direction[0] == -1 or                                                                         #type: ignore
                    self.data60.close[0] < self.superTrend_15min.lines.supertrend[0]                                                           #type: ignore
                )
        elif pos.size < 0:
            if upNdown:
                cShortsig = (self.data60.close[-1] > self.boll_15min.lines.mid[-1]) and (self.data60.close[0] < self.boll_15min.lines.mid[0])          #type: ignore
                
            else:
                cShortsig = (
                    self.superTrend_15min.lines.direction[0] == 1 or                                                                         #type: ignore
                    self.data60.close[0] > self.superTrend_15min.lines.supertrend[0]                                                           #type: ignore
                )
            
        
        if len(self.data):
            if pos.size != 0:
                take_profit_price = pos.price * (1 + self.p.take_profit_rate) if pos.size > 0 \
                                        else pos.price * (1 - self.p.take_profit_rate)
                        
                stop_loss_price = pos.price * (1 - self.p.stop_loss_rate) if pos.size > 0 \
                                else pos.price * (1 + self.p.stop_loss_rate)
                if pos.size > 0:
                    if self.data.high[0] >= take_profit_price:
                        self.pr(f'多头止盈 @ {take_profit_price:.2f}')
                        sellsize = max(pos.size/2 , tradeMin) if pos.size > tradeMin \
                            else pos.size
                        self.order = self.sell(size = sellsize)
                    elif self.data.low[0] <= stop_loss_price:
                        self.pr(f'多头止损 @ {stop_loss_price:.2f}')
                        self.order = self.sell()
                elif pos.size < 0:
                    if self.data.low[0] <= take_profit_price:
                        self.pr(f'空头止盈 @ {take_profit_price:.2f}')
                        buysize = max(abs(pos.size/2),tradeMin) if abs(pos.size) > tradeMin \
                            else abs(pos.size) 
                        self.order = self.buy(size = buysize)
                    elif self.data.high[0] >= stop_loss_price:
                        self.pr(f'空头止损 @ {stop_loss_price:.2f}')
                        self.order = self.buy() 
                   
        if len(self.data60) > self.data60_len:
            self.data60_len = len(self.data60)
            
            if pos.size == 0:
                if buysignal:                                                        
                    self.pr('看多 开多仓： %.2f' %self.data60.close[0])
                    self.order = self.buy()
                    
                elif sellsignal:
                    self.pr('看空 开空仓： %.2f' %self.data60.close[0])
                    self.order = self.sell()
            else:
                if pos.size > 0 and cLongsig:
                #if pos.size > 0 and sellsignal:
                    self.pr('长头平仓：%.2f' % self.data60.close[0])
                    self.order = self.close()
                    ##self.order = self.sell()
                         
                if pos.size < 0 and cShortsig:
                #if pos.size < 0 and buysignal:
                    self.pr('短头平仓：%.2f' % self.data60.close[0])
                    self.order = self.close()
                    #self.pr('反手开多：%.2f' % self.data60.close[0])
                    #self.order = self.buy()
                    
                   
        if len(self.data) == totalbar - 1:
            if self.position:
                self.pr('最后一根k线清仓')
                self.order = self.close()                   #self.close（）平掉所有仓位
    
    def stop(self):
        if pbar and pbar.n < totalbar:
            pbar.update(totalbar - pbar.n)
            pbar.close()
        
if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats = False)                              # type: ignore
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell , bardist=0.5)   # 添加 BuySell 观察器（用于绘图）
    
    cerebro.addstrategy(hqStrategy)
   
    df = make_df(datafilename)
    
    totalbar = len(df)
    pbar = tqdm(total=totalbar , desc = '回测进度' , unit = "klines" , position = 0 , leave = True , bar_format='{desc}: {percentage:.2f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')

    data = bt.feeds.PandasData(                                                 
        dataname=df,                                                   # type: ignore
        datetime=None,                                                 # 时间是df的index   # type: ignore
        open=0,                                                        # type: ignore
        high=1,                                                        # type: ignore
        low=2,                                                         # type: ignore
        close=3,                                                       # type: ignore
        volume=4,                                                      # type: ignore
        openinterest=-1,                                               # type: ignore
        timeframe = bt.TimeFrame.Seconds,                              # type: ignore
        compression = 1 ,                                              # type: ignore
    )
    
    cerebro.adddata(data , name = 'data')
    
    cerebro.resampledata(
        data,
        timeframe = bt.TimeFrame.Seconds,                              #type: ignore
        compression = resamplenum,
        name = 'data60'
    )
    
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission = 0.0005 )
    # 设置固定金额滑点（例如每次成交价格偏差 0.01）
    cerebro.broker.set_slippage_fixed(0.005)
    # 或者设置百分比滑点（例如 0.5%）
    #cerebro.broker.set_slippage_perc(0.005)
    cerebro.broker.set_shortcash(False)
    cerebro.addsizer(bt.sizers.PercentSizer,percents = 95)
    
    #添加分析器
    #cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
    #cerebro.addanalyzer(bt.analyzers.SharpeRatio, riskfreerate=0.02, _name='sharpe')
    #cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    #cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_stats')

    #cerebro.broker.set_coc(True)  # 以当日k线收盘价成交
    
    tqdm.write('='*10 + '回测开始' + '='*10)
    tqdm.write('入场身价: %.2f' % cerebro.broker.getvalue()) 
    t0 = time.time()
    
    result = cerebro.run(maxcpus = None)

    tqdm.write('出场身价: %.2f '% cerebro.broker.getvalue() )
    t1 = time.time()
    tqdm.write(f">>> 回测完成，耗时: {t1 - t0:.2f} 秒")

    cerebro.plot()
    