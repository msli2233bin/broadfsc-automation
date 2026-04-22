"""
BroadFSC Reddit Karma Checker
Checks Reddit account karma via public API (runs on GitHub Actions to avoid IP ban)
Sends results to Telegram for monitoring.

Requirements:
    REDDIT_USERNAME      - Reddit username to check (default: StretchRare207)
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
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Karma thresholds for auto-posting readiness
MIN_COMMENT_KARMA = 50
MIN_ACCOUNT_AGE_DAYS = 14


def check_karma(username):
    """Check Reddit user's karma via public API."""
    headers = {"User-Agent": "BroadFSC-Karma-Check/1.0"}
    
    try:
        r = requests.get(
            f"https://www.reddit.com/user/{username}/about.json",
            headers=headers,
            timeout=15
        )
        
        if r.status_code == 200:
            data = r.json().get("data", {})
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
        elif r.status_code == 404:
            return {"success": False, "error": f"User '{username}' not found (404)"}
        elif r.status_code == 403:
            return {"success": False, "error": f"Blocked by Reddit (403) - IP banned"}
        else:
            return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_telegram_message(result):
    """Format karma check result for Telegram notification."""
    if not result["success"]:
        return f"🔴 <b>Reddit Karma Check FAILED</b>\n\nUser: {REDDIT_USERNAME}\nError: {result['error']}"
    
    # Status emoji
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
    
    msg = (
        f"📊 <b>Reddit Karma Report</b>\n\n"
        f"👤 User: u/{result['username']}\n"
        f"📅 Account age: {result['age_str']}\n"
        f"📝 Post Karma: <b>{result['link_karma']:,}</b>\n"
        f"💬 Comment Karma: <b>{result['comment_karma']:,}</b>\n"
        f"🏆 Total Karma: <b>{result['total_karma']:,}</b>\n"
        f"📧 Verified email: {verified_email}\n\n"
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
    else:
        print(f"  FAILED: {result['error']}")
    
    # Step 2: Save to JSON for tracking history
    result["checked_at"] = datetime.datetime.utcnow().isoformat()
    history_file = "knowledge/reddit_karma_history.json"
    
    try:
        # Load existing history
        history = []
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        
        # Append new entry
        history.append(result)
        
        # Keep only last 90 entries (3 months of daily checks)
        if len(history) > 90:
            history = history[-90:]
        
        # Save
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
