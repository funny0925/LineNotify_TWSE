"""
===版本紀錄===
"""

"""
111/1/4
1.新增成交量異常通知
2.取消溢價差內含成本($70)
----------
111/1/10
1.成交量異常(last)通知參數調整
2.新增成交量異常(last)多空力道分布警示
3.調整觀察名單
4.調整排程時間
----------
111/1/11
1.調整觀察名單
2.成交量異常(last)通知參數調整
3.調整排程時間
4.高額掛單通知新增(漲跌幅)
5.更新總發行股數資料來源至2021版
----------
111/1/12
1.改回系統時間，待上版heroku在調整為GMT+8
----------
111/3/11
1.調整初上市(-5)、初上櫃(-10)分數計算邏輯
2.提高溢價差(百分比%)分數(+5/per)
----------
111/3/22
1.調整部分文字說明
2.刪除新申購資訊Alert內部分無功能變數
3.新增各類股Alert(16:00)
4.新增三大法人買賣超前15檔資訊(17:00)
5.合併高額掛單通知改為def藉由變數(a,b)控制
6.修正公開申購Alert每年需更換網址問題                                                    
----------
111/3/25
1.修正高額掛單alert內 漲停市價單取消Alert (Beta)
----------
111/3/29
1.修正公開申購Alert 判斷新上市、新上櫃，改由in ['新上市','新上櫃']
2.調整買賣超15檔Alert推播時間(新增間隔5s)
----------
111/3/30
1.修正高額掛單、成交量異常通知新增驗證工具
----------
111/11/1
1.修正新申購資訊預估收益百分比
"""

# --------------------使用函數庫--------------------#

from flask import Flask, request, abort
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import numpy as np
import json
import requests.packages.urllib3  # 用於消除requests報錯
requests.packages.urllib3.disable_warnings()  # 用於消除requests報錯
import datetime

scheduler = BlockingScheduler(timezone="Asia/Taipei")

# --------------------高額掛單設定名單--------------------#

myList = [2603, 2609, 8279, 6271, 3406, 2368, 2340, 9951, 8099, 2412, 1315, 6176, 2355, 2303, 9958, 6591, 1402, 2105,
          3708, 1712, 9103, 4142, 3008, 2330, 9105, 5465, 3049, 2498, 6197, 6715, 2002, 2371, 3293, 8933, 3062, 6121,
          2324, 6426, 3373, 1587, 1314, 2455, 3264, 2404, 2206, 6125, 3036, 1303, 6560, 9935, 6477, 2478, 8050, 5220,
          3376, 2888, 5371, 5880, 6679, 2428, 6274, 2880, 3450, 5609, 2812, 3045, 6251, 6288, 6235, 6533, 3532, 6416,
          1714, 6257, 2417, 2301, 1301, 3484, 8086, 9904, 3083, 2360, 1526, 8213, 5876, 2472, 1907, 6561, 3163, 3712,
          2352, 2347, 3323, 2106, 2312, 3056, 9941, 1326, 2395, 2610, 3029, 1734, 6582, 3044, 8299, 6237, 1586, 1514,
          3030, 6443, 2887, 3131, 2892, 2454, 6230, 2344, 2441, 2207, 2882, 6214, 2201, 6141, 3413, 2505, 2426, 4736,
          1519, 6547, 2392, 4119, 4536, 8261, 6239, 2356, 3047, 9945, 6116, 8069, 8454, 5521, 6196, 1312, 1102, 9938,
          2881, 2464, 3015, 6409, 1476, 3017, 5274, 4915, 3703, 3272, 6213, 2367, 3483, 3576, 3042, 3078, 6187, 2618,
          2912, 1609, 5474, 6104, 5209, 3016, 1216, 6510, 9919, 2884, 4147, 9921, 2885, 2520, 1736, 6414, 4906, 2891,
          6191, 3645, 2439, 6589, 3217, 5483, 2388, 1605, 2421, 2332, 3032, 4551, 3014, 9910, 6269, 3711, 1309, 3005,
          3669, 6683, 2337, 3081, 6706, 3605, 5306, 8046, 1477, 2614, 2383, 3227, 3552, 6504, 2231, 2357, 1760, 4128,
          2408, 1785, 3152, 6488, 2886, 3529, 2108, 1101, 3231, 4953, 3325, 3213, 3533, 2323, 6282, 5347, 2049, 1717,
          4938, 2449, 2382, 3653, 3324, 3481, 3680, 3034, 2376, 6441, 4123, 2504, 6223, 1325, 6278, 1515, 5309, 5469,
          9914, 8081, 3189, 6438, 6669, 2387, 3443, 2308, 2492, 2313, 1727, 2353, 3596, 4743, 6446, 2377, 2409, 2615,
          6285, 3374, 5457, 2379, 2345, 4133, 2458, 3037, 6538, 3704, 6188, 2317, 3105, 2474, 2481, 4968, 3540, 2327,
          2457, 2883, 2889, 2890, 6505, 2801, 4904, 3702, 2385, 2542, 2014, 2606, 2354]

"""
# =====名單測試===== #
https://kgieworld.moneydj.com/z/bcd/GetStkRTDataJSON.djjson?B=%s&xyz=
https://marketinfo.api.cnyes.com/mi/api/v1/TWS%3Axxxx%3ASTOCK/directorholder/2021
https://ws.api.cnyes.com/ws/api/v1/quote/quotes/TWS:%s:STOCK
# =====名單測試===== #
"""

myList_3 = range(0, 35, 1)  # 用於類股Alert 總共29種類股 #第30項為加權指數

def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        'message': msg
    }
    r = requests.post("https://notify-api.line.me/api/notify", verify=False, headers=headers, params=payload)
    return r.status_code

"""
# =====成交量異常Alert===== #
"""

def s_Yesterday_Volume(stock_no, a, b):
    url_last = 'https://kgieworld.moneydj.com/z/bcd/GetStkRTDataJSON.djjson?B=%s&xyz=' % stock_no

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    r_last = requests.get(url_last, verify=False, headers=headers)
    html_last = r_last.text

    if html_last[-2] == ',':
        return ""

    data_last = json.loads(html_last)

    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")
    datetime_format_check = datetime_dt.strftime("%Y/%m/%d")

    if data_last['Date'] != datetime_format_check:
        return ""

    """
    datetime_format = new_dt.strftime("%Y/%m/%d %H:%M:%S")
    """

    stock_TV = int(np.array(data_last['TV']))  # 本日交易量
    stock_PV = int(np.array(data_last['PV']))  # 昨日交易量
    stock_Price = float(np.array(data_last['P']))  # 即時股價
    stock_Yesterday = float(np.array(data_last['PC']))  # 昨天收盤
    stock_Variety = np.array(data_last['sUPR'])
    stock_Name = np.array(data_last['Name'])  # 股票名稱

    # ----------------------------------------------#
    if stock_PV == 0:
        stock_last = 0

    else:
        stock_last = int(stock_TV) / int(stock_PV)

    stock_last_dis = round(stock_last, 1)

    if np.array(data_last['sUPFlag']) == 'DOWN':
        stock_Way = '-'

    else:
        stock_Way = '+'

    stock_AW = float(np.array(data_last['sAw']))
    stock_BW = float(np.array(data_last['sBw']))

    if int(stock_AW) == 80:
        stock_Analyze = '\n※絕對外盤！'

    elif int(stock_AW) >= 70:
        stock_Analyze = '\n※相對外盤！'

    elif int(stock_AW) >= 60:
        stock_Analyze = '\n※偏向外盤！'

    elif int(stock_BW) == 80:
        stock_Analyze = '\n※絕對內盤！'

    elif int(stock_BW) >= 70:
        stock_Analyze = '\n※相對內盤！'

    elif int(stock_BW) >= 60:
        stock_Analyze = '\n※偏向內盤！'

    else:
        stock_Analyze = ''

    # ----------------------------------------------#

    if stock_last >= a and int(stock_TV) >= b:
        my_Text_last = '\n【' + datetime_format + '】\n股票名稱：' + str(stock_Name) + ' - ' + str(
            stock_no) + '\n目前股價：' + str(format(float(stock_Price), ',')) + ' (' + str(stock_Way) + str(
            stock_Variety) + ')\n成交量：' + str(format(int(stock_TV), ',')) + '張\n相較昨日：' + str(
            stock_last_dis) + '倍' + str(stock_Analyze)
        return my_Text_last

    else:
        return ""

'''
# =====高額掛單Alert===== #
'''


def s_High_Order(stock_no):
    url = 'https://marketinfo.api.cnyes.com/mi/api/v1/TWS%%3A%s%%3ASTOCK/directorholder/2021' % stock_no

    """
    https://marketinfo.api.cnyes.com/mi/api/v1/TWS%3Axxxx%3ASTOCK/directorholder/2020
    """

    url_Five = 'https://kgieworld.moneydj.com/z/bcd/GetStkRTDataJSON.djjson?B=%s&xyz=' % stock_no

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    r = requests.get(url, verify=False, headers=headers)
    r_Five = requests.get(url_Five, verify=False, headers=headers)
    html_doc = r.text
    html_doc_Five = r_Five.text

    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")
    datetime_format_check = datetime_dt.strftime("%Y/%m/%d")

    """
    datetime_format = new_dt.strftime("%Y/%m/%d %H:%M:%S")
    """

    data = json.loads(html_doc)
    a = np.array(data['data']['categories'])

    if a is None or html_doc_Five[-2] == ',':
        return ""

    data_Five = json.loads(html_doc_Five)

    if data_Five['Date'] != datetime_format_check:
        return ""

    stock_Name = data_Five['Name']
    stock_Price = str(float(data_Five['P']))
    stock_amount = int(a[12]['amount']) / 1000
    stock_Variety = data_Five['sUPR']

    if data_Five['sUPFlag'] == 'DOWN':
        stock_Way = '-'

    else:
        stock_Way = '+'

    # ----------------------------------------------#

    a_Five_BS = int(np.array(data_Five['BS']))

    if int(a_Five_BS) / int(stock_amount) >= 0.01 and str(np.array(data_Five['B'])) != '市價':
        # if int(a_Five_BS) / int(stock_amount) >= 0.01 and (str(np.array(data_Five['B'])) != '市價' or np.array(data_Five['B2']) != np.array(data_Five['P'])):

        a_Five_BS_1 = "\n大額買單：" + format(int(a_Five_BS), ',') + "張\n價格：" + str(
            np.array(data_Five['B'])) + ' 【第一順位】'

    else:
        a_Five_BS_1 = ""

    # ----------------------------------------------#

    a_Five_BS2 = int(np.array(data_Five['BS2']))

    if int(a_Five_BS2) / int(stock_amount) >= 0.01 and np.array(data_Five['B2']) != np.array(data_Five['P']):
        a_Five_BS_2 = "\n大額買單：" + format(int(a_Five_BS2), ',') + "張\n價格：" + str(
            np.array(data_Five['B2'])) + ' 【第二順位】'

    else:
        a_Five_BS_2 = ""

    # ----------------------------------------------#

    a_Five_BS3 = int(np.array(data_Five['BS3']))

    if int(a_Five_BS3) / int(stock_amount) >= 0.01:
        a_Five_BS_3 = "\n大額買單：" + format(int(a_Five_BS3), ',') + "張\n價格：" + str(
            np.array(data_Five['B3'])) + ' 【第三順位】'

    else:
        a_Five_BS_3 = ""

    # ----------------------------------------------#

    a_Five_BS4 = int(np.array(data_Five['BS4']))

    if int(a_Five_BS4) / int(stock_amount) >= 0.01:
        a_Five_BS_4 = "\n大額買單：" + format(int(a_Five_BS4), ',') + "張\n價格：" + str(
            np.array(data_Five['B4'])) + ' 【第四順位】'

    else:
        a_Five_BS_4 = ""

    # ----------------------------------------------#

    a_Five_BS5 = int(np.array(data_Five['BS5']))

    if int(a_Five_BS5) / int(stock_amount) >= 0.01:
        a_Five_BS_5 = "\n大額買單：" + format(int(a_Five_BS5), ',') + "張\n價格：" + str(
            np.array(data_Five['B5'])) + ' 【第五順位】'

    else:
        a_Five_BS_5 = ""

    # ----------------------------------------------#

    a_Five_AS = int(np.array(data_Five['AS']))

    if int(a_Five_AS) / int(stock_amount) >= 0.01 and str(np.array(data_Five['A'])) != '市價':
        a_Five_AS_1 = "\n大額賣單：" + format(int(a_Five_AS), ',') + "張\n價格：" + str(
            np.array(data_Five['A'])) + ' 【第一順位】'

    else:
        a_Five_AS_1 = ""

    # ----------------------------------------------#

    a_Five_AS2 = int(np.array(data_Five['AS2']))

    if int(a_Five_AS2) / int(stock_amount) >= 0.01 and np.array(data_Five['A2']) != np.array(data_Five['P']):
        a_Five_AS_2 = "\n大額賣單：" + format(int(a_Five_AS2), ',') + "張\n價格：" + str(
            np.array(data_Five['A2'])) + ' 【第二順位】'

    else:
        a_Five_AS_2 = ""

    # ----------------------------------------------#

    a_Five_AS3 = int(np.array(data_Five['AS3']))

    if int(a_Five_AS3) / int(stock_amount) >= 0.01:
        a_Five_AS_3 = "\n大額賣單：" + format(int(a_Five_AS3), ',') + "張\n價格：" + str(
            np.array(data_Five['A3'])) + ' 【第三順位】'

    else:
        a_Five_AS_3 = ""

    # ----------------------------------------------#

    a_Five_AS4 = int(np.array(data_Five['AS4']))

    if int(a_Five_AS4) / int(stock_amount) >= 0.01:
        a_Five_AS_4 = "\n大額賣單：" + format(int(a_Five_AS4), ',') + "張\n價格：" + str(
            np.array(data_Five['A4'])) + ' 【第四順位】'

    else:
        a_Five_AS_4 = ""

    # ----------------------------------------------#

    a_Five_AS5 = int(np.array(data_Five['AS5']))

    if int(a_Five_AS5) / int(stock_amount) >= 0.01:
        a_Five_AS_5 = "\n大額賣單：" + format(int(a_Five_AS5), ',') + "張\n價格：" + str(
            np.array(data_Five['A5'])) + ' 【第五順位】'

    else:
        a_Five_AS_5 = ""

    # ----------------------------------------------#

    if a_Five_BS_1 + a_Five_BS_2 + a_Five_BS_3 + a_Five_BS_4 + a_Five_BS_5 + a_Five_AS_1 + a_Five_AS_2 + a_Five_AS_3 + a_Five_AS_4 + a_Five_AS_5 != "":
        my_Text_All = '\n【' + datetime_format + '】\n股票名稱：' + str(stock_Name) + ' - ' + str(
            stock_no) + '\n目前股價：' + stock_Price + ' (' + str(stock_Way) + str(stock_Variety) + ')' + str(
            a_Five_BS_1) + str(
            a_Five_BS_2) + str(a_Five_BS_3) + str(a_Five_BS_4) + str(a_Five_BS_5) + str(a_Five_AS_1) + str(
            a_Five_AS_2) + str(a_Five_AS_3) + str(a_Five_AS_4) + str(a_Five_AS_5)
        return my_Text_All

    else:
        return ""

'''
# =====動態調整公開申購撈取日期===== #
'''

#判斷最舊資料序號,超過30筆則max=30
def New_buy_Date():

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }
    url = 'https://www.twse.com.tw/rwd/zh/announcement/publicForm?response=json&_=1679627792613'
    r = requests.get(url, verify=False, headers=headers)
    html_doc = r.text
    format_pattern = "%Y-%m-%d"
    data = json.loads(html_doc)
    a = np.array(data['data'])

    if int(a[-1][0]) < 20:
        return int(a[-1][0])
    elif int(a[-1][0]) >= 20 :
        return "20"
    else:
        return ""

if New_buy_Date() == 20:
    myList_2 = range(20, -1, -1)
elif New_buy_Date() == "":
    myList_2 = ""
else:
    myList_2 = range(int(New_buy_Date()), -1, -1)


def transform_date(date):
    y, m, d = date.split('/')
    return str(int(y) + 1911) + '-' + m + '-' + d  # 民國轉西元

datetime_ThisYear = datetime.datetime.today()
datetime_Format_ThisYear = datetime_ThisYear.strftime("%Y")

'''
# =====公開申購資訊Alert===== #
'''

def New_Buy(n):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    # url = 'https://www.twse.com.tw/announcement/publicForm?response=json&yy=2022&_='
    # url = 'https://www.twse.com.tw/announcement/publicForm?response=json&yy=' + datetime_Format_ThisYear
    url = 'https://www.twse.com.tw/rwd/zh/announcement/publicForm?response=json&_=1679627792613'

    r = requests.get(url, verify=False, headers=headers)
    html_doc = r.text
    format_pattern = "%Y-%m-%d"
    data = json.loads(html_doc)
    a = np.array(data['data'])
    today = datetime.date.today()
    today = today.strftime(format_pattern)

    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")
    datetime_format_check = datetime_dt.strftime("%Y/%m/%d")

    """
    datetime_format = new_dt.strftime("%Y/%m/%d %H:%M:%S")
    """

    if transform_date(a[n][6]) >= today:  # 申購截止日>今天

        if len(a[n][3]) == 4:  # 排除公債、特種股

            stock_no = str(a[n][3])
            stock_Ticket = int(int(a[n][7].replace(',', '')) / 1000)  # 全部張數
            stock_Amount = int(int(a[n][13].replace(',', '')) / 1000)  # 每人需申購張數
            stock_TA = int(stock_Ticket / stock_Amount)  # 名額

            # if str(a[n][4]) in ['初上市', '初上櫃', '上市增資', '上櫃增資']:
            if str(a[n][4]) != '中央登錄公債':

                stock_no = a[n][3]  # 股票代碼
                url_Another = 'https://kgieworld.moneydj.com/z/bcd/GetStkRTDataJSON.djjson?B=%s&xyz=' % stock_no
                r_Another = requests.get(url_Another, verify=False, headers=headers)
                html_doc_Another = r_Another.text

                if html_doc_Another[-2] == ',':
                    return ""

                data_Another = json.loads(html_doc_Another)

                if data_Another['Date'] != datetime_format_check:
                    return ""

                stock_Price = float(np.array(data_Another['P']))  # 即時股價
                stock_Name = np.array(data_Another['Name'])  # 股票名稱
                stock_Yesterday = float(np.array(data_Another['PC']))  # 昨天收盤

                stock_Volume_Yesterday = int(np.array(data_Another['PV']))  # 昨天交易量
                stock_Volume_Today = int(np.array(data_Another['TV']))  # 本日交易量
                stock_Volume_Avg = int(round((stock_Volume_Yesterday + stock_Volume_Today) / 2, 0))

                stock_Variety = float(round(((stock_Price - stock_Yesterday) / stock_Yesterday) * 100, 2))  # 漲跌幅

                if str(a[n][4]) == "初上市":
                    stock_new = "\n※初上市，請注意風險！"
                    stock_Recommend_First = -5

                elif str(a[n][4]) == "初上櫃":
                    stock_new = "\n※初上櫃，請注意風險！"
                    stock_Recommend_First = -10

                else:
                    stock_new = ""
                    stock_Recommend_First = 0

                if stock_Variety >= 0:
                    stock_Way_Price = '+'

                else:
                    stock_Way_Price = ''

                stock_Quantity = np.array(data_Another['TV'])  # 成交量

                # 111/3/31 新增流動性考量

                if stock_Volume_Avg == '' or stock_Volume_Avg == 0:
                    stock_Recommend_Volume = 0

                else:
                    ticket_Volume_Ratio = stock_Ticket / stock_Volume_Avg

                    if ticket_Volume_Ratio <= 0.1:
                        stock_Recommend_Volume = 0

                    elif ticket_Volume_Ratio <= 0.3:
                        stock_Recommend_Volume = -5

                    elif ticket_Volume_Ratio <= 0.5:
                        stock_Recommend_Volume = -10

                    elif ticket_Volume_Ratio <= 0.8:
                        stock_Recommend_Volume = -15

                    else:
                        stock_Recommend_Volume = -20

                # 111/1/4 移除中籤成本$70
                stock_Premium = int(
                    float(round(stock_Price - float(a[n][9]), 2) * 1000 * stock_Amount))  # (即時價格 - 申購價格)*申購股數

                if stock_Premium >= 0:
                    stock_Way_Premium = '+'

                else:
                    stock_Way_Premium = ''

                '''
                111/1/4 移除中籤成本$70
                stock_Premium_Percent = round((int(stock_Premium) / int(float(a[n][9]) * 1000) * 100) ,2)
                '''
                # 111/11/1 調整預估收益百分比
                stock_Premium_Percent = round(((int(stock_Premium) / stock_Amount) / int(float(a[n][9]) * 1000) * 100),
                                              2)
                # --------------------溢價%數判斷開始--------------------#

                if stock_Premium_Percent <= 0:
                    stock_Recommend_1 = -999

                elif stock_Premium_Percent <= 5:
                    stock_Recommend_1 = 15

                elif stock_Premium_Percent <= 10:
                    stock_Recommend_1 = 20

                elif stock_Premium_Percent <= 15:
                    stock_Recommend_1 = 25

                elif stock_Premium_Percent <= 20:
                    stock_Recommend_1 = 30

                elif stock_Premium_Percent <= 25:
                    stock_Recommend_1 = 35

                elif stock_Premium_Percent <= 30:
                    stock_Recommend_1 = 40

                elif stock_Premium_Percent <= 35:
                    stock_Recommend_1 = 45

                elif stock_Premium_Percent <= 40:
                    stock_Recommend_1 = 50

                else:
                    stock_Recommend_1 = 999

                # --------------------申購張數判斷開始--------------------#

                if stock_TA <= 500:
                    stock_Recommend_2 = 10

                elif stock_TA <= 1000:
                    stock_Recommend_2 = 15

                elif stock_TA <= 1500:
                    stock_Recommend_2 = 20

                elif stock_TA <= 2000:
                    stock_Recommend_2 = 25

                elif stock_TA <= 2500:
                    stock_Recommend_2 = 30

                elif stock_TA <= 3000:
                    stock_Recommend_2 = 35

                elif stock_TA <= 3500:
                    stock_Recommend_2 = 40

                else:
                    stock_Recommend_2 = 45

                # --------------------溢價金額判斷開始-------------------- #

                if stock_Premium <= 1000:
                    stock_Recommend_Bonus = -999

                elif stock_Premium <= 3000:
                    stock_Recommend_Bonus = 5

                elif stock_Premium <= 5000:
                    stock_Recommend_Bonus = 10

                elif stock_Premium <= 8000:
                    stock_Recommend_Bonus = 15

                elif stock_Premium <= 10000:
                    stock_Recommend_Bonus = 20

                elif stock_Premium <= 20000:
                    stock_Recommend_Bonus = 30

                elif stock_Premium <= 40000:
                    stock_Recommend_Bonus = 40

                else:
                    stock_Recommend_Bonus = 50

                # --------------------入場成本判斷開始-------------------- #

                if int(float(a[n][9]) * 1000) <= 50000:
                    stock_Recommend_Price = 0

                elif int(float(a[n][9]) * 1000) <= 80000:
                    stock_Recommend_Price = -5

                elif int(float(a[n][9]) * 1000) <= 100000:
                    stock_Recommend_Price = -10

                elif int(float(a[n][9]) * 1000) <= 150000:
                    stock_Recommend_Price = -15

                elif int(float(a[n][9]) * 1000) <= 200000:
                    stock_Recommend_Price = -20

                elif int(float(a[n][9]) * 1000) <= 250000:
                    stock_Recommend_Price = -25

                elif int(float(a[n][9]) * 1000) <= 300000:
                    stock_Recommend_Price = -30

                elif int(float(a[n][9]) * 1000) <= 350000:
                    stock_Recommend_Price = -35

                elif int(float(a[n][9]) * 1000) <= 400000:
                    stock_Recommend_Price = -40

                elif int(float(a[n][9]) * 1000) <= 450000:
                    stock_Recommend_Price = -45

                else:
                    stock_Recommend_Price = -50

                # --------------------溢價分數合計-------------------- #

                stock_Recommend = int(
                    stock_Recommend_1 + stock_Recommend_2 + stock_Recommend_Bonus + stock_Recommend_Price + stock_Recommend_First + stock_Recommend_Volume)

                if stock_Recommend >= 100:
                    stock_Recommend = 100

                elif stock_Recommend < 0:
                    stock_Recommend = 0

                # --------------------推薦度分析-------------------- #

                if int(stock_Recommend) < 70:  # 70以下
                    stock_Comment = ""

                elif int(stock_Recommend) < 80:  # 70~79
                    stock_Comment = " #考慮購買"

                elif int(stock_Recommend) < 90:  # 80~89
                    stock_Comment = " #值得購買"

                else:  # 90(含)以上
                    stock_Comment = " #務必申購"

                if ticket_Volume_Ratio > 0.8:
                    stock_Comment = stock_Comment + "\n※成交量低，流動性較差！"

                else:
                    stock_Comment = stock_Comment

                if transform_date(a[n][6]) == today:
                    my_LastDay = '※申購截止日※\n'

                else:
                    my_LastDay = ''

                my_text = '\n【' + datetime_format + '】\n' + my_LastDay + '股票名稱：' + str(
                    a[n][2] + ' - ' + a[n][3]) + '\n名額：' + str(format(int(stock_TA), ',')) + '張\n成本：$ ' + str(
                    format(int(float(a[n][9]) * stock_Amount * 1000), ',')) + '\n目前股價：' + str(
                    format(float(stock_Price), ',')) + ' (' + str(stock_Way_Price) + str(
                    stock_Variety) + '%)\n預估收益：$ ' + str(format(stock_Premium, ',')) + ' (' + str(
                    stock_Way_Premium) + str(stock_Premium_Percent) + '%)\n推薦度：' + str(stock_Recommend) + '%' + str(
                    stock_Comment) + stock_new
                return my_text
            else:
                return ""
        else:
            return ""
    else:
        return ""

'''
# =====公開申購回測收益===== #
'''

def New_Buy_BackTest(n):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    # url = 'https://www.twse.com.tw/announcement/publicForm?response=json&yy=2022&_='
    # url = 'https://www.twse.com.tw/announcement/publicForm?response=json&yy=' + datetime_Format_ThisYear
    url = 'https://www.twse.com.tw/rwd/zh/announcement/publicForm?response=json&_=1679627792613'

    r = requests.get(url, verify=False, headers=headers)
    html_doc = r.text
    format_pattern = "%Y-%m-%d"
    data = json.loads(html_doc)
    a = np.array(data['data'])
    today = datetime.date.today()
    today = today.strftime(format_pattern)

    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")
    datetime_format_check = datetime_dt.strftime("%Y/%m/%d")

    """
    datetime_format = new_dt.strftime("%Y/%m/%d %H:%M:%S")
    """

    if transform_date(a[n][11]) == today:  # 撥券日期 = 今天

        if len(a[n][3]) == 4:  # 排除公債、特種股

            stock_no = str(a[n][3])  #股票代號
            stock_Price_PreSell = float(a[n][9]) #承銷價格
            stock_Ticket = int(int(a[n][7].replace(',', '')) / 1000)  # 全部張數
            stock_Amount = int(int(a[n][13].replace(',', '')) / 1000)  # 每人需申購張數
            stock_Hit_Percent = str(float(a[n][16]))  # 中籤率

            #if str(a[n][4]) in ['初上市', '初上櫃', '上市增資', '上櫃增資']:
            if str(a[n][4]) != '中央登錄公債':

                stock_no = a[n][3]  # 股票代碼
                url_Another = 'https://kgieworld.moneydj.com/z/bcd/GetStkRTDataJSON.djjson?B=%s&xyz=' % stock_no
                r_Another = requests.get(url_Another, verify=False, headers=headers)
                html_doc_Another = r_Another.text

                if html_doc_Another[-2] == ',':
                    return ""

                data_Another = json.loads(html_doc_Another)

                if data_Another['Date'] != datetime_format_check:
                    return ""

                stock_Price = float(np.array(data_Another['P']))  # 即時股價
                stock_Yesterday = float(np.array(data_Another['PC']))  # 昨天收盤
                stock_Variety = np.array(data_Another['sUPR'])  #漲跌幅
                stock_Name = np.array(data_Another['Name'])  # 股票名稱

                if np.array(data_Another['sUPFlag']) == 'DOWN': #漲跌標記
                    stock_Way = '-'
                else:
                    stock_Way = '+'

                if stock_Price_PreSell != 0 and stock_Price != 0:
                    stock_benefit = int(float(stock_Price - stock_Price_PreSell) * stock_Amount * 1000)
                    stock_benefit_Percent = float(round((float(stock_Price - stock_Price_PreSell) / stock_Price_PreSell)*100,1))
                    if stock_benefit < 0:
                        stock_Way_Pre = ''
                    else:
                        stock_Way_Pre = ''

                    my_text = '\n【' + datetime_format + '】\n' + '股票名稱：' + str(stock_Name) + ' - ' + str(stock_no) + '\n撥券收盤價：' + str(format(float(stock_Price), ',')) + ' (' + str(stock_Way) + str(stock_Variety) + ')\n付出成本：$' + str(format(int(stock_Price_PreSell*1000),',')) + '\n實際收益：$' + str(stock_Way_Pre) + str(format(stock_benefit, ',')) + '\n報酬率：' + str(stock_Way_Pre) + str(stock_benefit_Percent) + '%\n中籤率：' + str(stock_Hit_Percent) + '%'

                    return my_text
                else:
                    return ""
            else:
                return ""
        else:
            return ""
    else:
        return ""

'''
#=====類股當日資訊Alert=====#
'''

def funds_Flow(x):
    # 資料來源
    url = 'https://pscnetsecrwd.moneydj.com/b2brwdCommon/jsondata/c6/fb/f2/twstockdata.xdjjson?x=afterhours-market0003-1&revision='  # 類股指數
    url_BuySell = 'https://pscnetsecrwd.moneydj.com/b2brwdCommon/jsondata/4e/3f/ec/twstockdata.xdjjson?x=afterHours-market0001-1&b=d&c=60&revision='  # 買賣超

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")

    """
    datetime_format = new_dt.strftime("%Y/%m/%d %H:%M:%S")
    """

    r = requests.get(url, verify=False, headers=headers)
    r.encoding = 'UTF-8'
    data = json.loads(r.text)
    a = np.array(data['ResultSet']['Result'])

    r_BS = requests.get(url_BuySell, verify=False, headers=headers)
    r_BS.encoding = 'UTF-8'
    data_BS = json.loads(r_BS.text)
    b = np.array(data_BS['ResultSet']['Result'][0])

    # 類股用參數
    '''
    #V5=本日類股成交量
    #V6=昨日類股成交量
    #V7=本日類股指數
    #V8=昨日類股指數    
    '''
    # ===內建參數定義===#

    f_Time = a[x]['V2']  # 類股指數更新時間
    f_Name = str(a[x]['V4'])  # 類股名稱
    f_Volume_Today = 1000 * int(a[x]['V5'])  # 本日成交量(單位:千元)
    f_Volume_Yesterday = 1000 * int(a[x]['V6'])  # 昨日成交量(單位:千元)
    f_Volume_Today_All = 1000 * int(a[34]['V5'])  # 大盤本日成交量(單位:千元)
    f_Volume_Yesterday_All = 1000 * int(a[34]['V6'])  # 大盤昨日成交量(單位:千元)
    f_Volume_All_Diff = int(f_Volume_Today_All - f_Volume_Yesterday_All)  # 大盤成交量差異
    f_Volume_All_Diff_Ratio = float(round(100 * (f_Volume_All_Diff / f_Volume_Yesterday_All), 1))  # 大盤成交量成長率

    if f_Volume_All_Diff > 0:
        f_Volume_All_Diff_Way = '+'

    else:
        f_Volume_All_Diff_Way = ''

    f_Index_Today = float(a[x]['V7'])  # 本日類股指數
    f_Index_Yesterday = float(a[x]['V8'])  # 昨日類股指數
    f_Index_Today_All = float(a[34]['V7'])  # 本日大盤指數
    f_Index_Yesterday_All = float(a[34]['V8'])  # 昨日大盤指數
    f_Index_All_Diff = float(round(f_Index_Today_All - f_Index_Yesterday_All, 1))  # 大盤指數差異
    f_Index_All_Diff_Ratio = float(round(100 * (f_Index_All_Diff / f_Index_Yesterday_All), 1))  # 大盤指數成長率

    if f_Index_All_Diff > 0:
        f_Index_All_Diff_Way = '+'

    else:
        f_Index_All_Diff_Way = ''

    # ===內建參數結束=== #

    # ===建立需求欄位=== #

    f_Volume_Diff = int(f_Volume_Today - f_Volume_Yesterday)  # 成交量差異
    f_Volume_Diff_Ratio = float(round(100 * (f_Volume_Diff / f_Volume_Yesterday), 1))  # 成交量成長率

    if f_Volume_Diff > 0:
        f_Volume_Diff_Way = '+'

    else:
        f_Volume_Diff_Way = ''

    f_Index_Diff = float(round(f_Index_Today - f_Index_Yesterday, 2))  # 指數差異

    if f_Index_Diff > 0:
        f_Index_Diff_Way = '+'

    else:
        f_Index_Diff_Way = ''

    f_Index_Diff_Ratio = float(round(100 * (f_Index_Diff / f_Index_Yesterday), 1))  # 指數成長率

    if f_Index_Diff_Ratio > 0:
        f_Index_Diff_Ratio_Way = '+'

    else:
        f_Index_Diff_Ratio_Way = ''

    f_Volume_Today_Ratio = float(round(100 * (f_Volume_Today / f_Volume_Today_All), 2))  # 類股本日占比 (類股本日成交量/大盤本日成交量)
    f_Volume_Yesterday_Ratio = float(
        round(100 * (f_Volume_Yesterday / f_Volume_Yesterday_All), 2))  # 類股昨日占比 (類股昨日成交量/大盤昨日成交量)
    f_Volume_Ratio_Diff = float(round(f_Volume_Today_Ratio - f_Volume_Yesterday_Ratio, 1))  # 類股本日占比 - 類股昨日占比

    if f_Volume_Ratio_Diff > 0:
        f_Volume_Ratio_Diff_Way = '+'

    else:
        f_Volume_Ratio_Diff_Way = ''

    # ===需求欄位結束=== #

    # 買賣超用參數
    '''
    #V2=外資買超成交量
    #V3=外資賣超成交量
    #V4=投信買超成交量
    #V5=投信賣超成交量
    #V6=自行買賣買超成交量(散戶)
    #V7=自行買賣賣超成交量(散戶)
    #V8=自營避險買超成交量
    #V9=自營避險賣超成交量
    #V10=外資自營買超成交量
    #V11=外資自營賣超成交量
    '''
    # ===內建參數定義=== #

    f_BS_Time = np.array(data_BS['ResultSet']['Result'][0]['V1'])  # 買賣超資料更新時間
    f_BS_1_Buy = int(np.array(data_BS['ResultSet']['Result'][0]['V2']))  # 外資買超
    f_BS_1_Sell = int(np.array(data_BS['ResultSet']['Result'][0]['V3']))  # 外資賣超
    f_BS_2_Buy = int(np.array(data_BS['ResultSet']['Result'][0]['V4']))  # 投信買超
    f_BS_2_Sell = int(np.array(data_BS['ResultSet']['Result'][0]['V5']))  # 投信賣超
    f_BS_3_Buy = int(np.array(data_BS['ResultSet']['Result'][0]['V6']))  # 自行買賣買超
    f_BS_3_Sell = int(np.array(data_BS['ResultSet']['Result'][0]['V7']))  # 自行買賣賣超
    f_BS_4_Buy = int(np.array(data_BS['ResultSet']['Result'][0]['V8']))  # 自營避險買超
    f_BS_4_Sell = int(np.array(data_BS['ResultSet']['Result'][0]['V9']))  # 自營避險賣超
    f_BS_5_Buy = int(np.array(data_BS['ResultSet']['Result'][0]['V10']))  # 外資自營買超
    f_BS_5_Sell = int(np.array(data_BS['ResultSet']['Result'][0]['V11']))  # 外資自營賣超

    # ===內建參數結束=== #

    # ===建立需求欄位=== #

    f_BS_1_Diff = float(round((f_BS_1_Buy - f_BS_1_Sell) / 100000000, 2))  # 外資買賣超

    if f_BS_1_Diff > 0:
        f_BS_1_Diff_Way = '買超：'

    else:
        f_BS_1_Diff_Way = '賣超：'

    f_BS_2_Diff = float(round((f_BS_2_Buy - f_BS_2_Sell) / 100000000, 2))  # 投信買賣超

    if f_BS_2_Diff > 0:
        f_BS_2_Diff_Way = '買超：'

    else:
        f_BS_2_Diff_Way = '賣超：'

    f_BS_3_Diff = int(f_BS_3_Buy - f_BS_3_Sell)  # 自行買賣買賣超
    f_BS_4_Diff = int(f_BS_4_Buy - f_BS_4_Sell)  # 自營避險買賣超

    f_BS_5_Diff = float(round((f_BS_3_Diff + f_BS_4_Diff) / 100000000, 2))  # 自營買賣超

    if f_BS_5_Diff > 0:
        f_BS_5_Diff_Way = '買超：'

    else:
        f_BS_5_Diff_Way = '賣超：'

    f_BS_All_Diff = float(
        round(f_BS_1_Diff + f_BS_2_Diff + f_BS_5_Diff, 2))  # 三大法人(f_BS_1_Diff,f_BS_2_Diff,f_BS_5_Diff)

    if f_BS_All_Diff > 0:
        f_BS_All_Diff_Way = '買超：'

    else:
        f_BS_All_Diff_Way = '賣超：'

    '''
    #警示情境：
    #1.成交量差值可以判斷資金流向(含占比) [PS閥值1] f_Volume_Diff > 50(b) 起警示
    #2.資金占比判斷資金流向 [PS閥值2] f_Volume_Ratio_Diff > 5(%) 起警示
    #3.成交量異常(成長率>100%)||需同時滿足增加成交量>15(b)起警示

    #警示Alert欄位預覽
    #【YYYY/MM/DD HH:MM:SS】
    #【f_Name類股】
    #加權指數：f_Index_Today_All (f_Index_All_Diff_Way , f_Index_Diff %) (111.3.21修改後)
    #成交量：f_Volume_Diff_Way , f_Volume_Diff 億 (f_Volume_Diff_Way f_Volume_Diff_Ratio %)
    #成交比重：f_Volume_Today_Ratio % (f_Volume_Ratio_Diff_Way f_Volume_Ratio_Diff %)
    '''

    # 觸發警示條件設定
    f_Volume_Alert = 5000000000  # 成交量>50億
    f_Volume_Ratio_Alert = 5  # 成交比重占比>5%
    f_Volume_Diff_Ratio_Alert = 100  # 成交量成長率>100%
    f_Volume_Alert_Low = 2500000000  # 合併前項條件成交量需>15億(排除冷門類股)

    format_pattern = "%Y/%m/%d"
    today = datetime.date.today()
    today_f_Flow = today.strftime(format_pattern)

    if f_Time == today_f_Flow and f_BS_Time == today_f_Flow:  # 檢核資料是否更新

        if x < 34:  # 各類股Alert
            if abs(f_Volume_Diff) >= f_Volume_Alert or abs(f_Volume_Ratio_Diff) >= f_Volume_Ratio_Alert or (
                    (abs(f_Volume_Diff_Ratio) >= f_Volume_Diff_Ratio_Alert) and (
                    abs(f_Volume_Diff) >= f_Volume_Alert_Low)):
                f_Flow_Text = '\n【' + datetime_format + '】\n【' + str(f_Name) + '類股】\n加權指：' + str(
                    f_Index_Diff_Way) + str(format(f_Index_Diff, ',')) + ' (' + str(f_Index_Diff_Ratio_Way) + str(
                    format(f_Index_Diff_Ratio, ',')) + '%)\n成交量：' + str(f_Volume_Diff_Way) + str(
                    format(round(f_Volume_Diff / 100000000, 2), ',')) + '億 (' + str(f_Volume_Diff_Way) + str(
                    format(f_Volume_Diff_Ratio, ',')) + '%)\n成交比重：' + str(
                    format(f_Volume_Today_Ratio, ',')) + '% (' + str(f_Volume_Ratio_Diff_Way) + str(
                    format(f_Volume_Ratio_Diff, ',')) + '%)'
                return f_Flow_Text

            else:
                return ""

        elif x == 34:  # 大盤Alert
            f_Flow_Text = '\n【' + datetime_format + '】\n【加權股價指數 - TAIEX】\n加權指：' + str(
                format(float(round(f_Index_Today_All, 1)), ',')) + ' (' + str(f_Index_All_Diff_Way) + str(
                format(f_Index_All_Diff, ',')) + ')\n成交量：' + str(
                format(int(round(f_Volume_Today_All / 100000000, 0)), ',')) + '億 (' + str(f_Volume_All_Diff_Way) + str(
                format(int(round(f_Volume_All_Diff / 100000000, 0)), ',')) + '億)\n外資 ' + str(f_BS_1_Diff_Way) + str(
                abs(f_BS_1_Diff)) + '億\n投信 ' + str(f_BS_2_Diff_Way) + str(abs(f_BS_2_Diff)) + '億\n自營 ' + str(
                f_BS_5_Diff_Way) + str(abs(f_BS_5_Diff)) + '億\n合計 ' + str(f_BS_All_Diff_Way) + str(
                abs(f_BS_All_Diff)) + '億'
            return f_Flow_Text

        else:
            return ""

    else:
        return ""

'''
#=====三大法人買超前15檔Alert=====#
'''

def max_Three_Buy():
    format_pattern_Max_Three = "%Y%m%d"
    today = datetime.date.today()
    today_Max_Three = today.strftime(format_pattern_Max_Three)

    # url = 'https://www.twse.com.tw/fund/T86?response=json&date=&selectType=ALLBUT0999&_=1648963436427'  # 三大法人 買超
    url = 'https://www.twse.com.tw/rwd/zh/fund/T86?date=%s&selectType=ALL&response=json&_=1695172061788' % today_Max_Three

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")

    """
    datetime_format = new_dt.strftime("%Y/%m/%d %H:%M:%S")
    """

    r = requests.get(url, verify=False, headers=headers)
    data = json.loads(r.text)
    t = str(np.array(data['date']))

    def my_Loop_Three(y):  # 三大法人

        a = np.array(data['data'][y])
        m_Three_BS_Name = str(a[1])
        m_Three_BS_Name = m_Three_BS_Name.replace(' ', '')
        m_Three_BS_Name = m_Three_BS_Name[:3]

        m_Three_BS_Number = str(a[0])
        m_Three_BS_Number = m_Three_BS_Number.replace(' ', '')
        m_Three_BS_Number = m_Three_BS_Number[:6]

        m_Three_BS_Volume = str(a[18])
        m_Three_BS_Volume = format(int(round(int(m_Three_BS_Volume.replace(',', '')) / 1000, 0)), ',')

        my_Loop_Text = '\n【' + str(m_Three_BS_Name) + '-' + str(m_Three_BS_Number) + '】 ' + str(m_Three_BS_Volume) + '張'
        return my_Loop_Text

    if t == today_Max_Three:  # 檢核資料是否更新
        m_Three_Message_Buy = '\n【' + datetime_format + '】' + my_Loop_Three(0) + my_Loop_Three(1) + my_Loop_Three(
            2) + my_Loop_Three(3) + my_Loop_Three(4) + my_Loop_Three(5) + my_Loop_Three(6) + my_Loop_Three(
            7) + my_Loop_Three(8) + my_Loop_Three(9) + my_Loop_Three(10) + my_Loop_Three(11) + my_Loop_Three(
            12) + my_Loop_Three(13) + my_Loop_Three(14)
        return m_Three_Message_Buy
    else:
        return ""


'''
#=====三大法人賣超前15檔Alert=====#
'''


def max_Three_Sell():

    format_pattern_Max_Three = "%Y%m%d"
    today = datetime.date.today()
    today_Max_Three = today.strftime(format_pattern_Max_Three)

    # url = 'https://www.twse.com.tw/fund/T86?response=json&date=&selectType=ALLBUT0999&_=1648963436427'  # 三大法人 買超
    url = 'https://www.twse.com.tw/rwd/zh/fund/T86?date=%s&selectType=ALL&response=json&_=1695172061788' % today_Max_Three

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")

    """
    datetime_format = new_dt.strftime("%Y/%m/%d %H:%M:%S")
    """

    r = requests.get(url, verify=False, headers=headers)
    data = json.loads(r.text)
    t = str(np.array(data['date']))

    def my_Loop_Three(y):  # 三大法人

        a = np.array(data['data'][y])
        m_Three_BS_Name = str(a[1])
        m_Three_BS_Name = m_Three_BS_Name.replace(' ', '')
        m_Three_BS_Name = m_Three_BS_Name[:3]

        m_Three_BS_Number = str(a[0])
        m_Three_BS_Number = m_Three_BS_Number.replace(' ', '')
        m_Three_BS_Number = m_Three_BS_Number[:6]

        m_Three_BS_Volume = str(a[18])
        m_Three_BS_Volume = format(int(abs(round(int(m_Three_BS_Volume.replace(',', '')) / 1000, 0))), ',')
        my_Loop_Text = '\n【' + str(m_Three_BS_Name) + '-' + str(m_Three_BS_Number) + '】 ' + str(m_Three_BS_Volume) + '張'
        return my_Loop_Text

    if t == today_Max_Three:  # 檢核資料是否更新
        m_Three_Message_Sell = '\n【' + datetime_format + '】' + my_Loop_Three(-1) + my_Loop_Three(-2) + my_Loop_Three(
            -3) + my_Loop_Three(-4) + my_Loop_Three(-5) + my_Loop_Three(-6) + my_Loop_Three(-7) + my_Loop_Three(
            -8) + my_Loop_Three(-9) + my_Loop_Three(-10) + my_Loop_Three(-11) + my_Loop_Three(-12) + my_Loop_Three(
            -13) + my_Loop_Three(-14) + my_Loop_Three(-15)
        return m_Three_Message_Sell
    else:
        return ""


"""
#=====漲跌幅異常Alert=====#
"""

def H_Today_Amplitude(stock_no):
    url_last = 'https://kgieworld.moneydj.com/z/bcd/GetStkRTDataJSON.djjson?B=%s&xyz=' % stock_no

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.39'
    }

    r_last = requests.get(url_last, verify=False, headers=headers)
    html_last = r_last.text

    if html_last[-2] == ',':
        return ""

    data_last = json.loads(html_last)
    datetime_dt = datetime.datetime.today()
    time_delta = datetime.timedelta(hours=8)
    new_dt = datetime_dt + time_delta
    datetime_format = datetime_dt.strftime("%Y/%m/%d %H:%M:%S")
    datetime_format_check = datetime_dt.strftime("%Y/%m/%d")

    if data_last['Date'] != datetime_format_check:
        return ""

    stock_Price_High = float(np.array(data_last['H']))  # 本日最高價
    stock_Price_Low = float(np.array(data_last['L']))  # 本日最低價
    stock_Price = float(np.array(data_last['P']))  # 即時股價
    stock_Yesterday = float(np.array(data_last['PC']))  # 昨天收盤
    stock_Variety = np.array(data_last['sUPR'])  #漲跌幅
    stock_Name = np.array(data_last['Name'])  # 股票名稱

    if stock_Yesterday == 0:
        return ""
    else:
        stock_Today_Amplitude = round(float((float(stock_Price_High)-float(stock_Price_Low))/float(stock_Yesterday))*100, 2)

    if np.array(data_last['sUPFlag']) == 'DOWN':
        stock_Way = '-'
    else:
        stock_Way = '+'

    if float(stock_Today_Amplitude) > 10:
        my_Text_last = '\n【' + datetime_format + '】\n股票名稱：' + str(stock_Name) + ' - ' + str(
            stock_no) + '\n目前股價：' + str(format(float(stock_Price), ',')) + ' (' + str(stock_Way) + str(
            stock_Variety) + ')\n最高價：' + str(format(float(stock_Price_High), ',')) + '\n最低價：' + str(format(float(stock_Price_Low), ',')) + '\n振幅：' + str(float(stock_Today_Amplitude)) + '%'
        return my_Text_last
    else:
        return ""

# --------------------Line Notify Token-------------------- #
def job_Yesterday_1000():
    for stock_no in myList:
        if s_Yesterday_Volume(stock_no, 1.5, 150) != "":
            message = s_Yesterday_Volume(stock_no, 1.5, 150)
            # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            token = '3XTMYsMq76pBJkSVQyGWeBK6VvGYfnAgHXbTqtnLJBg'  # 正式區token
            lineNotifyMessage(token, message)

def job_Yesterday_1100():
    for stock_no in myList:
        if s_Yesterday_Volume(stock_no, 2, 300) != "":
            message = s_Yesterday_Volume(stock_no, 2, 300)
            # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            token = '6A99nMgweCMgYUtordwtYPOoLKASsXdoLoxRhjAGzO1'  # 正式區token
            lineNotifyMessage(token, message)

def job_Yesterday_1200():
    for stock_no in myList:
        if s_Yesterday_Volume(stock_no, 2.5, 500) != "":
            message = s_Yesterday_Volume(stock_no, 2.5, 500)
            # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            token = '3bOmciadhL70n07F5C2DYqs0ujeUHFLetTAQQL2SBow'  # 正式區token
            lineNotifyMessage(token, message)

def job_Yesterday_1300():
    for stock_no in myList:
        if s_Yesterday_Volume(stock_no, 3, 700) != "":
            message = s_Yesterday_Volume(stock_no, 3, 700)
            # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            token = 'KBTqj1AHNrgEG31fssOxQaYtOHvSJyKolRycRrSwexE'  # 正式區token

def job_Yesterday_1330():
    for stock_no in myList:
        if s_Yesterday_Volume(stock_no, 3.5, 1000) != "":
            message = s_Yesterday_Volume(stock_no, 3.5, 1000)
            # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            token = 'zG1mW7DSbEz4ufuN9fFL4Aqcjts2hlJG0yV9K0KXNHz'  # 正式區token
            lineNotifyMessage(token, message)

def job_High_Order():
    for stock_no in myList:
        if s_High_Order(stock_no) != "":
            message = s_High_Order(stock_no)
            # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            token = 'yQHOWRYtUjL9C1LMxsq9H7k4BpFSw8ERxSoT30sBtO9'  # 正式區token
            lineNotifyMessage(token, message)

def job_H_Today_Amplitude():
    for stock_no in myList:
        if H_Today_Amplitude(stock_no) != "":
            message = H_Today_Amplitude(stock_no)
            token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            #token = 'yQHOWRYtUjL9C1LMxsq9H7k4BpFSw8ERxSoT30sBtO9'  # 正式區token
            lineNotifyMessage(token, message)

def job_New_Buy():
    if myList_2 != "" :
        for n in myList_2:
            if New_Buy(n) != "":
                message = New_Buy(n)
                # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
                token = '3c9LfmgHP4h7ltSsrVTH8UK9RobZeYeJeekGSwlesBc'  # 正式區token
                lineNotifyMessage(token, message)

def job_New_Buy_BackTest():
    if myList_2 != "" :
        for n in myList_2:
            if New_Buy_BackTest(n) != "":
                message = New_Buy_BackTest(n)
                #token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
                token = 'FxaO8CPBB2u61DaD8I2M2Q6Nt13oQilOVFF29sjWOM6'  # 正式區token
                lineNotifyMessage(token, message)

# =====類股當日資訊Alert===== #
def job_Funds_Flow():
    for x in myList_3:
        if funds_Flow(x) != "":
            message = funds_Flow(x)
            # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
            token = 'ACgCA27MX139CFkGpxBq72GPVKiJ2NFvcDNaq8zCsEH'  # 正式區token
            lineNotifyMessage(token, message)

# =====三大法人買超Alert===== #
def job_Max_Three_Buy():
    if max_Three_Buy() != "":
        message = max_Three_Buy()
        # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
        token = 'GhTxVsY7ky86mPKOTo8UuKAuYww8uooeNVMTZiyqGaT'  # 正式區token
        lineNotifyMessage(token, message)

# =====三大法人賣超Alert===== #
def job_Max_Three_Sell():
    if max_Three_Sell() != "":
        message = max_Three_Sell()
        # token = 'h41Olw9LglGB4PTZqLafnXVgaoTan2SbsydM4AmBEsb' #測試區token
        token = '44u8ntsX8WqXFnyG2g7hcnIFcfelYm2xlvJHhgM7sGW'  # 正式區token
        lineNotifyMessage(token, message)

# =====更新每日申購使用日期計算模組===== #
scheduler.add_job(New_buy_Date, 'cron', day_of_week='mon-fri', hour='9', minute='40', second='5')

# =====高額掛單Alert===== #
scheduler.add_job(job_High_Order, 'cron', day_of_week='mon-fri', hour='9-12', minute='*/15')
scheduler.add_job(job_High_Order, 'cron', day_of_week='mon-fri', hour='13', minute='10')
scheduler.add_job(job_High_Order, 'cron', day_of_week='mon-fri', hour='13', minute='20')

# =====成交量異常Alert===== #
scheduler.add_job(job_Yesterday_1000, 'cron', day_of_week='mon-fri', hour='10')
scheduler.add_job(job_Yesterday_1100, 'cron', day_of_week='mon-fri', hour='11')
scheduler.add_job(job_Yesterday_1200, 'cron', day_of_week='mon-fri', hour='12')
scheduler.add_job(job_Yesterday_1300, 'cron', day_of_week='mon-fri', hour='13')
scheduler.add_job(job_Yesterday_1330, 'cron', day_of_week='mon-fri', hour='13', minute='30')

# =====漲跌幅異常Alert===== #
scheduler.add_job(job_H_Today_Amplitude, 'cron', day_of_week='mon-fri', hour='10')
scheduler.add_job(job_H_Today_Amplitude, 'cron', day_of_week='mon-fri', hour='11')
scheduler.add_job(job_H_Today_Amplitude, 'cron', day_of_week='mon-fri', hour='12')
scheduler.add_job(job_H_Today_Amplitude, 'cron', day_of_week='mon-fri', hour='13')
scheduler.add_job(job_H_Today_Amplitude, 'cron', day_of_week='mon-fri', hour='13', minute='30')

# =====公開申購資訊Alert===== #
scheduler.add_job(job_New_Buy, 'cron', day_of_week='mon-fri', hour='9', minute='45')
scheduler.add_job(job_New_Buy, 'cron', day_of_week='mon-fri', hour='12')
scheduler.add_job(job_New_Buy, 'cron', day_of_week='mon-fri', hour='14', minute='25')

# =====公開申購回測收益===== #
scheduler.add_job(job_New_Buy_BackTest, 'cron', day_of_week='mon-fri', hour='14', minute='30')

# =====類股當日資訊Alert===== #
scheduler.add_job(job_Funds_Flow, 'cron', day_of_week='mon-fri', hour='16', minute='30', second='5')

# =====三大法人買賣超前15檔Alert===== #
scheduler.add_job(job_Max_Three_Buy, 'cron', day_of_week='mon-fri', hour='17', minute='00', second='30')
scheduler.add_job(job_Max_Three_Sell, 'cron', day_of_week='mon-fri', hour='17', minute='01', second='30')


scheduler.start()
