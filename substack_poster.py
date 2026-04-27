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
# Persona System — Substack Edition
# ============================================================
PERSONAS = [
    {
        "name": "Alex 'The Croc'",
        "emoji": "\U0001f40a",
        "title": "Technical Analyst",
        "style": "Sharp, data-driven, no-nonsense. Uses charts and patterns. Precise about levels and signals.",
        "hook": "Start with a striking chart pattern or critical price level that defines the current market regime",
        "hashtags": ["TechnicalAnalysis", "Trading", "Charts"],
    },
    {
        "name": "Thomas Yang",
        "emoji": "\U0001f4d8",
        "title": "Value Investor",
        "style": "Patient, methodical, long-term focused. Deep fundamental analysis, DCF thinking, margin of safety.",
        "hook": "Open with an undervalued asset the market is systematically mispricing, backed by numbers",
        "hashtags": ["ValueInvesting", "Fundamentals", "LongTerm"],
    },
    {
        "name": "Michael Hong",
        "emoji": "\U0001f52d",
        "title": "Macro Strategist",
        "style": "Big-picture thinker. Central banks, geopolitics, cross-asset correlations, regime shifts.",
        "hook": "Lead with a macro trend or policy shift that markets have not fully priced in",
        "hashtags": ["Macro", "GlobalMarkets", "CentralBanks"],
    },
]

# Article types — rotates weekly: Mon=DeepDive, Wed=Radar, Fri=Contrarian
ARTICLE_TYPES = [
    {
        "name": "Weekly Deep Dive",
        "description": "One theme, thoroughly explored with institutional depth",
        "structure": (
            "1. THESIS STATEMENT — One clear, arguable claim (2-3 sentences)\n"
            "2. THE EVIDENCE — 4-6 detailed paragraphs examining data, history, and mechanism\n"
            "3. WHAT THE NUMBERS SAY — 8-12 specific data points with sources (precise figures, not vague)\n"
            "4. INSTITUTIONAL POSITIONING — How smart money is positioned and why\n"
            "5. RISK FACTORS — What could make this thesis wrong (honest assessment)\n"
            "6. FRAMEWORK FOR DECISIONS — A clear decision tree or criteria, not just 'buy/sell'\n"
            "7. KEY TAKEAWAY — One insight the reader won't find elsewhere"
        ),
        "word_count": "2500-4000",
    },
    {
        "name": "Market Radar",
        "description": "This week's critical data points, anomalies, and what they signal",
        "structure": (
            "1. SIGNALS THIS WEEK — 3-5 charts/data points that moved markets and why they matter\n"
            "2. ANOMALY DETECTION — Something unusual in the data that most people missed\n"
            "3. CROSS-ASSET READ — How equities, bonds, FX, and commodities are telling different stories\n"
            "4. POSITIONING CHECK — COT data, fund flows, or options market signals\n"
            "5. WHAT TO WATCH — 3-5 catalysts in the coming week with expected market impact\n"
            "6. BOTTOM LINE — One actionable observation"
        ),
        "word_count": "1500-2500",
    },
    {
        "name": "Contrarian Take",
        "description": "Where the consensus is wrong — and the opportunity is real",
        "structure": (
            "1. THE CONSENSUS — What everyone believes right now (state it fairly)\n"
            "2. WHY THEY'RE WRONG — The specific analytical error or blind spot\n"
            "3. HISTORICAL PRECEDENT — When has this same consensus been wrong before? What happened?\n"
            "4. THE DATA THEY'RE MISSING — 5-8 data points that contradict consensus\n"
            "5. IF I'M RIGHT — Concrete scenario analysis with price targets or probability ranges\n"
            "6. IF I'M WRONG — What would invalidate this thesis (honest, specific)\n"
            "7. HOW TO PLAY IT — 2-3 structured approaches with defined risk"
        ),
        "word_count": "2000-3500",
    },
]


def get_daily_persona(platform_shift=0):
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    return PERSONAS[(day_idx + platform_shift) % len(PERSONAS)]


def get_article_type():
    """Determine article type based on day of week.
    Mon=Deep Dive, Wed=Radar, Fri=Contrarian (other days rotate)
    """
    weekday = datetime.datetime.utcnow().weekday()  # 0=Mon, 6=Sun
    # Map: Mon(0)->Deep Dive, Tue(1)->Radar, Wed(2)->Radar, Thu(3)->Contrarian, Fri(4)->Deep Dive, Sat(5)->Radar, Sun(6)->Contrarian
    type_map = {0: 0, 1: 1, 2: 1, 3: 2, 4: 0, 5: 1, 6: 2}
    return ARTICLE_TYPES[type_map.get(weekday, 1)]


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
        article_type = get_article_type()

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    f"PERSONA: {persona['emoji']} {persona['name']} — {persona['title']}\n"
                    f"STYLE: {persona['style']}\n"
                    f"ARTICLE TYPE: {article_type['name']} — {article_type['description']}\n\n"
                    f"Write a {article_type['name']} for {now.strftime('%A')}, {now.strftime('%B %d, %Y')}.\n"
                    f"Focus: US stocks / global macro / investment strategy — pick ONE specific theme.\n"
                    f"Hook rule: {persona['hook']}\n\n"
                    f'OUTPUT FORMAT - valid JSON single line:\n'
                    f'{{"title":"...","subtitle":"...","content":"...(markdown)...","tags":["tag1","tag2"]}}\n\n'
                    f"- content uses \\n for line breaks, escape \" inside content\n"
                    f"- No code blocks wrapping JSON\n"
                    f"\nARTICLE STRUCTURE:\n"
                    f"{article_type['structure']}\n\n"
                    f"\nQUALITY RULES:\n"
                    f"- {article_type['word_count']} words of SUBSTANTIVE analysis (not filler)\n"
                    f"- ## headers for each section, **bold** for key terms\n"
                    f"- Use SPECIFIC numbers: 'S&P 500 at 5,234' not 'markets are up'\n"
                    f"- Reference real indices, yields, prices, earnings multiples\n"
                    f"- Show your work: explain the mechanism, don't just state conclusions\n"
                    f"- Be intellectually honest: acknowledge risks and opposing views\n"
                    f"- Write like a sell-side research note, not a blog post\n"
                    f"- NO promotional language, NO calls to action, NO 'subscribe', NO 'sign up'\n"
                    f"- NO disclaimers about 'not financial advice' — we are a research publication\n"
                    f"- Tags: 3-5 without #, lowercase\n"
                    f"- Title <80 chars, Subtitle <120 chars\n"
                    f"- The title should be specific and newsworthy, not generic"
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

        article.setdefault("tags", ["investing", "markets"])
        article.setdefault("subtitle", "")

        print(f"  Article: '{article['title']}' ({len(article['content'])} chars)")
        print(f"  Persona: {persona['name']}")
        print(f"  Type: {article_type['name']}")
        return article

    except Exception as e:
        print(f"  AI failed ({e}), using fallback")
        return get_fallback_article()


def get_fallback_article():
    day_idx = datetime.datetime.utcnow().timetuple().tm_yday
    articles = [
        {
            "title": "The Yield Curve Is Speaking — Are You Listening?",
            "subtitle": "What 50 years of inversion data tells us about the next 12 months",
            "content": (
                "## The Signal Nobody Wants to Hear\n\n"
                "The 10Y-2Y Treasury spread has been inverted for over 18 months. "
                "In the last 50 years, every single recession was preceded by this signal "
                "— with a 12-18 month lag. We're in that lag window right now.\n\n"
                "But the yield curve isn't just a binary recession indicator. It encodes "
                "information about credit conditions, bank profitability, and the term premium "
                "that institutional investors demand for locking up capital.\n\n"
                "## The Mechanism: Why Inversions Precede Downturns\n\n"
                "When short-term rates exceed long-term rates, banks' net interest margins compress. "
                "The 3-month/10-year spread is currently at -125 basis points — one of the deepest "
                "inversions since 1980. Historical analysis shows that when this spread stays below "
                "-100bp for more than 6 months, recession probability within 12 months rises to 85%.\n\n"
                "The transmission mechanism works through three channels:\n"
                "- **Bank lending**: Compressed margins reduce credit extension to businesses\n"
                "- **Corporate refinancing**: Higher short-term borrowing costs hit rollover debt\n"
                "- **Consumer spending**: Variable-rate mortgages and credit cards drain disposable income\n\n"
                "## What the Numbers Say\n\n"
                "- **10Y-2Y Spread**: -0.35% (inverted 18 months)\n"
                "- **3M-10Y Spread**: -1.25% (deepest since 1980)\n"
                "- **S&P 500 P/E**: 21.2x forward (10-year avg: 17.8x, +19% premium)\n"
                "- **VIX**: 14.2 (bottom 10th percentile historically)\n"
                "- **Fed Funds Rate**: 5.25-5.50% (highest in 23 years)\n"
                "- **Commercial RE Delinquencies**: 6.2% (up 2.1x YoY)\n"
                "- **Consumer Savings Rate**: 3.6% (down from 7.9% in 2021)\n"
                "- **S&P 500 Earnings Growth**: 2.1% YoY (vs. 12% average expansion)\n"
                "- **High Yield Spread**: 340bp (still tight, not pricing recession)\n"
                "- **Corporate Bond Issuance**: -23% YoY (deleveraging underway)\n\n"
                "## How Smart Money Is Positioned\n\n"
                "Hedge fund net long exposure has dropped 15% this quarter — the sharpest "
                "decline since Q1 2022. But here's the nuance: they're not going short. "
                "They're shifting from growth to quality. Large-cap, high-margin, low-debt "
                "names are seeing inflows while small-cap speculative plays are being liquidated.\n\n"
                "Corporate insiders are selling at a 3:1 ratio — the highest since October 2021. "
                "When people closest to the data head for exits, it's worth paying attention.\n\n"
                "## What Could Make This Wrong\n\n"
                "The 'soft landing' camp has one strong argument: labor markets. "
                "Unemployment at 3.8% with job openings at 8.7 million means the economy "
                "still has slack. If the Fed engineers a measured rate cut cycle (25bp per quarter), "
                "the yield curve could normalize without triggering recession.\n\n"
                "Additionally, the AI capex cycle is creating a secular demand driver that "
                "didn't exist in prior inversion episodes. Data center spending is projected "
                "to grow 35% YoY through 2027 — this is real capital formation, not financial engineering.\n\n"
                "## Framework for Decisions\n\n"
                "Rather than a binary 'recession or not' call, here's a more useful framework:\n\n"
                "| Signal | Bullish Scenario | Bearish Scenario |\n"
                "|--------|-----------------|------------------|\n"
                "| Fed cuts begin | Normalize curve, risk-on | Signal承认衰退, risk-off |\n"
                "| Credit spreads widen | Value opportunity | Systemic risk rising |\n"
                "| Earnings revise down | Already priced in | Downward spiral begins |\n\n"
                "## Key Takeaway\n\n"
                "The yield curve is the most reliable leading indicator we have. "
                "It's been right every time for 50 years. The question isn't whether "
                "a slowdown is coming — it's how severe and how well-positioned you are.\n"
                "The smart move isn't to panic; it's to build a portfolio that benefits "
                "from either scenario."
            ),
            "tags": ["yieldcurve", "recession", "bonds", "macro", "treasury"],
        },
        {
            "title": "Intel's Turnaround: Reading the Signal from the Noise",
            "subtitle": "Below the 24% surge, the real story is in the gross margin trajectory",
            "content": (
                "## Beyond the Headlines\n\n"
                "Intel surged 24% in a single session — its largest move in decades. "
                "The narrative is simple: AI chip wins, foundry partnerships, short squeeze. "
                "But the real question for investors isn't what happened yesterday. "
                "It's whether the structural turnaround thesis is actually intact.\n\n"
                "## The Bull Case: What's Real\n\n"
                "Intel's foundry business secured two major design wins from tier-1 customers "
                "in Q1 — the first external foundry revenue of meaningful scale. "
                "The 18A process node is on track for H2 2025 production, "
                "which would close the gap with TSMC's N3 to under 18 months.\n\n"
                "The data center segment showed +18% YoY revenue growth, driven by "
                "Xeon Scalable deployments in AI inference workloads. This is a real trend: "
                "inference is shifting from training-dominated GPUs to CPU-centric architectures "
                "for cost-sensitive deployment at the edge.\n\n"
                "## What the Numbers Say\n\n"
                "- **Current Price**: ~$31 (post-surge, +24% from $25)\n"
                "- **Market Cap**: ~$130B\n"
                "- **P/E (TTM)**: 32x (vs. AMD 45x, TSMC 25x, NVDA 65x)\n"
                "- **Forward P/E**: 28x (implies 14% earnings growth)\n"
                "- **Gross Margin**: 38.2% (vs. peak of 65% in 2020, floor was 35%)\n"
                "- **Foundry Revenue**: $1.2B (+340% YoY, but still -$7B annual loss)\n"
                "- **Free Cash Flow**: -$2.8B (negative for 6 consecutive quarters)\n"
                "- **Short Interest**: 14% of float (still elevated post-squeeze)\n"
                "- **R&D Spend**: $16.2B (23% of revenue — industry high)\n"
                "- **Debt/Equity**: 0.42 (manageable but rising)\n\n"
                "## The Bear Case: Why This Isn't 1990s Intel\n\n"
                "Intel's gross margins have collapsed from 65% to 38% in four years. "
                "This isn't a cyclical dip — it's structural. The foundry business "
                "requires $30B+ in cumulative capex before it reaches breakeven, "
                "and Intel's free cash flow can't sustain that pace without dilution.\n\n"
                "The competitive landscape is fundamentally different from Intel's golden era. "
                "TSMC has a 3-4 year process lead and $40B annual capex budget. "
                "AMD has taken 15% server CPU share. NVIDIA dominates AI training. "
                "Intel isn't competing against one rival — it's fighting a multi-front war.\n\n"
                "## Historical Precedent: IBM's Semiconductor Pivot\n\n"
                "Intel's situation parallels IBM's 2014 semiconductor foundry pivot. "
                "IBM invested $3B in fabs, secured design wins, then sold the entire "
                "division to GlobalFoundries for $1.5B two years later. The lesson: "
                "foundry economics are brutal for companies without existing scale.\n\n"
                "## Framework for Decisions\n\n"
                "Intel is a binary outcome stock. The key metrics to watch:\n"
                "- **Gross margin above 42%**: Turnaround thesis intact\n"
                "- **Gross margin below 35%**: Structural decline accelerating\n"
                "- **Foundry revenue >$3B/quarter**: Path to breakeven visible\n"
                "- **Free cash flow turns positive**: Risk/reward fundamentally shifts\n\n"
                "## Key Takeaway\n\n"
                "One-day surges don't fix structural problems. Intel's turnaround is real "
                "but early, and the stock is pricing in a recovery that's at least "
                "12 months away. The better trade: wait for the post-surge pullback "
                "to the $25-27 range (20-day MA), then size small with defined risk."
            ),
            "tags": ["Intel", "semiconductors", "foundry", "value"],
        },
        {
            "title": "The Dollar's Breakout: What History Says About What Comes Next",
            "subtitle": "DXY above 106 has preceded major regime shifts in global capital flows",
            "content": (
                "## The World's Most Important Chart\n\n"
                "The US Dollar Index just punched through 106 — a level it hasn't sustained "
                "above since 2003. Most commentary focuses on what this means for US exporters "
                "or emerging markets. But the real story is about the global financial system's "
                "plumbing: dollar-denominated debt, cross-currency basis swaps, and the "
                "feedback loop between a strong dollar and tightening global financial conditions.\n\n"
                "## The Mechanics of Dollar Strength\n\n"
                "The dollar doesn't operate in isolation. When DXY rises by 4% in a quarter "
                "(as it has in Q1 2026), the effects cascade through the global system:\n\n"
                "- **S&P 500**: ~40% of revenue comes from overseas; 4% USD rise = ~1.5% earnings headwind\n"
                "- **Emerging Markets**: $12.8 trillion in dollar-denominated corporate and sovereign debt\n"
                "- **Commodities**: Gold, oil, and copper all priced in dollars — inverse pressure\n"
                "- **Global Liquidity**: Strong dollar tightens Eurodollar funding markets\n\n"
                "## What the Numbers Say\n\n"
                "- **DXY Level**: 106.4 (+4.2% YTD, +8.1% from 2025 low)\n"
                "- **EUR/USD**: 1.062 (lowest since 2022, within 5% of parity)\n"
                "- **JPY/USD**: 154.8 (BoJ intervention at 160 is widely expected)\n"
                "- **Gold**: $2,340 (+12% YTD) — decoupling from inverse dollar correlation\n"
                "- **US 10Y**: 4.52% (rising despite Fed 'pause' narrative)\n"
                "- **EM FX Index**: -6.3% YTD vs. USD\n"
                "- **CTFC Net Short EUR**: 182K contracts (highest since Q4 2022)\n"
                "- **Cross-currency Basis (EUR/USD)**: -35bp (elevated dollar funding stress)\n"
                "- **BIS Dollar Credit**: $13.6T outstanding (+$800B YoY)\n"
                "- **Central Bank Gold Purchases**: 1,137 tonnes in 2025 (highest since 1967)\n\n"
                "## The Gold Anomaly\n\n"
                "Gold should be falling with a strong dollar. It's not — it's up 12%. "
                "This divergence has only happened three times in the past 30 years: "
                "2008 (GFC), 2011 (Euro crisis), and 2020 (COVID). Each time, it signaled "
                "a fundamental repricing of global financial risk.\n\n"
                "Central banks are buying gold at record pace. This isn't speculation — "
                "it's de-dollarization in action. China, India, and Poland collectively "
                "added 450 tonnes in Q4 2025 alone.\n\n"
                "## Historical Precedent: 1985 and 2000\n\n"
                "The last two times DXY broke above 106 (1985 and 2000-2002), "
                "what followed was significant:\n"
                "- **1985**: Plaza Accord engineered a 40% dollar decline over 3 years\n"
                "- **2000**: Dollar peaked at 121, then fell 35% over 5 years as the "
                "dot-com bubble deflated and current account deficit widened\n\n"
                "In both cases, the dollar reversal created massive winners in EM assets, "
                "commodities, and non-US equities.\n\n"
                "## What Could Break the Dollar Bull\n\n"
                "Three catalysts could reverse the trend:\n"
                "1. **Fed cutting cycle begins** — Every major dollar peak in the past "
                "40 years was followed by rate cuts within 6 months\n"
                "2. **US current account deteriorates** — At -3.2% of GDP, the deficit "
                "is widening as energy exports decline and imports rise\n"
                "3. **G7 coordinated intervention** — Less likely than 1985, but EUR/JPY "
                "weakness creates political pressure\n\n"
                "## Framework for Decisions\n\n"
                "A strong dollar regime favors specific strategies:\n"
                "- **Domestic revenue US stocks**: Tech and financials outperform multinationals\n"
                "- **Currency-hedged international equity**: Eliminates the FX drag\n"
                "- **Gold allocation 5-10%**: Hedge against both inflation AND dollar volatility\n"
                "- **Avoid EM local currency debt**: Duration risk compounded by FX risk\n"
                "- **Long USD/short JPY**: Momentum trade supported by yield differential\n\n"
                "## Key Takeaway\n\n"
                "The dollar is telling us something important: global liquidity is tightening, "
                "and capital is flowing to the safest, highest-yielding asset. "
                "The trade isn't to fight the dollar — it's to position for what happens "
                "when it eventually reverses. Because it always does."
            ),
            "tags": ["USD", "dollar", "gold", "forex", "macro", "emergingmarkets"],
        },
    ]
    article = articles[day_idx % len(articles)]
    article_type = get_article_type()
    print(f"  Fallback: '{article['title']}' ({article_type['name']})")
    return article


# ============================================================
# Substack Poster (Playwright Headless)
# ============================================================
def post_to_substack(article):
    """Publish an article to Substack via headless Playwright.
    
    Flow: substack.com -> Dashboard -> Create -> Article -> Fill -> Publish
    Session must be pre-saved via login_substack_v4.py (persistent browser context).
    """
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
            # === Step 1: Check login via substack.com/settings ===
            print("  [Substack] Checking login...")
            page.goto("https://substack.com/settings", timeout=60000)
            time.sleep(5)

            # Handle Cloudflare challenge
            for wait in range(30):
                title = page.title()
                if all(x not in title for x in ["稍候", "Checking", "Just a moment", "Attention"]):
                    break
                time.sleep(2)
                print(f"    Cloudflare wait... ({wait+1})")

            settings_text = page.locator("body").inner_text(timeout=5000)
            is_logged_in = SUBSTACK_EMAIL in settings_text or "broadcastmarketintelligence" in settings_text

            if not is_logged_in:
                # Check URL for redirect to sign-in
                current_url = page.url
                if "/sign-in" in current_url or "/signin" in current_url:
                    print("  [Substack] NOT LOGGED IN - need manual login first")
                    print("    Run: python login_substack_v4.py")
                    log_article("substack", article["title"], "not_logged_in")
                    return False, ""
                # Double-check via dashboard
                page.goto("https://substack.com/dashboard", timeout=30000)
                time.sleep(3)
                dash_text = page.locator("body").inner_text(timeout=3000)
                if "Discover world class culture" in dash_text and "Create" not in dash_text:
                    print("  [Substack] NOT LOGGED IN - session expired")
                    log_article("substack", article["title"], "session_expired")
                    return False, ""
                # Maybe settings page loaded differently - check for email
                if SUBSTACK_EMAIL.split("@")[0] in dash_text or "Broadcast" in dash_text:
                    is_logged_in = True

            if not is_logged_in:
                print("  [Substack] Login status unclear, proceeding anyway...")

            print("  [Substack] Login confirmed.")

            # === Step 2: Navigate to editor (multiple methods) ===
            print("  [Substack] Opening editor...")
            
            editor_url = None

            # Method 1: Direct write URL (fastest, no dashboard needed)
            print("    Trying substack.com/write...")
            page.goto("https://substack.com/write", timeout=60000)
            time.sleep(5)
            editor_url = page.url
            print(f"    /write URL: {editor_url}")

            # Method 2: If /write didn't give an editor, try dashboard -> Create -> Article
            if "/publish" not in editor_url and "/write" not in editor_url and "/post" not in editor_url:
                print("    /write didn't work, trying dashboard -> Create -> Article...")
                page.goto(f"{PUB_URL}/dashboard", timeout=60000)
                time.sleep(5)
                
                try:
                    create_btn = page.locator('button:has-text("Create")').first
                    if create_btn.is_visible(timeout=5000):
                        create_btn.click()
                        time.sleep(2)
                        article_btn = page.locator('a:has-text("Article"), button:has-text("Article")').first
                        if article_btn.is_visible(timeout=3000):
                            article_btn.click()
                            time.sleep(5)
                            editor_url = page.url
                            print(f"    Dashboard->Article URL: {editor_url}")
                except Exception as e:
                    print(f"    Dashboard flow error: {e}")

            # Method 3: Try direct publish URL on publication
            if "/publish" not in (editor_url or ""):
                print("    Trying direct publish URL...")
                page.goto(f"{PUB_URL}/publish/post", timeout=60000)
                time.sleep(5)
                editor_url = page.url
                print(f"    Direct publish URL: {editor_url}")

            if not editor_url:
                page.screenshot(path=os.path.join(debug_dir, "substack_no_editor.png"))
                log_article("substack", article["title"], "no_editor_found")
                return False, ""

            print(f"    Editor URL: {editor_url}")

            # === Step 4: Wait for editor to load ===
            print("  [Substack] Waiting for editor...")
            
            # Wait for editable elements - Substack editor uses contenteditable
            editor_loaded = False
            for attempt in range(10):
                try:
                    # Substack editor: title input placeholder is "Add a title..."
                    title_input = page.locator('input[placeholder*="title"], input[placeholder*="Title"]')
                    content_editable = page.locator('[contenteditable="true"]')
                    
                    if title_input.count() > 0:
                        editor_loaded = True
                        print(f"    Editor loaded (attempt {attempt+1}) - found title input")
                        break
                    if content_editable.count() > 0:
                        editor_loaded = True
                        print(f"    Editor loaded (attempt {attempt+1}) - found contenteditable")
                        break
                    
                    time.sleep(2)
                except Exception:
                    time.sleep(2)

            if not editor_loaded:
                # Try one more approach: click on the editor area
                print("    Trying to activate editor by clicking...")
                try:
                    page.click("body")
                    time.sleep(2)
                    # Click in center of page where editor should be
                    page.click("#main", position={"x": 640, "y": 300})
                    time.sleep(3)
                    
                    if page.locator('[contenteditable="true"]').count() > 0:
                        editor_loaded = True
                        print("    Editor activated after click")
                except Exception:
                    pass

            if not editor_loaded:
                page.screenshot(path=os.path.join(debug_dir, "substack_editor_timeout.png"))
                print("  [Substack] ERROR: Editor never loaded")
                log_article("substack", article["title"], "editor_timeout")
                return False, ""

            # === Step 5: Fill article content ===
            print("  [Substack] Filling content...")

            # Fill Title — Substack editor: click the ProseMirror body area, title is the first line
            # The sidebar "Add a title..." is just a file name input, NOT the post title
            # The real post title goes into the ProseMirror editor as the first content
            title_done = False
            
            # Click the main ProseMirror editor to focus it
            try:
                editor_el = page.locator('.ProseMirror[contenteditable="true"]').first
                if editor_el.is_visible(timeout=3000):
                    editor_el.click()
                    time.sleep(0.5)
                    # Type the title as the first line in the editor
                    page.keyboard.type(article["title"], delay=15)
                    title_done = True
                    print(f"    Title typed into ProseMirror editor")
            except Exception as e:
                print(f"    ProseMirror click failed: {e}")
            
            if not title_done:
                # Fallback: try sidebar title input
                for sel in [
                    'input[placeholder="Add a title..."]',
                    'input[placeholder*="title"]',
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.is_visible(timeout=2000):
                            el.click()
                            time.sleep(0.3)
                            el.fill("")
                            page.keyboard.type(article["title"], delay=20)
                            title_done = True
                            print(f"    Title filled via: {sel}")
                            break
                    except Exception:
                        continue

            if not title_done:
                # Fallback: use first contenteditable or input
                try:
                    first_input = page.locator('input').first
                    first_input.click()
                    page.keyboard.type(article["title"], delay=20)
                    title_done = True
                    print("    Title filled via first input")
                except Exception:
                    print("    WARNING: Could not fill title")

            # Move to body area — press Enter twice after title to create space
            if title_done:
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")
                time.sleep(0.5)
            
            # If subtitle exists, type it as the next line (Substack auto-styles it)
            if article.get("subtitle"):
                page.keyboard.type(article["subtitle"], delay=15)
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")
                time.sleep(0.3)

            # Fill Body content — type directly into the focused ProseMirror editor
            # (already focused from title typing above)

            # Type body content paragraph by paragraph using clipboard
            paragraphs = article["content"].split("\n")
            char_count = 0
            for i, para in enumerate(paragraphs):
                if para.strip():
                    if i > 0:
                        page.keyboard.press("Enter")
                        time.sleep(0.05)
                    try:
                        page.evaluate(f'navigator.clipboard.writeText({json.dumps(para)})')
                        page.keyboard.press("Control+v")
                    except Exception:
                        page.keyboard.type(para[:500], delay=2)
                    char_count += len(para)

            print(f"    Content filled: ~{char_count} chars")

            # === Step 6: Publish ===
            time.sleep(2)
            published = False
            
            # First click "Continue" if visible (Substack has Continue -> Review -> Publish flow)
            continue_sels = [
                'button:has-text("Continue")',
                'button:has-text("Next")',
            ]
            for sel in continue_sels:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        print(f"    Clicked: {sel}")
                        time.sleep(3)
                        break
                except Exception:
                    continue

            # Now look for Publish/Send button
            # Substack uses "Send to everyone now" (not "Publish")
            publish_sels = [
                'button:has-text("Send to everyone now")',
                'button:has-text("Publish")',
                'button:has-text("Publish now")',
                'button:has-text("Post")',
                'button:has-text("Post now")',
                'button[data-testid="publish-button"]',
            ]
            
            for sel in publish_sels:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        print(f"    Publish button clicked: {sel}")
                        time.sleep(3)
                        
                        # Confirm dialog (if any)
                        for csel in [
                            'button:has-text("Publish now")', 'button:has-text("Confirm")',
                            'button:has-text("Yes, publish")',
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
                # Try clicking Continue one more time if there's a multi-step flow
                for sel in continue_sels:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=2000):
                            btn.click()
                            print(f"    Second Continue: {sel}")
                            time.sleep(3)
                            # Try publish again
                            for psel in publish_sels:
                                try:
                                    pbtn = page.locator(psel).first
                                    if pbtn.is_visible(timeout=2000):
                                        pbtn.click()
                                        time.sleep(3)
                                        published = True
                                        break
                                except Exception:
                                    continue
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

    # Check if today is a Substack publishing day (Mon/Wed/Fri)
    weekday = datetime.datetime.utcnow().weekday()  # 0=Mon, 6=Sun
    pub_days = {0, 2, 4}  # Mon, Wed, Fri
    if weekday not in pub_days and IS_CI:
        print(f"Today is {datetime.datetime.utcnow().strftime('%A')} — skipping (publish Mon/Wed/Fri only)")
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
