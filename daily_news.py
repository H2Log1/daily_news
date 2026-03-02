import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone

# 配置
RSS_FEEDS = {
    "IT之家": "https://www.ithome.com/rss/",
    "36氪": "https://36kr.com/feed",
    "IEEE Robotics": "https://spectrum.ieee.org/feeds/topic/robotics.rss",
    "量子位": "https://www.qbitai.com/feed"
}

CATEGORIES = {
    "🤖 机器人与具身智能": ["机器人", "robot", "embodied", "vla", "智元", "驱动器"],
    "🧠 AI 与大模型": ["ai", "模型", "gpt", "llm", "深度学习", "人工智能"],
    "🛠️ 编程与嵌入式": ["python", "stm32", "ros", "linux", "matlab", "开源"],
}

def get_ai_summary(news_text):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key: return "⚠️ 未配置 API Key"

    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个科技分析师。请用3句简练的话总结今日技术趋势，重点关注机器人和AI。"},
            {"role": "user", "content": news_text}
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        res_json = response.json()
        if response.status_code == 200:
            return res_json['choices'][0]['message']['content']
        else:
            # 这里的改进让你能看到真正的错误原因
            error_msg = f"API 错误: {res_json.get('error', {}).get('message', '未知错误')}"
            return f"（AI 总结暂时不可用：{error_msg}）"
    except Exception as e:
        return f"请求异常: {str(e)}"
    
    

def fetch_and_process():
    grouped_news = {cat: [] for cat in CATEGORIES.keys()}
    grouped_news["🌐 综合科技"] = []
    all_titles = []
    
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if hasattr(entry, 'published_parsed') else None
                if pub_date and pub_date > one_day_ago:
                    found_cat = "🌐 综合科技"
                    for cat, keywords in CATEGORIES.items():
                        if any(k in entry.title.lower() for k in keywords):
                            found_cat = cat
                            break
                    
                    # 修复排版：使用 Markdown 链接格式
                    item = f"• **[{source}]** [{entry.title}]({entry.link})"
                    grouped_news[found_cat].append(item)
                    all_titles.append(entry.title)
        except: continue

    summary_input = "\n".join(all_titles[:20])
    ai_summary = get_ai_summary(summary_input) if all_titles else "今日无重大更新。"
    return ai_summary, grouped_news

def send_push(summary, grouped_data):
    sendkey = os.environ.get("SC_SENDKEY")
    if not sendkey: return

    # 修复 f-string 反斜杠报错：先处理好换行引用
    quoted_summary = summary.replace('\n', '\n> ')
    
    header = f"# 📅 {datetime.now().strftime('%m月%d日')} 科技情报\n\n"
    ai_section = f"### 🤖 AI 趋势导航\n> {quoted_summary}\n\n---\n"
    
    body_parts = []
    for category, news_list in grouped_data.items():
        if news_list:
            body_parts.append(f"#### {category}\n" + "\n".join(news_list))
    
    full_content = header + ai_section + "\n\n".join(body_parts)
    
    requests.post(f"https://sctapi.ftqq.com/{sendkey}.send", data={
        "title": f"今日科技简报 - {datetime.now().strftime('%m-%d')}",
        "desp": full_content
    })

if __name__ == "__main__":
    summary, news = fetch_and_process()
    send_push(summary, news)