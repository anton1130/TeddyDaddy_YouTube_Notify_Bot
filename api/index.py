import os
import requests
from lxml import etree
import urllib.parse
import googleapiclient.discovery
from http.server import BaseHTTPRequestHandler

# 從 Vercel 環境變數中讀取
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 初始化 YouTube API 客戶端
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# ... (send_telegram_notification 和 get_video_info 函式保持不變) ...

def handler(request, response):
    """
    Vercel 伺服器函式入口點
    處理所有進入的 HTTP 請求
    """
    method = request.method
    
    if method == 'GET':
        # 處理 WebSub 訂閱確認請求
        query_params = urllib.parse.parse_qs(request.url.split('?')[1])
        if 'hub.mode' in query_params and query_params['hub.mode'][0] == 'subscribe':
            challenge = query_params.get('hub.challenge', [''])[0]
            response.write(challenge.encode('utf-8'))
            print("WebSub 訂閱已確認。")
            return
        
        # 處理其他 GET 請求 (可選)
        response.write("機器人已啟動。")

    elif method == 'POST':
        # 處理 WebSub 影片發布通知
        try:
            tree = etree.fromstring(request.body)
            # 使用 lxml 找到影片 ID
            video_id_element = tree.find(".//{http://www.youtube.com/xml/schemas/2015}videoId")
            if video_id_element is not None:
                video_id = video_id_element.text
                
                # 獲取影片資訊並判斷類型
                video_info, video_type = get_video_info(video_id)
                
                if video_info and video_type:
                    # 發送 Telegram 通知
                    send_telegram_notification(
                        video_info['title'],
                        video_info['url'],
                        video_type,
                        video_info['channelTitle']
                    )
            
            response.write("通知已接收。")
            
        except etree.LxmlError as e:
            response.write("XML 解析錯誤。")
            print(f"XML 解析錯誤: {e}")

    else:
        response.write("不支持的請求方法。")
