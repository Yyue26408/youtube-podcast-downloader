import yt_dlp
import json
import os
import argparse
from datetime import datetime, timedelta

KEYWORD = "ai podcast"
DOWNLOAD_PATH = "./downloads/"
LOG_FILE = "downloaded_ids.json"

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

class MyLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"❌ 错误: {msg}")

def filter_by_date_and_id(info_dict, downloaded_ids):
    if info_dict.get('_type') == 'playlist':
        return None
        
    video_id = info_dict.get('id')
    upload_date = info_dict.get('upload_date')
    
    if video_id in downloaded_ids:
        print(f"⏭️ 跳过已下载: {info_dict.get('title', 'Unknown')}")
        return "已存在于本地缓存"
        
    if upload_date:
        vid_date = datetime.strptime(upload_date, '%Y%m%d')
        if datetime.now() - vid_date > timedelta(days=2):
            print(f"📅 跳过过期视频 (>2天): {info_dict.get('title', 'Unknown')}")
            return "视频发布日期超过2天"
    
    print(f"✅ 符合条件，准备下载: {info_dict.get('title', 'Unknown')}")
    return None

def create_ydl_opts(cookies_file=None):
    downloaded_ids = load_downloaded_ids()
    
    def match_filter(info_dict):
        return filter_by_date_and_id(info_dict, downloaded_ids)
    
    opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{DOWNLOAD_PATH}%(title)s.%(ext)s',
        'logger': MyLogger(),
        'match_filter': match_filter,
        'ignoreerrors': True,
        'extract_flat': False,
        'sleep_interval': 5,
        'sleep_interval_subtitles': 5,
        'max_sleep_interval': 10,
    }
    
    if cookies_file:
        opts['cookiefile'] = cookies_file
        print(f"🍪 使用 Cookies 文件: {cookies_file}")
    
    return opts

def download_audio(cookies_file=None):
    ydl_opts = create_ydl_opts(cookies_file)
    search_query = f"ytsearch10:{KEYWORD}"
    
    print(f"🔍 搜索关键词: {KEYWORD}")
    print(f"📋 获取最近 10 个视频，按日期排序并过滤...")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_query, download=False)
            if not info or 'entries' not in info:
                print("❌ 未搜索到任何视频")
                return
                
            videos = info['entries']
            videos = [v for v in videos if v and v.get('upload_date')]
            videos.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            
            print(f"📹 搜索到 {len(videos)} 个视频，取最新 5 个检查...")
            
            video_urls = [v['webpage_url'] for v in videos[:5]]
            
            for url in video_urls:
                try:
                    ydl.download([url])
                except Exception as e:
                    if "Sign in to confirm" in str(e):
                        print("⚠️ YouTube 要求登录验证，请检查 Cookies 是否正确配置")
                    else:
                        print(f"下载失败: {e}")
                    
        except Exception as e:
            print(f"执行异常: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookies', help='Path to cookies.txt file', default=None)
    args = parser.parse_args()
    
    download_audio(cookies_file=args.cookies)
