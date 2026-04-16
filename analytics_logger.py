"""
BroadFSC Analytics Logger
统一数据采集模块 - 所有推广脚本共用

功能：
- 记录帖子发布（platform, type, content, status）
- 记录用户互动（bot对话、按钮点击）
- 生成 dashboard.html 可视化看板
- JSON 文件存储，GitHub Actions 自动更新

数据文件：
- analytics/posts.json  — 帖子发布记录
- analytics/interactions.json — 用户互动记录
- analytics/summary.json — 每日汇总（dashboard 读取）
"""

import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

ANALYTICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics")
POSTS_FILE = os.path.join(ANALYTICS_DIR, "posts.json")
INTERACTIONS_FILE = os.path.join(ANALYTICS_DIR, "interactions.json")
SUMMARY_FILE = os.path.join(ANALYTICS_DIR, "summary.json")


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
    """记录一次帖子发布"""
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
