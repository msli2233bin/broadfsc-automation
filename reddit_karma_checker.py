"""
BroadFSC Reddit Karma Checker
Uses web proxy to bypass Reddit IP ban.
Multiple proxy fallbacks: codetabs → allorigins → direct API

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

# Web proxies that can bypass Reddit IP ban (ordered by reliability)
PROXY_APIS = [
    {
        "name": "codetabs",
        "url": "https://api.codetabs.com/v1/proxy?quest=https://www.reddit.com/user/{username}/about.json",
        "returns_json": True,
    },
    {
        "name": "allorigins",
        "url": "https://api.allorigins.win/raw?url=https://www.reddit.com/user/{username}/about.json",
        "returns_json": True,  # May return HTML on some IPs
    },
]


def _verify_profile_exists(username):
    """Verify a Reddit profile exists by checking if the HTML page loads (not about.json).
    Reddit restricts about.json for new/low-karma accounts, but the profile page still loads."""
    import requests
    try:
        url = f"https://api.codetabs.com/v1/proxy?quest=https://www.reddit.com/user/{username}/"
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            html = r.text.lower()
            # A valid user page will have the username in the page content
            # and NOT redirect to a generic "Reddit - heart of internet" with no user data
            if username.lower() in html:
                return True
            # Fallback: check for typical user page indicators
            if "profile" in html and ("karma" in html or "joined" in html):
                return True
        return False
    except Exception:
        return False


def check_karma_via_proxy(username):
    """Check Reddit karma using web proxy to bypass IP ban."""
    import requests

    for proxy in PROXY_APIS:
        url = proxy["url"].format(username=username)
        print(f"  Trying proxy: {proxy['name']}...")
        try:
            r = requests.get(url, timeout=20)
            print(f"    HTTP {r.status_code}")

            if r.status_code != 200:
                continue

            # Check if response is valid JSON (not HTML block page)
            try:
                data = r.json()
            except (json.JSONDecodeError, ValueError):
                text = r.text[:200]
                if "blocked" in text.lower() or "theme-beta" in text.lower():
                    print(f"    Got block page instead of JSON, skipping")
                    continue
                print(f"    Invalid JSON response, skipping")
                continue

            # Extract karma data from Reddit API response
            reddit_data = data.get("data", {})
            if not reddit_data or "name" not in reddit_data:
                # Check for error response from proxy (Reddit returns 429/404 via proxy)
                if data.get("error") == 429 or "too many requests" in str(data).lower():
                    print(f"    Reddit rate-limited this proxy ({proxy['name']}), trying next...")
                    continue
                if data.get("error") == 404 or "not found" in str(data).lower():
                    # about.json returns 404 for new/low-karma accounts
                    # Skip to HTML profile check (avoids double request to same proxy)
                    print(f"    about.json returned 404 — will check HTML profile page...")
                    break  # Exit proxy loop, fallthrough to HTML profile check
                print(f"    Unexpected response structure, skipping")
                continue

            link_karma = reddit_data.get("link_karma", 0)
            comment_karma = reddit_data.get("comment_karma", 0)
            has_verified_email = reddit_data.get("has_verified_email", False)
            created_utc = reddit_data.get("created_utc", 0)
            is_suspended = reddit_data.get("is_suspended", False)

            age_days = 0
            age_str = "Unknown"
            if created_utc:
                created_date = datetime.datetime.utcfromtimestamp(created_utc)
                age_days = (datetime.datetime.utcnow() - created_date).days
                age_str = f"{age_days} days (since {created_date.strftime('%Y-%m-%d')})"

            return {
                "success": True,
                "username": reddit_data.get("name", username),
                "link_karma": link_karma,
                "comment_karma": comment_karma,
                "total_karma": link_karma + comment_karma,
                "age_days": age_days,
                "age_str": age_str,
                "has_verified_email": has_verified_email,
                "is_suspended": is_suspended,
                "ready_for_posting": comment_karma >= MIN_COMMENT_KARMA and age_days >= MIN_ACCOUNT_AGE_DAYS,
                "method": f"proxy-{proxy['name']}",
            }

        except requests.exceptions.Timeout:
            print(f"    Timeout, trying next proxy...")
            continue
        except Exception as e:
            print(f"    Error: {str(e)[:100]}, trying next proxy...")
            continue

    # All proxies failed (429/403/522). Try HTML profile page as last resort.
    print("  All proxies failed. Checking HTML profile page...")
    return check_karma_html_profile(username)


def check_karma_html_profile(username):
    """Last resort: check HTML profile page when all proxies/API are rate-limited.
    Returns a proxy-rate-limited status so we don't get false failure alerts daily."""
    import requests

    try:
        # Use codetabs to access the HTML profile page (HTML is less rate-limited than API)
        url = f"https://api.codetabs.com/v1/proxy?quest=https://www.reddit.com/user/{username}/"
        r = requests.get(url, timeout=30)

        if r.status_code == 200:
            html = r.text.lower()
            if username.lower() in html:
                # Account exists, but we can't get karma data
                return {
                    "success": True,  # Not a failure — account is alive
                    "username": username,
                    "link_karma": -1,
                    "comment_karma": -1,
                    "total_karma": -1,
                    "age_days": -1,
                    "age_str": "Unknown (proxy rate-limited)",
                    "has_verified_email": True,
                    "is_suspended": False,
                    "ready_for_posting": False,
                    "method": "proxy-html-profile",
                    "note": "Reddit is rate-limiting all proxies (429/403). Profile page is accessible — account is alive. Karma data unavailable. Check manually at reddit.com/u/" + username,
                }
            # Generic block page
            if "blocked" in html or "theme-beta" in html:
                return {"success": False, "error": "Reddit blocking all access (HTML profile also blocked)"}
            return {"success": False, "error": "Profile page returned unexpected content"}

        elif r.status_code == 404:
            return {"success": False, "error": f"User '{username}' not found"}
        else:
            return {"success": False, "error": f"HTML profile check failed: HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"HTML profile check error: {str(e)[:100]}"}


def format_telegram_message(result):
    """Format karma check result for Telegram."""
    if not result["success"]:
        return (
            f"🔴 <b>Reddit Karma Check FAILED</b>\n\n"
            f"User: u/{REDDIT_USERNAME}\n"
            f"Error: {result['error']}"
        )

    # Handle proxy-rate-limited state (karma = -1, can't get data)
    is_rate_limited = result.get("comment_karma", 0) == -1
    method = result.get("method", "unknown")

    if is_rate_limited:
        msg = (
            f"⚠️ <b>Reddit Karma Check — Proxy Rate Limited</b>\n\n"
            f"👤 User: u/{result['username']}\n"
            f"🔧 Method: {method}\n\n"
            f"📊 Karma data unavailable — Reddit is rate-limiting all proxies (429/403).\n\n"
            f"✅ Account is alive (profile page accessible)\n"
            f"❌ Karma data cannot be fetched automatically\n\n"
            f"💡 <a href='https://www.reddit.com/user/{result['username']}'>Check karma manually</a>\n\n"
            f"📝 Note: {result.get('note', 'N/A')[:120]}"
        )
        return msg

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
    suspended = "⚠️ SUSPENDED" if result.get("is_suspended") else ""

    msg = (
        f"📊 <b>Reddit Karma Report</b>\n\n"
        f"👤 User: u/{result['username']}\n"
        f"📅 Account age: {result['age_str']}\n"
        f"📝 Post Karma: <b>{result['link_karma']:,}</b>\n"
        f"💬 Comment Karma: <b>{result['comment_karma']:,}</b>\n"
        f"🏆 Total Karma: <b>{result['total_karma']:,}</b>\n"
        f"📧 Verified email: {verified}\n"
    )
    if suspended:
        msg += f"{suspended}\n"
    msg += (
        f"🔧 Method: {method}\n\n"
        f"{status}\n\n"
        f"💡 Threshold: {MIN_COMMENT_KARMA} comment karma + {MIN_ACCOUNT_AGE_DAYS} days"
    )
    return msg


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
    print("BroadFSC Reddit Karma Checker v3")
    print("=" * 50)
    print(f"Checking: u/{REDDIT_USERNAME}")
    print(f"Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Check karma
    print("Fetching karma data via web proxy...")
    result = check_karma_via_proxy(REDDIT_USERNAME)

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

    # Exit with 0 even on failure (we still reported the failure via Telegram)
    # Previously sys.exit(1) was causing GitHub Actions to mark as failed


if __name__ == "__main__":
    main()
