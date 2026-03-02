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
    "🤖 机器人与具身智能": ["机器人", "robot", "embodied", "vla", "智元", "宇树"],
    "🧠 AI 与大模型": ["ai", "模型", "gpt", "llm", "深度学习", "训练"],
    "🛠️ 编程与嵌入式": ["python", "stm32", "ros", "git", "linux", "matlab"],
}

def get_ai_summary(news_text):
    """调用 DeepSeek API 进行摘要总结"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "⚠️ 未配置 AI API Key，跳过总结。"

    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 构建 Prompt，引导 AI 关注你的专业领域
    prompt = f"请根据以下科技新闻标题，用 3 句话总结今日最重要的技术趋势。重点关注机器人、具身智能和 AI 模型进展：\n\n{news_text}"
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个资深的科技分析师，擅长从繁杂信息中提取核心价值。"},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 总结失败: {str(e)}"

def fetch_and_process():
    grouped_news = {cat: [] for cat in CATEGORIES.keys()}
    grouped_news["🌐 综合科技"] = []
    all_titles = []
    
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)

    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if hasattr(entry, 'published_parsed') else None
            if pub_date and pub_date > one_day_ago:
                # 分类
                found_cat = "🌐 综合科技"
                for cat, keywords in CATEGORIES.items():
                    if any(k in entry.title.lower() for k in keywords):
                        found_cat = cat
                        break
                
                item = f"• {entry.title} ({source})\n  🔗 {entry.link}"
                grouped_news[found_cat].append(item)
                all_titles.append(entry.title)

    # 仅对前 15 条重要标题进行总结，避免内容过长
    summary_input = "\n".join(all_titles[:15])
    ai_summary = get_ai_summary(summary_input) if all_titles else "今日无新闻。"
    
    return ai_summary, grouped_news

def send_push(summary, grouped_data):
    sendkey = os.environ.get("SC_SENDKEY")
    
    # 1. 头部：日期与 AI 深度总结
    header = f"# 📅 {datetime.now().strftime('%m月%d日')} 科技情报\n\n"
    ai_section = f"### 🤖 AI 趋势导航\n> {summary.replace('\n', '\n> ')}\n\n---\n"
    
    # 2. 正文：分类资讯
    body_parts = []
    for category, news_list in grouped_data.items():
        if news_list:
            # 分类标题加粗并带上图标
            section_title = f"#### {category}\n"
            # 列表条目：[来源] 标题 (链接方式)
            formatted_list = "\n".join(news_list)
            body_parts.append(section_title + formatted_list)
    
    full_content = header + ai_section + "\n\n".join(body_parts)
    
    # 3. 发送
    data = {
        "title": f"今日科技简报 - {len(sum(grouped_data.values(), []))} 条更新",
        "desp": full_content
    }
    requests.post(f"https://sctapi.ftqq.com/{sendkey}.send", data=data)

# 在 fetch_and_process 函数中，修改 item 的格式：
# item = f"• **[{source}]** [{entry.title}]({entry.link})"

if __name__ == "__main__":
    summary, news = fetch_and_process()
    send_push(summary, news)