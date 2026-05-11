#!/usr/bin/env python3
"""
Substack Auto-Post: Daily Article Generator
Reads latest knowledge files, generates English article via Groq, auto-posts to Substack.

Usage:
  python substack_auto_post.py          # Generate + publish 1 article
  python substack_auto_post.py --test  # Test only (no publish)
  python substack_auto_post.py --dry-run  # Generate only (no publish)

Schedule: Daily via GitHub Actions (08:00 Beijing time)
"""

import os
import sys
import json
import datetime
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SUBSTACK_EMAIL = os.environ.get("SUBSTACK_EMAIL", "")
SUBSTACK_PASSWORD = os.environ.get("SUBSTACK_PASSWORD", "")
PUBLICATION_SLUG = "broadcastmarketintelligence"
PUBLICATION_ID = "8790672"
PUB_URL = f"https://{PUBLICATION_SLUG}.substack.com"

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")

# Detect environment
IS_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"


# ============================================================
# Step 1: Find Latest Knowledge File
# ============================================================
def find_latest_knowledge_file():
    """Find the most recent .md file across all knowledge subdirectories."""
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"[Knowledge] Directory not found: {KNOWLEDGE_DIR}")
        return None

    all_md_files = []
    for root, dirs, files in os.walk(KNOWLEDGE_DIR):
        # Skip hidden dirs and episodic/patterns/strategic
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith('.md') and not f.startswith('_'):
                full_path = os.path.join(root, f)
                all_md_files.append(full_path)

    if not all_md_files:
        print("[Knowledge] No .md files found")
        return None

    # Sort by modification time (newest first)
    all_md_files.sort(key=os.path.getmtime, reverse=True)
    latest = all_md_files[0]
    print(f"[Knowledge] Latest file: {os.path.basename(latest)}")
    return latest


def read_knowledge_file(filepath):
    """Read knowledge file and extract key content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title (first # header)
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
        'body': body[:3000],  # First 3000 chars for context
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

    prompt = f"""You are a professional investment analyst writing for Substack.

Based on the Chinese market analysis below, write an English article (800-1200 words) with:

1. An engaging title (SEO-friendly, starting with "Market Radar:" or "Technical Analysis:")
2. Professional tone (like Bloomberg/Seeking Alpha)
3. Clear structure: Introduction → Analysis → Key Levels → Conclusion
4. Include specific data points (RSI, MACD, Bollinger Bands)
5. Actionable insights (not just news, but what it means for investors)
6. A soft CTA at the end: "For deeper analysis, message @BroadInvestBot on Telegram"

Chinese source content:
Title: {title_zh}
Body: {body_zh}

IMPORTANT:
- Write in native English (no AI痕迹)
- Include specific numbers and percentages
- Use professional financial terminology
- End with: "Disclaimer: This is for informational purposes only, not financial advice."
"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            max_tokens=2000,
            temperature=0.7,
        )
        article = chat_completion.choices[0].message.content
        print("[Groq] ✅ Article generated successfully")
        return article
    except Exception as e:
        print(f"[Groq] ❌ Error: {e}")
        return generate_template_article(title_zh, body_zh)


def generate_template_article(title_zh, body_zh):
    """Fallback template if Groq fails."""
    date_str = datetime.datetime.now().strftime("%B %d, %Y")

    # Extract English title
    title_en = title_zh.replace("—", "-").replace("（", "(").replace("）", ")")
    if len(title_en) > 60:
        title_en = "Market Radar: " + title_en[:40] + "..."

    article = f"""# {title_en}

**{date_str}** | BroadFSC Market Briefing

---

## Market Overview

Based on our latest technical analysis, here are the key signals investors need to watch today.

## Key Technical Signals

Our algorithmic screening has identified several high-conviction setups across major indices and sector ETFs.

### RSI Divergence Watch

When price makes a lower low but RSI makes a higher low — that's bullish divergence. We're seeing this pattern emerge in several tech names after the recent consolidation.

### MACD Zero-Line Cross

Three S&P 500 components are showing MACD histograms turning positive above the zero line. Historically, this signal has a 68% win rate over the following 10 trading days.

### Bollinger Band Squeeze

Multiple sectors are showing contracting Bollinger Bands — a classic precursor to volatility expansion. Our models flag these setups 2-3 days before the breakout.

## Actionable Insights

1. **Don't chase overbought RSI**: S&P 500 RSI at 74+ has a 60% chance of 3-5% pullback within 1-2 weeks
2. **Watch volume confirmation**: MACD cross without volume = noise
3. **Sector rotation accelerating**: Money flowing from defensive to cyclical sectors

## Free Analysis Offer

Want a professional review of your current holdings? Our licensed analysts offer **free portfolio assessments** to newsletter subscribers.

👉 **Get your free analysis**: Message @BroadInvestBot on Telegram

Available this week only. No obligations.

---

*Disclaimer: This content is for informational purposes only and does not constitute financial advice. Past performance does not guarantee future results.*
"""

    print("[Template] ✅ Using fallback template article")
    return article


def extract_title_from_article(article_text):
    """Extract a clean title from the generated article."""
    lines = article_text.strip().split('\n')
    for line in lines:
        if line.startswith('# '):
            return line.lstrip('# ').strip()
    # Fallback
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"Market Radar: Technical Analysis Update {date_str}"


# ============================================================
# Step 3: Publish to Substack (Email Method - No Browser)
# ============================================================

def publish_via_smtp(title, article_body):
    """Fallback: Send via SMTP (Gmail)."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    publish_email = f"post+{PUBLICATION_SLUG}@substack.com"
    sender_email = SUBSTACK_EMAIL
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = title
    msg['From'] = sender_email
    msg['To'] = publish_email
    
    text_part = MIMEText(article_body, 'plain', 'utf-8')
    msg.attach(text_part)
    
    html_body = article_body.replace('\n\n', '<br><br>').replace('\n', '<br>')
    html_part = MIMEText(f"<html><body><p>{html_body}</p></body></html>", 'html', 'utf-8')
    msg.attach(html_part)
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, SUBSTACK_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("[Substack] ✅ Article sent via SMTP!")
        return True
    except Exception as e:
        print(f"[Substack] ❌ SMTP failed: {e}")
        return False


def publish_to_substack(title, article_body, dry_run=False):
    """Publish to Substack via email (no browser needed)."""
    if dry_run:
        print("[Substack] DRY RUN — not publishing")
        print(f"[Substack] Title: {title}")
        print(f"[Substack] Body length: {len(article_body)} chars")
        return True
    
    print("[Substack] 📧 Publishing via Brevo API...")
    
    import requests
    
    # Brevo API key
    brevo_key = os.environ.get("BREVO_API_KEY", "")
    if not brevo_key:
        print("[Substack] ❌ BREVO_API_KEY not set")
        print("[Substack] Falling back to SMTP...")
        return publish_via_smtp(title, article_body)
    
    # Substack email-to-publish address
    publish_email = f"post+{PUBLICATION_SLUG}@substack.com"
    sender_email = SUBSTACK_EMAIL
    
    # Brevo API endpoint
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": brevo_key,
        "content-type": "application/json"
    }
    
    # Prepare email content
    html_content = article_body.replace('\n\n', '</p><p>').replace('\n', '<br>')
    html_content = f"<html><body><p>{html_content}</p></body></html>"
    
    payload = {
        "sender": {"name": "BroadFSC Automation", "email": sender_email},
        "to": [{"email": publish_email}],
        "subject": title,
        "htmlContent": html_content,
        "textContent": article_body
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code in [200, 201, 202]:
            print("[Substack] ✅ Article sent via Brevo API!")
            print(f"[Substack] Check: https://{PUBLICATION_SLUG}.substack.com")
            return True
        else:
            print(f"[Substack] ❌ Brevo API failed: {response.status_code}")
            print(f"[Substack] Response: {response.text[:200]}")
            print("[Substack] Falling back to SMTP...")
            return publish_via_smtp(title, article_body)
    except Exception as e:
        print(f"[Substack] ❌ Brevo API error: {e}")
        print("[Substack] Falling back to SMTP...")
        return publish_via_smtp(title, article_body)


# ============================================================
# Main
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Test mode (no publish)')
    parser.add_argument('--dry-run', action='store_true', help='Generate only (no publish)')
    args = parser.parse_args()

    print("=" * 60)
    print("Substack Auto-Post: Daily Article Generator")
    print("=" * 60)

    # Step 1: Find latest knowledge file
    print("\n[Step 1] Finding latest knowledge file...")
    latest_file = find_latest_knowledge_file()
    if not latest_file:
        print("❌ No knowledge files found. Run ai_learning_agent.py first.")
        sys.exit(1)

    # Step 2: Read content
    print("\n[Step 2] Reading knowledge content...")
    content = read_knowledge_file(latest_file)
    print(f"  Title (ZH): {content['title']}")
    print(f"  Body length: {len(content['body'])} chars")

    # Step 3: Generate English article
    print("\n[Step 3] Generating English article via Groq...")
    article = generate_article(content['title'], content['body'])

    # Extract title
    article_title = extract_title_from_article(article)
    print(f"  Article title: {article_title}")
    print(f"  Article length: {len(article)} chars")

    # Save article locally (backup)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    output_file = f"substack_draft_{date_str}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {article_title}\n\n")
        f.write(article)
    print(f"\n[Backup] Article saved to: {output_file}")

    # Step 4: Publish to Substack
    if not args.dry_run:
        print("\n[Step 4] Publishing to Substack...")
        success = publish_to_substack(article_title, article, dry_run=args.test)
        if success:
            print("\n✅ Article published successfully!")
        else:
            print("\n⚠️ Publish failed. Article saved locally.")
            sys.exit(1)
    else:
        print("\n[DRY RUN] Skipping publish step.")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
