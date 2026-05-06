"""
BroadFSC Threads Auto-Poster
Posts market analysis to Meta Threads via official API.

Threads API (Meta):
- Official API launched late 2024
- Rate limit: 250 posts/day, 1000 replies/day
- Authentication: OAuth 2.0 via Meta Developer App
- Supports text, images, carousels, videos
- Max text: 500 characters per post
- Thread support: reply chains

Setup:
1. Go to developers.facebook.com → create App
2. Add "Threads API" product
3. Get App ID + App Secret
4. Generate User Access Token with threads_basic + threads_content_publish scopes
5. Set environment variables: THREADS_ACCESS_TOKEN

Alternative: Use long-lived token (refreshes automatically)
"""

import os
import sys
import datetime
import json
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Config - try env first, then .env file, then threads_token.txt
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")

if not THREADS_ACCESS_TOKEN:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    # Try .env file
    _env_path = os.path.join(_script_dir, ".env")
    if os.path.exists(_env_path):
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("THREADS_ACCESS_TOKEN="):
                    THREADS_ACCESS_TOKEN = line.strip().split("=", 1)[1]
                elif line.startswith("THREADS_USER_ID=") and not THREADS_USER_ID:
                    THREADS_USER_ID = line.strip().split("=", 1)[1]
    # Try threads_token.txt
    if not THREADS_ACCESS_TOKEN:
        _token_path = os.path.join(_script_dir, "threads_token.txt")
        if os.path.exists(_token_path):
            with open(_token_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("THREADS_ACCESS_TOKEN="):
                        THREADS_ACCESS_TOKEN = line.strip().split("=", 1)[1]
                    elif line.startswith("THREADS_USER_ID=") and not THREADS_USER_ID:
                        THREADS_USER_ID = line.strip().split("=", 1)[1]

# API endpoints
THREADS_API_BASE = "https://graph.threads.net/v1.0"

# ============================================================
# Persona system (shared with social_poster.py)
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


def get_daily_persona(platform_shift: int = 4) -> dict:
    """Return today's active persona, shifted for Threads."""
    now = datetime.datetime.utcnow()
    keys = list(SOCIAL_PERSONAS.keys())
    idx = (now.timetuple().tm_yday + platform_shift) % len(keys)
    return SOCIAL_PERSONAS[keys[idx]]


# ============================================================
# Content Generation
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def generate_threads_content():
    """Generate a Threads thread in today's analyst persona voice.

    Strategy: 3-4 post thread with clear structure.
    Each post = self-contained insight. Last post = CTA + engagement.
    """
    if not GROQ_API_KEY:
        return ["Market update: Key levels to watch. #Investing #Trading 📱@BroadInvestBot"]

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")
        persona = get_daily_persona(platform_shift=4)

        # Inject real market data
        market_snippet = ""
        try:
            import yfinance as yf
            tickers = {"SPY": "^GSPP", "QQQ": "^IXIC", "VIX": "^VIX"}
            parts = []
            for sym, ticker in tickers.items():
                try:
                    t = yf.Ticker(ticker)
                    h = t.history(period="2d")
                    if len(h) >= 1:
                        c = h['Close'].iloc[-1]
                        if len(h) >= 2:
                            pct = (c / h['Close'].iloc[-2] - 1) * 100
                            parts.append(f"{sym}={c:.0f}({pct:+.1f}%)")
                        else:
                            parts.append(f"{sym}={c:.0f}")
                except Exception:
                    pass
            if parts:
                market_snippet = " | ".join(parts)
        except Exception:
            pass

        if not market_snippet:
            market_snippet = "US markets open"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write a Threads thread (3 posts) for " + day + ", " + date_str + ".\n\n"
                    "LIVE DATA: " + market_snippet + "\n\n"
                    "HOOK: " + persona["hook"] + "\n\n"
                    "Thread structure:\n"
                    "1/ 🔥 HOOK — Bold claim with specific number (1-2 sentences)\n"
                    "2/ 💡 INSIGHT — Contrarian angle, what consensus misses, 2-3 data points with $TICKER format\n"
                    "3/ 🎯 TAKE + ENGAGE — One takeaway + provocative question inviting replies\n\n"
                    "Rules:\n"
                    "- Each post MAX 480 characters (leave room for hashtags)\n"
                    "- Start each with number: 1/, 2/, 3/\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Include 3-4 specific numbers across the thread\n"
                    "- Use $TICKER for every stock mention (e.g. $AAPL, $TSLA)\n"
                    "- Post 3 MUST end with: #Investing #Trading\n"
                    "- Post 3 MUST include a question that demands an opinion\n"
                    "- Do NOT include any links — they will be appended\n"
                    "- Do NOT promise returns or add disclaimers\n"
                    "- Zero filler — every word earns its place\n"
                    "- Separate posts with '---POST_BREAK---'"
                )
            }],
            max_tokens=600,
            temperature=0.9
        )

        raw = response.choices[0].message.content.strip()
        posts = [p.strip() for p in raw.split("---POST_BREAK---") if p.strip()]

        # Validate: ensure each post is under 500 chars
        validated = []
        for p in posts:
            if len(p) > 497:
                p = p[:494] + "..."
            validated.append(p)

        # Append CTA to last post
        if validated:
            cta = " 📱@BroadInvestBot"
            last = validated[-1]
            if len(last) + len(cta) <= 500:
                validated[-1] = last + cta

        return validated if len(validated) > 1 else (validated if validated else ["Markets in focus: Key levels to watch. #Investing #Trading 📱@BroadInvestBot"])

    except Exception as e:
        print(f"  Threads: AI generation failed ({e})")
        return ["Markets in focus: Key levels and setups to watch. #Investing #Trading 📱@BroadInvestBot"]


# ============================================================
# Threads API Functions
# ============================================================
def create_threads_container(text, media_type="TEXT", retries=2):
    """Create a media container for a Threads post (with retry).

    Step 1 of 2-step posting process.
    Returns container ID.
    """
    url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
    params = {
        "media_type": media_type,
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN,
    }

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, params=params, timeout=15)
            r.raise_for_status()
            container_id = r.json().get("id")
            print(f"  Threads: Container created: {container_id}")
            return container_id
        except requests.exceptions.RequestException as e:
            status = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            if status in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 2 ** attempt
                print(f"  Threads: Container retry {attempt}/{retries} in {wait}s (HTTP {status})")
                import time; time.sleep(wait)
                continue
            print(f"  Threads: Failed to create container: {e}")
            return None
    return None


def publish_threads_container(container_id, retries=2):
    """Publish a previously created container (with retry).

    Step 2 of 2-step posting process.
    Returns the post ID.
    """
    url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads_publish"
    params = {
        "creation_id": container_id,
        "access_token": THREADS_ACCESS_TOKEN,
    }

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, params=params, timeout=15)
            r.raise_for_status()
            post_id = r.json().get("id")
            print(f"  Threads: Published! Post ID: {post_id}")
            return post_id
        except requests.exceptions.RequestException as e:
            status = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            if status in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 2 ** attempt
                print(f"  Threads: Publish retry {attempt}/{retries} in {wait}s (HTTP {status})")
                import time; time.sleep(wait)
                continue
            print(f"  Threads: Failed to publish container: {e}")
            return None
    return None


def post_threads_single(text):
    """Post a single Threads post (2-step process: create + publish)."""
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("  Threads: Missing THREADS_ACCESS_TOKEN or THREADS_USER_ID")
        return False

    container_id = create_threads_container(text)
    if not container_id:
        return False

    post_id = publish_threads_container(container_id)
    return post_id is not None


def post_threads_thread(posts):
    """Post a Threads thread (first post + replies).

    Each subsequent post is a reply to the previous one.
    """
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("  Threads: Missing THREADS_ACCESS_TOKEN or THREADS_USER_ID")
        return False

    if not posts:
        print("  Threads: No posts to publish")
        return False

    # Post first message
    print(f"  Threads: Posting thread ({len(posts)} posts)...")
    container_id = create_threads_container(posts[0])
    if not container_id:
        return False

    post_id = publish_threads_container(container_id)
    if not post_id:
        return False

    # Post replies
    for i, reply_text in enumerate(posts[1:], 2):
        import time
        time.sleep(2)  # Small delay between replies

        # Create reply container
        url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
        params = {
            "media_type": "TEXT",
            "text": reply_text,
            "reply_to_id": post_id,
            "access_token": THREADS_ACCESS_TOKEN,
        }

        try:
            r = requests.post(url, params=params, timeout=15)
            r.raise_for_status()
            reply_container_id = r.json().get("id")

            # Publish reply
            publish_params = {
                "creation_id": reply_container_id,
                "access_token": THREADS_ACCESS_TOKEN,
            }
            pub_r = requests.post(
                f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads_publish",
                params=publish_params,
                timeout=15,
            )
            pub_r.raise_for_status()
            post_id = pub_r.json().get("id")
            print(f"  Threads: Reply {i}/{len(posts)} posted! ID: {post_id}")

        except Exception as e:
            print(f"  Threads: Failed to post reply {i}: {e}")
            continue

    return True


def post_to_threads():
    """Main entry: generate content and post to Threads."""
    print("\n📱 Threads ===")

    # Auto-refresh token before posting
    current_token = check_and_refresh_token()
    if not current_token:
        print("  Threads: No valid token, skipping post")
        return False

    content = generate_threads_content()

    if isinstance(content, list):
        return post_threads_thread(content)
    else:
        return post_threads_single(content)


# ============================================================
# Token Management (Long-lived tokens)
# ============================================================
def refresh_long_lived_token(short_lived_token=None):
    """Exchange a short-lived token for a long-lived one (60 days).

    Call this once during setup, then store the long-lived token.
    """
    token = short_lived_token or THREADS_ACCESS_TOKEN
    url = f"{THREADS_API_BASE}/access_token"
    params = {
        "grant_type": "th_exchange_token",
        "client_secret": os.environ.get("THREADS_APP_SECRET", ""),
        "access_token": token,
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        new_token = data.get("access_token")
        expires_in = data.get("expires_in", "unknown")
        print(f"  Threads: Got long-lived token (expires in {expires_in}s)")
        return new_token
    except Exception as e:
        print(f"  Threads: Token refresh failed: {e}")
        return None


def refresh_access_token(long_lived_token=None):
    """Refresh a long-lived token. Can be called any time.

    Long-lived tokens for Threads can be refreshed once per day.
    """
    token = long_lived_token or THREADS_ACCESS_TOKEN
    url = f"{THREADS_API_BASE}/refresh_access_token"
    params = {
        "grant_type": "th_refresh_token",
        "access_token": token,
    }

    try:
        r = requests.post(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        new_token = data.get("access_token")
        expires_in = data.get("expires_in", "unknown")
        print(f"  Threads: Token refreshed (expires in {expires_in}s)")
        return new_token
    except Exception as e:
        print(f"  Threads: Token refresh failed: {e}")
        return None


def check_and_refresh_token():
    """Check if token is about to expire and auto-refresh.

    Long-lived tokens last 60 days and can be refreshed once per day.
    This should be called before every posting session.
    Returns the current (possibly refreshed) token, or None on failure.
    """
    global THREADS_ACCESS_TOKEN
    token = THREADS_ACCESS_TOKEN
    if not token:
        print("  Threads: No token configured, skipping refresh check")
        return None

    # Try to verify current token
    try:
        r = requests.get(
            f"{THREADS_API_BASE}/me",
            params={"access_token": token},
            timeout=10,
        )
        if r.status_code == 200:
            # Token still valid, try to refresh it (extends expiry)
            print("  Threads: Token valid, attempting daily refresh...")
            new_token = refresh_access_token(token)
            if new_token:
                print("  Threads: Token refreshed successfully")
                # Update environment for this session
                os.environ["THREADS_ACCESS_TOKEN"] = new_token
                THREADS_ACCESS_TOKEN = new_token
                # Save refreshed token to .env
                _save_token_to_env(new_token)
                return new_token
            else:
                print("  Threads: Refresh not needed or failed, using current token")
                return token
        else:
            print(f"  Threads: Token expired or invalid (HTTP {r.status_code})")
            print("  Threads: Manual re-authorization required via get_threads_token_v3.py")
            return None
    except Exception as e:
        print(f"  Threads: Token check error: {e}")
        return None


def _save_token_to_env(token):
    """Save refreshed token to .env file."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        env_lines = []
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        except FileNotFoundError:
            pass

        updated = False
        new_lines = []
        for line in env_lines:
            if line.startswith("THREADS_ACCESS_TOKEN="):
                new_lines.append(f"THREADS_ACCESS_TOKEN={token}\n")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f"THREADS_ACCESS_TOKEN={token}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"  Threads: Failed to save token to .env: {e}")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "post":
            post_to_threads()
        elif cmd == "refresh-token":
            new_token = check_and_refresh_token()
            if new_token:
                print(f"New token: {new_token[:20]}...")
            else:
                print("Token refresh failed. Re-authorization needed.")
        elif cmd == "exchange-token":
            short_token = sys.argv[2] if len(sys.argv) > 2 else None
            new_token = refresh_long_lived_token(short_token)
            if new_token:
                print(f"Long-lived token: {new_token[:20]}...")
        elif cmd == "check-token":
            token = check_and_refresh_token()
            if token:
                print(f"Token OK: {token[:30]}...")
            else:
                print("Token invalid or expired. Run get_threads_token_v3.py")
        else:
            print("Usage: threads_poster.py [post|refresh-token|exchange-token|check-token]")
    else:
        post_to_threads()
