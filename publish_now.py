#!/usr/bin/env python3
"""
One-shot: Generate today's Substack article from real market data and publish.

Publishing method (in order of preference):
1. Playwright launch_persistent_context (most reliable, for local Windows)
2. Brevo API email (fallback for CI/GitHub Actions)

Usage:
  python publish_now.py                  # Generate + publish (Playwright preferred)
  python publish_now.py --email-only     # Force email/Brevo method only
  python publish_now.py --dry-run        # Generate only, no publish
"""
import os, sys, re, datetime, requests

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
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "msli2233bin+brevo@gmail.com")
SUBSTACK_POST_EMAIL = os.environ.get("SUBSTACK_POST_EMAIL", "post+broadcastmarketintelligence@substack.com")
PUBLICATION_SLUG = "broadcastmarketintelligence"
PUB_URL = "https://{}.substack.com".format(PUBLICATION_SLUG)

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
# Step 2: Generate Article via Groq
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

prompt = """You are a senior market analyst writing for a professional Substack newsletter (BroadFSC Market Intelligence). Based on the REAL market data below from today ({}), write a compelling 800-1200 word English article.

REAL MARKET DATA (from yfinance, {}):
{}

ARTICLE REQUIREMENTS:
1. Title: Start with "Market Radar:" and reference the key story
2. Opening hook: Lead with the most striking data point
3. Structure:
   - Executive Summary (2-3 sentences)
   - The Overbought Tech Problem (analyze SPY/QQQ/XLK RSI above 80)
   - Sector Divergence Signal (XLF RSI ~32 vs XLK RSI ~84)
   - Gold & Bonds: The Safe Haven Play (GLD neutral, TLT weakening)
   - Bitcoin: Cooling Off (RSI around 70)
   - Actionable Takeaways (3-4 bullet points)
4. Use ONLY the real numbers above - do NOT invent any data
5. Reference RSI levels specifically (above 70 = overbought, below 30 = oversold)
6. Professional tone like Bloomberg or Seeking Alpha
7. End with: "For personalized technical analysis of your portfolio, message @BroadInvestBot on Telegram"
8. Final line: "Disclaimer: This is for informational purposes only, not financial advice."

CRITICAL: Do NOT use generic filler. Every paragraph must reference specific data. Write like a real analyst.""".format(date_str, date_str, market_data_for_prompt)

try:
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        max_tokens=2000,
        temperature=0.7,
    )
    article = chat_completion.choices[0].message.content
    print("+ Article generated ({} chars)".format(len(article)))
except Exception as e:
    print("x Groq error: {}".format(e))
    sys.exit(1)

# Extract title
lines = article.strip().split('\n')
title = ""
for line in lines:
    if line.startswith('# '):
        title = line.lstrip('# ').strip()
        break
if not title:
    title = "Market Radar: Technical Analysis Update {}".format(datetime.datetime.now().strftime('%Y-%m-%d'))

print("Title: {}".format(title))

# Save draft locally
date_str_file = datetime.datetime.now().strftime("%Y-%m-%d")
output_file = os.path.join(_script_dir, "substack_draft_{}.md".format(date_str_file))
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# {}\n\n{}".format(title, article))
print("+ Draft saved: {}".format(output_file))

# ============================================================
# Step 3: Parse command line args
# ============================================================
email_only = "--email-only" in sys.argv
dry_run = "--dry-run" in sys.argv

if dry_run:
    print("\n[DRY RUN] Skipping publish step.")
    sys.exit(0)

# ============================================================
# Step 4: Publish (Playwright preferred, Brevo fallback)
# ============================================================
print("\n" + "=" * 60)
print("Step 3: Publishing to Substack...")
print("=" * 60)

# Extract article body (without title header)
body_lines = article.strip().split('\n')
body_start = 0
for i, line in enumerate(body_lines):
    if line.startswith('# '):
        body_start = i + 1
        break
article_body = '\n'.join(body_lines[body_start:]).strip()

published = False

# Method 1: Playwright (launch_persistent_context) — most reliable
if not email_only:
    print("\n[Method 1] Trying Playwright (launch_persistent_context)...")
    try:
        from substack_cookie_publish import publish_article
        published = publish_article(title, article_body)
        if published:
            print("\n+ Published via Playwright!")
        else:
            print("\n- Playwright publishing failed, falling back to email...")
    except ImportError:
        print("  substack_cookie_publish module not available, falling back to email...")
    except Exception as e:
        print("  Playwright error: {}, falling back to email...".format(e))

# Method 2: Brevo API email
if not published:
    print("\n[Method 2] Publishing via Brevo API email...")
    
    if not BREVO_API_KEY:
        print("x No BREVO_API_KEY")
        sys.exit(1)

    # Convert Markdown to HTML
    def markdown_to_simple_html(md_text):
        html = md_text
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
            elif re.match(r'^\d+\. (.+)', line):
                if not in_list:
                    result.append('<ol>')
                    in_list = True
                item = re.sub(r'^\d+\. ', '', line)
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

    html_body = markdown_to_simple_html(article)

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
        "textContent": article,
    }

    print("  From: {}".format(BREVO_SENDER_EMAIL))
    print("  To: {}".format(SUBSTACK_POST_EMAIL))
    print("  Subject: {}".format(title))

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code in (200, 201):
            msg_id = r.json().get("messageId", "unknown")
            print("\n+ Email sent via Brevo API (messageId: {})".format(msg_id))
            published = True
        else:
            print("\nx Brevo API error {}: {}".format(r.status_code, r.text[:500]))
    except Exception as e:
        print("\nx Failed: {}".format(e))

# Final status
print("\n" + "=" * 60)
if published:
    print("+ DONE! Article published to Substack!")
    print("  View at: {}".format(PUB_URL))
else:
    print("x PUBLISHING FAILED. Draft saved locally.")
print("=" * 60)
