"""
BroadFSC Analytics Logger
统一数据采集模块 - 所有推广脚本共用

功能：
- 记录帖子发布（platform, type, content, status）
- 记录用户互动（bot对话、按钮点击）
- 记录引流点击（source, link_type, target_url）
- 记录客户注册（name, email, interests, source）
- 生成 dashboard 可视化看板
- JSON 文件存储 + SQLite 双写（GitHub Actions 自动更新）

数据文件：
- analytics/posts.json  — 帖子发布记录
- analytics/interactions.json — 用户互动记录
- analytics/summary.json — 每日汇总（dashboard 读取）
- analytics.db (SQLite) — 统一数据库（registrations, clicks 等）
"""

import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

ANALYTICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics")
POSTS_FILE = os.path.join(ANALYTICS_DIR, "posts.json")
INTERACTIONS_FILE = os.path.join(ANALYTICS_DIR, "interactions.json")
SUMMARY_FILE = os.path.join(ANALYTICS_DIR, "summary.json")

# Try importing SQLite analytics for unified tracking
try:
    from analytics_db import log_post as _db_log_post, log_click as _db_log_click, log_registration as _db_log_registration
    HAS_DB = True
except ImportError:
    HAS_DB = False


def _ensure_dir():
    os.makedirs(ANALYTICS_DIR, exist_ok=True)


def _load_json(filepath):
    _ensure_dir()
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_json(filepath, data):
    _ensure_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_post(platform, post_type="text", content_preview="", status="success", error_msg=""):
    """记录一次帖子发布（JSON + SQLite 双写）"""
    posts = _load_json(POSTS_FILE)
    entry = {
        "id": len(posts) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "platform": platform,
        "type": post_type,
        "content_preview": content_preview[:200],
        "status": status,
        "error_msg": error_msg
    }
    posts.append(entry)
    # Keep last 5000 records
    if len(posts) > 5000:
        posts = posts[-5000:]
    _save_json(POSTS_FILE, posts)
    # Dual-write to SQLite
    if HAS_DB:
        try:
            _db_log_post(platform=platform, post_type=post_type, content_preview=content_preview[:200], status=status, error_msg=error_msg[:200])
        except Exception as e:
            print(f"[analytics_logger] SQLite log_post error: {e}")
    return entry["id"]


def log_interaction(platform, action, user_id="", details=""):
    """记录一次用户互动"""
    interactions = _load_json(INTERACTIONS_FILE)
    entry = {
        "id": len(interactions) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "platform": platform,
        "action": action,
        "user_id": str(user_id),
        "details": details[:200]
    }
    interactions.append(entry)
    if len(interactions) > 5000:
        interactions = interactions[-5000:]
    _save_json(INTERACTIONS_FILE, interactions)
    return entry["id"]


def log_click(source_platform, link_type="website", target_url="", referrer=""):
    """记录一次引流链接点击（JSON + SQLite 双写）"""
    clicks_file = os.path.join(ANALYTICS_DIR, "clicks.json")
    clicks = _load_json(clicks_file)
    entry = {
        "id": len(clicks) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_platform": source_platform,
        "link_type": link_type,
        "target_url": target_url[:300],
        "referrer": referrer[:200]
    }
    clicks.append(entry)
    if len(clicks) > 5000:
        clicks = clicks[-5000:]
    _save_json(clicks_file, clicks)
    # Dual-write to SQLite
    if HAS_DB:
        try:
            _db_log_click(source_platform=source_platform, link_type=link_type, target_url=target_url[:300], referrer=referrer[:200])
        except Exception as e:
            print(f"[analytics_logger] SQLite log_click error: {e}")
    return entry["id"]


def log_registration(name, email, interests="", source=""):
    """记录一次客户注册（JSON + SQLite 双写）"""
    regs_file = os.path.join(ANALYTICS_DIR, "registrations.json")
    regs = _load_json(regs_file)
    entry = {
        "id": len(regs) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "name": name,
        "email": email,
        "interests": interests,
        "source": source
    }
    regs.append(entry)
    if len(regs) > 5000:
        regs = regs[-5000:]
    _save_json(regs_file, regs)
    # Dual-write to SQLite
    if HAS_DB:
        try:
            _db_log_registration(name=name, email=email, interests=interests, source=source)
        except Exception as e:
            print(f"[analytics_logger] SQLite log_registration error: {e}")
    return entry["id"]


def get_tracking_url(target_url, source_platform, link_type="website"):
    """生成带追踪参数的引流链接

    Args:
        target_url: 目标 URL（如 https://msli2233bin.github.io/broadfsc-automation/）
        source_platform: 来源平台（如 twitter, telegram, mastodon 等）
        link_type: 链接类型（website, telegram, contact）

    Returns:
        带 UTM 追踪参数的 URL
    """
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(target_url)
    params = parse_qs(parsed.query)

    # Add UTM parameters
    params["utm_source"] = [source_platform]
    params["utm_medium"] = ["social"]
    params["utm_campaign"] = [f"broadfsc_{link_type}"]

    new_query = urlencode({k: v[0] if len(v) == 1 else v for k, v in params.items()}, doseq=True)
    tracking_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    return tracking_url


def generate_summary():
    """生成每日汇总数据"""
    posts = _load_json(POSTS_FILE)
    interactions = _load_json(INTERACTIONS_FILE)
    
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    
    def filter_by_date(records, since_date):
        return [r for r in records if r.get("timestamp", "")[:10] >= since_date]
    
    # Posts summary
    today_posts = filter_by_date(posts, today)
    week_posts = filter_by_date(posts, week_ago)
    month_posts = filter_by_date(posts, month_ago)
    
    # By platform
    platform_stats = defaultdict(lambda: {"today": 0, "week": 0, "month": 0, "success": 0, "failed": 0})
    for p in posts:
        plat = p["platform"]
        ts = p.get("timestamp", "")[:10]
        platform_stats[plat]["month"] += 1
        if ts >= week_ago:
            platform_stats[plat]["week"] += 1
        if ts >= today:
            platform_stats[plat]["today"] += 1
        if p["status"] == "success":
            platform_stats[plat]["success"] += 1
        else:
            platform_stats[plat]["failed"] += 1
    
    # Interactions summary
    today_interactions = filter_by_date(interactions, today)
    week_interactions = filter_by_date(interactions, week_ago)
    month_interactions = filter_by_date(interactions, month_ago)
    
    interaction_stats = defaultdict(lambda: {"today": 0, "week": 0, "month": 0})
    for i in interactions:
        plat = i["platform"]
        ts = i.get("timestamp", "")[:10]
        interaction_stats[plat]["month"] += 1
        if ts >= week_ago:
            interaction_stats[plat]["week"] += 1
        if ts >= today:
            interaction_stats[plat]["today"] += 1
    
    # Action breakdown
    action_stats = defaultdict(int)
    for i in month_interactions:
        action_stats[i["action"]] += 1
    
    # Daily trend (last 30 days)
    daily_trend = defaultdict(lambda: {"posts": 0, "interactions": 0})
    for p in month_posts:
        day = p.get("timestamp", "")[:10]
        daily_trend[day]["posts"] += 1
    for i in month_interactions:
        day = i.get("timestamp", "")[:10]
        daily_trend[day]["interactions"] += 1
    
    # Hourly distribution (for optimal posting time)
    hourly_dist = defaultdict(int)
    for p in month_posts:
        if p["status"] == "success":
            hour = int(p.get("timestamp", "T00")[11:13])
            hourly_dist[hour] += 1
    
    summary = {
        "generated_at": now.isoformat() + "Z",
        "period": {
            "today": today,
            "yesterday": yesterday,
            "week_ago": week_ago,
            "month_ago": month_ago
        },
        "totals": {
            "posts_today": len(today_posts),
            "posts_week": len(week_posts),
            "posts_month": len(month_posts),
            "interactions_today": len(today_interactions),
            "interactions_week": len(week_interactions),
            "interactions_month": len(month_interactions),
            "success_rate": round(
                len([p for p in month_posts if p["status"] == "success"]) / max(len(month_posts), 1) * 100, 1
            )
        },
        "platforms": dict(platform_stats),
        "interactions_by_platform": dict(interaction_stats),
        "action_breakdown": dict(action_stats),
        "daily_trend": dict(daily_trend),
        "hourly_distribution": dict(hourly_dist),
        "recent_posts": posts[-20:],
        "recent_interactions": interactions[-20:]
    }

    # Add click and registration data
    clicks_file = os.path.join(ANALYTICS_DIR, "clicks.json")
    clicks = _load_json(clicks_file)
    regs_file = os.path.join(ANALYTICS_DIR, "registrations.json")
    regs = _load_json(regs_file)

    today_clicks = filter_by_date(clicks, today)
    week_clicks = filter_by_date(clicks, week_ago)
    month_clicks = filter_by_date(clicks, month_ago)

    today_regs = filter_by_date(regs, today)
    week_regs = filter_by_date(regs, week_ago)
    month_regs = filter_by_date(regs, month_ago)

    # Clicks by source platform
    click_by_source = defaultdict(lambda: {"today": 0, "week": 0, "month": 0})
    for c in clicks:
        src = c.get("source_platform", "unknown")
        ts = c.get("timestamp", "")[:10]
        click_by_source[src]["month"] += 1
        if ts >= week_ago:
            click_by_source[src]["week"] += 1
        if ts >= today:
            click_by_source[src]["today"] += 1

    # Registrations by source
    reg_by_source = defaultdict(int)
    reg_by_interest = defaultdict(int)
    for r in regs:
        if r.get("timestamp", "")[:10] >= month_ago:
            reg_by_source[r.get("source", "unknown")] += 1
            reg_by_interest[r.get("interests", "unknown")] += 1

    summary["clicks"] = {
        "today": len(today_clicks),
        "week": len(week_clicks),
        "month": len(month_clicks),
        "by_source": dict(click_by_source),
        "recent": clicks[-10:]
    }
    summary["registrations"] = {
        "today": len(today_regs),
        "week": len(week_regs),
        "month": len(month_regs),
        "total": len(regs),
        "by_source": dict(reg_by_source),
        "by_interest": dict(reg_by_interest),
        "recent": regs[-10:]
    }

    _save_json(SUMMARY_FILE, summary)
    return summary


# Auto-detect if analytics is available
try:
    _ensure_dir()
    HAS_ANALYTICS = True
except Exception:
    HAS_ANALYTICS = False


if __name__ == "__main__":
    # Test + generate dashboard
    summary = generate_summary()
    print(f"Summary generated: {summary['totals']}")
