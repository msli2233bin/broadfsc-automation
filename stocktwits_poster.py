"""
BroadFSC StockTwits Auto-Poster
Posts market analysis to StockTwits — the largest social investing community.

StockTwits API:
- REST API with OAuth 2.0 authentication
- POST /messages endpoint for posting messages
- Cashtag syntax: $AAPL $TSLA (required for visibility)
- Max 140 characters per message
- Rate limit: ~200 messages/day
- Free developer access

Setup:
1. Go to api.stocktwits.com/developers
2. Create an application
3. Get Client ID + Client Secret
4. Authorize and get Access Token
5. Set environment variables: STOCKTWITS_ACCESS_TOKEN, STOCKTWITS_CLIENT_ID, STOCKTWITS_CLIENT_SECRET

Registration:
- Sign up at stocktwits.com with msli2233bin@gmail.com
- Username: BroadFSC
"""

import os
import sys
import datetime
import json
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Config
STOCKTWITS_ACCESS_TOKEN = os.environ.get("STOCKTWITS_ACCESS_TOKEN", "")
STOCKTWITS_CLIENT_ID = os.environ.get("STOCKTWITS_CLIENT_ID", "")
STOCKTWITS_CLIENT_SECRET = os.environ.get("STOCKTWITS_CLIENT_SECRET", "")

# API endpoints
STOCKTWITS_API_BASE = "https://api.stocktwits.com/api/2"

# ============================================================
# Persona system (shared)
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
        "hashtags": ["$SPY", "$QQQ", "#Trading"],
    },
    "yang": {
        "name": "Thomas Yang",
        "title": "Value Compass",
        "emoji": "📘",
        "style": (
            "You are Thomas, a Buffett disciple. Calm, philosophical, long-term. "
            "Challenge short-term panic with fundamentals. Use rhetorical questions."
        ),
        "hook": "Start with a rhetorical question that challenges the short-term narrative.",
        "hashtags": ["$BRK.B", "$AAPL", "#ValueInvesting"],
    },
    "hong": {
        "name": "Michael Hong",
        "title": "Macro Strategist",
        "emoji": "🔭",
        "style": (
            "You are Michael, a macro strategist. Data-driven, intellectually rigorous. "
            "Connect cycles, capital flows, and geopolitics."
        ),
        "hook": "Start with a macro data point most investors overlook.",
        "hashtags": ["$TLT", "$DXY", "#MacroStrategy"],
    },
    "warrior": {
        "name": "Iron Bull",
        "title": "Voice of the Retail Fighter",
        "emoji": "⚔️",
        "style": (
            "You are Iron Bull, voice of the everyday investor. "
            "Passionate, relatable. Use 'we' — in this together."
        ),
        "hook": "Start with empathy — name the fear most retail investors feel right now.",
        "hashtags": ["$GME", "$AMC", "#RetailInvestor"],
    },
}


def get_daily_persona(platform_shift: int = 5) -> dict:
    """Return today's active persona, shifted for StockTwits."""
    now = datetime.datetime.utcnow()
    keys = list(SOCIAL_PERSONAS.keys())
    idx = (now.timetuple().tm_yday + platform_shift) % len(keys)
    return SOCIAL_PERSONAS[keys[idx]]


# ============================================================
# Content Generation
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def generate_stocktwits_content():
    """Generate a StockTwits message in today's persona voice.

    StockTwits uses cashtags ($AAPL) and has a 140-char limit.
    Must include at least one cashtag for visibility.
    """
    if not GROQ_API_KEY:
        return "$SPY Key levels to watch today. Stay disciplined. #Trading #Investing"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")

        persona = get_daily_persona(platform_shift=5)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write ONE StockTwits message for " + day + ", " + date_str + ".\n"
                    "Focus on a specific stock or ETF with actionable insight.\n\n"
                    "Hook: " + persona["hook"] + "\n\n"
                    "CRITICAL RULES:\n"
                    "- MAXIMUM 140 characters (hard limit)\n"
                    "- MUST include at least one cashtag like $AAPL or $SPY\n"
                    "- Must be punchy and actionable — this is a trading community\n"
                    "- Include 1-2 relevant cashtags\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Do NOT promise returns or give financial advice\n"
                    "- No disclaimers\n"
                    "- End with relevant hashtag"
                )
            }],
            max_tokens=80,
            temperature=0.9
        )

        text = response.choices[0].message.content.strip()

        # Ensure cashtag presence
        if "$" not in text:
            tags = persona["hashtags"]
            if tags:
                cashtag = tags[0]
                text = text[:140 - len(cashtag) - 1] + " " + cashtag

        # Hard truncate to 140 chars
        if len(text) > 140:
            text = text[:137] + "..."

        return text

    except Exception as e:
        print(f"  StockTwits: AI generation failed ({e}), using fallback")
        return "$SPY Watching key support/resistance levels. Data over drama. #Trading"


# ============================================================
# StockTwits API Functions
# ============================================================
def post_stocktwits_message(body, chart=None):
    """Post a message to StockTwits.

    Args:
        body: Message text (max 140 chars, must include cashtag)
        chart: Optional chart URL to attach

    Returns:
        bool: Success status
    """
    if not STOCKTWITS_ACCESS_TOKEN:
        print("  StockTwits: Missing STOCKTWITS_ACCESS_TOKEN")
        print("  -> Register at stocktwits.com with msli2233bin@gmail.com")
        print("  -> Create app at api.stocktwits.com/developers")
        return False

    url = f"{STOCKTWITS_API_BASE}/messages/create.json"
    payload = {
        "body": body,
        "access_token": STOCKTWITS_ACCESS_TOKEN,
    }

    if chart:
        payload["chart"] = chart

    try:
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            msg_id = data.get("message", {}).get("id", "unknown")
            print(f"  StockTwits: Posted! Message ID: {msg_id}")
            return True
        elif r.status_code == 401:
            print("  StockTwits: Token expired or invalid. Need to re-authorize.")
            return False
        elif r.status_code == 429:
            print("  StockTwits: Rate limited. Too many messages.")
            return False
        else:
            print(f"  StockTwits: Error {r.status_code}: {r.text[:200]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  StockTwits: Request failed: {e}")
        return False


def get_trending_symbols():
    """Fetch currently trending symbols on StockTwits."""
    url = f"{STOCKTWITS_API_BASE}/trending/symbols.json"

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            symbols = r.json().get("symbols", [])
            return [s.get("symbol", "") for s in symbols[:10] if s.get("symbol")]
        return []
    except Exception:
        return []


def get_symbol_stream(symbol, limit=5):
    """Fetch recent messages for a symbol."""
    url = f"{STOCKTWITS_API_BASE}/streams/symbol/{symbol}.json"
    params = {"limit": limit}

    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            messages = r.json().get("messages", [])
            return messages
        return []
    except Exception:
        return []


# ============================================================
# OAuth Flow (for initial setup)
# ============================================================
def get_auth_url():
    """Generate the OAuth authorization URL for StockTwits."""
    if not STOCKTWITS_CLIENT_ID:
        print("  StockTwits: Missing STOCKTWITS_CLIENT_ID")
        return None

    url = (
        f"https://api.stocktwits.com/api/2/oauth/authorize"
        f"?client_id={STOCKTWITS_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri=https://msli2233bin.github.io/broadfsc-automation/"
    )
    return url


def exchange_code_for_token(code):
    """Exchange OAuth authorization code for access token."""
    url = f"{STOCKTWITS_API_BASE}/oauth/token"
    payload = {
        "client_id": STOCKTWITS_CLIENT_ID,
        "client_secret": STOCKTWITS_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://msli2233bin.github.io/broadfsc-automation/",
    }

    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        access_token = data.get("access_token")
        print(f"  StockTwits: Got access token: {access_token[:20]}...")
        return access_token
    except Exception as e:
        print(f"  StockTwits: Token exchange failed: {e}")
        return None


# ============================================================
# Smart Content with Trending Data
# ============================================================
def generate_stocktwits_smart_content():
    """Generate a StockTwits message referencing trending symbols."""
    trending = get_trending_symbols()

    if not GROQ_API_KEY:
        if trending:
            top = trending[0]
            return f"${top} on the move. Watching key levels. #Trading"
        return "$SPY Key levels to watch. #Trading"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%b %d")
        persona = get_daily_persona(platform_shift=5)

        trending_str = ", ".join(["$" + s for s in trending[:5]]) if trending else "$SPY, $QQQ, $AAPL"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["emoji"] + " " + persona["name"] + " — " + persona["title"] + "\n"
                    "STYLE: " + persona["style"] + "\n\n"
                    "Write ONE StockTwits message for " + day + ", " + date_str + ".\n"
                    "TRENDING NOW: " + trending_str + "\n\n"
                    "Pick ONE trending symbol and give an actionable take.\n\n"
                    "CRITICAL RULES:\n"
                    "- MAXIMUM 140 characters (hard limit)\n"
                    "- MUST include the cashtag of your chosen symbol (e.g., $AAPL)\n"
                    "- Must be punchy, actionable, and timely\n"
                    "- Stay in character as " + persona["name"] + "\n"
                    "- Do NOT promise returns or give financial advice\n"
                    "- No disclaimers\n"
                    "- End with one hashtag"
                )
            }],
            max_tokens=80,
            temperature=0.9
        )

        text = response.choices[0].message.content.strip()

        if "$" not in text:
            tags = persona["hashtags"]
            if tags:
                cashtag = tags[0]
                text = text[:140 - len(cashtag) - 1] + " " + cashtag

        if len(text) > 140:
            text = text[:137] + "..."

        return text

    except Exception as e:
        print(f"  StockTwits: Smart generation failed ({e})")
        return generate_stocktwits_content()


# ============================================================
# Main
# ============================================================
def post_to_stocktwits():
    """Main entry: generate content and post to StockTwits."""
    print("\n📊 StockTwits ===")

    content = generate_stocktwits_smart_content()

    if "$" not in content:
        content = "$SPY " + content

    if len(content) > 140:
        content = content[:137] + "..."

    print(f"  StockTwits: Content ({len(content)} chars): {content}")
    return post_stocktwits_message(content)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "post":
            post_to_stocktwits()
        elif cmd == "trending":
            symbols = get_trending_symbols()
            print("Trending: " + ", ".join(["$" + s for s in symbols]))
        elif cmd == "auth-url":
            url = get_auth_url()
            if url:
                print(f"Visit: {url}")
        elif cmd == "exchange":
            code = sys.argv[2] if len(sys.argv) > 2 else None
            if code:
                exchange_code_for_token(code)
            else:
                print("Usage: stocktwits_poster.py exchange <code>")
        else:
            print("Usage: stocktwits_poster.py [post|trending|auth-url|exchange <code>]")
    else:
        post_to_stocktwits()
