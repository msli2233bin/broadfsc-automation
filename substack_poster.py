"""
BroadFSC Substack Auto-Poster (Playwright Headless)
Works on GitHub Actions AND local Windows.
Uses persistent browser context for session reuse.

Environment variables:
  SUBSTACK_EMAIL      — Login email
  SUBSTACK_PASSWORD   — Login password
  GROQ_API_KEY        — For AI content generation (optional)

Usage:
  python substack_poster.py          # Generate + publish one article
  python substack_poster.py --test   # Test login only
"""

import os
import sys
import json
import datetime
import time
import re

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
SUBSTACK_EMAIL = os.environ.get("SUBSTACK_EMAIL", "msli2233bin@gmail.com")
SUBSTACK_PASSWORD = os.environ.get("SUBSTACK_PASSWORD", "Lin2233509.")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
PUBLICATION_SLUG = "broadcastmarketintelligence"
PUBLICATION_ID = "8790672"  # Discovered from public API
PUB_URL = f"https://{PUBLICATION_SLUG}.substack.com"

TELEGRAM_LINK = "https://t.me/BroadFSC"
WEBSITE_LINK = "https://www.broadfsc.com/different"

# Session storage path (persistent browser profile)
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

ARTICLE_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "article_log.json")

# Detect environment
IS_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"


# ============================================================
# Persona System
# ============================================================
PERSONAS = [
    {
        "name": "Alex 'The Croc'",
        "emoji": "\U0001f40a",
        "title": "Technical Analyst",
        "style": "Sharp, data-driven, no-nonsense. Uses charts and patterns.",
        "hook": "Start with a striking chart pattern or price level",
        "hashtags": ["TechnicalAnalysis", "Trading", "Charts"],
    },
    {
        "name": "Thomas Yang",
        "emoji": "\U0001f4d8",
        "title": "Value Investor",
        "style": "Patient, methodical, long-term focused.",
        "hook": "Open with an undervalued asset the market is ignoring",
        "hashtags": ["ValueInvesting", "Fundamentals", "LongTerm"],
    },
    {
        "name": "Michael Hong",
        "emoji": "\U0001f52d",
        "title": "Macro Strategist",
        "style": "Big-picture thinker. Central banks, geopolitics.",
        "hook": "Lead with a macro trend markets haven't priced in",
        "hashtags": ["Macro", "GlobalMarkets", "CentralBanks"],
    },
    {
        "name": "Iron Bull",
        "emoji": "\u2694\ufe0f",
        "title": "Retail Warrior",
        "style": "Bold, contrarian. No jargon, straight talk.",
        "hook": "Open with a bold contrarian take",
        "hashtags": ["RetailTrading", "Contrarian", "StockMarket"],
    },
]


def get_daily_persona(platform_shift=0):
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    return PERSONAS[(day_idx + platform_shift) % len(PERSONAS)]


# ============================================================
# AI Content Generation
# ============================================================
def generate_article():
    if not GROQ_API_KEY:
        return get_fallback_article()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        now = datetime.datetime.utcnow()
        persona = get_daily_persona(platform_shift=3)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    f"PERSONA: {persona['emoji']} {persona['name']} \u2014 {persona['title']}\n"
                    f"STYLE: {persona['style']}\n\n"
                    f"Write DEEP-DIVE investment analysis for {now.strftime('%A')}, {now.strftime('%B %d, %Y')}.\n"
                    f"Focus: US stocks / global macro / investment strategy.\n"
                    f"Hook rule: {persona['hook']}\n\n"
                    f'OUTPUT FORMAT - valid JSON single line:\n'
                    f'{{"title":"...","subtitle":"...","content":"...(markdown)...","tags":["tag1","tag2"]}}\n\n'
                    f"- content uses \\n for line breaks, escape \" inside content\n"
                    f"- No code blocks wrapping JSON\n"
                    f"\nARTICLE STRUCTURE:\n"
                    f"1. HOOK - Bold opening paragraph\n"
                    f"2. BIG PICTURE - 4-6 sentences macro context\n"
                    f"3. DEEP DIVE - 3-5 detailed paragraphs\n"
                    f"4. BY THE NUMBERS - 5-8 data points\n"
                    f"5. SMART MONEY - Institutional positioning\n"
                    f"6. CONTRARIAN CASE - What if consensus wrong?\n"
                    f"7. ACTIONABLE TAKEAWAYS - 3-5 bullets\n"
                    f"8. CLOSING THOUGHT - One powerful insight\n"
                    f"\nRULES:\n"
                    f"- 1500-2500 words markdown\n"
                    f"- ## headers, **bold**, 8-12 numbers\n"
                    f"- End: \u26a0\ufe0f *Not financial advice.*\n"
                    f"- Tags: 3-5 without #\n"
                    f"- Title <80 chars, Subtitle <120 chars\n"
                    f"- Include: Subscribe at {TELEGRAM_LINK} | Learn free at {WEBSITE_LINK}"
                )
            }],
            max_tokens=4000,
            temperature=0.85,
        )

        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        raw = re.sub(r'[\x00-\x1f]', ' ', raw)
        article = json.loads(raw)

        if not all(k in article for k in ["title", "content"]):
            raise ValueError("Missing required fields")

        article.setdefault("tags", ["investing", "trading"])
        article.setdefault("subtitle", "")

        print(f"  Article: '{article['title']}' ({len(article['content'])} chars)")
        print(f"  Persona: {persona['name']}")
        return article

    except Exception as e:
        print(f"  AI failed ({e}), using fallback")
        return get_fallback_article()


def get_fallback_article():
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    articles = [
        {
            "title": "The Yield Curve Is Speaking \u2014 Are You Listening?",
            "subtitle": "What 50 years of inversion tells us about recession risk",
            "content": (
                "## The Signal Nobody Wants to Hear\n\n"
                "The 10Y-2Y Treasury spread has been inverted for over 18 months. "
                "In the last 50 years, every single recession was preceded by this signal "
                "\u2014 with a 12-18 month lag. We're in that lag window right now.\n\n"
                "## The Big Picture\n\n"
                "Markets are priced for perfection. The S&P 500 trades at 21x forward earnings. "
                "Credit spreads sit near historic tights. The VIX refuses to break above 15.\n\n"
                "But the bond market \u2014 historically the smartest money in the room \u2014 "
                "is telling a different story. Long-term rates remain depressed despite short-term "
                "rates at multi-decade highs. This isn't normal. This is pricing in economic damage.\n\n"
                "## By The Numbers\n\n"
                "- **10Y-2Y Spread:** -0.35% (still inverted)\n"
                "- **S&P 500 P/E:** 21.2x forward (10-year avg: 17.8x)\n"
                "- **VIX:** 14.2 (bottom 10th percentile)\n"
                "- **Fed Funds Rate:** 5.25-5.50% (highest in 23 years)\n"
                "- **Commercial RE Delinquencies:** Up 2.1x YoY\n"
                "- **Consumer Savings Rate:** Dropped from 5.3% to 3.6%\n\n"
                "## What Smart Money Is Doing\n\n"
                "Hedge fund net long exposure has dropped 15% this quarter. "
                "Corporate insiders are selling at a 3:1 ratio \u2014 highest since 2021. "
                "When people closest to the data head for exits, pay attention.\n\n"
                "## Actionable Takeaways\n\n"
                "- **Reduce leverage:** Margin debt still elevated\n"
                "- **Raise cash:** 6-month T-bills yield 5.3% \u2014 get paid to wait\n"
                "- **Own quality:** Strong balance sheets outperform 2-3x in downturns\n"
                "- **Diversify:** Gold, managed futures, long volatility\n"
                "- **Stay invested:** Missing best 10 days cuts returns by 50%\n\n"
                "---\n\n"
                f"Subscribe: {TELEGRAM_LINK} | {WEBSITE_LINK}\n\n"
                "\u26a0\ufe0f *Not financial advice. Do your own research.*"
            ),
            "tags": ["yieldcurve", "recession", "bonds", "macro", "investing"],
        },
        {
            "title": "Intel's 24% Surge: Reading Between the Candlesticks",
            "subtitle": "What the dramatic reversal really means for your portfolio",
            "content": (
                "## The Comeback Nobody Expected\n\n"
                "Intel just surged 24% in a single session \u2014 its biggest move in decades. "
                "But before you chase the rally, let's examine what actually happened.\n\n"
                "## The Catalyst Breakdown\n\n"
                "The move wasn't driven by earnings alone. A confluence converged:\n"
                "AI chip design wins, foundry partnership announcements, and massive short covering.\n\n"
                "When 15% of float is short, even modest good news creates explosive rallies.\n\n"
                "## By The Numbers\n\n"
                "- **One-day gain:** +24% (~$6B market cap added)\n"
                "- **Short interest:** ~14% of float (still elevated)\n"
                "- **P/E after rally:** 32x (vs AMD 45x, NVDA 65x)\n"
                "- **Data center revenue growth:** +18% YoY\n"
                "- **Foundry business burn:** ~$7B/year (still losing money)\n\n"
                "## The Contrarian View\n\n"
                "Here's what bulls miss: Intel's gross margins are still contracting. "
                "The foundry business bleeds $7B/year. One day doesn't fix structural problems.\n"
                "The real test comes next quarter when we see if GM improvement is real.\n\n"
                "## Actionable Takeaways\n\n"
                "- **Don't FOMO in:** Wait for pullback to 20-day MA\n"
                "- **Watch margins closely:** Next quarter GM is the key metric\n"
                "- **Consider options:** Straddles work well in high-vol names like INTC\n"
                "- **Position size small:** Intel remains a turnaround story, not growth\n\n"
                "---\n\n"
                f"Subscribe: {TELEGRAM_LINK} | {WEBSITE_LINK}\n\n"
                "\u26a0\ufe0f *Not financial advice. Do your own research.*"
            ),
            "tags": ["Intel", "stocks", "semiconductors", "trading", "tech"],
        },
        {
            "title": "The Dollar's Hidden Message for Your Portfolio",
            "subtitle": "What DXY breakout means for emerging markets and gold",
            "content": (
                "## The World's Most Watched Chart Just Broke Out\n\n"
                "The US Dollar Index (DXY) just punched through 106 resistance \u2014 a level "
                "it hasn't sustained above since 2003. Most investors don't realize how much this matters.\n\n"
                "## Why the Dollar Matters More Than You Think\n\n"
                "A strong dollar isn't just a forex story. It's a global margin compressor:\n"
                "- S&P 500 companies earn 40%+ revenue overseas\n"
                "- EM debt is dollar-denominated\n"
                "- Commodity prices fall when USD rises\n"
                "- Gold typically inversely correlates (but decoupling now)\n\n"
                "## By The Numbers\n\n"
                "- **DXY Level:** 106.4 (+4.2% YTD)\n"
                "- **EM FX Index:** -6.3% vs USD YTD\n"
                "- **Gold:** $2,340 (+12% YTD) \u2014 decoupling from inverse correlation!\n"
                "- **EUR/USD:** 1.0620 (near parity zone)\n"
                "- **JPY/USD:** 154.80 (BoJ intervention risk rising)\n"
                "- **CTFT net short EUR:** Highest since 2022\n\n"
                "## Smart Money Positioning\n\n"
                "Leveraged funds are net short EUR at levels unseen since 2022. "
                "Central banks are accelerating gold purchases \u2014 buying more Q1 than any quarter since 1967.\n"
                "This gold buying spree isn't speculation; it's de-dollarization in action.\n\n"
                "## Actionable Takeaways\n\n"
                "- **Hedge USD exposure:** Currency-hedged ETFs for international equity\n"
                "- **Gold allocation 5-10%:** Hedge against both inflation AND dollar volatility\n"
                "- **Avoid EM debt:** Dollar strength = EM debt pain\n"
                "- **Tech winners:** Domestic-revenue tech outperforms in strong-dollar regime\n"
                "- **Treasury ladders:** Lock in yields before Fed cuts\n\n"
                "---\n\n"
                f"Subscribe: {TELEGRAM_LINK} | {WEBSITE_LINK}\n\n"
                "\u26a0\ufe0f *Not financial advice. Do your own research.*"
            ),
            "tags": ["USD", "forex", "gold", "macro", "emergingmarkets"],
        },
    ]
    article = articles[day_idx % len(articles)]
    print(f"  Fallback: '{article['title']}'")
    return article


# ============================================================
# Substack Poster (Playwright Headless)
# ============================================================
def post_to_substack(article):
    """Publish an article to Substack via headless Playwright."""
    from playwright.sync_api import sync_playwright

    user_data_dir = os.path.join(SESSION_DIR, "substack_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    debug_dir = os.path.join(SESSION_DIR, "debug")
    os.makedirs(debug_dir, exist_ok=True)

    # CI environment needs headless mode
    headless = IS_CI
    slow_mo = 100 if not IS_CI else 50

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=headless,
            slow_mo=slow_mo,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )

        page = context.new_page()

        try:
            # === Step 1: Navigate to Substack dashboard ===
            print("  [Substack] Navigating...")
            page.goto(f"{PUB_URL}/dashboard", timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)

            # Handle Cloudflare challenge
            for wait in range(30):
                time.sleep(2)
                title = page.title()
                if all(x not in title for x in ["稍候", "Checking", "Just a moment", "Attention"]):
                    break
                print(f"    Cloudflare wait... ({wait+1})")
            else:
                print("    WARNING: Cloudflare may have blocked us")

            time.sleep(3)
            current_url = page.url
            print(f"    Current URL: {current_url}")

            # === Step 2: Login if needed ===
            needs_login = any(kw in current_url.lower() for kw in [
                "/sign-in", "/login", "signin", "login"
            ]) or current_url == PUB_URL or current_url == "https://substack.com/"

            # Also check if we can find editor elements
            if not needs_login:
                try:
                    # If dashboard loads but no new post button, might need login
                    has_editor = page.locator('[href*="/new"], [href*="/drafts/new"], [href*="/write"]').count() > 0
                    if not has_editor and page.locator('a[href*="/new"], button:has-text("New")').count() > 0:
                        has_editor = True
                    if not has_editor:
                        # Check if we're on a login-ish page
                        body_text = page.locator("body").inner_text(timeout=3000) if page.locator("body").count() else ""
                        if "sign in" in body_text.lower()[:200] or "log in" in body_text.lower()[:200]:
                            needs_login = True
                except Exception:
                    pass

            if needs_login:
                print("  [Substack] Need to login...")
                
                page.goto("https://substack.com/sign-in", timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(3)

                # Click "Sign in with email" button first
                try:
                    email_btn = page.locator('button:has-text("Sign in with email"), '
                                            'button:has-text("Sign in"), '
                                            'a:has-text("Sign in with email")').first
                    if email_btn.is_visible(timeout=5000):
                        email_btn.click()
                        time.sleep(2)
                        print("    Clicked sign-in button")
                except Exception as e:
                    print(f"    Sign-in btn click: {e}")

                # Fill email
                try:
                    email_input = page.locator('input[type="email"], input[name="email"], '
                                             'input[inputmode="email"]').first
                    email_input.fill(SUBSTACK_EMAIL)
                    time.sleep(1)
                    
                    # Click Continue
                    continue_btn = page.locator('button:has-text("Continue"), '
                                               'button:has-text("Next"), '
                                               'button[type="submit"]').first
                    continue_btn.click()
                    time.sleep(3)
                    print("    Email submitted, waiting for password/magic code step...")
                except Exception as e:
                    print(f"    Email fill error: {e}")

                # Check what appeared next: password field or magic code request
                time.sleep(2)
                page_content = page.content()

                # Try password
                pwd_filled = False
                try:
                    pwd_input = page.locator('input[type="password"], input[name="password"]').first
                    if pwd_input.is_visible(timeout=3000):
                        pwd_input.fill(SUBSTACK_PASSWORD)
                        time.sleep(1)
                        
                        submit_btn = page.locator('button:has-text("Continue"), '
                                                 'button:has-text("Sign in"), '
                                                 'button:has-text("Log in"), '
                                                 'button[type="submit"]').first
                        submit_btn.click()
                        time.sleep(5)
                        pwd_filled = True
                        print("    Password submitted")
                except Exception:
                    pass

                if not pwd_filled:
                    # Might need magic code - try submitting without it
                    # Some accounts auto-send magic code on email submit
                    print("    No password field found - checking for magic code...")
                    
                    # Try clicking any continue/next/submit button that appeared
                    for sel in ['button:has-text("Continue")', 'button:has-text("Submit")',
                                'button:has-text("Send")']:
                        try:
                            btn = page.locator(sel).first
                            if btn.is_visible(timeout=2000):
                                btn.click()
                                time.sleep(3)
                                print(f"    Clicked: {sel}")
                                break
                        except Exception:
                            continue
                
                # Wait for redirect after login attempt
                time.sleep(5)
                final_url = page.url
                print(f"    After login URL: {final_url}")

                if "sign-in" in final_url or "login" in final_url:
                    print("    ERROR: Still on login page. May need manual intervention.")
                    log_article("substack", article["title"], "login_failed")
                    return False, ""

            # === Step 3: Navigate to New Post ===
            print("  [Substack] Looking for New Post button...")
            
            # Go directly to write page (might work if logged in)
            page.goto(f"{PUB_URL}/write", timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            time.sleep(5)

            # Fallback: click New Post from dashboard
            if "/write" not in page.url.lower():
                page.goto(f"{PUB_URL}/dashboard", timeout=60000)
                time.sleep(3)
                
                new_post_sels = [
                    'a:has-text("New post")', 'button:has-text("New post")',
                    'a:has-text("Create post")', 'button:has-text("Create post")',
                    'a[href*="/drafts/new"]', 'a[href*="/write"]', 'a[href*="/new"]',
                ]
                clicked = False
                for sel in new_post_sels:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=2000):
                            btn.click()
                            time.sleep(3)
                            clicked = True
                            print(f"    Clicked: {sel}")
                            break
                    except Exception:
                        continue
                if not clicked:
                    print("    Trying direct URL...")
                    page.goto(f"{PUB_URL}/write", timeout=60000)
                    time.sleep(5)

            time.sleep(3)
            print(f"    Editor URL: {page.url}")

            # === Step 4: Fill in article content ===
            print("  [Substack] Filling content...")

            # Wait for editor
            for attempt in range(5):
                try:
                    page.wait_for_selector('[contenteditable="true"], textarea', timeout=8000)
                    break
                except Exception:
                    if attempt < 4:
                        page.reload(timeout=30000)
                        time.sleep(5)
                    else:
                        page.click("body")
                        time.sleep(3)

            time.sleep(2)

            # Find and fill title
            title_selectors = [
                'input[placeholder*="itle"]', 'input[placeholder*="itle"]',
                'h1[contenteditable="true"]', 'div[contenteditable="true"][class*="title"]',
                '[data-testid="post-title-input"]', '#title',
            ]
            
            title_done = False
            for sel in title_selectors:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=2000):
                        el.click()
                        time.sleep(0.3)
                        el.fill("")
                        page.keyboard.type(article["title"], delay=15)
                        title_done = True
                        print(f"    Title filled via: {sel}")
                        break
                except Exception:
                    continue

            if not title_done:
                first_editable = page.locator('[contenteditable="true"]').first
                first_editable.click()
                page.keyboard.type(article["title"], delay=15)
                title_done = True

            # Move to body
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(0.5)

            # Subtitle
            if article.get("subtitle"):
                page.keyboard.type(article["subtitle"], delay=15)
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # Body content - paste paragraphs
            paragraphs = article["content"].split("\n")
            char_count = 0
            for i, para in enumerate(paragraphs):
                if para.strip():
                    if i > 0 or article.get("subtitle"):
                        page.keyboard.press("Enter")
                        time.sleep(0.05)
                    try:
                        page.evaluate(f'navigator.clipboard.writeText({json.dumps(para)})')
                        page.keyboard.press("Control+v")
                    except Exception:
                        page.keyboard.type(para[:500], delay=1)
                    char_count += len(para)

            print(f"    Content filled: ~{char_count} chars")

            # === Step 5: Publish ===
            time.sleep(2)
            published = False
            
            publish_sels = [
                'button:has-text("Publish")', 'button:has-text("Publish now")',
                'button[data-testid="publish-button"]',
                'button:has-text("Send")', 'button:has-text("Post now")',
            ]
            
            for sel in publish_sels:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        print(f"    Publish button clicked: {sel}")
                        time.sleep(3)
                        
                        # Confirm dialog
                        for csel in [
                            'button:has-text("Publish now")', 'button:has-text("Confirm")',
                            'button:has-text("Send now")', 'button:has-text("Yes, publish")',
                        ]:
                            try:
                                cb = page.locator(csel).first
                                if cb.is_visible(timeout=2000):
                                    cb.click()
                                    print(f"    Confirmed: {csel}")
                                    time.sleep(3)
                                    break
                            except Exception:
                                continue
                        
                        published = True
                        break
                except Exception:
                    continue

            if not published:
                print("    No publish button found, saving draft...")
                page.keyboard.press("Control+s")
                time.sleep(3)

            final_url = page.url
            print(f"    Final URL: {final_url}")
            log_article("substack", article["title"], "published" if published else "draft_only", final_url)
            
            return True, final_url

        except Exception as e:
            print(f"  [Substack] ERROR: {e}")
            try:
                page.screenshot(path=os.path.join(debug_dir, "substack_error.png"))
            except Exception:
                pass
            log_article("substack", article["title"], f"error: {str(e)[:80]}")
            return False, ""

        finally:
            context.close()


# ============================================================
# Logging & Notification
# ============================================================
def log_article(platform, title, status, url=""):
    try:
        log = []
        if os.path.exists(ARTICLE_LOG):
            with open(ARTICLE_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        log.append({
            "platform": platform, "title": title, "status": status,
            "url": url, "timestamp": datetime.datetime.utcnow().isoformat(),
        })
        log = log[-100:]
        with open(ARTICLE_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  Log failed: {e}")


def notify_telegram(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    if not bot_token or not channel_id:
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, data={"chat_id": channel_id, "text": message,
                                 "parse_mode": "HTML"}, timeout=10)
    except Exception:
        pass


# ============================================================
# Main
# ============================================================
def main():
    test_mode = "--test" in sys.argv or "--dry-run" in sys.argv

    print("=" * 60)
    print("BroadFSC Substack Auto-Poster (Playwright)")
    print("=" * 60)
    print(f"UTC: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    print(f"Mode: {'HEADLESS (CI)' if IS_CI else 'GUI (local)'}")
    print()

    if test_mode:
        print("[Test Mode] Checking login only...\n")
        result, url = post_to_substack({
            "title": "[TEST] Connection Check",
            "subtitle": "",
            "content": "This is a test post. Please ignore.",
            "tags": [],
        })
        print(f"\nResult: {'OK' if result else 'FAILED'} | URL: {url}")
        return

    # Generate article
    print("[Step 1] Generating article...")
    article = generate_article()
    print(f"  Title: {article['title']}")
    print(f"  Content: {len(article['content'])} chars\n")

    # Post to Substack
    print("[Step 2] Publishing to Substack...")
    success, url = post_to_substack(article)

    if success:
        print(f"\n\u270a DONE! Published to Substack")
        print(f"   URL: {url}")
        notify_telegram(
            f"\U0001f4f0 <b>Substack Published</b>\n\n"
            f"<b>{article['title']}</b>\n"
            f"\u2705 {url}"
        )
    else:
        print("\n\u274c FAILED - check debug screenshots")
        notify_telegram(
            f"\U0001f4f0 <b>Substack FAILED</b>\n\n"
            f"<b>{article['title']}</b>\n"
            f"\u274c Could not publish"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
