import feedparser
import requests
import os
import logging
from datetime import datetime, timedelta

# ================== 基础配置 ==================

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

MAX_PER_CATEGORY = 6

logging.basicConfig(level=logging.INFO)

session = requests.Session()

# ================== AI 总结 ==================

def get_ai_summary(news_text):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "⚠️ 未配置 DEEPSEEK_API_KEY"

    url = "https://api.deepseek.com/chat/completions"

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "你是科技分析师。请用3句简练的话总结今日技术趋势，重点关注机器人和AI。"
            },
            {"role": "user", "content": news_text}
        ]
    }

    try:
        response = session.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        response.raise_for_status()

        res_json = response.json()
        content = res_json.get("choices", [{}])[0].get("message", {}).get("content")

        if not content:
            return "⚠️ AI 返回内容异常"

        return content.strip()

    except requests.RequestException as e:
        logging.error(f"AI API 请求失败: {e}")
        return "（AI 总结暂时不可用）"


# ================== 抓取与分类 ==================

def fetch_and_process():
    grouped_news = {cat: [] for cat in CATEGORIES.keys()}
    grouped_news["🌐 综合科技"] = []

    seen_titles = set()
    all_titles = []

    now = datetime.now()
    one_day_ago = now - timedelta(days=1)

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                pub_struct = getattr(entry, "published_parsed", None)
                if not pub_struct:
                    continue

                pub_date = datetime(*pub_struct[:6])
                if pub_date < one_day_ago:
                    continue

                title = entry.title.strip()

                if title in seen_titles:
                    continue
                seen_titles.add(title)

                title_lower = title.lower()

                category_found = "🌐 综合科技"

                for cat, keywords in CATEGORIES.items():
                    if any(k in title_lower for k in keywords):
                        category_found = cat
                        break

                # item = f"• **[{source}]** [{title}]({entry.link})"
                item = f"{len(grouped_news[category_found]) + 1}. **{title}** ([{source}]({entry.link}))"

                if len(grouped_news[category_found]) < MAX_PER_CATEGORY:
                    grouped_news[category_found].append(item)

                all_titles.append(title)

        except Exception as e:
            logging.error(f"{source} 抓取失败: {e}")

    summary_input = "\n".join(all_titles[:20])
    ai_summary = get_ai_summary(summary_input) if all_titles else "今日无重大更新。"

    return ai_summary, grouped_news


# ================== 组装 Markdown ==================

def build_markdown(summary, grouped_data):
    # 1. 标题增加装饰，更有报纸感
    header = f"# 🚀 {datetime.now().strftime('%m/%d')} 科技早报\n\n"
    
    # 2. AI 总结部分：增加优雅降级
    # 如果 summary 包含错误提示，则不显示这个板块
    if "⚠️" in summary or "不可用" in summary or "失败" in summary:
        ai_section = ""
    else:
        quoted_summary = summary.replace("\n", "\n> ")
        ai_section = f"### 💡 今日深度导航\n> {quoted_summary}\n\n---\n\n"

    # 3. 正文分类：增加分隔符和间距
    body_parts = []
    for category, news_list in grouped_data.items():
        if news_list:
            # 分类名加粗并空行
            section = f"### {category}\n" + "\n".join(news_list)
            body_parts.append(section)

    # 用分隔线连接各个分类
    main_body = "\n\n---\n\n".join(body_parts)
    
    footer = "\n\n---\n*📫 自动发送自 GitHub Actions *"
    
    return header + ai_section + main_body + footer


# ================== 推送 ==================

def send_push(content):
    sendkey = os.environ.get("SC_SENDKEY")
    if not sendkey:
        logging.warning("未配置 SC_SENDKEY，跳过推送")
        return

    try:
        session.post(
            f"https://sctapi.ftqq.com/{sendkey}.send",
            data={
                "title": f"今日科技简报 - {datetime.now().strftime('%m-%d')}",
                "desp": content
            },
            timeout=20
        )
        logging.info("推送成功")

    except requests.RequestException as e:
        logging.error(f"推送失败: {e}")


# ================== 主程序 ==================

if __name__ == "__main__":
    summary, news = fetch_and_process()
    markdown_content = build_markdown(summary, news)
    send_push(markdown_content)