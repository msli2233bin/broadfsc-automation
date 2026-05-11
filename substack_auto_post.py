#!/usr/bin/env python3
"""
Substack Auto-Post: Daily Article Generator (Fixed Version)
- Enhanced logging for debugging
- Better HTML formatting
- Validates configuration before sending
- Always saves article locally as backup

Usage:
  python substack_auto_post.py          # Generate + publish 1 article
  python substack_auto_post.py --test  # Test only (no publish)
  python substack_auto_post.py --dry-run  # Generate only (no publish)
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
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
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
        print(f"[Knowledge] ❌ Directory not found: {KNOWLEDGE_DIR}")
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
        print("[Knowledge] ❌ No .md files found")
        return None

    # Sort by modification time (newest first)
    all_md_files.sort(key=os.path.getmtime, reverse=True)
    latest = all_md_files[0]
    print(f"[Knowledge] ✅ Latest file: {os.path.basename(latest)}")
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
        print("[Groq] ❌ No API key, using template fallback")
        return generate_template_article(title_zh, body_zh)

    try:
        from groq import Groq
    except ImportError:
        print("[Groq] ❌ groq package not installed, using template fallback")
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

def validate_config():
    """Validate all required configuration before attempting to publish."""
    print("\n[Config] Validating configuration...")
    errors = []

    if not SUBSTACK_EMAIL:
        errors.append("SUBSTACK_EMAIL not set")
    else:
        print(f"[Config] ✅ SUBSTACK_EMAIL: {SUBSTACK_EMAIL}")

    if not BREVO_API_KEY:
        errors.append("BREVO_API_KEY not set")
    else:
        print(f"[Config] ✅ BREVO_API_KEY: ...{BREVO_API_KEY[-4:]}")

    if not PUBLICATION_SLUG:
        errors.append("PUBLICATION_SLUG not set")
    else:
        publish_email = f"post+{PUBLICATION_SLUG}@substack.com"
        print(f"[Config] ✅ Publish email: {publish_email}")

    if errors:
        print(f"\n[Config] ❌ Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("[Config] ✅ All configuration valid!")
    return True


def publish_via_smtp(title, article_body):
    """Fallback: Send via SMTP (Gmail)."""
    print("\n[SMTP] Attempting to send via Gmail SMTP...")
    
    if not SUBSTACK_PASSWORD:
        print("[SMTP] ❌ SUBSTACK_PASSWORD not set, cannot use SMTP fallback")
        return False

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
    except ImportError as e:
        print(f"[SMTP] ❌ Missing email modules: {e}")
        return False

    publish_email = f"post+{PUBLICATION_SLUG}@substack.com"
    sender_email = SUBSTACK_EMAIL

    print(f"[SMTP] From: {sender_email}")
    print(f"[SMTP] To: {publish_email}")
    print(f"[SMTP] Subject: {title}")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = title
    msg['From'] = sender_email
    msg['To'] = publish_email

    text_part = MIMEText(article_body, 'plain', 'utf-8')
    msg.attach(text_part)

    # Better HTML formatting
    html_body = article_body.replace('\n\n', '</p><p>').replace('\n', '<br>')
    html_body = f"<html><head><meta charset='utf-8'></head><body><p>{html_body}</p></body></html>"
    html_part = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(html_part)

    try:
        print("[SMTP] Connecting to smtp.gmail.com:587...")
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()
        print("[SMTP] Logging in...")
        server.login(sender_email, SUBSTACK_PASSWORD)
        print("[SMTP] Sending message...")
        server.send_message(msg)
        server.quit()
        print("[SMTP] ✅ Article sent via SMTP successfully!")
        return True
    except Exception as e:
        print(f"[SMTP] ❌ Failed: {e}")
        return False


def publish_to_substack(title, article_body, dry_run=False):
    """Publish to Substack via email (prioritize SMTP over Brevo)."""
    if dry_run:
        print("[Substack] DRY RUN — not publishing")
        print(f"[Substack] Title: {title}")
        print(f"[Substack] Body length: {len(article_body)} chars")
        return True

    print("\n[Substack] Starting publication process...")

    # Validate config
    if not validate_config():
        print("[Substack] ❌ Configuration invalid, aborting")
        return False

    # Try SMTP first (more reliable, no sender verification needed)
    print("\n[Substack] 📧 Attempting SMTP (Gmail) first...")
    if publish_via_smtp(title, article_body):
        return True

    # Fallback to Brevo API
    print("\n[Substack] 📧 SMTP failed, trying Brevo API...")
    import requests

    publish_email = f"post+{PUBLICATION_SLUG}@substack.com"
    sender_email = SUBSTACK_EMAIL

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    html_content = article_body.replace('\n\n', '</p><p>').replace('\n', '<br>')
    html_content = f"<html><head><meta charset='utf-8'></head><body><p>{html_content}</p></body></html>"

    payload = {
        "sender": {"name": "BroadFSC Automation", "email": sender_email},
        "to": [{"email": publish_email}],
        "subject": title,
        "htmlContent": html_content,
        "textContent": article_body
    }

    print(f"[Brevo] From: {sender_email}")
    print(f"[Brevo] To: {publish_email}")
    print(f"[Brevo] Subject: {title}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"[Brevo] Response status: {response.status_code}")

        if response.status_code in [200, 201, 202]:
            print("[Brevo] ✅ Article sent via Brevo API successfully!")
            print(f"[Brevo] Check your Substack: https://{PUBLICATION_SLUG}.substack.com")
            return True
        else:
            print(f"[Brevo] ❌ Brevo API failed: {response.status_code}")
            print(f"[Brevo] Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"[Brevo] ❌ Brevo API error: {e}")
        return False


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
    print("Substack Auto-Post: Daily Article Generator (Fixed Version)")
    print("=" * 60)
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"CI Mode: {IS_CI}")

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

    # Save article locally (ALWAYS, as backup)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    output_file = f"substack_draft_{date_str}.md"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {article_title}\n\n")
            f.write(article)
        print(f"\n[Backup] ✅ Article saved to: {output_file}")
    except Exception as e:
        print(f"\n[Backup] ❌ Failed to save locally: {e}")

    # Step 4: Publish to Substack
    if not args.dry_run:
        print("\n[Step 4] Publishing to Substack...")
        success = publish_to_substack(article_title, article, dry_run=args.test)
        if success:
            print("\n✅ Article published successfully!")
            print(f"👉 Check: https://{PUBLICATION_SLUG}.substack.com")
        else:
            print("\n⚠️ Publish failed. Article saved locally.")
            print("👉 Check the logs above for error details.")
            print("👉 Verify your Brevo API key and Substack email settings.")
            sys.exit(1)
    else:
        print("\n[DRY RUN] Skipping publish step.")
        print(f"👉 Article saved at: {output_file}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
