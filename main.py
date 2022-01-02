from configparser import ConfigParser
from package.subpackage1 import *
import Analysis
import Application

'''-------------------------------------------------'''
if __name__ == '__main__':
    '''====================
    | 讀取 config.ini
    ===================='''
    globalvar._init()
    config = ConfigParser()
    config.read('config.ini', encoding='utf8')
    globalvar.set_value('radius', config['DEFAULT']['RADIUS'])
    globalvar.set_value('city', config['DEFAULT']['CITY'])
    globalvar.set_value('img_path', config['DEFAULT']['IMG_PATH'])
    globalvar.set_value('csv_path', config['DEFAULT']['CSV_PATH'])
    globalvar.set_value('application_csv_path', config['DEFAULT']['APPLICATION_CSV_PATH'])

    config.read('token.ini', encoding='utf8')
    app_id = config['token']['id']
    app_key = config['token']['key']
    p = auth.PTX(app_id, app_key)
    globalvar.set_value('PTX', p)

    googlemaps_key = config['googlemaps-token']['key']
    g = auth.GoogleMap(googlemaps_key)
    globalvar.set_value('GoogleMap', g)

    Analysis.main() #執行 analysis.py
    Application.main() #執行 application.py