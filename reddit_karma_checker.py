"""
BroadFSC Reddit Karma Checker
Uses Playwright browser to check Reddit karma (bypasses API IP ban).
Runs on GitHub Actions where Reddit is accessible.

No Reddit App / OAuth credentials needed.
Only requires: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
"""

import os
import sys
import json
import datetime
import re

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "Only-Character4025")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

MIN_COMMENT_KARMA = 50
MIN_ACCOUNT_AGE_DAYS = 14


def check_karma_browser(username):
    """Check Reddit karma using Playwright browser (bypasses API IP ban)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # Fallback: try requests (will fail on blocked IPs but works from some networks)
        print("  Playwright not available, trying requests fallback...")
        return check_karma_requests(username)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to user profile
            url = f"https://www.reddit.com/user/{username}/"
            print(f"  Navigating to {url}")
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)

            # Check if blocked
            body_text = page.inner_text("body")
            if "blocked" in body_text.lower() and "network security" in body_text.lower():
                browser.close()
                return {"success": False, "error": "Browser also blocked by Reddit network security"}

            # Check if user not found
            if "sorry, nobody on reddit goes by that name" in body_text.lower() or "page not found" in body_text.lower():
                browser.close()
                return {"success": False, "error": f"User '{username}' not found"}

            # Try to extract karma from page content
            result = extract_karma_from_text(body_text, username)
            browser.close()
            return result

    except Exception as e:
        return {"success": False, "error": f"Browser error: {str(e)}"}


def extract_karma_from_text(text, username):
    """Extract karma numbers from Reddit profile page text."""
    link_karma = 0
    comment_karma = 0
    total_karma = 0

    # Pattern 1: "1,234 karma" or "1234 karma" or "1.2k karma"
    karma_matches = re.findall(r'([\d,]+(?:\.\d+)?[kK]?)\s*karma', text, re.IGNORECASE)
    if karma_matches:
        for i, k in enumerate(karma_matches):
            val = parse_karma_value(k)
            if i == 0:
                total_karma = val
            # Sometimes it shows post/comment separately

    # Pattern 2: Look for "Post karma" / "Comment karma" patterns
    post_match = re.search(r'(?:post|link)\s*karma[:\s]*([\d,]+(?:\.\d+)?[kK]?)', text, re.IGNORECASE)
    comment_match = re.search(r'(?:comment)\s*karma[:\s]*([\d,]+(?:\.\d+)?[kK]?)', text, re.IGNORECASE)

    if post_match:
        link_karma = parse_karma_value(post_match.group(1))
    if comment_match:
        comment_karma = parse_karma_value(comment_match.group(1))

    # If we got separate values, total is sum
    if link_karma > 0 or comment_karma > 0:
        total_karma = link_karma + comment_karma
    # If we only got total, estimate split
    elif total_karma > 0:
        link_karma = total_karma // 2
        comment_karma = total_karma - link_karma

    # Look for account age / "Cake day" pattern
    age_days = 0
    age_str = "Unknown"
    cake_match = re.search(r'cake\s*day[:\s]*(\w+\s+\d+,\s*\d{4})', text, re.IGNORECASE)
    if cake_match:
        try:
            cake_date = datetime.datetime.strptime(cake_match.group(1).strip(), "%B %d, %Y")
            age_days = (datetime.datetime.utcnow() - cake_date).days
            age_str = f"{age_days} days (since {cake_date.strftime('%Y-%m-%d')})"
        except:
            pass

    # Look for "X years ago" or "X months ago" for account age
    if age_days == 0:
        time_match = re.search(r'(\d+)\s*(year|month|day)s?\s*ago', text, re.IGNORECASE)
        if time_match:
            num = int(time_match.group(1))
            unit = time_match.group(2).lower()
            if unit == "year":
                age_days = num * 365
            elif unit == "month":
                age_days = num * 30
            elif unit == "day":
                age_days = num
            age_str = f"~{age_days} days"

    has_verified_email = "verified email" in text.lower() or "✓" in text

    # Check if we got any useful data
    if total_karma == 0 and age_days == 0:
        # Save page text for debugging (first 2000 chars)
        return {
            "success": False,
            "error": f"Could not extract karma from page. Text preview: {text[:500]}",
        }

    return {
        "success": True,
        "username": username,
        "link_karma": link_karma,
        "comment_karma": comment_karma,
        "total_karma": total_karma,
        "age_days": age_days,
        "age_str": age_str,
        "has_verified_email": has_verified_email,
        "ready_for_posting": comment_karma >= MIN_COMMENT_KARMA and age_days >= MIN_ACCOUNT_AGE_DAYS,
        "method": "browser",
    }


def parse_karma_value(s):
    """Parse karma value string like '1,234' or '1.2k' to int."""
    s = s.strip().replace(",", "")
    try:
        if s.lower().endswith("k"):
            return int(float(s[:-1]) * 1000)
        return int(float(s))
    except:
        return 0


def check_karma_requests(username):
    """Fallback: check karma via public API (may be IP blocked)."""
    import requests
    headers = {"User-Agent": "BroadFSC-Karma-Check/1.0"}
    try:
        r = requests.get(
            f"https://www.reddit.com/user/{username}/about.json",
            headers=headers, timeout=15
        )
        if r.status_code == 200:
            data = r.json().get("data", {})
            link_karma = data.get("link_karma", 0)
            comment_karma = data.get("comment_karma", 0)
            created_utc = data.get("created_utc", 0)
            has_verified_email = data.get("has_verified_email", False)

            if created_utc:
                created_date = datetime.datetime.utcfromtimestamp(created_utc)
                age_days = (datetime.datetime.utcnow() - created_date).days
                age_str = f"{age_days} days (since {created_date.strftime('%Y-%m-%d')})"
            else:
                age_days = 0
                age_str = "Unknown"

            return {
                "success": True,
                "username": username,
                "link_karma": link_karma,
                "comment_karma": comment_karma,
                "total_karma": link_karma + comment_karma,
                "age_days": age_days,
                "age_str": age_str,
                "has_verified_email": has_verified_email,
                "ready_for_posting": comment_karma >= MIN_COMMENT_KARMA and age_days >= MIN_ACCOUNT_AGE_DAYS,
                "method": "api",
            }
        elif r.status_code == 404:
            return {"success": False, "error": f"User '{username}' not found"}
        elif r.status_code == 403:
            return {"success": False, "error": "API blocked (403) — need browser method"}
        else:
            return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_telegram_message(result):
    """Format karma check result for Telegram."""
    if not result["success"]:
        return (
            f"🔴 <b>Reddit Karma Check FAILED</b>\n\n"
            f"User: u/{REDDIT_USERNAME}\n"
            f"Error: {result['error']}"
        )

    if result["ready_for_posting"]:
        status = "✅ READY FOR AUTO-POSTING"
    else:
        missing = []
        if result["comment_karma"] < MIN_COMMENT_KARMA:
            missing.append(f"Need {MIN_COMMENT_KARMA - result['comment_karma']} more comment karma")
        if result["age_days"] < MIN_ACCOUNT_AGE_DAYS:
            missing.append(f"Need {MIN_ACCOUNT_AGE_DAYS - result['age_days']} more days")
        status = f"⏳ NOT READY — {', '.join(missing)}"

    verified = "✅" if result.get("has_verified_email") else "❌"
    method = result.get("method", "unknown")

    return (
        f"📊 <b>Reddit Karma Report</b>\n\n"
        f"👤 User: u/{result['username']}\n"
        f"📅 Account age: {result['age_str']}\n"
        f"📝 Post Karma: <b>{result['link_karma']:,}</b>\n"
        f"💬 Comment Karma: <b>{result['comment_karma']:,}</b>\n"
        f"🏆 Total Karma: <b>{result['total_karma']:,}</b>\n"
        f"📧 Verified email: {verified}\n"
        f"🔧 Method: {method}\n\n"
        f"{status}\n\n"
        f"💡 Threshold: {MIN_COMMENT_KARMA} comment karma + {MIN_ACCOUNT_AGE_DAYS} days"
    )


def send_telegram(message):
    """Send notification to Telegram."""
    if not BOT_TOKEN or not CHANNEL_ID:
        print("  Telegram not configured, skipping notification")
        return

    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("  Telegram notification sent ✅")
        else:
            print(f"  Telegram send failed: HTTP {r.status_code}")
    except Exception as e:
        print(f"  Telegram send failed: {e}")


def main():
    print("=" * 50)
    print("BroadFSC Reddit Karma Checker")
    print("=" * 50)
    print(f"Checking: u/{REDDIT_USERNAME}")
    print(f"Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Check karma
    print("Fetching karma data...")
    result = check_karma_browser(REDDIT_USERNAME)

    if result["success"]:
        print(f"  Post Karma: {result['link_karma']:,}")
        print(f"  Comment Karma: {result['comment_karma']:,}")
        print(f"  Total Karma: {result['total_karma']:,}")
        print(f"  Account age: {result['age_str']}")
        print(f"  Ready for posting: {result['ready_for_posting']}")
        print(f"  Method: {result.get('method', 'unknown')}")
    else:
        print(f"  FAILED: {result['error'][:300]}")

    # Save history
    result["checked_at"] = datetime.datetime.utcnow().isoformat()
    history_file = "knowledge/reddit_karma_history.json"

    try:
        history = []
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

        history.append(result)
        if len(history) > 90:
            history = history[-90:]

        os.makedirs("knowledge", exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        print(f"  History saved ({len(history)} entries)")
    except Exception as e:
        print(f"  History save failed: {e}")

    # Send Telegram
    print()
    print("Sending Telegram notification...")
    msg = format_telegram_message(result)
    send_telegram(msg)

    print()
    print("=" * 50)

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
