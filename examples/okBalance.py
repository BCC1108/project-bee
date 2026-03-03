import json
from okx import Account
from env import getOkApiKey

# === 配置 ===
apiKey, apiSecretKey, passphrase = getOkApiKey(
    "okApiKey", "okApiSecret", "passphrase"
)

# 初始化 OKX 账户 API（flag="0" 表示实盘，若用模拟盘请改为 "1"）
accountAPI = Account.AccountAPI(apiKey, apiSecretKey, passphrase, False, flag="0")


# 你关心的币种列表（按需修改）
TARGET_CCYS = ["BTC", "ETH", "OKB", "USDT"]

def safe_get(data, key, default="N/A"):
    """安全获取字典值，避免空字符串或 None"""
    val = data.get(key, default)
    return val if val not in ("", None) else default

# 步骤1：先尝试获取全量资产（API 自动返回的非零币种）===
print("正在查询账户资产...\n")
result_all = accountAPI.get_account_balance()

all_details = {}
total_eq = "N/A"

if result_all.get("code") == "0" and "data" in result_all:
    account_data = result_all["data"][0]
    total_eq = account_data.get("totalEq", "N/A")
    details_list = account_data.get("details", [])
    all_details = {d["ccy"]: d for d in details_list}
else:
    print("❌ 全量资产查询失败:", result_all.get("msg", "Unknown error"))

# 步骤2：补查目标币种（确保不遗漏，即使余额为0也可能需要显示）===
for ccy in TARGET_CCYS:
    if ccy not in all_details:
        print(f"补查币种: {ccy}")
        res = accountAPI.get_account_balance(ccy=ccy)
        if res.get("code") == "0" and res.get("data"):
            details_list = res["data"][0].get("details", [])
            if details_list:
                detail = details_list[0]
                all_details[ccy] = detail
            else:
                # 即使无资产，也可保留一个占位符（可选）
                # 这里选择不添加，后续会显示“无数据”
                pass
        else:
            print(f"  ❌ 查询失败: {res.get('msg', 'No message')}")

# 步骤3：输出结果 ===
print("\n=== 账户总览 ===")
print(f"账户总权益 (USD): {total_eq}\n")

print("=== 各币种明细 ===")
for ccy in TARGET_CCYS:
    if ccy in all_details:
        d = all_details[ccy]
        avail_bal = safe_get(d, "availBal", "0")
        eq_usd = safe_get(d, "eqUsd", "N/A")
        upl = safe_get(d, "upl", "0")
        print(f"币种: {ccy}")
        print(f"  可用余额: {avail_bal} {ccy}")
        print(f"  权益 (USD): {eq_usd}")
        print(f"  未实现盈亏: {upl} {ccy}")
        print("-" * 30)
    else:
        print(f"币种: {ccy} — 无数据（可能未支持或完全无资产）")
        print("-" * 30)
