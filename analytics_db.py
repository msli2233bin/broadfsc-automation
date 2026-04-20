"""
BroadFSC Analytics Database Module
SQLite-based tracking for all promotion metrics.
Tables: posts, clicks, conversations, website_visits, daily_summary
"""

import os
import sys
import sqlite3
import datetime
import json
import threading

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Thread-local storage for DB connections
_local = threading.local()

# DB path — same directory as scripts
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "analytics.db")


def get_db():
    """Get thread-local DB connection."""
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, timeout=10)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def close_db():
    """Close thread-local DB connection."""
    if hasattr(_local, 'conn') and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


def init_db():
    """Initialize all tables."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            platform TEXT NOT NULL,
            post_type TEXT DEFAULT 'post',
            channel TEXT DEFAULT '',
            content_preview TEXT DEFAULT '',
            post_id TEXT DEFAULT '',
            status TEXT DEFAULT 'success',
            error_msg TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            source_platform TEXT NOT NULL,
            source_post_id TEXT DEFAULT '',
            link_type TEXT DEFAULT 'website',
            target_url TEXT DEFAULT '',
            ip_hash TEXT DEFAULT '',
            country TEXT DEFAULT '',
            referrer TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            platform TEXT NOT NULL DEFAULT 'telegram',
            user_id TEXT DEFAULT '',
            user_name TEXT DEFAULT '',
            direction TEXT DEFAULT 'inbound',
            message_type TEXT DEFAULT 'text',
            is_ai_response INTEGER DEFAULT 1,
            chat_mode TEXT DEFAULT 'auto'
        );

        CREATE TABLE IF NOT EXISTS website_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            source TEXT DEFAULT 'direct',
            campaign TEXT DEFAULT '',
            ip_hash TEXT DEFAULT '',
            country TEXT DEFAULT '',
            user_agent TEXT DEFAULT '',
            referrer TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            interests TEXT DEFAULT '',
            source TEXT DEFAULT '',
            ip_hash TEXT DEFAULT '',
            country TEXT DEFAULT '',
            user_agent TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,
            telegram_posts INTEGER DEFAULT 0,
            twitter_posts INTEGER DEFAULT 0,
            tiktok_posts INTEGER DEFAULT 0,
            mastodon_posts INTEGER DEFAULT 0,
            discord_posts INTEGER DEFAULT 0,
            reddit_posts INTEGER DEFAULT 0,
            total_posts INTEGER DEFAULT 0,
            total_clicks INTEGER DEFAULT 0,
            total_conversations INTEGER DEFAULT 0,
            ai_responses INTEGER DEFAULT 0,
            live_chats INTEGER DEFAULT 0,
            website_visits INTEGER DEFAULT 0,
            whatsapp_clicks INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
        CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp);
        CREATE INDEX IF NOT EXISTS idx_clicks_timestamp ON clicks(timestamp);
        CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
        CREATE INDEX IF NOT EXISTS idx_visits_timestamp ON website_visits(timestamp);
        CREATE INDEX IF NOT EXISTS idx_registrations_timestamp ON registrations(timestamp);
        CREATE INDEX IF NOT EXISTS idx_registrations_email ON registrations(email);
    """)
    db.commit()


# ============================================================
# Logging functions (call from other scripts)
# ============================================================

def log_post(platform, post_type="post", channel="", content_preview="", post_id="", status="success", error_msg=""):
    """Log a post event."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO posts (platform, post_type, channel, content_preview, post_id, status, error_msg) VALUES (?,?,?,?,?,?,?)",
            (platform, post_type, channel, content_preview[:200], post_id, status, error_msg[:200])
        )
        db.commit()
    except Exception as e:
        print(f"[analytics] log_post error: {e}")


def log_click(source_platform, source_post_id="", link_type="website", target_url="", ip_hash="", country="", referrer=""):
    """Log a click event."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO clicks (source_platform, source_post_id, link_type, target_url, ip_hash, country, referrer) VALUES (?,?,?,?,?,?,?)",
            (source_platform, source_post_id, link_type, target_url, ip_hash, country, referrer)
        )
        db.commit()
    except Exception as e:
        print(f"[analytics] log_click error: {e}")


def log_conversation(platform="telegram", user_id="", user_name="", direction="inbound", message_type="text", is_ai_response=True, chat_mode="auto"):
    """Log a conversation event."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO conversations (platform, user_id, user_name, direction, message_type, is_ai_response, chat_mode) VALUES (?,?,?,?,?,?,?)",
            (platform, user_id, user_name, direction, message_type, 1 if is_ai_response else 0, chat_mode)
        )
        db.commit()
    except Exception as e:
        print(f"[analytics] log_conversation error: {e}")


def log_website_visit(source="direct", campaign="", ip_hash="", country="", user_agent="", referrer=""):
    """Log a website visit event."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO website_visits (source, campaign, ip_hash, country, user_agent, referrer) VALUES (?,?,?,?,?,?)",
            (source, campaign, ip_hash, country, user_agent[:200], referrer[:200])
        )
        db.commit()
    except Exception as e:
        print(f"[analytics] log_visit error: {e}")


def log_registration(name, email, interests="", source="", ip_hash="", country="", user_agent=""):
    """Log a new registration."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO registrations (name, email, interests, source, ip_hash, country, user_agent) VALUES (?,?,?,?,?,?,?)",
            (name, email, interests, source, ip_hash, country, user_agent[:200])
        )
        db.commit()
    except Exception as e:
        print(f"[analytics] log_registration error: {e}")


# ============================================================
# Query functions (for dashboard API)
# ============================================================

def get_overview(days=30):
    """Get overview stats for the last N days."""
    db = get_db()
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()

    stats = {}

    # Total posts by platform
    rows = db.execute(
        "SELECT platform, COUNT(*) as cnt FROM posts WHERE timestamp >= ? GROUP BY platform",
        (since,)
    ).fetchall()
    stats['posts_by_platform'] = {r['platform']: r['cnt'] for r in rows}
    stats['total_posts'] = sum(stats['posts_by_platform'].values())

    # Total clicks
    row = db.execute("SELECT COUNT(*) as cnt FROM clicks WHERE timestamp >= ?", (since,)).fetchone()
    stats['total_clicks'] = row['cnt']

    # Clicks by platform
    rows = db.execute(
        "SELECT source_platform, COUNT(*) as cnt FROM clicks WHERE timestamp >= ? GROUP BY source_platform",
        (since,)
    ).fetchall()
    stats['clicks_by_platform'] = {r['source_platform']: r['cnt'] for r in rows}

    # Conversations
    row = db.execute("SELECT COUNT(*) as cnt FROM conversations WHERE timestamp >= ?", (since,)).fetchone()
    stats['total_conversations'] = row['cnt']

    rows = db.execute(
        "SELECT is_ai_response, COUNT(*) as cnt FROM conversations WHERE timestamp >= ? GROUP BY is_ai_response",
        (since,)
    ).fetchall()
    for r in rows:
        if r['is_ai_response']:
            stats['ai_responses'] = r['cnt']
        else:
            stats['live_chats'] = r['cnt']
    stats.setdefault('ai_responses', 0)
    stats.setdefault('live_chats', 0)

    # Website visits
    row = db.execute("SELECT COUNT(*) as cnt FROM website_visits WHERE timestamp >= ?", (since,)).fetchone()
    stats['website_visits'] = row['cnt']

    # WhatsApp clicks
    row = db.execute(
        "SELECT COUNT(*) as cnt FROM clicks WHERE link_type='whatsapp' AND timestamp >= ?",
        (since,)
    ).fetchone()
    stats['whatsapp_clicks'] = row['cnt']

    # Post success rate
    row = db.execute(
        "SELECT COUNT(*) as total, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success FROM posts WHERE timestamp >= ?",
        (since,)
    ).fetchone()
    total = row['total'] or 0
    success = row['success'] or 0
    stats['post_success_rate'] = round(success / max(total, 1) * 100, 1)

    return stats


def get_daily_trend(days=30):
    """Get daily trend data for charts."""
    db = get_db()
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')

    # Posts per day per platform
    rows = db.execute("""
        SELECT DATE(timestamp) as day, platform, COUNT(*) as cnt
        FROM posts WHERE DATE(timestamp) >= ?
        GROUP BY day, platform ORDER BY day
    """, (since,)).fetchall()

    trend = {}
    for r in rows:
        day = r['day']
        if day not in trend:
            trend[day] = {}
        trend[day][r['platform']] = r['cnt']

    # Clicks per day
    rows = db.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM clicks WHERE DATE(timestamp) >= ?
        GROUP BY day ORDER BY day
    """, (since,)).fetchall()
    clicks_by_day = {r['day']: r['cnt'] for r in rows}

    # Conversations per day
    rows = db.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM conversations WHERE DATE(timestamp) >= ?
        GROUP BY day ORDER BY day
    """, (since,)).fetchall()
    convs_by_day = {r['day']: r['cnt'] for r in rows}

    # Website visits per day
    rows = db.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM website_visits WHERE DATE(timestamp) >= ?
        GROUP BY day ORDER BY day
    """, (since,)).fetchall()
    visits_by_day = {r['day']: r['cnt'] for r in rows}

    return {
        'posts': trend,
        'clicks': clicks_by_day,
        'conversations': convs_by_day,
        'visits': visits_by_day
    }


def get_recent_posts(limit=20):
    """Get recent post log."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM posts ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_recent_conversations(limit=20):
    """Get recent conversation log."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_hourly_distribution(days=7):
    """Get posting/click distribution by hour of day."""
    db = get_db()
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()

    rows = db.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
        FROM posts WHERE timestamp >= ?
        GROUP BY hour ORDER BY hour
    """, (since,)).fetchall()
    posts_by_hour = {r['hour']: r['cnt'] for r in rows}

    rows = db.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
        FROM clicks WHERE timestamp >= ?
        GROUP BY hour ORDER BY hour
    """, (since,)).fetchall()
    clicks_by_hour = {r['hour']: r['cnt'] for r in rows}

    return {'posts': posts_by_hour, 'clicks': clicks_by_hour}


def get_registrations(days=30):
    """Get registration list."""
    db = get_db()
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()
    rows = db.execute(
        "SELECT * FROM registrations WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT 200",
        (since,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_registration_stats(days=30):
    """Get registration statistics."""
    db = get_db()
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()

    total = db.execute("SELECT COUNT(*) as cnt FROM registrations WHERE timestamp >= ?", (since,)).fetchone()
    by_source = db.execute(
        "SELECT source, COUNT(*) as cnt FROM registrations WHERE timestamp >= ? GROUP BY source",
        (since,)
    ).fetchall()
    by_interest = db.execute(
        "SELECT interests, COUNT(*) as cnt FROM registrations WHERE timestamp >= ? GROUP BY interests",
        (since,)
    ).fetchall()
    by_day = db.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as cnt
        FROM registrations WHERE timestamp >= ?
        GROUP BY day ORDER BY day
    """, (since,)).fetchall()

    return {
        'total': total['cnt'],
        'by_source': {r['source']: r['cnt'] for r in by_source},
        'by_interest': {r['interests']: r['cnt'] for r in by_interest},
        'by_day': {r['day']: r['cnt'] for r in by_day}
    }


# ============================================================
# Auto-backfill from existing logs (run once)
# ============================================================

def backfill_from_daily_promotion():
    """Scan daily_promotion.py log output to backfill historical data."""
    # This is a placeholder — actual backfill would parse log files
    # For now, we'll rely on new data going forward
    pass


# ============================================================
# Main — initialize DB
# ============================================================

if __name__ == "__main__":
    init_db()
    print(f"✅ Analytics DB initialized at: {DB_PATH}")

    # Quick stats
    stats = get_overview(days=30)
    print(f"📊 Last 30 days: {stats['total_posts']} posts, {stats['total_clicks']} clicks, {stats['total_conversations']} conversations")
