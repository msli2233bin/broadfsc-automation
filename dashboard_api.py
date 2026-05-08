"""
BroadFSC Analytics Dashboard API
Serves JSON data for the HTML dashboard visualization.
"""
import os, sys, json, datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def get_full_report(days=30):
    """Get complete analytics report for dashboard."""
    from analytics_db import (
        get_overview, get_daily_trend, get_recent_posts,
        get_hourly_distribution, get_customer_count, get_customer_pipeline,
        get_recent_engagements, get_funnel_metrics
    )

    overview = get_overview(days=days)
    trend = get_daily_trend(days=days)
    hourly = get_hourly_distribution(days=days)
    recent_posts = get_recent_posts(limit=20)
    customers = get_customer_count()
    pipeline = get_customer_pipeline()
    funnel = get_funnel_metrics(days=days)

    # Format recent posts
    formatted_posts = []
    for p in recent_posts:
        formatted_posts.append({
            'ts': p['timestamp'][:19] if p.get('timestamp') else '?',
            'platform': p.get('platform', '?'),
            'type': p.get('post_type', '?'),
            'status': p.get('status', '?'),
            'preview': (p.get('content_preview', '') or '')[:60],
        })

    # Platform summary
    platform_summary = {}
    for plat, count in overview.get('posts_by_platform', {}).items():
        platform_summary[plat] = {
            'posts': count,
            'customers': customers.get(plat, {}).get('total', 0),
            'engaged': customers.get(plat, {}).get('engaged', 0),
        }

    # Post success rate by platform
    from analytics_db import get_db
    db = get_db()
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()
    rows = db.execute("""
        SELECT platform,
               COUNT(*) as total,
               SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success
        FROM posts WHERE timestamp >= ?
        GROUP BY platform
    """, (since,)).fetchall()
    success_rates = {}
    for r in rows:
        total = r['total'] or 1
        success_rates[r['platform']] = round(r['success'] / total * 100, 1)

    return {
        'report_time': datetime.datetime.utcnow().isoformat(),
        'days': days,
        'overview': overview,
        'trend': trend,
        'hourly': hourly,
        'recent_posts': formatted_posts,
        'platform_summary': platform_summary,
        'success_rates': success_rates,
        'customers': customers,
        'pipeline': pipeline,
        'funnel': funnel,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--output', '-o', default=None)
    args = parser.parse_args()

    report = get_full_report(days=args.days)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Report saved to {args.output}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
