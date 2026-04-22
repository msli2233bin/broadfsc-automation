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


def generate_platform_content(platform: str) -> str:
    """智能内容生成：优先用知识库内容，其次AI生成，最后fallback"""
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
    """Post a tweet using OAuth 1.0a."""
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
            return True
        else:
            print("  X/Twitter: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            if HAS_ANALYTICS:
                log_post(platform="twitter", post_type="tweet", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print("  X/Twitter: FAIL - " + str(e))
        if HAS_ANALYTICS:
            log_post(platform="twitter", post_type="tweet", content_preview=text[:100], status="failed", error_msg=str(e)[:200])
        return False


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
    if len(text) > 480:
        text = text[:477] + "..."
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
    """Generate a Mastodon post (longer than tweet, up to 500 chars)."""
    if not GROQ_API_KEY:
        return get_fallback_mastodon()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        tags = " ".join(HASHTAGS[:4])
        links = get_tracked_links("mastodon")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write a market insight post for Mastodon.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- Maximum 450 characters\n"
                    "- Include 1-2 specific market observations\n"
                    "- End with: " + tags + "\n"
                    "- Add link: " + links["hub"] + "\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=150,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI Mastodon generation failed: " + str(e))
        return get_fallback_mastodon()


def get_fallback_mastodon():
    """Fallback Mastodon content."""
    links = get_tracked_links("mastodon")
    toots = [
        "Global markets update: Central bank policy divergence continues to drive cross-currency flows. "
        "Stay informed with daily pre-market briefings covering Asia, Europe, Middle East & Americas. "
        f"Subscribe free: {links['telegram']} | Learn investing: {links['hub']} #Investing #Trading #MarketAnalysis #Finance",
        "Key themes this week: Fed signals, earnings season dynamics, and geopolitical risk premiums "
        "shaping commodity markets. Get daily AI-powered market insights in English, Spanish & Arabic. "
        f"{links['telegram']} | Free education: {links['hub']} #StockMarket #Investing #Trading #MarketAnalysis",
    ]
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(toots)
    return toots[idx]


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
    """Generate a Discord post (can be longer, use embed format)."""
    if not GROQ_API_KEY:
        return get_fallback_discord()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        tags = " ".join(HASHTAGS)
        links = get_tracked_links("discord")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write a daily market outlook post for a Discord community.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- Maximum 1500 characters\n"
                    "- Include 2-3 specific market observations\n"
                    "- Professional but conversational tone\n"
                    "- End with: " + tags + "\n"
                    "- Add: 'Subscribe for daily briefings: " + links["telegram"] + "'\n"
                    "- Add: 'Free education: " + links["hub"] + "'\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI Discord generation failed: " + str(e))
        return get_fallback_discord()


def get_fallback_discord():
    """Fallback Discord content."""
    links = get_tracked_links("discord")
    return (
        "**Daily Market Outlook** :chart_with_upwards_trend:\n\n"
        "Key themes for today:\n"
        "• Central bank policy divergence driving cross-currency flows\n"
        "• Earnings season providing real-time economic signals\n"
        "• Geopolitical risk premiums influencing commodity markets\n\n"
        "Stay informed with daily pre-market briefings covering "
        "Asia, Europe, Middle East & Americas.\n\n"
        f"Subscribe free: {links['telegram']}\n"
        f"Learn investing free: {links['hub']}\n"
        f"Website: {links['website']}\n\n"
        "#Investing #Trading #MarketAnalysis #StockMarket #Finance"
    )


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


def generate_bluesky_content():
    """Generate a Bluesky post (max 300 chars)."""
    if not GROQ_API_KEY:
        return get_fallback_bluesky()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        tags = " ".join(HASHTAGS[:3])
        link = get_platform_link("bluesky")
        link_note = f"\n- Add this link at the end: {link}" if link and not link.startswith("Follow") else "\n- Do NOT include any links"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write ONE short market insight post for Bluesky.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- Maximum 280 characters\n"
                    "- Include 1 specific market observation\n"
                    "- End with: " + tags + "\n"
                    + link_note + "\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=100,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI Bluesky generation failed: " + str(e))
        return get_fallback_bluesky()


def get_fallback_bluesky():
    """Fallback Bluesky content."""
    posts = [
        "Global markets update: Central bank policy divergence continues to drive cross-currency flows. Stay informed with daily briefings. #Investing #Trading #MarketAnalysis",
        "Key themes this week: Fed signals, earnings season, and geopolitical risk premiums shaping commodity markets. #StockMarket #Investing #Finance",
        "From Tokyo to New York, markets move fast. BroadFSC delivers AI-powered daily market briefings. #Investing #Trading #MarketAnalysis",
    ]
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(posts)
    return posts[idx]


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
    """Generate a tweet-sized market insight using AI."""
    if not GROQ_API_KEY:
        return get_fallback_tweet()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        tags = " ".join(HASHTAGS[:3])
        link = get_platform_link("twitter")
        link_instruction = f"\n- Include this link: {link}" if link and not link.startswith("Learn") else "\n- Do NOT include any links (link in bio instead)"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write ONE short tweet about today's market outlook.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- Maximum 250 characters (Twitter limit is 280)\n"
                    "- Be specific with a market observation or data point\n"
                    "- End with: " + tags + "\n"
                    + link_instruction + "\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=100,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
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
    """Fallback tweet content."""
    links = get_tracked_links("twitter")
    tweets = [
        f"Markets are navigating a complex macro landscape. Stay informed with daily pre-market briefings from BroadFSC covering Asia, Europe, Middle East & Americas. {links['hub']} #Investing #Trading #MarketAnalysis",
        f"Key week ahead: Central bank decisions, earnings season updates, and geopolitical developments shaping global markets. Get daily insights: {links['telegram']} #StockMarket #Finance",
        f"From Tokyo to New York, global markets move fast. BroadFSC delivers AI-powered pre-market briefings. Subscribe free: {links['telegram']} #Investing #Trading",
    ]
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(tweets)
    return tweets[idx]


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
        tweet = generate_platform_content('twitter')
        print("  Content: " + tweet[:100] + "...")
        post_tweet(tweet)
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
        bluesky_post = generate_platform_content('bluesky')
        print("  Content: " + bluesky_post[:100] + "...")
        post_bluesky(bluesky_post)
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
