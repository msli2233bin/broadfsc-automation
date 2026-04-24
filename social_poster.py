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
        }
    return {
        "telegram": TELEGRAM_LINK,
        "website": WEBSITE_LINK,
        "hub": HUB_LINK,
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
        "prefer": "website",
    },
    "line": {
        "style": "flex",           # LINE: Flex Message with CTA button, link in button
        "link_every_n": 1,
        "prefer": "website",       # Website link goes into Flex Message CTA button
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
def post_mastodon(text):
    """Post to Mastodon using access token."""
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
        else:
            print("  Mastodon: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            if HAS_ANALYTICS:
                log_post(platform="mastodon", post_type="toot", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print("  Mastodon: FAIL - " + str(e))
        if HAS_ANALYTICS:
            log_post(platform="mastodon", post_type="toot", content_preview=text[:100], status="failed", error_msg=str(e)[:200])
        return False


def generate_mastodon_content():
    """Generate a deep-dive Mastodon analysis post in today's analyst persona voice."""
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

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE market analysis for " + day + ", " + date_str + ".\n"
                    "Focus on US stocks, global macro, or investment strategy.\n\n"
                    "Hook rule: " + persona["hook"] + "\n\n"
                    "Structure (follow this exactly):\n"
                    "1. HOOK — Open with a bold, specific claim or data point\n"
                    "2. THE SETUP — 2-3 sentences of context (what's happening, why it matters)\n"
                    "3. THE INSIGHT — Your unique angle that others miss (data-driven reasoning)\n"
                    "4. THE TAKEAWAY — One clear, actionable conclusion\n\n"
                    "Rules:\n"
                    "- Maximum 500 characters (strict Mastodon limit)\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Include 2-3 specific numbers (prices, yields, %, data points)\n"
                    "- End with: " + tags + "\n"
                    "- Add link: " + links["hub"] + "\n"
                    "- Do NOT promise returns or give direct buy/sell advice"
                )
            }],
            max_tokens=350,
            temperature=0.85
        )
        result = response.choices[0].message.content.strip()
        # Hard-truncate to 500 chars if AI exceeded
        if len(result) > 500:
            result = result[:497] + "..."
        print("  Mastodon persona: " + persona["name"] + " (" + str(len(result)) + " chars)")
        return result
    except Exception as e:
        print("  AI Mastodon generation failed: " + str(e))
        return get_fallback_mastodon()


def get_fallback_mastodon():
    """Fallback Mastodon content with deep-dive analysis."""
    links = get_tracked_links("mastodon")
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    toots = [
        f"The bond market is pricing in something equities refuse to acknowledge. 10Y-2Y inverted for 18+ months — historically that's never resolved with a soft landing. Which asset class blinks first? My money's on credit. {links['hub']} #Investing #Trading #MarketAnalysis #Finance",
        f"Cross-asset divergence: Gold at ATH while real yields stay elevated. That's not supposed to happen. Either gold is wrong or bonds are wrong. Central banks will cut faster than priced — that's the bet. {links['hub']} #Investing #Trading #MarketAnalysis #Finance",
        f"AI stocks = 2000 dot-com parallel. Transformative tech, insane valuations, 50%+ correction before real winners emerged. The tech is real. The prices aren't. Patience will be rewarded — but only if you survive the drawdown. {links['hub']} #Investing #Trading #StockMarket #Finance",
    ]
    return toots[day_idx % len(toots)]


# ============================================================
# Discord Poster
# ============================================================
def post_discord(text):
    """Post a message to a Discord channel using Bot token."""
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
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            msg_id = r.json().get("id", "")
            print("  Discord: Posted! Message ID: " + str(msg_id))
            if HAS_ANALYTICS:
                log_post(platform="discord", post_type="message", content_preview=text[:100], post_id=str(msg_id), status="success")
            return True
        else:
            print("  Discord: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            if HAS_ANALYTICS:
                log_post(platform="discord", post_type="message", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print("  Discord: FAIL - " + str(e))
        if HAS_ANALYTICS:
            log_post(platform="discord", post_type="message", status="failed", error_msg=str(e)[:200])
        return False


def generate_discord_content():
    """Generate a deep-dive Discord analysis post using today's analyst persona."""
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

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE market analysis post for Discord community on " + day + ", " + date_str + ".\n"
                    "Focus on US stocks, global macro, or investment strategy.\n\n"
                    "Hook rule: " + persona["hook"] + "\n\n"
                    "Structure (follow this exactly):\n"
                    "1. **HOOK** — Open with a bold, specific claim or data point that stops scrolling\n"
                    "2. **THE BIG PICTURE** — 3-4 sentences of macro context (what's happening globally)\n"
                    "3. **WHY IT MATTERS** — Connect the dots: how does this affect portfolios? What's the contrarian angle?\n"
                    "4. **BY THE NUMBERS** — 2-3 specific data points with context (not just 'S&P up 1%' but 'S&P at 5,280 — testing resistance from the Jan 2022 double top')\n"
                    "5. **THE BOTTOM LINE** — One clear takeaway for readers\n"
                    "6. **DISCUSSION** — End with a thought-provoking question for the community\n\n"
                    "Rules:\n"
                    "- Maximum 1800 characters\n"
                    "- Use Discord markdown: **bold** for section headers, bullet points for data\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Include 3-5 specific numbers (prices, yields, %, data points)\n"
                    "- End with: " + tags + "\n"
                    "- Subscribe: " + links["telegram"] + "\n"
                    "- Learn free: " + links["hub"] + "\n"
                    "- Add ⚠️ 'Not financial advice' disclaimer at the very end\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=800,
            temperature=0.85
        )
        result = response.choices[0].message.content.strip()
        # Discord limit is 2000 chars
        if len(result) > 1900:
            result = result[:1897] + "..."
        print("  Discord persona: " + persona["name"] + " (" + str(len(result)) + " chars)")
        return result
    except Exception as e:
        print("  AI Discord generation failed: " + str(e))
        return get_fallback_discord()


def get_fallback_discord():
    """Fallback Discord content with deep analysis and engagement hooks."""
    links = get_tracked_links("discord")
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    posts = [
        (
            "**🔥 The Soft Landing Illusion?**\n\n"
            "Here's the question splitting Wall Street right now — and your portfolio depends on the answer.\n\n"
            "**The Big Picture:**\n"
            "Markets are priced for perfection. S&P earnings multiples at 21x. Credit spreads near historic tights. VIX below 15. Everything says 'all clear.'\n\n"
            "**Why It Matters:**\n"
            "But the yield curve has been inverted for 18+ months. Historically, every recession in the last 50 years was preceded by an inversion — with a 12-18 month lag. We're in that lag window NOW.\n\n"
            "**By The Numbers:**\n"
            "• 10Y-2Y spread: -0.35% (still inverted)\n"
            "• Commercial real estate delinquencies: up 2.1x YoY\n"
            "• Consumer savings rate: dropped from 5.3% → 3.6% in 6 months\n\n"
            "**The Bottom Line:**\n"
            "You don't need to predict a recession. You need to be prepared for one. That means reducing leverage, raising cash, and owning assets that zig when equities zag.\n\n"
            "**What do you think — soft landing or hard reality?** Drop your take below 👇\n\n"
            f"Subscribe for daily briefings: {links['telegram']}\n"
            f"Learn free: {links['hub']}\n\n"
            "⚠️ Not financial advice\n\n"
            "#Investing #Trading #MarketAnalysis #StockMarket #Finance"
        ),
        (
            "**📊 The Carry Trade: The Hidden Force Moving Your Portfolio**\n\n"
            "Ever wonder why the market suddenly tanked in August 2024 — and recovered just as fast? The answer is the carry trade, and understanding it will make you a better investor.\n\n"
            "**The Setup:**\n"
            "Imagine borrowing money at 0.5% and investing it at 5%. That 4.5% difference is the 'carry.' Hedge funds do this at scale — borrowing in JPY (near-zero rates) and buying USD assets (high yields + equity upside).\n\n"
            "**Why It Matters:**\n"
            "This trade was worth an estimated $4 TRILLION. When the BOJ unexpectedly hiked rates in July 2024, the math flipped. Borrowing costs rose → funds had to unwind → forced selling of US equities → market crash. All in 3 trading days.\n\n"
            "**By The Numbers:**\n"
            "• JPY/USD moved 12% in 3 weeks (massive for FX)\n"
            "• Nikkei dropped 12% in a single day\n"
            "• S&P 500 fell 6% before rebounding\n\n"
            "**The Takeaway:**\n"
            "The biggest market moves often come from hidden leverage — not fundamentals. When you see a violent, unexplained selloff, think: who's being forced to sell?\n\n"
            "**What's the next carry trade unwind? JPY is still cheap. What happens if BOJ hikes again?** 👇\n\n"
            f"Subscribe for daily briefings: {links['telegram']}\n"
            f"Learn free: {links['hub']}\n\n"
            "⚠️ Not financial advice\n\n"
            "#Investing #Trading #MarketAnalysis #StockMarket #Finance"
        ),
    ]
    return posts[day_idx % len(posts)]


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
        link_line = f"\n- Include this link in the LAST tweet: {link}" if link and not link.startswith("Learn") else "\n- Do NOT include any links (link in bio instead)"

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
                    "- Do NOT promise returns or give direct financial advice\n"
                    "- NEVER start with 'Market update', 'Key themes', or 'Markets are'\n"
                    "- Separate each tweet with '---TWEET_BREAK---' on its own line"
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
            post_line(line_content, lang=lang)
    else:
        print("LINE: Not configured")
    print()
    
    print("=" * 50)
    print("Social posting check complete.")


if __name__ == "__main__":
    main()
