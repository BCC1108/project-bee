# klines.py - 静默模式行情监听（后台实时更新，前台定时显示）
import asyncio
import json
from okx.websocket.WsPublicAsync import WsPublicAsync

SYMBOLS = ["BTC-USDT", "ETH-BTC", "ETH-USDT"]
latest_prices = {symbol: 0.0 for symbol in SYMBOLS}
last_display = latest_prices.copy()  # 用于判断是否变化

# ===== 新增：控制台显示间隔（秒）=====
DISPLAY_INTERVAL = 5  # 每5秒打印一次状态
# ===================================

def publicCallback(msg_str):
    """仅更新数据，不打印每条消息（静默模式）"""
    try:
        msg = json.loads(msg_str)
        if msg.get("event") == "error":
            print(f"❌ 订阅错误: {msg.get('msg', 'Unknown')}, code: {msg.get('code')}")
            return
        if "data" not in msg or not msg["data"]:
            return  # 忽略心跳、订阅确认等

        data = msg["data"][0]
        symbol = data["instId"]
        price = float(data["last"])

        if symbol in latest_prices:
            latest_prices[symbol] = price
        # 不在这里 print！

    except Exception as e:
        pass  # 后台静默运行，可选记录日志

async def display_status():
    """独立任务：定期打印状态"""
    global last_display
    while True:
        await asyncio.sleep(DISPLAY_INTERVAL)
        
        # 判断是否有价格更新
        changed = any(latest_prices[s] != last_display[s] for s in SYMBOLS)
        all_ready = all(v is not None for v in latest_prices.values())
        
        if changed or not all_ready:
            status = "🟢 就绪" if all_ready else "🟡 等待中"
            print(f"[{asyncio.get_event_loop().time():.0f}] 📊 价格: {latest_prices} | {status}")
            last_display = latest_prices.copy()

async def main():
    print("🚀 启动 OKX 行情监听（静默模式）")
    print("订阅交易对:", SYMBOLS)
    print(f"📈 终端每 {DISPLAY_INTERVAL} 秒刷新一次状态（后台数据实时更新）")
    print("-" * 60)

    url = "wss://ws.okx.com:8443/ws/v5/public"
    ws = WsPublicAsync(url=url)
    
    try:
        await ws.start()
    except Exception as e:
        print("❌ WebSocket 连接失败:", e)
        return

    args = [{"channel": "tickers", "instId": symbol} for symbol in SYMBOLS]
    await ws.subscribe(args, publicCallback)

    # 启动独立的状态显示任务
    asyncio.create_task(display_status())

    # 主循环（保持程序运行）
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在关闭...")
    finally:
        await ws.stop()

if __name__ == "__main__":
    asyncio.run(main())