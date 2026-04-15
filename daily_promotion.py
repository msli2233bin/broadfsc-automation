"""
BroadFSC Daily Promotion - Simplified Debug Version
For testing Telegram integration
"""

import os
import sys
import datetime
import requests

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

REQUIRED_DISCLAIMER = (
    "\n\nRisk Disclaimer: Investment involves risk. "
    "Past performance is not indicative of future results. "
    "Please consult a licensed advisor before investing."
)

# ============================================================
# Step 1: Check environment variables
# ============================================================
print(f"[1/4] Checking environment variables...")
print(f"  TELEGRAM_BOT_TOKEN: {'SET (' + BOT_TOKEN[:10] + '...)' if BOT_TOKEN else 'NOT SET'}")
print(f"  TELEGRAM_CHANNEL_ID: {CHANNEL_ID if CHANNEL_ID else 'NOT SET'}")
print(f"  GROQ_API_KEY: {'SET (' + GROQ_API_KEY[:8] + '...)' if GROQ_API_KEY else 'NOT SET'}")

# ============================================================
# Step 2: Generate content with AI (or use fallback)
# ============================================================
print(f"\n[2/4] Generating content...")
today = datetime.datetime.utcnow()
weekday = today.weekday()

topics = {
    0: "global market outlook and macroeconomic trends",
    1: "investment portfolio diversification strategies",
    2: "risk management in volatile financial markets",
    3: "emerging market opportunities for international investors",
    4: "asset allocation and long-term wealth building",
    5: "understanding investment advisory services and their benefits",
    6: "financial market trends and investment opportunities for the week ahead"
}

topic = topics[weekday]

if GROQ_API_KEY:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{
                "role": "user",
                "content": f"Write a professional market insight about: '{topic}'. "
                          f"Keep it under 280 characters. Include 1 actionable insight. "
                          f"End with: Learn more: broadfsc.com/different"
            }],
            max_tokens=300,
            temperature=0.75
        )
        content = response.choices[0].message.content
        print(f"  AI content generated: {len(content)} chars")
    except Exception as e:
        print(f"  AI generation failed: {e}")
        content = None
else:
    print("  No GROQ_API_KEY, using fallback content")
    content = None

if not content:
    content = (
        f"Daily Market Insight: {topic.capitalize()}\n\n"
        f"Markets continue to evolve with new opportunities emerging globally. "
        f"Stay informed and make data-driven decisions.\n\n"
        f"Learn more: broadfsc.com/different"
    )

# ============================================================
# Step 3: Send to Telegram
# ============================================================
print(f"\n[3/4] Sending to Telegram...")
if not BOT_TOKEN or not CHANNEL_ID:
    print("  FAIL: Missing BOT_TOKEN or CHANNEL_ID, cannot send")
    success = False
else:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": content + REQUIRED_DISCLAIMER,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"  SUCCESS! Message ID: {data['result']['message_id']}")
            success = True
        else:
            print(f"  FAIL: HTTP {r.status_code} - {r.text[:200]}")
            success = False
    except Exception as e:
        print(f"  FAIL: Exception - {e}")
        success = False

# ============================================================
# Step 4: Summary
# ============================================================
print(f"\n[4/4] Summary")
print(f"  Date: {today.strftime('%Y-%m-%d %H:%M')} UTC")
print(f"  Topic: {topic}")
print(f"  Telegram sent: {'YES' if success else 'NO'}")
print(f"\nDone!")
