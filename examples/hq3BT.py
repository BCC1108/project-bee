#backtrader库
import backtrader as bt
import backtrader.indicators as btind
from core.commonFunctions import make_df

#绘图库


#别的库
import pandas as pd
from tqdm import tqdm , trange
import json
import time

#import multiprocessing

#===全局变量====
resamplenum = 60 * 60          #K线重聚和时间，秒计算
tradeMin = 0.01*0.001          #swapCcy * swapMin
datafilename = 'soldata'

#===此地不需要修改===

def got_df(datafilename):
    with open(datafilename) as databook:
        data = json.load(databook)
        
    df = pd.DataFrame(data, columns=[
            "ts", "open", "high", "low", "close", "vol", "volCcy", "volCcyQuote", "confirm"
        ])
    #df = df.iloc[::-1].reset_index(drop=True)  # oldest → newest

    df['ts'] = pd.to_numeric(df['ts'])
    df = df.sort_values('ts').reset_index(drop=True)
    
    df['datetime'] = pd.to_datetime(df['ts'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'vol']:
        df[col] = pd.to_numeric(df[col])
    
    df = df[['datetime', 'open', 'high', 'low', 'close', 'vol']]
    #此处应有一行转换时区
    df.rename(columns={'vol': 'volume'}, inplace=True)
    df.set_index('datetime', inplace=True)
    #df = df[::5]       #调试用
    
    
    return df

# Create a Stratey
class hqStrategy(bt.Strategy):
    params = (
        ('testperiod', 20 ),
        ('take_profit_rate' , 0.08),
        ('stop_loss_rate' , 0.08)
    )

    def pr(self, prtxt , dt=None):                             # dt = None  如果不传入参数，就自动使用当前k线的日期
        dt = dt or self.datas[0].datetime.datetime(0)          #self.data.datetime[0] 是完整的“日期+时间”（精确到秒/毫秒），而 self.data.datetime.date(0) 只取“日期部分”（年-月-日），去掉时分秒。
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        tqdm.write('%s, %s' % (time_str, prtxt))
        

    def __init__(self):
        self.boll = btind.BollingerBands(self.data1, period = self.p.testperiod)    #type: ignore
        self.body_high = bt.Max(self.data1.open, self.data1.close)   # 柱体上沿
        self.body_low  = bt.Min(self.data1.open, self.data1.close)   # 柱体下沿
        self.order = None 
        self.win_trades = 0
        self.total_trades = 0
        self.data1_len = 0    

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

        if len(self.data1) < 2:
            return
        
        if self.order:
            return

        buysignal = (
            self.data1.low[-1] < self.boll.bot[-1] and           # 第一根下破下轨
            self.data1.close[0] > self.data1.open[0] and         # 第二根是绿线（阳线）
            self.data1.volume[0] < self.data1.volume[-1]         # 第二根缩量
        )

        sellsignal = (
            self.data1.high[-1] > self.boll.top[-1] and          # 第一根上穿上轨
            self.data1.close[0] < self.data1.open[0] and         # 第二根是红线（阴线）
            self.data1.volume[0] < self.data1.volume[-1]         # 第二根缩量
        )
        
        cLongsig = (self.data1.close[-1] >= self.boll.mid[-1]) and (self.data1.close[0] < self.boll.mid[0])      # 多头：收盘回穿中轨
        cShortsig = (self.data1.close[-1] <= self.boll.mid[-1])  and (self.data1.close[0] > self.boll.mid[0])    # 空头：收盘回穿中轨
        
        pos = self.getposition(self.data)
        
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
                   
        if len(self.data1) > self.data1_len:
            self.data1_len = len(self.data1)
            
            if pos.size == 0:
                if buysignal:                                                        
                    self.pr('看多 开多仓： %.2f' %self.data1.close[0])
                    self.order = self.buy()
                    
                elif sellsignal:
                    self.pr('看空 开空仓： %.2f' %self.data1.close[0])
                    self.order = self.sell()
            else:
                if pos.size > 0 and cLongsig:
                #if pos.size > 0 and sellsignal:
                    self.pr('长头平仓：%.2f' % self.data1.close[0])
                    self.order = self.close()
                    ##self.order = self.sell()
                         
                if pos.size < 0 and cShortsig:
                #if pos.size < 0 and buysignal:
                    self.pr('短头平仓：%.2f' % self.data1.close[0])
                    self.order = self.close()
                    #self.pr('反手开多：%.2f' % self.data1.close[0])
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
   
    df = got_df(datafilename)
    totalbar = len(df)
    pbar = tqdm(total=totalbar , desc = '回测进度' , unit = "klines" , position = 0 , leave = True , bar_format='{desc}: {percentage:.2f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')

    data = bt.feeds.PandasData(                                                 
        dataname=df,                                                   # type: ignore
        datetime=None,                                                 # type: ignore
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
        name = 'data1'
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
    
    strat = result[0]

    cerebro.plot()
    