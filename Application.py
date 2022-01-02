import json
import pandas as pd
import time
import os
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
from package.subpackage1 import *
import collections

def main():
    global RADIUS ; RADIUS = globalvar.get_value('radius')
    global CITY ; CITY = globalvar.get_value('city')
    global p ; p = globalvar.get_value('PTX')
    global g ; g = globalvar.get_value('GoogleMap')
    global application_csv_path ; application_csv_path = globalvar.get_value('application_csv_path')
    while True:
        '''====================
        | 輸入資料
        ===================='''
        print(f'市區公車查詢系統！將為您找出附近 {RADIUS} 公尺內可搭乘的公車站')
        input_origins = input('我現在人在：')
        input_destinations = input('我想要到：')
        print()
        
        origins = getNearByStation(input_origins) #讀取所在地公車站資訊
        destinations = getNearByStation(input_destinations) #讀取目的地公車站資訊
        
        routes = set()
        result_dataframe = pd.DataFrame()
        for _index, _columns in origins.iterrows():
            for index, columns in destinations.iterrows():
                stops1 = set(value['RouteName']['Zh_tw'] for value in _columns['Stops']) #停靠所在地車站的所有路線
                stops2 = set(value['RouteName']['Zh_tw'] for value in columns['Stops']) #停靠目的地車站的所有路線
                sameRoute = stops1 & stops2 #會經過所在地與目的地的路線
                route = f'{_columns["StationID"]}, {sameRoute}'
                
                if (len(sameRoute) == 0): #所在地與目的地沒有相同的路線
                    continue

                if (route in routes): #路線重複
                    continue
                routes.add(route)
                # getSchedule(_columns["StationID"], _columns["StationName"]['Zh_tw'], columns["StationName"]['Zh_tw'])
                
                originsEstimate = getEstimatedTimeOfArrival(_columns["StationID"]) #所在地附近公車站的預計到站資料
                if len(originsEstimate.index) == 0:
                    continue
                
                bus = pd.DataFrame()
                bus = originsEstimate[originsEstimate['RouteName'].apply(lambda x : x['Zh_tw']).isin(sameRoute)]
                for _index, __columns in bus.iterrows():
                    if (True if 'Estimates' not in __columns.index else (type(__columns['Estimates']) == float)):
                        continue # 略過此步驟
                        # _dict = {
                        #     '公車路線': __columns['RouteName']['Zh_tw'], 
                        #     '出發站': _columns["StationName"]['Zh_tw'], 
                        #     '出發車站ID': _columns["StationID"], 
                        #     '目標站': columns["StationName"]['Zh_tw'], 
                        #     '目標車站ID': columns["StationID"]
                        # }
                        # new_row = pd.DataFrame(_dict, index=[0])
                        # result_dataframe = result_dataframe.append(new_row, ignore_index=True)

                    else:
                        for _ in __columns['Estimates']:

                            t = time.localtime(time.time() + _["EstimateTime"])
                            t = time.strftime("%H:%M", t)
                            _dict = {
                                '車牌號碼': _["PlateNumb"], 
                                '公車路線': __columns['RouteName']['Zh_tw'], 
                                '預計到站時間': t, 
                                # '預計到站時間': '{:g}'.format(_["EstimateTime"] / 60) + '分' if _["EstimateTime"] > 60  else f'{_["EstimateTime"]}秒', 
                                '出發站': _columns["StationName"]['Zh_tw'], 
                                # '出發車站ID': _columns["StationID"], 
                                '目標站': columns["StationName"]['Zh_tw'], 
                                # '目標車站ID': columns["StationID"]
                            }

                            new_row = pd.DataFrame(_dict, index=[0])
                            result_dataframe = result_dataframe.append(new_row, ignore_index=True)
        
        if result_dataframe.empty:
            print('無結果')
            continue
        
        result_dataframe = result_dataframe.sort_values(['預計到站時間', '出發站'])
        file = f'{input_origins} to {input_destinations}.csv'
        current_path = os.getcwd()
        if not(os.path.exists(current_path + application_csv_path)): os.mkdir(current_path + application_csv_path)
        result_dataframe.to_csv(current_path + application_csv_path + file, encoding='utf_8_sig')
        print(result_dataframe)
            
        print(('====================分隔線====================\n\n'))

'''====================
| 輸入地址，經過 Google Geocoding API 將地址轉換成經緯度，取得並回傳地址周圍的公車站牌資料
===================='''
def getNearByStation(address):
    r = g.get_geocode(address)
    if len(r['results']) == 0:
        print(r)
        return pd.DataFrame()

    location = r['results'][0]['geometry']['location']
    params= {
        # '$top': 20, 
        '$spatialFilter': f'nearby({location["lat"]}, {location["lng"]}, {RADIUS})', 
        '$format': 'JSON'
    }
    response = p.request('Station/NearBy', params)
    if response.status_code == 200:
        data = json.loads(response.content)
        #points = [g.distancematrix(address, f"{i['StationPosition']['PositionLat']},{i['StationPosition']['PositionLon']}") for i in data]
        # df =  = pd.DataFrame({
        #     # '組StationID': [i['StationGroupID'] if 'StationGroupID' in i else None for i in data], #有些縣市沒有提供組StationID
        #     'StationID': [i['StationID'] for i in data],
        #     'StationName': [i['StationName']['Zh_tw'] for i in data],
        #     'RouteNameList': [[j['RouteName']['Zh_tw'] for j in i['Stops']] for i in data]
        #     # 'RouteID': [[j['RouteID'] for j in i['Stops']] for i in data]
        # })
        df = pd.DataFrame(data)
        return df
        
    else:
        print(response.status_code)

'''====================
| 取得公車站預計到站資訊
===================='''
def getEstimatedTimeOfArrival(stationID):
    params= {
        # '$top': 20, 
        '$format': 'JSON'
    }
    response = p.request(f'EstimatedTimeOfArrival/City/{CITY}/PassThrough/Station/{stationID}', params)
    if response.status_code == 200:
        data = json.loads(response.content)
        df = pd.DataFrame(data)
        file = f'{stationID}.csv'
        current_path = os.getcwd()
        if not(os.path.exists(current_path + application_csv_path)): os.mkdir(current_path + application_csv_path)
        df.to_csv(current_path + application_csv_path + file, encoding='utf_8_sig')
        return df
        
    else:
        print(response.status_code)

'''====================
| 未使用
| 取得公車站固定班表
===================='''
def getSchedule(stationID, origin, destination):
    print(origin)
    params= {
        '$format': 'JSON'
    }
    response = p.request(f'Schedule/City/{CITY}/PassThrough/Station/{stationID}', params)
    if response.status_code == 200:
        data = json.loads(response.content)
        df = pd.DataFrame()
        for ___index, ___value in enumerate(data):
            for __index, __value in enumerate(___value['Timetables']):
                if (__value['ServiceDay']['Monday'] and __value['ServiceDay']['Tuesday'] and __value['ServiceDay']['Wednesday'] and __value['ServiceDay']['Thursday']  and __value['ServiceDay']['Friday']):
                    _data = collections.OrderedDict()
                    
                    condition = False
                    for _index, _value in enumerate(__value['StopTimes']):
                        if (_value['StopName']['Zh_tw'] == origin):
                            condition = True
                            
                        if condition:
                            _data[_value['StopName']['Zh_tw']] = _value['ArrivalTime']

                        if (_value['StopName']['Zh_tw'] == destination):
                            condition = False
                    if condition == False:
                        df = df.append(_data, ignore_index=True)
                        print(df)
                        quit()
        file = f'{origin} to {destination}.csv'
        current_path = os.getcwd()
        if not(os.path.exists(current_path + application_csv_path)): os.mkdir(current_path + application_csv_path)
        df.to_csv(current_path + application_csv_path + 'test/' + file, encoding='utf_8_sig')
        return df
        
    else:
        print(response.status_code)
