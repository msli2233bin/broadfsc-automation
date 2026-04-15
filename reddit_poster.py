"""
BroadFSC Reddit Auto-Poster
Posts daily market analysis to relevant subreddits.
IMPORTANT: Reddit requires account age > 2 weeks and minimum karma.
           Set REDDIT_ENABLED=true in GitHub Secrets after account is ready.

Target subreddits: r/investing, r/stocks, r/Daytrading, r/StockMarket,
                   r/investment, r/financialindependence, r/wallstreetbets (casual tone)

Requirements:
    REDDIT_CLIENT_ID     - Reddit app client_id
    REDDIT_CLIENT_SECRET - Reddit app client_secret
    REDDIT_USERNAME      - Reddit username
    REDDIT_PASSWORD      - Reddit password
    REDDIT_ENABLED       - Set to "true" to enable (default: false)
    GROQ_API_KEY         - For AI content generation
    TELEGRAM_BOT_TOKEN   - For notifications
    TELEGRAM_CHANNEL_ID  - For success notifications
"""

import os
import sys
import datetime
import requests
import json

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
REDDIT_ENABLED = os.environ.get("REDDIT_ENABLED", "false").lower() == "true"
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

TELEGRAM_LINK = "https://t.me/BroadFSC"
WEBSITE_LINK = "https://www.broadfsc.com/different"

# Subreddits and their tone/style
SUBREDDITS = [
    {"name": "investing", "style": "analytical"},
    {"name": "stocks", "style": "informative"},
    {"name": "StockMarket", "style": "professional"},
    {"name": "investment", "style": "educational"},
    {"name": "financialindependence", "style": "long-term"},
]

# Rotation: post to different subreddits each day to avoid spam
# Only 1 subreddit per day, rotating through the list
POSTS_PER_DAY = 1


def get_reddit_token():
    """Authenticate with Reddit API."""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("  FAIL: Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET")
        return None

    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {"grant_type": "password", "username": REDDIT_USERNAME, "password": REDDIT_PASSWORD}
    headers = {"User-Agent": "BroadFSC-Market-Bot/1.0"}

    try:
        r = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers, timeout=15)
        if r.status_code == 200:
            token = r.json()["access_token"]
            print("  Reddit auth success")
            return token
        else:
            print("  Reddit auth FAIL: HTTP " + str(r.status_code) + " - " + r.text[:200])
            return None
    except Exception as e:
        print("  Reddit auth FAIL: " + str(e))
        return None


def generate_reddit_post(subreddit, style):
    """Use AI to generate a Reddit post tailored to the subreddit."""
    if not GROQ_API_KEY:
        return get_fallback_post(subreddit, style)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day_of_week = now.strftime("%A")

        style_prompts = {
            "analytical": "Write an analytical market post with data-driven insights. Use technical terms appropriately.",
            "informative": "Write an informative post explaining market concepts. Be educational and accessible.",
            "professional": "Write a professional market analysis. Reference macro trends and sector rotations.",
            "educational": "Write an educational post about investment strategy. Focus on long-term wealth building.",
            "long-term": "Write about long-term investment strategies. Focus on portfolio diversification and compounding.",
        }

        prompt = (
            "You are a professional market analyst at Broad Investment Securities. "
            "Write a Reddit post for r/{subreddit}.\n\n"
            "Today is {day}. Style: {style_desc}\n\n"
            "Requirements:\n"
            "- Compelling title (max 100 chars)\n"
            "- Body: 200-400 words, well-structured with paragraphs\n"
            "- Include 2-3 specific market observations or data points\n"
            "- Be genuine and valuable, NOT promotional\n"
            "- End subtly: 'For more daily market briefings, check out the link in my profile'\n"
            "- NO direct links to our website in the post body (Reddit spam filter)\n"
            "- NO guaranteed returns or specific buy/sell recommendations\n"
            "- Format as JSON: {{\"title\": \"...\", \"body\": \"...\"}}"
        ).format(
            subreddit=subreddit,
            day=day_of_week,
            style_desc=style_prompts.get(style, "Write a professional market analysis."),
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.8
        )
        content = response.choices[0].message.content.strip()

        # Parse JSON response
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        post = json.loads(content)
        return post.get("title", "Daily Market Analysis"), post.get("body", "")

    except Exception as e:
        print("  AI generation failed: " + str(e))
        return get_fallback_post(subreddit, style)


def get_fallback_post(subreddit, style):
    """Generate fallback Reddit post when AI is unavailable."""
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%B %d, %Y")

    titles = [
        "Weekly Market Outlook: Key Trends to Watch This Week",
        "How Global Events Are Shaping Investment Opportunities",
        "Understanding Market Sentiment in Current Conditions",
        "Long-Term vs Short-Term: A Balanced Investment Approach",
    ]

    bodies = [
        "With markets navigating through a period of heightened uncertainty, "
        "several key trends deserve attention from investors:\n\n"
        "1. **Global Interest Rate Environment** - Central banks across major economies "
        "continue to calibrate monetary policy. The interplay between Fed, ECB, and BOJ "
        "decisions creates both risks and opportunities across asset classes.\n\n"
        "2. **Sector Rotation Patterns** - Recent market action suggests continued rotation "
        "between growth and value sectors. Understanding these flows can help position "
        "portfolios for different scenarios.\n\n"
        "3. **Geopolitical Risk Premium** - Ongoing geopolitical developments continue "
        "to influence commodity prices and supply chain dynamics, affecting sectors from "
        "energy to technology.\n\n"
        "What's your take on the current market environment? "
        "For daily market briefings, check out the link in my profile.\n\n"
        "*Disclaimer: This is for educational purposes only. Not financial advice.*",
    ]

    import random
    idx = now.timetuple().tm_yday % len(titles)
    return titles[idx], bodies[0].format(date=date_str)


def submit_reddit_post(token, subreddit, title, body):
    """Submit a post to Reddit."""
    headers = {
        "Authorization": "bearer " + token,
        "User-Agent": "BroadFSC-Market-Bot/1.0",
    }
    data = {
        "title": title,
        "text": body,
        "sr": subreddit,
        "kind": "self",
        "api_type": "json",
    }

    try:
        r = requests.post(
            "https://oauth.reddit.com/api/submit",
            headers=headers,
            data=data,
            timeout=15
        )
        if r.status_code == 200:
            result = r.json()
            # Reddit returns success in different formats
            if "json" in result and "data" in result["json"]:
                url = result["json"]["data"].get("url", "unknown")
                print("  Posted to r/" + subreddit + ": " + url)
                return True
            # Check for errors
            if "json" in result and "errors" in result["json"]:
                errors = result["json"]["errors"]
                if errors:
                    print("  Reddit errors: " + str(errors))
                    return False
            print("  Posted to r/" + subreddit + " (check subreddit)")
            return True
        else:
            print("  Reddit post FAIL: HTTP " + str(r.status_code) + " - " + r.text[:200])
            return False
    except Exception as e:
        print("  Reddit post FAIL: " + str(e))
        return False


def notify_telegram(message):
    """Send notification to Telegram channel."""
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass


def main():
    print("=" * 50)
    print("BroadFSC Reddit Auto-Poster")
    print("=" * 50)

    if not REDDIT_ENABLED:
        print("Reddit posting is DISABLED.")
        print("To enable, set REDDIT_ENABLED=true in GitHub Secrets")
        print("and configure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, etc.")
        print()
        print("Reminder: Reddit requires account age > 2 weeks and karma.")
        print("No action taken. Exiting.")
        return

    # Check credentials
    missing = []
    if not REDDIT_CLIENT_ID:
        missing.append("REDDIT_CLIENT_ID")
    if not REDDIT_CLIENT_SECRET:
        missing.append("REDDIT_CLIENT_SECRET")
    if not REDDIT_USERNAME:
        missing.append("REDDIT_USERNAME")
    if not REDDIT_PASSWORD:
        missing.append("REDDIT_PASSWORD")

    if missing:
        print("Missing credentials: " + ", ".join(missing))
        print("Please add them to GitHub Secrets.")
        return

    now = datetime.datetime.utcnow()
    print("Current UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print()

    # Rotate subreddits by day of year
    day_index = now.timetuple().tm_yday % len(SUBREDDITS)
    target = SUBREDDITS[day_index]
    subreddit = target["name"]
    style = target["style"]

    print("Today's target: r/" + subreddit + " (style: " + style + ")")
    print()

    # Step 1: Authenticate
    print("Step 1: Authenticating with Reddit...")
    token = get_reddit_token()
    if not token:
        notify_telegram("Reddit poster failed: authentication error")
        print("EXITING: Authentication failed.")
        return

    # Step 2: Generate content
    print("Step 2: Generating content...")
    title, body = generate_reddit_post(subreddit, style)
    print("  Title: " + title[:80])
    print("  Body length: " + str(len(body)) + " chars")

    # Step 3: Submit
    print("Step 3: Submitting to r/" + subreddit + "...")
    success = submit_reddit_post(token, subreddit, title, body)

    if success:
        notify_telegram("Reddit post published: r/" + subreddit + "\n" + title)
        print()
        print("SUCCESS! Post submitted to r/" + subreddit)
    else:
        notify_telegram("Reddit post failed: submission error to r/" + subreddit)
        print()
        print("FAILED: Could not submit post.")

    print("=" * 50)


if __name__ == "__main__":
    main()
