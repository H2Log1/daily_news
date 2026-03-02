import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone

# 科技资讯 RSS 源列表（可自行添加）
RSS_FEEDS = [
    "https://www.ithome.com/rss/",       # IT之家
    "https://36kr.com/feed",             # 36氪
]

def fetch_tech_news():
    print("正在抓取科技资讯...")
    news_list = []
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 解析发布时间并转换为 UTC
                # 部分 RSS 的日期格式可能略有不同，这里做简单处理
                pub_date = None
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
                if pub_date and pub_date > one_day_ago:
                    item = f"【{feed.feed.title}】{entry.title}\n链接：{entry.link}"
                    news_list.append(item)
        except Exception as e:
            print(f"解析 {url} 出错: {e}")

    return news_list

def send_to_wechat(content_list):
    sendkey = os.environ.get("SC_SENDKEY")
    if not sendkey:
        print("错误：未找到 SC_SENDKEY 环境变量")
        return

    if not content_list:
        content = "过去 24 小时内未发现新的科技资讯。"
    else:
        content = "\n\n---\n\n".join(content_list)

    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = {
        "title": f"今日科技资讯摘要 ({datetime.now().strftime('%m-%d-%Y')})",
        "desp": content
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("推送成功！")
    else:
        print(f"推送失败：{response.text}")

if __name__ == "__main__":
    news = fetch_tech_news()
    send_to_wechat(news)