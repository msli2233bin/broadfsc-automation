"""
BroadFSC 每日全自动推广脚本
功能：AI生成内容 → 合规检查 → 发布到 Reddit / Telegram / X → 记录日志
部署：GitHub Actions 每天 UTC 08:00 自动执行（免费）

依赖安装：
    pip install requests praw groq python-telegram-bot

环境变量（GitHub Secrets 中配置）：
    GROQ_API_KEY          - 从 console.groq.com 获取（免费）
    REDDIT_CLIENT_ID      - 从 reddit.com/prefs/apps 获取
    REDDIT_SECRET         - 同上
    REDDIT_USERNAME       - Reddit 用户名
    REDDIT_PASSWORD       - Reddit 密码
    TELEGRAM_BOT_TOKEN    - 从 @BotFather 获取
    TELEGRAM_CHANNEL_EN   - 英语频道ID，如 @broadfsc_investors
    TELEGRAM_CHANNEL_ES   - 西班牙语频道ID（可选）
"""

import os
import json
import time
import datetime
import requests

# ============================================================
# 初始化 AI 客户端（Groq 免费版）
# ============================================================
try:
    from groq import Groq
    ai_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    AI_MODEL = "llama3-8b-8192"  # 免费、速度快
    print("✅ Groq AI client initialized")
except Exception as e:
    print(f"❌ AI init error: {e}")
    ai_client = None

# ============================================================
# 初始化 Reddit 客户端
# ============================================================
try:
    import praw
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent="BroadFSC Investment Research Bot v1.0"
    )
    print("✅ Reddit client initialized")
except Exception as e:
    print(f"⚠️  Reddit init skipped: {e}")
    reddit = None

# ============================================================
# 内容话题库（按星期轮换）
# ============================================================
WEEKLY_TOPICS = {
    0: {  # 周一
        "topic": "global market outlook and macroeconomic trends",
        "reddit_title": "This Week's Key Market Drivers — Macro Analysis",
        "angle": "macroeconomic analysis and portfolio positioning"
    },
    1: {  # 周二
        "topic": "investment portfolio diversification strategies",
        "reddit_title": "How to Diversify Your Portfolio — Complete Guide",
        "angle": "educational content for beginner and intermediate investors"
    },
    2: {  # 周三
        "topic": "risk management in volatile financial markets",
        "reddit_title": "Risk Management Strategies Every Investor Should Know",
        "angle": "practical risk management techniques"
    },
    3: {  # 周四
        "topic": "emerging market opportunities for international investors",
        "reddit_title": "Emerging Markets 2026: Opportunities Worth Watching",
        "angle": "global investment opportunities and market analysis"
    },
    4: {  # 周五
        "topic": "asset allocation and long-term wealth building",
        "reddit_title": "Asset Allocation Guide: Building Long-Term Wealth",
        "angle": "long-term investment strategy and wealth management"
    },
    5: {  # 周六
        "topic": "understanding investment advisory services and their benefits",
        "reddit_title": "When Should You Use a Professional Investment Advisor?",
        "angle": "value of professional investment guidance"
    },
    6: {  # 周日
        "topic": "financial market trends and investment opportunities for the week ahead",
        "reddit_title": "Weekly Preview: What's Moving Markets This Week",
        "angle": "weekly market preview and actionable insights"
    }
}

# ============================================================
# 目标 Subreddits
# ============================================================
SUBREDDITS_BY_DAY = {
    0: "investing",
    1: "personalfinance",
    2: "stocks",
    3: "financialindependence",
    4: "investing",
    5: "portfolios",
    6: "stockmarket"
}

# ============================================================
# 合规禁语检查
# ============================================================
BANNED_PHRASES = [
    "guaranteed returns", "risk-free", "100% profit", "get rich quick",
    "no risk", "definitely will earn", "sure profit", "cannot lose",
    "guaranteed income", "assured returns", "zero risk"
]

REQUIRED_DISCLAIMER = (
    "\n\n⚠️ *Risk Disclaimer: Investment involves risk. "
    "Past performance is not indicative of future results. "
    "Please consult a licensed advisor before investing.*"
)


def compliance_check(content: str) -> tuple[bool, str]:
    """检查内容是否合规，返回 (通过/失败, 原因)"""
    content_lower = content.lower()
    for phrase in BANNED_PHRASES:
        if phrase in content_lower:
            return False, f"Contains banned phrase: '{phrase}'"
    return True, "OK"


# ============================================================
# AI 内容生成
# ============================================================
def generate_content(platform: str, topic: str, language: str = "English",
                     angle: str = "") -> str:
    """使用 Groq 免费 API 生成平台内容"""
    if not ai_client:
        return f"[{platform}] Fallback content: Explore investment opportunities at broadfsc.com"

    platform_prompts = {
        "reddit_post": f"""Write an informative, educational Reddit post about: "{topic}"

Style requirements:
- Angle: {angle}
- Tone: Helpful, knowledgeable, NOT salesy or promotional
- Format: Well-structured with paragraphs, no excessive markdown
- Length: 300-400 words
- Language: {language}
- Naturally mention "working with a licensed investment advisory firm" as one option
- Do NOT directly promote any brand in the post body
- End with a genuine question to encourage discussion

IMPORTANT: Never promise guaranteed returns or risk-free profits.""",

        "telegram": f"""Write a professional market insight message about: "{topic}"

Requirements:
- Language: {language}
- Tone: Professional financial advisor style
- Length: 200-280 characters (Telegram-friendly)
- Include one actionable insight
- Add emoji for visual appeal (2-3 max)
- End with: "Learn more: broadfsc.com/different"
- NEVER promise guaranteed profits""",

        "twitter": f"""Write an engaging tweet about: "{topic}"

Requirements:
- Language: {language}
- Max 240 characters
- Include 2-3 hashtags: #investing #finance #globalmarkets
- Insightful and data-driven
- NEVER promise guaranteed returns""",
    }

    prompt = platform_prompts.get(platform, platform_prompts["telegram"])

    try:
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.75
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI generation error: {e}")
        return None


# ============================================================
# Reddit 发布
# ============================================================
def post_to_reddit(subreddit_name: str, title: str, content: str) -> bool:
    """发布帖子到 Reddit"""
    if not reddit:
        print("⏭️  Reddit client not available, skipping")
        return False
    try:
        subreddit = reddit.subreddit(subreddit_name)
        submission = subreddit.submit(title=title, selftext=content)
        print(f"✅ Reddit posted: r/{subreddit_name} | {submission.url}")
        time.sleep(30)  # Reddit 限速保护
        return True
    except Exception as e:
        print(f"❌ Reddit post failed: {e}")
        return False


def comment_on_reddit(subreddit_name: str, search_query: str, reply_content: str) -> bool:
    """在相关热帖下发表有价值的评论"""
    if not reddit:
        return False
    try:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.search(search_query, limit=3, time_filter="day"):
            # 只回复互动量中等的帖子（不抢热帖也不冷帖）
            if 10 <= post.score <= 500 and not post.locked:
                post.reply(reply_content[:500])  # 评论限长
                print(f"✅ Reddit comment on: {post.title[:50]}...")
                time.sleep(60)  # 评论间隔更长
                return True
    except Exception as e:
        print(f"❌ Reddit comment failed: {e}")
    return False


# ============================================================
# Telegram 发布
# ============================================================
def post_to_telegram(channel_id: str, content: str) -> bool:
    """发送消息到 Telegram 频道"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or not channel_id:
        print("⏭️  Telegram config missing, skipping")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": content + REQUIRED_DISCLAIMER,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"✅ Telegram posted to {channel_id}")
            return True
        else:
            print(f"❌ Telegram error {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


# ============================================================
# 日志记录（写入 GitHub Actions 日志）
# ============================================================
def log_result(results: dict):
    """记录每日运行结果"""
    print("\n" + "="*50)
    print(f"📊 Daily Promotion Report — {datetime.date.today()}")
    print("="*50)
    for platform, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {platform}: {'Success' if status else 'Failed'}")
    print("="*50)


# ============================================================
# 主任务
# ============================================================
def main():
    today = datetime.datetime.utcnow()
    weekday = today.weekday()
    topic_config = WEEKLY_TOPICS[weekday]

    topic = topic_config["topic"]
    angle = topic_config["angle"]
    reddit_title = topic_config["reddit_title"]
    subreddit = SUBREDDITS_BY_DAY[weekday]

    print(f"\n🚀 BroadFSC Daily Promotion — {today.strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"📌 Topic: {topic}\n")

    results = {}

    # ── 1. Reddit 帖子 ──────────────────────────────────────
    reddit_content = generate_content("reddit_post", topic, "English", angle)
    if reddit_content:
        ok, reason = compliance_check(reddit_content)
        if ok:
            results["Reddit Post"] = post_to_reddit(subreddit, reddit_title, reddit_content)
        else:
            print(f"⛔ Reddit content failed compliance: {reason}")
            results["Reddit Post"] = False
    else:
        results["Reddit Post"] = False

    # ── 2. Telegram 英语频道 ──────────────────────────────
    tg_en = generate_content("telegram", topic, "English", angle)
    if tg_en:
        ok, reason = compliance_check(tg_en)
        channel_en = os.environ.get("TELEGRAM_CHANNEL_EN", "")
        if ok and channel_en:
            results["Telegram EN"] = post_to_telegram(channel_en, tg_en)
        else:
            print(f"⛔ Telegram EN skipped: {reason if not ok else 'no channel configured'}")
            results["Telegram EN"] = False

    # ── 3. Telegram 西班牙语频道（拉美市场）──────────────
    tg_es = generate_content("telegram", topic, "Spanish", angle)
    if tg_es:
        ok, reason = compliance_check(tg_es)
        channel_es = os.environ.get("TELEGRAM_CHANNEL_ES", "")
        if ok and channel_es:
            results["Telegram ES"] = post_to_telegram(channel_es, tg_es)
        else:
            results["Telegram ES"] = False

    # ── 4. 每周三额外：阿拉伯语内容 ────────────────────────
    if weekday == 2:
        tg_ar = generate_content("telegram", topic, "Arabic", angle)
        if tg_ar:
            ok, _ = compliance_check(tg_ar)
            channel_ar = os.environ.get("TELEGRAM_CHANNEL_AR", "")
            if ok and channel_ar:
                results["Telegram AR"] = post_to_telegram(channel_ar, tg_ar)

    # ── 5. 记录结果 ──────────────────────────────────────
    log_result(results)

    success_count = sum(1 for v in results.values() if v)
    print(f"\n🎉 Completed: {success_count}/{len(results)} tasks succeeded")


if __name__ == "__main__":
    main()
