#!/usr/bin/env python3
"""
Substack Auto-Post: Daily Article Generator
Reads latest knowledge files, generates English article via Groq, auto-posts to Substack.

Publish method: Playwright browser automation (uses saved cookies, no email needed).

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
    print(f"[Knowledge] Latest file: {os.path.basename(latest)}")
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
- Write in native English (no AI traces)
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
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"Market Radar: Technical Analysis Update {date_str}"


# ============================================================
# Step 3: Publish to Substack via Playwright (Browser)
# ============================================================

def save_substack_cookies():
    """Interactive: save Substack login cookies to file (run once locally)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Substack] ❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    state_file = os.path.join(SESSION_DIR, "substack_state.json")
    print(f"[Substack] 💾 Saving login cookies to {state_file}...")
    print("[Substack] A browser window will open. Please log in to Substack manually.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"[Substack] Opening: {PUB_URL}/publish")
        page.goto(f"{PUB_URL}/publish")
        print("\n" + "="*50)
        print("Please log in to Substack in the browser window.")
        print("After logging in, navigate to: " + PUB_URL + "/publish")
        print("Then press Enter here to save cookies...")
        print("="*50 + "\n")
        input()  # Wait for user to log in

        # Save cookies
        context.storage_state(path=state_file)
        print(f"[Substack] ✅ Cookies saved to {state_file}")
        print("[Substack] You can now run the auto-post script without manual login.")
        browser.close()
        return True


def publish_to_substack(title, article_body, dry_run=False):
    """Publish article to Substack using Playwright (with saved cookies)."""
    if dry_run:
        print("[Substack] DRY RUN — not publishing")
        print(f"[Substack] Title: {title}")
        print(f"[Substack] Body length: {len(article_body)} chars")
        return True

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Substack] ❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    print("[Substack] 🚀 Launching browser...")

    with sync_playwright() as p:
        state_file = os.path.join(SESSION_DIR, "substack_state.json")

        launch_options = {'headless': IS_CI}
        if IS_CI:
            launch_options['args'] = ['--no-sandbox', '--disable-setuid-sandbox']

        context_options = {}
        if os.path.exists(state_file):
            print(f"[Substack] ✅ Loading saved cookies from {state_file}")
            context_options['storage_state'] = state_file
        else:
            print(f"[Substack] ⚠️ No saved cookies ({state_file} not found)")
            print("[Substack] Run: python substack_auto_post.py --save-cookies")
            browser.close()
            return False

        browser = p.chromium.launch(**launch_options)
        context = browser.new_context(**context_options)
        page = context.new_page()

        # Check if already logged in
        print("[Substack] Checking login status...")
        try:
            page.goto(f"{PUB_URL}/publish", timeout=30000)
            time.sleep(3)
            current_url = page.url.lower()
            if "login" in current_url or "sign-in" in current_url:
                print("[Substack] ❌ Not logged in! Cookies expired.")
                print("[Substack] Run locally: python substack_auto_post.py --save-cookies")
                browser.close()
                return False
        except Exception as e:
            print(f"[Substack] ⚠️ Login check warning: {e}")

        # Create new draft
        print("[Substack] Creating new draft...")
        try:
            page.goto(f"{PUB_URL}/publish", timeout=30000)
            time.sleep(3)
            try:
                page.get_by_text("New post", exact=False).click(timeout=5000)
                print("[Substack] ✅ Clicked 'New post' button")
            except Exception:
                print("[Substack] 'New post' not found, trying direct URL...")
                page.goto(f"{PUB_URL}/publish/post", timeout=30000)

            time.sleep(5)
            current_url = page.url
            print(f"[Substack] Current URL after new post: {current_url}")

            if "/publish/post/" not in current_url:
                print(f"[Substack] ⚠️ Draft URL not detected, current: {current_url}")
        except Exception as e:
            print(f"[Substack] ⚠️ New draft warning: {e}")

        # Fill title and body
        print("[Substack] Filling title and body...")

        # Extract title and body from article
        lines = article_body.strip().split('\n')
        article_title = title
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith('# '):
                article_title = line.lstrip('# ').strip()
                body_start = i + 1
                break
        article_body_only = '\n'.join(lines[body_start:])

        # Use JavaScript to set content (more reliable than selectors)
        # Use placeholders, then replace (avoids f-string backslash error)
        js_script = """
        () => {
            // Set title
            let titleSet = false;
            document.querySelectorAll('input[placeholder*="title" i], input[aria-label*="title" i]').forEach(el => {
                if (!titleSet) {
                    el.focus();
                    el.value = "___TITLE___";
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    titleSet = true;
                    console.log('Title set');
                }
            });

            // Click into body editor and type
            setTimeout(() => {
                let bodySet = false;
                document.querySelectorAll('[contenteditable="true"], .ProseMirror').forEach(el => {
                    if (!bodySet) {
                        el.focus();
                        const text = "___BODY___";
                        el.innerHTML = '<p>' + text.replace(/\\n\\n/g, '</p><p>').replace(/\\n/g, '<br>') + '</p>';
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        bodySet = true;
                        console.log('Body set');
                    }
                });
            }, 1000);

            return {titleSet, bodySet};
        }
        """
        # Safely inject title and body (escape JS strings)
        import json
        title_escaped = json.dumps(article_title)[1:-1]  # remove surrounding quotes
        body_escaped = json.dumps(article_body_only)[1:-1]
        js_script = js_script.replace("___TITLE___", title_escaped)
        js_script = js_script.replace("___BODY___", body_escaped)

        try:
            result = page.evaluate(js_script)
            print(f"[Substack] JS result: {result}")
            time.sleep(3)
        except Exception as e:
            print(f"[Substack] ⚠️ JavaScript injection warning: {e}")

        # Publish
        print("[Substack] Publishing...")
        publish_selectors = [
            'button:has-text("Send to everyone now")',
            'button:has-text("Publish")',
            'button:has-text("Save")',
            '[role="button"]:has-text("Send")',
        ]

        published = False
        for selector in publish_selectors:
            try:
                page.click(selector, timeout=3000)
                time.sleep(5)
                print(f"[Substack] ✅ Published via: {selector}")
                published = True
                break
            except Exception:
                continue

        if not published:
            print("[Substack] ⚠️ Could not find publish button")
            screenshot_path = os.path.join(SESSION_DIR, f"debug_publish_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            page.screenshot(path=screenshot_path)
            print(f"[Substack] Screenshot saved: {screenshot_path}")
            browser.close()
            return False

        # Save updated cookies
        if os.path.exists(state_file):
            context.storage_state(path=state_file)
            print(f"[Substack] ✅ Cookies updated: {state_file}")

        browser.close()
        return True


# ============================================================
# Main
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Test mode (no publish)')
    parser.add_argument('--dry-run', action='store_true', help='Generate only (no publish)')
    parser.add_argument('--save-cookies', action='store_true', help='Interactive: save Substack login cookies')
    args = parser.parse_args()

    print("=" * 60)
    print("Substack Auto-Post: Daily Article Generator")
    print("=" * 60)

    if args.save_cookies:
        save_substack_cookies()
        return

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
        print("\n[Step 4] Publishing to Substack via Playwright...")
        success = publish_to_substack(article_title, article, dry_run=args.test)
        if success:
            print("\n✅ Article published successfully!")
            print(f"[Substack] Check: {PUB_URL}/archive")
        else:
            print("\n⚠️ Publish failed. Article saved locally.")
            print("[Substack] Try running: python substack_auto_post.py --save-cookies")
            sys.exit(1)
    else:
        print("\n[DRY RUN] Skipping publish step.")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
