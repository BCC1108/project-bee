import pandas as pd
import vectorbt as vbt

# === 1. 构造秒级 OHLC 数据（3 小时，每小时 3 根K线）===
dates = pd.date_range('2025-01-01 10:00:00', periods=9, freq='20min')
price = pd.DataFrame({
    'open':  [100, 101, 102,  98, 97, 96,  99, 100, 101],
    'high':  [103, 104, 105,  99, 98, 97, 102, 103, 104],
    'low':   [99,  100, 101,  96, 95, 94,  98, 99, 100],
    'close': [101, 102, 103,  97, 96, 95, 100, 101, 102]
}, index=dates)

print(price)
# === 2. 重采样到 1h ===
df_h = price.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last'})

print("=== 小时级K线 ===")
print(df_h)

# === 3. 生成信号（基于前1小时）===
# 假设策略：前1小时收阳（close > open）则做多
entries_h = (df_h['close'].shift(1) > df_h['open'].shift(1))
exits_h = pd.Series(False, index=df_h.index)  # 暂不退出

print("\n=== 小时信号（基于前1小时）===")
print(entries_h)

# === 4. 映射到秒级 ===
def resamplesig2origion(sig, orig_idx):
    triggers = sig[sig].index
    if len(triggers) == 0:
        return pd.Series(False, index=orig_idx)
    pos = orig_idx.get_indexer(triggers, method='bfill')
    result = pd.Series(False, index=orig_idx)
    result.iloc[pos[pos != -1]] = True
    return result

entries_s = resamplesig2origion(entries_h, price.index)
print("\n=== 秒级信号 ===")
print(entries_s)

# === 5. 回测（TP=2%）===
pf = vbt.Portfolio.from_signals(
    price,
    entries=entries_s,
    exits=False,
    tp_stop=0.02,
    init_cash=10000,
    freq='20min'
)

print("\n=== 订单记录 ===")
orders = pf.orders.records_readable
print(orders[['Timestamp', 'Side', 'Price']])

print("\n=== 交易记录 ===")
trades = pf.trades.records_readable
if not trades.empty:
    print(trades)