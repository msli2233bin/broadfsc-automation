"""
BroadFSC Medium & Substack Auto-Poster (Browser Automation)
Uses Playwright to publish long-form articles to Medium and Substack.

Both platforms locked their APIs:
- Medium: No new Integration Tokens since Jan 2025
- Substack: No public API, no Email Publishing for new accounts

This script runs LOCALLY on Windows (not GitHub Actions).
Requires: playwright (pip install playwright && playwright install chromium)

Environment variables:
  MEDIUM_EMAIL     — Medium login email
  MEDIUM_PASSWORD  — Medium login password
  SUBSTACK_EMAIL   — Substack login email
  SUBSTACK_PASSWORD— Substack login password
  GROQ_API_KEY     — For AI content generation
"""

import os
import sys
import datetime
import json
import time
import hashlib
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
MEDIUM_EMAIL = os.environ.get("MEDIUM_EMAIL", "msli2233bin@gmail.com")
MEDIUM_PASSWORD = os.environ.get("MEDIUM_PASSWORD", "Lin2233509.")
SUBSTACK_EMAIL = os.environ.get("SUBSTACK_EMAIL", "msli2233bin@gmail.com")
SUBSTACK_PASSWORD = os.environ.get("SUBSTACK_PASSWORD", "Lin2233509.")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Substack publication URL (update after first publish to get the real slug)
SUBSTACK_PUB_URL = os.environ.get("SUBSTACK_PUB_URL", "https://broadcasts.substack.com")

TELEGRAM_LINK = "https://t.me/BroadFSC"
WEBSITE_LINK = "https://www.broadfsc.com/different"

# Session storage path (persist login cookies between runs)
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

# Article output log
ARTICLE_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "article_log.json")


# ============================================================
# Persona System (same as social_poster.py)
# ============================================================
PERSONAS = [
    {
        "name": "Alex 'The Croc'",
        "emoji": "🐊",
        "title": "Technical Analyst",
        "style": "Sharp, data-driven, no-nonsense. Uses charts and patterns. Speaks in probabilities, not certainties.",
        "hook": "Start with a striking chart pattern or price level that challenges conventional wisdom",
        "hashtags": ["#TechnicalAnalysis", "#Trading", "#Charts"],
    },
    {
        "name": "Thomas Yang",
        "emoji": "📘",
        "title": "Value Investor",
        "style": "Patient, methodical, long-term focused. References fundamentals, moats, and margin of safety.",
        "hook": "Open with an undervalued asset or a fundamental disconnect the market is ignoring",
        "hashtags": ["#ValueInvesting", "#Fundamentals", "#LongTerm"],
    },
    {
        "name": "Michael Hong",
        "emoji": "🔭",
        "title": "Macro Strategist",
        "style": "Big-picture thinker, connects global dots. Talks central banks, geopolitics, and capital flows.",
        "hook": "Lead with a global macro trend or central bank signal that markets haven't priced in yet",
        "hashtags": ["#Macro", "#GlobalMarkets", "#CentralBanks"],
    },
    {
        "name": "Iron Bull",
        "emoji": "⚔️",
        "title": "Retail Warrior",
        "style": "Bold, contrarian, speaks from the trenches. No jargon, straight talk.",
        "hook": "Open with a bold contrarian take or a retail-level insight that Wall Street dismisses",
        "hashtags": ["#RetailTrading", "#Contrarian", "#StockMarket"],
    },
]


def get_daily_persona(platform_shift=0):
    """Get today's persona, with per-platform offset so they differ on the same day."""
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    idx = (day_idx + platform_shift) % len(PERSONAS)
    return PERSONAS[idx]


# ============================================================
# AI Content Generation — Long-form Article
# ============================================================
def generate_article():
    """Generate a long-form investment analysis article (1500-2500 words).

    Returns dict with: title, subtitle, content (markdown), tags
    """
    if not GROQ_API_KEY:
        return get_fallback_article()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        date_str = now.strftime("%B %d, %Y")

        persona = get_daily_persona(platform_shift=3)
        tags_str = ", ".join(persona["hashtags"])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    f"PERSONA: {persona['emoji']} {persona['name']} — {persona['title']}\n"
                    f"STYLE: {persona['style']}\n\n"
                    f"Write a DEEP-DIVE investment analysis article for {day}, {date_str}.\n"
                    f"Focus on US stocks, global macro, or investment strategy.\n\n"
                    f"Hook rule: {persona['hook']}\n\n"
                    f"OUTPUT FORMAT — return EXACTLY this JSON structure on a SINGLE LINE:\n"
                    f'{{"title": "...", "subtitle": "...", "content": "...(escaped markdown)...", "tags": ["tag1", "tag2", "tag3"]}}\n\n'
                    f"CRITICAL JSON RULES:\n"
                    f"- The entire response must be valid JSON on one line\n"
                    f"- In the content field, use \\\\n for line breaks (not actual newlines)\n"
                    f"- Escape all double quotes inside content with \\\\\n"
                    f"- Do NOT wrap in code blocks\n\n"
                    f"ARTICLE STRUCTURE (follow this exactly):\n"
                    f"1. **HOOK** — A bold opening paragraph that stops the scroll\n"
                    f"2. **THE BIG PICTURE** — 4-6 sentences of macro context\n"
                    f"3. **DEEP DIVE** — 3-5 detailed paragraphs analyzing the key theme\n"
                    f"4. **BY THE NUMBERS** — A section with 5-8 specific data points with context\n"
                    f"5. **WHAT SMART MONEY IS DOING** — Institutional positioning and flow data\n"
                    f"6. **THE CONTRARIAN CASE** — What if the consensus is wrong?\n"
                    f"7. **ACTIONABLE TAKEAWAYS** — 3-5 bullet points readers can act on\n"
                    f"8. **CLOSING THOUGHT** — One powerful final insight\n\n"
                    f"RULES:\n"
                    f"- Article body: 1500-2500 words in markdown format\n"
                    f"- Use ## for section headers, **bold** for emphasis\n"
                    f"- Include 8-12 specific numbers (prices, yields, percentages, data points)\n"
                    f"- Stay 100% in character as {persona['name']}\n"
                    f"- End with: ⚠️ *Not financial advice. Always do your own research.*\n"
                    f"- Tags: 3-5 relevant tags without # symbol\n"
                    f"- Title: Under 80 characters, compelling\n"
                    f"- Subtitle: Under 120 characters, expands on the title\n"
                    f"- Do NOT promise returns or guarantee outcomes\n"
                    f"- Include naturally: Subscribe at {TELEGRAM_LINK} | Learn free at {WEBSITE_LINK}"
                )
            }],
            max_tokens=4000,
            temperature=0.85
        )

        raw = response.choices[0].message.content.strip()

        # Try to parse JSON from the response
        # Sometimes the model wraps JSON in ```json ... ``` blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        # Clean up control characters that break JSON parsing
        import re
        raw = re.sub(r'[\x00-\x1f]', ' ', raw)

        article = json.loads(raw)

        # Validate required fields
        if not all(k in article for k in ["title", "content"]):
            raise ValueError("Missing required fields in article JSON")

        # Ensure tags exist
        if "tags" not in article or not article["tags"]:
            article["tags"] = ["investing", "trading", "stockmarket"]

        # Ensure subtitle
        if "subtitle" not in article:
            article["subtitle"] = ""

        print(f"  Article: '{article['title']}' ({len(article['content'])} chars, {len(article['tags'])} tags)")
        print(f"  Persona: {persona['name']}")
        return article

    except json.JSONDecodeError as e:
        print(f"  AI article JSON parse failed: {e}")
        print(f"  Raw response (first 200): {raw[:200]}")
        return get_fallback_article()
    except Exception as e:
        print(f"  AI article generation failed: {e}")
        return get_fallback_article()


def get_fallback_article():
    """Fallback article when AI is unavailable."""
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    articles = [
        {
            "title": "The Yield Curve Is Speaking — Are You Listening?",
            "subtitle": "What 50 years of inversion data tells us about the next recession",
            "content": (
                "## The Signal Nobody Wants to Hear\n\n"
                "The 10Y-2Y Treasury spread has been inverted for over 18 months. "
                "In the last 50 years, every single recession was preceded by this signal — "
                "with a 12-18 month lag. We're in that lag window right now.\n\n"
                "## The Big Picture\n\n"
                "Markets are priced for perfection. The S&P 500 trades at 21x forward earnings. "
                "Credit spreads sit near historic tights. The VIX refuses to break above 15. "
                "Everything screams 'all clear.'\n\n"
                "But the bond market — historically the smartest money in the room — is telling a different story. "
                "Long-term rates remain depressed despite short-term rates at multi-decade highs. "
                "This isn't normal. This is the bond market pricing in economic damage.\n\n"
                "## By The Numbers\n\n"
                "- **10Y-2Y Spread:** -0.35% (still inverted)\n"
                "- **S&P 500 P/E:** 21.2x forward (10-year avg: 17.8x)\n"
                "- **VIX:** 14.2 (bottom 10th percentile historically)\n"
                "- **Commercial RE Delinquencies:** Up 2.1x year-over-year\n"
                "- **Consumer Savings Rate:** Dropped from 5.3% to 3.6% in 6 months\n"
                "- **Fed Funds Rate:** 5.25-5.50% (highest in 23 years)\n\n"
                "## What Smart Money Is Doing\n\n"
                "Institutional investors aren't waiting for the all-clear. "
                "Hedge fund net long exposure has dropped 15% in the last quarter. "
                "Corporate insiders are selling at a 3:1 ratio — the highest since 2021. "
                "When the people closest to the data are heading for the exits, pay attention.\n\n"
                "## The Contrarian Case\n\n"
                "Here's the twist: maybe this time IS different. AI-driven productivity gains "
                "could offset tighter financial conditions. The labor market remains remarkably resilient. "
                "Consumer spending, while slowing, hasn't collapsed.\n\n"
                "But 'this time is different' are the four most expensive words in investing. "
                "The prudent move isn't to bet on a soft landing — it's to prepare for turbulence "
                "while staying invested.\n\n"
                "## Actionable Takeaways\n\n"
                "- **Reduce leverage:** Margin debt is still elevated — don't add to it\n"
                "- **Raise cash:** 6-month T-bills yield 5.3% — get paid to wait\n"
                "- **Own quality:** Companies with strong balance sheets outperform in downturns by 2-3x\n"
                "- **Diversify:** Add uncorrelated assets (gold, managed futures, long volatility)\n"
                "- **Stay invested:** Missing the 10 best days in a decade cuts returns by 50%\n\n"
                "## Closing Thought\n\n"
                "The yield curve has never lied. It's just a matter of timing. "
                "The question isn't IF a downturn comes — it's whether you'll be ready when it does.\n\n"
                "---\n\n"
                f"Subscribe for daily briefings: {TELEGRAM_LINK}\n"
                f"Learn free: {WEBSITE_LINK}\n\n"
                "⚠️ *Not financial advice. Always do your own research.*"
            ),
            "tags": ["yieldcurve", "recession", "bonds", "investing", "macro"],
        },
        {
            "title": "AI Stocks at All-Time Highs: Brilliance or Bubble?",
            "subtitle": "Separating genuine value from momentum in the AI trade",
            "content": (
                "## The Trillion-Dollar Question\n\n"
                "NVIDIA just crossed $3 trillion in market cap. Microsoft is at 35x earnings. "
                "The Magnificent 7 now represent 30% of the S&P 500 — a concentration level "
                "not seen since the 1970s Nifty Fifty. Is this the dawn of an AI-powered "
                "productivity revolution, or the greatest momentum trap of our generation?\n\n"
                "## The Bull Case Is Real\n\n"
                "Let's give credit where it's due. AI is generating real revenue. "
                "Cloud AI services grew 85% YoY. Enterprise AI adoption jumped from 35% to 65% "
                "in 12 months. This isn't vaporware — companies are paying real money for AI tools "
                "that deliver measurable productivity gains.\n\n"
                "## But Valuations Are Stretched\n\n"
                "The problem isn't the technology — it's the price. NVIDIA trades at 65x trailing earnings. "
                "The last time a dominant chip company traded at these levels was Cisco in 2000. "
                "We all know how that ended.\n\n"
                "## By The Numbers\n\n"
                "- **Magnificent 7 Weight in S&P:** 30.2% (historic high)\n"
                "- **NVIDIA P/E:** 65x trailing, 35x forward\n"
                "- **AI Revenue Growth:** 85% YoY (cloud services)\n"
                "- **Enterprise AI Adoption:** 65% (up from 35%)\n"
                "- **Semiconductor Capex:** $280B globally (up 40%)\n"
                "- **AI ETF Inflows:** $12B in Q1 alone\n\n"
                "## Actionable Takeaways\n\n"
                "- **Trim, don't dump:** Take profits on positions that have 3x+ — you can't go broke locking in gains\n"
                "- **Look downstream:** The real money may be in AI infrastructure, not just chips\n"
                "- **Value exists:** Many non-AI stocks trade at 10-12x earnings with growing dividends\n"
                "- **Set stop losses:** If you're playing momentum, protect your downside\n\n"
                "## Closing Thought\n\n"
                "Every great technological revolution went through a bubble phase. "
                "Railroads. Radio. The Internet. The technology changed the world — "
                "but most early investors lost money. Don't confuse a great technology with a great investment at any price.\n\n"
                "---\n\n"
                f"Subscribe for daily briefings: {TELEGRAM_LINK}\n"
                f"Learn free: {WEBSITE_LINK}\n\n"
                "⚠️ *Not financial advice. Always do your own research.*"
            ),
            "tags": ["AI", "stocks", "NVIDIA", "valuation", "growth"],
        },
    ]
    article = articles[day_idx % len(articles)]
    print(f"  Fallback article: '{article['title']}'")
    return article


# ============================================================
# Article Logging
# ============================================================
def log_article(platform, title, status, url=""):
    """Log article publish attempt for tracking."""
    try:
        log = []
        if os.path.exists(ARTICLE_LOG):
            with open(ARTICLE_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)

        log.append({
            "platform": platform,
            "title": title,
            "status": status,
            "url": url,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        })

        # Keep last 100 entries
        log = log[-100:]

        with open(ARTICLE_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  Log write failed: {e}")


# ============================================================
# Medium — Browser Automation
# ============================================================
def post_medium(article):
    """Publish an article to Medium via browser automation.

    Strategy:
    1. Launch Chromium with persistent context (saves all state including localStorage)
    2. Login to Medium if needed (with full browser state persistence)
    3. Navigate to 'New Story'
    4. Fill in title and content
    5. Publish as draft

    Args:
        article: dict with 'title', 'content', 'tags'

    Returns:
        (success: bool, url: str)
    """
    from playwright.sync_api import sync_playwright

    # Use persistent context to keep all browser state (cookies, localStorage, etc.)
    # This handles Cloudflare challenges much better than saving cookies alone
    user_data_dir = os.path.join(SESSION_DIR, "medium_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    debug_dir = os.path.join(SESSION_DIR, "debug")
    os.makedirs(debug_dir, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=300,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )

        page = context.new_page()

        try:
            # Step 1: Navigate to Medium new story
            print("  [Medium] Navigating to Medium...")
            page.goto("https://medium.com/new-story", timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)

            # Wait for Cloudflare challenge to complete (if any)
            for wait in range(30):
                time.sleep(2)
                title = page.title()
                if "稍候" not in title and "Checking" not in title and "Just a moment" not in title:
                    break
                print(f"  [Medium] Waiting for Cloudflare challenge... ({wait+1})")

            time.sleep(3)

            # Debug: save current URL and screenshot
            current_url = page.url
            print(f"  [Medium] Current URL: {current_url}")
            page.screenshot(path=os.path.join(debug_dir, "medium_step1.png"))

            # Step 2: Check if logged in by looking for the editor
            # If we see contenteditable, we're logged in and on the editor
            editor_visible = False
            try:
                editor_visible = page.locator('div[contenteditable="true"]').first.is_visible(timeout=5000)
            except Exception:
                pass

            if not editor_visible and ("login" in current_url or "signin" in current_url or page.url == "https://medium.com/" or "m/signin" in current_url):
                print("  [Medium] Need to login...")
                if not MEDIUM_EMAIL or not MEDIUM_PASSWORD:
                    print("  [Medium] ERROR: MEDIUM_EMAIL/PASSWORD not set")
                    log_article("medium", article["title"], "failed_no_creds")
                    return False, ""

                # Go to sign-in page
                page.goto("https://medium.com/m/signin", timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(3)
                page.screenshot(path=os.path.join(debug_dir, "medium_login1.png"))
                print(f"  [Medium] Login page URL: {page.url}")

                # Try to find and click "Sign in with email" or Google
                try:
                    # Look for Google sign-in (since email is gmail)
                    google_btn = page.locator('button:has-text("Google"), a:has-text("Google"), div[data-testid*="google"]').first
                    if google_btn.is_visible(timeout=5000):
                        print("  [Medium] Found Google sign-in button, clicking...")
                        google_btn.click()
                        time.sleep(5)

                        # Google OAuth flow
                        # Enter email
                        email_input = page.locator('input[type="email"], input[name="identifier"]').first
                        email_input.fill(MEDIUM_EMAIL)
                        time.sleep(1)

                        # Click Next
                        next_btn = page.locator('button:has-text("Next"), #identifierNext').first
                        next_btn.click()
                        time.sleep(3)

                        # Enter password
                        pwd_input = page.locator('input[type="password"], input[name="password"]').first
                        pwd_input.fill(MEDIUM_PASSWORD)
                        time.sleep(1)

                        # Click Next
                        next_btn2 = page.locator('button:has-text("Next"), #passwordNext').first
                        next_btn2.click()
                        time.sleep(8)

                        page.wait_for_load_state("domcontentloaded", timeout=30000)
                        print(f"  [Medium] After Google OAuth URL: {page.url}")
                        page.screenshot(path=os.path.join(debug_dir, "medium_login_google.png"))

                    else:
                        # Fallback: email + password login
                        print("  [Medium] Using email login...")
                        email_input = page.locator('input[type="email"], input[name="email"]').first
                        email_input.fill(MEDIUM_EMAIL)
                        time.sleep(1)

                        continue_btn = page.locator('button:has-text("Continue"), button:has-text("Next")').first
                        continue_btn.click()
                        time.sleep(3)

                        pwd_input = page.locator('input[type="password"]').first
                        pwd_input.fill(MEDIUM_PASSWORD)
                        time.sleep(1)

                        signin_btn = page.locator('button:has-text("Sign in"), button[type="submit"]').first
                        signin_btn.click()
                        time.sleep(5)

                        page.wait_for_load_state("domcontentloaded", timeout=30000)

                except Exception as login_err:
                    print(f"  [Medium] Login interaction error: {login_err}")
                    page.screenshot(path=os.path.join(debug_dir, "medium_login_error.png"))
                    print("  [Medium] Please complete login manually in the browser window...")
                    # Wait for user to manually complete login
                    for i in range(60):
                        time.sleep(2)
                        if "medium.com" in page.url and "signin" not in page.url and "login" not in page.url:
                            print("  [Medium] Login detected!")
                            break
                    else:
                        print("  [Medium] Login timeout (2 min)")
                        log_article("medium", article["title"], "login_timeout")
                        return False, ""


                # Session is auto-saved by persistent context
                print("  [Medium] Session saved (persistent context)")


                # Navigate to new story
                page.goto("https://medium.com/new-story", timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(5)

            page.screenshot(path=os.path.join(debug_dir, "medium_editor.png"))
            print(f"  [Medium] Editor URL: {page.url}")

            # Step 3: Fill in the article content
            print("  [Medium] Filling article content...")

            # Medium editor: title is the first contenteditable div
            # Wait for the editor to load (may need longer with Cloudflare)
            editor_loaded = False
            for attempt in range(5):
                try:
                    page.wait_for_selector('div[contenteditable="true"], textarea, [contenteditable]', timeout=10000)
                    editor_loaded = True
                    break
                except Exception:
                    print(f"  [Medium] Editor not loaded yet, refreshing... (attempt {attempt+1})")
                    page.reload(timeout=30000)
                    time.sleep(5)
                    # Wait for Cloudflare
                    for wait in range(20):
                        title = page.title()
                        if "稍候" not in title and "Checking" not in title:
                            break
                        time.sleep(2)

            if not editor_loaded:
                # Last resort: try clicking anywhere on the page first
                print("  [Medium] Trying to activate editor by clicking on page...")
                page.click("body")
                time.sleep(3)

            time.sleep(2)

            # Get all contenteditable divs
            editables = page.locator('div[contenteditable="true"]')
            count = editables.count()
            print(f"  [Medium] Found {count} contenteditable areas")

            # First one is usually the title
            title_area = editables.first
            title_area.click()
            time.sleep(0.5)
            # Clear and type title
            title_area.fill("")
            page.keyboard.type(article["title"], delay=20)
            time.sleep(1)
            print(f"  [Medium] Title filled: {article['title'][:50]}")

            # Press Enter to move to content area
            page.keyboard.press("Enter")
            time.sleep(1)

            # Now type the content — use clipboard for reliability with long text
            # Split content into paragraphs
            paragraphs = article["content"].split("\n")
            for i, para in enumerate(paragraphs):
                if i > 0:
                    page.keyboard.press("Enter")
                    time.sleep(0.1)
                if para.strip():
                    # Use clipboard paste for each paragraph
                    try:
                        page.evaluate(f"navigator.clipboard.writeText({json.dumps(para)})")
                        page.keyboard.press("Control+v")
                    except Exception:
                        page.keyboard.type(para, delay=2)
                    time.sleep(0.05)

            print(f"  [Medium] Content filled ({len(article['content'])} chars)")

            # Step 4: Add tags (look for tag input)
            time.sleep(2)
            try:
                # Medium has a tag button/input, try various selectors
                tag_selectors = [
                    'input[placeholder*="tag"]',
                    'input[placeholder*="Tag"]',
                    'button:has-text("Tags")',
                    'div[data-testid*="tag"]',
                ]
                tag_input = None
                for sel in tag_selectors:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=2000):
                            tag_input = loc
                            break
                    except Exception:
                        continue

                if tag_input:
                    tag_input.click()
                    time.sleep(1)
                    for tag in article.get("tags", [])[:5]:
                        page.keyboard.type(tag, delay=20)
                        time.sleep(0.3)
                        page.keyboard.press("Enter")
                        time.sleep(0.5)
                    print(f"  [Medium] Tags added: {article.get('tags', [])[:5]}")
                else:
                    print("  [Medium] Tag input not found (non-critical)")
            except Exception as e:
                print(f"  [Medium] Tag adding skipped: {e}")

            # Step 5: Publish — look for the Publish/Ready button
            time.sleep(2)
            published = False

            # Try clicking "Publish" or "Ready to publish"
            publish_selectors = [
                'button:has-text("Publish")',
                'button:has-text("Ready to publish")',
                'button[data-testid*="publish"]',
            ]
            for sel in publish_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        print("  [Medium] Clicked publish button")
                        time.sleep(3)

                        # If publish dialog appears, try to confirm
                        for confirm_sel in [
                            'button:has-text("Publish now")',
                            'button:has-text("Confirm")',
                            'button:has-text("Create draft")',
                        ]:
                            try:
                                confirm_btn = page.locator(confirm_sel).first
                                if confirm_btn.is_visible(timeout=3000):
                                    confirm_btn.click()
                                    print(f"  [Medium] Confirmed with: {confirm_sel}")
                                    break
                            except Exception:
                                continue

                        time.sleep(3)
                        page.wait_for_load_state("domcontentloaded", timeout=15000)
                        published = True
                        break
                except Exception:
                    continue

            if not published:
                print("  [Medium] Could not find publish button — saving as draft via Ctrl+S")
                page.keyboard.press("Control+s")
                time.sleep(3)

            # Get final URL
            final_url = page.url
            page.screenshot(path=os.path.join(debug_dir, "medium_result.png"))
            print(f"  [Medium] Article saved! URL: {final_url}")
            log_article("medium", article["title"], "success", final_url)

            return True, final_url

        except Exception as e:
            print(f"  [Medium] Error: {e}")
            try:
                page.screenshot(path=os.path.join(SESSION_DIR, "medium_error.png"))
            except Exception:
                pass
            log_article("medium", article["title"], f"error: {e}")
            return False, ""

        finally:
            context.close()  # persistent context auto-saves state


# ============================================================
# Substack — Browser Automation
# ============================================================
def post_substack(article):
    """Publish an article to Substack via browser automation.

    Strategy:
    1. Launch Chromium with persistent context (saves all state)
    2. Login to Substack if needed
    3. Navigate to Dashboard → New post
    4. Fill in title, subtitle, and content
    5. Publish

    Args:
        article: dict with 'title', 'subtitle', 'content', 'tags'

    Returns:
        (success: bool, url: str)
    """
    from playwright.sync_api import sync_playwright

    # Use persistent context for full browser state persistence
    user_data_dir = os.path.join(SESSION_DIR, "substack_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    debug_dir = os.path.join(SESSION_DIR, "debug")
    os.makedirs(debug_dir, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=300,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )

        page = context.new_page()

        try:
            # Step 1: Navigate to Substack editor
            print("  [Substack] Navigating to Substack...")
            # Go to Dashboard first, then find the "New post" button
            dashboard_url = f"{SUBSTACK_PUB_URL}/dashboard"
            page.goto(dashboard_url, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)

            # Wait for Cloudflare challenge to complete (if any)
            for wait in range(30):
                time.sleep(2)
                title = page.title()
                if "稍候" not in title and "Checking" not in title and "Just a moment" not in title:
                    break
                print(f"  [Substack] Waiting for Cloudflare challenge... ({wait+1})")

            time.sleep(5)

            current_url = page.url
            print(f"  [Substack] Current URL: {current_url}")
            page.screenshot(path=os.path.join(debug_dir, "substack_step1.png"))

            # Step 2: Check if logged in (if on login page, dashboard will redirect)
            if "login" in current_url or "sign-in" in current_url or "signin" in current_url:
                print("  [Substack] Need to login...")
                if not SUBSTACK_EMAIL or not SUBSTACK_PASSWORD:
                    print("  [Substack] ERROR: SUBSTACK_EMAIL/PASSWORD not set")
                    log_article("substack", article["title"], "failed_no_creds")
                    return False, ""

                # Go to login page
                page.goto("https://substack.com/sign-in", timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(3)
                page.screenshot(path=os.path.join(debug_dir, "substack_login1.png"))
                print(f"  [Substack] Login page URL: {page.url}")

                # Try Google sign-in first (gmail account)
                try:
                    google_btn = page.locator('button:has-text("Google"), a:has-text("Google"), div[data-testid*="google"]').first
                    if google_btn.is_visible(timeout=5000):
                        print("  [Substack] Found Google sign-in button, clicking...")
                        google_btn.click()
                        time.sleep(5)

                        # Google OAuth flow
                        email_input = page.locator('input[type="email"], input[name="identifier"]').first
                        email_input.fill(SUBSTACK_EMAIL)
                        time.sleep(1)

                        next_btn = page.locator('button:has-text("Next"), #identifierNext').first
                        next_btn.click()
                        time.sleep(3)

                        pwd_input = page.locator('input[type="password"], input[name="password"]').first
                        pwd_input.fill(SUBSTACK_PASSWORD)
                        time.sleep(1)

                        next_btn2 = page.locator('button:has-text("Next"), #passwordNext').first
                        next_btn2.click()
                        time.sleep(8)

                        page.wait_for_load_state("domcontentloaded", timeout=30000)
                    else:
                        # Fallback: email login
                        print("  [Substack] Using email login...")
                        email_signin = page.locator('button:has-text("Sign in with email"), a:has-text("Sign in with email")').first
                        if email_signin.is_visible(timeout=3000):
                            email_signin.click()
                            time.sleep(2)

                        email_input = page.locator('input[type="email"], input[name="email"]').first
                        email_input.fill(SUBSTACK_EMAIL)
                        time.sleep(1)

                        continue_btn = page.locator('button:has-text("Continue"), button:has-text("Next")').first
                        continue_btn.click()
                        time.sleep(3)

                        pwd_input = page.locator('input[type="password"]').first
                        pwd_input.fill(SUBSTACK_PASSWORD)
                        time.sleep(1)

                        signin_btn = page.locator('button:has-text("Sign in"), button[type="submit"]').first
                        signin_btn.click()
                        time.sleep(5)

                        page.wait_for_load_state("domcontentloaded", timeout=30000)

                except Exception as login_err:
                    print(f"  [Substack] Login interaction error: {login_err}")
                    page.screenshot(path=os.path.join(debug_dir, "substack_login_error.png"))
                    print("  [Substack] Please complete login manually in the browser window...")
                    # Wait for user to manually complete login
                    for i in range(60):
                        time.sleep(2)
                        if "substack.com" in page.url and "sign-in" not in page.url and "login" not in page.url:
                            print("  [Substack] Login detected!")
                            break
                    else:
                        print("  [Substack] Login timeout (2 min)")
                        log_article("substack", article["title"], "login_timeout")
                        return False, ""


                # Session is auto-saved by persistent context
                print("  [Substack] Session saved (persistent context)")


                # Navigate to dashboard after login
                page.goto(dashboard_url, timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                time.sleep(5)

            # Click "New post" button on dashboard
            print("  [Substack] Looking for 'New post' button...")
            new_post_clicked = False
            new_post_selectors = [
                'a:has-text("New post")',
                'button:has-text("New post")',
                'a:has-text("Create post")',
                'button:has-text("Create post")',
                'a:has-text("Write")',
                'button:has-text("Write")',
                'a[href*="/drafts/new"]',
                'a[href*="/write"]',
                'a[href*="/new"]',
            ]

            for sel in new_post_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        print(f"  [Substack] Clicked: {sel}")
                        new_post_clicked = True
                        break
                except Exception:
                    continue

            if not new_post_clicked:
                # Try navigating directly to the editor
                print("  [Substack] No 'New post' button found, trying direct editor URL...")
                page.goto(f"{SUBSTACK_PUB_URL}/write", timeout=60000)
                time.sleep(3)

            # Wait for editor to load
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            time.sleep(5)

            page.screenshot(path=os.path.join(debug_dir, "substack_editor.png"))
            print(f"  [Substack] Editor URL: {page.url}")

            # Step 3: Fill in the article
            print("  [Substack] Filling article content...")

            # Wait for editor to load (may need longer)
            editor_loaded = False
            for attempt in range(5):
                try:
                    page.wait_for_selector('[contenteditable="true"], textarea, [contenteditable]', timeout=10000)
                    editor_loaded = True
                    break
                except Exception:
                    print(f"  [Substack] Editor not loaded yet, refreshing... (attempt {attempt+1})")
                    page.reload(timeout=30000)
                    time.sleep(5)

            if not editor_loaded:
                print("  [Substack] Trying to activate editor by clicking on page...")
                page.click("body")
                time.sleep(3)

            time.sleep(2)

            # Find title input — try multiple selectors
            title_filled = False
            title_selectors = [
                'h1[contenteditable="true"]',
                'input[placeholder*="Title"]',
                'input[placeholder*="title"]',
                'div[contenteditable="true"][class*="title"]',
                'div[contenteditable="true"]',
            ]

            for sel in title_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=3000):
                        loc.click()
                        time.sleep(0.5)
                        loc.fill("")
                        page.keyboard.type(article["title"], delay=20)
                        print(f"  [Substack] Title filled via {sel}")
                        title_filled = True
                        break
                except Exception:
                    continue

            if not title_filled:
                print("  [Substack] Could not find title field, trying first contenteditable...")
                first_editable = page.locator('[contenteditable="true"]').first
                first_editable.click()
                page.keyboard.type(article["title"], delay=20)

            # Move to content area
            page.keyboard.press("Enter")
            time.sleep(1)

            # Type subtitle if available
            if article.get("subtitle"):
                page.keyboard.type(article["subtitle"], delay=20)
                page.keyboard.press("Enter")
                time.sleep(1)

            # Type content paragraph by paragraph
            paragraphs = article["content"].split("\n")
            for i, para in enumerate(paragraphs):
                if i > 0:
                    page.keyboard.press("Enter")
                    time.sleep(0.1)
                if para.strip():
                    try:
                        page.evaluate(f"navigator.clipboard.writeText({json.dumps(para)})")
                        page.keyboard.press("Control+v")
                    except Exception:
                        page.keyboard.type(para, delay=2)
                    time.sleep(0.05)

            print(f"  [Substack] Content filled ({len(article['content'])} chars)")

            # Step 4: Publish
            time.sleep(2)
            published = False

            publish_selectors = [
                'button:has-text("Publish")',
                'button:has-text("Send")',
                'button[data-testid*="publish"]',
            ]

            for sel in publish_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        print(f"  [Substack] Clicked publish button: {sel}")
                        time.sleep(3)

                        # Confirm if dialog appears
                        for confirm_sel in [
                            'button:has-text("Publish now")',
                            'button:has-text("Confirm")',
                            'button:has-text("Send to everyone")',
                        ]:
                            try:
                                confirm_btn = page.locator(confirm_sel).first
                                if confirm_btn.is_visible(timeout=3000):
                                    confirm_btn.click()
                                    print(f"  [Substack] Confirmed with: {confirm_sel}")
                                    break
                            except Exception:
                                continue

                        time.sleep(3)
                        page.wait_for_load_state("domcontentloaded", timeout=15000)
                        published = True
                        break
                except Exception:
                    continue

            if not published:
                print("  [Substack] Could not auto-publish — article saved as draft")
                page.keyboard.press("Control+s")
                time.sleep(3)

            # Get final URL
            final_url = page.url
            page.screenshot(path=os.path.join(debug_dir, "substack_result.png"))
            print(f"  [Substack] Article saved! URL: {final_url}")
            log_article("substack", article["title"], "success", final_url)

            return True, final_url

        except Exception as e:
            print(f"  [Substack] Error: {e}")
            try:
                page.screenshot(path=os.path.join(SESSION_DIR, "substack_error.png"))
            except Exception:
                pass
            log_article("substack", article["title"], f"error: {e}")
            return False, ""

        finally:
            context.close()  # persistent context auto-saves state


# ============================================================
# Telegram Notification
# ============================================================
def notify_telegram(message):
    """Send notification to BroadFSC Telegram channel."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if not bot_token or not channel_id:
        print("  [Notify] Telegram not configured, skipping")
        return

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": channel_id,
            "text": message,
            "parse_mode": "HTML",
        }
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"  [Notify] Telegram failed: {e}")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("BroadFSC Medium & Substack Article Publisher")
    print("=" * 60)

    now = datetime.datetime.utcnow()
    print(f"Current UTC: {now.strftime('%Y-%m-%d %H:%M')}")
    print()

    # Generate article
    print("--- Generating Article ---")
    article = generate_article()
    print(f"  Title: {article['title']}")
    print(f"  Subtitle: {article.get('subtitle', 'N/A')}")
    print(f"  Content: {len(article['content'])} chars")
    print(f"  Tags: {article.get('tags', [])}")
    print()

    results = {}

    # --- Medium ---
    print("--- Medium ---")
    if MEDIUM_EMAIL and MEDIUM_PASSWORD:
        print(f"  Email: {MEDIUM_EMAIL[:3]}***@***")
        success, url = post_medium(article)
        results["medium"] = {"success": success, "url": url}
        status = "✅" if success else "❌"
        print(f"  Result: {status}")
    else:
        print("  Not configured (MEDIUM_EMAIL/PASSWORD missing)")
        results["medium"] = {"success": False, "url": ""}
    print()

    # --- Substack ---
    print("--- Substack ---")
    if SUBSTACK_EMAIL and SUBSTACK_PASSWORD:
        print(f"  Email: {SUBSTACK_EMAIL[:3]}***@***")
        success, url = post_substack(article)
        results["substack"] = {"success": success, "url": url}
        status = "✅" if success else "❌"
        print(f"  Result: {status}")
    else:
        print("  Not configured (SUBSTACK_EMAIL/PASSWORD missing)")
        results["substack"] = {"success": False, "url": ""}
    print()

    # Summary
    print("=" * 60)
    print("Publish Summary:")
    for platform, result in results.items():
        status = "✅" if result["success"] else "❌"
        url_str = f" → {result['url'][:60]}" if result.get("url") else ""
        print(f"  {platform}: {status}{url_str}")

    # Telegram notification
    notify_msg = f"📰 <b>Article Published</b>\n\n"
    notify_msg += f"<b>{article['title']}</b>\n"
    for platform, result in results.items():
        if result["success"]:
            notify_msg += f"✅ {platform}: {result.get('url', 'OK')}\n"
        else:
            notify_msg += f"❌ {platform}: Failed\n"
    notify_telegram(notify_msg)

    print("\nDone.")


if __name__ == "__main__":
    main()
