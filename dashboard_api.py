"""
BroadFSC Analytics Dashboard — Flask API Backend
Serves analytics data as JSON API and the dashboard HTML.

Run: python dashboard_api.py
Open: http://localhost:5000
"""

import os
import sys
import json
import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from flask import Flask, jsonify, request, send_from_directory, redirect
from analytics_db import init_db, get_db, close_db, log_click, log_website_visit, log_conversation

app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)))

# Initialize DB on startup
init_db()


# ============================================================
# API Endpoints
# ============================================================

@app.route('/')
def index():
    """Serve the dashboard HTML."""
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')
    if os.path.exists(dashboard_path):
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')
    return "<h1>BroadFSC Analytics Dashboard</h1><p>dashboard.html not found</p>"


@app.route('/api/overview')
def api_overview():
    """Get overview stats."""
    days = request.args.get('days', 30, type=int)
    from analytics_db import get_overview
    return jsonify(get_overview(days=days))


@app.route('/api/trend')
def api_trend():
    """Get daily trend data."""
    days = request.args.get('days', 30, type=int)
    from analytics_db import get_daily_trend
    return jsonify(get_daily_trend(days=days))


@app.route('/api/recent/posts')
def api_recent_posts():
    """Get recent posts."""
    limit = request.args.get('limit', 50, type=int)
    from analytics_db import get_recent_posts
    return jsonify(get_recent_posts(limit=limit))


@app.route('/api/recent/conversations')
def api_recent_conversations():
    """Get recent conversations."""
    limit = request.args.get('limit', 50, type=int)
    from analytics_db import get_recent_conversations
    return jsonify(get_recent_conversations(limit=limit))


@app.route('/api/hourly')
def api_hourly():
    """Get hourly distribution."""
    days = request.args.get('days', 7, type=int)
    from analytics_db import get_hourly_distribution
    return jsonify(get_hourly_distribution(days=days))


# ============================================================
# Click / Visit Tracking Endpoints
# ============================================================

@app.route('/track/click')
def track_click():
    """Track a click event (called from short links)."""
    source = request.args.get('source', 'unknown')
    post_id = request.args.get('post_id', '')
    link_type = request.args.get('type', 'website')
    target = request.args.get('url', 'https://www.broadfsc.com/different')
    campaign = request.args.get('campaign', '')

    # Get visitor info
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    import hashlib
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16] if ip else ''

    log_click(
        source_platform=source,
        source_post_id=post_id,
        link_type=link_type,
        target_url=target,
        ip_hash=ip_hash,
        referrer=request.headers.get('Referer', '')
    )

    # Redirect to target
    return redirect(target)


@app.route('/track/visit')
def track_visit():
    """Track a website visit (called from website embed)."""
    source = request.args.get('source', 'direct')
    campaign = request.args.get('campaign', '')

    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    import hashlib
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16] if ip else ''

    log_website_visit(
        source=source,
        campaign=campaign,
        ip_hash=ip_hash,
        user_agent=request.headers.get('User-Agent', ''),
        referrer=request.headers.get('Referer', '')
    )

    return jsonify({'status': 'ok'})


@app.route('/track/conversation', methods=['POST'])
def track_conversation():
    """Track a conversation event (called from telegram_bot.py)."""
    data = request.get_json() or {}
    log_conversation(
        platform=data.get('platform', 'telegram'),
        user_id=data.get('user_id', ''),
        user_name=data.get('user_name', ''),
        direction=data.get('direction', 'inbound'),
        message_type=data.get('message_type', 'text'),
        is_ai_response=data.get('is_ai_response', True),
        chat_mode=data.get('chat_mode', 'auto')
    )
    return jsonify({'status': 'ok'})


# ============================================================
# Health check
# ============================================================

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'db_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analytics.db'),
        'time': datetime.datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    print("🚀 BroadFSC Analytics Dashboard starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/overview")
    app.run(host='0.0.0.0', port=5000, debug=False)
