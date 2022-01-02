import json
import pandas as pd
import mapclassify as mc
import matplotlib.patches as mpatches
import os

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
from package.subpackage1 import *
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta']
import geopandas as gpd

def main():
    global RADIUS ; RADIUS = globalvar.get_value('radius')
    global CITY ; CITY = globalvar.get_value('city')
    global p ; p = globalvar.get_value('PTX')
    global g ; g = globalvar.get_value('GoogleMap')
    global csv_path ; csv_path = globalvar.get_value('csv_path')
    global img_path ; img_path = globalvar.get_value('img_path')
    try:
        current_path = os.getcwd()
        df1 = pd.read_csv(current_path + csv_path + '109行政區人口資料.csv', index_col=[0])
    except FileNotFoundError as e:
        df1 = getDemographicData()

    #| 過濾不必要的資料
    df1 = df1[['site_id', 'people_total', 'area', 'population_density']]
    bool_ = df1['site_id'].str.startswith('高雄市', na=False)
    df1 = df1.loc[bool_]
    df1['city'] = df1['site_id'].apply(lambda x: x[x.find('高雄市'):x.find('高雄市')+3])
    df1['district'] = df1['site_id'].apply(lambda x: x[x.find('高雄市')+3:])

    try:
        current_path = os.getcwd()
        df2 = pd.read_csv(current_path + csv_path + '行政區公車站位統計.csv', index_col=[0])
    except FileNotFoundError as e:
        df2 = getStationCountGroupByDistrict()

    newdf = pd.merge(df1, df2, how='left', left_on=['city', 'district'], right_on=['city', 'district'])
    cols=['people_total', 'area', 'population_density', 'bus_station_total']
    newdf[cols] = newdf[cols].apply(pd.to_numeric, errors='coerce', downcast='float')
    '''=欄位說明================================
    | city:縣市
    | district:行政區
    | people_total:人口數量
    | area:土地面積
    | population_density:人口密度
    | bus_station_total:公車站牌數
    | --
    | bus_station_density:公車站牌密度
    | person_per_bus_station:多少人分配一個公車站牌
    ========================================'''

    newdf['bus_station_density'] = newdf['bus_station_total'] / newdf['area']
    newdf['person_per_bus_station'] = newdf['people_total'] / newdf['bus_station_total']
    newdf = newdf[['city', 'district', 'people_total', 'area', 'population_density', 'bus_station_total', 'bus_station_density', 'person_per_bus_station']] #欄位排序

    current_path = os.getcwd()
    if not(os.path.exists(current_path + csv_path)): os.mkdir(current_path + csv_path)
    newdf.to_csv(current_path + csv_path + '行政區分析結果.csv', encoding='utf_8_sig')
    print(newdf)

    show1() #高雄市各行政區公車站牌統計圖
    
    try:
        current_path = os.getcwd()
        df3 = pd.read_csv(current_path + csv_path + '公車站牌.csv', encoding='utf_8_sig', index_col=[0])
    except FileNotFoundError as e:
        df3 = getStationLocation()
        
    showMap(df3) #高雄市市區公車公車站牌分佈圖
    showMap2(newdf, 'bus_station_total', '公車站牌數量') #高雄市市區公車分層設色圖-公車站牌數量
    showMap2(newdf, 'people_total', '人口數量') #高雄市市區公車分層設色圖-人口數量
    showMap2(newdf, 'population_density', '人口密度') #高雄市市區公車分層設色圖-人口密度
    showMap2(newdf, 'bus_station_density', '公車站牌密度', isFloat=True) #高雄市市區公車分層設色圖-公車站牌密度
    showMap2(newdf, 'person_per_bus_station', '每個公車站牌乘載人口數') #高雄市市區公車分層設色圖-每個公車站牌乘載人口數

'''====================
| 取得109行政區人口統計資料
===================='''
def getDemographicData():
    d = auth.MOI()
    response = d.request()
    data = json.loads(response.content)
    df = pd.DataFrame(data['result']['records'])
    
    current_path = os.getcwd()
    if not(os.path.exists(current_path + csv_path)): os.mkdir(current_path + csv_path)
    df.to_csv(current_path + csv_path + '109行政區人口資料.csv', encoding='utf_8_sig')
    return df

'''====================
| 取得公車站牌所在行政區(同位置多個站牌只算一個)
===================='''
import time
def getStationLocation():
    print('警告！作業附上的 公車站牌.csv 就是執行結果，你確定要執行嗎？\nAPI KEY設有配額，可能會造成無法執行的結果')
    input('按下任意鍵繼續')
    params= {
        '$format': 'JSON'
    }
    response = p.request(f'Station/City/{CITY}', params)
    if response.status_code == 200:
        df = pd.DataFrame(columns=['station_name'])
        data = json.loads(response.content)
        _list = set()
        for _ in data:
            _stationName = _['StationName']['Zh_tw']
            if _stationName not in _list:
                try:
                    lat = _["StationPosition"]["PositionLat"]
                    lng = _["StationPosition"]["PositionLon"]
                    latlng = f'{lat},{lng}'
                    response_ = dict() ; response_['status'] = 'OK'
                    response_ = g.get_geocode_uselatlng(latlng)
                    time.sleep(0.021) # Geocoding API 有 50 QPS(每秒請求數)限制，因此在迴圈增加 21ms 延遲
                    _list.add(_stationName)
                    if response_['status'] == 'OK':
                        address_components = response_['results'][0]['address_components']
                        city = address_components[-3]['long_name']
                        district = address_components[-4]['long_name']
                        village = address_components[-5]['long_name']
                        columns = {
                            'station_name': _stationName,
                            'lat': lat,
                            'lng': lng, 
                            'city': city,
                            'district': district,
                            'village': village
                        }

                    else:
                        columns = {
                            'station_name': _stationName,
                            'lat': lat,
                            'lng': lng
                        }
                        print(response_)
                    
                    new_row = pd.DataFrame(columns, index=[0])
                    print(new_row)
                    df = df.append(new_row, ignore_index=True)
                except Exception as e:
                    print(e)
                    current_path = os.getcwd()
                    if not(os.path.exists(current_path + csv_path)): os.mkdir(current_path + csv_path)
                    df.to_csv(current_path + csv_path + '公車站牌.csv', encoding='utf_8_sig')
                
        print(df)
        current_path = os.getcwd()
        if not(os.path.exists(current_path + csv_path)): os.mkdir(current_path + csv_path)
        df.to_csv(current_path + csv_path + '公車站牌.csv', encoding='utf_8_sig')
        return df
        
    else:
        print(response.status_code)
    
'''====================
| 取得公車站牌數量以行政區劃分
===================='''
def getStationCountGroupByDistrict():
    try:
        current_path = os.getcwd()
        df = pd.read_csv(current_path + csv_path + '公車站牌.csv', encoding='utf_8_sig', index_col=[0])
    except FileNotFoundError as e:
        print(csv_path)
        df = getStationLocation()
    df = df.groupby(['city', 'district'])['district'].count().reset_index(name='bus_station_total')
    
    #| 統計列
    # _ = {
    #     'city': '高雄市', 
    #     'district': '',
    #     'bus_station_total': df['bus_station_total'].sum()
    # }
    # total_row = pd.DataFrame(_, index=[0])
    # df = df.append(total_row, ignore_index=True)
    current_path = os.getcwd()
    if not(os.path.exists(current_path + csv_path)): os.mkdir(current_path + csv_path)
    df.to_csv(current_path + csv_path + '行政區公車站位統計.csv', encoding='utf_8_sig')
    return df

'''====================
| 繪製圖形：公車站牌數量以行政區劃分
===================='''
def show1():
    fig, ax = plt.subplots(1, figsize=(16, 9))

    try:
        current_path = os.getcwd()
        df = pd.read_csv(current_path + csv_path + '行政區公車站位統計.csv', index_col=[0])
    except FileNotFoundError as e:
        df = getStationCountGroupByDistrict()

    df = df[df['city'] == '高雄市']
    df.sort_values('bus_station_total')[['district', 'bus_station_total']].plot(ax=ax, 
                                                                                x="district", 
                                                                                y="bus_station_total", 
                                                                                kind="barh")
    
    title = '高雄市各行政區公車站牌統計圖'
    plt.title(title)
    plt.xlabel('公車站牌數量')
    plt.ylabel('行政區')
    plt.yticks(fontsize=5)
    file = f'{title}.png'
    current_path = os.getcwd()
    if not(os.path.exists(current_path + img_path)): os.mkdir(current_path + img_path)
    plt.savefig(current_path + img_path + file, dpi=300, bbox_inches='tight', padinches=0)
    plt.show()

'''
提供公車站牌 dataframe 資料，輸出地圖
'''
def showMap(df):
    fig, ax = plt.subplots(1, figsize=(9, 8))
    ax.set_aspect('equal')

    town_shp = gpd.read_file('./mapdata202104280245/TOWN_MOI_1100415.shp', encoding='utf-8')
    town_shp[town_shp['COUNTYNAME']!='高雄市'].plot(ax=ax, 
                                                    linewidth=0.3,
                                                    color='gray')
    town_shp[town_shp['COUNTYNAME']=='高雄市'].plot(ax=ax, 
                                                    color='#F5F5DC', 
                                                    linewidth=0.3,
                                                    edgecolor='0.8')

    # df = df[df['district'].str.contains('高雄市')] # 刪除高雄市以外的公車站牌
    town_shp = town_shp.dissolve(by='TOWNNAME').reset_index(drop=False)
    ax.scatter(df['lng'], df['lat'], c='#FFAC00', s=1, marker='.')
    
    LegendElement = [plt.plot([], [], marker='.', label='公車站牌', linewidth=0, color='#FFAC00')[0]]
    ax.legend(handles = LegendElement, loc='lower right', fontsize=8, title='圖例', shadow=True, borderpad=0.6)

    plt.axis([120.1, 121.1, 22.4, 23.5])
    title = '高雄市市區公車公車站牌分佈圖'
    plt.title(title)
    current_path = os.getcwd()
    file = f'{title}.png'
    if not(os.path.exists(current_path + img_path)): os.mkdir(current_path + img_path)
    plt.savefig(current_path + img_path + file, dpi=300, bbox_inches='tight', padinches=0)
    plt.show()

'''
提供公車站牌 dataframe 資料，輸出地圖
'''
def showMap2(df, variable, legend_title, isFloat=False):
    fig, ax = plt.subplots(1, figsize=(9, 8))
    ax.set_aspect('equal')
    
    town_shp = gpd.read_file('./mapdata202104280245/TOWN_MOI_1100415.shp', encoding='utf-8')
    town_shp = town_shp.set_index('TOWNNAME').join(df.set_index('district'))
    
    ax = town_shp[town_shp['COUNTYNAME']!='高雄市'].plot(ax=ax,
                                                        linewidth=0.3,
                                                        color='gray')
    town_shp = town_shp.dropna(axis=0, how='any')

    ax = town_shp[town_shp['COUNTYNAME']=='高雄市'].plot(ax=ax,
                                                    column=variable,
                                                    cmap='Blues',
                                                    legend=True, 
                                                    scheme='BoxPlot',
                                                    linewidth=0.3,
                                                    edgecolor='0.5')

    handles, labels = ax.get_legend_handles_labels() #get existing legend item handles and labels
    
    # 實例化cmap方案
    cmap = plt.get_cmap('Blues')

    # 得到mapclassify中BoxPlot的數據分層點
    bp = mc.BoxPlot(town_shp[variable])
    bins = bp.bins
    
    classes_numbers = len(bins) - 1
    # # 制作圖例映射對象列表
    LegendElement = [mpatches.Patch(facecolor=cmap((1 + _) / classes_numbers), label=f'{"{:.2f}".format(max(bins[_], 0)) if isFloat else int(max(bins[_], 0))} - {"{:.2f}".format(bins[_+1]) if isFloat else int(bins[_+1])}') for _ in range(classes_numbers)] + \
                    [mpatches.Patch(facecolor='lightgrey', edgecolor='black', hatch='////', label='沒有資料')]

    # # 將制作好的圖例映射對象列表導入legend()中，並配置相關參數
    ax.legend(handles = LegendElement, loc='lower right', fontsize=8, title=legend_title, shadow=True, borderpad=0.6)

    # ax.axis('off') #| 隱藏軸值
    # df = df[df['district'].str.contains('高雄市')] # 刪除高雄市以外的公車站牌
    plt.axis([120.1, 121.1, 22.4, 23.5])
    title = '高雄市市區公車分層設色圖'
    plt.title(title)
    file = f'{title}-{legend_title}.png'
    current_path = os.getcwd()
    if not(os.path.exists(current_path + img_path)): os.mkdir(current_path + img_path)
    plt.savefig(current_path + img_path + file, dpi=300, bbox_inches='tight', padinches=0)
    plt.show()
