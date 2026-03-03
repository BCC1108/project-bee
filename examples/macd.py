import argparse
import pandas as pd
from okx import MarketData
from okx import Trade
import time
import socket
import requests
import okx.Account as Account

# ====== API Key 设置 ======
apiKey = "59a57b46-c3a2-4335-b1f4-471bddd81e1f"
apiSecretKey = "6AD5FC212DF33A066BAECC66BDC02949"
passphrase = "Jessy02.1108"
flag = "1"  # 使用模拟盘

# ====== API 初始化 ======
tradeAPI = Trade.TradeAPI(
    apiKey, apiSecretKey, passphrase, use_server_time=False, flag=flag)
AccountAPI = Account.AccountAPI(
    apiKey, apiSecretKey, passphrase, use_server_time=False, flag=flag)
marketApi = MarketData.MarketAPI(
    apiKey, apiSecretKey, passphrase, use_server_time=False, flag=flag)
accountAPI = Account.AccountAPI(apiKey, apiSecretKey, passphrase, False, flag)

# ====== 全局变量 ======
instId = ""
qty = 0.0
leverL = 3
leverS = 3
longSz = 0.0
shortSz = 0.0
clycleNum = 0
zhiyingzhisun = []


# MACD信号策略
def macd_strategy(
    macd,
    signal,
    in_uptrend=False,
    in_downtrend=False,
    bullish_momentum=False,
    bearish_momentum=False
):
    global instId, qty, longSz, shortSz

    if (
        isinstance(macd, pd.Series)
        and isinstance(signal, pd.Series)
        and len(macd) > 1
        and len(signal) > 1
    ):
        # ========== 做多条件：金叉 + 趋势 + 动量 ==========
        if macd.iloc[-1] > signal.iloc[-1]:  # 金叉
            if not in_uptrend:
                print("金叉但不在上涨趋势（价格 < EMA200），忽略")
                return
            if not bullish_momentum:
                print("金叉但动量不足（柱状图未放大），忽略")
                return

            print("✅ 有效金叉：趋势向上 + 动量增强，建议做多")

            if longSz < 1:  # 未开多则开多
                print("开仓做多")
                ord_result = NewOrd(instId, "buy", qty, "long")
                if ord_result.get("code") == "0" and len(ord_result.get("data", [])) > 0:
                    orderId = ord_result["data"][0]["ordId"]
                    fillPx, fillSz = getOrder(instId, orderId)
                    if fillSz > 0:
                        print(f"开多单已成交，成交数量（币）: {fillSz}")
                    else:
                        print("开多单未成交或成交数量为0")
                else:
                    print("开多单提交失败")

            if shortSz > 0:  # 有空头则平空
                print("平空")
                ord_result_close = NewOrd(instId, "buy", shortSz, "short")
                if ord_result_close.get("code") == "0" and len(ord_result_close.get("data", [])) > 0:
                    orderId_close = ord_result_close["data"][0]["ordId"]
                    fillPx_close, fillSz_close = getOrder(instId, orderId_close)
                    if fillSz_close > 0:
                        print(f"平空单已成交，成交数量（币）: {fillSz_close}")
                        shortSz = 0.0
                    else:
                        print("平空单未成交")
                else:
                    print("平空单提交失败")
            else:
                print("当前有多头无空头，观望")

        # ========== 做空条件：死叉 + 趋势 + 动量 ==========
        elif macd.iloc[-1] < signal.iloc[-1]:  # 死叉
            if not in_downtrend:
                print("死叉但不在下跌趋势（价格 > EMA200），忽略")
                return
            if not bearish_momentum:
                print("死叉但动量不足（柱状图未扩大负值），忽略")
                return

            print("✅ 有效死叉：趋势向下 + 动量增强，建议做空")

            if shortSz < 1:  # 未开空则开空
                print("开仓做空")
                ord_result = NewOrd(instId, "sell", qty, "short")
                if ord_result.get("code") == "0" and len(ord_result.get("data", [])) > 0:
                    orderId = ord_result["data"][0]["ordId"]
                    fillPx, fillSz = getOrder(instId, orderId)
                    if fillSz > 0:
                        print(f"开空单已成交，成交数量（币）: {fillSz}")
                    else:
                        print("开空单未成交")
                else:
                    print("开空单提交失败")

            if longSz > 0:  # 有多头则平多
                print("平多")
                ord_result_close = NewOrd(instId, "sell", longSz, "long")
                if ord_result_close.get("code") == "0" and len(ord_result_close.get("data", [])) > 0:
                    orderId_close = ord_result_close["data"][0]["ordId"]
                    fillPx_close, fillSz_close = getOrder(instId, orderId_close)
                    if fillSz_close > 0:
                        print(f"平多单已成交，成交数量（币）: {fillSz_close}")
                        longSz = 0.0
                    else:
                        print("平多单未成交")
                else:
                    print("平多单提交失败")
            else:
                print("当前有空头无多头，观望")

        else:
            print("MACD = Signal，处于关键平衡点")

    else:
        print("数据不足，无法计算 MACD 信号")


# 获取K线数据
def getKlines(instId, bar, limit):
    data = marketApi.get_candlesticks(instId=instId, bar=bar, limit=limit)
    klines_data = data.get("data", [])
    if all(isinstance(i, list) for i in klines_data):
        df = pd.DataFrame(
            klines_data,
            columns=["ts", "o", "h", "l", "vol", "c", "volCcy", "volCcyQuote", "confirm"],
        )
        df["c"] = pd.to_numeric(df["c"])
        ema200 = df["c"].ewm(span=200, adjust=False).mean()
        df["o"] = pd.to_numeric(df["o"])

        exp1 = df["c"].ewm(span=21, adjust=False).mean()
        exp2 = df["c"].ewm(span=55, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal_line
        
        # 趋势判断
        close = df["c"].iloc[-1]
        in_uptrend = close > ema200.iloc[-1]
        in_downtrend = close < ema200.iloc[-1]
        #动量确认
        bullish_momentum = (hist.iloc[-1] > 0) and (hist.iloc[-1] > hist.iloc[-2])
        bearish_momentum = (hist.iloc[-1] < 0) and (hist.iloc[-1] < hist.iloc[-2])

        # === 调用策略 ===
        macd_strategy(
            macd=macd,
            signal=signal_line,
            in_uptrend=in_uptrend,
            in_downtrend=in_downtrend,
            bullish_momentum=bullish_momentum,
            bearish_momentum=bearish_momentum
        )
    else:
        print("Invalid klines data structure.")


# 开仓或平仓
def NewOrd(instId, side, qty, positionSide):
    try:
        qty_num = float(qty)
        sz_value = int(round(qty_num))
        if sz_value < 1:
            print(f"警告：下单数量 {qty} < 1 张，USDT-SWAP 最小1张，跳过。")
            return {"code": "-1", "msg": "数量不足1张", "data": []}

        result = tradeAPI.place_order(
            instId=instId,
            ccy="USDT",
            tdMode="isolated",
            side=side,
            posSide=positionSide,
            ordType="market",
            sz=str(sz_value),
        )

        print(f"订单提交返回结果 Scode: {result['data'][0]['sCode']}")
        if result.get("code") != "0":
            print(f"下单失败: {result.get('msg', '未知错误')}")
            return result

        data_list = result.get("data")
        if not data_list or len(data_list) == 0:
            print("下单失败: 返回数据为空")
            return result

        first_order_data = data_list[0]
        if "ordId" not in first_order_data:
            print(f"下单失败: 缺少 ordId: {first_order_data}")
            return result

        order_id = first_order_data["ordId"]
        print(f"订单ID: {order_id}")
        return result

    except (socket.timeout, requests.exceptions.Timeout) as e:
        print(f"网络超时，下单失败: {e}")
        return {"code": "-1", "msg": f"网络超时: {e}", "data": []}
    except Exception as e:
        print(f"下单发生未知异常: {e}")
        return {"code": "-1", "msg": f"未知异常: {e}", "data": []}


# 查询订单
def getOrder(instId, orderId):
    try:
        if not orderId:
            print("错误: 订单ID为空")
            return 0, 0

        result = tradeAPI.get_order(instId, orderId)
        if result.get("code") != "0":
            print(f"查询订单失败: {result.get('msg', '未知错误')}")
            return 0, 0

        data_list = result.get("data")
        if not data_list or len(data_list) == 0:
            print(f"未找到订单 {orderId} 的数据")
            return 0, 0

        order_info = data_list[0]
        print(f"产品类型: {order_info['instType']} | 状态: {order_info['state']} | "
              f"模式: {order_info['tdMode']} | 更新时间: {order_info['uTime']}")

        fill_px_str = order_info.get("fillPx")
        fill_sz_str = order_info.get("fillSz")

        if fill_px_str is None or fill_sz_str is None:
            print(f"订单 {orderId} 尚未成交")
            return 0, 0

        fillPx = float(fill_px_str)
        fillSz = float(fill_sz_str)

        state = order_info.get("state")
        if state in ("filled", "partially_filled"):
            print(f"订单 {orderId} 成交: 价格 {fillPx}, 数量（币） {fillSz}")
            return fillPx, fillSz
        elif state == "canceled":
            print(f"订单 {orderId} 已撤销")
            return 0, 0
        else:
            print(f"订单 {orderId} 状态 {state}, 但有成交记录 {fillPx}, {fillSz}")
            return fillPx, fillSz

    except Exception as e:
        print(f"查询订单 {orderId} 异常: {e}")
        return 0, 0


# 设置杠杆倍数
def setLeverage(instId, leverL, leverS):
    try:
        p1 = '多头杠杆未配置'
        p2 = '空头杠杆未配置'

        resp = AccountAPI.set_leverage(
            instId=instId, lever=leverL, mgnMode="isolated", posSide="long"
        )
        if resp.get("code") == "0":
            p1 = f"多头杠杆: {resp['data'][0]['lever']} X"

        resp = AccountAPI.set_leverage(
            instId=instId, lever=leverS, mgnMode="isolated", posSide="short"
        )
        if resp.get("code") == "0":
            p2 = f"空头杠杆: {resp['data'][0]['lever']} X"

        print(f"杠杆配置: {p1}, {p2}")

    except Exception as e:
        print(f"设置杠杆异常: {e}")


# 查看持仓信息
def get_positions():
    global longSz, shortSz, zhiyingzhisun
    zhiyingzhisun.clear()  # ⚠️ 清空旧数据！

    positions = accountAPI.get_positions()
    if positions['code'] != "0":
        print("获取持仓失败:", positions['msg'])
        return

    psdata = positions.get('data', [])
    if not psdata:
        longSz = 0.0
        shortSz = 0.0
        print("当前无持仓")
        return

    for sePos in psdata:
        inst_id = sePos['instId']
        pos_side = sePos['posSide']
        pos_val = float(sePos['pos'])
        upl_val = float(sePos['upl'])
        upl_ratio_val = float(sePos['uplRatio'])

        print(f"持仓: {inst_id} | 方向: {pos_side} | 张数: {pos_val} | "
              f"均价: {sePos['avgPx']} | 当前价: {sePos['last']} | "
              f"未实现盈亏: {upl_val} | 收益率: {upl_ratio_val}")

        # 存入止盈止损列表（全部为 float）
        zhiyingzhisun.append({
            'bilei': inst_id,
            'pos': pos_val,
            'posSide': pos_side,
            'upl': upl_val,
            'uplRatio': upl_ratio_val
        })

        if pos_side == "long":
            longSz = pos_val
        elif pos_side == "short":
            shortSz = pos_val


# 查看是否需要止盈止损
def get_zhiyingzhisun():
    global zhiyingzhisun
    if not zhiyingzhisun:
        print("无持仓，无需止盈止损")
        return

    for item in zhiyingzhisun:
        pos_side = item['posSide']
        pos = item['pos']
        upl = item['upl']
        upl_ratio = item['uplRatio']

        if pos_side == "long":
            if upl_ratio >= 0.1 or upl >= 20.0:
                print(f"多头止盈触发: {item['bilei']}")
                NewOrd(item['bilei'], "sell", pos, "long")
            elif upl_ratio <= -0.08 or upl <= -20.0:
                print(f"多头止损触发: {item['bilei']}")
                NewOrd(item['bilei'], "sell", pos, "long")
            else:
                print("Long止盈止损未执行")

        elif pos_side == "short":
            if upl_ratio >= 0.1 or upl >= 20.0:
                print(f"空头止盈触发: {item['bilei']}")
                NewOrd(item['bilei'], "buy", pos, "short")
            elif upl_ratio <= -0.08 or upl <= -20.0:
                print(f"空头止损触发: {item['bilei']}")
                NewOrd(item['bilei'], "buy", pos, "short")
            else:
                print("Short止盈止损未执行")


# 主函数
def main():
    global instId, qty, leverL, leverS, clycleNum

    parser = argparse.ArgumentParser(description="MACD 交易策略")
    parser.add_argument("--symbol", "-s", type=str, required=True, help="交易对，如 BTC-USDT-SWAP")
    parser.add_argument("--qty", "-q", type=float, required=True, help="下单数量（张）")
    parser.add_argument("--leverL", "-lL", type=int, default=3, help="开多杠杆倍数")
    parser.add_argument("--leverS", "-lS", type=int, default=3, help="开空杠杆倍数")
    args = parser.parse_args()

    instId = args.symbol
    qty = args.qty
    leverL = args.leverL
    leverS = args.leverS

    print(f"合约：{instId}, 下单量：{qty} 张，开多杠杆：{leverL} 倍，开空杠杆：{leverS} 倍")
    interval = "1m"
    limit = 100
    print(f"| === MACD信号策略: {instId} === | {interval} * latest {limit} bars |")

    last_set_leverage_time = 0

    while True:
        try:
            clycleNum += 1
            current_time = time.time()
            print(f"\n===== 周期 {clycleNum}，时间: {time.strftime('%Y-%m-%d %H:%M:%S')} =====")

            get_positions()          # 同步持仓（权威来源）
            get_zhiyingzhisun()      # 检查止盈止损
            
            # 每10分钟设置一次杠杆
            if current_time - last_set_leverage_time >= 600:
                last_set_leverage_time = current_time
                setLeverage(instId, leverL, leverS)

            getKlines(instId, interval, limit)

        except (socket.timeout, requests.exceptions.Timeout) as e:
            print("网络超时，等待后重试:", e)
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            print("策略执行出错:", e)
            time.sleep(10)

        time.sleep(60)


if __name__ == "__main__":
    main()
    