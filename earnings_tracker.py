"""
BroadFSC Earnings Tracker
Scans upcoming earnings reports for major stocks, generates AI analysis,
and pushes to Telegram channel + Discord community.

Runs daily via GitHub Actions on weekdays.
Data source: yfinance (free, no API key needed)
AI: Groq (free tier)
"""

import os
import sys
import datetime
import requests
import json

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
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Fallback: read from .env file
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
                key = key.strip()
                val = val.strip()
                if key == "GROQ_API_KEY" and not GROQ_API_KEY:
                    GROQ_API_KEY = val
                elif key == "TELEGRAM_BOT_TOKEN" and not BOT_TOKEN:
                    BOT_TOKEN = val

DISCLAIMER = (
    "\n\n<i>Risk Disclaimer: Investment involves risk. "
    "Past performance is not indicative of future results. "
    "Please consult a licensed advisor before investing.</i>"
)

# ============================================================
# Ticker Universe — major global stocks that matter to our audience
# ============================================================
US_LARGE_CAP = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
    "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "UBER", "SQ",
    # Finance
    "JPM", "BAC", "GS", "MS", "V", "MA", "C", "WFC",
    # Healthcare
    "JNJ", "PFE", "UNH", "ABBV", "MRK", "LLY", "TMO",
    # Energy
    "XOM", "CVX", "COP", "SLB",
    # Consumer
    "WMT", "COST", "TGT", "HD", "NKE", "MCD", "SBUX", "DIS",
    # Industrial
    "BA", "CAT", "GE", "HON",
    # Telecom
    "T", "VZ", "TMUS",
]

ASIA_TICKERS = [
    # Japan
    "7203.T", "6758.T", "6861.T", "9984.T",  # Toyota, Sony, Keyence, SoftBank
    # Korea
    "005930.KS", "000660.KS",  # Samsung, SK Hynix
    # Hong Kong / China
    "9988.HK", "0700.HK", "3690.HK",  # Alibaba, Tencent, Meituan
    # India
    "INFY", "WIT", "HDB", "IBN",
    # Australia
    "BHP", "RIO", "CBA.AX",
]

EUROPE_TICKERS = [
    "SAP", "ASML", "NVO", "AZN", "SIE.DE", "NESN.SW",
]

ALL_TICKERS = US_LARGE_CAP + ASIA_TICKERS + EUROPE_TICKERS

# ============================================================
# Data Fetching
# ============================================================
def get_earnings_this_week():
    """Fetch upcoming earnings for all tracked tickers."""
    import yfinance as yf

    today = datetime.date.today()
    week_end = today + datetime.timedelta(days=7)
    earnings = []

    print(f"Scanning earnings: {today} to {week_end}")
    print(f"Total tickers to check: {len(ALL_TICKERS)}")

    for ticker_str in ALL_TICKERS:
        try:
            tk = yf.Ticker(ticker_str)
            cal = tk.calendar
            if not cal:
                continue

            ed = cal.get('Earnings Date')
            if not ed:
                continue

            # Normalize to list
            dates = ed if isinstance(ed, list) else [ed]

            for d in dates:
                if isinstance(d, datetime.date) and today <= d <= week_end:
                    eps_avg = cal.get('Earnings Average')
                    eps_high = cal.get('Earnings High')
                    eps_low = cal.get('Earnings Low')
                    rev_avg = cal.get('Revenue Average')
                    rev_high = cal.get('Revenue High')
                    rev_low = cal.get('Revenue Low')

                    # Get current price for context
                    price = None
                    try:
                        hist = tk.history(period="2d")
                        if not hist.empty:
                            price = round(hist['Close'].iloc[-1], 2)
                    except Exception:
                        pass

                    earnings.append({
                        'ticker': ticker_str,
                        'date': d,
                        'eps_avg': eps_avg,
                        'eps_high': eps_high,
                        'eps_low': eps_low,
                        'rev_avg': rev_avg,
                        'rev_high': rev_high,
                        'rev_low': rev_low,
                        'price': price,
                    })
        except Exception as e:
            # Silently skip — yfinance can be flaky
            pass

    # Sort by date
    earnings.sort(key=lambda x: (x['date'], x['ticker']))
    print(f"Found {len(earnings)} earnings reports this week")
    return earnings


def get_company_name(ticker_str):
    """Get company name from ticker, with common fallbacks."""
    names = {
        "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet",
        "AMZN": "Amazon", "NVDA": "NVIDIA", "META": "Meta Platforms",
        "TSLA": "Tesla", "NFLX": "Netflix", "AMD": "AMD", "INTC": "Intel",
        "CRM": "Salesforce", "ORCL": "Oracle", "ADBE": "Adobe",
        "PYPL": "PayPal", "UBER": "Uber", "SQ": "Block",
        "JPM": "JPMorgan Chase", "BAC": "Bank of America", "GS": "Goldman Sachs",
        "MS": "Morgan Stanley", "V": "Visa", "MA": "Mastercard",
        "C": "Citigroup", "WFC": "Wells Fargo",
        "JNJ": "Johnson & Johnson", "PFE": "Pfizer", "UNH": "UnitedHealth",
        "ABBV": "AbbVie", "MRK": "Merck", "LLY": "Eli Lilly", "TMO": "Thermo Fisher",
        "XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips", "SLB": "Schlumberger",
        "WMT": "Walmart", "COST": "Costco", "TGT": "Target", "HD": "Home Depot",
        "NKE": "Nike", "MCD": "McDonald's", "SBUX": "Starbucks", "DIS": "Disney",
        "BA": "Boeing", "CAT": "Caterpillar", "GE": "GE Aerospace", "HON": "Honeywell",
        "T": "AT&T", "VZ": "Verizon", "TMUS": "T-Mobile",
        "7203.T": "Toyota", "6758.T": "Sony", "6861.T": "Keyence", "9984.T": "SoftBank",
        "005930.KS": "Samsung", "000660.KS": "SK Hynix",
        "9988.HK": "Alibaba HK", "0700.HK": "Tencent", "3690.HK": "Meituan",
        "INFY": "Infosys", "WIT": "Wipro", "HDB": "HDFC Bank", "IBN": "ICICI Bank",
        "BHP": "BHP Group", "RIO": "Rio Tinto", "CBA.AX": "CBA",
        "SAP": "SAP", "ASML": "ASML", "NVO": "Novo Nordisk",
        "AZN": "AstraZeneca", "SIE.DE": "Siemens", "NESN.SW": "Nestle",
    }
    return names.get(ticker_str, ticker_str)


# ============================================================
# Content Generation
# ============================================================
def format_earnings_brief(earnings_list):
    """Format earnings data into a readable brief without AI (fallback)."""
    if not earnings_list:
        return None

    today = datetime.date.today()
    lines = [f"<b>📊 Earnings Calendar: Week of {today.strftime('%b %d')}</b>\n"]

    current_date = None
    for e in earnings_list:
        if e['date'] != current_date:
            current_date = e['date']
            day_name = current_date.strftime("%A, %b %d")
            lines.append(f"\n📅 <b>{day_name}</b>")

        name = get_company_name(e['ticker'])
        price_str = f" @ ${e['price']}" if e['price'] else ""

        eps_str = ""
        if e['eps_avg'] is not None:
            eps_str = f" | EPS est: ${e['eps_avg']:.2f}"

        rev_str = ""
        if e['rev_avg'] is not None:
            rev_b = e['rev_avg'] / 1e9
            rev_str = f" | Rev est: ${rev_b:.1f}B"

        lines.append(f"  • {name} ({e['ticker']}){price_str}{eps_str}{rev_str}")

    lines.append("\n💡 Follow @BroadFSC for earnings analysis")
    return "\n".join(lines)


def generate_ai_earnings_analysis(earnings_list):
    """Use Groq AI to generate deep earnings analysis."""
    if not GROQ_API_KEY or not earnings_list:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        return None

    # Build earnings summary for AI
    today = datetime.date.today()
    summary_parts = []
    for e in earnings_list:
        name = get_company_name(e['ticker'])
        parts = [f"{name} ({e['ticker']}) on {e['date'].strftime('%b %d')}"]
        if e['eps_avg'] is not None:
            parts.append(f"EPS est: ${e['eps_avg']:.2f}")
            if e['eps_high'] and e['eps_low']:
                parts.append(f"range ${e['eps_low']:.2f}-${e['eps_high']:.2f}")
        if e['rev_avg'] is not None:
            rev_b = e['rev_avg'] / 1e9
            parts.append(f"Rev est: ${rev_b:.1f}B")
        if e['price']:
            parts.append(f"Last: ${e['price']}")
        summary_parts.append(" | ".join(parts))

    earnings_text = "\n".join(summary_parts)

    prompt = f"""You are a senior equity analyst at a global investment firm. Today is {today.strftime('%A, %B %d, %Y')}.

Key earnings reports coming up this week:

{earnings_text}

Write a concise, actionable earnings week preview (max 800 chars) for a Telegram channel audience of global investors. Structure:
1. Headline: 1-2 sentences on the key theme of this earnings week
2. Must-watch: Top 3 earnings that could move markets, and WHY
3. Key metrics to watch: What specific numbers matter (margins, guidance, segment growth)
4. Sector angle: Which sector narrative these earnings will confirm or challenge
5. Trading implication: One actionable insight

Be specific with numbers and tickers. No generic filler. No disclaimers."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        analysis = response.choices[0].message.content.strip()
        print("AI earnings analysis generated successfully")
        return analysis
    except Exception as e:
        print(f"AI generation failed: {e}")
        return None


# ============================================================
# Telegram + Discord Posting
# ============================================================
def send_telegram(text, channel_id=None):
    """Send message to Telegram channel."""
    cid = channel_id or CHANNEL_ID
    if not BOT_TOKEN or not cid:
        print("  Telegram: Missing BOT_TOKEN or CHANNEL_ID")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": text + DISCLAIMER,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            msg_id = r.json()['result']['message_id']
            print(f"  Telegram: Sent! Message ID: {msg_id}")
            if HAS_ANALYTICS:
                log_post(platform="telegram_en", post_type="earnings",
                         content_preview=text[:100], post_id=str(msg_id), status="success")
            return True
        else:
            print(f"  Telegram: FAIL HTTP {r.status_code} - {r.text[:200]}")
            if HAS_ANALYTICS:
                log_post(platform="telegram_en", post_type="earnings",
                         content_preview=text[:100], status="failed",
                         error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  Telegram: FAIL - {e}")
        if HAS_ANALYTICS:
            log_post(platform="telegram_en", post_type="earnings",
                     status="failed", error_msg=str(e)[:200])
        return False


def send_discord(text):
    """Post earnings analysis to Discord channel."""
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        print("  Discord: Missing DISCORD_BOT_TOKEN or DISCORD_CHANNEL_ID")
        return False

    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    # Discord limit 2000 chars
    if len(text) > 1900:
        text = text[:1897] + "..."

    payload = {"content": text}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            msg_id = r.json().get("id", "")
            print(f"  Discord: Posted! Message ID: {msg_id}")
            if HAS_ANALYTICS:
                log_post(platform="discord", post_type="earnings",
                         content_preview=text[:100], post_id=str(msg_id), status="success")
            return True
        else:
            print(f"  Discord: FAIL HTTP {r.status_code} - {r.text[:300]}")
            if HAS_ANALYTICS:
                log_post(platform="discord", post_type="earnings",
                         content_preview=text[:100], status="failed",
                         error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  Discord: FAIL - {e}")
        if HAS_ANALYTICS:
            log_post(platform="discord", post_type="earnings",
                     status="failed", error_msg=str(e)[:200])
        return False


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("BroadFSC Earnings Tracker")
    print(f"Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # Step 1: Fetch earnings data
    earnings = get_earnings_this_week()

    if not earnings:
        print("No earnings found this week. Exiting.")
        return

    # Step 2: Format calendar brief (for Telegram)
    calendar_brief = format_earnings_brief(earnings)
    if calendar_brief:
        print(f"\nCalendar brief ({len(calendar_brief)} chars):")
        print(calendar_brief[:200] + "...")

    # Step 3: Generate AI analysis (for Telegram + Discord)
    ai_analysis = generate_ai_earnings_analysis(earnings)
    if ai_analysis:
        print(f"\nAI analysis ({len(ai_analysis)} chars):")
        print(ai_analysis[:200] + "...")
    else:
        print("\nAI analysis: fallback mode (no Groq)")

    # Step 4: Build Telegram message
    # Telegram: calendar + AI analysis combined
    tg_parts = []
    if calendar_brief:
        tg_parts.append(calendar_brief)
    if ai_analysis:
        tg_parts.append(f"\n\n<b>🔍 Analyst Preview</b>\n{ai_analysis}")

    tg_message = "\n".join(tg_parts)

    # Step 5: Build Discord message (richer, longer format)
    ds_parts = ["📊 **EARNINGS WEEK PREVIEW** 📊\n"]
    if calendar_brief:
        # Strip HTML tags for Discord
        ds_brief = calendar_brief.replace("<b>", "**").replace("</b>", "**")
        ds_parts.append(ds_brief)
    if ai_analysis:
        ds_parts.append(f"\n🔍 **Analyst Preview**\n{ai_analysis}")

    ds_message = "\n".join(ds_parts)

    # Step 6: Post
    print("\n--- Posting ---")
    tg_ok = send_telegram(tg_message)
    ds_ok = send_discord(ds_message)

    print(f"\nResults: Telegram={'OK' if tg_ok else 'SKIP/FAIL'}, Discord={'OK' if ds_ok else 'SKIP/FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
