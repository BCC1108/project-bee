import okx.Funding as Funding
import json as json

# API 初始化
apikey = "05cec9d9-5ad6-4b6a-853a-d93d316ca224"
secretkey = "F7A533F020CBC3F712DF39C7CDC437BC"
passphrase = "Jessy02.1108"

flag = "0"  # 实盘: 0, 模拟盘: 1

fundingAPI = Funding.FundingAPI(apikey, secretkey, passphrase, False, flag)

# 获取账户资产估值
result = fundingAPI.get_asset_valuation()

dic = json.loads(str(result).replace("'", '"'))

if dic["code"] == "0":
    print("获取返回值成功，以下是账户资产估值：\n")
    for item in dic["data"]:
        print(f"总资产估值(USD): {item['totalBal']} ,资金账户: {item['details']['funding']}, 交易账户: {item['details']['trading']}, 金融账户: {item['details']['earn']} ")



