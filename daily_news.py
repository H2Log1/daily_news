import feedparser
import requests
import os
import logging
from datetime import datetime, timedelta, timezone

# ================== 基础配置 ==================

RSS_FEEDS = {
    "IT之家": "https://www.ithome.com/rss/",
    "36氪": "https://36kr.com/feed",
    "IEEE Robotics": "https://spectrum.ieee.org/feeds/topic/robotics.rss",
    "量子位": "https://www.qbitai.com/feed",
    "机核网": "https://rsshub.app/gcores/category/1",
    "游民星空": "https://rsshub.app/gamersky/news",
    "爱范儿": "https://rsshub.app/ifanr/category/entertainment"
}

CATEGORIES = {
    "🤖 机器人与具身智能": ["机器人", "robot", "embodied", "vla", "智元", "驱动器"],
    "🧠 AI 与大模型": ["ai", "模型", "gpt", "llm", "深度学习", "人工智能"],
    "🎮 游戏快讯": ["游戏", "steam", "任天堂", "nintendo", "主机", "ps5", "xbox", "机核"],
    "🎬 影视动态": ["电影", "剧集", "netflix", "漫威", "预告", "院线", "豆瓣"],
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

    # 修改 get_ai_summary 内部的 payload
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system", 
                "content": "你是科技与娱乐深度分析师。请用4句精练的话总结今日动态：前2句侧重机器人与AI的前沿突破，后2句侧重游戏、影视行业的重大快讯。"
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
    # 扩展分类
    grouped_news = {cat: [] for cat in CATEGORIES.keys()}
    grouped_news["🌐 综合资讯"] = []

    seen_titles = set()
    all_titles_for_ai = []

    # 关键：统一使用带时区信息的 UTC 时间判定
    # 很多源显示为 0 是因为本地时间与服务器 UTC 时间 8 小时差导致判定失效
    now_utc = datetime.now(timezone.utc)
    one_day_ago = now_utc - timedelta(days=1)

    for source, url in RSS_FEEDS.items():
        try:
            # 必须添加 User-Agent 伪装，解决 IT之家 Connection Reset 和 RSSHub 拦截问题
            feed = feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # 日志诊断：如果抓到 0 条，可能是时间格式或链接无法访问
            count = 0
            for entry in feed.entries:
                # 兼容多种日期字段
                pub_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
                if not pub_struct: continue
                
                # 转换时间并强制对齐到 UTC
                pub_date = datetime(*pub_struct[:6], tzinfo=timezone.utc)
                if pub_date < one_day_ago: continue

                title = entry.title.strip()
                if title in seen_titles: continue
                seen_titles.add(title)

                # 分类搜索逻辑
                title_lower = title.lower()
                category_found = "🌐 综合资讯"
                for cat, keywords in CATEGORIES.items():
                    if any(k in title_lower for k in keywords):
                        category_found = cat
                        break

                # 排版优化：使用 Markdown 链接 [标题](链接)，解决长 URL 乱跳问题
                idx = len(grouped_news[category_found]) + 1
                item = f"{idx}. **[{source}]** [{title}]({entry.link})"
                
                if len(grouped_news[category_found]) < MAX_PER_CATEGORY:
                    grouped_news[category_found].append(item)
                    all_titles_for_ai.append(f"[{category_found}] {title}")
                    count += 1
            
            logging.info(f"✅ {source}: 成功解析 {count} 条")

        except Exception as e:
            logging.error(f"❌ {source} 请求失败: {e}")

    summary_input = "\n".join(all_titles_for_ai[:25])
    ai_summary = get_ai_summary(summary_input) if all_titles_for_ai else "今日暂无更新。"

    return ai_summary, grouped_news


# ================== 组装 Markdown ==================

def build_markdown(summary, grouped_data):
    header = f"# 🚀 {datetime.now().strftime('%m/%d')} 早报\n\n"
    
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
                "title": f"今日简报 {datetime.now().strftime('%m-%d')}",
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