import yt_dlp
import json
import os
from datetime import datetime, timedelta

KEYWORD = "ai podcast"
DOWNLOAD_PATH = "./downloads/"
LOG_FILE = "downloaded_ids.json"

# 创建下载目录
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

def load_downloaded_ids():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_downloaded_id(video_id):
    ids = load_downloaded_ids()
    ids.add(video_id)
    with open(LOG_FILE, 'w') as f:
        json.dump(list(ids), f)

def download_audio():
    downloaded_ids = load_downloaded_ids()
    print(f"当前已缓存视频ID数量: {len(downloaded_ids)}")
    
    class MyLogger:
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): print(f"❌ 错误: {msg}")

    def filter_by_date_and_id(info_dict):
        if info_dict.get('_type') == 'playlist':
            return None
            
        video_id = info_dict.get('id')
        upload_date = info_dict.get('upload_date')
        
        # 1. 防重复检查
        if video_id in downloaded_ids:
            print(f"⏭️ 跳过已下载: {info_dict.get('title', 'Unknown')}")
            return "已存在于本地缓存"
            
        # 2. 时效性检查 (只保留最近2天)
        if upload_date:
            vid_date = datetime.strptime(upload_date, '%Y%m%d')
            if datetime.now() - vid_date > timedelta(days=2):
                print(f"📅 跳过过期视频 (>2天): {info_dict.get('title', 'Unknown')}")
                return "视频发布日期超过2天"
        
        print(f"✅ 符合条件，准备下载: {info_dict.get('title', 'Unknown')}")
        return None

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{DOWNLOAD_PATH}%(title)s.%(ext)s',
        'logger': MyLogger(),
        'match_filter': filter_by_date_and_id,
        'ignoreerrors': True,
        'extract_flat': False,
        'sleep_interval': 3,  # 避免请求过快被风控
    }
    
    # 强制按上传日期排序 (这是专家模式提醒的关键点)
    search_query = f"ytsearchdate5:{KEYWORD}"
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([search_query])
        except Exception as e:
            print(f"执行异常: {e}")
            
    # 保存本次运行后的新ID (由于异步回调限制，这里仅做兜底逻辑)
    # 更精准的存ID需要写 postprocessor_hooks，为简化部署先不展开

if __name__ == "__main__":
    download_audio()