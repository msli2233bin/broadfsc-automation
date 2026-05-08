"""
BroadFSC Customer Nurture Pipeline
Detects interactions across platforms → logs contacts → automates nurturing.

Funnel: Awareness → Interest → Consideration → Conversation → Lead → Customer

Detection sources:
- Threads: Graph API post engagement, follower notifications
- Bluesky: AT Protocol notifications
- Telegram: Bot conversations, channel reactions
- Mastodon: Notifications API
- Discord: Message reactions, DMs

Actions per stage:
- awareness → interest: auto-like their comment, polite reply
- interest → consideration: send DM with free research report offer
- consideration → conversation: warm handoff to TG Bot for live chat
- conversation → lead: scheduled follow-up after 48h
- lead → customer: offer paid service consultation
"""
import os, sys, datetime, json, time, requests
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from analytics_db import (
        init_db, upsert_customer_contact, log_funnel_event,
        get_customers_by_stage, log_engagement
    )
    HAS_DB = True
except ImportError:
    HAS_DB = False

# Funnel stages
STAGES = ['awareness', 'interest', 'consideration', 'conversation', 'lead', 'customer']

# ============================================================
# Threads Interaction Detection
# ============================================================
def detect_threads_interactions(post_id=None):
    """Scan Threads for new interactions on our posts.

    Uses Meta Graph API to get replies/likes on our posts.
    Returns list of new interactions.
    """
    access_token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    if not access_token:
        print("[nurture] Threads: No THREADS_ACCESS_TOKEN")
        return []

    # Get our recent posts
    url = "https://graph.threads.net/v1.0/me/threads"
    params = {
        "fields": "id,text,timestamp,permalink",
        "limit": 10,
        "access_token": access_token,
    }

    interactions = []
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            posts = resp.json().get("data", [])
            for post in posts:
                pid = post.get("id", "")
                # Get replies (conversations)
                conv_url = f"https://graph.threads.net/v1.0/{pid}/conversations"
                conv_params = {
                    "fields": "id,from{username,id},text,timestamp",
                    "limit": 10,
                    "access_token": access_token,
                }
                try:
                    conv_resp = requests.get(conv_url, params=conv_params, timeout=15)
                    if conv_resp.status_code == 200:
                        for conv in conv_resp.json().get("data", []):
                            fr = conv.get("from", {})
                            interactions.append({
                                "platform": "threads",
                                "type": "reply",
                                "post_id": pid,
                                "user_id": fr.get("id", ""),
                                "user_name": fr.get("username", ""),
                                "text": conv.get("text", "")[:200],
                                "timestamp": conv.get("timestamp", ""),
                            })
                except Exception as e:
                    print(f"[nurture] Threads conv error: {e}")
    except Exception as e:
        print(f"[nurture] Threads scan error: {e}")

    return interactions


# ============================================================
# Bluesky Interaction Detection
# ============================================================
def detect_bluesky_interactions():
    """Scan Bluesky for new replies/likes on our posts.

    Uses AT Protocol notification API.
    """
    handle = os.environ.get("BLUESKY_HANDLE", "")
    password = os.environ.get("BLUESKY_APP_PASSWORD", "")
    if not handle or not password:
        return []

    interactions = []
    try:
        # Auth
        resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        session = resp.json()
        jwt = session["accessJwt"]

        # Get notifications
        resp = requests.get(
            "https://bsky.social/xrpc/app.bsky.notification.listNotifications",
            headers={"Authorization": f"Bearer {jwt}"},
            params={"limit": 25},
            timeout=15,
        )
        if resp.status_code == 200:
            for n in resp.json().get("notifications", []):
                author = n.get("author", {})
                interactions.append({
                    "platform": "bluesky",
                    "type": n.get("reason", "interaction"),
                    "post_id": n.get("reasonSubject", ""),
                    "user_id": author.get("did", ""),
                    "user_name": author.get("handle", ""),
                    "display_name": author.get("displayName", ""),
                    "text": n.get("record", {}).get("text", "")[:200],
                    "timestamp": n.get("indexedAt", ""),
                })
    except Exception as e:
        print(f"[nurture] Bluesky scan error: {e}")

    return interactions


# ============================================================
# Log & Classify Interactions
# ============================================================
def process_interactions(interactions):
    """Log new interactions to DB and classify into funnel.

    Returns summary dict.
    """
    if not HAS_DB:
        print("[nurture] DB not available, skipping")
        return {"new": 0, "upgraded": 0}

    seen_users = set()  # Track unique users per platform
    new_contacts = 0
    upgraded = 0

    for i in interactions:
        platform = i.get("platform", "unknown")
        username = i.get("user_name", "")

        # Skip if empty username
        if not username:
            continue

        # Deduplicate in this batch
        key = f"{platform}:{username}"
        if key in seen_users:
            continue
        seen_users.add(key)

        # Log engagement
        log_engagement(
            platform=platform,
            engagement_type=i.get("type", "reply"),
            target_post_id=i.get("post_id", ""),
            target_user_id=i.get("user_id", ""),
            target_user_name=username,
            content_preview=i.get("text", "")[:100],
        )

        # Determine funnel stage based on interaction type
        int_type = i.get("type", "")
        if int_type in ("follow", "like"):
            funnel_stage = "awareness"
        elif int_type in ("reply", "comment"):
            funnel_stage = "interest"
        elif int_type in ("mention", "share"):
            funnel_stage = "consideration"
        else:
            funnel_stage = "awareness"

        # Upsert contact
        upsert_customer_contact(
            platform=platform,
            username=username,
            display_name=i.get("display_name", ""),
            source=i.get("post_id", ""),
            funnel_stage=funnel_stage,
        )

        new_contacts += 1

    return {"new": new_contacts, "upgraded": upgraded}


# ============================================================
# Nurture Actions — Automated but human-feeling
# ============================================================
NURTURE_MESSAGES = {
    "interest": [
        "Thanks for engaging! What stocks are you watching this week?",
        "Good eye on that chart. I post daily TA breakdowns — what tickers interest you most?",
        "Appreciate the interaction. If you need specific stock analysis, let me know.",
    ],
    "consideration": [
        "I noticed you've been following the TA posts. Would you like a free research report on any ticker? Just name it.",
        "Since you're into technical analysis — I can send you a detailed breakdown of any stock. Free, no catch. What interests you?",
    ],
    "conversation": [
        "Let's take this to a more detailed chat — I'm active on Telegram @BroadInvestBot. Faster responses and free reports there.",
    ],
}


def get_nurture_message(stage):
    """Get a randomized but appropriate nurture message for the stage."""
    import random
    messages = NURTURE_MESSAGES.get(stage, [])
    if messages:
        return random.choice(messages)
    return None


# ============================================================
# Nurture Pipeline Runner
# ============================================================
def run_nurture_cycle():
    """Run one full nurture cycle: detect → log → act.

    Returns summary.
    """
    print("=" * 50)
    print(f"[nurture] Starting cycle at {datetime.datetime.utcnow().isoformat()}")

    # 1. Detect interactions on all platforms
    all_interactions = []

    print("[nurture] Scanning Threads...")
    threads_ints = detect_threads_interactions()
    all_interactions.extend(threads_ints)
    print(f"  Found {len(threads_ints)} Threads interactions")

    print("[nurture] Scanning Bluesky...")
    bluesky_ints = detect_bluesky_interactions()
    all_interactions.extend(bluesky_ints)
    print(f"  Found {len(bluesky_ints)} Bluesky interactions")

    # 2. Process & log to DB
    print("[nurture] Processing interactions...")
    result = process_interactions(all_interactions)
    print(f"  New contacts: {result['new']}, Upgraded: {result['upgraded']}")

    # 3. Show pipeline summary
    if HAS_DB:
        from analytics_db import get_customer_pipeline
        pipeline = get_customer_pipeline()
        print(f"[nurture] Current pipeline: {pipeline}")

        # Show contacts ready for nurturing
        for stage in ['interest', 'consideration', 'conversation']:
            contacts = get_customers_by_stage(stage, limit=5)
            if contacts:
                print(f"\n  [{stage.upper()}] {len(contacts)} contacts:")
                for c in contacts[:5]:
                    print(f"    @{c.get('username')} ({c.get('platform')}) — since {c.get('last_interaction', '?')[:10]}")

    print("=" * 50)
    return result


# ============================================================
# Auto-nurture: Scan + Suggest Actions
# ============================================================
def suggest_actions():
    """Scan pipeline and suggest nurture actions (doesn't auto-send)."""
    if not HAS_DB:
        return []

    suggestions = []
    for stage in ['interest', 'consideration']:
        contacts = get_customers_by_stage(stage, limit=20)
        for c in contacts:
            msg = get_nurture_message(stage)
            if msg:
                suggestions.append({
                    "platform": c.get("platform"),
                    "username": c.get("username"),
                    "stage": stage,
                    "suggested_message": msg,
                })
    return suggestions


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='BroadFSC Customer Nurture Pipeline')
    parser.add_argument('--scan', action='store_true', help='Scan for new interactions')
    parser.add_argument('--suggest', action='store_true', help='Suggest nurture actions')
    parser.add_argument('--summary', action='store_true', help='Show pipeline summary')
    args = parser.parse_args()

    if args.scan or (not args.suggest and not args.summary):
        run_nurture_cycle()

    if args.suggest:
        actions = suggest_actions()
        if actions:
            print(f"\n💡 Suggested nurture actions ({len(actions)}):")
            for a in actions:
                print(f"  [{a['stage']}] @{a['username']} on {a['platform']}:")
                print(f'    → "{a["suggested_message"]}"')
        else:
            print("\n✅ No nurture actions needed right now.")

    if args.summary:
        if HAS_DB:
            from analytics_db import get_customer_pipeline, get_customer_count
            pipeline = get_customer_pipeline()
            customers = get_customer_count()
            print(f"\n📊 Pipeline Summary:")
            print(f"   Total contacts: {sum(v.get('total',0) for v in customers.values())}")
            for stage in STAGES:
                count = pipeline.get(stage, 0)
                bar = '█' * min(count, 20)
                print(f"   {stage:15s}: {count:3d} {bar}")
