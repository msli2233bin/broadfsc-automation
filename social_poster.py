"""
BroadFSC Social Media Auto-Poster
Posts daily market analysis to X/Twitter and other platforms.

X/Twitter Free API limitations (2024+):
- OAuth 2.0 App-Only (Bearer Token): READ ONLY - can read tweets but NOT post
- OAuth 1.0a User Context: REQUIRED for posting - needs 4 credentials
- Free tier: 1,500 tweets/month post limit

To POST tweets, you need OAuth 1.0a credentials:
  - TWITTER_API_KEY (Consumer Key)
  - TWITTER_API_SECRET (Consumer Secret)  
  - TWITTER_ACCESS_TOKEN
  - TWITTER_ACCESS_TOKEN_SECRET

If only Bearer Token is available, the script will:
  - Monitor trending finance hashtags
  - Log engagement data for strategy optimization
  - Post only when OAuth 1.0a credentials are provided

LinkedIn:
  - LINKEDIN_ACCESS_TOKEN (long-lived)
  - Can post to LinkedIn Page with OAuth 2.0
"""

import os
import sys
import datetime
import requests
import json
import hashlib
from pathlib import Path

# Analytics tracking
try:
    from analytics_logger import log_post, get_tracking_url
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
# X/Twitter - OAuth 1.0a (for posting)
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

# X/Twitter - Bearer Token (read-only, for monitoring)
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")

# LinkedIn
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")

# Mastodon
MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN", "")
MASTODON_INSTANCE = os.environ.get("MASTODON_INSTANCE", "mastodon.social")

# Discord
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "")

# TikTok (via Postproxy)
POSTPROXY_API_KEY = os.environ.get("POSTPROXY_API_KEY", "")
TIKTOK_VIDEO_URL = os.environ.get("TIKTOK_VIDEO_URL", "")
TIKTOK_MODE = os.environ.get("TIKTOK_MODE", "slideshow").lower()

# Bluesky
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")

# LINE Official Account
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

# Threads (Meta API)
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")

if not THREADS_ACCESS_TOKEN:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _env_path = os.path.join(_script_dir, ".env")
    if os.path.exists(_env_path):
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("THREADS_ACCESS_TOKEN="):
                    THREADS_ACCESS_TOKEN = line.strip().split("=", 1)[1]
                elif line.startswith("THREADS_USER_ID=") and not THREADS_USER_ID:
                    THREADS_USER_ID = line.strip().split("=", 1)[1]
    if not THREADS_ACCESS_TOKEN:
        _token_path = os.path.join(_script_dir, "threads_token.txt")
        if os.path.exists(_token_path):
            with open(_token_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("THREADS_ACCESS_TOKEN="):
                        THREADS_ACCESS_TOKEN = line.strip().split("=", 1)[1]
                    elif line.startswith("THREADS_USER_ID=") and not THREADS_USER_ID:
                        THREADS_USER_ID = line.strip().split("=", 1)[1]

# StockTwits
STOCKTWITS_ACCESS_TOKEN = os.environ.get("STOCKTWITS_ACCESS_TOKEN", "")

# Medium (browser automation — runs locally, not on GitHub Actions)
MEDIUM_EMAIL = os.environ.get("MEDIUM_EMAIL", "")
MEDIUM_PASSWORD = os.environ.get("MEDIUM_PASSWORD", "")

# Substack (browser automation — runs locally, not on GitHub Actions)
SUBSTACK_EMAIL = os.environ.get("SUBSTACK_EMAIL", "")
SUBSTACK_PASSWORD = os.environ.get("SUBSTACK_PASSWORD", "")
SUBSTACK_PUB_URL = os.environ.get("SUBSTACK_PUB_URL", "https://broadcastmarketintelligence.substack.com")
SUBSTACK_LINK = os.environ.get("SUBSTACK_LINK", "https://broadcastmarketintelligence.substack.com")

# AI
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Notification
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

TELEGRAM_LINK = "https://t.me/BroadFSC"
WEBSITE_LINK = "https://www.broadfsc.com/different"
HUB_LINK = "https://www.broadfsc.com/different"


def get_tracked_links(platform):
    """Generate UTM-tracked links for a specific platform.

    Returns dict with: telegram, website, hub — all with UTM params.
    Each platform has a different引流 strategy to reduce ban risk.
    """
    if HAS_ANALYTICS:
        return {
            "telegram": get_tracking_url(TELEGRAM_LINK, platform, "telegram"),
            "website": get_tracking_url(WEBSITE_LINK, platform, "website"),
            "hub": get_tracking_url(HUB_LINK, platform, "website"),
            "substack": get_tracking_url(SUBSTACK_LINK, platform, "website"),
        }
    return {
        "telegram": TELEGRAM_LINK,
        "website": WEBSITE_LINK,
        "hub": HUB_LINK,
        "substack": SUBSTACK_LINK,
    }


# ============================================================
# Platform-Specific Link Strategies
# ============================================================
# Different platforms have different rules and risk levels.
# This config controls how links appear in posts per platform.

LINK_STRATEGY = {
    "twitter": {
        "style": "short",          # Twitter: Short, no full URL in every post
        "link_every_n": 3,         # Only include link every N posts
        "prefer": "hub",           # Prefer hub link (more visual, educational)
        "text_fallback": "Learn more → link in bio",  # When no link included
    },
    "mastodon": {
        "style": "full",           # Mastodon: Full links OK, lenient platform
        "link_every_n": 1,         # Every post can have a link
        "prefer": "hub",
    },
    "discord": {
        "style": "full",           # Discord: Full links, community-friendly
        "link_every_n": 1,
        "prefer": "hub",
    },
    "bluesky": {
        "style": "minimal",        # Bluesky: Minimal links, focus on content
        "link_every_n": 2,
        "prefer": "hub",
        "text_fallback": "Follow for daily insights",
    },
    "tiktok": {
        "style": "caption_only",   # TikTok: Link only in caption, not in video
        "link_every_n": 1,
        "prefer": "hub",
    },
    "linkedin": {
        "style": "professional",   # LinkedIn: Professional tone, website preferred
        "link_every_n": 1,
        "prefer": "hub",
    },
    "threads": {
        "style": "minimal",        # Threads: Minimal links, focus on engagement
        "link_every_n": 2,
        "prefer": "substack",      # Prefer Substack link for Threads audience
        "text_fallback": "Follow for daily market insights",
    },
    "stocktwits": {
        "style": "none",           # StockTwits: No links (140 char limit), cashtags only
        "link_every_n": 0,
        "prefer": "hub",
        "text_fallback": "",
    },
    "line": {
        "style": "flex",           # LINE: Flex Message with CTA button, link in button
        "link_every_n": 1,
        "prefer": "website",       # Website link goes into Flex Message CTA button
    },
    "medium": {
        "style": "full",           # Medium: Full links in article body, no character limit
        "link_every_n": 1,
        "prefer": "hub",
    },
    "substack": {
        "style": "full",           # Substack: Full links in article body, no character limit
        "link_every_n": 1,
        "prefer": "hub",
    },
}


def should_include_link(platform, post_count=0):
    """Determine if this post should include a引流 link.

    Args:
        platform: Social platform name
        post_count: How many posts have been made today (for frequency control)

    Returns:
        bool: Whether to include a link
    """
    strategy = LINK_STRATEGY.get(platform, LINK_STRATEGY["twitter"])
    every_n = strategy.get("link_every_n", 1)
    return post_count % every_n == 0


def get_platform_link(platform, post_count=0):
    """Get the appropriate link for a platform post.

    Args:
        platform: Social platform name
        post_count: Post count for frequency control

    Returns:
        str or None: The link to include, or None if skipping this time
    """
    if not should_include_link(platform, post_count):
        strategy = LINK_STRATEGY.get(platform, LINK_STRATEGY["twitter"])
        return strategy.get("text_fallback", "")

    links = get_tracked_links(platform)
    strategy = LINK_STRATEGY.get(platform, LINK_STRATEGY["twitter"])
    prefer = strategy.get("prefer", "hub")
    return links.get(prefer, links["hub"])

# Tags
HASHTAGS = ["#Investing", "#Trading", "#MarketAnalysis", "#StockMarket", "#Finance"]


# ============================================================
# 4-Persona Voice System
# Inspired by top Chinese finance KOLs, adapted for international
# English-speaking audiences covering US & global markets.
# Rotates daily — each persona gets its own distinct voice.
# ============================================================
SOCIAL_PERSONAS = {
    "croc": {
        "name": "Alex 'The Croc'",
        "title": "Technical Hunter",
        "emoji": "🐊",
        "style": (
            "You are Alex, a razor-sharp technical trader. Ultra-concise, chart-driven. "
            "Give exact levels (support/resistance/breakout). Skip macro fluff. "
            "Write like a trader texting alpha to a friend. "
            "Short punchy sentences. Max 2 emojis. Never use 'may' or 'could'."
        ),
        "hook": "Start with a specific price level or % move.",
        "hashtags": ["#TechnicalAnalysis", "#Trading", "#StockMarket", "#Investing"],
    },
    "yang": {
        "name": "Thomas Yang",
        "title": "Value Compass",
        "emoji": "📘",
        "style": (
            "You are Thomas, a Buffett disciple who has managed money for 30+ years. "
            "Calm, philosophical, long-term perspective. Challenge short-term panic with fundamentals. "
            "Use rhetorical questions. Quote great investors when relevant. "
            "Redirect to earnings quality, balance sheet strength, and moats."
        ),
        "hook": "Start with a rhetorical question that challenges the short-term narrative.",
        "hashtags": ["#ValueInvesting", "#LongTerm", "#Buffett", "#Investing"],
    },
    "hong": {
        "name": "Michael Hong",
        "title": "Macro Strategist",
        "emoji": "🔭",
        "style": (
            "You are Michael, a macro strategist who connects cycles, capital flows, and geopolitics. "
            "Data-driven, intellectually rigorous. Use one specific data point (yield, PMI, spread) to anchor thesis. "
            "Speak with quiet authority. Structure: 1 macro observation → 1 implication → 1 takeaway. "
            "Say what the consensus is missing."
        ),
        "hook": "Start with a macro data point most investors overlook.",
        "hashtags": ["#MacroStrategy", "#GlobalMarkets", "#Investing", "#Finance"],
    },
    "warrior": {
        "name": "Iron Bull",
        "title": "Voice of the Retail Fighter",
        "emoji": "⚔️",
        "style": (
            "You are Iron Bull, voice of the everyday investor fighting Wall Street. "
            "Passionate, relatable, emotionally resonant. Validate retail pain then rally with data. "
            "Use 'we' — you're in this together. Call out market dynamics with fire but back with fact. "
            "Energy of a coach at halftime. End with a battle cry or motivational close."
        ),
        "hook": "Start with empathy — name the fear most retail investors feel right now.",
        "hashtags": ["#RetailInvestor", "#WallStreet", "#Investing", "#StockMarket"],
    },
}


def get_daily_persona(platform_shift: int = 0) -> dict:
    """Return today's active persona, shifted per platform for variety.

    Args:
        platform_shift: int offset so different platforms use different personas same day.
    """
    now = datetime.datetime.utcnow()
    keys = list(SOCIAL_PERSONAS.keys())
    idx = (now.timetuple().tm_yday + platform_shift) % len(keys)
    return SOCIAL_PERSONAS[keys[idx]]


# ============================================================
# Knowledge-Driven Content (知识库→帖子)
# ============================================================
CONTENT_QUEUE_DIR = Path(__file__).parent / 'knowledge' / 'content_queue'

def get_queued_content(platform: str) -> str | None:
    """从知识库内容队列中读取未使用的帖子内容"""
    if not CONTENT_QUEUE_DIR.exists():
        return None

    # 扫描该平台的未使用内容，按日期倒序
    candidates = []
    for f in sorted(CONTENT_QUEUE_DIR.glob(f"*_{platform}_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            if not data.get('used', False):
                candidates.append((f, data))
        except:
            continue

    if not candidates:
        return None

    # 随机选一个（避免每次都用最新的）
    import random
    chosen_file, chosen_data = random.choice(candidates)

    # 标记为已使用
    chosen_data['used'] = True
    chosen_data['used_at'] = datetime.datetime.now().isoformat()
    chosen_file.write_text(json.dumps(chosen_data, ensure_ascii=False, indent=2), encoding='utf-8')

    return chosen_data.get('content')


def generate_platform_content(platform: str):
    """智能内容生成：优先用知识库内容，其次AI生成，最后fallback

    Returns:
        str for most platforms, list[str] for twitter/bluesky (thread format)
    """
    # 1. 优先从知识库内容队列读取
    queued = get_queued_content(platform)
    if queued:
        print(f"  [{platform}] Using knowledge-queue content")
        return queued

    # 2. 回退到原平台专属生成函数
    generators = {
        'twitter': generate_tweet_content,
        'mastodon': generate_mastodon_content,
        'discord': generate_discord_content,
        'bluesky': generate_bluesky_content,
        'tiktok': generate_tiktok_content,
        'linkedin': generate_linkedin_content,
        'line': generate_line_content,
        'medium': generate_medium_content,
        'substack': generate_substack_content,
        'threads': generate_threads_content,
        'stocktwits': generate_stocktwits_content,
    }

    gen_func = generators.get(platform)
    if gen_func:
        return gen_func()

    return "Market update from BroadFSC. #Investing #Trading"


# ============================================================
# X/Twitter OAuth 1.0a Helper
# ============================================================
def percent_encode(s):
    """Percent-encode a string per OAuth 1.0a spec."""
    import urllib.parse
    return urllib.parse.quote(str(s), safe='')


def create_oauth_signature(method, url, params, api_key, api_secret, token="", token_secret=""):
    """Create OAuth 1.0a signature."""
    import urllib.parse
    # Create parameter string (sorted)
    param_str = "&".join([percent_encode(k) + "=" + percent_encode(v) for k, v in sorted(params.items())])
    
    # Create base string
    base_string = method.upper() + "&" + percent_encode(url) + "&" + percent_encode(param_str)
    
    # Create signing key
    signing_key = percent_encode(api_secret) + "&" + percent_encode(token_secret)
    
    # Sign
    import hmac
    import hashlib
    signature = hmac.new(
        signing_key.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    import base64
    return base64.b64encode(signature).decode('utf-8')


def get_oauth_header(method, url, api_key, api_secret, access_token="", access_token_secret=""):
    """Generate full OAuth 1.0a Authorization header."""
    import time
    import uuid
    
    params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if access_token:
        params["oauth_token"] = access_token
    
    signature = create_oauth_signature(method, url, params, api_key, api_secret, access_token, access_token_secret)
    params["oauth_signature"] = signature
    
    header_parts = ["OAuth "]
    for k, v in sorted(params.items()):
        header_parts.append(percent_encode(k) + '="' + percent_encode(v) + '", ')
    
    return "".join(header_parts).rstrip(", ")


def post_tweet(text):
    """Post a single tweet using OAuth 1.0a."""
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("  X/Twitter: Missing OAuth 1.0a credentials (need API Key, API Secret, Access Token, Access Token Secret)")
        print("  X/Twitter: Bearer Token is read-only and cannot post tweets")
        return False

    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": get_oauth_header(
            "POST", url,
            TWITTER_API_KEY, TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
        ),
        "Content-Type": "application/json",
        "User-Agent": "BroadFSC-Bot/1.0",
    }
    payload = {"text": text}

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 201:
            tweet_id = r.json()["data"]["id"]
            print("  X/Twitter: Posted! Tweet ID: " + tweet_id)
            print("  URL: https://twitter.com/i/status/" + tweet_id)
            if HAS_ANALYTICS:
                log_post(platform="twitter", post_type="tweet", content_preview=text[:100], post_id=tweet_id, status="success")
            return True, tweet_id
        elif r.status_code == 402:
            print("  X/Twitter: HTTP 402 - Payment Required (Twitter API is no longer free for posting)")
            print("  X/Twitter: Basic plan starts at $100/month. See: https://developer.twitter.com/en/portal/products/basic")
            print("  X/Twitter: SKIPPING (zero-cost strategy - set TWITTER_SKIP_402=true)")
            if HAS_ANALYTICS:
                log_post(platform="twitter", post_type="tweet", content_preview=text[:100], status="skipped", error_msg="HTTP 402 - API not free")
            return False, None
        else:
            print("  X/Twitter: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            if HAS_ANALYTICS:
                log_post(platform="twitter", post_type="tweet", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False, None
    except Exception as e:
        print("  X/Twitter: FAIL - " + str(e))
        if HAS_ANALYTICS:
            log_post(platform="twitter", post_type="tweet", content_preview=text[:100], status="failed", error_msg=str(e)[:200])
        return False, None


def post_tweet_thread(tweets):
    """Post a Twitter thread (multiple tweets linked by replies).

    Args:
        tweets: list of strings, each ≤280 characters.
                First tweet is the root, rest are replies.

    Returns:
        True if all tweets posted, False otherwise.
    """
    if not tweets:
        return False

    if len(tweets) == 1:
        ok, _ = post_tweet(tweets[0])
        return ok

    previous_tweet_id = None
    all_ok = True

    for i, tweet_text in enumerate(tweets):
        if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
            print("  X/Twitter thread: Missing OAuth 1.0a credentials")
            return False

        url = "https://api.twitter.com/2/tweets"
        headers = {
            "Authorization": get_oauth_header(
                "POST", url,
                TWITTER_API_KEY, TWITTER_API_SECRET,
                TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
            ),
            "Content-Type": "application/json",
            "User-Agent": "BroadFSC-Bot/1.0",
        }

        payload = {"text": tweet_text}
        if previous_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": previous_tweet_id}

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 201:
                tweet_id = r.json()["data"]["id"]
                previous_tweet_id = tweet_id
                print("  X/Twitter thread [" + str(i+1) + "/" + str(len(tweets)) + "]: Posted! ID: " + tweet_id)
                if HAS_ANALYTICS and i == 0:
                    log_post(platform="twitter", post_type="thread", content_preview=tweet_text[:100], post_id=tweet_id, status="success")
            else:
                print("  X/Twitter thread [" + str(i+1) + "/" + str(len(tweets)) + "]: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
                all_ok = False
                break
        except Exception as e:
            print("  X/Twitter thread [" + str(i+1) + "/" + str(len(tweets)) + "]: FAIL - " + str(e))
            all_ok = False
            break

    return all_ok


# ============================================================
# Mastodon Poster
# ============================================================
def post_mastodon(text, retries=2):
    """Post to Mastodon using access token. Retries on transient failures."""
    if not MASTODON_ACCESS_TOKEN or not MASTODON_INSTANCE:
        print("  Mastodon: Missing MASTODON_ACCESS_TOKEN or MASTODON_INSTANCE")
        return False

    url = "https://" + MASTODON_INSTANCE + "/api/v1/statuses"
    headers = {
        "Authorization": "Bearer " + MASTODON_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    # Mastodon limit is 500 chars
    if len(text) > 500:
        text = text[:497] + "..."
    payload = {"status": text}

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                toot_id = r.json().get("id", "")
                toot_url = r.json().get("url", "")
                print("  Mastodon: Posted! ID: " + str(toot_id))
                print("  URL: " + str(toot_url))
                if HAS_ANALYTICS:
                    log_post(platform="mastodon", post_type="toot", content_preview=text[:100], post_id=str(toot_id), status="success")
                return True
            elif r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 2 ** attempt
                print("  Mastodon: HTTP " + str(r.status_code) + " — retry " + str(attempt) + "/" + str(retries) + " in " + str(wait) + "s")
                import time; time.sleep(wait)
                continue
            else:
                print("  Mastodon: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
                if HAS_ANALYTICS:
                    log_post(platform="mastodon", post_type="toot", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
                return False
        except requests.exceptions.ConnectionError as e:
            if attempt < retries:
                wait = 2 ** attempt
                print("  Mastodon: Connection error — retry " + str(attempt) + "/" + str(retries) + " in " + str(wait) + "s")
                import time; time.sleep(wait)
                continue
            print("  Mastodon: FAIL (connection) - " + str(e))
            if HAS_ANALYTICS:
                log_post(platform="mastodon", post_type="toot", content_preview=text[:100], status="failed", error_msg=str(e)[:200])
            return False
        except Exception as e:
            print("  Mastodon: FAIL - " + str(e))
            if HAS_ANALYTICS:
                log_post(platform="mastodon", post_type="toot", content_preview=text[:100], status="failed", error_msg=str(e)[:200])
            return False
    return False


def _get_market_snippet():
    """Fetch a compact real-time market data snippet for AI prompt injection.

    Returns a short string like "SPY=5280(+0.8%) VIX=14.2 10Y=4.35%"
    Falls back gracefully if yfinance is unavailable.
    """
    try:
        import yfinance as yf
        parts = []
        for sym, label in [("^GSPC", "SPY"), ("^IXIC", "QQQ"), ("^VIX", "VIX"), ("^TNX", "10Y")]:
            try:
                t = yf.Ticker(sym)
                h = t.history(period="2d")
                if len(h) >= 1:
                    c = h['Close'].iloc[-1]
                    if len(h) >= 2:
                        pct = (c / h['Close'].iloc[-2] - 1) * 100
                        parts.append(label + "=" + f"{c:.1f}" + "(" + f"{pct:+.1f}%" + ")")
                    else:
                        parts.append(label + "=" + f"{c:.1f}")
            except Exception:
                continue
        return " | ".join(parts) if parts else "US markets open"
    except ImportError:
        return "US markets open"
    except Exception:
        return "US markets open"


def generate_mastodon_content():
    """Generate a punchy Mastodon toot in today's analyst persona voice.

    Strategy for 500-char limit: Front-load insight, end with CTA + link.
    The AI must produce the VALUE first — links get truncated if needed.
    """
    if not GROQ_API_KEY:
        return get_fallback_mastodon()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")

        persona = get_daily_persona(platform_shift=1)
        tags = " ".join(persona["hashtags"])
        links = get_tracked_links("mastodon")

        # Inject real market data
        market_snippet = _get_market_snippet()

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a PUNCHY Mastodon toot for " + day + ", " + date_str + ".\n\n"
                    "LIVE DATA: " + market_snippet + "\n\n"
                    "HOOK: " + persona["hook"] + "\n\n"
                    "Structure (STRICT — you have only 500 chars total):\n"
                    "1. BOLD HOOK — One specific data point or contrarian claim (1 sentence)\n"
                    "2. THE INSIGHT — Why it matters, what others miss (2-3 short sentences)\n"
                    "3. THE TAKE — One actionable takeaway (1 sentence)\n"
                    "4. ENGAGE — Ask a question that invites replies\n"
                    "5. TAGS — 2-3 hashtags\n\n"
                    "CRITICAL RULES:\n"
                    "- TOTAL output MUST be under 480 characters (leave room for link)\n"
                    "- Include 2-3 specific numbers (prices, %, yields)\n"
                    "- Use $TICKER format for stock mentions\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Do NOT include any links — they will be appended automatically\n"
                    "- Do NOT promise returns or give buy/sell advice\n"
                    "- Write like a trader texting alpha, not a newsletter\n"
                    "- Every word must earn its place — zero filler"
                )
            }],
            max_tokens=300,
            temperature=0.9
        )
        result = response.choices[0].message.content.strip()

        # Append CTA + link (auto-truncate body if needed)
        cta_line = " 📱@BroadInvestBot"
        link_line = " " + links["substack"]
        footer = cta_line + link_line

        available = 497 - len(footer)
        if len(result) > available:
            result = result[:available - 3] + "..."
        result += footer

        # Final safety net
        if len(result) > 500:
            result = result[:497] + "..."

        print("  Mastodon persona: " + persona["name"] + " (" + str(len(result)) + " chars)")
        return result
    except Exception as e:
        print("  AI Mastodon generation failed: " + str(e))
        return get_fallback_mastodon()


def get_fallback_mastodon():
    """Fallback Mastodon content — 5 diverse toots, always under 480 chars."""
    links = get_tracked_links("mastodon")
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    toots = [
        "10Y-2Y inverted 18+ months. Every recession in 50 years followed. Credit spreads say 'all clear' — they said that in 2007 too. Which blinks first: bonds or equities? #Investing #Bonds 📱@BroadInvestBot " + links["substack"],
        "Gold at ATH while real yields stay elevated. Cross-asset divergence this extreme happened 3 times in 40 years — each time, central banks cut faster than priced. #Gold #Macro 📱@BroadInvestBot " + links["substack"],
        "AI stocks = 2000 dot-com. Transformative tech, insane valuations. $NVDA at 65x sales vs $CSCO at 40x in 2000. The tech is real. The prices aren't. Patience wins. #AI #Investing 📱@BroadInvestBot " + links["substack"],
        "S&P earnings growth 4% but multiples expanding 15%. This market runs on multiple expansion, not earnings. That works until it doesn't. What's your exit signal? #SP500 #Trading 📱@BroadInvestBot " + links["substack"],
        "Consumer savings rate dropped from 5.3% to 3.6% in 6 months. Credit card delinquencies at 12-year high. The consumer engine is sputtering — markets haven't noticed. #Economy #Risk 📱@BroadInvestBot " + links["substack"],
    ]
    fallback = toots[day_idx % len(toots)]
    # Safety: ensure under 500 chars
    if len(fallback) > 500:
        fallback = fallback[:497] + "..."
    return fallback


# ============================================================
# Discord Poster
# ============================================================
def post_discord(text, retries=2):
    """Post a message to Discord channel. Retries on transient failures."""
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        print("  Discord: Missing DISCORD_BOT_TOKEN or DISCORD_CHANNEL_ID")
        return False

    url = "https://discord.com/api/v10/channels/" + DISCORD_CHANNEL_ID + "/messages"
    headers = {
        "Authorization": "Bot " + DISCORD_BOT_TOKEN,
        "Content-Type": "application/json",
    }
    # Discord limit is 2000 chars
    if len(text) > 1900:
        text = text[:1897] + "..."
    payload = {"content": text}

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                msg_id = r.json().get("id", "")
                print("  Discord: Posted! Message ID: " + str(msg_id))
                if HAS_ANALYTICS:
                    log_post(platform="discord", post_type="message", content_preview=text[:100], post_id=str(msg_id), status="success")
                return True
            elif r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 2 ** attempt
                if r.status_code == 429:
                    retry_after = r.json().get("retry_after", wait)
                    wait = max(wait, float(retry_after))
                print("  Discord: HTTP " + str(r.status_code) + " — retry " + str(attempt) + "/" + str(retries) + " in " + str(wait) + "s")
                import time; time.sleep(wait)
                continue
            else:
                print("  Discord: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
                if HAS_ANALYTICS:
                    log_post(platform="discord", post_type="message", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
                return False
        except requests.exceptions.ConnectionError as e:
            if attempt < retries:
                wait = 2 ** attempt
                print("  Discord: Connection error — retry " + str(attempt) + "/" + str(retries) + " in " + str(wait) + "s")
                import time; time.sleep(wait)
                continue
            print("  Discord: FAIL (connection) - " + str(e))
            if HAS_ANALYTICS:
                log_post(platform="discord", post_type="message", status="failed", error_msg=str(e)[:200])
            return False
        except Exception as e:
            print("  Discord: FAIL - " + str(e))
            if HAS_ANALYTICS:
                log_post(platform="discord", post_type="message", status="failed", error_msg=str(e)[:200])
            return False
    return False


def generate_discord_content():
    """Generate a Discord community post in today's analyst persona voice.

    Discord advantage: 2000 chars, markdown, community engagement.
    Strategy: Rich analysis + embedded data + discussion hook.
    """
    if not GROQ_API_KEY:
        return get_fallback_discord()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")

        persona = get_daily_persona(platform_shift=2)
        tags = " ".join(persona["hashtags"])
        links = get_tracked_links("discord")

        # Inject real market data
        market_snippet = _get_market_snippet()

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE Discord post for " + day + ", " + date_str + ".\n\n"
                    "LIVE DATA: " + market_snippet + "\n\n"
                    "HOOK: " + persona["hook"] + "\n\n"
                    "Structure (follow exactly, use Discord markdown):\n"
                    "1. **🔥 HOOK** — One bold claim with a specific number (stops scrolling)\n"
                    "2. **📊 THE SETUP** — 3-4 sentences of context connecting to LIVE DATA above\n"
                    "3. **💡 THE INSIGHT** — Your contrarian angle. What's the consensus missing? Use $TICKER format.\n"
                    "4. **🔢 BY THE NUMBERS** — Bullet list of 3-4 specific data points:\n"
                    "   • Point with context (not just 'S&P up 1%')\n"
                    "   • Each bullet = one insight, not one number\n"
                    "5. **🎯 THE TAKE** — One clear, actionable takeaway\n"
                    "6. **💬 DISCUSSION** — End with a specific, provocative question that demands an opinion\n\n"
                    "Rules:\n"
                    "- Maximum 1700 characters (leave room for footer)\n"
                    "- Use **bold** for headers, bullet points for data\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Include 4-6 specific numbers across the post\n"
                    "- Use $TICKER for every stock mention (e.g. $AAPL, $TSLA, $NVDA)\n"
                    "- Sound like a senior analyst sharing alpha, not a chatbot\n"
                    "- Do NOT include links or CTAs — they will be appended\n"
                    "- Do NOT promise returns or give buy/sell advice\n"
                    "- Zero filler: 'In today's market', 'It's worth noting' = DELETE"
                )
            }],
            max_tokens=750,
            temperature=0.9
        )
        result = response.choices[0].message.content.strip()

        # Append footer with links and CTA
        footer = (
            "\n\n━━━━━━━━━━━━━━━━━━\n"
            "📱 Free consult @BroadInvestBot | 📐 Full analysis t.me/BroadFSC\n"
            "📖 Deep dives: " + links["substack"] + "\n"
            "⚠️ Not financial advice\n\n"
            + tags
        )

        # Ensure total under 1900 chars
        available = 1897 - len(footer)
        if len(result) > available:
            result = result[:available - 3] + "..."
        result += footer

        if len(result) > 1900:
            result = result[:1897] + "..."

        print("  Discord persona: " + persona["name"] + " (" + str(len(result)) + " chars)")
        return result
    except Exception as e:
        print("  AI Discord generation failed: " + str(e))
        return get_fallback_discord()


def get_fallback_discord():
    """Fallback Discord content — 5 diverse community posts with engagement hooks."""
    links = get_tracked_links("discord")
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    posts = [
        (
            "**🔥 The Soft Landing Illusion?**\n\n"
            "Markets are priced for perfection. S&P at 21x earnings. Credit spreads near historic tights. VIX below 15. Everything says 'all clear.'\n\n"
            "**💡 The Insight:**\n"
            "The yield curve has been inverted for 18+ months. Every recession in 50 years was preceded by an inversion — with a 12-18 month lag. We're in that lag window NOW.\n\n"
            "**🔢 By The Numbers:**\n"
            "• 10Y-2Y spread: -0.35% (still inverted)\n"
            "• CRE delinquencies: up 2.1x YoY\n"
            "• Consumer savings: 5.3% → 3.6% in 6 months\n\n"
            "**🎯 Take:** Don't predict a recession. Prepare for one. Reduce leverage, raise cash, own zig-when-equities-zag assets.\n\n"
            "**💬 Soft landing or hard reality? What's your positioning?**"
        ),
        (
            "**📊 The $4 Trillion Carry Trade Nobody Talks About**\n\n"
            "Borrow at 0.5%, invest at 5%. That 4.5% spread is 'carry.' Hedge funds do this at scale — borrowing JPY to buy USD assets.\n\n"
            "**💡 The Insight:**\n"
            "When BOJ hiked rates in July 2024, the math flipped. Forced selling of $SPY, $QQQ, $NVDA — all in 3 trading days. The biggest moves come from hidden leverage, not fundamentals.\n\n"
            "**🔢 By The Numbers:**\n"
            "• $JPY moved 12% in 3 weeks\n"
            "• Nikkei: -12% in a single day\n"
            "• $SPY: -6% before rebound\n"
            "• Estimated carry trade: $4 TRILLION\n\n"
            "**🎯 Take:** When you see violent unexplained selloffs, ask: who's being forced to sell?\n\n"
            "**💬 What's the next carry trade unwind? If BOJ hikes again, what breaks?**"
        ),
        (
            "**⚠️ AI Valuations: This Time Is Different (Said Everyone Before a Crash)**\n\n"
            "$NVDA at 65x sales. $MSFT at 35x earnings for 12% growth. $PLTR at 20x revenue. Sound familiar?\n\n"
            "**💡 The Insight:**\n"
            "In 2000, $CSCO hit 40x sales. The internet was real — the valuations weren't. $CSCO took 15 years to recover. AI is transformative. That doesn't mean today's prices are justified.\n\n"
            "**🔢 By The Numbers:**\n"
            "• Magnificent 7 = 30% of $SPY market cap\n"
            "• AI capex: $200B+ in 2025, revenue? Unclear\n"
            "• Top 5 AI stocks: avg P/E of 55x vs S&P 500 at 21x\n\n"
            "**🎯 Take:** The winners will be huge. But 80% of today's 'AI stocks' won't survive the correction.\n\n"
            "**💬 Which AI stock do you think is actually worth its price? Reply with $TICKER**"
        ),
        (
            "**🛡️ The Portfolio Armor Test: How Protected Are You?**\n\n"
            "Most investors think they're diversified. They're not. Correlation goes to 1 in a crisis.\n\n"
            "**💡 The Insight:**\n"
            "If your 'diversification' is $AAPL + $MSFT + $GOOGL + $AMZN + $NVDA, you have one bet: US tech megacap. When $SPY drops 20%, these all drop 25%+. Real diversification means owning things that zig when equities zag.\n\n"
            "**🔢 By The Numbers:**\n"
            "• Top 10 $SPY stocks = 35% of index\n"
            "• 60/40 portfolio correlation: 0.6 (not the 0.2 people assume)\n"
            "• Gold + TLT + $SPY: only combo with <0.3 correlation in 2022\n\n"
            "**🎯 Take:** Stress-test your portfolio. What happens if $SPY drops 30%? If your answer is 'I lose 30%,' you're not diversified.\n\n"
            "**💬 What's your non-correlated hedge? Gold, bonds, cash, or something else?**"
        ),
        (
            "**📉 Earnings Season Reality Check**\n\n"
            "Companies are beating estimates. Markets are rallying. Everything looks great — until you look closer.\n\n"
            "**💡 The Insight:**\n"
            "Earnings 'beats' are manufactured. 78% of companies beat EPS estimates, but that's because estimates were cut 15% before reporting. Revenue growth is the real number — and it's slowing.\n\n"
            "**🔢 By The Numbers:**\n"
            "• EPS beat rate: 78% (historical avg: 73%)\n"
            "• Pre-season estimate cuts: -15% average\n"
            "• Revenue growth S&P 500: 4% (vs 8% last year)\n"
            "• Forward P/E: 20.5x (10-year avg: 17.5x)\n\n"
            "**🎯 Take:** Don't celebrate beats from lowered bars. Watch revenue, not EPS. Watch guidance, not backwards-looking results.\n\n"
            "**💬 Which company's earnings surprised you most this season? Bull or bear?**"
        ),
    ]
    base = posts[day_idx % len(posts)]
    footer = (
        "\n\n━━━━━━━━━━━━━━━━━━\n"
        "📱 Free consult @BroadInvestBot | 📐 Full analysis t.me/BroadFSC\n"
        "📖 Deep dives: " + links["substack"] + "\n"
        "⚠️ Not financial advice\n\n"
        "#Investing #Trading #MarketAnalysis #StockMarket #Finance"
    )
    combined = base + footer
    if len(combined) > 1900:
        combined = combined[:1897] + "..."
    return combined


# ============================================================
# LinkedIn Poster
# ============================================================
def post_linkedin(text):
    """Post to LinkedIn using access token."""
    if not LINKEDIN_ACCESS_TOKEN:
        print("  LinkedIn: Missing LINKEDIN_ACCESS_TOKEN")
        return False
    
    # Get user's LinkedIn person ID (urn)
    headers = {"Authorization": "Bearer " + LINKEDIN_ACCESS_TOKEN, "Content-Type": "application/json"}
    try:
        r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=10)
        if r.status_code != 200:
            print("  LinkedIn: Auth FAIL - " + str(r.status_code))
            return False
        user_data = r.json()
        person_urn = user_data.get("sub", "")
    except Exception as e:
        print("  LinkedIn: FAIL - " + str(e))
        return False
    
    if not person_urn:
        print("  LinkedIn: Could not get person URN")
        return False
    
    # Create post
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    payload = {
        "author": "urn:li:person:" + person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "ARTICLE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        r = requests.post(post_url, headers=headers, json=payload, timeout=15)
        if r.status_code == 201:
            print("  LinkedIn: Posted successfully!")
            return True
        else:
            print("  LinkedIn: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            return False
    except Exception as e:
        print("  LinkedIn: FAIL - " + str(e))
        return False


# ============================================================
# Bluesky Poster (AT Protocol)
# ============================================================
PDS_URL = "https://bsky.social/xrpc"


def post_bluesky(text):
    """Post to Bluesky using AT Protocol API."""
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        print("  Bluesky: Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD")
        return False

    # Step 1: Create session
    try:
        session_resp = requests.post(
            f"{PDS_URL}/com.atproto.server.createSession",
            json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
            timeout=15,
        )
        if session_resp.status_code != 200:
            print("  Bluesky: Auth FAIL HTTP " + str(session_resp.status_code) + " - " + session_resp.text[:200])
            return False
        session = session_resp.json()
        access_jwt = session["accessJwt"]
        did = session["did"]
    except Exception as e:
        print("  Bluesky: Auth FAIL - " + str(e))
        return False

    # Step 2: Create post (max 300 graphemes)
    if len(text) > 290:
        text = text[:287] + "..."

    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    try:
        r = requests.post(
            f"{PDS_URL}/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + access_jwt},
            json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
            timeout=15,
        )
        if r.status_code in [200, 201]:
            uri = r.json().get("uri", "")
            print("  Bluesky: Posted! URI: " + str(uri))
            if HAS_ANALYTICS:
                log_post(platform="bluesky", post_type="post", content_preview=text[:100], post_id=str(uri), status="success")
            return True
        else:
            print("  Bluesky: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            if HAS_ANALYTICS:
                log_post(platform="bluesky", post_type="post", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print("  Bluesky: FAIL - " + str(e))
        if HAS_ANALYTICS:
            log_post(platform="bluesky", post_type="post", content_preview=text[:100], status="failed", error_msg=str(e)[:200])
        return False


def _post_bluesky_thread(posts):
    """Post a Bluesky thread (multiple posts linked by replies).

    Args:
        posts: list of strings, each ≤300 graphemes.
    """
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        print("  Bluesky thread: Missing credentials")
        return False

    if not posts:
        return False

    # Create session once
    try:
        session_resp = requests.post(
            f"{PDS_URL}/com.atproto.server.createSession",
            json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
            timeout=15,
        )
        if session_resp.status_code != 200:
            print("  Bluesky thread: Auth FAIL HTTP " + str(session_resp.status_code))
            return False
        session = session_resp.json()
        access_jwt = session["accessJwt"]
        did = session["did"]
    except Exception as e:
        print("  Bluesky thread: Auth FAIL - " + str(e))
        return False

    parent_uri = None
    parent_cid = None

    for i, text in enumerate(posts):
        if len(text) > 290:
            text = text[:287] + "..."

        record = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        # Add reply reference for all posts after the first
        if parent_uri and parent_cid:
            record["reply"] = {
                "root": {"uri": root_uri, "cid": root_cid},
                "parent": {"uri": parent_uri, "cid": parent_cid},
            }

        try:
            r = requests.post(
                f"{PDS_URL}/com.atproto.repo.createRecord",
                headers={"Authorization": "Bearer " + access_jwt},
                json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
                timeout=15,
            )
            if r.status_code in [200, 201]:
                resp_data = r.json()
                uri = resp_data.get("uri", "")
                cid = resp_data.get("cid", "")
                parent_uri = uri
                parent_cid = cid
                # Set root to the first post
                if i == 0:
                    root_uri = uri
                    root_cid = cid
                print("  Bluesky thread [" + str(i+1) + "/" + str(len(posts)) + "]: Posted! URI: " + str(uri))
                if HAS_ANALYTICS and i == 0:
                    log_post(platform="bluesky", post_type="thread", content_preview=text[:100], post_id=str(uri), status="success")
            else:
                print("  Bluesky thread [" + str(i+1) + "/" + str(len(posts)) + "]: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
                return False
        except Exception as e:
            print("  Bluesky thread [" + str(i+1) + "/" + str(len(posts)) + "]: FAIL - " + str(e))
            return False

    return True


def generate_bluesky_content():
    """Generate a deep-dive Bluesky analysis thread in today's analyst persona voice.

    Returns either a single post or a list of posts (thread).
    When returning a thread, the caller (post_bluesky) handles posting each reply.
    """
    if not GROQ_API_KEY:
        return get_fallback_bluesky()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")

        persona = get_daily_persona(platform_shift=3)
        link = get_platform_link("bluesky")
        link_line = "\n- Include this link in the LAST post: " + link if link and not link.startswith("Follow") else "\n- Do NOT include any links"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE Bluesky thread (3-4 posts) for " + day + ", " + date_str + ".\n"
                    "Focus on US stocks, global macro, or investment strategy.\n\n"
                    "Hook rule: " + persona["hook"] + "\n\n"
                    "Thread structure:\n"
                    "Post 1/4 — HOOK + THE SETUP: Bold opening claim + 2-3 sentences of context\n"
                    "Post 2/4 — THE INSIGHT: Your unique angle, data-driven reasoning, what others miss\n"
                    "Post 3/4 — BY THE NUMBERS: 2-3 specific data points with context\n"
                    "Post 4/4 — THE TAKEAWAY: One clear conclusion + call to action\n\n"
                    "Rules:\n"
                    "- Each post MAXIMUM 280 characters (strict Bluesky limit)\n"
                    "- Start each post with its number: 1/, 2/, 3/, 4/\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Include 3-4 specific numbers across the whole thread\n"
                    "- End LAST post with: #Investing #Trading"
                    + link_line + "\n"
                    "- In LAST post, also include: 📱 Free consult: https://t.me/BroadInvestBot\n"
                    "- Do NOT promise returns\n"
                    "- Separate each post with '---POST_BREAK---' on its own line"
                )
            }],
            max_tokens=600,
            temperature=0.9
        )
        raw = response.choices[0].message.content.strip()
        print("  Bluesky persona: " + persona["name"] + " (" + str(len(raw)) + " chars total)")

        # Parse thread: split by delimiter
        if "---POST_BREAK---" in raw:
            posts = [p.strip() for p in raw.split("---POST_BREAK---") if p.strip()]
            # Validate each post ≤280 chars
            validated = []
            for p in posts:
                if len(p) > 280:
                    # Hard-truncate
                    validated.append(p[:277] + "...")
                else:
                    validated.append(p)
            return validated
        else:
            # AI didn't use delimiter, treat as single post
            if len(raw) > 280:
                raw = raw[:277] + "..."
            return [raw]
    except Exception as e:
        print("  AI Bluesky generation failed: " + str(e))
        return get_fallback_bluesky()


def get_fallback_bluesky():
    """Fallback Bluesky thread content with deep analysis."""
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    links = get_tracked_links("bluesky")
    threads = [
        [
            "1/ The smart money isn't buying the dip anymore. They're buying puts.",
            "2/ When hedging outpaces speculation, a regime change is coming. Put/call ratios at 2-year highs. Institutions are positioning for volatility — not recovery.",
            "3/ Watch the VIX. If it breaks above 25 and stays there, the regime shift is confirmed. Until then, trade small and stay nimble. " + links['hub'] + " #Investing #Trading",
        ],
        [
            "1/ Everyone thinks inflation is dead. Core services CPI says otherwise.",
            "2/ The last mile of disinflation is always the hardest. Shelter costs are sticky. Wage growth is still above the Fed's comfort zone.",
            "3/ Markets aren't pricing this — they're pricing 3 cuts. If we get 1 or 0, that's a repricing event. Position for the gap. " + links['hub'] + " #Investing #Trading",
        ],
        [
            "1/ Myth: 'Stocks always go up long-term.' Reality check: The Nikkei took 34 years to reclaim its 1989 high.",
            "2/ Time horizon matters. Market selection matters more. Not every market is the S&P 500. Diversify globally or pay the price.",
            "3/ The lesson? Buy quality, diversify across markets, and never assume your timeframe matches the market's. " + links['hub'] + " #Investing #Trading",
        ],
    ]
    return threads[day_idx % len(threads)]


# ============================================================
# LINE Official Account Poster
# ============================================================
def post_line(text, lang="en"):
    """Post to LINE Official Account via Messaging API.
    
    Uses Flex Message with CTA button for best engagement.
    Falls back to plain text if Flex fails.
    """
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("  LINE: Missing LINE_CHANNEL_ACCESS_TOKEN")
        return False

    try:
        from line_poster import build_market_briefing_flex, broadcast_flex, broadcast_text
    except ImportError:
        print("  LINE: line_poster.py not found, using direct API")
        from line_poster import broadcast_text as _bt
        return _bt(text)

    # Try Flex Message first (richer UI)
    titles = {
        "en": "\U0001f4c8 Daily Market Briefing",
        "jp": "\U0001f4c8 毎日マーケットレポート",
        "zh-tw": "\U0001f4c8 每日市場速報",
    }
    title = titles.get(lang, titles["en"])
    flex = build_market_briefing_flex(title, text, lang)
    success = broadcast_flex(title, flex)

    # Fallback to plain text if Flex fails
    if not success:
        print("  LINE: Flex failed, trying plain text...")
        success = broadcast_text(text)

    return success


def generate_line_content(lang="en"):
    """Generate a LINE market briefing post."""
    if not GROQ_API_KEY:
        return get_fallback_line(lang)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        lang_instruction = {
            "en": "Write in English.",
            "jp": "Write in Japanese (日本語). Use professional financial terminology (日経平均, ドル円, 新NISA).",
            "zh-tw": "Write in Traditional Chinese (繁體中文). Use Taiwan market terminology (台股, 美股, 台積電, 法說會).",
        }.get(lang, "Write in English.")

        links = get_tracked_links("line")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write a concise daily market briefing for LINE Official Account.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- " + lang_instruction + "\n"
                    "- Maximum 400 characters\n"
                    "- Include 2-3 specific market observations\n"
                    "- Use bullet points for readability\n"
                    "- Professional but engaging tone\n"
                    "- Do NOT include any links (they go in the CTA button)\n"
                    "- Do mention: 'Free consult via Telegram: @BroadInvestBot'\n"
                    "- Do NOT promise guaranteed returns\n"
                    "- Do NOT add hashtags"
                )
            }],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI LINE generation failed: " + str(e))
        return get_fallback_line(lang)


def get_fallback_line(lang="en"):
    """Fallback LINE content."""
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")

    fallbacks = {
        "en": (
            "Daily Market Briefing | " + date_str + "\n\n"
            "Key factors to watch today:\n"
            "\u2022 Central bank policy signals (Fed, ECB, BOJ)\n"
            "\u2022 Global equity futures direction\n"
            "\u2022 Key economic data releases\n"
            "\u2022 Geopolitical risk premiums in commodities\n\n"
            "Stay ahead with daily briefings from BroadFSC."
        ),
        "jp": (
            "毎日マーケットレポート | " + date_str + "\n\n"
            "本日の注目ポイント:\n"
            "\u2022 日銀・FRB・ECBの政策シグナル\n"
            "\u2022 グローバル株価先物の方向感\n"
            "\u2022 主要経済指標の発表予定\n"
            "\u2022 コモディティの地政学リスク\n\n"
            "BroadFSCの毎日レポートで情報優位を。"
        ),
        "zh-tw": (
            "每日市場速報 | " + date_str + "\n\n"
            "今日關注重點:\n"
            "\u2022 央行政策信號（Fed、ECB、日銀）\n"
            "\u2022 全球股指期貨方向\n"
            "\u2022 重要經濟數據公布\n"
            "\u2022 大宗商品地緣風險溢價\n\n"
            "BroadFSC每日盤前速報，掌握市場先機。"
        ),
    }
    return fallbacks.get(lang, fallbacks["en"])


# ============================================================
# Content Generation
# ============================================================
def generate_tweet_content():
    """Generate a deep-dive Twitter thread in today's analyst persona voice.

    Returns a list of tweet strings (thread), each ≤280 characters.
    The caller (main) should use post_tweet_thread() to post them.
    """
    if not GROQ_API_KEY:
        return get_fallback_tweet()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")

        persona = get_daily_persona(platform_shift=0)
        link = get_platform_link("twitter")
        links = get_tracked_links("twitter")
        link_line = f"\n- Include this link in the LAST tweet: {link}" if link and not link.startswith("Learn") else "\n- Do NOT include any links (link in bio instead)"
        substack_line = f"\n- Also add in LAST tweet: 'Deep analysis: {links['substack']}'" if "substack" in links else ""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE Twitter thread (3-5 tweets) about today's markets (" + day + ", " + date_str + ").\n"
                    "Focus on US stocks, macro, or investment strategy.\n\n"
                    "Hook rule: " + persona["hook"] + "\n\n"
                    "Thread structure:\n"
                    "Tweet 1 — HOOK + THE SETUP: Bold opening claim that stops scrolling + 1-2 sentences of context\n"
                    "Tweet 2 — THE INSIGHT: Your unique angle, data-driven reasoning, what consensus misses\n"
                    "Tweet 3 — BY THE NUMBERS: 2-3 specific data points with context\n"
                    "Tweet 4 — THE TAKEAWAY: One clear conclusion + what to watch next\n\n"
                    "Rules:\n"
                    "- Each tweet MAXIMUM 280 characters (strict Twitter limit)\n"
                    "- Start each tweet with its number: 1/, 2/, 3/, 4/\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Include 3-4 specific numbers across the whole thread\n"
                    "- End LAST tweet with: #Investing #Trading"
                    + link_line + "\n"
                    "- In LAST tweet, also include: 📱 Free consult: https://t.me/BroadInvestBot\n"
                    "- End LAST tweet with interactive question: 'Your take? Reply with $TICKER'"
                    "- Use $TICKER format for stock mentions (e.g, $AAPL, $TSLA)"
                    "- Invite: 'Bull or Bear? B / bearish'"
                    "- Do NOT promise returns or give direct financial advice\n"
                    "- NEVER start with 'Market update', 'Key themes', or 'Markets are'\n"
                    "- Separate each tweet with '---TWEET_BREAK---' on its own line"
                    + substack_line
                )
            }],
            max_tokens=600,
            temperature=0.9
        )
        raw = response.choices[0].message.content.strip()
        print("  Twitter persona: " + persona["name"] + " (" + str(len(raw)) + " chars total)")

        # Parse thread: split by delimiter
        if "---TWEET_BREAK---" in raw:
            tweets = [t.strip() for t in raw.split("---TWEET_BREAK---") if t.strip()]
            # Validate each tweet ≤280 chars
            validated = []
            for t in tweets:
                if len(t) > 280:
                    validated.append(t[:277] + "...")
                else:
                    validated.append(t)
            return validated
        else:
            # AI didn't use delimiter, treat as single tweet
            if len(raw) > 280:
                raw = raw[:277] + "..."
            return [raw]
    except Exception as e:
        print("  AI tweet generation failed: " + str(e))
        return get_fallback_tweet()


def generate_linkedin_content():
    """Generate a LinkedIn article-style post."""
    if not GROQ_API_KEY:
        return get_fallback_linkedin()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        links = get_tracked_links("linkedin")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a senior market strategist at Broad Investment Securities. "
                    "Write a LinkedIn post about today's market outlook.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- Professional tone, 200-400 words\n"
                    "- Include 2-3 specific market observations\n"
                    "- Reference macro trends (Fed, ECB, geopolitics)\n"
                    "- End with: 'For daily market briefings, visit " + links["website"] + "'\n"
                    "- Also add: '📱 Free consult: https://t.me/BroadInvestBot | Follow: https://t.me/BroadFSC'\n"
                    "- Do NOT promise returns or give specific buy/sell advice"
                )
            }],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI LinkedIn generation failed: " + str(e))
        return get_fallback_linkedin()


def get_fallback_tweet():
    """Fallback tweet thread content with deep analysis hooks."""
    links = get_tracked_links("twitter")
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    # Each entry is a thread (list of tweets)
    threads = [
        [
            "1/ The 10Y-2Y spread just inverted again. Nobody's talking about it — but they should be.",
            "2/ Last 3 times this happened? Recession within 14 months. Every. Single. Time. The bond market doesn't lie — it just speaks slowly.",
            "3/ Right now: equities are pricing in a soft landing. Bonds are pricing in a hard one. They can't both be right.",
            "4/ Watch the 10Y yield. If it breaks below 4.0%, the market is telling you something. Position accordingly. " + links['hub'] + " #Investing #Trading",
        ],
        [
            "1/ Unpopular opinion: most 'diversified' portfolios aren't diversified at all.",
            "2/ If everything dropped together in 2022, you're not diversified — you're just holding different names for the same bet. True diversification means some things zig when others zag.",
            "3/ The fix? Add uncorrelated assets: long-duration bonds, gold, managed futures. Not 5 tech stocks and an S&P fund.",
            "4/ Correlation goes to 1 in a crisis — unless you build for it. Think about your portfolio's stress test. " + links['hub'] + " #Investing #Trading",
        ],
        [
            "1/ S&P 500 is up. But fewer than 30% of stocks are above their 200-day MA. This isn't a bull market — it's a narrow float.",
            "2/ The 'magnificent 7' are carrying the index. When breadth is this thin, one bad earnings season can flip everything.",
            "3/ Smart money is watching the advance-decline line, not the S&P level. When A/D diverges from price, a reversal is usually coming.",
            "4/ Don't confuse a rising index with a healthy market. Look under the hood. " + links['hub'] + " #Investing #Trading",
        ],
    ]
    return threads[day_idx % len(threads)]


def get_fallback_linkedin():
    """Fallback LinkedIn content."""
    links = get_tracked_links("linkedin")
    return (
        "Global Market Outlook\n\n"
        "As markets navigate through a period of heightened macro uncertainty, "
        "several key themes deserve investor attention:\n\n"
        "1. Central Bank Policy Divergence - The Fed, ECB, and BOJ continue to "
        "calibrate monetary policy at different paces, creating cross-currency "
        "and cross-border capital flow implications.\n\n"
        "2. Geopolitical Risk Premium - Ongoing developments continue to influence "
        "commodity markets and supply chain dynamics across multiple sectors.\n\n"
        "3. Earnings Season Dynamics - Corporate earnings provide real-time signals "
        "about the health of the global economy and sector-specific trends.\n\n"
        "At Broad Investment Securities, we provide daily pre-market briefings "
        "covering all major global markets. Stay ahead of market moves.\n\n"
        f"For daily market briefings, visit {links['website']}\n\n"
        "#Investing #MarketAnalysis #GlobalMarkets"
    )


def notify_telegram(message):
    """Send notification to Telegram."""
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": message}, timeout=10)
    except Exception:
        pass


# ============================================================
# TikTok Poster (via Postproxy API)
# ============================================================
def post_tiktok(text, image_urls=None, video_url=None):
    """Post to TikTok via Postproxy API. Supports image carousel or video."""
    if not POSTPROXY_API_KEY:
        print("  TikTok: Missing POSTPROXY_API_KEY")
        return False

    api_url = "https://api.postproxy.dev/api/posts"
    headers = {
        "Authorization": "Bearer " + POSTPROXY_API_KEY,
        "Content-Type": "application/json",
    }

    # Determine mode: video if video URL provided, otherwise image
    if video_url:
        payload = {
            "post": {"body": text},
            "profiles": ["tiktok"],
            "media": [video_url],
            "platforms": {
                "tiktok": {
                    "format": "video",
                    "privacy_status": "PUBLIC_TO_EVERYONE",
                    "disable_comment": False,
                    "disable_duet": False,
                    "disable_stitch": False,
                }
            }
        }
    elif image_urls:
        payload = {
            "post": {"body": text},
            "profiles": ["tiktok"],
            "media": image_urls,
            "platforms": {
                "tiktok": {
                    "format": "image",
                    "privacy_status": "PUBLIC_TO_EVERYONE",
                    "auto_add_music": True,
                    "disable_comment": False,
                }
            }
        }
    else:
        print("  TikTok: No media provided (need image_urls or video_url)")
        return False

    try:
        r = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if r.status_code in [200, 201]:
            post_id = r.json().get("id", "unknown")
            print("  TikTok: Posted! ID: " + str(post_id))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:400])
            return False
    except Exception as e:
        print("  TikTok: FAIL - " + str(e))
        return False


def generate_tiktok_content():
    """Generate a TikTok-optimized caption."""
    if not GROQ_API_KEY:
        return get_fallback_tiktok()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        links = get_tracked_links("tiktok")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a financial content creator for BroadFSC on TikTok. "
                    "Write an engaging short caption for a market insight post.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- Maximum 300 characters\n"
                    "- Hook in the first line\n"
                    "- 2-3 relevant hashtags\n"
                    "- Add link: " + links["hub"] + "\n"
                    "- Also add: 📱 Free consult: https://t.me/BroadInvestBot\n"
                    "- Do NOT promise guaranteed returns"
                )
            }],
            max_tokens=120,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI TikTok generation failed: " + str(e))
        return get_fallback_tiktok()


def get_fallback_tiktok():
    """Fallback TikTok content."""
    links = get_tracked_links("tiktok")
    captions = [
        "Want to invest smarter in 2026? Here's what the pros watch every morning \U0001f4c8 "
        f"Daily global market briefings - FREE! {links['hub']} #Investing #StockMarket #FinanceTips",

        "Markets move FAST. Don't get caught off guard \u26a1 "
        "Pre-market briefings for Asia, Europe, Middle East & Americas. "
        f"Subscribe free: {links['hub']} #Trading #Investing #MarketAnalysis",

        "3 things smart investors check before markets open \U0001f4ca "
        "1. Overnight futures 2. Central bank signals 3. Key economic data. "
        f"Get all this daily at BroadFSC {links['hub']} #Investing #StockMarket #WealthBuilding",
    ]
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(captions)
    return captions[idx]


# ============================================================
# Medium & Substack — Long-form Article Content
# ============================================================

def generate_medium_content():
    """Generate a long-form article for Medium (markdown format).

    Returns:
        dict with 'title', 'content', 'tags' — used by medium_substack_poster.py
    """
    if not GROQ_API_KEY:
        return get_fallback_medium()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")

        persona = get_daily_persona(platform_shift=3)
        tags = " ".join(persona["hashtags"])
        links = get_tracked_links("medium")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE investment analysis article for Medium on " + day + ", " + date_str + ".\n"
                    "Focus on US stocks, global macro, or investment strategy.\n\n"
                    "Hook rule: " + persona["hook"] + "\n\n"
                    "OUTPUT FORMAT — return EXACTLY this JSON structure:\n"
                    '{\"title\": \"...\", \"content\": \"...(markdown)...\", \"tags\": [\"tag1\", \"tag2\", \"tag3\"]}\n\n'
                    "ARTICLE STRUCTURE:\n"
                    "1. **HOOK** — A bold opening paragraph\n"
                    "2. **THE BIG PICTURE** — 4-6 sentences of macro context\n"
                    "3. **DEEP DIVE** — 3-5 detailed paragraphs\n"
                    "4. **BY THE NUMBERS** — 5-8 specific data points\n"
                    "5. **WHAT SMART MONEY IS DOING** — Institutional positioning\n"
                    "6. **THE CONTRARIAN CASE** — What if consensus is wrong?\n"
                    "7. **ACTIONABLE TAKEAWAYS** — 3-5 bullet points\n"
                    "8. **CLOSING THOUGHT** — One powerful insight\n\n"
                    "Rules:\n"
                    "- Article body: 1500-2500 words in markdown\n"
                    "- Use ## for headers, **bold** for emphasis\n"
                    "- Include 8-12 specific numbers\n"
                    "- Stay in character as " + persona["name"] + "\n"
                    "- End with: ⚠️ *Not financial advice*\n"
                    "- Tags: 3-5 tags without # symbol\n"
                    "- Title: Under 80 characters\n"
                    "- Include: Subscribe at " + links["telegram"] + " | 📱 Free consult: https://t.me/BroadInvestBot | Learn free at " + links["hub"] + "\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=4000,
            temperature=0.85
        )

        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        article = json.loads(raw)
        if not all(k in article for k in ["title", "content"]):
            raise ValueError("Missing required fields")

        if "tags" not in article or not article["tags"]:
            article["tags"] = ["investing", "trading", "stockmarket"]

        print("  Medium article: '" + article["title"] + "' (" + str(len(article["content"])) + " chars)")
        return article

    except json.JSONDecodeError as e:
        print("  Medium article JSON parse failed: " + str(e))
        return get_fallback_medium()
    except Exception as e:
        print("  Medium article generation failed: " + str(e))
        return get_fallback_medium()


def get_fallback_medium():
    """Fallback Medium article."""
    links = get_tracked_links("medium")
    return {
        "title": "The Yield Curve Is Speaking — Are You Listening?",
        "content": (
            "## The Signal Nobody Wants to Hear\n\n"
            "The 10Y-2Y Treasury spread has been inverted for over 18 months. "
            "In the last 50 years, every single recession was preceded by this signal. "
            "We're in the lag window right now.\n\n"
            "## The Big Picture\n\n"
            "Markets are priced for perfection. The S&P 500 trades at 21x forward earnings. "
            "Credit spreads sit near historic tights. The VIX refuses to break above 15.\n\n"
            "But the bond market is telling a different story.\n\n"
            "## By The Numbers\n\n"
            "- **10Y-2Y Spread:** -0.35% (still inverted)\n"
            "- **S&P 500 P/E:** 21.2x forward (10-year avg: 17.8x)\n"
            "- **VIX:** 14.2 (bottom 10th percentile)\n"
            "- **Commercial RE Delinquencies:** Up 2.1x YoY\n"
            "- **Consumer Savings Rate:** 5.3% → 3.6% in 6 months\n\n"
            "## Actionable Takeaways\n\n"
            "- Reduce leverage\n"
            "- Raise cash (6-month T-bills yield 5.3%)\n"
            "- Own quality companies with strong balance sheets\n"
            "- Add uncorrelated assets\n\n"
            "---\n\n"
            "Subscribe for daily briefings: " + links["telegram"] + "\n"
            "Learn free: " + links["hub"] + "\n\n"
            "⚠️ *Not financial advice. Always do your own research.*"
        ),
        "tags": ["investing", "bonds", "recession", "macro"],
    }


def generate_substack_content():
    """Generate a long-form article for Substack (markdown format).

    Returns:
        dict with 'title', 'subtitle', 'content', 'tags'
    """
    if not GROQ_API_KEY:
        return get_fallback_substack()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")

        persona = get_daily_persona(platform_shift=1)
        tags = " ".join(persona["hashtags"])
        links = get_tracked_links("substack")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE investment analysis article for Substack newsletter on " + day + ", " + date_str + ".\n"
                    "Focus on US stocks, global macro, or investment strategy.\n\n"
                    "Hook rule: " + persona["hook"] + "\n\n"
                    "OUTPUT FORMAT — return EXACTLY this JSON structure:\n"
                    '{\"title\": \"...\", \"subtitle\": \"...\", \"content\": \"...(markdown)...\", \"tags\": [\"tag1\", \"tag2\"]}\n\n'
                    "ARTICLE STRUCTURE:\n"
                    "1. **HOOK** — Bold opening paragraph\n"
                    "2. **THE BIG PICTURE** — Macro context\n"
                    "3. **DEEP DIVE** — Detailed analysis (3-5 paragraphs)\n"
                    "4. **BY THE NUMBERS** — 5-8 data points\n"
                    "5. **WHAT SMART MONEY IS DOING** — Institutional moves\n"
                    "6. **THE CONTRARIAN CASE** — Challenge consensus\n"
                    "7. **ACTIONABLE TAKEAWAYS** — 3-5 bullets\n"
                    "8. **CLOSING THOUGHT** — Final insight\n\n"
                    "Rules:\n"
                    "- Article body: 1500-2500 words in markdown\n"
                    "- Use ## for headers, **bold** for emphasis\n"
                    "- Include 8-12 specific numbers\n"
                    "- Stay in character as " + persona["name"] + "\n"
                    "- End with: ⚠️ *Not financial advice*\n"
                    "- Tags: 3-5 tags without #\n"
                    "- Title: Under 80 chars, Subtitle: Under 120 chars\n"
                    "- Include: Subscribe at " + links["telegram"] + " | 📱 Free consult: https://t.me/BroadInvestBot | Learn free at " + links["hub"] + "\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=4000,
            temperature=0.85
        )

        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        article = json.loads(raw)
        if not all(k in article for k in ["title", "content"]):
            raise ValueError("Missing required fields")

        if "tags" not in article or not article["tags"]:
            article["tags"] = ["investing", "newsletter", "markets"]
        if "subtitle" not in article:
            article["subtitle"] = ""

        print("  Substack article: '" + article["title"] + "' (" + str(len(article["content"])) + " chars)")
        return article

    except json.JSONDecodeError as e:
        print("  Substack article JSON parse failed: " + str(e))
        return get_fallback_substack()
    except Exception as e:
        print("  Substack article generation failed: " + str(e))
        return get_fallback_substack()


def get_fallback_substack():
    """Fallback Substack article."""
    links = get_tracked_links("substack")
    return {
        "title": "AI Stocks at All-Time Highs: Brilliance or Bubble?",
        "subtitle": "Separating genuine value from momentum in the AI trade",
        "content": (
            "## The Trillion-Dollar Question\n\n"
            "NVIDIA just crossed $3 trillion in market cap. The Magnificent 7 now represent "
            "30% of the S&P 500. Is this the dawn of an AI-powered productivity revolution, "
            "or the greatest momentum trap of our generation?\n\n"
            "## The Bull Case Is Real\n\n"
            "AI is generating real revenue. Cloud AI services grew 85% YoY. Enterprise adoption "
            "jumped from 35% to 65% in 12 months. This isn't vaporware.\n\n"
            "## But Valuations Are Stretched\n\n"
            "NVIDIA trades at 65x trailing earnings. The last time a dominant chip company "
            "traded at these levels was Cisco in 2000.\n\n"
            "## By The Numbers\n\n"
            "- **Mag 7 Weight in S&P:** 30.2% (historic high)\n"
            "- **NVIDIA P/E:** 65x trailing, 35x forward\n"
            "- **AI Revenue Growth:** 85% YoY\n"
            "- **Enterprise AI Adoption:** 65% (up from 35%)\n"
            "- **AI ETF Inflows:** $12B in Q1\n\n"
            "## Actionable Takeaways\n\n"
            "- Trim positions that have 3x+ — lock in gains\n"
            "- Look downstream: AI infrastructure, not just chips\n"
            "- Value exists at 10-12x earnings outside AI\n\n"
            "---\n\n"
            "Subscribe for daily briefings: " + links["telegram"] + "\n"
            "Learn free: " + links["hub"] + "\n\n"
            "⚠️ *Not financial advice. Always do your own research.*"
        ),
        "tags": ["AI", "stocks", "valuation", "growth"],
    }


def post_medium_article(article):
    """Post article to Medium via browser automation (calls medium_substack_poster.py)."""
    # 检测 Playwright 是否可用（GitHub Actions 主步骤未安装）
    _playwright_available = False
    try:
        import playwright
        _playwright_available = True
    except ImportError:
        pass

    if not _playwright_available:
        print("  Medium: Playwright 未安装，跳过（由 dedicated workflow step 处理）")
        return False, ""

    try:
        from medium_substack_poster import post_medium
        success, url = post_medium(article)
        return success, url
    except ImportError:
        print("  Medium: medium_substack_poster.py not found, running standalone...")
        # Run as subprocess
        try:
            import subprocess
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medium_substack_poster.py")
            result = subprocess.run(
                [sys.executable, script, "--medium"],
                capture_output=True, text=True, timeout=300,
                env={**os.environ, "MEDIUM_EMAIL": MEDIUM_EMAIL, "MEDIUM_PASSWORD": MEDIUM_PASSWORD,
                     "GROQ_API_KEY": GROQ_API_KEY}
            )
            if result.returncode == 0:
                print("  Medium poster completed")
                return True, ""
            else:
                print("  Medium poster error: " + result.stderr[:200])
                return False, ""
        except Exception as e:
            print("  Medium poster failed: " + str(e))
            return False, ""
    except Exception as e:
        print("  Medium posting failed: " + str(e))
        return False, ""


def post_substack_article(article):
    """Post article to Substack via browser automation (calls substack_poster.py)."""
    # 检测 Playwright 是否可用（GitHub Actions 主步骤未安装）
    _playwright_available = False
    try:
        import playwright
        _playwright_available = True
    except ImportError:
        pass

    if not _playwright_available:
        print("  Substack: Playwright 未安装，跳过（由 dedicated workflow step 处理）")
        return False, ""

    try:
        from substack_poster import post_substack
        success, url = post_substack(article)
        return success, url
    except ImportError:
        print("  Substack: substack_poster.py not found, running standalone...")
        # Run as subprocess
        try:
            import subprocess
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substack_poster.py")
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True, text=True, timeout=300,
                env={**os.environ, "SUBSTACK_EMAIL": SUBSTACK_EMAIL, "SUBSTACK_PASSWORD": SUBSTACK_PASSWORD,
                     "SUBSTACK_PUB_URL": SUBSTACK_PUB_URL, "GROQ_API_KEY": GROQ_API_KEY}
            )
            if result.returncode == 0:
                print("  Substack poster completed")
                return True, ""
            else:
                print("  Substack poster error: " + result.stderr[:200])
                return False, ""
        except Exception as e:
            print("  Substack poster failed: " + str(e))
            return False, ""
    except Exception as e:
        print("  Substack posting failed: " + str(e))
        return False, ""


# ============================================================
# Threads Content Generation (Meta API)
# ============================================================
def generate_threads_content():
    """Generate a Threads thread in today's persona voice.

    Threads uses Meta API, supports threads (reply chains).
    Max 500 chars per post. Free API: 250 posts/day.
    """
    if not GROQ_API_KEY:
        return "Market update: Key levels to watch. Data over drama. #Investing #Trading"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")
        persona = get_daily_persona(platform_shift=4)
        links = get_tracked_links("threads")
        link_line = "\n- Include this link in the LAST post: " + links["substack"] if links.get("substack") else ""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE Threads thread (3-4 posts) for " + day + ", " + date_str + ".\n"
                    "Focus on US stocks, global macro, or investment strategy.\n\n"
                    "Hook: " + persona["hook"] + "\n\n"
                    "Thread structure:\n"
                    "Post 1/4 — HOOK + THE SETUP\n"
                    "Post 2/4 — THE INSIGHT\n"
                    "Post 3/4 — BY THE NUMBERS\n"
                    "Post 4/4 — THE TAKEAWAY\n\n"
                    "Rules:\n"
                    "- Each post MAX 500 characters\n"
                    "- Start each with number: 1/, 2/, 3/, 4/\n"
                    "- Stay in character as " + persona["name"] + "\n"
                    "- Include 3-4 specific numbers\n"
                    "- End LAST post with: #Investing #Trading"
                    + link_line + "\n"
                    "- In LAST post, also include: 📱 Free consult: https://t.me/BroadInvestBot\n"
                    "- End LAST post with interactive question: 'Your take? Drop $TICKER below'"
                    "- Use $TICKER format for stock mentions (e.g, $AAPL, $TSLA)"
                    "- Do NOT promise returns or add disclaimers\n"
                    "- Separate posts with '---POST_BREAK---'"
                )
            }],
            max_tokens=700,
            temperature=0.9
        )

        raw = response.choices[0].message.content.strip()
        posts = [p.strip() for p in raw.split("---POST_BREAK---") if p.strip()]
        return posts if len(posts) > 1 else (posts[0] if posts else raw)

    except Exception as e:
        print(f"  Threads: AI generation failed ({e})")
        return "Markets in focus: Key levels and setups to watch. #Investing #Trading"


# ============================================================
# StockTwits Content Generation (Cashtag Community)
# ============================================================
def generate_stocktwits_content():
    """Generate a StockTwits message with cashtag.

    StockTwits: 140 char limit, must include $TICKER cashtag.
    Vertical investing community — high conversion potential.
    """
    if not GROQ_API_KEY:
        return "$SPY Key levels to watch. Stay disciplined. #Trading"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")
        persona = get_daily_persona(platform_shift=5)

        # Try to get trending symbols for smarter content
        trending_str = "$SPY, $QQQ, $AAPL"
        try:
            r = requests.get("https://api.stocktwits.com/api/2/trending/symbols.json", timeout=5)
            if r.status_code == 200:
                symbols = r.json().get("symbols", [])
                trending_str = ", ".join(["$" + s.get("symbol", "") for s in symbols[:5]])
        except Exception:
            pass

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write ONE StockTwits message for " + day + ", " + date_str + ".\n"
                    "TRENDING: " + trending_str + "\n\n"
                    "Pick ONE trending symbol and give an actionable take.\n\n"
                    "CRITICAL RULES:\n"
                    "- MAXIMUM 140 characters (hard limit)\n"
                    "- MUST include at least one cashtag like $AAPL\n"
                    "- Punchy, actionable, timely\n"
                    "- Stay in character as " + persona["name"] + "\n"
                    "- Do NOT promise returns\n"
                    "- End with one hashtag"
                )
            }],
            max_tokens=80,
            temperature=0.9
        )

        text = response.choices[0].message.content.strip()

        # Ensure cashtag
        if "$" not in text:
            text = text[:135] + " " + persona["hashtags"][0]

        # Hard truncate
        if len(text) > 140:
            text = text[:137] + "..."

        return text

    except Exception as e:
        print(f"  StockTwits: AI generation failed ({e})")
        return "$SPY Watching key levels. Data over drama. #Trading"


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 50)
    print("BroadFSC Social Media Auto-Poster")
    print("=" * 50)
    
    now = datetime.datetime.utcnow()
    print("Current UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print()
    
    # --- X/Twitter ---
    print("--- X/Twitter ---")
    has_oauth = all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET])
    if has_oauth:
        print("OAuth 1.0a: Configured (can post)")
        tweet_content = generate_platform_content('twitter')
        # Twitter now returns list[str] (thread format)
        if isinstance(tweet_content, list):
            print("  Thread: " + str(len(tweet_content)) + " tweets")
            for i, t in enumerate(tweet_content):
                print("  Tweet " + str(i+1) + ": " + t[:80] + ("..." if len(t) > 80 else ""))
            post_tweet_thread(tweet_content)
        else:
            # Fallback: single string (from knowledge queue or fallback)
            print("  Content: " + str(tweet_content)[:100] + "...")
            post_tweet(str(tweet_content))
    elif TWITTER_BEARER_TOKEN:
        print("Bearer Token: Configured (READ ONLY - cannot post)")
        print("  To enable posting, you need OAuth 1.0a credentials.")
    else:
        print("No X/Twitter credentials configured.")
    print()
    
    # --- LinkedIn ---
    print("--- LinkedIn ---")
    if LINKEDIN_ACCESS_TOKEN:
        print("LinkedIn: Configured")
        linkedin_post = generate_platform_content('linkedin')
        print("  Content length: " + str(len(linkedin_post)) + " chars")
        post_linkedin(linkedin_post)
    else:
        print("LinkedIn: Not configured")
    print()
    
    # --- Mastodon ---
    print("--- Mastodon ---")
    if MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE:
        print("Mastodon: Configured (" + MASTODON_INSTANCE + ")")
        mastodon_post = generate_platform_content('mastodon')
        print("  Content: " + mastodon_post[:100] + "...")
        post_mastodon(mastodon_post)
    else:
        print("Mastodon: Not configured")
    print()
    
    # --- Discord ---
    print("--- Discord ---")
    if DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID:
        print("Discord: Configured")
        discord_post = generate_platform_content('discord')
        print("  Content: " + discord_post[:100] + "...")
        post_discord(discord_post)
    else:
        print("Discord: Not configured")
    print()
    
    # --- Bluesky ---
    print("--- Bluesky ---")
    if BLUESKY_HANDLE and BLUESKY_APP_PASSWORD:
        print("Bluesky: Configured (" + BLUESKY_HANDLE + ")")
        bluesky_content = generate_platform_content('bluesky')
        # Bluesky now returns list[str] (thread format)
        if isinstance(bluesky_content, list):
            print("  Thread: " + str(len(bluesky_content)) + " posts")
            for i, p in enumerate(bluesky_content):
                print("  Post " + str(i+1) + ": " + p[:80] + ("..." if len(p) > 80 else ""))
            # Post thread: first post via API, rest as replies
            _post_bluesky_thread(bluesky_content)
        else:
            print("  Content: " + str(bluesky_content)[:100] + "...")
            post_bluesky(str(bluesky_content))
    else:
        print("Bluesky: Not configured")
    print()
    
    # --- TikTok ---
    print("--- TikTok ---")
    if POSTPROXY_API_KEY:
        print("TikTok: Configured (via Postproxy)")
        tiktok_caption = generate_platform_content('tiktok')
        print("  Caption: " + tiktok_caption[:100] + "...")
        if TIKTOK_VIDEO_URL:
            print("  Mode: Direct Video")
            post_tiktok(tiktok_caption, video_url=TIKTOK_VIDEO_URL)
        else:
            print("  Mode: Slideshow (running tiktok_poster.py)")
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiktok_poster.py")],
                    capture_output=True, text=True, timeout=120, env=os.environ
                )
                if result.returncode == 0:
                    print("  TikTok poster completed successfully")
                else:
                    print("  TikTok poster error: " + result.stderr[:200])
            except Exception as e:
                print("  TikTok poster failed: " + str(e))
    else:
        print("TikTok: Not configured")
    print()
    
    # --- LINE Official Account ---
    print("--- LINE Official Account ---")
    if LINE_CHANNEL_ACCESS_TOKEN:
        print("LINE: Configured")
        # Post in Japanese and Traditional Chinese (Japan/Taiwan markets)
        for lang in ["jp", "zh-tw"]:
            lang_name = {"jp": "Japanese", "zh-tw": "Traditional Chinese"}.get(lang, lang)
            print("  [" + lang_name + "]")
            line_content = generate_line_content(lang)
            print("  Content: " + line_content[:100] + "...")
            try:
                result = post_line(line_content, lang=lang)
                if HAS_ANALYTICS:
                    log_post(platform="line", post_type=f"flex_{lang}", content_preview=line_content[:100], status="success" if result else "failed")
            except Exception as e:
                print("  LINE: Failed - " + str(e))
                if HAS_ANALYTICS:
                    log_post(platform="line", post_type=f"flex_{lang}", content_preview=line_content[:100], status="failed", error_msg=str(e)[:200])
    else:
        print("LINE: Not configured")
    print()
    
    # --- Threads (Meta API) ---
    print("--- Threads ---")
    if THREADS_ACCESS_TOKEN and THREADS_USER_ID:
        print("Threads: Configured")
        try:
            from threads_poster import post_to_threads
            success = post_to_threads()
            if HAS_ANALYTICS:
                if success:
                    log_post(platform="threads", post_type="thread", content_preview="Threads post", status="success")
                else:
                    log_post(platform="threads", post_type="thread", content_preview="Threads post", status="failed", error_msg="post_to_threads returned False")
        except Exception as e:
            print("  Threads: Failed - " + str(e))
            if HAS_ANALYTICS:
                log_post(platform="threads", post_type="thread", content_preview="Threads post", status="failed", error_msg=str(e)[:200])
    else:
        print("Threads: Not configured (THREADS_ACCESS_TOKEN / THREADS_USER_ID missing)")
        print("  -> Setup: developers.facebook.com > create App > add Threads API")
        print("  -> Register: threads.net with msli2233bin@gmail.com")
    print()
    
    # --- StockTwits ---
    print("--- StockTwits ---")
    if STOCKTWITS_ACCESS_TOKEN:
        print("StockTwits: Configured")
        try:
            from stocktwits_poster import post_to_stocktwits
            success = post_to_stocktwits()
            if HAS_ANALYTICS:
                if success:
                    log_post(platform="stocktwits", post_type="message", content_preview="StockTwits post", status="success")
                else:
                    log_post(platform="stocktwits", post_type="message", content_preview="StockTwits post", status="failed", error_msg="post_to_stocktwits returned False")
        except Exception as e:
            print("  StockTwits: Failed - " + str(e))
            if HAS_ANALYTICS:
                log_post(platform="stocktwits", post_type="message", content_preview="StockTwits post", status="failed", error_msg=str(e)[:200])
    else:
        print("StockTwits: Not configured (STOCKTWITS_ACCESS_TOKEN missing)")
        print("  -> Register: stocktwits.com with msli2233bin@gmail.com")
        print("  -> Create app: api.stocktwits.com/developers")
    print()
    
    # --- Medium (browser automation, LOCAL ONLY) ---
    print("--- Medium ---")
    if MEDIUM_EMAIL and MEDIUM_PASSWORD:
        print("Medium: Configured (browser automation, runs locally)")
        medium_article = generate_platform_content('medium')
        if isinstance(medium_article, dict):
            print("  Title: " + medium_article.get("title", "N/A"))
            print("  Content: " + str(len(medium_article.get("content", ""))) + " chars")
            try:
                success, url = post_medium_article(medium_article)
                if HAS_ANALYTICS:
                    log_post(platform="medium", post_type="story", content_preview=medium_article.get("title", "")[:100],
                             status="success" if success else "failed", error_msg="" if success else "post_medium_article returned False")
            except Exception as e:
                print("  Medium: Failed - " + str(e))
                if HAS_ANALYTICS:
                    log_post(platform="medium", post_type="story", content_preview=medium_article.get("title", "")[:100],
                             status="failed", error_msg=str(e)[:200])
        else:
            print("  Unexpected content type: " + str(type(medium_article)))
    else:
        print("Medium: Not configured (MEDIUM_EMAIL/PASSWORD missing)")
    print()
    
    # --- Substack (browser automation, LOCAL ONLY) ---
    print("--- Substack ---")
    if SUBSTACK_EMAIL and SUBSTACK_PASSWORD:
        print("Substack: Configured (browser automation, runs locally)")
        substack_article = generate_platform_content('substack')
        if isinstance(substack_article, dict):
            print("  Title: " + substack_article.get("title", "N/A"))
            print("  Content: " + str(len(substack_article.get("content", ""))) + " chars")
            try:
                success, url = post_substack_article(substack_article)
                if HAS_ANALYTICS:
                    log_post(platform="substack", post_type="article",
                             content_preview=substack_article.get("title", "")[:100],
                             status="success" if success else "failed",
                             error_msg="" if success else "post_substack_article returned False")
            except Exception as e:
                print("  Substack: Failed - " + str(e))
                if HAS_ANALYTICS:
                    log_post(platform="substack", post_type="article",
                             content_preview=substack_article.get("title", "")[:100],
                             status="failed", error_msg=str(e)[:200])
        else:
            print("  Unexpected content type: " + str(type(substack_article)))
    else:
        print("Substack: Not configured (SUBSTACK_EMAIL/PASSWORD missing)")
    print()
    
    print("=" * 50)
    print("Social posting check complete.")


if __name__ == "__main__":
    main()
