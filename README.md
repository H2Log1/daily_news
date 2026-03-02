# 🚀 Daily Tech News Push

这是一个基于 **Python** 和 **GitHub Actions** 实现的自动化科技资讯抓取与推送工具。

每天早上 **07:00 (北京时间)**，系统会自动抓取过去 24 小时内的硬核科技动态，并通过 **Server 酱** 推送到你的微信上。

## ✨ 功能特性

* **完全自动化**：利用 GitHub Actions 定时触发，无需服务器部署。
* **精准抓取**：基于 RSS 订阅源，仅筛选过去 24 小时内的最新内容。
* **微信提醒**：集成 Server 酱 API，手机微信即时接收摘要。
* **高度可定制**：轻松添加或更换你感兴趣的科技资讯源。

## 🛠️ 快速上手

### 1. 准备工作

* 获取你的 Server 酱 **SendKey**（[点击此处前往官网](https://sct.ftqq.com/)）。
* 在 GitHub 仓库中配置 `Secret`：
* 进入 `Settings` -> `Secrets and variables` -> `Actions`。
* 点击 `New repository secret`。
* Name 填入：`SC_SENDKEY`，Value 填入你的密钥。

### 2. 项目结构

```text
.
├── .github/workflows/
│   └── daily_job.yml     # GitHub Actions 配置文件
├── daily_news.py         # Python 抓取与推送脚本
└── README.md             # 项目说明文档

```

### 3. 自定义订阅源

如果你关注其他领域，可以修改 `daily_news.py` 中的 `RSS_FEEDS` 列表。

## ⚙️ 配置说明

### 定时任务

在 `.github/workflows/daily_job.yml` 中，你可以修改 `cron` 表达式来调整推送时间：

```yaml
on:
  schedule:
    - cron: '0 23 * * *'  # 对应北京时间早上 7 点

```

## 📝 开源许可

本项目采用 [MIT License](https://www.google.com/search?q=LICENSE) 开源。

欢迎 Fork 和 Star！如果你有任何建议或改进，欢迎提交 Pull Request。