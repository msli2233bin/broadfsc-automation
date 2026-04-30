"""
BroadFSC Content Repurposer — 一鱼多吃，内容最大化

核心理念：
1. 从知识库 + 实时数据 → 生成一篇高质量核心内容（"母内容"）
2. 从母内容自动拆分为各平台适配版本（Telegram/Discord/X/Mastodon/Bluesky/Threads/Substack）
3. 内容丰富、有深度、有吸引力，不是模板化的废话

运行方式：
  python content_repurposer.py              # 完整流程：生成+发布
  python content_repurposer.py --generate   # 只生成，不发布（预览）
  python content_repurposer.py --platform telegram discord  # 只发布指定平台
"""

import os
import sys
import datetime
import requests
import json
import random
from pathlib import Path

# Analytics tracking
try:
    from analytics_logger import log_post
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "")
MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN", "")
MASTODON_INSTANCE = os.environ.get("MASTODON_INSTANCE", "mastodon.social")
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SUBSTACK_LINK = os.environ.get("SUBSTACK_LINK", "https://broadcastmarketintelligence.substack.com")

# Fallback from .env
if not GROQ_API_KEY or not BOT_TOKEN:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _env_path = os.path.join(_script_dir, ".env")
    if os.path.exists(_env_path):
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if key == "GROQ_API_KEY" and not GROQ_API_KEY:
                    GROQ_API_KEY = val
                elif key == "TELEGRAM_BOT_TOKEN" and not BOT_TOKEN:
                    BOT_TOKEN = val
                elif key == "THREADS_ACCESS_TOKEN" and not THREADS_ACCESS_TOKEN:
                    THREADS_ACCESS_TOKEN = val
                elif key == "THREADS_USER_ID" and not THREADS_USER_ID:
                    THREADS_USER_ID = val

KNOWLEDGE_DIR = Path(__file__).parent / 'knowledge'
CONTENT_QUEUE_DIR = KNOWLEDGE_DIR / 'content_queue'

DISCLAIMER = "\n\n<i>Risk Disclaimer: Investment involves risk. Consult a licensed advisor.</i>"

# ============================================================
# 知识库素材聚合 — 从各子目录读取最丰富的内容
# ============================================================
def gather_knowledge():
    """从知识库读取所有素材，按新鲜度排序，返回合并后的上下文"""
    sources = []
    now = datetime.datetime.utcnow()

    # 遍历所有知识子目录
    for subdir in ['finance', 'sales', 'marketing', 'competitor']:
        dir_path = KNOWLEDGE_DIR / subdir
        if not dir_path.exists():
            continue
        for md_file in sorted(dir_path.glob("*.md"), reverse=True)[:5]:
            try:
                content = md_file.read_text(encoding='utf-8')
                # 提取最有价值的部分（跳过元数据）
                lines = content.split('\n')
                useful = [l for l in lines if l.strip() and not l.startswith('#') and len(l.strip()) > 20]
                if useful:
                    sources.append({
                        'file': md_file.name,
                        'category': subdir,
                        'highlights': useful[:15],  # 每个文件取最相关的15行
                    })
            except Exception:
                continue

    # 也读取市场参考数据
    market_ref = KNOWLEDGE_DIR / 'finance' / 'market_reference_2026_04.md'
    market_data = ""
    if market_ref.exists():
        try:
            market_data = market_ref.read_text(encoding='utf-8')
        except Exception:
            pass

    return sources, market_data


def fetch_realtime_data():
    """用 yfinance 获取实时市场快照，增加内容的数据密度"""
    try:
        import yfinance as yf
    except ImportError:
        return ""

    snapshots = []
    tickers = {
        "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow": "^DJI",
        "Gold": "GC=F", "Oil": "CL=F", "Bitcoin": "BTC-USD",
        "10Y Yield": "^TNX", "VIX": "^VIX",
        "AAPL": "AAPL", "NVDA": "NVDA", "TSLA": "TSLA",
        "USD/JPY": "JPY=X", "EUR/USD": "EURUSD=X",
    }

    for name, symbol in tickers.items():
        try:
            tk = yf.Ticker(symbol)
            hist = tk.history(period="2d")
            if hist.empty:
                continue
            close = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[0] if len(hist) > 1 else close
            change = ((close - prev) / prev) * 100 if prev else 0
            arrow = "+" if change >= 0 else ""
            snapshots.append(f"{name}: {close:,.2f} ({arrow}{change:.1f}%)")
        except Exception:
            continue

    return " | ".join(snapshots) if snapshots else ""


# ============================================================
# 核心内容生成 — 高质量"母内容"
# ============================================================
PERSONAS = {
    "croc": {
        "name": "Alex 'The Croc'",
        "emoji": "🐊",
        "angle": "technical levels, breakouts, risk/reward setups",
        "voice": "sharp, concise, data-first. Like a trader texting alpha to a friend.",
    },
    "yang": {
        "name": "Thomas Yang",
        "emoji": "📘",
        "angle": "fundamental value, moats, long-term compounding",
        "voice": "calm, philosophical, Buffett-style. Use rhetorical questions.",
    },
    "hong": {
        "name": "Michael Hong",
        "emoji": "🔭",
        "angle": "macro cycles, capital flows, geopolitical shifts",
        "voice": "quiet authority. One data point → one implication → one takeaway.",
    },
    "warrior": {
        "name": "Iron Bull",
        "emoji": "⚔️",
        "angle": "retail empowerment, Wall Street vs Main Street, emotional conviction",
        "voice": "passionate, relatable, 'we' language. Coach at halftime energy.",
    },
}


def get_today_persona():
    """按日期轮换人格"""
    keys = list(PERSONAS.keys())
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(keys)
    return PERSONAS[keys[idx]]


def generate_core_content(knowledge_sources, market_data, realtime):
    """生成核心母内容 — 500-800词深度分析，作为所有平台的内容源头"""
    if not GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        return None

    persona = get_today_persona()
    today = datetime.datetime.utcnow().strftime("%A, %B %d, %Y")

    # 聚合知识库亮点
    knowledge_text = ""
    for src in knowledge_sources[:6]:
        knowledge_text += f"\n[{src['category'].upper()}] {src['file']}:\n"
        knowledge_text += "\n".join(src['highlights'][:8]) + "\n"

    prompt = f"""You are {persona['name']}, a senior market analyst at BroadFSC (global investment advisory). Today is {today}.

YOUR STYLE: {persona['voice']}
YOUR ANGLE: {persona['angle']}

KNOWLEDGE BASE (latest research):
{knowledge_text}

MARKET REFERENCE:
{market_data[:1500]}

LIVE MARKET SNAPSHOT:
{realtime}

TASK: Write a compelling, data-rich market insight (800-1200 words) that our global investor audience cannot scroll past. This will be repurposed across Telegram, Discord, X/Twitter, Mastodon, Bluesky, and Threads.

STRUCTURE:
1. HOOK (1-2 sentences): A specific, surprising data point or observation that stops the scroll. NOT generic market commentary.
2. THE THESIS (3-5 paragraphs): Develop ONE clear argument with:
   - At least 5 specific numbers (prices, percentages, multiples, dollar amounts)
   - At least 1 comparison to historical precedent or cross-asset relationship
   - One contrarian angle — what's the consensus missing?
   - Connect to real earnings, guidance, or macro events happening this week
3. ACTIONABLE FRAMEWORK: A clear framework for how to think about this (not buy/sell advice, but a decision lens with specific scenarios)
4. WHAT WE'RE WATCHING: 2-3 specific catalysts or data points to monitor next
5. CLOSER: One punchy sentence that sticks

QUALITY RULES:
- Zero filler phrases ("In today's market", "It's worth noting")
- Every sentence must contain information or insight, not just words
- Use specific tickers, prices, and percentages
- Be opinionated — fence-sitting is boring
- Sound like an expert sharing alpha, not a newscaster reading headlines
- NO disclaimer, NO "Not financial advice", NO "Subscribe", NO promotional language

Output ONLY valid JSON with no other text: {{"title": "...", "body": "...", "key_data": ["fact1", "fact2", "fact3"], "tickers_mentioned": ["SYM1", "SYM2"]}}

IMPORTANT: Output ONLY the JSON object. No markdown, no code fences, no explanation before or after."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.85,
        )
        raw = response.choices[0].message.content.strip()

        # Robust JSON extraction
        # 1. Remove markdown code fences
        if "```" in raw:
            raw = raw.split("```", 1)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            if "```" in raw:
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

        # 2. Find JSON object boundaries
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        # 3. Remove control characters that break JSON parsing
        import re as _re
        raw = _re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', raw)

        core = json.loads(raw)
        print(f"Core content generated: '{core.get('title', '?')}' ({len(core.get('body', ''))} chars)")
        return core
    except (json.JSONDecodeError, Exception) as e:
        # Last resort: extract title and body from raw text using regex
        print(f"JSON parse failed: {e}")
        title = "Market Insight"
        body = raw if raw else "Market analysis unavailable."

        # Try to extract title and body from malformed JSON
        title_match = __import__('re').search(r'"title"\s*:\s*"([^"]+)"', raw)
        body_match = __import__('re').search(r'"body"\s*:\s*"(.+?)"(?:\s*,|\s*})', raw, __import__('re').DOTALL)
        if title_match:
            title = title_match.group(1)
        if body_match:
            body = body_match.group(1)
        elif len(body) > 2000:
            body = body[:2000]

        # Extract key_data if possible
        key_data = []
        tickers = []
        kd_match = __import__('re').search(r'"key_data"\s*:\s*\[(.*?)\]', raw, __import__('re').DOTALL)
        if kd_match:
            key_data = [s.strip().strip('"') for s in kd_match.group(1).split(",") if s.strip()]
        tk_match = __import__('re').search(r'"tickers_mentioned"\s*:\s*\[(.*?)\]', raw, __import__('re').DOTALL)
        if tk_match:
            tickers = [s.strip().strip('"') for s in tk_match.group(1).split(",") if s.strip()]

        return {"title": title, "body": body, "key_data": key_data, "tickers_mentioned": tickers}
    except Exception as e:
        print(f"Core content generation failed: {e}")
        return None


# ============================================================
# 平台适配 — 从母内容拆分出各平台版本
# ============================================================
def adapt_for_telegram(core):
    """Telegram: 1500字符，HTML格式，5段结构"""
    title = core.get('title', 'Market Insight')
    body = core.get('body', '')
    key_data = core.get('key_data', [])
    tickers = core.get('tickers_mentioned', [])

    parts = [f"<b>📊 {title}</b>\n"]

    # 截断 body 到合适长度
    if len(body) > 1200:
        body = body[:1197] + "..."
    parts.append(body)

    if key_data:
        parts.append("\n<b>🔑 Key Data:</b>")
        for d in key_data[:4]:
            parts.append(f"  • {d}")

    if tickers:
        parts.append("\n" + " ".join(f"#{t}" for t in tickers[:6]))

    return "\n".join(parts)


def adapt_for_discord(core):
    """Discord: 1800字符，Markdown，6段深度分析"""
    title = core.get('title', 'Market Insight')
    body = core.get('body', '')
    key_data = core.get('key_data', [])
    tickers = core.get('tickers_mentioned', [])

    parts = [f"📊 **{title}**\n"]

    if len(body) > 1500:
        body = body[:1497] + "..."
    parts.append(body)

    if key_data:
        parts.append("\n🔑 **Key Data:**")
        for d in key_data[:5]:
            parts.append(f"  • {d}")

    if tickers:
        parts.append("\n" + " ".join(f"`{t}`" for t in tickers[:8]))

    parts.append(f"\n📖 Deep dives → {SUBSTACK_LINK}")
    return "\n".join(parts)


def adapt_for_twitter_thread(core):
    """X/Twitter: 3-5条推文串，每条280字符"""
    title = core.get('title', 'Market Insight')
    body = core.get('body', '')
    key_data = core.get('key_data', [])
    tickers = core.get('tickers_mentioned', [])

    tweets = []

    # 推文1: Hook — 取第一段的核心观点
    # Split by sentence-ending punctuation, keep delimiters
    import re
    sentences = re.split(r'(?<=[.!?])\s+', body)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    hook_parts = []
    hook_len = 0
    for s in sentences[:3]:
        if hook_len + len(s) + 1 > 250:
            break
        hook_parts.append(s)
        hook_len += len(s) + 1

    if hook_parts:
        hook = " ".join(hook_parts)
    else:
        hook = body[:250]
    tweets.append(f"🐊 {hook} 🧵👇")

    # 推文2-4: 正文拆分（按句子边界，不截断数字）
    used_sentences = len(hook_parts)
    remaining = sentences[used_sentences:]

    chunk = ""
    tweet_count = 1
    for s in remaining:
        if len(chunk) + len(s) + 1 > 265:
            if chunk:
                tweets.append(chunk.strip())
                tweet_count += 1
            chunk = s
            if tweet_count >= 4:
                break
        else:
            chunk += " " + s if chunk else s

    if chunk and tweet_count < 5:
        tweets.append(chunk.strip())

    # 最后推文: Key data + tickers
    closing_parts = ["🔑"]
    if key_data:
        closing_parts.append(" | ".join(key_data[:3]))
    if tickers:
        # Clean up index tickers (remove ^ prefix for hashtags)
        clean_tickers = [t.replace("^", "") for t in tickers[:5]]
        closing_parts.append(" ".join(f"#{t}" for t in clean_tickers))
    closing = " ".join(closing_parts)
    if len(closing) > 275:
        closing = closing[:272] + "..."
    tweets.append(closing)

    return tweets


def adapt_for_mastodon(core):
    """Mastodon: 500字符，深度分析"""
    body = core.get('body', '')
    title = core.get('title', 'Market Insight')
    tickers = core.get('tickers_mentioned', [])

    text = f"📊 {title}\n\n"
    if len(body) > 420:
        body = body[:417] + "..."
    text += body

    if tickers:
        tags = " ".join(f"#{t}" for t in tickers[:3])
        remaining = 498 - len(text) - len(tags) - 1
        if remaining > 0:
            text += f"\n{tags}"

    return text[:500]


def adapt_for_bluesky_thread(core):
    """Bluesky: 3-4条串，每条300字符"""
    title = core.get('title', 'Market Insight')
    body = core.get('body', '')
    key_data = core.get('key_data', [])

    posts = []

    # 帖1: Hook
    hook = body.split('.')[0] + '.' if '.' in body else body[:250]
    posts.append(f"📊 {hook} 🧵")

    # 帖2-3: Body chunks
    chunks = []
    chunk = ""
    for sentence in body.split('. '):
        if len(chunk) + len(sentence) + 2 > 280:
            if chunk:
                chunks.append(chunk)
            chunk = sentence
        else:
            chunk += (". " if chunk else "") + sentence
    if chunk:
        chunks.append(chunk)

    for c in chunks[:2]:
        if len(c) > 295:
            c = c[:292] + "..."
        posts.append(c)

    # 帖4: Key data
    if key_data:
        kd = "🔑 " + " | ".join(key_data[:3])
        posts.append(kd[:300])

    return posts


def adapt_for_threads(core):
    """Threads: 500字符，简洁有力"""
    title = core.get('title', 'Market Insight')
    body = core.get('body', '')
    tickers = core.get('tickers_mentioned', [])

    text = f"📊 {title}\n\n"
    if len(body) > 430:
        body = body[:427] + "..."
    text += body

    if tickers and len(text) + 30 < 500:
        text += "\n" + " ".join(f"#{t}" for t in tickers[:4])

    return text[:500]


# ============================================================
# 发布函数
# ============================================================
def send_telegram(text):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("  Telegram: SKIP (no token)")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text + DISCLAIMER, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            msg_id = r.json()['result']['message_id']
            print(f"  Telegram: OK (msg {msg_id})")
            if HAS_ANALYTICS:
                log_post(platform="telegram_en", post_type="repurposed", content_preview=text[:100], post_id=str(msg_id), status="success")
            return True
        else:
            print(f"  Telegram: FAIL HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  Telegram: FAIL {e}")
        return False


def send_discord(text):
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        print("  Discord: SKIP (no token)")
        return False
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}
    if len(text) > 1900:
        text = text[:1897] + "..."
    try:
        r = requests.post(url, headers=headers, json={"content": text}, timeout=15)
        if r.status_code == 200:
            msg_id = r.json().get("id", "")
            print(f"  Discord: OK (msg {msg_id})")
            if HAS_ANALYTICS:
                log_post(platform="discord", post_type="repurposed", content_preview=text[:100], post_id=str(msg_id), status="success")
            return True
        else:
            print(f"  Discord: FAIL HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  Discord: FAIL {e}")
        return False


def send_mastodon(text):
    if not MASTODON_ACCESS_TOKEN:
        print("  Mastodon: SKIP (no token)")
        return False
    url = f"https://{MASTODON_INSTANCE}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"}
    try:
        r = requests.post(url, headers=headers, data={"status": text}, timeout=15)
        if r.status_code == 200:
            print(f"  Mastodon: OK")
            if HAS_ANALYTICS:
                log_post(platform="mastodon", post_type="repurposed", content_preview=text[:100], status="success")
            return True
        else:
            print(f"  Mastodon: FAIL HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  Mastodon: FAIL {e}")
        return False


def send_bluesky(posts):
    """发送 Bluesky thread（多条）"""
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        print("  Bluesky: SKIP (no credentials)")
        return False
    try:
        from atproto import Client
        client = Client()
        client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)

        parent = None
        root = None
        for i, post_text in enumerate(posts):
            reply_ref = None
            if parent and root:
                reply_ref = {"root": root, "parent": parent}

            response = client.send_post(post_text, reply_to=reply_ref)
            uri = response.uri
            cid = response.cid

            if i == 0:
                root = {"uri": str(uri), "cid": str(cid)}
            parent = {"uri": str(uri), "cid": str(cid)}

        print(f"  Bluesky: OK ({len(posts)} posts)")
        if HAS_ANALYTICS:
            log_post(platform="bluesky", post_type="repurposed", content_preview=posts[0][:100], status="success")
        return True
    except Exception as e:
        print(f"  Bluesky: FAIL {e}")
        return False


def send_twitter_thread(tweets):
    """发送 X/Twitter thread（OAuth 1.0a）"""
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("  X/Twitter: SKIP (no OAuth 1.0a credentials)")
        return False
    try:
        import authlib
        from authlib.integrations.requests_client import OAuth1Session
    except ImportError:
        print("  X/Twitter: SKIP (authlib not installed)")
        return False

    try:
        oauth = OAuth1Session(
            TWITTER_API_KEY, client_secret=TWITTER_API_SECRET,
            resource_owner_key=TWITTER_ACCESS_TOKEN,
            resource_owner_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )

        prev_id = None
        for i, tweet in enumerate(tweets):
            payload = {"text": tweet}
            if prev_id:
                payload["reply"] = {"in_reply_to_tweet_id": prev_id}

            r = oauth.post("https://api.twitter.com/2/tweets", json=payload)
            if r.status_code == 201:
                data = r.json().get("data", {})
                prev_id = data.get("id")
                print(f"  X/Twitter: Tweet {i+1}/{len(tweets)} OK")
            else:
                print(f"  X/Twitter: Tweet {i+1} FAIL HTTP {r.status_code}")
                return False

        if HAS_ANALYTICS:
            log_post(platform="twitter", post_type="repurposed", content_preview=tweets[0][:100], status="success")
        return True
    except Exception as e:
        print(f"  X/Twitter: FAIL {e}")
        return False


def send_threads(text):
    """发送到 Threads（2步: create container → publish）"""
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("  Threads: SKIP (no token)")
        return False
    api_base = "https://graph.threads.net/v1.0"

    try:
        # Step 1: Create container
        r = requests.post(
            f"{api_base}/{THREADS_USER_ID}/threads",
            params={
                "media_type": "TEXT",
                "text": text,
                "access_token": THREADS_ACCESS_TOKEN,
            },
            timeout=15,
        )
        if r.status_code != 200:
            print(f"  Threads: Container FAIL HTTP {r.status_code} - {r.text[:200]}")
            return False

        creation_id = r.json().get("id")

        # Step 2: Publish
        r = requests.post(
            f"{api_base}/{THREADS_USER_ID}/threads_publish",
            params={"creation_id": creation_id, "access_token": THREADS_ACCESS_TOKEN},
            timeout=15,
        )
        if r.status_code == 200:
            post_id = r.json().get("id", "")
            print(f"  Threads: OK (post {post_id})")
            if HAS_ANALYTICS:
                log_post(platform="threads", post_type="repurposed", content_preview=text[:100], post_id=str(post_id), status="success")
            return True
        else:
            print(f"  Threads: Publish FAIL HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  Threads: FAIL {e}")
        return False


# ============================================================
# Main
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="BroadFSC Content Repurposer")
    parser.add_argument("--generate", action="store_true", help="Only generate, don't post")
    parser.add_argument("--platform", nargs="*", help="Only post to specified platforms")
    args = parser.parse_args()

    print("=" * 60)
    print("BroadFSC Content Repurposer — 一鱼多吃")
    print(f"Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    persona = get_today_persona()
    print(f"Persona: {persona['emoji']} {persona['name']}")
    print("=" * 60)

    # Step 1: 聚合素材
    print("\n📚 Gathering knowledge base...")
    knowledge_sources, market_data = gather_knowledge()
    print(f"  Found {len(knowledge_sources)} knowledge sources")

    print("\n📡 Fetching real-time market data...")
    realtime = fetch_realtime_data()
    print(f"  {'OK: ' + realtime[:100] + '...' if realtime else 'No data'}")

    # Step 2: 生成核心内容
    print("\n🧠 Generating core content...")
    core = generate_core_content(knowledge_sources, market_data, realtime)

    if not core:
        print("FAILED: Could not generate core content. Exiting.")
        return

    print(f"\n  Title: {core.get('title', '?')}")
    print(f"  Body length: {len(core.get('body', ''))} chars")
    print(f"  Key data: {core.get('key_data', [])}")
    print(f"  Tickers: {core.get('tickers_mentioned', [])}")

    # Step 3: 平台适配
    print("\n🔄 Adapting for platforms...")
    adaptations = {
        "telegram": adapt_for_telegram(core),
        "discord": adapt_for_discord(core),
        "twitter": adapt_for_twitter_thread(core),
        "mastodon": adapt_for_mastodon(core),
        "bluesky": adapt_for_bluesky_thread(core),
        "threads": adapt_for_threads(core),
    }

    for platform, content in adaptations.items():
        if isinstance(content, list):
            total_chars = sum(len(p) for p in content)
            print(f"  {platform}: {len(content)} posts, {total_chars} total chars")
        else:
            print(f"  {platform}: {len(content)} chars")

    if args.generate:
        print("\n📝 Preview mode — not posting. Content generated above.")
        # 输出预览
        print("\n" + "=" * 60)
        print("TELEGRAM PREVIEW:")
        print("-" * 40)
        print(adaptations["telegram"][:500])
        print("\n" + "=" * 60)
        print("DISCORD PREVIEW:")
        print("-" * 40)
        print(adaptations["discord"][:500])
        print("\n" + "=" * 60)
        print("X/TWITTER THREAD PREVIEW:")
        print("-" * 40)
        for i, tweet in enumerate(adaptations["twitter"]):
            print(f"  Tweet {i+1}: {tweet}")
        return

    # Step 4: 发布
    print("\n📤 Publishing...")
    target_platforms = args.platform if args.platform else list(adaptations.keys())
    results = {}

    for platform in target_platforms:
        if platform not in adaptations:
            print(f"  {platform}: Unknown platform, skip")
            continue

        content = adaptations[platform]

        if platform == "telegram":
            results[platform] = send_telegram(content)
        elif platform == "discord":
            results[platform] = send_discord(content)
        elif platform == "twitter":
            results[platform] = send_twitter_thread(content)
        elif platform == "mastodon":
            results[platform] = send_mastodon(content)
        elif platform == "bluesky":
            results[platform] = send_bluesky(content)
        elif platform == "threads":
            results[platform] = send_threads(content)

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS:")
    for p, ok in results.items():
        status = "✅" if ok else "❌/SKIP"
        print(f"  {p}: {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
