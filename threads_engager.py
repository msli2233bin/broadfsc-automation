"""
Threads 社区评论机器人（v2）
==================
策略：监控对本账号的提及+回复，进行互动。

Threads API 限制：
- 不支持 hashtag 搜索
- 支持：获取 mentions、获取自己帖子的回复、发布回复
- API: https://graph.threads.net/v1.0

运行：
    python threads_engager.py              # 默认：处理mentions+回复，最多回复5条
    python threads_engager.py --dry-run    # 只查看不回复
    python threads_engager.py --limit 3    # 最多回复3条
    python threads_engager.py --check      # 查看已回复
"""
import os
import sys
import json
import time
import random
import re
import logging
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
STATE_FILE = Path(__file__).parent / ".bot_memory" / "threads_engagements.json"

DAILY_LIMIT = 5

SKIP_PATTERNS = [
    r"buy now|sell now|pump|to the moon",
    r"click here|sign up|follow me|dm me",
    r"giveaway|free money|airdrop",
]

FINANCE_KEYWORDS = [
    "stock", "invest", "trad", "portfolio", "market", "etf",
    "rsi", "macd", "support", "resistance", "breakout",
    "$aapl", "$tsla", "$nvda", "$msft",
    "earnings", "fed", "inflation", "recession",
]


# ============================================================
# API 封装
# ============================================================
def threads_get(endpoint, params=None):
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


def get_mentions(limit=25):
    """获取提及本账号的帖子"""
    result = threads_get(f"{THREADS_USER_ID}/mentions", {
        "fields": "id,caption,username,timestamp,permalink,like_count,replies_count",
        "limit": limit,
    })
    return result.get("data", []) if result else []


def get_my_threads(limit=25):
    """获取我发的帖子（用于检查有哪些回复）"""
    result = threads_get(f"{THREADS_USER_ID}/threads", {
        "fields": "id,caption,username,timestamp,permalink,like_count,replies_count",
        "limit": limit,
    })
    return result.get("data", []) if result else []


def get_thread_replies(thread_id):
    """获取某条帖子下的回复"""
    result = threads_get(f"{thread_id}/replies", {
        "fields": "id,caption,username,timestamp,like_count",
        "limit": 50,
    })
    return result.get("data", []) if result else []


def reply_to_post(media_id, text):
    """回复一条Threads帖子"""
    return threads_post(f"{media_id}/replies", {"text": text})


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
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_reset") != today:
        state["daily_count"] = 0
        state["last_reset"] = today
    return state


# ============================================================
# 内容筛选
# ============================================================
def should_engage(post_or_reply, state):
    item_id = post_or_reply.get("id", "")
    caption = post_or_reply.get("caption", "") or ""
    username = post_or_reply.get("username", "")

    if item_id in state["replied_to"]:
        return False, "already_replied"
    if len(caption) < 30:
        return False, "too_short"
    text_lower = caption.lower()
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text_lower):
            return False, "spam"
    has_finance = any(kw in text_lower for kw in FINANCE_KEYWORDS)
    if not has_finance:
        return False, "not_finance"
    return True, "ok"


# ============================================================
# AI 生成评论
# ============================================================
def generate_comment(post_caption, groq_client):
    if not groq_client:
        return "Interesting point. The technical setup here suggests watching the key support level closely. Volume confirmation will be critical."

    prompt = f"""You are a seasoned financial analyst replying to a social media comment.

RULES:
- Write a thoughtful reply (150-280 chars)
- Add 1 specific technical or fundamental insight
- No emojis, no self-introduction, no pitching
- Sound like a real person

Original comment: {post_caption[:300]}

Your reply:"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.8,
        )
        comment = resp.choices[0].message.content.strip()
        comment = re.sub(r'^["\']+|["\']+$', '', comment)
        return comment[:500]
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None


# ============================================================
# 主逻辑
# ============================================================
def run_engager(dry_run=False, limit=None):
    if not THREADS_ACCESS_TOKEN:
        logger.error("THREADS_ACCESS_TOKEN not set!")
        return

    state = load_state()
    state = reset_daily_count(state)

    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

    # 收集候选：mentions + 自己帖子的回复
    candidates = []

    # 1. 提及
    mentions = get_mentions(limit=20)
    logger.info(f"Found {len(mentions)} mentions")
    for m in mentions:
        ok, reason = should_engage(m, state)
        if ok:
            m["_source"] = "mention"
            candidates.append(m)

    # 2. 自己帖子的回复
    my_threads = get_my_threads(limit=10)
    for thread in my_threads:
        replies = get_thread_replies(thread["id"])
        logger.info(f"Thread {thread['id'][:8]}: {len(replies)} replies")
        for r in replies:
            ok, reason = should_engage(r, state)
            if ok:
                r["_source"] = "reply_to_my_post"
                candidates.append(r)
        time.sleep(1)

    if not candidates:
        logger.info("No suitable items to engage with.")
        return

    to_reply = candidates[:limit or DAILY_LIMIT]
    logger.info(f"Replying to {len(to_reply)} items...")

    for item in to_reply:
        if state["daily_count"] >= DAILY_LIMIT:
            break
        if dry_run:
            print(f"[DRY-RUN] Would reply to {item.get('username')}: {item.get('caption','')[:60]}...")
            continue

        comment = generate_comment(item.get("caption", ""), groq_client)
        if not comment:
            continue

        result = reply_to_post(item["id"], comment)
        if result and "id" in result:
            logger.info(f"✓ Replied to {item.get('username')} via {item.get('_source')}")
            state["replied_to"].append(item["id"])
            state["daily_count"] += 1
            state["total_engagements"] = state.get("total_engagements", 0) + 1
            save_state(state)
            time.sleep(random.uniform(30, 90))
        else:
            logger.error(f"Failed to reply: {result}")

    logger.info(f"Done. Daily: {state['daily_count']}/{DAILY_LIMIT}")


def check_status():
    state = load_state()
    print(f"Total engagements: {state.get('total_engagements', 0)}")
    print(f"Today's count: {state.get('daily_count', 0)}")
    print(f"Replied to {len(state.get('replied_to', []))} items total")


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        check_status()
    else:
        run_engager(dry_run=args.dry_run, limit=args.limit)
