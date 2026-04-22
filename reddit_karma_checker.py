"""
BroadFSC Reddit Karma Checker
Checks Reddit account karma and sends report to Telegram.

Two methods:
  1. OAuth (preferred) - Login with username/password + app credentials → query own profile
  2. Public API (fallback) - No login needed, but IP may be blocked

OAuth Setup:
  1. Go to https://www.reddit.com/prefs/apps
  2. Click "create another app..."
  3. Choose "script" type
  4. Name: BroadFSC-Karma-Check
  5. Redirect URI: http://localhost:8080
  6. Copy client_id (under app name) and client_secret

Requirements:
    REDDIT_CLIENT_ID     - Reddit app client_id (for OAuth)
    REDDIT_CLIENT_SECRET - Reddit app client_secret (for OAuth)
    REDDIT_USERNAME      - Reddit username (default: Only-Character4025)
    REDDIT_PASSWORD      - Reddit password (for OAuth)
    TELEGRAM_BOT_TOKEN   - For notifications
    TELEGRAM_CHANNEL_ID  - For notifications
"""

import os
import sys
import json
import datetime
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "Only-Character4025")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Karma thresholds for auto-posting readiness
MIN_COMMENT_KARMA = 50
MIN_ACCOUNT_AGE_DAYS = 14


def get_oauth_token():
    """Get Reddit OAuth token using script-type app credentials."""
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        missing = []
        if not REDDIT_CLIENT_ID:
            missing.append("REDDIT_CLIENT_ID")
        if not REDDIT_CLIENT_SECRET:
            missing.append("REDDIT_CLIENT_SECRET")
        if not REDDIT_USERNAME:
            missing.append("REDDIT_USERNAME")
        if not REDDIT_PASSWORD:
            missing.append("REDDIT_PASSWORD")
        print(f"  OAuth skipped: missing {', '.join(missing)}")
        return None

    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {
        "grant_type": "password",
        "username": REDDIT_USERNAME,
        "password": REDDIT_PASSWORD
    }
    headers = {"User-Agent": "BroadFSC-Karma-Check/1.0"}

    try:
        r = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth, data=data, headers=headers, timeout=15
        )
        if r.status_code == 200:
            token = r.json().get("access_token")
            if token:
                print("  OAuth auth success ✅")
                return token
            else:
                print("  OAuth auth FAIL: no access_token in response")
                return None
        else:
            print(f"  OAuth auth FAIL: HTTP {r.status_code} - {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  OAuth auth FAIL: {e}")
        return None


def check_karma_oauth(token, username):
    """Check Reddit karma using OAuth token (authenticates with Reddit, avoids IP ban)."""
    headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": "BroadFSC-Karma-Check/1.0",
    }

    try:
        r = requests.get(
            f"https://oauth.reddit.com/user/{username}/about",
            headers=headers, timeout=15
        )

        if r.status_code == 200:
            data = r.json().get("data", {})
            return parse_user_data(data)
        elif r.status_code == 403:
            return {"success": False, "error": "OAuth token rejected (403)"}
        elif r.status_code == 404:
            return {"success": False, "error": f"User '{username}' not found (404)"}
        else:
            return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def check_karma_public(username):
    """Check Reddit karma via public API (fallback, may be IP blocked)."""
    headers = {"User-Agent": "BroadFSC-Karma-Check/1.0"}

    try:
        r = requests.get(
            f"https://www.reddit.com/user/{username}/about.json",
            headers=headers, timeout=15
        )

        if r.status_code == 200:
            data = r.json().get("data", {})
            return parse_user_data(data)
        elif r.status_code == 404:
            return {"success": False, "error": f"User '{username}' not found (404)"}
        elif r.status_code == 403:
            return {"success": False, "error": "Blocked by Reddit (403) - need OAuth credentials"}
        else:
            return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_user_data(data):
    """Parse Reddit user data into standardized result dict."""
    username = data.get("name", "unknown")
    link_karma = data.get("link_karma", 0)
    comment_karma = data.get("comment_karma", 0)
    total_karma = link_karma + comment_karma
    created_utc = data.get("created_utc", 0)
    is_verified = data.get("verified", False)
    has_verified_email = data.get("has_verified_email", False)

    # Calculate account age
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
        "total_karma": total_karma,
        "age_days": age_days,
        "age_str": age_str,
        "is_verified": is_verified,
        "has_verified_email": has_verified_email,
        "ready_for_posting": comment_karma >= MIN_COMMENT_KARMA and age_days >= MIN_ACCOUNT_AGE_DAYS,
    }


def check_karma(username):
    """Check Reddit karma — try OAuth first, then public API as fallback."""
    # Method 1: OAuth (works even from blocked IPs)
    token = get_oauth_token()
    if token:
        print("  Using OAuth method...")
        result = check_karma_oauth(token, username)
        if result["success"]:
            result["method"] = "oauth"
            return result
        print(f"  OAuth method failed: {result['error']}")

    # Method 2: Public API (fallback)
    print("  Using public API method (fallback)...")
    result = check_karma_public(username)
    if result["success"]:
        result["method"] = "public"
    return result


def format_telegram_message(result):
    """Format karma check result for Telegram notification."""
    if not result["success"]:
        return (
            f"🔴 <b>Reddit Karma Check FAILED</b>\n\n"
            f"User: u/{REDDIT_USERNAME}\n"
            f"Error: {result['error']}\n\n"
            f"💡 Need Reddit OAuth credentials to bypass IP ban.\n"
            f"Create a script app at: reddit.com/prefs/apps"
        )

    # Status
    if result["ready_for_posting"]:
        status = "✅ READY FOR AUTO-POSTING"
    else:
        missing = []
        if result["comment_karma"] < MIN_COMMENT_KARMA:
            missing.append(f"Need {MIN_COMMENT_KARMA - result['comment_karma']} more comment karma")
        if result["age_days"] < MIN_ACCOUNT_AGE_DAYS:
            missing.append(f"Need {MIN_ACCOUNT_AGE_DAYS - result['age_days']} more days")
        status = f"⏳ NOT READY — {', '.join(missing)}"

    verified_email = "✅" if result["has_verified_email"] else "❌"
    method = result.get("method", "unknown")

    msg = (
        f"📊 <b>Reddit Karma Report</b>\n\n"
        f"👤 User: u/{result['username']}\n"
        f"📅 Account age: {result['age_str']}\n"
        f"📝 Post Karma: <b>{result['link_karma']:,}</b>\n"
        f"💬 Comment Karma: <b>{result['comment_karma']:,}</b>\n"
        f"🏆 Total Karma: <b>{result['total_karma']:,}</b>\n"
        f"📧 Verified email: {verified_email}\n"
        f"🔧 Method: {method}\n\n"
        f"{status}\n\n"
        f"💡 Threshold: {MIN_COMMENT_KARMA} comment karma + {MIN_ACCOUNT_AGE_DAYS} days"
    )
    return msg


def send_telegram(message):
    """Send notification to Telegram channel."""
    if not BOT_TOKEN or not CHANNEL_ID:
        print("  Telegram not configured, skipping notification")
        return

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

    # Step 1: Check karma
    print("Fetching karma data...")
    result = check_karma(REDDIT_USERNAME)

    if result["success"]:
        print(f"  Post Karma: {result['link_karma']:,}")
        print(f"  Comment Karma: {result['comment_karma']:,}")
        print(f"  Total Karma: {result['total_karma']:,}")
        print(f"  Account age: {result['age_str']}")
        print(f"  Verified email: {result['has_verified_email']}")
        print(f"  Ready for posting: {result['ready_for_posting']}")
        print(f"  Method: {result.get('method', 'unknown')}")
    else:
        print(f"  FAILED: {result['error']}")

    # Step 2: Save to JSON for tracking history
    result["checked_at"] = datetime.datetime.utcnow().isoformat()
    history_file = "knowledge/reddit_karma_history.json"

    try:
        history = []
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

        history.append(result)

        # Keep only last 90 entries
        if len(history) > 90:
            history = history[-90:]

        os.makedirs("knowledge", exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        print(f"  History saved ({len(history)} entries)")
    except Exception as e:
        print(f"  History save failed: {e}")

    # Step 3: Send Telegram notification
    print()
    print("Sending Telegram notification...")
    msg = format_telegram_message(result)
    send_telegram(msg)

    print()
    print("=" * 50)

    # Exit with error code if check failed (for workflow monitoring)
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
