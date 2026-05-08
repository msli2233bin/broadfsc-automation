"""
Bluesky 社区深度互动机器人
===========================
与 Mastodon 互动机器人同策略：先交朋友，再引流。

策略：
1. 搜索投资相关话题（#investing #stocks #NVDA #SP500等）
2. 筛选值得回复的帖子（提问型、分析型、讨论型）
3. AI生成有见地的评论（基于knowledge_fusion跨域知识）
4. 按热度排序，热帖优先回复（曝光最大化）
5. 追踪互动效果，提取成功模式

运行：
    python bluesky_engager.py              # 默认：搜索+回复最多8条
    python bluesky_engager.py --dry-run    # 只搜索不回复
    python bluesky_engager.py --limit 3    # 最多回复3条
    python bluesky_engager.py --check      # 回查之前评论效果
    python bluesky_engager.py --analyze    # 分析成功/失败模式
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

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Bluesky SDK
from atproto import Client, models

# Groq for AI generation
from groq import Groq

# 跨域知识
try:
    from knowledge_fusion import get_bot_prompt_injection
    HAS_FUSION = True
except ImportError:
    HAS_FUSION = False
    def get_bot_prompt_injection(q):
        return ""

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# 追踪文件
STATE_FILE = Path(__file__).parent / ".bot_memory" / "bluesky_engagements.json"

# 搜索关键词（轮换，避免重复搜同一话题）
SEARCH_TERMS_POOL = [
    "#investing",
    "#stocks",
    "#stockmarket",
    "$NVDA",
    "Nvidia stock",
    "#SP500",
    "#technicalanalysis",
    "#trading",
    "#forex",
    "#crypto",
    "#bitcoin",
    "gold price",
    "BTC analysis",
    "AAPL stock",
    "TSLA stock",
    "MSFT stock",
    "market correction",
    "RSI oversold",
    "earnings report",
    "Fed rate",
    "inflation data",
    "recession risk",
    "stock rally",
    "bear market",
    "bull market",
]

# 每日回复上限
DAILY_LIMIT = 8

# 最小互动标准
MIN_CONTENT_LENGTH = 60
SKIP_PATTERNS = [
    r"buy now|sell now|pump|dump|moon|to the moon",
    r"click here|sign up|follow me|subscribe",
    r"giveaway|free money|airdrop",
    r"get funded|prop firm|prop trading|instant funding|evaluation.*funding|funded trader|funding.*code|discount.*code|off.*funding",
    r"use code|promo code|coupon|take \d+% off",
    r"screen reader|accessibility|jaws|voiceover|talkback|narrator|html support",
]

# 投资主题必需关键词
FINANCE_REQUIRED = [
    "stock", "invest", "trad", "portfolio", "market", "etf", "bond",
    "dividend", "earning", "revenue", "valuation", "bull", "bear",
    "sector", "index", "s&p", "nasdaq", "dow", "fed", "rate",
    "inflation", "gdp", "recession", "correction", "rally", "ipo",
    "option", "future", "forex", "crypto", "bitcoin", "commodity",
    "hedge", "alpha", "beta", "yield", "margin", "leverage",
    "p/e", "pe ratio", "rsi", "macd", "support", "resistance",
    "breakout", "pullback", "overbought", "oversold", "volume",
    "financial", "fiscal", "monetary", "quantitative",
    "$aapl", "$tsla", "$nvda", "$msft", "$amzn", "$googl", "$meta",
    "ticker", "share", "shareholder", "buyback", "split",
]


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
# Bluesky 客户端
# ============================================================
_client = None

def get_client():
    """获取已登录的Bluesky客户端"""
    global _client
    if _client is not None:
        return _client
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        logger.error("BLUESKY_HANDLE or BLUESKY_APP_PASSWORD not set!")
        return None
    _client = Client()
    profile = _client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
    logger.info(f"Logged in as {profile.display_name} (@{profile.handle})")
    return _client


# ============================================================
# 搜索与筛选
# ============================================================
def search_posts(query, limit=25):
    """搜索Bluesky帖子"""
    client = get_client()
    if not client:
        return []
    try:
        results = client.app.bsky.feed.search_posts(
            models.AppBskyFeedSearchPosts.Params(q=query, limit=limit)
        )
        return results.posts
    except Exception as e:
        logger.error(f"Search error for '{query}': {e}")
        return []


def should_engage(post, state):
    """判断是否值得回复"""
    # 跳过自己的帖子
    author_handle = post.author.handle if post.author else ""
    if author_handle.lower() == BLUESKY_HANDLE.lower().replace("@", ""):
        return False, "own_post"

    # 已回复过
    post_uri = str(post.uri)
    if post_uri in state["replied_to"]:
        return False, "already_replied"

    # 获取文本内容
    text = ""
    if hasattr(post, 'record') and hasattr(post.record, 'text'):
        text = post.record.text or ""

    # 内容太短
    if len(text) < MIN_CONTENT_LENGTH:
        return False, "too_short"

    # 硬广告/喊单
    text_lower = text.lower()
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text_lower):
            return False, "spam_pattern"

    # 必须与投资/金融相关
    has_finance = any(kw in text_lower for kw in FINANCE_REQUIRED)
    if not has_finance:
        return False, "not_finance_related"

    # 判断帖子类型
    is_question = "?" in text or any(w in text_lower for w in [
        "how", "what", "why", "should i", "do you think", "anyone",
        "thoughts", "opinion", "help", "advice", "confused", "wonder",
    ])
    is_analysis = any(w in text_lower for w in [
        "rsi", "macd", "support", "resistance", "bollinger", "trend",
        "breakout", "pullback", "overbought", "oversold", "volume",
        "earnings", "revenue", "valuation", "pe ratio",
    ])
    is_discussion = any(w in text_lower for w in [
        "discuss", "debate", "interesting", "what's happening",
        "market", "sector", "strategy", "portfolio",
    ])

    if is_question:
        return True, "question"
    elif is_analysis:
        return True, "analysis"
    elif is_discussion:
        return True, "discussion"
    elif len(text) > 200:
        return True, "long_post"

    return False, "not_engaging"


def find_engageable_posts(state, max_posts=30):
    """搜索并筛选可回复的帖子"""
    # 随机选3个搜索词
    terms = random.sample(SEARCH_TERMS_POOL, min(3, len(SEARCH_TERMS_POOL)))
    candidates = []

    for term in terms:
        posts = search_posts(term, limit=25)
        logger.info(f"Searched '{term}': {len(posts)} posts")

        for post in posts:
            engage, reason = should_engage(post, state)
            if engage:
                author_handle = post.author.handle if post.author else "unknown"
                author_name = post.author.display_name if post.author else ""
                text = post.record.text if hasattr(post, 'record') and hasattr(post.record, 'text') else ""

                # 获取互动数据
                like_count = post.like_count if hasattr(post, 'like_count') else 0
                repost_count = post.repost_count if hasattr(post, 'repost_count') else 0
                reply_count = post.reply_count if hasattr(post, 'reply_count') else 0

                candidates.append({
                    "uri": str(post.uri),
                    "cid": str(post.cid),
                    "author": author_handle,
                    "author_display": author_name,
                    "content": text,
                    "reason": reason,
                    "like_count": like_count,
                    "repost_count": repost_count,
                    "reply_count": reply_count,
                    "indexed_at": str(post.indexed_at) if hasattr(post, 'indexed_at') else "",
                })

        if len(candidates) >= 10:
            break

    # 去重
    seen = set()
    unique = []
    for c in candidates:
        if c["uri"] not in seen:
            seen.add(c["uri"])
            unique.append(c)

    return unique


# ============================================================
# AI 评论生成
# ============================================================
def generate_reply(post_content, post_author, lang="en"):
    """用Groq AI生成有见地的回复"""
    if not GROQ_API_KEY:
        return None

    # 注入知识
    fusion_ctx = get_bot_prompt_injection("investment analysis market") if HAS_FUSION else ""

    prompt = f"""You are a sharp, opinionated trader replying on Bluesky. Sound like someone who actually trades, not a textbook.
THE POST: @{post_author} wrote: {post_content}
KNOWLEDGE: {fusion_ctx}

RULES:
1. Address their SPECIFIC point - show you actually read their post
2. Drop ONE concrete number (RSI level, PE, % move, yield, volume)
3. Add ONE insight they missed - contrarian angle, second-order effect, or timing call
4. 2-3 sentences MAX - punchy, no padding
5. BANNED openings: "Your post highlights", "Great question!", "@handle", "I appreciate", "Interesting", "As [source] notes"
6. BANNED sources: Investopedia, Wikipedia, "many analysts"
7. Never mention BroadFSC or any service
8. Vary your style - don't repeat the same structure

BAD (generic, preachy): "Your post highlights the diversity of trading strategies. As Investopedia notes, technical analysis focuses on..."
GOOD (specific, punchy): "Every 'combine both approaches' take misses the point. High vol = technicals win. Low vol = fundamentals. Know your regime."

BAD (textbook): "RSI is a momentum indicator that measures overbought and oversold conditions..."
GOOD (trader): "RSI 28 but volume drying up on the sell - no climax selling, no real bottom. Wait for the spike."

BAD (obvious): "It's important to consider both bull and bear cases when evaluating a stock."
GOOD (contrarian): "35x PE prices in 15% growth but they guided 8%. Either the street knows something, or this is a $40 stock at $60."

Now reply:"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.8,
        )
        reply = response.choices[0].message.content.strip()
        # 清理
        reply = re.sub(r'^["\']|["\']$', '', reply)
        if len(reply) > 300:
            reply = reply[:297] + "..."
        return reply
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return None


# ============================================================
# 发帖与互动
# ============================================================
def reply_to_post(post_uri, post_cid, reply_text):
    """回复一条Bluesky帖子"""
    client = get_client()
    if not client:
        return None
    try:
        # 构建回复引用
        reply_ref = models.AppBskyFeedPost.ReplyRef(
            parent=models.ComAtprotoRepoStrongRef.Main(uri=post_uri, cid=post_cid),
            root=models.ComAtprotoRepoStrongRef.Main(uri=post_uri, cid=post_cid),
        )
        result = client.send_post(reply_text, reply_to=reply_ref)
        logger.info(f"  Reply posted: {result.uri}")
        return {"uri": str(result.uri), "cid": str(result.cid)}
    except Exception as e:
        logger.error(f"  Reply error: {e}")
        return None


def run_engagement(dry_run=False, max_replies=DAILY_LIMIT):
    """主运行函数"""
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        logger.error("BLUESKY_HANDLE or BLUESKY_APP_PASSWORD not set!")
        return

    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — will skip AI generation")

    state = load_state()
    state = reset_daily_count(state)

    remaining = max_replies - state["daily_count"]
    if remaining <= 0:
        logger.info(f"Daily limit reached ({state['daily_count']}/{max_replies}). Skipping.")
        return

    logger.info(f"Daily quota: {state['daily_count']}/{max_replies} used. Looking for {remaining} posts...")

    # 找到可回复的帖子
    candidates = find_engageable_posts(state, max_posts=30)
    logger.info(f"Found {len(candidates)} engageable posts")

    if not candidates:
        logger.info("No suitable posts found. Try again later.")
        return

    # 按热度排序：热帖优先回复
    for post in candidates:
        likes = post.get("like_count", 0)
        reposts = post.get("repost_count", 0)
        replies = post.get("reply_count", 0)
        post["heat_score"] = likes * 1 + reposts * 3 + replies * 2
    candidates.sort(key=lambda p: p["heat_score"], reverse=True)
    logger.info(f"Heat scores: {[(c['author'], c['heat_score']) for c in candidates[:5]]}")

    engaged = 0
    for post in candidates[:remaining]:
        logger.info(f"\n--- Engaging with @{post['author']} ---")
        logger.info(f"Post: {post['content'][:150]}...")
        logger.info(f"Reason: {post['reason']}")

        # AI生成回复
        reply = generate_reply(post["content"], post["author"])
        if not reply:
            logger.warning("  Skipping — no AI reply generated")
            continue

        logger.info(f"Reply: {reply}")

        if dry_run:
            logger.info(f"  [DRY RUN] Would reply to {post['uri']}")
            continue

        # 发送回复
        result = reply_to_post(post["uri"], post["cid"], reply)
        if result:
            logger.info(f"  ✅ Replied! URI: {result['uri']}")
            state["replied_to"].append(post["uri"])
            state["daily_count"] += 1
            state["total_engagements"] = state.get("total_engagements", 0) + 1
            engaged += 1

            # 保存记录
            engagement_record = {
                "date": datetime.now(timezone.utc).isoformat(),
                "post_uri": post["uri"],
                "author": post["author"],
                "my_reply_uri": result["uri"],
                "post_preview": post["content"][:100],
                "reply_preview": reply[:100],
                "heat_score": post.get("heat_score", 0),
            }
            if "engagements" not in state:
                state["engagements"] = []
            state["engagements"].append(engagement_record)
            save_state(state)  # 每次发帖后立即保存

            # 间隔30-120秒
            delay = random.randint(30, 120)
            logger.info(f"  Waiting {delay}s before next...")
            time.sleep(delay)
        else:
            logger.error(f"  ❌ Failed to reply")

    # 最终保存
    save_state(state)
    logger.info(f"\nDone. Engaged: {engaged}. Total today: {state['daily_count']}/{max_replies}")

    return engaged


# ============================================================
# 互动效果追踪
# ============================================================
def check_reply_outcomes():
    """回查之前的评论有没有被回复/点赞/关注"""
    client = get_client()
    if not client:
        return

    state = load_state()
    engagements = state.get("engagements", [])
    if not engagements:
        logger.info("No past engagements to check.")
        return

    logger.info(f"Checking outcomes for {len(engagements)} past engagements...")

    updated = []
    for eng in engagements[-20:]:
        reply_uri = eng.get("my_reply_uri", "")
        if not reply_uri:
            continue
        try:
            # 获取我们回复的帖子线程
            thread = client.get_post_thread(reply_uri)
            if hasattr(thread, 'thread') and hasattr(thread.thread, 'post'):
                post_data = thread.thread.post
                likes = post_data.like_count if hasattr(post_data, 'like_count') else 0
                reposts = post_data.repost_count if hasattr(post_data, 'repost_count') else 0
                replies = post_data.reply_count if hasattr(post_data, 'reply_count') else 0

                eng["checked_likes"] = likes
                eng["checked_reposts"] = reposts
                eng["checked_replies"] = replies
                eng["last_checked"] = datetime.now(timezone.utc).isoformat()

                # 判断结果
                if replies > 0:
                    eng["result"] = "replied"
                    logger.info(f"  🔥 HOT LEAD! @{eng['author']} replied to us! (❤{likes} 🔁{reposts} 💬{replies})")
                elif likes > 0 or reposts > 0:
                    eng["result"] = "noticed"
                    logger.info(f"  👀 Noticed by @{eng['author']} (❤{likes} 🔁{reposts})")
                else:
                    eng["result"] = "silent"
                    logger.info(f"  😐 Silent from @{eng['author']}")
            updated.append(eng)
            time.sleep(1)  # Rate limit
        except Exception as e:
            logger.error(f"  Error checking {reply_uri}: {e}")
            updated.append(eng)

    state["engagements"] = updated + engagements[20:]
    save_state(state)


# ============================================================
# 成功模式分析
# ============================================================
def extract_success_patterns():
    """分析什么类型的帖子回复成功率最高"""
    state = load_state()
    engagements = state.get("engagements", [])
    if len(engagements) < 3:
        logger.info("Not enough data for pattern extraction (need 3+).")
        return

    patterns = []
    successful = [e for e in engagements if e.get("result") in ("replied", "noticed")]
    failed = [e for e in engagements if e.get("result") == "silent"]

    patterns.append(f"*总互动: {len(engagements)} | 成功: {len(successful)} | 沉默: {len(failed)}*\n")

    # 按帖子类型统计
    type_success = {}
    for e in engagements:
        reason = e.get("reason", "unknown")
        if reason not in type_success:
            type_success[reason] = {"total": 0, "success": 0}
        type_success[reason]["total"] += 1
        if e.get("result") in ("replied", "noticed"):
            type_success[reason]["success"] += 1

    patterns.append("**帖子类型成功率:**")
    for reason, data in sorted(type_success.items(), key=lambda x: -x[1]["total"]):
        rate = data["success"] / data["total"] * 100 if data["total"] else 0
        patterns.append(f"- {reason}: {data['success']}/{data['total']} ({rate:.0f}%)")

    patterns.append(f"\n- 当前成功率: {len(successful)/(len(engagements) or 1)*100:.0f}%")

    # 保存模式报告
    patterns_dir = Path(__file__).parent / "knowledge" / "patterns"
    patterns_dir.mkdir(parents=True, exist_ok=True)
    report_file = patterns_dir / f"bluesky_patterns_{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
    report_file.write_text("\n".join(patterns), encoding='utf-8')
    logger.info(f"Pattern report saved to {report_file}")
    logger.info("\n".join(patterns))


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bluesky 社区互动机器人")
    parser.add_argument("--dry-run", action="store_true", help="只搜索不回复")
    parser.add_argument("--limit", type=int, default=DAILY_LIMIT, help="最大回复数")
    parser.add_argument("--test-reply", type=str, help="测试AI回复生成")
    parser.add_argument("--check", action="store_true", help="回查互动效果")
    parser.add_argument("--analyze", action="store_true", help="分析成功模式")
    args = parser.parse_args()

    if args.test_reply:
        reply = generate_reply(args.test_reply, "test_user")
        print(f"Generated reply: {reply}")
    elif args.check:
        check_reply_outcomes()
    elif args.analyze:
        extract_success_patterns()
    else:
        engaged = run_engagement(dry_run=args.dry_run, max_replies=args.limit)
        if args.dry_run:
            print("🔍 DRY RUN — searching only, no replies will be posted")
