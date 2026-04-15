"""
BroadFSC Global Market Pre-Market Briefing System
Sends targeted market insights 30 min before each major market opens.
Covers: US, Europe, Asia-Pacific, Middle East, Latin America.

GitHub Actions cron schedule: runs every 30 minutes.
Only sends when it's 30 min before a market open.
"""

import os
import sys
import datetime
import requests
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

DISCLAIMER = (
    "\n\n<i>Risk Disclaimer: Investment involves risk. "
    "Past performance is not indicative of future results. "
    "Please consult a licensed advisor before investing.</i>"
)

# ============================================================
# Global Market Schedule (UTC times, 30 min before open)
# Weekend = no US/Europe trading; Asia/Middle East may trade
# ============================================================
# Format: (hour_utc, minute_utc, market_name, target_region, emoji)
MARKET_SCHEDULE = [
    # --- Asia-Pacific Markets ---
    (0,  0, "Australia (ASX)",        "APAC",          "🇦🇺"),   # Open 00:30 UTC -> send 00:00
    (0, 30, "Japan (Nikkei/TSE)",      "APAC",          "🇯🇵"),   # Open 01:00 UTC -> send 00:30
    (0, 30, "South Korea (KOSPI)",     "APAC",          "🇰🇷"),   # Open 01:00 UTC -> send 00:30
    (0, 30, "China A-Shares",          "APAC",          "🇨🇳"),   # Open 01:00 UTC -> send 00:30 (for reference)
    (1,  0, "Hong Kong (HKEX)",       "APAC",          "🇭🇰"),   # Open 01:30 UTC -> send 01:00
    (1,  0, "Singapore (SGX)",        "APAC",          "🇸🇬"),   # Open 01:30 UTC -> send 01:00
    (3, 30, "India (NSE/BSE)",         "South Asia",    "🇮🇳"),   # Open 04:00 UTC -> send 03:30

    # --- Middle East Markets ---
    (5,  30, "Saudi Arabia (Tadawul)", "Middle East",   "🇸🇦"),   # Open 06:00 UTC -> send 05:30
    (5,  30, "UAE (DFM/ADX)",          "Middle East",   "🇦🇪"),   # Open 06:00 UTC -> send 05:30

    # --- European Markets ---
    (7,  0, "UK (LSE)",                "Europe",        "🇬🇧"),   # Open 08:00 UTC -> send 07:30 (winter 07:00)
    (7,  0, "Germany (Xetra)",          "Europe",        "🇩🇪"),   # Open 09:00 CET -> send 07:00/08:00 UTC
    (7,  0, "France (Euronext)",        "Europe",        "🇫🇷"),   # Open 09:00 CET -> send 07:00/08:00 UTC
    (7, 30, "Europe Main Session",      "Europe",        "🇪🇺"),   # Consolidated EU briefing at 08:00 UTC

    # --- Americas ---
    (13, 0, "Brazil (B3)",             "Latin America", "🇧🇷"),   # Open 10:00 BRT -> send 13:00 UTC
    (13, 30, "US Pre-Market Briefing",  "North America", "🇺🇸"),   # US open 14:30 UTC -> send 13:30
    (18, 30, "US After-Hours Summary",  "North America", "🇺🇸"),   # US close 21:00 UTC -> send 18:30 for after-hours movers
]

# Grouped schedule: only send ONE consolidated message per region per session
# to avoid spamming the channel with 6+ messages in 2 hours
REGION_SESSIONS = {
    # Asia morning (all open within 1.5 hours)
    "APAC":     {"hour": 0, "minute": 0,  "markets": "Japan, South Korea, Hong Kong, Singapore, Australia, India"},
    # Middle East
    "Middle East": {"hour": 5, "minute": 30, "markets": "Saudi Arabia (Tadawul), UAE (DFM/ADX)"},
    # Europe morning
    "Europe":   {"hour": 7, "minute": 0,  "markets": "UK (LSE), Germany (Xetra), France (Euronext)"},
    # Americas
    "Americas": {"hour": 13, "minute": 30, "markets": "US (NYSE/NASDAQ), Brazil (B3)"},
}

# Weekend check: Mon=0 ... Sun=6
# Asia trades Mon-Fri, Middle East Sun-Thu, US/Europe Mon-Fri
WEEKEND_SKIP = {
    "APAC":         [5, 6],   # Skip Saturday, Sunday
    "Middle East":  [5, 6],   # Skip Friday, Saturday (Saudi/UAE)
    "Europe":       [5, 6],   # Skip Saturday, Sunday
    "Americas":     [5, 6],   # Skip Saturday, Sunday
}

# Region-specific content focus
REGION_FOCUS = {
    "APAC": (
        "Focus on: Asian market movers, China economic data, RBA/BOJ policy signals, "
        "Asia-Pacific trade flows, semiconductor and tech sector trends."
    ),
    "Middle East": (
        "Focus on: Oil price trends (Brent/WTI), OPEC+ developments, regional geopolitics, "
        "Saudi Vision 2030 sectors, UAE economic diversification, GCC sovereign bond moves."
    ),
    "Europe": (
        "Focus on: ECB policy signals, Eurozone inflation/GDP data, Bank of England decisions, "
        "European energy markets, EU regulatory changes, DAX/FTSE/CAC key levels."
    ),
    "Americas": (
        "Focus on: Fed policy expectations, US CPI/NFP/fomc minutes, S&P 500/NASDAQ/Dow futures, "
        "earnings season highlights, US Treasury yields, Latin America FX and commodity impacts."
    ),
}

# Fallback content templates (when no GROQ_API_KEY)
FALLBACK_TEMPLATES = {
    "APAC": (
        "{emoji} ASIA PRE-MARKET BRIEFING | {date}\n\n"
        "{markets}\n\n"
        "Key factors to watch today:\n"
        "- Overnight US market close and futures direction\n"
        "- BOJ/RBA/PBOC policy signals\n"
        "- China PMI and trade data releases\n"
        "- Semiconductor sector momentum (TSMC, Samsung)\n"
        "- Asia FX movements (JPY, CNY, AUD)\n\n"
        "Stay ahead of Asian session volatility.\n\n"
        "Learn more: broadfsc.com/different"
    ),
    "Middle East": (
        "{emoji} MIDDLE EAST PRE-MARKET BRIEFING | {date}\n\n"
        "{markets}\n\n"
        "Key factors to watch today:\n"
        "- Oil prices (Brent/WTI) and OPEC+ developments\n"
        "- Regional geopolitical updates\n"
        "- GCC equity fund flows\n"
        "- Saudi Aramco and regional blue chips\n"
        "- UAE real estate and tourism sector trends\n\n"
        "Position for Gulf market opportunities.\n\n"
        "Learn more: broadfsc.com/different"
    ),
    "Europe": (
        "{emoji} EUROPE PRE-MARKET BRIEFING | {date}\n\n"
        "{markets}\n\n"
        "Key factors to watch today:\n"
        "- ECB rate decision expectations\n"
        "- Eurozone flash PMI and inflation data\n"
        "- Bank of England policy signals\n"
        "- European energy prices (TTF gas)\n"
        "- DAX 40, CAC 40, FTSE 100 key technicals\n\n"
        "Prepare for European session moves.\n\n"
        "Learn more: broadfsc.com/different"
    ),
    "Americas": (
        "{emoji} AMERICAS PRE-MARKET BRIEFING | {date}\n\n"
        "{markets}\n\n"
        "Key factors to watch today:\n"
        "- US stock futures (S&P, NASDAQ, Dow)\n"
        "- Fed policy expectations and FOMC minutes\n"
        "- Key economic releases (CPI, NFP, GDP)\n"
        "- Earnings season highlights\n"
        "- US 10Y Treasury yield and USD index\n"
        "- Latin America: BRL/MXN FX, Bovespa trends\n\n"
        "Get ready for the main session.\n\n"
        "Learn more: broadfsc.com/different"
    ),
}

REGION_EMOJIS = {
    "APAC": "🌏",
    "Middle East": "🌍",
    "Europe": "🇪🇺",
    "Americas": "🌎",
}


# ============================================================
# Core Functions
# ============================================================

def check_which_session(now_utc):
    """Determine which market session briefing should run now (if any)."""
    matched = []
    for region, session in REGION_SESSIONS.items():
        if now_utc.hour == session["hour"] and now_utc.minute == session["minute"]:
            if now_utc.weekday() not in WEEKEND_SKIP[region]:
                matched.append(region)
    return matched


def generate_ai_content(region, focus_text):
    """Use Groq API to generate market-specific briefing."""
    if not GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{
                "role": "user",
                "content": (
                    f"You are a professional market analyst at BroadFSC. "
                    f"Write a concise pre-market briefing for {region} markets.\n\n"
                    f"{focus_text}\n\n"
                    f"Requirements:\n"
                    f"- Format as a Telegram message with clear bullet points\n"
                    f"- Keep it under 500 characters\n"
                    f"- Be specific with current market themes\n"
                    f"- Use a professional but engaging tone\n"
                    f"- End with: Learn more: broadfsc.com/different\n"
                    f"- NEVER promise guaranteed returns"
                )
            }],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  AI generation failed: {e}")
        return None


def get_fallback_content(region):
    """Generate fallback content when AI is unavailable."""
    now = datetime.datetime.utcnow()
    template = FALLBACK_TEMPLATES[region]
    session = REGION_SESSIONS[region]
    emoji = REGION_EMOJIS[region]
    return template.format(
        emoji=emoji,
        date=now.strftime("%Y-%m-%d"),
        markets=session["markets"]
    )


def send_telegram(text):
    """Send message to Telegram channel."""
    if not BOT_TOKEN or not CHANNEL_ID:
        print("  FAIL: Missing BOT_TOKEN or CHANNEL_ID")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text + DISCLAIMER,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            msg_id = r.json()['result']['message_id']
            print(f"  Sent successfully! Message ID: {msg_id}")
            return True
        else:
            print(f"  FAIL: HTTP {r.status_code} - {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


# ============================================================
# Main
# ============================================================
def main():
    now_utc = datetime.datetime.utcnow()
    weekday = now_utc.weekday()
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    print(f"BroadFSC Pre-Market Briefing System")
    print(f"Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M')} ({weekday_names[weekday]})")
    print(f"BOT_TOKEN: {'SET' if BOT_TOKEN else 'NOT SET'}")
    print(f"CHANNEL_ID: {CHANNEL_ID if CHANNEL_ID else 'NOT SET'}")
    print(f"GROQ_API_KEY: {'SET' if GROQ_API_KEY else 'NOT SET (using fallback)'}")
    print()

    # Check which sessions should fire
    sessions = check_which_session(now_utc)

    if not sessions:
        print(f"No market session scheduled at this time.")
        print(f"Next sessions (UTC):")
        for region, s in REGION_SESSIONS.items():
            skip_days = [weekday_names[d] for d in WEEKEND_SKIP[region]]
            print(f"  {region}: {s['hour']:02d}:{s['minute']:02d} UTC (skip: {', '.join(skip_days)})")
        print("\nNo messages sent. Exiting.")
        return

    # Generate and send for each matched session
    for region in sessions:
        session = REGION_SESSIONS[region]
        focus = REGION_FOCUS[region]
        emoji = REGION_EMOJIS[region]

        print(f"{emoji} {region} Pre-Market Briefing")
        print(f"  Markets: {session['markets']}")
        print(f"  UTC schedule: {session['hour']:02d}:{session['minute']:02d}")

        # Try AI first, fallback to template
        content = generate_ai_content(region, focus)
        if not content:
            content = get_fallback_content(region)
            print(f"  Using fallback content")

        # Send
        success = send_telegram(content)
        print(f"  Result: {'SUCCESS' if success else 'FAILED'}")
        print()

    print("Done!")


if __name__ == "__main__":
    main()
