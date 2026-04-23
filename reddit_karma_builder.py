"""
BroadFSC Reddit Karma Builder - 自动生成高质量评论建议
帮助用户快速积累 comment karma 到 50+ 门槛

策略：在热门金融/投资 subreddit 搜索最新帖子，AI生成有价值的回复建议
用户只需复制粘贴到Reddit网页即可

运行方式：python reddit_karma_builder.py
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
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Target subreddits for karma building (high activity, investment related)
TARGET_SUBREDDITS = [
    "investing",          # 2M+ members, general investing
    "stocks",             # 900K+ members, stock discussion
    "personalfinance",    # 18M+ members, personal finance
    "financialindependence", # 2M+ members, FIRE movement
    "dividends",          # 300K+ members, dividend investing
    "options",            # 400K+ members, options trading
    "stockmarket",        # 300K+ members, market discussion
    "ValueInvesting",     # 300K+ members, value investing
    "SecurityAnalysis",   # 100K+ members, deeper analysis
    "ETFs",              # 200K+ members, ETF discussion
]

# RSS-to-JSON service to bypass Reddit IP ban (codetabs returns empty for subreddit feeds)
RSS_API = "https://api.rss2json.com/v1/api.json?rss_url=https://www.reddit.com/r/"


def fetch_subreddit_posts(subreddit, limit=5):
    """Fetch latest hot posts from a subreddit via RSS-to-JSON service."""
    import requests
    
    url = f"{RSS_API}{subreddit}/hot.rss"
    
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            print(f"  Failed to fetch r/{subreddit}: HTTP {r.status_code}")
            return []
        
        data = r.json()
        if data.get("status") != "ok":
            print(f"  RSS error for r/{subreddit}: {data.get('message', 'unknown')}")
            return []
        
        items = data.get("items", [])
        
        results = []
        for item in items[:limit]:
            # Skip stickied posts (usually "Daily Discussion" threads)
            title = item.get("title", "")
            if "daily" in title.lower() and "discussion" in title.lower():
                continue
            if "weekly" in title.lower():
                continue
                
            # Extract permalink from the link
            link = item.get("link", "")
            permalink = link if link else f"https://www.reddit.com/r/{subreddit}/"
            
            # Extract description (selftext preview)
            description = item.get("description", "")[:500]
            # Clean HTML from description
            description = re.sub(r'<[^>]+>', '', description)
            
            # Extract comment count from description if available
            num_comments = 0
            comments_match = re.search(r'(\d+)\s*comments?', description, re.IGNORECASE)
            if comments_match:
                num_comments = int(comments_match.group(1))
            
            results.append({
                "title": title,
                "selftext": description,
                "author": item.get("author", ""),
                "score": 0,  # RSS doesn't provide score
                "num_comments": num_comments,
                "permalink": permalink,
                "subreddit": subreddit,
                "created_utc": 0,
            })
        
        return results
    except Exception as e:
        print(f"  Error fetching r/{subreddit}: {str(e)[:100]}")
        return []


def generate_reply_suggestion(post, subreddit):
    """Use Groq AI to generate a helpful, genuine reply suggestion."""
    import requests
    
    if not GROQ_API_KEY:
        # Fallback: generate template reply
        return generate_template_reply(post, subreddit)
    
    prompt = f"""You are helping a Reddit user build karma by writing genuine, helpful comments in r/{subreddit}.

IMPORTANT RULES:
- Be genuinely helpful and knowledgeable about investing/finance
- Do NOT mention any company, brand, or service
- Do NOT include any links or self-promotion
- Write like a real person, not an AI or corporate account
- Keep it 3-6 sentences, conversational tone
- Add a specific insight or personal perspective
- If the post asks a question, answer it directly

Post title: {post['title']}
Post content: {post['selftext']}

Write a genuine, helpful reply (3-6 sentences):"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.8,
            },
            timeout=15,
        )
        
        if r.status_code == 200:
            reply = r.json()["choices"][0]["message"]["content"].strip()
            # Clean up any remaining promotional content
            reply = re.sub(r'(broadfsc|broad investment|broadfsc\.com)', '', reply, flags=re.IGNORECASE)
            return reply
        else:
            return generate_template_reply(post, subreddit)
    except Exception as e:
        print(f"  AI generation failed: {str(e)[:50]}")
        return generate_template_reply(post, subreddit)


def generate_template_reply(post, subreddit):
    """Fallback: generate a template-based reply."""
    title = post['title'].lower()
    
    if '?' in post['title']:
        if 'etf' in title or 'index' in title:
            return "Great question! For most investors starting out, broad market ETFs like VTI or VXUS give you instant diversification at minimal cost. The key is consistency - regular contributions matter more than timing. What's your current allocation looking like?"
        elif 'dividend' in title:
            return "Dividend investing is a solid long-term strategy. Focus on companies with a history of growing dividends, not just high yields. A 3% growing dividend beats an 8% shrinking one. Consider SCHD or VYM for diversified exposure."
        elif 'option' in title or 'call' in title or 'put' in title:
            return "Options can be powerful but they're not for everyone. If you're just starting, paper trade for at least 3 months. The Greeks matter more than you think - especially theta decay on weekly options. What's your risk tolerance?"
        else:
            return "This is a really thoughtful question. From my experience, the most important thing is to have a clear strategy and stick to it regardless of market noise. Dollar cost averaging into quality assets has worked well for many long-term investors."
    else:
        return "Interesting perspective! I've been thinking about this too. The data supports a balanced approach - keeping emotions out of investment decisions is easier said than done but makes a huge difference in returns over time."


def send_telegram_report(opportunities):
    """Send karma building opportunities to Telegram."""
    if not BOT_TOKEN or not CHANNEL_ID:
        print("  Telegram not configured, skipping")
        return
    
    import requests
    
    msg = "🎯 <b>Reddit Karma Building - Daily Targets</b>\n\n"
    msg += f"u/{REDDIT_USERNAME} — Need 50 comment karma\n\n"
    
    for i, opp in enumerate(opportunities[:8], 1):
        msg += f"<b>{i}. r/{opp['subreddit']}</b>\n"
        msg += f"📝 {opp['title'][:60]}...\n"
        msg += f"💬 Suggested reply:\n{opp['reply'][:150]}\n\n"
    
    msg += "📋 Steps: Open link → Read post → Post your reply\n"
    msg += "💡 5-10 replies/day = 50 karma in ~1-2 weeks"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("  Telegram report sent ✅")
        else:
            print(f"  Telegram failed: HTTP {r.status_code}")
    except Exception as e:
        print(f"  Telegram failed: {e}")


def main():
    print("=" * 50)
    print("BroadFSC Reddit Karma Builder")
    print("=" * 50)
    print(f"User: u/{REDDIT_USERNAME}")
    print(f"Target: 50 comment karma")
    print(f"Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()
    
    # Fetch posts from multiple subreddits
    all_posts = []
    print("Fetching hot posts from target subreddits...")
    
    for sr in TARGET_SUBREDDITS[:5]:  # Top 5 to avoid rate limits
        print(f"  r/{sr}...", end=" ")
        posts = fetch_subreddit_posts(sr, limit=3)
        print(f"{len(posts)} posts")
        all_posts.extend(posts)
    
    if not all_posts:
        print("No posts fetched. Check proxy availability.")
        return
    
    # Prioritize questions (more likely to get upvoted replies)
    question_posts = [p for p in all_posts if '?' in p['title']]
    other_posts = [p for p in all_posts if '?' not in p['title']]
    all_posts_sorted = question_posts + other_posts
    
    # Pick top 8 posts
    opportunities = []
    for post in all_posts_sorted[:15]:
        # Skip very short titles
        if len(post['title']) < 15:
            continue

        print(f"\n  Generating reply for: {post['title'][:60]}...")
        reply = generate_reply_suggestion(post, post['subreddit'])
        opportunities.append({
            "subreddit": post['subreddit'],
            "title": post['title'],
            "permalink": post['permalink'],
            "num_comments": post['num_comments'],
            "reply": reply,
        })
        print(f"    Reply: {reply[:80]}...")
        
        if len(opportunities) >= 8:
            break
    
    # Print opportunities
    print()
    print("=" * 50)
    print("TODAY'S KARMA BUILDING TARGETS")
    print("=" * 50)
    
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. r/{opp['subreddit']} ({opp['num_comments']} comments)")
        print(f"   Title: {opp['title'][:80]}")
        print(f"   Link: {opp['permalink']}")
        print(f"   Suggested reply: {opp['reply'][:150]}")
    
    # Save to file for easy reference
    output = {
        "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        "username": REDDIT_USERNAME,
        "opportunities": opportunities,
    }
    
    os.makedirs("knowledge", exist_ok=True)
    with open("knowledge/reddit_karma_targets.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to knowledge/reddit_karma_targets.json")
    
    # Send Telegram
    print("\nSending Telegram report...")
    send_telegram_report(opportunities)
    
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("1. Open each link in your browser")
    print("2. Read the full post")
    print("3. Customize and post the suggested reply")
    print("4. Target: 5-10 replies/day = 50 karma in 1-2 weeks")
    print("=" * 50)


if __name__ == "__main__":
    main()
