# 🤖 Tech News Daily

> **基于 GitHub Actions + DeepSeek AI + Server 酱的早报**

这是一个自动化资讯追踪系统。每天早上 **07:00 (UTC+8)**，系统会自动汇总全球前沿动态，并通过 AI 生成深度摘要，直接推送到你的微信。

## 🌟 核心亮点

* **AI 智能摘要**：利用 **DeepSeek-V3/R1** 自动提炼新闻重点，一眼看透当日技术风向。
* **全自动化流程**：零成本运行在 GitHub Actions 上，无需购置服务器。

## 📂 项目结构

```text
.
├── .github/workflows/
│   └── daily_job.yml     # GitHub Actions 自动化流程配置
├── daily_news.py         # 核心 Python 脚本 (爬虫 + AI + 推送)
└── README.md             # 本文档

```

## 🚀 快速部署

### 1. 配置 API 密钥

为了使系统正常工作，你需要在 GitHub 仓库的 `Settings -> Secrets and variables -> Actions` 中添加以下两个加密变量：

| 变量名 | 说明 | 来源 |
| --- | --- | --- |
| `SC_SENDKEY` | Server 酱推送密钥 | [sct.ftqq.com](https://sct.ftqq.com/) |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | [platform.deepseek.com](https://platform.deepseek.com/) |

### 2. 自定义订阅源

在 `daily_news.py` 的 `RSS_FEEDS` 中，已为你预设了以下优质源：

* **核心科技**：IEEE Spectrum (Robotics), 量子位, 36Kr, IT之家
* **游戏文化**：机核网 (Gcores), 游民星空 (GamerSky)
* **数字生活**：爱范儿 (ifanr) - 影视娱乐板块

### 3. 本地运行 (可选)

如果你想在本地测试：

```bash
# 安装依赖
pip install feedparser requests

# 设置环境变量
export SC_SENDKEY="你的密钥"
export DEEPSEEK_API_KEY="你的密钥"

# 执行脚本
python daily_news.py

```

## 🕒 定时任务配置

默认配置在 **北京时间每日 07:00** 运行。
如需调整，请修改 `.github/workflows/daily_job.yml` 中的 `cron` 表达式（注意 GitHub 使用 UTC 时间）：

```yaml
# UTC 23:00 = 北京时间 07:00
- cron: '0 23 * * *'

```