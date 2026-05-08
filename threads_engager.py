"""
Threads 社区评论机器人
==================
搜索投资相关hashtag，AI生成有见地的评论并回复。

API 限制：250 posts/day, 1000 replies/day
认证：OAuth 2.0 Bearer Token

运行：
    python threads_engager.py              # 默认：搜索+回复最多5条
    python threads_engager.py --dry-run    # 只搜索不回复
    python threads_engager.py --limit 3    # 最多回复3条
    python threads_engager.py --check      # 查看已回复效果
"""
import os
import sys
import json
import time
import random
import re
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from groq import Groq

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

API_BASE = "https://graph.threads.net/v1.0"

# 状态文件
STATE_FILE = Path(__file__).parent / ".bot_memory" / "threads_engagements.json"

# 搜索hashtag池（Threads用hashtag搜索）
SEARCH_HASHTAGS = [
    "investing", "stocks", "stockmarket", "trading", "technicalanalysis",
    "Nvidia", "Apple", "Tesla", "Bitcoin", "ETF", "forex", "goldprice",
    "marketNews", "earnings", "SP500", "nasdaq", "fedrate", "recession",
]

# 每日回复上限
DAILY_LIMIT = 5

# 跳过模式（广告/垃圾）
SKIP_PATTERNS = [
    r"buy now|sell now|pump|to the moon|moon shot",
    r"click here|sign up|follow me|subscribe|dm me",
    r"giveaway|free money|airdrop|promo code",
    r"prop firm|funded trader|instant funding",
]

FINANCE_KEYWORDS = [
    "stock", "invest", "trad", "portfolio", "market", "etf", "bond",
    "dividend", "earning", "revenue", "valuation", "bull", "bear",
    "sector", "index", "fed", "rate", "inflation", "gdp", "recession",
    "option", "future", "forex", "crypto", "bitcoin", "commodity",
    "rsi", "macd", "support", "resistance", "breakout", "volume",
    "$aapl", "$tsla", "$nvda", "$msft", "$amzn", "$googl", "$meta",
]

# ============================================================
# Groq 客户端
# ============================================================
def get_groq():
    if not GROQ_API_KEY:
        return None
    return Groq(api_key=GROQ_API_KEY)


# ============================================================
# Threads API 封装
# ============================================================
def threads_get(endpoint, params=None):
    """GET 请求 Threads API"""
    if params is None:
        params = {}
    params["access_token"] = THREADS_ACCESS_TOKEN
    try:
        import requests
        resp = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"GET {endpoint} error: {e}")
        return None


def threads_post(endpoint, data=None, params=None):
    """POST 请求 Threads API"""
    if params is None:
        params = {}
    params["access_token"] = THREADS_ACCESS_TOKEN
    try:
        import requests
        resp = requests.post(f"{API_BASE}/{endpoint}", params=params, json=data, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"POST {endpoint} error: {e}")
        return None


def get_hashtag_id(hashtag):
    """获取hashtag的ID（用于搜索）"""
    result = threads_get(f"tags/{hashtag}")
    if result and "id" in result:
        return result["id"]
    return None


def search_hashtag_posts(hashtag, limit=25):
    """搜索hashtag下的帖子"""
    hid = get_hashtag_id(hashtag)
    if not hid:
        logger.warning(f"Hashtag '{hashtag}' not found")
        return []
    result = threads_get(f"tags/{hid}/recent_media", {
        "fields": "id,caption,media_type,timestamp,permalink,username,comments_count,like_count",
        "limit": limit,
    })
    if result and "data" in result:
        return result["data"]
    return []


def reply_to_post(media_id, text):
    """回复一条Threads帖子"""
    result = threads_post(f"{media_id}/replies", {"text": text})
    return result


# ============================================================
# 状态管理
# ============================================================
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {"replied_to": [], "daily_count": 0, "last_reset": "", "total_engagements": 0}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def reset_daily_count(state):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_reset") != today:
        state["daily_count"] = 0
        state["last_reset"] = today
    return state


# ============================================================
# 内容筛选
# ============================================================
def should_engage(post, state):
    """判断是否值得回复"""
    media_id = post.get("id", "")
    caption = post.get("caption", "") or ""
    username = post.get("username", "")

    # 已回复过
    if media_id in state["replied_to"]:
        return False, "already_replied"

    # 内容太短
    if len(caption) < 60:
        return False, "too_short"

    # 跳过广告
    text_lower = caption.lower()
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text_lower):
            return False, "spam_pattern"

    # 必须投资相关
    has_finance = any(kw in text_lower for kw in FINANCE_KEYWORDS)
    if not has_finance:
        return False, "not_finance_related"

    return True, "ok"


def classify_post(caption):
    """分类帖子类型"""
    text_lower = caption.lower()
    if "?" in caption or any(w in text_lower for w in ["how", "what", "why", "should i", "do you think"]):
        return "question"
    if any(w in text_lower for w in ["rsi", "macd", "support", "resistance", "earnings", "revenue"]):
        return "analysis"
    return "discussion"


# ============================================================
# AI 生成评论
# ============================================================
def generate_comment(post_caption, post_type, groq_client):
    """用AI生成有见地的评论"""
    if not groq_client:
        # 后备模板
        templates = {
            "question": "Great question. The key is to look at the technical indicators alongside fundamentals. RSI divergence often signals a reversal before price action confirms it.",
            "analysis": "Solid analysis. One thing to add: volume confirmation is critical when evaluating breakout setups. Without it, false breakouts are common.",
            "discussion": "Interesting perspective. The interplay between macro factors and technical levels is what makes this market particularly nuanced right now.",
        }
        return templates.get(post_type, templates["discussion"])[:300]

    prompt = f"""You are a seasoned financial analyst commenting on a social media post.

RULES:
- Write a thoughtful, concise reply (150-280 chars, keep it short)
- Add 1 specific insight (RSI, MACD, support/resistance, earnings, sector trend)
- Do NOT use emojis
- Do NOT introduce yourself or pitch anything
- Sound like a real person, not an AI
- Do not use "Great post" or "Thanks for sharing"

Post type: {post_type}
Post content: {post_caption[:300]}

Your reply:"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.8,
        )
        comment = resp.choices[0].message.content.strip()
        # 清理引号和多余内容
        comment = re.sub(r'^["\']+|["\']+$', '', comment)
        return comment[:500]
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None


# ============================================================
# 主逻辑
# ============================================================
def run_engager(dry_run=False, limit=None):
    """主函数：搜索并回复"""
    if not THREADS_ACCESS_TOKEN:
        logger.error("THREADS_ACCESS_TOKEN not set!")
        return

    state = load_state()
    state = reset_daily_count(state)

    groq_client = get_groq()
    if not groq_client:
        logger.warning("Groq not available, using templates")

    # 选随机hashtag
    hashtags = random.sample(SEARCH_HASHTAGS, min(5, len(SEARCH_HASHTAGS)))
    logger.info(f"Searching hashtags: {hashtags}")

    candidates = []
    for tag in hashtags:
        posts = search_hashtag_posts(tag, limit=20)
        logger.info(f"  #{tag}: {len(posts)} posts")
        for post in posts:
            ok, reason = should_engage(post, state)
            if ok:
                post["_tag"] = tag
                post["_type"] = classify_post(post.get("caption", ""))
                candidates.append(post)
        if len(candidates) >= (limit or DAILY_LIMIT) * 3:
            break

    if not candidates:
        logger.info("No suitable posts found to engage with.")
        return

    # 按热度排序
    candidates.sort(key=lambda p: (p.get("like_count", 0) + p.get("comments_count", 0) * 3), reverse=True)
    to_reply = candidates[:limit or DAILY_LIMIT]

    logger.info(f"Found {len(candidates)} candidates, replying to {len(to_reply)}")

    for post in to_reply:
        if state["daily_count"] >= DAILY_LIMIT:
            logger.info("Daily limit reached.")
            break
        if dry_run:
            print(f"[DRY-RUN] Would reply to @{post.get('username')}: {post.get('caption', '')[:80]}...")
            continue

        comment = generate_comment(post.get("caption", ""), post.get("_type", "discussion"), groq_client)
        if not comment:
            continue

        result = reply_to_post(post["id"], comment)
        if result and "id" in result:
            logger.info(f"✓ Replied to @{post.get('username')} | {post.get('_type')} | {comment[:60]}...")
            state["replied_to"].append(post["id"])
            state["daily_count"] += 1
            state["total_engagements"] = state.get("total_engagements", 0) + 1
            save_state(state)
            time.sleep(random.uniform(30, 90))  # 随机延迟
        else:
            logger.error(f"Failed to reply: {result}")

    logger.info(f"Done. Daily count: {state['daily_count']}/{DAILY_LIMIT}")


def check_effectiveness():
    """查看已回复帖子的效果"""
    state = load_state()
    print(f"Total engagements: {state.get('total_engagements', 0)}")
    print(f"Today's count: {state.get('daily_count', 0)}")
    print(f"Replied to {len(state.get('replied_to', []))} posts")


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Threads Community Engager")
    parser.add_argument("--dry-run", action="store_true", help="Search only, don't reply")
    parser.add_argument("--limit", type=int, default=None, help="Max replies this run")
    parser.add_argument("--check", action="store_true", help="Check effectiveness")
    args = parser.parse_args()

    if args.check:
        check_effectiveness()
    else:
        run_engager(dry_run=args.dry_run, limit=args.limit)
