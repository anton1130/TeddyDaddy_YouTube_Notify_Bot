import requests
import os

# 替換成你的 Vercel 部署網址，後綴 /api 是我們稍後設定的路由
VERCEL_CALLBACK_URL = "https://your-vercel-project.vercel.app/api"

# 這是你感興趣的 YouTube 頻道 ID 列表
# 你可以增加多個頻道的 ID
CHANNEL_IDS = [
    "UC3aipgNToMvs2pFaQyaM_hg",
    "",
    # ... 更多頻道
]

HUB_URL = "https://pubsubhubbub.appspot.com/"

for channel_id in CHANNEL_IDS:
    topic_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    payload = {
        "hub.mode": "subscribe",
        "hub.callback": VERCEL_CALLBACK_URL,
        "hub.topic": topic_url,
        "hub.verify": "async" # 建議使用非同步驗證
    }

    response = requests.post(HUB_URL, data=payload)

    if response.status_code == 202:
        print(f"成功發送訂閱請求給頻道 {channel_id}。")
    else:
        print(f"訂閱頻道 {channel_id} 失敗。狀態碼: {response.status_code}, 錯誤訊息: {response.text}")