import os
import requests
from lxml import etree
import urllib.parse
import googleapiclient.discovery

# 從 Vercel 環境變數中讀取
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 初始化 YouTube API 客戶端
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def send_telegram_notification(title, url, type, channel_name):
    """向 Telegram 發送通知訊息"""
    message = f"**新發布！**\n\n頻道：{channel_name}\n類型：{type}\n標題：{title}\n\n連結：{url}"
    
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        requests.post(telegram_url, data=payload, timeout=5)
        print(f"成功發送 Telegram 通知：{title}")
    except requests.exceptions.RequestException as e:
        print(f"發送 Telegram 通知時發生錯誤: {e}")

def get_video_info(video_id):
    """使用 YouTube Data API 獲取影片詳細資訊和類型"""
    try:
        request = youtube.videos().list(
            part="snippet,liveStreamingDetails",
            id=video_id
        )
        response = request.execute()
        
        if not response['items']:
            return None, "影片不存在"

        item = response['items'][0]
        snippet = item['snippet']
        
        # 判斷影片類型
        if 'liveStreamingDetails' in item:
            live_status = item['liveStreamingDetails'].get('activeLiveStreamStatus')
            if live_status == 'upcoming':
                video_type = "預計直播"
            elif live_status == 'live':
                video_type = "直播中"
            else:
                video_type = "普通影片" # 已結束的直播也可能歸類於此
        else:
            video_type = "普通影片"

        video_info = {
            "title": snippet['title'],
            "channelTitle": snippet['channelTitle'],
            "url": f"https://youtu.be/{video_id}"
        }
        
        return video_info, video_type
    
    except Exception as e:
        print(f"獲取影片資訊時發生錯誤: {e}")
        return None, "未知類型"


def handler(request, response):
    """Vercel 伺服器函式入口點"""
    method = request.method
    
    if method == 'GET':
        # 處理 WebSub 訂閱確認請求
        query_params = urllib.parse.parse_qs(request.url.split('?')[1])
        if 'hub.mode' in query_params and query_params['hub.mode'][0] == 'subscribe':
            challenge = query_params.get('hub.challenge', [''])[0]
            response.write(challenge.encode('utf-8'))
            print("WebSub 訂閱已確認。")
            return
        
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
