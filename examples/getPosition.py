import okx.Account as Account

# ====== API Key 设置 ======
apiKey = "59a57b46-c3a2-4335-b1f4-471bddd81e1f"              #备注名 = "sumulated_trading_ok"   #权限 = "读取/交易"
apiSecretKey = "6AD5FC212DF33A066BAECC66BDC02949"
passphrase="Jessy02.1108"
flag = "1"     # 使用模拟盘 flag="1"

accountAPI = Account.AccountAPI(apiKey, apiSecretKey, passphrase, False, flag)


longSz = 0.0
shortSz = 0.0
zhiyingzhisun = []

# 查看持仓信息
def get_positions(): 
    global longSz , shortSz , zhiyingzhisun
    positions = accountAPI.get_positions()
    psdata = positions['data']

    if positions['code'] != "0":
        print("获取持仓信息失败，原因：" + positions['msg'])

    else:
        for sePos in psdata:
            zyzs = {'bilei':"", "sell_or_buy":"", "pos":"", "posSide":"" ,"upl":"" ,"uplRatio":""}
            print("持仓信息获取成功，具体信息如下：")
            print(f"币种：{sePos['instId']} 持仓方向：{sePos['posSide']} 持仓量：{sePos['pos']} \n开仓均价：{sePos['avgPx']} 当前价：{sePos['last']} 手续费：{sePos['fee']} 未实现盈亏：{sePos['upl']} 未实现收益率：{sePos['uplRatio']}%")
            
            zyzs['bilei'] = sePos['instId']
            zyzs["pos"] = sePos['pos']
            zyzs["posSide"] = sePos['posSide']
            zyzs['upl'] = sePos['upl']
            zyzs['uplRatio'] = sePos['uplRatio']
            zhiyingzhisun.append(zyzs)

            if sePos['posSide'] == "long":
                longSz = sePos['pos']
            
            elif sePos['posSide'] == "short":
                shortSz = sePos['pos']
            
            else:
                print("当前无持仓")

    
get_positions()

def get_zhiyingzhisun():
    if zhiyingzhisun:
        for item in zhiyingzhisun:
            if item['posSide'] == "long":
                if float(item['uplRatio']) >= 10.0 or float(item['upl']) >= 20.0:     #止盈
                    item['sell_or_buy'] = "sell"
                elif float(item['uplRatio']) <= -8.0 or float(item['upl']) <= -20.0:  #止损
                    item['sell_or_buy'] = "sell"
            
            elif item['posSide'] == "short":  # ← 必须和上面的 if 对齐！
                if float(item['uplRatio']) >= 10.0 or float(item['upl']) >= 20.0:     #止盈
                    item['sell_or_buy'] = "buy"
                elif float(item['uplRatio']) <= -8.0 or float(item['upl']) <= -20.0:  #止损
                    item['sell_or_buy'] = "buy"

        
               
print(f"当前多头持仓量为：{longSz}，空头持仓量为：{shortSz}")