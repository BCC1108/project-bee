import argparse
import pandas as pd
import okx.MarketData as MarketData
from okx import Trade
import time
import okx.Account as Account

# ====== API Key 设置 ======
apiKey = "afb0b2ce-58a1-4a72-a2f7-e6c76832a6b7"
apiSecretKey = "7880398A0867B1C3F4F1CE5362665C8D"
passphrase = "Hu@41695132"
flag = "1"  # 使用模拟盘

# ====== API 初始化 ======
tradeAPI = Trade.TradeAPI(apiKey, apiSecretKey, passphrase, use_server_time=False, flag=flag)
AccountAPI = Account.AccountAPI(apiKey, apiSecretKey, passphrase, use_server_time=False, flag=flag)
marketDataAPI =  MarketData.MarketAPI(flag=flag)
accountAPI = Account.AccountAPI(apiKey, apiSecretKey, passphrase, False, flag)

# ====== 启动参数 ======                               
barperiod = ''                       
cash = 0                            
lever = 0                            
swapCcy = 0.0                        
swapMin = 0.0                        

# ====== 全局变量 ====== 
cycleNum = 0                         #全局变量，用于统计程序跑了多少回合
last_time = 0                        #全局变量，有一些函数我们不想它每个回合都触发
last_ts = None                       #wtf is this , 我在思考
last_update_time = 0                 #上一次更新手动开平仓的时间
last_time_update = 0                 #上一次调用update的时间
strategy_ord_history = set()         #程序历史订单
real_time_equility = 0.0             #qty的新名字，qty仍然存在


# 策略执行
def runhqbt2(buysignal , sellsignal ,cLongsig = None , cShortsig = None):
    global real_time_equility
     
    if not buysignal and not sellsignal and not cLongsig and not cShortsig:
        print('无任何开平信号，保持耐心....')
        return
    
    pos = get_positions()
    if pos:
        for posinfo in pos:
            posside = posinfo[0]
            swapnum = posinfo[1]
            margin = posinfo[7]

            if swapnum > swapMin:
                ordnumc = swapnum
                
                if posside == 'long' and cLongsig:
                    print('长头平仓')
                    oId = Neworder(instId , 'sell' , 'long' , ordnumc)
                    plu = getOrder(instId, oId)
                    real_time_equility += plu
                    #反手开空
                    #ordnumo = ordnumcauculating(real_time_equility)
                    #oId = Neworder(instId , 'sell' , 'short' ,ordnumo)
                    #plu = getOrder(instId, oId)
                    #real_time_equility += plu
                    print(f"策略实时权益更新: {real_time_equility:.2f}货币")  #一起打印
                    
                elif posside == 'short' and cShortsig:
                    print('短头平仓')
                    oId = Neworder(instId , 'buy' , 'short' , ordnumc)
                    plu = getOrder(instId, oId)
                    real_time_equility += plu
                    #print(f"策略实时权益更新: {real_time_equility:.2f}货币")
                    #ordnumo = ordnumcauculating(real_time_equility)
                    #oId = Neworder(instId , 'buy' , 'long' , ordnumo)
                    #plu = getOrder(instId, oId)
                    #real_time_equility += plu
                    print(f"策略实时权益更新: {real_time_equility:.2f}货币")
                else:
                    print('未到平仓条件，选择不平')
                
            elif swapnum == 0:
                if buysignal:
                    open_new_long_num = ordnumcauculating(real_time_equility)                             
                    print('看多 开多仓' )
                    oId = Neworder(instId , 'buy' , 'long' , open_new_long_num)
                    getOrder(instId, oId)
                        
                elif sellsignal:
                    open_new_short_num = ordnumcauculating(real_time_equility)
                    print('看空 开空仓')
                    oId = Neworder(instId , 'sell' , 'short' , open_new_short_num)
                    getOrder(instId, oId)
                else:
                    print('未到开仓条件，选择不开')
                    
                print('未持仓，不平')
            
            else:
                print('存在一个小于0的持仓价值？ 这不合理')
               
#计算合约张数 
def ordnumcauculating(money):
    if money <= 0:
        return 0.0
    result = marketDataAPI.get_ticker(instId = instId)
    result = result.get('data')
    price_now = result[0]['last']
    price_now = float(price_now)
    
    fldict = {10.0: 0, 1.0: 0, 0.1: 1, 0.01: 2 , 0.001:3}
    fl = fldict.get( swapMin , 2 )
    ordnum = money * int(lever) / price_now / swapCcy
    ordnum = round(ordnum , fl)
    return ordnum
    
    
# 获取K线数据
def getKlines(instId, ckp):
    global  last_ts ,latest_ts
    try:
        result = marketDataAPI.get_history_candlesticks(
            instId= instId,
            bar = ckp,
            limit = '30'
        )
        result = result.get('data')
        
        df = pd.DataFrame(result , columns = ['ts' , 'open' ,'high' , 'low' ,'close' ,'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm'])
        colums = ['ts' , 'open' ,'high' , 'low' ,'close' ,'volSWAP' ,'volCCY' , 'volUSDT' , 'confirm']
        df = df[colums].apply(pd.to_numeric , errors='coerce')
        df['ts'] = pd.to_datetime(df['ts'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai')        
        df = df[::-1].reset_index(drop=True)
        
        latest_ts = df['ts'].iloc[-1]
        if last_ts is not None and last_ts == latest_ts:
            print(f'本次 “ {ckp} ” K线还未形成')
            return
        last_ts = latest_ts
        
        #计算boll指标
        bollmid = df['close'].rolling(20).mean()      #SMA
        std = df['close'].rolling(20).std()           #标准差
        bolltop = bollmid + std * 2
        bollbot = bollmid - std * 2
        df['bollmid'] = bollmid
        df['bolltop'] = bolltop
        df['bollbot'] = bollbot
        
        buysignal = sellsignal = cLongsig = cShortsig = None       #事先重置信号
        
        buysignal = (
            df['low'].iloc[-2] < df['bollbot'].iloc[-2] and        # 第一根下破下轨
            df['close'].iloc[-1] >  df['open'].iloc[-1] and        # 第二根是绿线（阳线）
            df['volSWAP'].iloc[-1] <  df['volSWAP'].iloc[-2]       # 第二根缩量
        )

        sellsignal = (
            df['high'].iloc[-2] > df['bolltop'].iloc[-2] and        # 第一根上穿上轨
            df['close'].iloc[-1] <  df['open'].iloc[-1] and         # 第二根是红线（阴线）
            df['volSWAP'].iloc[-1] <  df['volSWAP'].iloc[-2]        # 第二根缩量
        )
        
        cLongsig =  df['close'].iloc[-2] >= df['bollmid'].iloc[-2] and df['close'].iloc[-1] < df['bollmid'].iloc[-1]    #当前收盘价下穿BOLL中轨
        cShortsig = df['close'].iloc[-2] <= df['bollmid'].iloc[-2] and df['close'].iloc[-1] > df['bollmid'].iloc[-1]    #当前收盘价上破BOLL中轨
        
        #buysignal = True     #调试代码
        #sellsignal = True
        
        print(f"{df['ts'].iloc[-1]}  开盘：{df['open'].iloc[-1]} 收盘：{df['close'].iloc[-1]} 最高：{df['high'].iloc[-1]} 最低：{df['low'].iloc[-1]}")
        runhqbt2(buysignal , sellsignal , cLongsig , cShortsig)
    
    except Exception as e:
        print(f'{e}')

# 开仓或平仓
def Neworder(instId, side, positionSide , ordnum):
    global swapMin , stretage_ord_history    
    try: 
        #ordnum 和 swapMIn 此时是浮点数
        fldict = {10.0: 0, 1.0: 0, 0.1: 1, 0.01: 2 , 0.001:3}
        fl = fldict.get( swapMin , 2 )
        ordnum = round(ordnum , fl )
        if ordnum < swapMin:
            print(f"警告：下单数量 {ordnum} < {swapMin} 张，USDT-SWAP 最小{swapMin}张，跳过。")
            return {"code": "-1", "msg": f"数量不足{swapMin}张", "data": []}
       
        ordnum = str(ordnum)
        result = tradeAPI.place_order(
            instId = instId,
            ccy = "USDT",
            tdMode = "isolated",
            side = side,               # buy or sell
            posSide= positionSide,     # long or short
            ordType ="market",
            sz = ordnum
        )
        
        if result.get("code") != "0":
            print(f"下单失败: {result.get('msg', '未知错误')}")
        else:
            print(f"下单成功")
            strategy_ord_history.add(result.get('data')[0]['ordId'])
        
        return result.get('data')[0]['ordId']
        

    except Exception as e:
        print(f"下单发生未知异常: {e}")
        return {"code": "-1", "msg": f"未知异常: {e}", "data": []}

# 查询订单
def getOrder( swapid , orderId):
    plu = 0.0
    try:
        if not swapid:
            print("错误: 订单ID为空")
            return plu

        result = tradeAPI.get_order( swapid , orderId)
        if result.get("code") != "0":
            print(f"查询订单失败: {result.get('msg', '未知错误')}")
            return plu

        ordinfo = result.get("data")
        if not ordinfo or len(ordinfo) == 0:
                print(f"未找到订单 {orderId} 的数据")
                return plu

        for orddetail in ordinfo:
            plu = orddetail['pnl']
            fee = float(orddetail['fee'])
            plu = float(plu) + fee
            
            print(f"交易对象: {orddetail['instType']} | 状态: {orddetail['state']} | "
                f"模式: {orddetail['tdMode']} | 更新时间: {orddetail['uTime']} | 订单收益：{plu:.2f}")

        return plu
            
    except Exception as e:
        print(f"查询订单 {orderId} 异常: {e}")
        return plu

# 设置杠杆倍数
def setLever(instId, lever):
    global last_time
    try:
        current = time.time()
        p1 = '多头杠杆未配置'
        p2 = '空头杠杆未配置'
        
        if current - last_time < 60 * 10:
            return
        else:
            resp = AccountAPI.set_leverage(instId=instId, lever=lever, mgnMode="isolated", posSide="long")
            if resp.get("code") == "0":
                p1 = f"多头杠杆: {resp['data'][0]['lever']} X"

            resp = AccountAPI.set_leverage(instId=instId, lever=lever, mgnMode="isolated", posSide="short")
            if resp.get("code") == "0":
                p2 = f"空头杠杆: {resp['data'][0]['lever']} X"

            print(f"杠杆已配置: {p1} | {p2}")
            last_time = current

    except Exception as e:
        print(f"设置杠杆异常: {e}")

# 查看持仓信息
def get_positions():
    positions = accountAPI.get_positions()
    if positions['code'] != "0":
        print("获取持仓失败:", positions['msg'])
        return

    psdata = positions.get('data')     # 字典之列表  [{},{}]
    apsr = []
    for sePos in psdata:
        inst_id = sePos['instId']
        pos_side = sePos['posSide']
        swapnum = float(sePos['pos'])
        upl_val = float(sePos['upl'])
        upl_ratio_val = float(sePos['uplRatio'])
        avgPx = float(sePos['avgPx'])
        margin = float(sePos['margin'])

        log = (f"持仓: {inst_id} | 方向: {pos_side} | 合约张数: {swapnum:.4f} |"
               f"开仓均价: {float(sePos['avgPx']):.2f} | 当前价: {float(sePos['last']):.2f} | "
               f"未实现盈亏: {upl_val:.2f} | 收益率: {upl_ratio_val:.2f}")
        
        psr = [pos_side , swapnum , avgPx , upl_val , upl_ratio_val , log , inst_id , margin]
        
        apsr.append(psr)
    if not apsr:
        apsr = [['none', 0.0, 0.0,0.0, 0.0, 'None' , 'None' ,'0.0']]
    return apsr

#止盈止损
def takePstopL(tpr = None , slr = None , tpa = None , sla = None , tpslccy = None):
    global real_time_equility
    pos = get_positions()
    if pos:
        for posinfo in pos:
            print(f'当前持仓明细\n{posinfo[5]}')
            posside = posinfo[0]
            posid = posinfo[6]
            if posid == tpslccy:
                swapnum = posinfo[1]
                pt1 = pt2 = 'None'
                if posside == 'long':
                    if (tpr is not None and posinfo[4] >= tpr) or (tpa is not None and posinfo[3] >= tpa):
                        pt1 ='多头止盈触发'
                        #margin = posinfo[7]
                        tpnum = max(swapnum / 2 , swapMin)
                        oId = Neworder( posid , 'sell' , 'long' , tpnum)
                        plu = getOrder( posid , oId)
                        real_time_equility += plu
                        print(f"策略实时权益更新: {real_time_equility:.2f}货币")
                    
                    elif (slr is not None and posinfo[4] <= -slr) or (sla is not None and posinfo[3] <= sla):
                        pt1 = '多头止损触发'
                        #margin = posinfo[7]
                        slnum = swapnum
                        oId = Neworder( posid , 'sell' , 'long' , slnum)
                        plu = getOrder( posid , oId )
                        real_time_equility += plu
                        print(f"策略实时权益更新: {real_time_equility:.2f}货币")
                    
                    else:
                        pt1 = '多头止盈止损未触发'
                
                elif posside == 'short':
                    if  (tpr is not None and posinfo[4] >= tpr) or (tpa is not None and posinfo[3] >= tpa):
                        pt2 = '空头止盈触发'
                        #margin = posinfo[7]
                        tpnum = max(swapnum / 2 , swapMin)
                        oId = Neworder( posid , 'buy' , 'short' , tpnum)
                        plu = getOrder( posid , oId )
                        real_time_equility += plu
                        print(f"策略实时权益更新:{real_time_equility:.2f}货币")
                        
                    elif (slr is not None and posinfo[4] <= -slr) or (sla is not None and posinfo[3] <= sla):
                        pt2 ='空头止损触发'
                        #margin = posinfo[7]
                        slnum = swapnum
                        oId = Neworder (posid , 'buy' , 'short' , slnum)
                        plu = getOrder( posid , oId )
                        real_time_equility += plu
                        print(f"策略实时权益更新: {real_time_equility:.2f}货币") 
                        
                    else:
                        pt2 ='空头止盈止损未触发'
                
                print(pt1 + '|' + pt2)
            else:
                if posside == 'long' or posside == 'short':
                    print('当前持仓币种与策略币种不一致，选择不进行止盈止损')
          
#同步外部手动开平仓
def update_external_pnl():
    global real_time_equility , last_update_time , strategy_ord_history 
    
    try:
        # 获取当前时间（毫秒）
        current_time_ms = int(time.time() * 1000)
        
        # 首次运行：设为10分钟前，避免拉取太多历史
        if last_update_time == 0:
            last_update_time = current_time_ms - 1 * 60 * 1000  # 10分钟前
        
        # 查询历史订单（最多100条，OKX限制）
        resp = tradeAPI.get_orders_history(
            instType="SWAP",
            instId=instId,          # 只查策略币种！
            limit="20" ,
            begin=str(last_update_time),
            end=str(current_time_ms),
            state = 'filled'
        )
        
        if resp['code'] != '0':
            print(f"查询订单历史失败: {resp.get('msg')}")
            return
        
        orders = resp.get('data')
        if not orders:
            # 更新 last_sync_time 避免重复查空
            last_update_time = current_time_ms - 1 * 1000
            return
        
        # 按时间排序（OKX 不保证顺序）
        orders.sort(key=lambda x: int(x['cTime']))
        
        pnl_sum = 0.0
        for order in orders:
            if order['ordId'] in strategy_ord_history:
                continue
                
            pnl = float(order['pnl'])
            fee = float(order['fee'])
            actual_pnl = pnl + fee
            pnl_sum += actual_pnl
            print(f"→ 检测到外部订单 {order['ordId']} | 盈亏: {actual_pnl:.2f}")
            
            # 更新 last_sync_time 为该订单创建时间
            last_update_time = current_time_ms - 2 * 1000
        
        if pnl_sum != 0.0:
            old_eq = real_time_equility
            real_time_equility += pnl_sum
            print(f"🔄 同步外部盈亏: {pnl_sum:.2f} | 权益从 {old_eq:.2f} → {real_time_equility:.2f}")
        else:
            print("→ 无新成交订单")
            
    except Exception as e:
        print("同步外部盈亏异常:", e)

# 主函数
def main():
    global instId , barperiod , cash , lever , swapCcy , swapMin , cycleNum , real_time_equility , last_time_update
    
    #命令行参数，如果不想命令行输入，不如试着修改default条目然后直接run即可
    parser = argparse.ArgumentParser(description="hq3交易策略")
    parser.add_argument("--symbol", "-s",     type = str,   required = False,  default = 'SOL-USDT-SWAP',   help = "交易对, eg: BTC-USDT-SWAP ")
    parser.add_argument("--barperiod", "-b",  type = str,   required = False,  default = '15m',             help = "k线的bar , 如 1s 1m 3m 5m 15m .....")
    parser.add_argument("--cash", "-c",       type = float, required = False,  default = 2000.0,            help = "入场资金(USDT)")
    parser.add_argument("--lever", "-l",      type = str,   required = False,  default = '5',               help = "杠杆倍数")
    parser.add_argument("--swapCcy", "-sc",   type = float, required = False,  default = 1.0,               help = "合约面值")
    parser.add_argument("--swapMin", "-sm",   type = float, required = False,  default = 0.01,              help = "最小交易张数")
    parser.add_argument("--tpr", "-tr",       type = float, required = False,  default = 0.25,              help = "止盈比例")
    parser.add_argument("--slr", "-sr",       type = float, required = False,  default = 0.25,              help = "止损比例")
    parser.add_argument("--tpa", "-ta",       type = float, required = False,  default = None,              help = "止盈绝对值")
    parser.add_argument("--sla", "-sa",       type = float, required = False,  default = None,              help = "止损绝对值")
    args = parser.parse_args()

    #将参数赋值到全局变量
    instId = args.symbol
    barperiod = args.barperiod
    cash = args.cash
    lever = args.lever
    swapCcy = args.swapCcy
    swapMin = args.swapMin
    tpr = args.tpr
    slr = args.slr
    tpa = args.tpa
    sla = args.sla
    tpslccy = instId
    real_time_equility = cash
    
    #策略开始运行
    print(f"========== hqbt2 : BOll策略 ==========\n === 币类：{instId}  |  入场身价：{cash} U  |  杠杆：{lever} X ===")

    while True:
        try:
            cycleNum += 1
            current = time.time()
            if current - last_time_update >= 60:
                update_external_pnl()
                last_time_update = current
                
            print(f"\n===== 周期 {cycleNum}，时间: {time.strftime('%Y-%m-%d %H:%M:%S')} =====")
            setLever(instId , lever)
            takePstopL(tpr , slr , tpa , sla , tpslccy)
            getKlines(instId , barperiod)
            
        except Exception as e:
            print("策略执行出错:", e)
            time.sleep(10)
        
        time.sleep(1)

if __name__ == "__main__":
    main()