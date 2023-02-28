#実行プログラム
import schedule
import datetime
from time import sleep
import cv2
import time
import glob
import os
import shutil
import json
import requests
from requests_oauthlib import OAuth1Session
from datetime import datetime as dt


#自動撮影
def auto_photo():
    ret, frame = capture.read()
    strdate=datetime.datetime.now().strftime('%Y%m%d_%H%M') 
    fname1="./media/" + strdate + ".jpg"
    fname2="./Movies_ph/" + strdate + ".jpg"
    cv2.imwrite(fname1, frame) 
    cv2.imwrite(fname2, frame) 
    print("撮影できました。")


#動画作成
def auto_movie():
    img_array = []
    for filename in sorted(glob.glob('Movies_Ph/*.jpg')):
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)

    strdate=datetime.datetime.now().strftime('%Y_%m%d')
    name = "./Movies/Movie"+strdate+".mp4"
    out = cv2.VideoWriter(name, cv2.VideoWriter_fourcc(*'H264'), 30.0, size)

    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()

    shutil.rmtree('Movies_ph')
    os.mkdir('Movies_ph')
    
    print("作成できました。")




#自動ツイート
def movie_Tweet():
    
    #観察日数カウント
    start_day = dt(2023,1,15)
    now = dt.now()
    total = now - start_day
    
    
    #ローカルの動画ファイルサイズを取得
    strdate=datetime.datetime.now().strftime('%Y_%m%d')
    totalBytes = os.path.getsize("./Movies/Movie"+strdate+".mp4")

    #メディアIDの取得
    initParams = {
        "command": "INIT",
        "media_type": "video/mp4",
        "total_bytes": totalBytes,
        "media_category": "tweet_video"
    }
    initResponse = twitter.post(url=url_media, data=initParams)
    media_id = initResponse.json()['media_id']

    #分割アップロード
    segment_id = 0
    bytesSent = 0
    with open("./Movies/Movie"+strdate+".mp4", "rb") as f:
        while bytesSent < totalBytes:
            #4MBずつアップロード
            chunk = f.read(4*1024*1024)

            addParams = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": segment_id
            }

            files = {"media": chunk}

            appendResponse = twitter.post(url=url_media, data=addParams, files=files)
        
            segment_id += 1
            bytesSent = f.tell()
            print("%s of %s bytes uploaded" % (str(bytesSent), str(totalBytes)))

        print("アップロード完了")

        #ファイナライズ処理
        finalizeParams = {"command": "FINALIZE", "media_id": media_id}

        finalizeResponse = twitter.post(url=url_media, data=finalizeParams)

        statusParams = {"command": "STATUS", "media_id": media_id}

        statusResponse = twitter.get(url=url_media, params=statusParams)
        processingInfo = statusResponse.json().get("processing_info", None)

        while processingInfo['state'] == 'in_progress':
            time.sleep(1)
            statusResponse = twitter.get(url=url_media, params=statusParams)
            processingInfo = statusResponse.json().get("processing_info", None)
            print(processingInfo)
    
        #テキスト入力
        today = datetime.datetime.now().strftime('%B %d,%Y')
        text = 'テキスト入力'
        #ツイート
        params = {"status": text, "media_ids": media_id}

        twitter.post(url=update_url, data=params)
        





#カメラ設定
deviceid=1
capture = cv2.VideoCapture(deviceid)

#Twitterの設定
API_KEY = 'MY_API_KEY'
API_KEY_SECRET= 'MY_API_KEY_SECRET'
ACCESS_TOKEN = 'MY_ACCESS_TOKEN'
ACCESS_TOKEN_SECRET = 'MY_ACCESS_TOKEN_SECRET'

twitter = OAuth1Session(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

update_url = "https://api.twitter.com/1.1/statuses/update.json"
url_media = "https://upload.twitter.com/1.1/media/upload.json"



#実行時間設定
#schedule.every(30).seconds.do(auto_photo)
schedule.every(6).minutes.do(auto_photo)
schedule.every().days.at("20:41").do(auto_movie)
schedule.every().days.at("21:06").do(movie_Tweet)

#イベント実行
while True:
    schedule.run_pending()
    sleep(1)

