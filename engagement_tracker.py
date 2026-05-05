"""
BroadFSC Engagement Tracker for Telegram Channel Posts
Tracks reactions, forwards, and replies on signal-type posts (RSI oversold, breakout, etc.)
and identifies high-engagement users for proactive sales follow-up.

Architecture:
- Polls Telegram Bot API getUpdates for message_reaction updates
- Stores engagement data in .bot_memory/signal_engagers.json
- Provides sorted list of engagers for Bot to follow up within 24h

Usage:
  python engagement_tracker.py                  # Single scan
  python engagement_tracker.py --continuous     # Run as daemon (poll every 30min)
"""

import os
import sys
import json
import time
import datetime
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_IDS = []  # Populated from env or config

# Try to load channel IDs from daily_promotion config
_env_channels = [
    os.environ.get("TELEGRAM_CHANNEL_ID", ""),
    os.environ.get("TELEGRAM_CHANNEL_ES", ""),
    os.environ.get("TELEGRAM_CHANNEL_AR", ""),
    os.environ.get("TELEGRAM_CHANNEL_JP", ""),
    os.environ.get("TELEGRAM_CHANNEL_ZH_TW", ""),
]
CHANNEL_IDS = [ch for ch in _env_channels if ch]

MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bot_memory")
ENGAGER_FILE = os.path.join(MEMORY_DIR, "signal_engagers.json")
SIGNAL_POSTS_FILE = os.path.join(MEMORY_DIR, "signal_posts.json")
OFFSET_FILE = os.path.join(MEMORY_DIR, "engagement_offset.txt")

# Follow-up window: 24 hours after engagement
FOLLOWUP_WINDOW_HOURS = 24

# Polling interval for continuous mode (seconds)
POLL_INTERVAL = 1800  # 30 min


def _ensure_dirs():
    """Ensure .bot_memory directory exists."""
    os.makedirs(MEMORY_DIR, exist_ok=True)


def _load_json(filepath, default=None):
    """Load JSON file with fallback."""
    if default is None:
        default = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default


def _save_json(filepath, data):
    """Save JSON file atomically."""
    _ensure_dirs()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_offset():
    """Load last processed update offset."""
    if os.path.exists(OFFSET_FILE):
        try:
            with open(OFFSET_FILE, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            pass
    return 0


def _set_offset(offset):
    """Save last processed update offset."""
    _ensure_dirs()
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))


def register_signal_post(channel_id, message_id, signal_type, ticker, content_preview=""):
    """Register a signal-type post for engagement tracking.

    Call this after sending a signal post (RSI oversold, breakout, etc.)

    Args:
        channel_id: Telegram channel/chat ID
        message_id: Message ID returned by sendMessage
        signal_type: 'rsi_oversold', 'breakout', 'volume_spike', 'earnings_alert', etc.
        ticker: Stock ticker (e.g. 'AAPL')
        content_preview: First 100 chars of post content
    """
    signal_posts = _load_json(SIGNAL_POSTS_FILE, {"posts": {}})
    post_key = str(channel_id) + "_" + str(message_id)
    signal_posts["posts"][post_key] = {
        "channel_id": channel_id,
        "message_id": message_id,
        "signal_type": signal_type,
        "ticker": ticker.upper(),
        "content_preview": content_preview[:100],
        "posted_at": datetime.datetime.utcnow().isoformat(),
        "reactions": {},
        "forwards": 0,
        "replies": 0,
    }
    _save_json(SIGNAL_POSTS_FILE, signal_posts)
    print("  Registered signal post: " + signal_type + " " + ticker + " (msg " + str(message_id) + ")")


def poll_reactions():
    """Poll Telegram API for message_reaction updates on signal posts.

    Uses getUpdates with allowed_updates=["message_reaction"] to detect
    emoji reactions on channel posts. Returns number of new engagements found.
    """
    if not BOT_TOKEN:
        print("  No BOT_TOKEN, skipping reaction poll")
        return 0

    signal_posts = _load_json(SIGNAL_POSTS_FILE, {"posts": {}})
    if not signal_posts["posts"]:
        print("  No signal posts registered, skipping")
        return 0

    # Build lookup: chat_id + message_id -> post_key
    post_lookup = {}
    for key, post in signal_posts["posts"].items():
        lookup_key = str(post["channel_id"]) + "_" + str(post["message_id"])
        post_lookup[lookup_key] = key

    offset = _get_offset()
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/getUpdates"
    params = {
        "offset": offset + 1,
        "limit": 100,
        "timeout": 10,
        "allowed_updates": json.dumps(["message_reaction", "message"])
    }

    try:
        r = requests.post(url, json=params, timeout=30)
        if r.status_code != 200:
            print("  getUpdates failed: HTTP " + str(r.status_code))
            return 0

        data = r.json()
        if not data.get("ok"):
            print("  getUpdates error: " + str(data.get("description", "unknown")))
            return 0

        updates = data.get("result", [])
        new_engagements = 0
        max_update_id = offset

        for update in updates:
            update_id = update.get("update_id", 0)
            if update_id > max_update_id:
                max_update_id = update_id

            # Process message_reaction updates
            reaction = update.get("message_reaction")
            if reaction:
                chat_id = str(reaction.get("chat", {}).get("id", ""))
                msg_id = str(reaction.get("message_id", ""))
                user = reaction.get("user", {})
                user_id = str(user.get("id", ""))
                user_name = user.get("first_name", "") + " " + user.get("last_name", "")
                user_name = user_name.strip()

                lookup_key = chat_id + "_" + msg_id
                post_key = post_lookup.get(lookup_key)

                if post_key and user_id:
                    # Get the new reaction emojis
                    new_reactions = reaction.get("new_reaction", [])
                    for react in new_reactions:
                        emoji = react.get("emoji", "")
                        if not emoji:
                            emoji = react.get("custom_emoji_id", "custom")

                        # Update signal_posts with reaction
                        if user_id not in signal_posts["posts"][post_key]["reactions"]:
                            signal_posts["posts"][post_key]["reactions"][user_id] = {
                                "name": user_name,
                                "emojis": [],
                                "first_reaction_at": datetime.datetime.utcnow().isoformat()
                            }
                        if emoji not in signal_posts["posts"][post_key]["reactions"][user_id]["emojis"]:
                            signal_posts["posts"][post_key]["reactions"][user_id]["emojis"].append(emoji)

                        # Register as signal engager
                        _register_engager(
                            user_id=user_id,
                            user_name=user_name,
                            post_key=post_key,
                            signal_type=signal_posts["posts"][post_key]["signal_type"],
                            ticker=signal_posts["posts"][post_key]["ticker"],
                            reaction_emoji=emoji
                        )
                        new_engagements += 1
                        print("  New engagement: " + user_name + " (" + user_id + ") reacted " + emoji + " on " + signal_posts["posts"][post_key]["ticker"])

            # Also track replies to signal posts (from forwarded messages in groups)
            message = update.get("message")
            if message:
                reply_to = message.get("reply_to_message")
                if reply_to:
                    reply_chat_id = str(reply_to.get("chat", {}).get("id", ""))
                    reply_msg_id = str(reply_to.get("message_id", ""))
                    lookup_key = reply_chat_id + "_" + reply_msg_id
                    post_key = post_lookup.get(lookup_key)
                    if post_key:
                        from_user = message.get("from", {})
                        user_id = str(from_user.get("id", ""))
                        user_name = from_user.get("first_name", "") + " " + from_user.get("last_name", "")
                        user_name = user_name.strip()
                        if user_id:
                            signal_posts["posts"][post_key]["replies"] += 1
                            _register_engager(
                                user_id=user_id,
                                user_name=user_name,
                                post_key=post_key,
                                signal_type=signal_posts["posts"][post_key]["signal_type"],
                                ticker=signal_posts["posts"][post_key]["ticker"],
                                reaction_emoji="reply"
                            )
                            new_engagements += 1

        _set_offset(max_update_id)
        _save_json(SIGNAL_POSTS_FILE, signal_posts)
        return new_engagements

    except Exception as e:
        print("  poll_reactions error: " + str(e))
        return 0


def _register_engager(user_id, user_name, post_key, signal_type, ticker, reaction_emoji):
    """Register a user as a signal engager for follow-up.

    Stores in signal_engagers.json with priority scoring:
    - Base: 50 points
    - RSI oversold / breakout: +20 (high intent signal)
    - Multiple reactions on same post: +10
    - Previously engaged before: +15 (returning interest)
    """
    engagers = _load_json(ENGAGER_FILE, {"engagers": {}})

    now = datetime.datetime.utcnow().isoformat()

    if user_id not in engagers["engagers"]:
        engagers["engagers"][user_id] = {
            "name": user_name,
            "engagements": [],
            "total_score": 0,
            "followed_up": False,
            "followed_up_at": None,
            "first_seen": now,
            "last_engagement": now,
            "tags": [],
        }

    engager = engagers["engagers"][user_id]
    engager["name"] = user_name
    engager["last_engagement"] = now

    # Check if already engaged with this post
    already_engaged = any(e.get("post_key") == post_key for e in engager["engagements"])

    # Calculate score for this engagement
    score = 50  # base
    high_intent_signals = ["rsi_oversold", "breakout", "volume_spike", "death_cross", "golden_cross"]
    if signal_type in high_intent_signals:
        score += 20
    if already_engaged:
        score += 10  # multiple interactions = higher intent
    if len(engager["engagements"]) > 0:
        score += 15  # returning user

    # Add engagement record
    engager["engagements"].append({
        "post_key": post_key,
        "signal_type": signal_type,
        "ticker": ticker,
        "reaction": reaction_emoji,
        "engaged_at": now,
        "score": score
    })

    engager["total_score"] = sum(e["score"] for e in engager["engagements"])

    # Add tags
    if "signal_interested" not in engager["tags"]:
        engager["tags"].append("signal_interested")
    if signal_type in high_intent_signals and "high_intent" not in engager["tags"]:
        engager["tags"].append("high_intent")

    _save_json(ENGAGER_FILE, engagers)


def get_pending_followups():
    """Get sorted list of engagers who haven't been followed up yet.

    Returns list of dicts sorted by total_score (highest first):
    [{"user_id": ..., "name": ..., "score": ..., "tickers": [...], "hours_since": ...}]
    """
    engagers = _load_json(ENGAGER_FILE, {"engagers": {}})
    now = datetime.datetime.utcnow()
    pending = []

    for user_id, engager in engagers["engagers"].items():
        if engager.get("followed_up"):
            continue

        # Calculate hours since last engagement
        last = engager.get("last_engagement", now.isoformat())
        try:
            last_dt = datetime.datetime.fromisoformat(last)
            hours_since = (now - last_dt).total_seconds() / 3600
        except (ValueError, TypeError):
            hours_since = 999

        # Only follow up within the window
        if hours_since > FOLLOWUP_WINDOW_HOURS * 3:
            continue  # Too old, skip

        # Collect unique tickers they engaged with
        tickers = list(set(e.get("ticker", "") for e in engager.get("engagements", []) if e.get("ticker")))

        # Get primary signal type
        signal_types = list(set(e.get("signal_type", "") for e in engager.get("engagements", [])))

        pending.append({
            "user_id": user_id,
            "name": engager.get("name", "Unknown"),
            "score": engager.get("total_score", 0),
            "tickers": tickers,
            "signal_types": signal_types,
            "hours_since_engagement": round(hours_since, 1),
            "tags": engager.get("tags", []),
            "engagement_count": len(engager.get("engagements", [])),
        })

    # Sort by score descending
    pending.sort(key=lambda x: x["score"], reverse=True)
    return pending


def mark_followed_up(user_id):
    """Mark a user as followed up after Bot sends them a message."""
    engagers = _load_json(ENGAGER_FILE, {"engagers": {}})
    if user_id in engagers["engagers"]:
        engagers["engagers"][user_id]["followed_up"] = True
        engagers["engagers"][user_id]["followed_up_at"] = datetime.datetime.utcnow().isoformat()
        _save_json(ENGAGER_FILE, engagers)
        return True
    return False


def cleanup_old_posts(max_age_days=7):
    """Remove signal posts older than max_age_days to keep data manageable."""
    signal_posts = _load_json(SIGNAL_POSTS_FILE, {"posts": {}})
    now = datetime.datetime.utcnow()
    to_remove = []

    for key, post in signal_posts["posts"].items():
        try:
            posted = datetime.datetime.fromisoformat(post.get("posted_at", "2000-01-01"))
            if (now - posted).days > max_age_days:
                to_remove.append(key)
        except (ValueError, TypeError):
            to_remove.append(key)

    for key in to_remove:
        del signal_posts["posts"][key]

    if to_remove:
        _save_json(SIGNAL_POSTS_FILE, signal_posts)
        print("  Cleaned up " + str(len(to_remove)) + " old signal posts")


def run_scan():
    """Single scan: poll reactions and report pending follow-ups."""
    print("=== BroadFSC Engagement Tracker ===")
    print("Time: " + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    print("Channels: " + str(len(CHANNEL_IDS)))
    print()

    new = poll_reactions()
    print("New engagements found: " + str(new))

    cleanup_old_posts()

    pending = get_pending_followups()
    print("Pending follow-ups: " + str(len(pending)))

    for p in pending[:10]:  # Show top 10
        print("  " + p["name"] + " (score:" + str(p["score"]) + ", tickers:" + ",".join(p["tickers"]) + ", " + str(p["hours_since_engagement"]) + "h ago)")

    return pending


def run_continuous():
    """Run as daemon, polling every POLL_INTERVAL seconds."""
    print("Starting engagement tracker in continuous mode (poll every " + str(POLL_INTERVAL // 60) + " min)")
    while True:
        try:
            run_scan()
        except Exception as e:
            print("Error in scan cycle: " + str(e))
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if "--continuous" in sys.argv:
        run_continuous()
    else:
        run_scan()
