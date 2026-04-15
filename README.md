# BroadFSC Global Automation System

**Zero Cost · AI-Powered · Global Coverage**

## System Architecture

```
GitHub Actions (Scheduler)
    |
    +-- daily_promotion.yml (Every 30 min)
    |       |-- daily_promotion.py
    |       |     Sends pre-market briefings to Telegram channels
    |       |     Languages: English / Spanish / Arabic
    |       |     Regions: APAC / Middle East / Europe / Americas
    |       |
    +-- social_posting.yml (Daily at 14:00 UTC)
            |-- social_poster.py
            |     Posts to X/Twitter + LinkedIn
            |-- reddit_poster.py
                  Posts to Reddit (rotation: r/investing, r/stocks, etc.)

Telegram Bot (@BroadInvestBot)  --  24/7 Customer Service
    |-- telegram_bot.py (Deploy to Railway)
```

## Project Files

```
broadfsc-automation/
├── daily_promotion.py          # Pre-market briefings to Telegram channels
├── social_poster.py            # Cross-platform posting (X + LinkedIn)
├── reddit_poster.py            # Reddit auto-poster (rotation strategy)
├── telegram_bot.py             # 24/7 Telegram customer service bot
├── Procfile                    # Railway deployment config
├── runtime.txt                 # Python version for Railway
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── .github/workflows/
│   ├── daily_promotion.yml     # Pre-market briefing scheduler (every 30 min)
│   └── social_posting.yml      # Social media posting scheduler (daily)
└── README.md
```

## GitHub Secrets Required

### Core (Already Configured)
| Secret | Status | Description |
|--------|--------|-------------|
| TELEGRAM_BOT_TOKEN | SET | Telegram Bot API token |
| TELEGRAM_CHANNEL_ID | SET | Main English channel ID |
| GROQ_API_KEY | SET | Groq AI API key (llama-3.1-8b-instant) |

### Multi-Language Channels (Optional)
| Secret | Status | Description |
|--------|--------|-------------|
| TELEGRAM_CHANNEL_ES | PENDING | Spanish channel ID (e.g. @BroadFSC_ES) |
| TELEGRAM_CHANNEL_AR | PENDING | Arabic channel ID (e.g. @BroadFSC_AR) |

### Social Media (Optional)
| Secret | Status | Description |
|--------|--------|-------------|
| X_API_KEY | PENDING | X/Twitter API key |
| X_API_SECRET | PENDING | X/Twitter API secret |
| X_ACCESS_TOKEN | PENDING | X/Twitter access token |
| X_ACCESS_TOKEN_SECRET | PENDING | X/Twitter access token secret |
| LINKEDIN_ACCESS_TOKEN | PENDING | LinkedIn OAuth token |

### Reddit (Enable After 2-Week Account Aging)
| Secret | Status | Description |
|--------|--------|-------------|
| REDDIT_ENABLED | PENDING | Set to "true" to enable |
| REDDIT_CLIENT_ID | PENDING | Reddit app client_id |
| REDDIT_CLIENT_SECRET | PENDING | Reddit app client_secret |
| REDDIT_USERNAME | PENDING | Reddit username |
| REDDIT_PASSWORD | PENDING | Reddit password |

## Daily Schedule (UTC)

| Time (UTC) | Region | Markets |
|------------|--------|---------|
| 00:00 | Asia-Pacific | Japan, Korea, HK, Singapore, Australia, India |
| 05:30 | Middle East | Saudi Arabia (Tadawul), UAE (DFM/ADX) |
| 07:00 | Europe | UK (LSE), Germany (Xetra), France (Euronext) |
| 13:30 | Americas | US (NYSE/NASDAQ), Brazil (B3) |
| 14:00 | Social | Daily post to X, LinkedIn, Reddit |

## Free Tier Limits

| Tool | Free Quota | Usage |
|------|-----------|-------|
| GitHub Actions | 2000 min/month | ~10 min/day = 300 min/month |
| Groq API | ~50K tokens/day | ~10K tokens/day |
| Railway | $5 credit/month | Sufficient for bot hosting |
| Telegram Bot API | Unlimited | No limit |

**Estimated Monthly Cost: $0**

## Setup Guide

### 1. Create Multi-Language Telegram Channels
- Open Telegram > New Channel
- Create @BroadFSC_ES (Spanish) and @BroadFSC_AR (Arabic)
- Add @BroadInvestBot as admin to each channel
- Send me the channel IDs

### 2. Set Up X/Twitter API (Optional)
1. Go to https://developer.twitter.com
2. Create a new App
3. Enable OAuth 1.0a
4. Copy API Key, API Secret, Access Token, Access Token Secret
5. Add to GitHub Secrets

### 3. Set Up LinkedIn API (Optional)
1. Go to https://developer.linkedin.com
2. Create an App
3. Request marketing developer platform access
4. Get OAuth access token
5. Add to GitHub Secrets

### 4. Deploy Customer Service Bot to Railway
1. Go to https://railway.app and sign up (free)
2. New Project > Deploy from GitHub repo
3. Select: msli2233bin/broadfsc-automation
4. Railway will auto-detect Procfile
5. Add environment variables: TELEGRAM_BOT_TOKEN, GROQ_API_KEY
6. Deploy - bot runs 24/7

### 5. Enable Reddit Posting (After 2-Week Aging)
1. Create Reddit app at https://www.reddit.com/prefs/apps
2. Add credentials to GitHub Secrets
3. Set REDDIT_ENABLED = "true"
4. Bot will post 1x/day, rotating subreddits

## Compliance

- All content includes risk disclaimers
- No guaranteed returns promised
- Professional tone across all platforms
- Multi-language content adapted per region
