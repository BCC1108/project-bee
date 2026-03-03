# okTriangularArbitrage.py - 修正版三角套利策略
import asyncio
import json
from okx.websocket.WsPublicAsync import WsPublicAsync
from okx import Trade, Account
from env import getOkApiKey

# === API 配置 ===
apiKey, apiSecretKey, passphrase = getOkApiKey(
    "okTestKey", "okTestSecret", "passphrase"
)

# === 全局价格存储（实时更新）===
prices = {
    "BTC-USDT": 0.0,
    "ETH-BTC": 0.0,
    "ETH-USDT": 0.0
}

# === 套利参数 ===
ARBITRAGE_THRESHOLD = 0.004  # 0.4% 净收益才触发（覆盖 3*0.1% 手续费）
TRADE_USDT_QTY = 50         # 每次套利用 50 USDT

# === 交易函数（保持不变）===
def marketOrder(symbol, side, qty):
    tradeAPI = Trade.TradeAPI(
        apiKey, apiSecretKey, passphrase, False, flag="1"  # 模拟盘
    )
    result = tradeAPI.place_order(
        instId=symbol,
        tdMode="cash",
        side=side,
        ordType="market",
        sz=str(qty),  # OKX 要求字符串
    )
    print("币币市价下单结果:", result)
    return result

def getOrd(instId, orderId):
    tradeAPI = Trade.TradeAPI(apiKey, apiSecretKey, passphrase, False, flag="1")
    result = tradeAPI.get_order(instId=instId, ordId=orderId)
    print("获取订单信息:", result)
    fillPx, fillSz = 0.0, 0.0
    data = result.get("data", [])
    if data:
        total_px_sz = sum(float(item["fillPx"]) * float(item["fillSz"]) for item in data)
        total_sz = sum(float(item["fillSz"]) for item in data)
        avg_px = total_px_sz / total_sz if total_sz > 0 else 0
        return avg_px, total_sz
    return 0, 0

def getBalance(ccy):
    accountAPI = Account.AccountAPI(apiKey, apiSecretKey, passphrase, False, flag="1")
    acc = accountAPI.get_account_balance(ccy=ccy)
    try:
        balance = float(acc["data"][0]["details"][0]["availBal"])
        return balance
    except (KeyError, IndexError, TypeError):
        print("⚠️ 获取余额失败:", acc)
        return 0.0

# === 套利检测（持续运行）===
async def monitor_arbitrage():
    """独立任务：持续检查套利机会"""
    last_check = {k: None for k in prices}
    while True:
        await asyncio.sleep(0.5)  # 高频检查（可调）

        # 确保三个价格都已就绪
        if any(v is None for v in prices.values()):
            continue

        # 避免重复检测相同价格
        if prices == last_check:
            continue
        last_check = prices.copy()

        btc_usdt = prices["BTC-USDT" ]
        eth_btc = prices["ETH-BTC"]
        eth_usdt = prices["ETH-USDT"]

        # 模拟三角路径：USDT → BTC → ETH → USDT
        usdt_start = 1000.0
        btc = usdt_start / btc_usdt * 0.999      # USDT → BTC
        eth = btc / eth_btc * 0.999              # BTC → ETH
        usdt_end = eth * eth_usdt * 0.999        # ETH → USDT

        profit_rate = (usdt_end - usdt_start) / usdt_start
        print(f"[📊] 利润率: {profit_rate:.4%} | BTC={btc_usdt}, ETH/BTC={eth_btc}, ETH/USDT={eth_usdt}")

        if profit_rate >= ARBITRAGE_THRESHOLD:
            print("💎 发现套利机会！开始执行三笔交易...")
            await execute_arbitrage(btc_usdt, eth_btc, eth_usdt)

# === 执行套利（异步安全）===
async def execute_arbitrage(btc_usdt, eth_btc, eth_usdt):
    try:
        # Step 1: USDT → BTC
        bal_before = getBalance("USDT")
        print(f"交易前 USDT 余额: {bal_before}")
        if bal_before < TRADE_USDT_QTY:
            print("⚠️ USDT 余额不足，跳过套利")
            return

        ord1 = marketOrder("BTC-USDT", "buy", TRADE_USDT_QTY / btc_usdt * 0.99)
        if not ord1.get("data"):
            return
        ord_id1 = ord1["data"][0]["ordId"]
        price1, sz1 = getOrd("BTC-USDT", ord_id1)
        print(f"✅ 买入 BTC: {sz1:.6f} @ {price1:.2f}")

        # Step 2: BTC → ETH
        ord2 = marketOrder("ETH-BTC", "buy", sz1 * 0.99)
        if not ord2.get("data"):
            return
        ord_id2 = ord2["data"][0]["ordId"]
        price2, sz2 = getOrd("ETH-BTC", ord_id2)
        print(f"✅ 买入 ETH: {sz2:.6f} @ {price2:.6f} BTC")

        # Step 3: ETH → USDT
        ord3 = marketOrder("ETH-USDT", "sell", sz2 * 0.99)
        print(f"✅ 卖出 ETH: {ord3}")

        bal_after = getBalance("USDT")
        print(f"交易后 USDT 余额: {bal_after}, 盈利: {bal_after - bal_before:.2f} USDT")

    except Exception as e:
        print("❌ 套利执行异常:", e)

# === WebSocket 回调（仅更新价格）===
def publicCallback(msg_str):
    try:
        msg = json.loads(msg_str)
        if msg.get("event") == "error":
            print(f"❌ WebSocket 错误: {msg.get('msg')}")
            return
        if "data" not in msg or not msg["data"]:
            return

        data = msg["data"][0]
        symbol = data["instId"]
        price = float(data["last"])  # tickers 频道使用 "last"

        if symbol in prices:
            prices[symbol] = price
    except Exception as e:
        pass  # 后台静默

# === 主程序 ===
async def main():
    print("🚀 启动 OKX 三角套利策略（模拟盘）")
    print("订阅交易对: BTC-USDT, ETH-BTC, ETH-USDT")
    print("-" * 50)

    # ✅ 正确的 public WebSocket 地址
    url = "wss://ws.okx.com:8443/ws/v5/public"
    ws = WsPublicAsync(url=url)
    await ws.start()

    # ✅ 订阅 tickers 频道（非 index-candle！）
    args = [
        {"channel": "tickers", "instId": "BTC-USDT"},
        {"channel": "tickers", "instId": "ETH-BTC"},
        {"channel": "tickers", "instId": "ETH-USDT"},
    ]
    await ws.subscribe(args, publicCallback)

    # 启动套利监控任务
    asyncio.create_task(monitor_arbitrage())

    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 策略停止中...")
    finally:
        await ws.stop()

if __name__ == "__main__":
    asyncio.run(main())