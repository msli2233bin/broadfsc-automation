"""
Mastodon 社区深度互动机器人
============================
不急着引流。先在投资社区建立专业信誉，用有深度的分析参与讨论。

策略：
1. 搜索投资相关话题（#investing #stocks #NVDA #SP500等）
2. 筛选值得回复的帖子（提问型、分析型、讨论型）
3. AI生成有见地的评论（基于knowledge_fusion跨域知识）
4. 自然地参与讨论，不硬推CTA
5. 追踪互动效果

运行：
    python mastodon_engager.py              # 默认：搜索+回复最多5条
    python mastodon_engager.py --dry-run    # 只搜索不回复
    python mastodon_engager.py --limit 3    # 最多回复3条
"""

import os
import sys
import json
import time
import random
import re
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

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
MASTODON_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN", "")
MASTODON_INSTANCE = os.environ.get("MASTODON_INSTANCE", "mastodon.social")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# 追踪文件
STATE_FILE = Path(__file__).parent / ".bot_memory" / "mastodon_engagements.json"

# 搜索关键词（轮换，避免重复搜同一话题）
SEARCH_TAGS_POOL = [
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

# 最小互动标准：帖子必须有这些特征才值得回复
MIN_FAVORITES = 1       # 至少有人点赞（说明是真实讨论）
MIN_CONTENT_LENGTH = 60  # 至少60字符（不是一句话水帖）
SKIP_PATTERNS = [        # 跳过的帖子类型
    r"buy now|sell now|pump|dump|moon|to the moon",  # 喊单
    r"click here|sign up|follow me|subscribe",        # 硬广告
    r"giveaway|free money|airdrop",                    # 抽奖
    r"get funded|prop firm|prop trading|instant funding|evaluation.*funding|funded trader|funding.*code|discount.*code|off.*funding",  # prop firm促销
    r"use code|promo code|coupon|take \d+% off",      # 优惠码
    r"screen reader|accessibility|jaws|voiceover|talkback|narrator|html support",  # NVDA屏幕阅读器误匹配
]


# ============================================================
# 状态管理
# ============================================================
def load_state():
    """加载已回复的帖子记录"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {"replied_to": [], "daily_count": 0, "last_reset": "", "total_engagements": 0}


def save_state(state):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def reset_daily_count(state):
    """每天重置计数"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_reset") != today:
        state["daily_count"] = 0
        state["last_reset"] = today
    return state


# ============================================================
# Mastodon API
# ============================================================
def mastodon_request(method, path, **kwargs):
    """通用Mastodon API请求"""
    headers = {"Authorization": f"Bearer {MASTODON_TOKEN}"}
    url = f"https://{MASTODON_INSTANCE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, params=kwargs.get("params"), timeout=15)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=kwargs.get("json"), data=kwargs.get("data"), timeout=15)
        else:
            return None
        if r.status_code == 429:
            time.sleep(60)
            return mastodon_request(method, path, **kwargs)
        return r
    except Exception as e:
        logger.error(f"Mastodon API error: {e}")
        return None


def search_posts(query, limit=20):
    """搜索Mastodon帖子"""
    r = mastodon_request("GET", "/api/v2/search", params={"q": query, "type": "statuses", "limit": limit})
    if r and r.status_code == 200:
        return r.json().get("statuses", [])
    return []


def get_timeline_hashtag(tag, limit=20):
    """获取话题时间线"""
    r = mastodon_request("GET", f"/api/v1/timelines/tag/{tag}", params={"limit": limit})
    if r and r.status_code == 200:
        return r.json()
    return []


def reply_to_post(status_id, text, visibility="public"):
    """回复帖子"""
    r = mastodon_request("POST", f"/api/v1/statuses", json={
        "status": text,
        "in_reply_to_id": status_id,
        "visibility": visibility,
    })
    if r and r.status_code == 200:
        return r.json()
    return None


def get_post_context(status_id):
    """获取帖子上下文（用于确认是否已有互动）"""
    r = mastodon_request("GET", f"/api/v1/statuses/{status_id}/context")
    if r and r.status_code == 200:
        return r.json()
    return None


# ============================================================
# 帖子筛选
# ============================================================
def clean_html(html_text):
    """清理HTML标签"""
    text = re.sub(r'<br\s*/?>', '\n', html_text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    return text.strip()


def should_engage(post, state):
    """判断是否值得回复"""
    # 已回复过
    if post["id"] in state["replied_to"]:
        return False, "already_replied"
    
    content = clean_html(post.get("content", ""))
    
    # 内容太短
    if len(content) < MIN_CONTENT_LENGTH:
        return False, "too_short"
    
    # 硬广告/喊单
    content_lower = content.lower()
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, content_lower):
            return False, "spam_pattern"
    
    # 必须与投资/金融相关（排除纯科技/编程等无关帖子）
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
    has_finance = any(kw in content_lower for kw in FINANCE_REQUIRED)
    if not has_finance:
        return False, "not_finance_related"
    
    # 至少有点互动（排除纯机器人刷屏）
    favs = post.get("favourites_count", 0)
    reblogs = post.get("reblogs_count", 0)
    if favs + reblogs < MIN_FAVORITES:
        return False, "no_engagement"
    
    # 判断帖子类型，优先回复提问型和讨论型
    is_question = "?" in content or any(w in content_lower for w in [
        "how", "what", "why", "should i", "do you think", "anyone",
        "thoughts", "opinion", "help", "advice", "confused", "wonder",
    ])
    is_analysis = any(w in content_lower for w in [
        "rsi", "macd", "support", "resistance", "bollinger", "trend",
        "breakout", "pullback", "overbought", "oversold", "volume",
        "earnings", "revenue", "valuation", "pe ratio",
    ])
    is_discussion = any(w in content_lower for w in [
        "discuss", "debate", "interesting", "what's happening",
        "market", "sector", "strategy", "portfolio",
    ])
    
    if is_question:
        return True, "question"
    elif is_analysis:
        return True, "analysis"
    elif is_discussion:
        return True, "discussion"
    elif len(content) > 200:
        return True, "long_post"
    
    return False, "not_engaging"


# ============================================================
# AI 评论生成
# ============================================================
def generate_reply(post_content, post_author, lang="en"):
    """用Groq AI生成有见地的回复。
    
    核心原则：
    - 不硬推BroadFSC（除非自然相关）
    - 提供真实的技术面/基本面分析
    - 用对话语气，不是AI味儿
    - 尊重原作者观点，在此基础上补充
    """
    if not GROQ_API_KEY:
        return None
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # 跨域知识注入
        fusion_ctx = ""
        if HAS_FUSION:
            fusion_ctx = get_bot_prompt_injection(post_content)
        
        prompt = f"""You are a sharp, opinionated trader replying on Mastodon. Sound like someone who actually trades, not a textbook.

THE POST: @{post_author} wrote: {post_content}

KNOWLEDGE: {fusion_ctx if fusion_ctx else "Use your real market experience."}

RULES:
1. Address their SPECIFIC point - show you actually read their post
2. Drop ONE concrete number (RSI level, PE, % move, yield, volume)
3. Add ONE insight they missed - contrarian angle, second-order effect, or timing call
4. 2-3 sentences MAX - punchy, no padding. 200-450 chars.
5. BANNED openings: "Your post highlights", "Great question!", "Interesting take!", "I appreciate", "As [source] notes", "It's important to consider"
6. BANNED sources: Investopedia, Wikipedia, "many analysts"
7. Never mention BroadFSC or any service
8. Vary your style - don't repeat the same structure
9. Like texting a smart colleague, not writing a research report

BAD (generic, preachy): "Your post highlights the importance of risk management. As many analysts note, diversification is key to long-term success."
GOOD (specific, punchy): "Risk management matters, but the real edge is position sizing. 2% per trade with a 1:3 R:R means you can be wrong 60% of the time and still print."

BAD (textbook): "RSI is a momentum indicator that measures overbought and oversold conditions on a scale of 0 to 100."
GOOD (trader): "RSI at 28 but volume drying up on the sell - no climax selling, no real bottom. Wait for the volume spike."

BAD (obvious): "It's important to consider both bull and bear cases when evaluating the market."
GOOD (contrarian): "Everyone's calling a top. When everyone agrees on direction, the trade's already crowded. I'm watching the VIX - below 14 means complacency, and complacency kills."

Now reply:"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=200,
        )
        
        reply = response.choices[0].message.content.strip()
        
        # 清理可能的引号包裹
        if reply.startswith('"') and reply.endswith('"'):
            reply = reply[1:-1]
        
        # 确保不超500字符
        if len(reply) > 490:
            reply = reply[:487] + "..."
        
        return reply
        
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        return None


# ============================================================
# 主流程
# ============================================================
def find_engageable_posts(state, max_posts=30):
    """搜索并筛选值得回复的帖子"""
    candidates = []
    
    # 随机选2个搜索词（不同角度）
    search_terms = random.sample(SEARCH_TAGS_POOL, min(3, len(SEARCH_TAGS_POOL)))
    
    for term in search_terms:
        # 先尝试话题时间线
        if term.startswith("#"):
            tag = term[1:]
            posts = get_timeline_hashtag(tag, limit=10)
        else:
            posts = search_posts(term, limit=10)
        
        logger.info(f"Searched '{term}': {len(posts)} posts")
        
        for post in posts:
            engage, reason = should_engage(post, state)
            if engage:
                author = post.get("account", {})
                candidates.append({
                    "id": post["id"],
                    "author": author.get("username", "unknown"),
                    "author_display": author.get("display_name", ""),
                    "content": clean_html(post.get("content", "")),
                    "reason": reason,
                    "url": post.get("url", ""),
                    "created_at": post.get("created_at", ""),
                    "favourites_count": post.get("favourites_count", 0),
                    "reblogs_count": post.get("reblogs_count", 0),
                    "replies_count": post.get("replies_count", 0),
                })
            elif reason not in ("already_replied", "no_engagement"):
                pass  # silently skip spam/too-short
        
        # 够了就停（多搜一些，给热度排序留选择空间）
        if len(candidates) >= 10:
            break
    
    # 去重（可能多个搜索词搜到同一帖子）
    seen = set()
    unique = []
    for c in candidates:
        if c["id"] not in seen:
            seen.add(c["id"])
            unique.append(c)
    
    return unique


def run_engagement(dry_run=False, max_replies=DAILY_LIMIT):
    """主运行函数"""
    if not MASTODON_TOKEN:
        logger.error("MASTODON_ACCESS_TOKEN not set!")
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
    logger.info(f"Found {len(candidates)} engageable posts (from 3 searches)")
    
    if not candidates:
        logger.info("No suitable posts found. Try again later.")
        return
    
    # 按热度排序：热帖优先回复，曝光量最大化
    # 热度分 = 点赞*1 + 转发*3 + 回复*2（回复和转发权重高，说明是深度讨论）
    for post in candidates:
        favs = post.get("favourites_count", 0)
        reblogs = post.get("reblogs_count", 0)
        replies = post.get("replies_count", 0)
        post["heat_score"] = favs * 1 + reblogs * 3 + replies * 2
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
            logger.warning("  AI generation failed, skipping")
            continue
        
        logger.info(f"Reply: {reply}")
        
        if dry_run:
            logger.info(f"  [DRY RUN] Would reply to {post['id']}")
            continue
        
        # 发送回复
        result = reply_to_post(post["id"], reply)
        if result:
            logger.info(f"  ✅ Replied! ID: {result.get('id')}")
            state["replied_to"].append(post["id"])
            state["daily_count"] += 1
            state["total_engagements"] = state.get("total_engagements", 0) + 1
            engaged += 1
            
            # 保存每条回复记录
            engagement_record = {
                "date": datetime.now(timezone.utc).isoformat(),
                "post_id": post["id"],
                "author": post["author"],
                "my_reply_id": result.get("id"),
                "post_preview": post["content"][:100],
                "reply_preview": reply[:100],
            }
            if "engagements" not in state:
                state["engagements"] = []
            state["engagements"].append(engagement_record)
            save_state(state)   # <-- 每次发帖后立即保存
            
            # 间隔30-120秒，模拟人类行为
            delay = random.randint(30, 120)
            logger.info(f"  Waiting {delay}s before next...")
            time.sleep(delay)
        else:
            logger.error(f"  ❌ Failed to reply")
    
    # 保存状态
    save_state(state)
    logger.info(f"\nDone. Engaged: {engaged}. Total today: {state['daily_count']}/{max_replies}")
    
    return engaged


# ============================================================
# 互动效果追踪
# ============================================================
def check_reply_outcomes():
    """回查之前的评论有没有被回复/点赞/关注。
    这才是真正的"成功"指标——对方理你了吗？
    """
    state = load_state()
    engagements = state.get("engagements", [])
    if not engagements:
        logger.info("No past engagements to check.")
        return
    
    outcomes = {"replied": 0, "favorited": 0, "reblogged": 0, "followed": 0, "silent": 0}
    updated = []
    
    for eng in engagements[-20:]:  # 最近20条
        if eng.get("outcome_checked"):
            updated.append(eng)
            continue
        
        reply_id = eng.get("my_reply_id")
        post_id = eng.get("post_id")
        if not reply_id:
            continue
        
        # 检查我们的回复被谁互动了
        r = mastodon_request("GET", f"/api/v1/statuses/{reply_id}")
        if r and r.status_code == 200:
            data = r.json()
            favs = data.get("favourites_count", 0)
            reblogs = data.get("reblogs_count", 0)
            replies = data.get("replies_count", 0)
            
            eng["outcome"] = {
                "favorites": favs,
                "reblogs": reblogs,
                "replies": replies,
            }
            
            if replies > 0:
                outcomes["replied"] += 1
                eng["result"] = "replied"
            elif favs > 0:
                outcomes["favorited"] += 1
                eng["result"] = "favorited"
            elif reblogs > 0:
                outcomes["reblogged"] += 1
                eng["result"] = "reblogged"
            else:
                outcomes["silent"] += 1
                eng["result"] = "silent"
            
            eng["outcome_checked"] = datetime.now(timezone.utc).isoformat()
        
        updated.append(eng)
    
    # 回写
    state["engagements"] = updated + engagements[20:]
    save_state(state)
    
    total = sum(outcomes.values())
    logger.info(f"\n📊 Engagement Outcomes (last {total} checked):")
    logger.info(f"  💬 Got replies: {outcomes['replied']}")
    logger.info(f"  ⭐ Got favorites: {outcomes['favorited']}")
    logger.info(f"  🔄 Got reblogs: {outcomes['reblogged']}")
    logger.info(f"  🔇 Silent: {outcomes['silent']}")
    
    if total > 0:
        engagement_rate = (total - outcomes['silent']) / total * 100
        logger.info(f"  📈 Engagement rate: {engagement_rate:.0f}%")
    
    return outcomes


def extract_success_patterns():
    """从成功互动中提取模式：什么样的回复能引起对方回应？
    
    输出到 knowledge/patterns/ 供后续使用。
    """
    state = load_state()
    engagements = state.get("engagements", [])
    
    # 分组：有回复的 vs 沉默的
    successful = [e for e in engagements if e.get("result") in ("replied", "reblogged")]
    failed = [e for e in engagements if e.get("result") == "silent"]
    
    if not successful:
        return "还没有成功的互动数据。"
    
    patterns = []
    patterns.append(f"## Mastodon 互动模式总结\n")
    patterns.append(f"*生成时间: {datetime.now(timezone.utc).isoformat()}*\n")
    patterns.append(f"*总互动: {len(engagements)} | 成功: {len(successful)} | 沉默: {len(failed)}*\n")
    
    # 分析1：帖子类型成功率
    type_success = {}
    for e in engagements:
        reason = e.get("reason", "unknown")
        if reason not in type_success:
            type_success[reason] = {"success": 0, "total": 0}
        type_success[reason]["total"] += 1
        if e.get("result") in ("replied", "reblogged"):
            type_success[reason]["success"] += 1
    
    patterns.append("### 帖子类型分析\n")
    for reason, data in sorted(type_success.items(), key=lambda x: -x[1]["total"]):
        rate = data["success"] / data["total"] * 100 if data["total"] > 0 else 0
        patterns.append(f"- **{reason}**: {data['success']}/{data['total']} 成功 ({rate:.0f}%)")
    
    # 分析2：成功回复的共同特征
    patterns.append("\n### 成功回复的共同特征\n")
    for e in successful[:5]:
        patterns.append(f"- @{e.get('author', '?')}: \"{e.get('reply_preview', '')[:80]}...\" → {e.get('result')}")
    
    # 分析3：策略建议
    patterns.append(f"\n### 策略建议\n")
    if successful:
        patterns.append(f"- 当前成功率: {len(successful)/(len(engagements) or 1)*100:.0f}%")
        
        # 哪种帖子类型最有效
        best_type = max(type_success.items(), key=lambda x: x[1]["success"]/(x[1]["total"] or 1))
        patterns.append(f"- 最佳回复类型: **{best_type[0]}** — 优先选择这类帖子")
    
    patterns.append(f"- 有回复的互动 → 标记为 'hot lead'，后续可主动跟进")
    patterns.append(f"- 沉默的互动 → 不重复回复同一个人")
    
    report = "\n".join(patterns)
    
    # 保存到 patterns 目录
    patterns_dir = Path(__file__).parent / "knowledge" / "patterns"
    patterns_dir.mkdir(parents=True, exist_ok=True)
    (patterns_dir / "mastodon_engagement_patterns.md").write_text(report, encoding='utf-8')
    
    return report


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mastodon Community Engager")
    parser.add_argument("--dry-run", action="store_true", help="Search but don't reply")
    parser.add_argument("--limit", type=int, default=DAILY_LIMIT, help=f"Max replies per run (default: {DAILY_LIMIT})")
    parser.add_argument("--test-reply", type=str, help="Test AI reply generation with a post")
    parser.add_argument("--check", action="store_true", help="Check outcomes of past replies")
    parser.add_argument("--analyze", action="store_true", help="Extract success patterns from history")
    args = parser.parse_args()
    
    if args.test_reply:
        reply = generate_reply(args.test_reply, "test_user")
        print(f"\n📝 Original post:\n{args.test_reply}\n")
        print(f"💬 AI Reply:\n{reply}\n")
        sys.exit(0)
    
    if args.check:
        print("🔍 Checking past engagement outcomes...\n")
        check_reply_outcomes()
        sys.exit(0)
    
    if args.analyze:
        print("📊 Analyzing engagement patterns...\n")
        report = extract_success_patterns()
        print(report)
        print("\n✅ 模式已保存到 knowledge/patterns/mastodon_engagement_patterns.md")
        sys.exit(0)
    
    if args.dry_run:
        print("🔍 DRY RUN — searching only, no replies will be posted\n")
    
    run_engagement(dry_run=args.dry_run, max_replies=args.limit)
