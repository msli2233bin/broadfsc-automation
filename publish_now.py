#!/usr/bin/env python3
"""
One-shot: Generate today's Substack article from real market data and publish.

Publishing method: Substack REST API
- Uses Playwright to get session cookies (substack.lli JWT + substack.sid)
- Creates draft via POST /api/v1/drafts (with Markdown in draft_body)
- Publishes via POST /api/v1/drafts/{id}/publish

Usage:
  python publish_now.py                  # Generate + publish
  python publish_now.py --dry-run        # Generate only, no publish
"""
import os, sys, re, datetime, requests, json, base64, time

# Load .env manually
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k not in os.environ:
                os.environ[k] = v

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
PUBLICATION_SLUG = "broadcastmarketintelligence"
PUB_URL = "https://{}.substack.com".format(PUBLICATION_SLUG)
BROWSER_SESSION_DIR = os.path.join(_script_dir, ".browser_sessions", "substack_profile")

# ============================================================
# Step 1: Fetch Real Market Data
# ============================================================
print("=" * 60)
print("Step 1: Fetching real market data from yfinance...")
print("=" * 60)

import yfinance as yf

tickers = {
    'SPY': 'S&P 500',
    'QQQ': 'Nasdaq 100',
    'IWM': 'Russell 2000',
    'XLK': 'Tech Sector',
    'XLF': 'Financial Sector',
    'GLD': 'Gold',
    'TLT': '20Y Treasury',
    'BTC-USD': 'Bitcoin'
}

market_lines = []
market_data_for_prompt = ""

for sym, name in tickers.items():
    try:
        t = yf.Ticker(sym)
        h = t.history(period='5d')
        if len(h) >= 2:
            latest = h.iloc[-1]
            prev = h.iloc[-2]
            change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
            # RSI 14
            h14 = t.history(period='1mo')
            rsi_val = "N/A"
            if len(h14) >= 14:
                delta = h14['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
                rs = gain / loss if loss != 0 else 100
                rsi_val = "{:.1f}".format(100 - (100 / (1 + rs)))
            
            line = "{} ({}): {:.2f} | Change: {:+.2f}% | RSI(14): {}".format(sym, name, latest['Close'], change, rsi_val)
            market_lines.append(line)
            print("  + {}".format(line))
    except Exception as e:
        print("  x {}: {}".format(sym, e))

market_data_for_prompt = "\n".join(market_lines)
print("\nFetched {} tickers".format(len(market_lines)))

# ============================================================
# Step 2: Generate Article via Groq (in Markdown format)
# ============================================================
print("\n" + "=" * 60)
print("Step 2: Generating article via Groq...")
print("=" * 60)

if not GROQ_API_KEY:
    print("x No GROQ_API_KEY")
    sys.exit(1)

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

date_str = datetime.datetime.now().strftime("%B %d, %Y")

prompt = """You are a senior market analyst writing for a professional Substack newsletter (BroadFSC Market Intelligence). Based on the REAL market data below from today ({}), write a compelling 800-1200 word article in MARKDOWN format.

REAL MARKET DATA (from yfinance, {}):
{}

ARTICLE REQUIREMENTS:
1. Title: Start with "Market Radar:" and reference the key story
2. Opening hook: Lead with the most striking data point
3. Structure:
   - Executive Summary (2-3 sentences)
   - The Overbought Tech Problem (analyze SPY/QQQ/XLK RSI)
   - Sector Divergence Signal (XLF vs XLK)
   - Gold & Bonds: The Safe Haven Play (GLD, TLT)
   - Bitcoin: Cooling Off (RSI analysis)
   - Actionable Takeaways (3-4 bullet points using - syntax)
4. Use ONLY the real numbers above - do NOT invent any data
5. RSI INTERPRETATION RULES (CRITICAL - follow exactly):
   - RSI > 70: overbought / extreme overbought
   - RSI 60-70: approaching overbought / elevated
   - RSI 40-60: NEUTRAL (never call this oversold or overbought)
   - RSI 30-40: approaching oversold
   - RSI < 30: oversold
   - DOUBLE-CHECK: RSI 57.8 = NEUTRAL, RSI 46.4 = NEUTRAL
6. Professional tone like Bloomberg or Seeking Alpha
7. End with: For personalized technical analysis of your portfolio, message [@BroadInvestBot](https://t.me/BroadInvestBot) on Telegram
8. Final line: *Disclaimer: This is for informational purposes only, not financial advice.*

CRITICAL FORMATTING RULES:
- Use ### for section headings (NOT ## or #)
- Use **bold** for emphasis
- Use - for bullet points
- Use [text](url) for links
- Write in pure MARKDOWN - do NOT use any HTML tags
- Do NOT wrap the title in # heading - the title will be set separately

CRITICAL: Do NOT use generic filler. Every paragraph must reference specific data. Write like a real analyst.""".format(date_str, date_str, market_data_for_prompt)

try:
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        max_tokens=2000,
        temperature=0.7,
    )
    article_md = chat_completion.choices[0].message.content
    print("+ Article generated ({} chars)".format(len(article_md)))
except Exception as e:
    print("x Groq error: {}".format(e))
    sys.exit(1)

# Extract title from first line if it starts with #
lines = article_md.strip().split('\n')
title = ""
body_start = 0
for i, line in enumerate(lines):
    if line.startswith('# '):
        title = line.lstrip('# ').strip()
        body_start = i + 1
        break
if not title:
    # If no heading found, use first line as title
    title = lines[0].strip().lstrip('# ').strip()
    body_start = 1

# Clean title - remove markdown formatting
title = re.sub(r'\*+', '', title).strip()

# Add date to title to avoid slug collisions
date_str_title = datetime.datetime.now().strftime("%b %d, %Y")
if date_str_title not in title:
    title = "{} - {}".format(title.rstrip('.'), date_str_title)

# Article body (everything after title)
article_body = '\n'.join(lines[body_start:]).strip()

# ============================================================
# Step 2b: Validate & fix RSI misinterpretations
# ============================================================
def fix_rsi_errors(text):
    """Auto-correct common RSI misinterpretations by the AI."""
    import re
    
    # Extract all RSI values mentioned in the text
    rsi_pattern = r'RSI\s*\(?14\)?\s*(?:at|of|=|:)\s*(\d+\.?\d*)'
    matches = re.finditer(rsi_pattern, text, re.IGNORECASE)
    
    corrections = []
    for m in matches:
        val = float(m.group(1))
        # Determine correct interpretation
        if val > 70:
            correct = "overbought"
        elif val >= 60:
            correct = "elevated / approaching overbought"
        elif val >= 40:
            correct = "neutral"
        elif val >= 30:
            correct = "approaching oversold"
        else:
            correct = "oversold"
        
        # Check if text nearby has wrong description
        start = max(0, m.start() - 100)
        end = min(len(text), m.end() + 150)
        context = text[start:end].lower()
        
        # Flag common wrong descriptions
        wrong_patterns = {
            'oversold': val >= 40,      # RSI >= 40 should never be called oversold
            'overbought': val <= 60,    # RSI <= 60 should never be called overbought
        }
        for word, is_wrong in wrong_patterns.items():
            if is_wrong and word in context:
                corrections.append("  ! RSI {:.1f} incorrectly described as '{}' -> should be '{}'".format(val, word, correct))
    
    if corrections:
        print("  ! RSI corrections found:")
        for c in corrections:
            print(c)
        
        # Apply fixes: replace wrong descriptions near RSI values
        # Fix 1: "RSI at X.X ... oversold" where X.X >= 40
        text = re.sub(
            r'(RSI\s*\(?14\)?\s*(?:at|of|=|:)\s*(?:[4-9]\d|100)\.?\d*.*?)(oversold)',
            r'\1neutral',
            text, flags=re.IGNORECASE
        )
        # Fix 2: "RSI at X.X ... overbought" where X.X <= 60
        text = re.sub(
            r'(RSI\s*\(?14\)?\s*(?:at|of|=|:)\s*(?:[0-5]\d)\.?\d*.*?)(overbought)',
            r'\1neutral',
            text, flags=re.IGNORECASE
        )
        print("  + Auto-corrected RSI descriptions")
    else:
        print("  + RSI values look correct")
    
    return text

article_body = fix_rsi_errors(article_body)

print("Title: {}".format(title))

# Save draft locally
date_str_file = datetime.datetime.now().strftime("%Y-%m-%d")
output_file = os.path.join(_script_dir, "substack_draft_{}.md".format(date_str_file))
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# {}\n\n{}".format(title, article_body))
print("+ Draft saved: {}".format(output_file))

# ============================================================
# Step 3: Parse command line args
# ============================================================
dry_run = "--dry-run" in sys.argv

if dry_run:
    print("\n[DRY RUN] Skipping publish step.")
    sys.exit(0)

# ============================================================
# Step 4: Publish via Substack REST API
# ============================================================
print("\n" + "=" * 60)
print("Step 3: Publishing to Substack via REST API...")
print("=" * 60)


def publish_via_browser(title, markdown_body):
    """Publish to Substack entirely via browser fetch (avoids proxy/cookie issues with requests)."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        # Use headless=False — headless mode has proxy/DNS issues on this server
        browser = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_SESSION_DIR,
            headless=False,
            viewport={'width': 1280, 'height': 900}
        )
        page = browser.new_page()
        
        # Navigate to the publication dashboard (loads cookies on correct domain)
        print("  + Opening Substack dashboard...")
        page.goto('https://broadcastmarketintelligence.substack.com/publish/posts', timeout=60000)
        time.sleep(3)
        
        current_url = page.url
        if 'sign-in' in current_url or 'login' in current_url:
            print("  x Session expired! Need to re-login manually.")
            browser.close()
            return False
        
        # Extract user_id from JWT cookie
        user_id = page.evaluate('''() => {
            const cookies = document.cookie;
            const lli = cookies.split(';').find(c => c.trim().startsWith('substack.lli='));
            if (!lli) return '';
            const token = lli.split('=')[1];
            const parts = token.split('.');
            try {
                const payload = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'));
                const decoded = JSON.parse(payload);
                return String(decoded.userId);
            } catch(e) { return ''; }
        }''')
        
        if not user_id:
            print("  x Could not extract user_id from session")
            browser.close()
            return False
        
        print("  + Session OK (user_id: {})".format(user_id))
        
        # Create draft via browser fetch (uses browser's cookies + proxy)
        print("  + Creating draft...")
        draft_result = page.evaluate('''async (params) => {
            try {
                const resp = await fetch('/api/v1/drafts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        draft_title: params.title,
                        draft_body: params.body,
                        draft_bylines: [{id: parseInt(params.userId), is_guest: false}],
                        type: 'newsletter'
                    })
                });
                if (!resp.ok) return {error: resp.status, text: await resp.text()};
                return await resp.json();
            } catch(e) { return {error: e.message}; }
        }''', {'title': title, 'body': markdown_body, 'userId': user_id})
        
        draft_id = draft_result.get('id', '') if isinstance(draft_result, dict) else ''
        
        if not draft_id:
            print("  x Draft creation failed: {}".format(json.dumps(draft_result, default=str)[:300]))
            browser.close()
            return False
        
        print("  + Draft created (id: {})".format(draft_id))
        
        # Publish the draft via browser fetch
        print("  + Publishing...")
        pub_result = page.evaluate('''async (params) => {
            try {
                const resp = await fetch('/api/v1/drafts/' + params.draftId + '/publish', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({audience: 'everyone'})
                });
                if (!resp.ok) return {error: resp.status, text: await resp.text()};
                return await resp.json();
            } catch(e) { return {error: e.message}; }
        }''', {'draftId': str(draft_id)})
        
        browser.close()
        
        if isinstance(pub_result, dict) and pub_result.get('error'):
            print("  x Publish failed: {}".format(json.dumps(pub_result, default=str)[:300]))
            return False
        
        slug = pub_result.get('slug', '') if isinstance(pub_result, dict) else ''
        post_url = 'https://broadcastmarketintelligence.substack.com/p/{}'.format(slug) if slug else PUB_URL
        print("  + Published! URL: {}".format(post_url))
        return True


# Execute publishing
published = False

if '--dry-run' in sys.argv:
    print("\n[DRY RUN] Skipping publish step.")
else:
    try:
        published = publish_via_browser(title, article_body)
    except ImportError:
        print("  x Playwright not installed. Run: pip install playwright && playwright install chromium")
    except Exception as e:
        print("  x Substack publish error: {}".format(e))

# Final status
print("\n" + "=" * 60)
if published:
    print("+ DONE! Article published to Substack!")
    print("  View at: {}".format(PUB_URL))
else:
    print("x PUBLISHING FAILED. Draft saved locally at: {}".format(output_file))
print("=" * 60)
