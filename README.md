# BroadFSC 全自动推广系统

**零成本 · AI 驱动 · 全球覆盖**

## 项目结构

```
broadfsc-automation/
├── scripts/
│   ├── daily_promotion.py    # 每日自动发帖脚本（GitHub Actions 运行）
│   └── telegram_bot.py       # Telegram 智能客服机器人（Railway 部署）
├── .github/
│   └── workflows/
│       └── daily_promotion.yml  # 定时任务配置
├── requirements.txt
└── README.md
```

---

## 快速上手（3步）

### 第1步：获取免费 API 密钥

| 服务 | 注册地址 | 用途 | 费用 |
|------|---------|------|------|
| Groq API | https://console.groq.com | AI内容生成 | 免费 |
| Reddit API | https://www.reddit.com/prefs/apps | 自动发帖 | 免费 |
| Telegram Bot | 找 @BotFather 发 /newbot | 客服+推送 | 免费 |

### 第2步：Fork 本仓库到 GitHub

1. 在 GitHub 创建新仓库，上传本项目文件
2. 进入 `Settings → Secrets and variables → Actions`
3. 添加以下 Secrets：

```
GROQ_API_KEY          = 你的 Groq API Key
REDDIT_CLIENT_ID      = 你的 Reddit App Client ID
REDDIT_SECRET         = 你的 Reddit App Secret
REDDIT_USERNAME       = 你的 Reddit 用户名
REDDIT_PASSWORD       = 你的 Reddit 密码
TELEGRAM_BOT_TOKEN    = 你的 Telegram Bot Token
TELEGRAM_CHANNEL_EN   = 你的英语频道ID（如 @broadfsc_en）
TELEGRAM_CHANNEL_ES   = 你的西班牙语频道ID（可选）
```

### 第3步：启用 Actions + 部署 Bot

**每日推广（GitHub Actions）：**
- 进入 Actions 标签页
- 启用 `BroadFSC Daily AI Promotion` 工作流
- 点击 `Run workflow` 测试一次

**Telegram 客服机器人（Railway）：**
1. 注册 https://railway.app（免费）
2. New Project → Deploy from GitHub repo
3. 选择本仓库，设置启动命令：`python scripts/telegram_bot.py`
4. 在 Railway 添加环境变量：`GROQ_API_KEY` 和 `TELEGRAM_BOT_TOKEN`
5. 部署完成，Bot 永久在线

---

## 注意事项

- **Reddit 养号**：新账号前2周只浏览和评论，不要大量发帖
- **内容质量**：每周检查 AI 生成内容质量，调整提示词
- **合规**：不承诺收益，所有内容包含风险免责声明
- **监控**：在 GitHub Actions 日志中查看每日运行结果

---

## 免费资源限额

| 工具 | 免费额度 | 是否够用 |
|------|---------|---------|
| GitHub Actions | 2000分钟/月 | ✅ 够（每次运行约2分钟）|
| Groq API | 每天约5万Token | ✅ 够（每次约2000Token）|
| Railway | $5额度/月 | ✅ 够运行轻量Bot |
| Telegram Bot API | 无限制 | ✅ |
| Reddit API | 免费版足够 | ✅ |

**预计月总成本：$0**
