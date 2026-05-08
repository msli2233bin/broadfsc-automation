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
SUBSTACK_EMAIL = os.environ.get("SUBSTACK_EMAIL", "")
SUBSTACK_PASSWORD = os.environ.get("SUBSTACK_PASSWORD", "")
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
# Cover Image Generator
# ============================================================
def generate_cover_image(title, article_type="Market Radar"):
    """Generate a branded cover image for Substack posts using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("    [Cover] Pillow not installed, skipping cover image")
        return None

    W, H = 1200, 630
    img = Image.new('RGB', (W, H), color='#1a1a2e')
    draw = ImageDraw.Draw(img)

    # Gradient background
    for i in range(H):
        r = min(255, 26 + int(i * 0.08))
        g = min(255, 26 + int(i * 0.04))
        b = min(255, 46 + int(i * 0.12))
        draw.line([(0, i), (W, i)], fill=(r, g, b))

    # Decorative lines
    for y_off in [80, 550]:
        draw.line([(50, y_off), (W - 50, y_off)], fill='#00d4aa', width=2)

    # Fonts
    try:
        font_title = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 44)
        font_sub = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
        font_brand = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 20)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_brand = font_title

    # Brand label (top-left)
    draw.text((60, 30), "DeepSight", fill='#00d4aa', font=font_brand)
    draw.text((200, 33), f"| {article_type}", fill='#666666', font=font_sub)

    # Title (centered, word-wrapped)
    max_chars_per_line = 30
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            current_line = (current_line + " " + word).strip()
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    line_height = 55
    start_y = (H - len(lines) * line_height) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        draw.text((tx, start_y + i * line_height), line, fill='#ffffff', font=font_title)

    # Date (bottom)
    date_str = datetime.datetime.utcnow().strftime('%B %d, %Y')
    bbox = draw.textbbox((0, 0), date_str, font=font_sub)
    dw = bbox[2] - bbox[0]
    draw.text(((W - dw) // 2, H - 60), date_str, fill='#888888', font=font_sub)

    # Save
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    path = os.path.join(assets_dir, "substack_cover.png")
    img.save(path, quality=95)
    print(f"    [Cover] Generated: {path}")
    return path


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
        viewport_w = 1920  # ★ v14: 1920足够，sidebar input不需要在viewport内
        viewport_h = 1080
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=headless,
            slow_mo=slow_mo,
            viewport={"width": viewport_w, "height": viewport_h},
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
            current_url = page.url

            # More robust login detection
            # 1. Check for obvious logged-out indicators
            logged_out_indicators = [
                "Discover world class culture",
                "Browse top publications",
                "Sign in to your account",
                "Sign in to Substack",
            ]
            logged_in_indicators = [
                SUBSTACK_EMAIL,
                "broadcastmarketintelligence",
                "settings",
                "Your account",
            ]

            is_logged_out = any(ind in settings_text for ind in logged_out_indicators)
            is_logged_in = any(ind in settings_text for ind in logged_in_indicators)

            # 2. Check URL redirect
            if "/sign-in" in current_url or "/signin" in current_url or "/login" in current_url:
                is_logged_out = True

            if not is_logged_in or is_logged_out:
                print("  [Substack] ⚠️ SESSION EXPIRED - User not logged in")
                print("  [Substack] URL:", current_url)
                print("  [Substack] Body text snippet:", settings_text[:200])
                print("")
                print("  To fix this:")
                print("  1. Run: python login_substack_v7.py")
                print("  2. Substack will send Magic Link to your email")
                print("  3. Click the Magic Link to refresh session")
                print("  4. Re-run this script")
                print("")

                # Take screenshot for debugging
                page.screenshot(path=os.path.join(debug_dir, "substack_login_expired.png"))
                log_article("substack", article["title"], "session_expired_magic_link_required")
                return False, ""

            print("  [Substack] ✅ Login confirmed.")

            # === Step 2: Navigate to editor (FIXED v7) ===
            # Substack 2025+ 新UI流程：
            # 方法1：/publish/posts → Create → Article → 等待跳转到 /publish/post/{id}
            # 方法2：直接 /publish/post?type=newsletter → 等待跳转
            print("  [Substack] Opening editor (v7 fixed)...")
            
            editor_url = None

            # 方法1：从 /publish/posts → Create → Article
            print(f"    Going to {PUB_URL}/publish/posts...")
            page.goto(f"{PUB_URL}/publish/posts", timeout=60000)
            time.sleep(5)
            print(f"    URL: {page.url}")
            
            try:
                create_btns = page.locator('button:has-text("Create")').all()
                print(f"    Found {len(create_btns)} Create buttons")
                
                btn_to_click = create_btns[1] if len(create_btns) >= 2 else (create_btns[0] if create_btns else None)
                if btn_to_click:
                    btn_to_click.click()
                    time.sleep(2)
                    print(f"    Clicked Create button")
                    
                    # 从菜单中点 Article 链接
                    article_link = page.locator('a:has-text("Article")').first
                    if article_link.is_visible(timeout=5000):
                        article_link.click()
                        print(f"    Clicked Article link, waiting for redirect...")
                        # 等待 URL 变化到 /publish/post/{id}
                        try:
                            page.wait_for_url("**/publish/post/*", timeout=15000)
                        except Exception:
                            pass
                        time.sleep(3)
                        editor_url = page.url
                        print(f"    After Article: {editor_url}")
            except Exception as e:
                print(f"    Create→Article error: {e}")
            
            # 方法2：直接访问 Article 创建 URL，等待重定向
            if not editor_url or "/publish/post/" not in editor_url:
                print("    Trying direct /publish/post?type=newsletter...")
                page.goto(f"{PUB_URL}/publish/post?type=newsletter", timeout=60000)
                try:
                    page.wait_for_url("**/publish/post/*", timeout=15000)
                except Exception:
                    pass
                time.sleep(3)
                editor_url = page.url
                print(f"    Direct URL result: {editor_url}")

            # 方法3：substack.com/write（最后的备选）
            if not editor_url or "/publish/post/" not in editor_url:
                print("    Trying substack.com/write...")
                page.goto("https://substack.com/write", timeout=60000)
                try:
                    page.wait_for_url("**/publish/post/*", timeout=15000)
                except Exception:
                    pass
                time.sleep(3)
                editor_url = page.url
                print(f"    /write result: {editor_url}")

            # 最终检查
            if not editor_url or "/publish/post/" not in editor_url:
                page.screenshot(path=os.path.join(debug_dir, "substack_no_editor.png"))
                log_article("substack", article["title"], "no_editor_found")
                return False, ""

            print(f"    ✅ Editor URL: {editor_url}")

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

            # === Step 5: Upload cover image ===
            # ★ v14: 暂时跳过cover image上传——可能干扰发布流程
            print("  [Substack] Skipping cover image (v14 — debugging publish issue)...")
            cover_path = None  # 不上传cover image
            if cover_path and os.path.exists(cover_path):
                try:
                    # Substack cover image: the button triggers a file chooser dialog
                    # We must set up expect_file_chooser BEFORE clicking the button
                    cover_clicked = False
                    
                    # Strategy: set up file_chooser listener, then click the cover button
                    # Try multiple selectors for the cover button
                    cover_sels = [
                        'button:has-text("Add a cover image")',
                        'button:has-text("cover image")',
                        'a:has-text("Add a cover image")',
                        'div:has-text("Add a cover image")',
                    ]
                    
                    for sel in cover_sels:
                        try:
                            btn = page.locator(sel).first
                            if btn.is_visible(timeout=1000):
                                # Set up file chooser listener BEFORE clicking
                                with page.expect_file_chooser(timeout=10000) as fc_info:
                                    btn.click()
                                file_chooser = fc_info.value
                                file_chooser.set_files(cover_path)
                                cover_clicked = True
                                print(f"    Cover uploaded via: {sel}")
                                time.sleep(3)
                                break
                        except Exception as e:
                            print(f"    {sel} failed: {e}")
                            continue
                    
                    if not cover_clicked:
                        # Last resort: try hidden file input (some Substack versions have one)
                        try:
                            file_inputs = page.locator('input[type="file"]').all()
                            if file_inputs:
                                file_inputs[0].set_input_files(cover_path)
                                cover_clicked = True
                                print("    Cover uploaded via hidden file input!")
                                time.sleep(3)
                        except Exception as e:
                            print(f"    Hidden file input failed: {e}")
                    
                    if not cover_clicked:
                        print("    ⚠️ No cover button found, skipping cover image")
                except Exception as e:
                    print(f"    Cover upload failed: {e}")
            else:
                print("    No cover image generated, skipping")

            # === Step 6: Fill title & content (v15 — API set title + page.reload + native setter fallback) ===
            # ★ v15 根本性修复（基于成功发布 ID:196882839 的逆向分析）：
            # 1. 先用 API PUT 设置 draft_title（服务端持久化）
            # 2. ★ page.reload() 让 React state 从 API 数据重新初始化（关键！）
            #    - 成功版本做了 reload，失败版本没有
            #    - React 内部 state 和 DOM 值不一致时，publish API 读的是 React state
            #    - reload 让 React 从服务端数据重建 state，确保一致性
            # 3. reload 后如果 sidebar input 仍为空，用 native setter + InputEvent 补设
            # 4. 不使用 route 拦截器（会阻止 POST /publish API 调用）
            print("  [Substack] Filling title + content (v15 API + reload)...")
            
            # 提取 post_id from editor_url
            post_id_match = re.search(r'/publish/post/(\d+)', editor_url)
            post_id = post_id_match.group(1) if post_id_match else None
            print(f"    Post ID: {post_id}")
            
            # === Step 6a: 先用 ProseMirror 填写正文内容 ===
            # ★ 先填内容，再设标题（避免标题设置后被内容操作干扰）
            content_done = False
            try:
                result = page.evaluate('''(data) => {
                    const editor = document.querySelector('.ProseMirror[contenteditable="true"]');
                    if (!editor) return {found: false};
                    let html = '';
                    if (data.subtitle) html += '<h3>' + data.subtitle + '</h3>';
                    const paras = data.content.split('\\n');
                    for (const p of paras) {
                        if (p.trim()) html += '<p>' + p + '</p>';
                    }
                    editor.innerHTML = html;
                    editor.dispatchEvent(new Event('input', {bubbles: true}));
                    return {found: true, chars: html.length};
                }''', {"title": article["title"], "subtitle": article.get("subtitle", ""), "content": article["content"]})
                if result and result.get("found"):
                    content_done = True
                    print(f"    ProseMirror content set: {result.get('chars')} chars")
                else:
                    print(f"    ⚠️ ProseMirror innerHTML failed: {result}")
            except Exception as e:
                print(f"    ProseMirror innerHTML error: {e}")

            # 备用 — keyboard.type 输入
            if not content_done:
                try:
                    editor_el = page.locator('.ProseMirror[contenteditable="true"]').first
                    if editor_el.is_visible(timeout=5000):
                        editor_el.click()
                        time.sleep(0.5)
                        paragraphs = article["content"].split("\n")
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
                        content_done = True
                        print(f"    Content typed in ProseMirror (keyboard)")
                except Exception as e:
                    print(f"    ProseMirror keyboard fill error: {e}")

            if not content_done:
                print("    ⚠️ WARNING: ProseMirror content fill failed!")
            
            # 等内容自动保存
            print("    Waiting for content auto-save...")
            time.sleep(5)
            
            # === Step 6b: 用 API PUT 设置 draft_title（服务端持久化）===
            # ★ 这是成功发布版本的关键第一步
            if post_id:
                try:
                    api_result = page.evaluate('''async (params) => {
                        try {
                            const resp = await fetch(`/api/v1/drafts/${params.postId}`, {
                                method: 'PUT',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({
                                    draft_title: params.title,
                                    draft_subtitle: params.subtitle || ''
                                })
                            });
                            const status = resp.status;
                            const data = await resp.json();
                            return {status: status, draft_title: data.draft_title || ''};
                        } catch(e) {
                            return {error: e.message};
                        }
                    }''', {"postId": post_id, "title": article["title"], "subtitle": article.get("subtitle", "")})
                    print(f"    API title set: {api_result}")
                except Exception as e:
                    print(f"    API title set error: {e}")
            
            # === Step 6c: ★ page.reload() 让 React state 从 API 数据重建 ===
            # ★★★ 这是成功版本的关键差异！★★★
            # 没有这一步，React 的内部 state 和 DOM 值不一致，
            # publish API 读的是 React state 而非 DOM，导致标题丢失
            print("    ★ Reloading editor to sync React state from API...")
            try:
                page.reload(timeout=30000)
                time.sleep(5)  # 等页面完全加载
                
                # 检查 sidebar input 是否从 API 加载了标题
                sidebar_val = page.evaluate('''() => {
                    const input = document.querySelector('input[placeholder*="title"], input[placeholder*="Title"]');
                    return input ? input.value : 'NO_INPUT';
                }''')
                print(f"    Sidebar input after reload: '{str(sidebar_val)[:60]}'")
                
                if sidebar_val and article["title"][:20] in str(sidebar_val):
                    print("    ✅ Title loaded from API after reload!")
                else:
                    # ★ reload 后 sidebar 仍为空，用 native setter + InputEvent 补设
                    print("    ⚠️ Sidebar still empty after reload — trying native setter + InputEvent...")
                    try:
                        page.evaluate('''(titleText) => {
                            const input = document.querySelector('input[placeholder*="title"], input[placeholder*="Title"]');
                            if (!input) return;
                            input.focus();
                            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            nativeSetter.call(input, titleText);
                            const inputEvent = new InputEvent('input', {
                                bubbles: true, cancelable: true, composed: true,
                                inputType: 'insertText', data: titleText
                            });
                            input.dispatchEvent(inputEvent);
                            input.dispatchEvent(new Event('change', {bubbles: true}));
                            input.blur();
                        }''', article["title"])
                        time.sleep(1)
                        verify_val = page.evaluate('''() => {
                            const input = document.querySelector('input[placeholder*="title"], input[placeholder*="Title"]');
                            return input ? input.value : 'NO_INPUT';
                        }''')
                        print(f"    After native setter: '{str(verify_val)[:60]}'")
                    except Exception as e:
                        print(f"    Native setter fallback error: {e}")
            except Exception as e:
                print(f"    Page reload error: {e}")
            
            # === Step 6d: 最终验证标题状态 ===
            if post_id:
                try:
                    final_check = page.evaluate('''async (postId) => {
                        const resp = await fetch(`/api/v1/drafts/${postId}`);
                        const data = await resp.json();
                        return {draft_title: data.draft_title || '', is_published: data.is_published || false};
                    }''', post_id)
                    print(f"    Draft before publish: draft_title='{str(final_check.get('draft_title', ''))[:40]}', is_published={final_check.get('is_published')}")
                except Exception as e:
                    print(f"    Final check error: {e}")

            # === Step 7: Publish (v15 — API + reload ensures React state sync) ===
            # ★ v15: page.reload() 已确保 React state 和 API 数据一致
            # 不需要额外 blur sync，直接发布
            
            time.sleep(3)  # 短暂等待确保页面稳定
            published = False

            # Step 7a: 点击 Continue/Publish 按钮
            print("    [7a] Looking for Continue/Publish button...")
            continue_btn_sels = [
                'button:has-text("Continue")',                # 最可靠：实际测试可见
                '[data-testid="publish-button"]',             # testid（注意不是 publish-button-wtooltip）
                'button:has-text("Publish")',
                '[data-testid="publish-button-wtooltip"]',    # 旧版 testid，可能不可见
            ]

            clicked_continue = False
            for sel in continue_btn_sels:
                try:
                    btn = page.locator(sel).first
                    # 先检查是否可见
                    if not btn.is_visible(timeout=3000):
                        continue
                    # 检查是否 disabled（内容为空时按钮禁用）
                    is_disabled = btn.is_disabled(timeout=2000)
                    if is_disabled:
                        print(f"    ⚠️ Button {sel} is DISABLED (content may not be saved yet)")
                        # 等更久再试
                        time.sleep(5)
                        is_disabled = btn.is_disabled(timeout=2000)
                        if is_disabled:
                            print(f"    ⚠️ Still disabled after wait, trying force click...")
                    
                    btn.click(force=True)  # force=True 绕过 disabled
                    clicked_continue = True
                    print(f"    Clicked Continue: {sel} (disabled={is_disabled})")
                    time.sleep(4)
                    break
                except Exception as e:
                    print(f"    {sel}: {e}")
                    continue

            if not clicked_continue:
                print("    ⚠️ No Continue button found, screenshotting...")
                page.screenshot(path=os.path.join(debug_dir, "substack_no_continue_btn.png"))

            # Step 7b: 点击 "Send to everyone now" 完成发布
            print("    [7b] Looking for Send/Publish button in dialog...")
            time.sleep(8)  # ★ v14: 等更久让发布对话框完全渲染

            # Retry logic: dialog may take time to appear in headless CI
            send_sels = [
                'button:has-text("Send to everyone now")',
                'button:has-text("Publish now")',
                '[role="button"]:has-text("Send to everyone now")',
                'button:has-text("Send")',
            ]

            for attempt in range(3):
                for sel in send_sels:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=8000):
                            btn.click()
                            published = True
                            print(f"    ✅ Clicked send button: {sel} (attempt {attempt+1})")
                            time.sleep(5)

                            # 可能还有确认对话框
                            for csel in ['button:has-text("Confirm")', 'button:has-text("Yes")']:
                                try:
                                    cb = page.locator(csel).first
                                    if cb.is_visible(timeout=3000):
                                        cb.click()
                                        time.sleep(3)
                                        break
                                except Exception:
                                    continue
                            break
                    except Exception:
                        continue
                
                if published:
                    break
                
                # Take screenshot for debugging
                page.screenshot(path=os.path.join(debug_dir, f"substack_6b_attempt{attempt+1}.png"))
                print(f"    ⚠️ Send button not found (attempt {attempt+1}/3), retrying...")
                time.sleep(5)

            if not published:
                # 最终兜底：检查 URL 或 Ctrl+S 保存草稿
                current_url = page.url
                if "/p/" in current_url and "/publish/" not in current_url:
                    print(f"    ✅ Published (detected from URL)! URL: {current_url}")
                    published = True
                else:
                    print("    ⚠️ Could not publish, saving as draft...")
                    page.keyboard.press("Control+s")
                    time.sleep(2)

            # === Step 9: Post-publish title verification (v15) ===
            # ★ v15: API + page.reload() 确保 React state 同步，标题应正确保留
            time.sleep(5)
            if published and post_id:
                print("  [Substack] Post-publish title verification...")
                try:
                    recheck = page.evaluate('''async (params) => {
                        const checkResp = await fetch(`/api/v1/drafts/${params.postId}`);
                        const checkData = await checkResp.json();
                        return {
                            draft_title: checkData.draft_title || '',
                            title: checkData.title || '',
                            is_published: checkData.is_published || false,
                            post_url: checkData.post_url || ''
                        };
                    }''', {"postId": post_id, "title": article["title"], "subtitle": article.get("subtitle", "")})
                    print(f"    Post-publish API check: {recheck}")
                    
                    if recheck.get("is_published") and recheck.get("title"):
                        print("    ✅ Article published with title!")
                    elif recheck.get("is_published") and not recheck.get("title"):
                        print("    ⚠️ Published but title is empty — may need API fix")
                        # 尝试API PUT修复
                        try:
                            fix_result = page.evaluate('''async (params) => {
                                const resp = await fetch(`/api/v1/drafts/${params.postId}`, {
                                    method: 'PUT',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({
                                        draft_title: params.title,
                                        draft_subtitle: params.subtitle || ''
                                    })
                                });
                                const data = await resp.json();
                                return {status: resp.status, draft_title: data.draft_title || ''};
                            }''', {"postId": post_id, "title": article["title"], "subtitle": article.get("subtitle", "")})
                            print(f"    Post-publish API fix: {fix_result}")
                        except Exception as e:
                            print(f"    Post-publish API fix error: {e}")
                    elif not recheck.get("is_published"):
                        print("    ⚠️ Article not published — publish may have failed")
                except Exception as e:
                    print(f"    Post-publish check error: {e}")

            # === Step 10: Verify publish by checking Published list ===
            # ★ 关键修复：点击 "Send to everyone now" 不等于真的发布了！
            # 必须去 Published 列表确认文章是否真的出现，否则是进草稿了
            time.sleep(8)  # Wait for Substack to process (增加等待时间)
            final_url = page.url
            print(f"    Post-publish URL: {final_url}")

            if published:
                # Verify by checking the Published posts list
                print("  [Substack] Verifying publish status in Published list...")
                try:
                    page.goto(f"{PUB_URL}/publish/posts/published", timeout=15000)
                    time.sleep(6)  # 等列表加载完成
                    
                    # 用更宽松的匹配：取标题前3个词做关键词
                    title_words = article["title"].split()[:3]
                    title_prefix = " ".join(title_words)
                    
                    page_text = page.evaluate('''() => document.body.innerText''')
                    
                    # 多种匹配策略：完整前30字符 / 前3词 / 前15字符
                    matched = False
                    for check_str in [article["title"][:30], title_prefix, article["title"][:15]]:
                        if check_str and check_str in page_text:
                            matched = True
                            break
                    
                    if matched:
                        print(f"    ✅ VERIFIED: Article '{article['title'][:40]}' is in Published list!")
                        # Try to get public URL
                        public_url = page.evaluate('''(titlePrefix) => {
                            var links = document.querySelectorAll('a');
                            for (var i = 0; i < links.length; i++) {
                                var href = links[i].getAttribute('href') || '';
                                if (href.indexOf('/p/') !== -1 && href.indexOf('/publish/') === -1) {
                                    var text = links[i].textContent.trim();
                                    if (text.indexOf(titlePrefix) !== -1) return href;
                                }
                            }
                            return '';
                        }''', title_words[0] if title_words else article["title"][:10])
                        if public_url:
                            final_url = public_url if public_url.startswith("http") else f"https://{PUBLICATION_SLUG}.substack.com{public_url}"
                            print(f"    Public URL: {final_url}")
                        else:
                            print("    ✅ Published (couldn't extract public URL)")
                    else:
                        # Article NOT in published list — check if still processing
                        print(f"    ⚠️ Not found in Published list yet, checking for 'Untitled' entries...")
                        # 可能刚发布还在索引中，等更久重试一次
                        time.sleep(10)
                        page.reload(timeout=15000)
                        time.sleep(6)
                        page_text2 = page.evaluate('''() => document.body.innerText''')
                        
                        matched2 = False
                        for check_str in [article["title"][:30], title_prefix, article["title"][:15]]:
                            if check_str and check_str in page_text2:
                                matched2 = True
                                break
                        
                        if matched2:
                            print(f"    ✅ VERIFIED (2nd try): Article is in Published list!")
                        else:
                            # 最终检查：是否文章名变成了 Untitled
                            if "Untitled" in page_text2:
                                print(f"    ⚠️ Found 'Untitled' entries — sidebar title may not have saved!")
                            print(f"    ⚠️ VERIFICATION FAILED: '{article['title'][:40]}' NOT in Published list!")
                            # 检查是否实际已通过post URL发布成功
                            published = False
                            # Check drafts
                            page.goto(f"{PUB_URL}/publish/posts/drafts", timeout=15000)
                            time.sleep(4)
                            draft_text = page.evaluate('''() => document.body.innerText''')
                            for check_str in [article["title"][:20], title_prefix, article["title"][:15]]:
                                if check_str and check_str in draft_text:
                                    print(f"    ⚠️ CONFIRMED: Article is in DRAFTS — publish failed")
                                    break
                            else:
                                print("    ⚠️ Article not found in drafts either (may still be processing)")
                except Exception as e:
                    print(f"    Verification error: {e}")
            else:
                # Not published — at least check drafts
                try:
                    page.goto(f"{PUB_URL}/publish/posts/drafts", timeout=15000)
                    time.sleep(3)
                    print("    ⚠️ Article saved as draft (publish button not found)")
                except Exception:
                    pass

            print(f"    Final URL: {final_url}")
            log_article("substack", article["title"], "published" if published else "draft_only", final_url)

            return published, final_url

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
        print("[Test Mode] Checking login only (no post will be published)...\n")
        from playwright.sync_api import sync_playwright as _pw
        user_data_dir = os.path.join(SESSION_DIR, "substack_profile")
        os.makedirs(user_data_dir, exist_ok=True)
        with _pw() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=IS_CI,
                slow_mo=100 if not IS_CI else 50,
                viewport={"width": 2560, "height": 1440},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            page.goto("https://substack.com/settings", timeout=60000)
            time.sleep(5)
            for wait in range(30):
                title = page.title()
                if all(x not in title for x in ["稍候", "Checking", "Just a moment", "Attention"]):
                    break
                time.sleep(2)
            settings_text = page.locator("body").inner_text(timeout=5000)
            logged_in = any(ind in settings_text for ind in [SUBSTACK_EMAIL, "broadcastmarketintelligence", "Your account"])
            context.close()
            print(f"\nLogin: {'✅ OK' if logged_in else '❌ FAILED'}")
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
