import okx.Finance.Savings as Savings
import json as json

# API 初始化
apikey = "05cec9d9-5ad6-4b6a-853a-d93d316ca224"
secretkey = "F7A533F020CBC3F712DF39C7CDC437BC"
passphrase = "Jessy02.1108"

flag = "0"  # 实盘: 0, 模拟盘: 1

SavingsAPI = Savings.SavingsAPI(apikey, secretkey, passphrase, False, flag)

result = SavingsAPI.get_saving_balance(ccy="USDT")

dic = json.loads(str(result).replace("'", '"'))

if dic["code"] == "0":
    print("获取返回值成功，以下是活期宝余额：\n")
    for item in dic["data"]:
        print(f"币种: {item['ccy']}, 持仓收益: {item['earnings']}, 币种数量: {item['amt']}, 已出借: {item['loanAmt']} , 未出借: {item['pendingAmt']}%")