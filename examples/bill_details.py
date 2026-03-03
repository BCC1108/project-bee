import json
import okx.Account as Account
from datetime import datetime


# API 初始化
apikey = "05cec9d9-5ad6-4b6a-853a-d93d316ca224"
secretkey = "F7A533F020CBC3F712DF39C7CDC437BC"
passphrase = "Jessy02.1108"

flag = "0"  # 实盘：0 , 模拟盘：1

accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)

# 查看账户账单详情 （近七日内）
result1 = accountAPI.get_account_bills()

# 获取当前账户交易手续费费率
result2 = accountAPI.get_fee_rates(
    instType="SPOT"
    #instId="BTC-USDT"
)
#处理json
data1 = json.loads(str(result1).replace("'", '"'))
data2 = json.loads(str(result2).replace("'", '"'))
if data1["code"] == "0":
    print("获取返回值成功，以下是账单详情：\n")

    for item in data1["data"]:
        print(f"币种: {item['ccy']}, 变动类型: {item['type']}, 余额: {item['bal']}, 变动时间: {item['ts']}")

if data2["code"] == "0":
    print("\n获取返回值成功，以下是当前账户交易手续费费率：\n")

    for item in data2["data"]:
        print(f"费率分组: {item['feeGroup'][0]['groupId']}, 挂单费率：{item['maker']}, 吃单费率: {item['taker']}")
