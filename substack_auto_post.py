#!/usr/bin/env python3
"""
Substack Auto-Post: Daily Article Generator
Reads latest knowledge files, generates English article via Groq, auto-posts to Substack.

Publishing methods (auto-detected):
1. Playwright launch_persistent_context (local Windows — most reliable)
2. Brevo API email (CI/GitHub Actions fallback)

Usage:
  python substack_auto_post.py          # Generate + publish (auto-detect method)
  python substack_auto_post.py --playwright  # Force Playwright method
  python substack_auto_post.py --email       # Force email/Brevo method
  python substack_auto_post.py --test        # Test only (no publish)
  python substack_auto_post.py --dry-run     # Generate only (no publish)

Schedule: Daily via GitHub Actions (08:00 Beijing time)
"""

import os
import sys
import json
import datetime
import requests
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
PUBLICATION_SLUG = "broadcastmarketintelligence"
PUB_URL = "https://{}.substack.com".format(PUBLICATION_SLUG)

# Substack email posting address
SUBSTACK_POST_EMAIL = os.environ.get(
    "SUBSTACK_POST_EMAIL",
    "post+broadcastmarketintelligence@substack.com"
)

# Brevo API (for sending emails — CI fallback)
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "msli2233bin+brevo@gmail.com")

# Playwright profile paths
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
STATE_FILE = os.path.join(SESSION_DIR, "state.json")
PROFILE_DIR = os.path.join(SESSION_DIR, "substack_profile")

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")

# Fallback: load from .env if running locally
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            _k, _v = _k.strip(), _v.strip()
            if _k == "BREVO_API_KEY" and not BREVO_API_KEY:
                BREVO_API_KEY = _v
            elif _k == "BREVO_SENDER_EMAIL" and not BREVO_SENDER_EMAIL:
                BREVO_SENDER_EMAIL = _v
            elif _k == "GROQ_API_KEY" and not GROQ_API_KEY:
                GROQ_API_KEY = _v


# ============================================================
# Step 1: Find Latest Knowledge File
# ============================================================
def find_latest_knowledge_file():
    """Find the most recent .md file across all knowledge subdirectories."""
    if not os.path.exists(KNOWLEDGE_DIR):
        print("[Knowledge] Directory not found: {}".format(KNOWLEDGE_DIR))
        return None

    all_md_files = []
    for root, dirs, files in os.walk(KNOWLEDGE_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith('.md') and not f.startswith('_'):
                full_path = os.path.join(root, f)
                all_md_files.append(full_path)

    if not all_md_files:
        print("[Knowledge] No .md files found")
        return None

    all_md_files.sort(key=os.path.getmtime, reverse=True)
    latest = all_md_files[0]
    print("[Knowledge] Latest file: {}".format(os.path.basename(latest)))
    return latest


def read_knowledge_file(filepath):
    """Read knowledge file and extract key content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    title = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line.lstrip('# ').strip()
            body_start = i + 1
            break

    body = '\n'.join(lines[body_start:])

    return {
        'title': title,
        'body': body[:3000],
        'filename': os.path.basename(filepath)
    }


# ============================================================
# Step 2: Generate English Article via Groq
# ============================================================
def generate_article(title_zh, body_zh):
    """Use Groq to generate an English investment article."""
    if not GROQ_API_KEY:
        print("[Groq] No API key, using template fallback")
        return generate_template_article(title_zh, body_zh)

    try:
        from groq import Groq
    except ImportError:
        print("[Groq] groq package not installed, using template fallback")
        return generate_template_article(title_zh, body_zh)

    client = Groq(api_key=GROQ_API_KEY)

    prompt = """You are a professional investment analyst writing for Substack.

Based on the Chinese market analysis below, write an English article (800-1200 words) with:

1. An engaging title (SEO-friendly, starting with "Market Radar:" or "Technical Analysis:")
2. Professional tone (like Bloomberg/Seeking Alpha)
3. Clear structure: Introduction -> Analysis -> Key Levels -> Conclusion
4. Include specific data points (RSI, MACD, Bollinger Bands)
5. Actionable insights (not just news, but what it means for investors)
6. A soft CTA at the end: "For deeper analysis, message @BroadInvestBot on Telegram"

Chinese source content:
Title: {}
Body: {}

IMPORTANT:
- Write in native English (no AI traces)
- Include specific numbers and percentages
- Use professional financial terminology
- End with: "Disclaimer: This is for informational purposes only, not financial advice."
""".format(title_zh, body_zh)

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            max_tokens=2000,
            temperature=0.7,
        )
        article = chat_completion.choices[0].message.content
        print("[Groq] + Article generated successfully")
        return article
    except Exception as e:
        print("[Groq] x Error: {}".format(e))
        return generate_template_article(title_zh, body_zh)


def generate_template_article(title_zh, body_zh):
    """Fallback template if Groq fails."""
    date_str = datetime.datetime.now().strftime("%B %d, %Y")
    title_en = title_zh.replace("\u2014", "-").replace("\uff08", "(").replace("\uff09", ")")
    if len(title_en) > 60:
        title_en = "Market Radar: " + title_en[:40] + "..."

    article = """# {}

**{}** | BroadFSC Market Briefing

---

## Market Overview

Based on our latest technical analysis, here are the key signals investors need to watch today.

## Key Technical Signals

Our algorithmic screening has identified several high-conviction setups across major indices and sector ETFs.

### RSI Divergence Watch

When price makes a lower low but RSI makes a higher low - that is bullish divergence. We are seeing this pattern emerge in several tech names after the recent consolidation.

### MACD Zero-Line Cross

Three S&P 500 components are showing MACD histograms turning positive above the zero line. Historically, this signal has a 68% win rate over the following 10 trading days.

### Bollinger Band Squeeze

Multiple sectors are showing contracting Bollinger Bands - a classic precursor to volatility expansion. Our models flag these setups 2-3 days before the breakout.

## Actionable Insights

1. **Don't chase overbought RSI**: S&P 500 RSI at 74+ has a 60% chance of 3-5% pullback within 1-2 weeks
2. **Watch volume confirmation**: MACD cross without volume = noise
3. **Sector rotation accelerating**: Money flowing from defensive to cyclical sectors

## Free Analysis Offer

Want a professional review of your current holdings? Our licensed analysts offer **free portfolio assessments** to newsletter subscribers.

For deeper analysis, message @BroadInvestBot on Telegram

Available this week only. No obligations.

---

*Disclaimer: This content is for informational purposes only and does not constitute financial advice. Past performance does not guarantee future results.*
""".format(title_en, date_str)

    print("[Template] + Using fallback template article")
    return article


def extract_title_from_article(article_text):
    """Extract a clean title from the generated article."""
    lines = article_text.strip().split('\n')
    for line in lines:
        if line.startswith('# '):
            return line.lstrip('# ').strip()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return "Market Radar: Technical Analysis Update {}".format(date_str)


# ============================================================
# Step 3: Publish to Substack (Playwright or Brevo)
# ============================================================
def publish_via_playwright(title, article_body):
    """Publish via Playwright launch_persistent_context (most reliable, local only)."""
    try:
        from substack_cookie_publish import publish_article
        print("[Playwright] Attempting publish via launch_persistent_context...")
        success = publish_article(title, article_body)
        if success:
            print("[Playwright] + Article published successfully!")
        else:
            print("[Playwright] - Publishing failed")
        return success
    except ImportError:
        print("[Playwright] substack_cookie_publish module not available")
        return False
    except Exception as e:
        print("[Playwright] Error: {}".format(e))
        return False


def publish_via_email(title, article_body):
    """Publish via Brevo API email (fallback for CI)."""
    if not BREVO_API_KEY:
        print("[Email] x BREVO_API_KEY not configured")
        return False

    if not SUBSTACK_POST_EMAIL:
        print("[Email] x SUBSTACK_POST_EMAIL not configured")
        return False

    print("[Email] Sending via Brevo -> {}".format(SUBSTACK_POST_EMAIL))

    html_body = markdown_to_simple_html(article_body)

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    payload = {
        "sender": {"name": "BroadFSC Market Intelligence", "email": BREVO_SENDER_EMAIL},
        "to": [{"email": SUBSTACK_POST_EMAIL}],
        "subject": title,
        "htmlContent": html_body,
        "textContent": article_body,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code in (200, 201):
            msg_id = r.json().get("messageId", "unknown")
            print("[Email] + Email sent! messageId={}".format(msg_id))
            return True
        else:
            print("[Email] x Brevo API error {}: {}".format(r.status_code, r.text[:300]))
            return False
    except requests.exceptions.ConnectionError:
        print("[Email] x Connection failed (network error)")
        return False
    except Exception as e:
        print("[Email] x Unexpected error: {}".format(e))
        return False


def markdown_to_simple_html(markdown_text):
    """Convert Markdown to simple HTML suitable for Substack email posting."""
    import re
    html = markdown_text

    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)

    lines = html.split('\n')
    result = []
    in_list = False
    for line in lines:
        if re.match(r'^[*\-] (.+)', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item = re.sub(r'^[*\-] ', '', line)
            result.append('<li>{}</li>'.format(item))
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')
    html = '\n'.join(result)

    paragraphs = html.split('\n\n')
    wrapped = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para.startswith('<'):
            wrapped.append(para)
        else:
            wrapped.append('<p>{}</p>'.format(para))
    html = '\n\n'.join(wrapped)

    return """<!DOCTYPE html>
<html>
<body style="font-family: Georgia, serif; max-width: 700px; margin: auto; padding: 20px; color: #333;">
{}
</body>
</html>""".format(html)


# ============================================================
# Main
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Test mode (no publish)')
    parser.add_argument('--dry-run', action='store_true', help='Generate only (no publish)')
    parser.add_argument('--playwright', action='store_true', help='Force Playwright method')
    parser.add_argument('--email', action='store_true', help='Force email/Brevo method')
    args = parser.parse_args()

    print("=" * 60)
    print("Substack Auto-Post: Daily Article Generator")
    print("=" * 60)

    # Step 1: Find latest knowledge file
    print("\n[Step 1] Finding latest knowledge file...")
    latest_file = find_latest_knowledge_file()
    if not latest_file:
        print("x No knowledge files found. Run ai_learning_agent.py first.")
        sys.exit(1)

    # Step 2: Read content
    print("\n[Step 2] Reading knowledge content...")
    content = read_knowledge_file(latest_file)
    print("  Title (ZH): {}".format(content['title']))
    print("  Body length: {} chars".format(len(content['body'])))

    # Step 3: Generate English article
    print("\n[Step 3] Generating English article via Groq...")
    article = generate_article(content['title'], content['body'])

    article_title = extract_title_from_article(article)
    print("  Article title: {}".format(article_title))
    print("  Article length: {} chars".format(len(article)))

    # Save article locally (backup)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    output_file = "substack_draft_{}.md".format(date_str)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# {}\n\n".format(article_title))
        f.write(article)
    print("\n[Backup] Article saved to: {}".format(output_file))

    # Step 4: Publish
    if args.dry_run:
        print("\n[DRY RUN] Skipping publish step.")
    elif args.test:
        print("\n[TEST] Skipping publish step.")
    else:
        print("\n[Step 4] Publishing to Substack...")

        # Extract body (without title header)
        body_lines = article.strip().split('\n')
        body_start = 0
        for i, line in enumerate(body_lines):
            if line.startswith('# '):
                body_start = i + 1
                break
        article_body = '\n'.join(body_lines[body_start:]).strip()

        published = False

        # Determine publishing method
        force_playwright = args.playwright
        force_email = args.email
        is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

        if force_playwright:
            # Force Playwright
            published = publish_via_playwright(article_title, article_body)
        elif force_email:
            # Force email
            published = publish_via_email(article_title, article)
        elif is_ci:
            # CI environment: use email (no browser profile available)
            print("[Auto-detect] CI environment detected, using email method")
            published = publish_via_email(article_title, article)
        else:
            # Local environment: try Playwright first, fall back to email
            print("[Auto-detect] Local environment, trying Playwright first")
            published = publish_via_playwright(article_title, article_body)
            if not published:
                print("[Fallback] Playwright failed, trying email method...")
                published = publish_via_email(article_title, article)

        if published:
            print("\n+ Article published successfully!")
        else:
            print("\nx Publish failed. Article saved locally.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
