"""
BroadFSC TikTok Auto-Poster v5 — Viral Finance Content Engine

COMPLETE REWRITE based on viral TikTok finance creator analysis:
- 12 hook frameworks (Pattern Interrupt, Pain First, Myth vs Fact, etc.)
- 5-part retention engine (Hook → Promise → Body → Midpoint Hook → CTA)
- 8 content categories x 3 variants each = 24 scripts in rotation
- Human-like conversational tone (anti-AI-detection optimized)
- Visual style matching top faceless finance creators:
    Large bold text cards with scene numbers
    Midpoint retention hooks ("But here's what most people miss...")
    Progress indicator bar
    Clean dark background (NO more noisy particles)
- Edge TTS voice + karaoke subtitles
- NO background music (clean voice-only, user feedback: "music too noisy")

Postproxy API: https://postproxy.dev/reference/posts/
Environment variables:
  POSTPROXY_API_KEY - Required
  GROQ_API_KEY - Optional. For AI-generated scripts
  TELEGRAM_BOT_TOKEN - Optional. For notifications
  TELEGRAM_CHANNEL_ID - Optional. For notifications
"""

import os
import sys
import datetime
import requests
import json
import random
import struct
import math
import io
import asyncio
import subprocess
import tempfile

# Analytics tracking
try:
    from analytics_logger import log_post
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import imageio.v2 as iio
    import numpy as np
    HAS_IMAGEIO = True
except ImportError:
    HAS_IMAGEIO = False

try:
    import edge_tts
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
POSTPROXY_API_KEY = os.environ.get("POSTPROXY_API_KEY", "")
POSTPROXY_BASE_URL = "https://api.postproxy.dev/api"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

WEBSITE_LINK = "https://www.broadfsc.com/different"
TELEGRAM_LINK = "https://t.me/BroadFSC"

# Video settings — optimized for TikTok algorithm
W, H = 1088, 1920  # 9:16, width divisible by 16
FPS = 30

# TTS voice config — 28yo male finance voice for credibility
TTS_VOICE = "en-US-GuyNeural"
TTS_VOICE_ALT = "en-US-AriaNeural"
TTS_RATE = "+5%"

# ============================================================
# Color Palette v5 — Clean & Bold (matching top creators)
# ============================================================
C = {
    "bg":      (8,  10,  18),   # near-black background
    "bg2":     (14, 17,  30),   # slightly lighter panels
    "accent":  (56, 134, 255),  # electric blue
    "green":   (0,  214, 130),  # profit green
    "gold":    (255, 196, 0),   # gold highlight
    "red":     (255,  60,  60), # loss red
    "white":   (255, 255, 255),
    "gray":    (130, 145, 175),
    "dim":     (50,  58,  85),
    "kara_hi": (255, 200, 50),  # karaoke highlight (gold)
    "kara_lo": (100, 115, 150), # karaoke inactive
}

# ============================================================
# v5 SCRIPT LIBRARY — 24 scripts across 8 viral content types
#
# Each script follows the 5-part retention engine:
#   hook      → pattern interrupt (first 3 seconds)
#   promise   → what they'll learn (sets expectation)
#   body      → 2-3 punchy facts/insights
#   midpoint  → re-engagement hook ("but wait...")
#   cta       → clear action
#
# Content types rotated:
#   A) Myth Buster   B) Market Signal  C) Wealth Principle
#   D) Mistake Alert E) Beginner Truth F) Sector Spotlight
#   G) Psychology    H) Numbers Tell
# ============================================================
SCRIPTS = [

    # ── TYPE A: MYTH BUSTER ──────────────────────────────────
    {
        "type": "myth",
        "hook": "That investing advice you heard is wrong.",
        "promise": "Here's what the data actually says.",
        "body": [
            "Myth: you need a lot of money to start investing.",
            "Reality: dollar cost averaging with fifty dollars a month beats trying to time a big lump sum.",
            "Compound interest doesn't care how you started. It cares that you started.",
        ],
        "midpoint": "But here's the part nobody tells beginners.",
        "midpoint_detail": "The biggest returns don't come from picking winners. They come from not selling losers.",
        "cta": "Save this. Share it with someone who keeps waiting to start.",
        "hashtags": "#investing #beginners #wealthbuilding #money #finance",
    },
    {
        "type": "myth",
        "hook": "Stop. You've been lied to about the stock market.",
        "promise": "Three myths that cost average investors thousands every year.",
        "body": [
            "Myth one: buying low and selling high sounds easy. In practice, seventy percent of retail traders lose money trying.",
            "Myth two: you need to watch the market every day. Actually, the less you check, the better your returns.",
            "Myth three: a good company equals a good stock. Price paid matters more than company quality.",
        ],
        "midpoint": "So what actually works?",
        "midpoint_detail": "Boring, consistent, diversified investing. Every time. It's not exciting but it's how wealth is built.",
        "cta": "Follow for more truths the financial industry doesn't want you to know.",
        "hashtags": "#stockmarket #investing #myths #personalfinance #money",
    },
    {
        "type": "myth",
        "hook": "Real talk: active trading is a losing game.",
        "promise": "And the numbers back this up completely.",
        "body": [
            "Over twenty years, over ninety percent of actively managed funds underperformed their benchmark index.",
            "The funds that do beat the market one year rarely do it the next.",
            "Meanwhile a simple S&P five hundred index fund has returned around ten percent annually on average.",
        ],
        "midpoint": "Wait, but what about the people who do beat the market?",
        "midpoint_detail": "Most are just lucky. Survivorship bias makes us see the winners. Not the thousands who failed.",
        "cta": "Follow for data-driven investing breakdowns.",
        "hashtags": "#indexfunds #passiveinvesting #SP500 #finance #wealthbuilding",
    },

    # ── TYPE B: MARKET SIGNAL ────────────────────────────────
    {
        "type": "signal",
        "hook": "Something quiet is happening in global markets.",
        "promise": "Most retail investors won't notice until it's too late.",
        "body": [
            "When the U.S. dollar weakens, emerging market stocks historically outperform.",
            "Dollar's been sliding for three straight months now.",
            "Smart money is already repositioning into international exposure.",
        ],
        "midpoint": "But there's a catch most people miss.",
        "midpoint_detail": "Currency risk cuts both ways. Gains can be wiped out by exchange rate moves if you're not careful.",
        "cta": "Follow for daily global market signals explained simply.",
        "hashtags": "#forex #emergingmarkets #investing #globalmarkets #finance",
    },
    {
        "type": "signal",
        "hook": "The bond market is flashing a warning sign.",
        "promise": "And historically this has always preceded a major shift.",
        "body": [
            "When short-term treasury yields exceed long-term ones, that's called an inverted yield curve.",
            "It's happened before every U.S. recession in the past fifty years.",
            "Right now? The curve has been inverted for over a year.",
        ],
        "midpoint": "Here's what smart investors are actually doing about it.",
        "midpoint_detail": "Shortening bond duration, holding more cash, and looking at defensive sectors like healthcare and utilities.",
        "cta": "Follow to stay ahead of what the market is really telling us.",
        "hashtags": "#bonds #yieldcurve #recession #investing #macroeconomics",
    },
    {
        "type": "signal",
        "hook": "Gold is doing something it hasn't done in years.",
        "promise": "And it's not just about inflation this time.",
        "body": [
            "Central banks around the world bought more gold last year than any year since nineteen fifty.",
            "China, India, and the Middle East are all de-dollarizing slowly.",
            "Gold isn't just an inflation hedge anymore. It's a geopolitical hedge.",
        ],
        "midpoint": "But should you actually buy gold right now?",
        "midpoint_detail": "Gold pays no dividends and has long dead periods. Most advisors recommend five to ten percent max of any portfolio.",
        "cta": "Follow for balanced takes on every asset class.",
        "hashtags": "#gold #investing #inflation #commodities #portfoliostrategy",
    },

    # ── TYPE C: WEALTH PRINCIPLE ─────────────────────────────
    {
        "type": "principle",
        "hook": "One financial habit separates the wealthy from everyone else.",
        "promise": "And it has nothing to do with picking stocks.",
        "body": [
            "They pay themselves first. Before bills. Before fun. Before anything.",
            "Set up an automatic transfer to your investment account on payday.",
            "Then live on what's left. Not save what's left.",
        ],
        "midpoint": "Here's the psychology behind why this works.",
        "midpoint_detail": "When money hits your account you don't miss what you never saw. Automation removes the willpower requirement entirely.",
        "cta": "Start with one percent if that's all you can do. Just start. Follow for more.",
        "hashtags": "#wealthbuilding #personalfinance #savingmoney #habits #investing",
    },
    {
        "type": "principle",
        "hook": "Rich people buy assets. Everyone else buys liabilities.",
        "promise": "Robert Kiyosaki made this famous. Here's the actual breakdown.",
        "body": [
            "An asset puts money in your pocket. Stocks, rental property, a business.",
            "A liability takes money out of your pocket. Car payments, credit card debt, subscriptions you forgot about.",
            "Most people's biggest purchase is a house. But a house you live in is technically a liability.",
        ],
        "midpoint": "Wait, does that mean don't buy a house?",
        "midpoint_detail": "Not necessarily. But understand what you're buying. A home is lifestyle. An investment property is an asset. They're different.",
        "cta": "Follow for clear explanations of wealth concepts.",
        "hashtags": "#assets #liabilities #cashflow #realestate #wealthmindset",
    },
    {
        "type": "principle",
        "hook": "The rule of seventy two is the most powerful math in finance.",
        "promise": "And most people have never heard of it.",
        "body": [
            "Divide seventy two by your annual return rate. That's how many years to double your money.",
            "At eight percent returns, your money doubles every nine years.",
            "At twelve percent, every six years. Starting at thirty, you could double three or four times before retirement.",
        ],
        "midpoint": "Now here's where it gets really interesting.",
        "midpoint_detail": "The same rule works in reverse for debt. At eighteen percent credit card interest, your debt doubles every four years. That's why minimum payments are a trap.",
        "cta": "Share this with anyone still carrying credit card debt. Follow for more.",
        "hashtags": "#ruleof72 #compoundinterest #investing #debt #financialliteracy",
    },

    # ── TYPE D: MISTAKE ALERT ────────────────────────────────
    {
        "type": "mistake",
        "hook": "I see investors make this mistake every single week.",
        "promise": "And it silently destroys long-term returns.",
        "body": [
            "They panic sell during market drops. Then wait for it to feel safe before buying back in.",
            "Problem: by the time it feels safe, the market has already recovered thirty to forty percent.",
            "Missing just the ten best days in the market over twenty years cuts your total return in half.",
        ],
        "midpoint": "So what should you actually do when markets crash?",
        "midpoint_detail": "Nothing. Or buy more if you can. Every major crash in history has fully recovered. Every single one.",
        "cta": "Screenshot this for the next time you want to panic sell. Follow.",
        "hashtags": "#investing #panicSelling #stockmarket #longterminvesting #wealthbuilding",
    },
    {
        "type": "mistake",
        "hook": "Most people invest backwards. Here's what I mean.",
        "promise": "A mistake so common it's basically taught as normal.",
        "body": [
            "They put their safe money in savings accounts earning one percent.",
            "And they put their risky money in speculative stocks chasing ten X.",
            "Result: the boring money stays boring. The risky money gets wiped out.",
        ],
        "midpoint": "The flip works better for most people.",
        "midpoint_detail": "Put the bulk in index funds. Keep a small portion for higher risk plays if you want the excitement. Not the other way around.",
        "cta": "Is this you? Comment below. Follow for a full breakdown.",
        "hashtags": "#investingmistakes #portfolioallocation #indexfunds #stockmarket #finance",
    },
    {
        "type": "mistake",
        "hook": "Chasing dividend yield is a trap most beginners fall into.",
        "promise": "Here's what the high yield is actually hiding.",
        "body": [
            "A ten percent dividend yield sounds amazing. But ask why it's that high.",
            "Usually it means the stock price dropped significantly. The yield went up because the price went down.",
            "Companies in trouble often cut dividends suddenly. You get no income and a capital loss.",
        ],
        "midpoint": "So dividends are bad? No, that's not what I'm saying.",
        "midpoint_detail": "Look for dividend growth, not just high current yield. A company growing its dividend five percent yearly is far more valuable long term.",
        "cta": "Follow for dividend investing done right.",
        "hashtags": "#dividends #investing #passiveincome #dividendstocks #finance",
    },

    # ── TYPE E: BEGINNER TRUTH ───────────────────────────────
    {
        "type": "beginner",
        "hook": "If I was starting investing from zero today, here's exactly what I'd do.",
        "promise": "Step by step. No fluff.",
        "body": [
            "Step one: build a three month emergency fund in a high yield savings account first. Don't touch this.",
            "Step two: invest in a total market index fund. Something like V T I or equivalent. Set up automatic contributions.",
            "Step three: never look at it more than once a quarter.",
        ],
        "midpoint": "That's it. Really?",
        "midpoint_detail": "Yes. The complicated stuff is for people who want to feel smart. This is for people who actually want to build wealth.",
        "cta": "Save this. Share it with someone who asked you how to start. Follow.",
        "hashtags": "#beginnerinvesting #howtostart #indexfunds #personalfinance #wealthbuilding",
    },
    {
        "type": "beginner",
        "hook": "Nobody explained taxes to me when I started investing. Huge mistake.",
        "promise": "Three things about investment taxes you should know before you start.",
        "body": [
            "One: long term capital gains are taxed lower than short term. Hold assets over a year when possible.",
            "Two: tax-advantaged accounts like four oh one Ks and IRAs grow tax-free or tax-deferred. Use them first.",
            "Three: tax-loss harvesting. You can sell losing positions to offset gains. It's legal. Most beginners don't know this.",
        ],
        "midpoint": "And the one move that changes everything.",
        "midpoint_detail": "Max out your retirement accounts before investing in a regular brokerage. The tax savings compound just like returns.",
        "cta": "Follow for investing concepts schools never taught you.",
        "hashtags": "#taxes #investing #401k #IRA #financialeducation",
    },
    {
        "type": "beginner",
        "hook": "The difference between investing at twenty five versus thirty five is insane.",
        "promise": "Let me show you the actual numbers.",
        "body": [
            "Invest two hundred dollars a month starting at twenty five: at sixty five you have over six hundred thousand assuming eight percent returns.",
            "Wait until thirty five to start the same thing: you end up with less than three hundred thousand.",
            "Same amount invested. Same returns. A ten year delay costs you over three hundred thousand dollars.",
        ],
        "midpoint": "But what if you're already past twenty five?",
        "midpoint_detail": "Start today anyway. The second best time to plant a tree is right now. Every year you wait costs more than the last.",
        "cta": "Follow. Share this with a younger sibling or friend who needs to hear it.",
        "hashtags": "#compoundinterest #investing #youngadults #wealthbuilding #finance",
    },

    # ── TYPE F: SECTOR SPOTLIGHT ─────────────────────────────
    {
        "type": "sector",
        "hook": "One sector has quietly outperformed every other for thirty years.",
        "promise": "And almost no one talks about it.",
        "body": [
            "Healthcare. Not just pharma. Medical devices, insurance, biotech, healthcare REITs.",
            "Aging population, chronic disease rates rising, new drugs in development. The tailwinds are structural.",
            "And unlike tech, healthcare demand doesn't shrink during recessions. People still get sick.",
        ],
        "midpoint": "But healthcare stocks seem complicated and risky, right?",
        "midpoint_detail": "ETFs make this easy. Something like X L V gives you diversified healthcare exposure without picking individual stocks.",
        "cta": "Follow for weekly sector breakdowns.",
        "hashtags": "#healthcare #investing #ETF #sectorinvesting #longterminvesting",
    },
    {
        "type": "sector",
        "hook": "AI is real. But most people are investing in it wrong.",
        "promise": "Here's where the smart money is actually flowing.",
        "body": [
            "Everyone buys the obvious names: the big tech companies everyone's already heard of.",
            "But the picks and shovels play is different. Semiconductors, cooling systems, data center REITs, energy infrastructure.",
            "AI needs electricity, chips, and cooling. Those businesses profit regardless of which AI company wins.",
        ],
        "midpoint": "What does this mean for regular investors?",
        "midpoint_detail": "Look at semiconductor ETFs and data infrastructure plays. Less headline risk, more stable cash flows, still massive upside.",
        "cta": "Follow for AI investing breakdowns that go beyond the obvious.",
        "hashtags": "#AI #artificialintelligence #semiconductors #techstocks #investing",
    },
    {
        "type": "sector",
        "hook": "Real estate without owning property is possible. Here's how.",
        "promise": "REITs explained in under sixty seconds.",
        "body": [
            "A REIT is a company that owns income-producing real estate. Shopping malls, apartments, warehouses, cell towers.",
            "By law they must pay out ninety percent of taxable income as dividends.",
            "You get real estate exposure, regular income, and full liquidity. You can sell your shares anytime.",
        ],
        "midpoint": "What's the catch?",
        "midpoint_detail": "REITs are sensitive to interest rates. When rates rise, REIT prices often drop. But long term, they've delivered strong total returns.",
        "cta": "Follow for simple explanations of every major investment type.",
        "hashtags": "#REITs #realestate #passiveincome #dividends #investing",
    },

    # ── TYPE G: PSYCHOLOGY ───────────────────────────────────
    {
        "type": "psychology",
        "hook": "Your brain is literally wired to make you lose money.",
        "promise": "Three cognitive biases that destroy investment returns.",
        "body": [
            "Loss aversion. Losing one hundred dollars hurts twice as much as gaining one hundred feels good. This makes us sell winners too early and hold losers too long.",
            "Recency bias. Whatever just happened feels permanent. Markets crash and we think it's over forever. Markets rally and we think it'll never stop.",
            "Overconfidence. After a few wins, everyone thinks they've found an edge. They haven't. The market humbles everyone eventually.",
        ],
        "midpoint": "How do you fight your own brain?",
        "midpoint_detail": "Systems beat willpower. Automate your contributions. Set rules before you invest. Don't make decisions when markets are moving fast.",
        "cta": "Follow for the psychology side of investing nobody talks about.",
        "hashtags": "#investingpsychology #behavioralfinance #biases #stockmarket #mindset",
    },
    {
        "type": "psychology",
        "hook": "FOMO has destroyed more portfolios than any market crash.",
        "promise": "Here's exactly how it plays out every cycle.",
        "body": [
            "Asset starts rising. Early buyers brag. You hear about it. You hesitate.",
            "It keeps rising. You feel stupid for missing it. You buy at the top.",
            "It crashes. You hold hoping it comes back. It doesn't come back to where you bought. You sell at a loss.",
        ],
        "midpoint": "Sound familiar? Here's the pattern break.",
        "midpoint_detail": "If you missed the move, you missed it. Accept it. The next opportunity isn't the same asset at a higher price. It's a completely different trade.",
        "cta": "Share this with someone who needed to hear it. Follow.",
        "hashtags": "#FOMO #investing #stockmarket #tradingpsychology #wealthbuilding",
    },
    {
        "type": "psychology",
        "hook": "Checking your portfolio every day is making you worse at investing.",
        "promise": "And there's actual research to prove it.",
        "body": [
            "A study found that investors who checked their portfolios daily made thirty percent less than those who checked quarterly.",
            "More information led to more trading. More trading led to more fees and worse timing.",
            "The best investors in history held for years or decades. Buffett's favorite holding period is forever.",
        ],
        "midpoint": "But what if something goes wrong?",
        "midpoint_detail": "Set rules in advance. A stop loss. A rebalancing trigger. Then automate and step away. Rules beat real-time emotions every time.",
        "cta": "Follow for investing discipline principles that actually work.",
        "hashtags": "#investingdiscipline #longterminvesting #portfoliomanagement #behavioralfinance #money",
    },

    # ── TYPE H: NUMBERS TELL ─────────────────────────────────
    {
        "type": "numbers",
        "hook": "These five numbers tell you everything about a stock.",
        "promise": "No finance degree needed.",
        "body": [
            "Price to earnings ratio. How much you pay per dollar of profit. Lower is usually cheaper.",
            "Revenue growth. Is the company actually getting bigger? Flat revenue is a red flag.",
            "Free cash flow. Profit that's actually real cash, not accounting tricks.",
        ],
        "midpoint": "Two more numbers most retail investors ignore.",
        "midpoint_detail": "Debt to equity ratio. High debt is fine in low rate environments, dangerous when rates rise. And insider ownership. If executives are buying shares with their own money, that's a good sign.",
        "cta": "Follow for stock analysis breakdowns every week.",
        "hashtags": "#stockanalysis #fundamentalanalysis #investing #stocks #finance",
    },
    {
        "type": "numbers",
        "hook": "Forty seven percent of Americans have zero stock market exposure.",
        "promise": "Here's what that actually means for their financial future.",
        "body": [
            "Over the last one hundred years the U.S. stock market has returned roughly ten percent annually before inflation.",
            "Someone who invested one thousand dollars in nineteen twenty four would have over five million dollars today.",
            "The people with zero market exposure are relying entirely on Social Security and savings accounts.",
        ],
        "midpoint": "But stock markets are risky, people say.",
        "midpoint_detail": "Yes, short term. Zero risk long term is actually the bigger risk. Inflation at three percent annually cuts your purchasing power in half every twenty four years.",
        "cta": "Follow for financial education that changes how you think about money.",
        "hashtags": "#financialliteracy #investing #stockmarket #retirement #wealthbuilding",
    },
    {
        "type": "numbers",
        "hook": "The average American household carries twenty two thousand dollars in non-mortgage debt.",
        "promise": "And the math of paying this off before investing might surprise you.",
        "body": [
            "Credit card debt at eighteen percent interest is a guaranteed negative eighteen percent return on your money.",
            "The stock market historically returns ten percent. So paying off credit card debt beats investing almost every time.",
            "But student loans at four or five percent? The math actually favors investing over paying extra.",
        ],
        "midpoint": "So what's the actual order of operations?",
        "midpoint_detail": "Pay off high interest debt first. Get your employer four oh one K match second. That's a hundred percent instant return. Then invest the rest.",
        "cta": "Follow. This order of operations alone could be worth hundreds of thousands over a lifetime.",
        "hashtags": "#debt #investing #personalfinance #401k #financialplanning",
    },
]


# ============================================================
# Script Helpers
# ============================================================
def _pick_script():
    """Pick script from library based on day-of-year rotation."""
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(SCRIPTS)
    return SCRIPTS[idx]


def _script_to_spoken_format(s):
    """
    Convert a v5 script dict into the spoken-lines format used by video engine.
    Returns: {"hook": str, "scenes": [str, ...], "cta": str, "hashtags": str}
    """
    scenes = list(s["body"])
    # Insert midpoint hook + detail as extra scenes (makes video longer / more engaging)
    scenes.append(s["midpoint"])
    scenes.append(s["midpoint_detail"])
    return {
        "hook": s["hook"],
        "promise": s.get("promise", ""),
        "scenes": scenes,
        "cta": s["cta"],
        "hashtags": s.get("hashtags", "#investing #finance #money"),
        "type": s.get("type", "general"),
    }


# ============================================================
# AI Script Generation
# ============================================================
def generate_script():
    """Generate today's video script. AI-first with v5 format, fallback to library."""
    if not GROQ_API_KEY:
        return _script_to_spoken_format(_pick_script())

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        # Pick a random content type to generate
        content_types = [
            "myth buster (debunk a common investing misconception)",
            "market signal (what's happening in markets right now)",
            "wealth principle (a core concept about building wealth)",
            "mistake alert (common investing mistake to avoid)",
            "beginner truth (something every new investor must know)",
            "sector spotlight (an interesting sector opportunity)",
            "psychology (how emotions destroy investment returns)",
            "numbers tell (surprising financial statistics)",
        ]
        chosen_type = random.choice(content_types)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "Write a TikTok FINANCE video script in the style of top creators like @thinkarytok.\n"
                    "Content type: " + chosen_type + "\n"
                    "Today is " + day + ".\n\n"
                    "FOLLOW THIS EXACT 5-PART STRUCTURE — return ONLY valid JSON:\n"
                    "{\n"
                    '  "hook": "Pattern interrupt opener — make them stop scrolling. Under 10 words.",\n'
                    '  "promise": "One sentence: what they will learn. Under 12 words.",\n'
                    '  "body": ["fact or insight 1", "fact or insight 2", "fact or insight 3"],\n'
                    '  "midpoint": "Re-engagement hook at midpoint. Start with: But here\'s... / Wait... / So...",\n'
                    '  "midpoint_detail": "The surprising reveal or deeper insight. 1-2 sentences.",\n'
                    '  "cta": "Clear action. Save/Share/Follow. Under 12 words.",\n'
                    '  "hashtags": "4-5 relevant lowercase hashtags"\n'
                    "}\n\n"
                    "CRITICAL — This is SPOKEN ALOUD by TTS voice. Write like a REAL PERSON talks:\n"
                    "- Short punchy sentences. Natural pauses.\n"
                    "- Use contractions: it's, don't, won't, they've, you're\n"
                    "- Spell out numbers: 'four point five percent' NOT '4.5%'\n"
                    "- Spell acronyms: 'S and P five hundred' NOT 'S&P500', 'C P I' NOT 'CPI'\n"
                    "- Sound like a smart 28-year-old talking to a friend, not a textbook\n\n"
                    "FORBIDDEN WORDS (AI giveaways, instant scroll-past):\n"
                    "game changer, pro tip, ninja, hack, leverage, navigate, crucial, essential,\n"
                    "paramount, comprehensive, landscape, moreover, furthermore, synergy, delve,\n"
                    "actionable, empower, robust, streamline, holistic, cutting-edge\n\n"
                    "HOOK FRAMEWORKS TO CHOOSE FROM:\n"
                    "- 'That [thing] you believe is wrong.'\n"
                    "- 'Nobody talks about [X] but it's costing you money.'\n"
                    "- 'I see investors make this mistake every single week.'\n"
                    "- 'The difference between [A] and [B] is [surprising number].'\n"
                    "- '[Surprising statistic] about [topic].'\n"
                    "- 'If I was starting from zero today, here's exactly what I'd do.'\n"
                    "- 'Stop. You've been lied to about [X].'\n"
                    "- 'One [thing] separates wealthy people from everyone else.'\n"
                )
            }],
            max_tokens=400,
            temperature=0.92
        )

        text = response.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]

        data = json.loads(text)
        # Validate required fields
        required = ["hook", "body", "midpoint", "midpoint_detail", "cta"]
        if all(k in data for k in required) and len(data["body"]) >= 2:
            # Fill optional fields
            data.setdefault("promise", "")
            data.setdefault("hashtags", "#investing #finance #money #stocks")
            data.setdefault("type", "ai")
            return _script_to_spoken_format(data)

        return _script_to_spoken_format(_pick_script())

    except Exception as e:
        print("  AI script generation failed: " + str(e))
        return _script_to_spoken_format(_pick_script())


def generate_caption(script):
    """Generate TikTok caption from script."""
    hashtags = script.get("hashtags", "#investing #finance #money")

    if not GROQ_API_KEY:
        return script["hook"] + " " + hashtags

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "Write a TikTok caption for a FINANCE video. Return ONLY the caption text, nothing else.\n"
                    "Hook: " + script["hook"] + "\n\n"
                    "Rules:\n"
                    "- Max 130 characters (not counting hashtags)\n"
                    "- Start with the hook or a slight variation of it\n"
                    "- Sound like a real person, not a brand\n"
                    "- End with these hashtags: " + hashtags + "\n"
                    "- No emoji spam (1-2 max)\n"
                    "- No financial advice disclaimers in the caption (too corporate)\n"
                )
            }],
            max_tokens=80,
            temperature=0.85
        )
        caption = response.choices[0].message.content.strip()
        # Ensure hashtags are present
        if "#" not in caption:
            caption += " " + hashtags
        return caption
    except Exception:
        return script["hook"] + " " + hashtags


# ============================================================
# Font Helper
# ============================================================
def _font(size, bold=False):
    """Get a font."""
    paths = []
    if bold:
        paths = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(text, font, max_w, draw):
    """Word-wrap text to fit within max_w pixels."""
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + (" " if cur else "") + w
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ============================================================
# TTS — Text-to-Speech with Word-Level Timing
# ============================================================
async def generate_tts_audio(text, output_path, voice=None):
    """
    Generate TTS audio file and return word-level timestamp data.
    Returns: (audio_path, word_data_list)
    """
    if voice is None:
        voice = TTS_VOICE

    # Step 1: Save audio
    comm_save = edge_tts.Communicate(text, voice, rate=TTS_RATE)
    await comm_save.save(output_path)

    # Step 2: Get timing data (try WordBoundary first, fall back to SentenceBoundary)
    word_data = []
    sentence_boundaries = []

    comm_stream = edge_tts.Communicate(text, voice, rate=TTS_RATE)
    try:
        async for event in comm_stream.stream():
            if event["type"] == "WordBoundary":
                word_data.append({
                    "text": event["text"],
                    "offset_sec": event["offset"] / 10_000_000,
                    "duration_sec": event["duration"] / 10_000_000,
                })
            elif event["type"] == "SentenceBoundary":
                sentence_boundaries.append({
                    "text": event["text"],
                    "offset_sec": event["offset"] / 10_000_000,
                    "duration_sec": event["duration"] / 10_000_000,
                })
    except Exception as e:
        print(f"  TTS stream warning: {e}")

    # If we got WordBoundary data, use it directly
    if word_data:
        print(f"  TTS: {len(word_data)} words from WordBoundary ({voice})")
        return output_path, word_data

    # If we got SentenceBoundary data, use it to build word-level timing
    if sentence_boundaries:
        total_dur = sentence_boundaries[-1]["offset_sec"] + sentence_boundaries[-1]["duration_sec"]
        word_data = _build_word_timing_from_sentences(text, sentence_boundaries, total_dur)
        print(f"  TTS: {len(word_data)} words from SentenceBoundary ({voice})")
        return output_path, word_data

    # Ultimate fallback: pure estimation from text
    print("  TTS: estimating timing from text...")
    word_data = _estimate_word_timing(text)
    print(f"  TTS: {len(word_data)} words estimated ({voice})")
    return output_path, word_data


def _build_word_timing_from_sentences(text, sentences, total_duration):
    """Build word-level timing from SentenceBoundary events."""
    word_data = []
    words = text.split()

    if not sentences or not words:
        return _estimate_word_timing(text)

    # Map each word to its containing sentence
    char_pos = 0
    word_sentence_map = []  # (word, start_char_pos)
    for w in words:
        word_sentence_map.append((w, char_pos))
        char_pos += len(w) + 1  # word + space

    # Distribute time across sentences, then across words in each sentence
    sent_idx = 0
    for wi, (word, wcpos) in enumerate(word_sentence_map):
        # Find which sentence this word belongs to
        while sent_idx < len(sentences) - 1:
            # Check next sentence start
            if wcpos >= sentences[sent_idx].get("_end_char", 0):
                sent_idx += 1
            else:
                break

        # Get sentence timing
        s_start = sentences[sent_idx]["offset_sec"]
        s_end = s_start + sentences[sent_idx]["duration_sec"]
        s_dur = sentences[sent_idx]["duration_sec"]

        # Words in this sentence
        s_words = [x for x in range(len(words)) if word_sentence_map[x][1] < wcpos or x <= wi]
        # Simpler: just distribute evenly within the sentence's time window
        pass

    # Fallback: even simpler approach — use sentence boundaries as anchors
    result = []
    pos = 0.0
    for i, w in enumerate(words):
        wdur = max(total_duration / len(words) * (len(w) / 5.0), 0.25)
        result.append({
            "text": (" " if i > 0 else "") + w,
            "offset_sec": pos,
            "duration_sec": min(wdur, total_duration - pos),
        })
        pos += result[-1]["duration_sec"]

    return result


def _estimate_word_timing(text):
    """Estimate per-word timing based on text analysis."""
    words = text.split()
    total_dur = _estimate_duration(text)

    # Weight each word by its length and punctuation
    weights = []
    for w in words:
        clean = w.strip(".,!?;:'\"")
        weight = max(len(clean) * 0.15 + 0.25, 0.3)  # base + length factor
        if any(p in w for p in ".,!?"):  # pause after punctuation
            weight += 0.3
        weights.append(weight)

    total_weight = sum(weights) or 1
    scale = total_dur / total_weight

    result = []
    pos = 0.0
    for i, w in enumerate(words):
        wdur = weights[i] * scale
        result.append({
            "text": (" " if i > 0 else "") + w,
            "offset_sec": pos,
            "duration_sec": min(wdur, total_dur - pos),
        })
        pos += result[-1]["duration_sec"]

    return result


def _estimate_duration(text):
    """Estimate spoken duration in seconds based on text length."""
    # Average English speaking rate: ~150 words/min = 2.5 words/sec
    # Plus pauses after sentences/commas
    num_words = len(text.split())
    num_sentences = text.count('.') + text.count('!') + text.count('?') + 1
    base = num_words / 2.5
    pause = num_sentences * 0.3  # pause between sentences
    return max(base + pause, 1.5)  # minimum 1.5 seconds


def build_spoken_lines(script):
    """
    Build full spoken text lines from v5 script with labels.
    v5 structure: hook → promise → body[0..n] → midpoint → midpoint_detail → cta
    Returns: [(label, text), ...]
    """
    lines = []
    lines.append(("hook", script["hook"]))
    if script.get("promise"):
        lines.append(("promise", script["promise"]))
    for i, scene in enumerate(script["scenes"]):
        lines.append((f"scene_{i}", scene))
    lines.append(("cta", script["cta"]))
    return lines


async def generate_all_audio(spoken_lines, output_dir):
    """
    Generate TTS audio for each line.
    Returns: [(label, audio_path, word_data), ...]
    """
    results = []
    for label, text in spoken_lines:
        audio_path = os.path.join(output_dir, f"tts_{label}.mp3")
        path, word_data = await generate_tts_audio(text, audio_path)
        results.append((label, path, word_data))

        # Small pause between sections (silence)
        if label != "cta":
            pass  # We'll add silence during merge

    return results


# ============================================================
# Background Generators — Cinematic Animated Style
# ============================================================
def _gradient_bg(w, h, top, bot):
    """Smooth vertical gradient."""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * r) for i in range(3))
        draw.line([(0, y), (w, y)], fill=c)
    return img


def _vignette(img, strength=0.3):
    """Dark vignette around edges."""
    w, h = img.size
    arr = np.array(img, dtype=np.float32)
    cx, cy = w / 2, h / 2
    max_dist = math.sqrt(cx * cx + cy * cy)
    y_coords, x_coords = np.ogrid[:h, :w]
    dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    vignette = 1 - (dist / max_dist) * strength
    vignette = np.clip(vignette, 0.3, 1.0)
    arr[:, :, 0] *= vignette
    arr[:, :, 1] *= vignette
    arr[:, :, 2] *= vignette
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ============================================================
# v5 Background — Clean, Bold, Minimal (matching top creators)
# ============================================================
def _gradient_bg(w, h, top, bot):
    """Smooth vertical gradient."""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * r) for i in range(3))
        draw.line([(0, y), (w, y)], fill=c)
    return img


def _vignette(img, strength=0.3):
    """Soft dark vignette around edges for depth."""
    w, h = img.size
    arr = np.array(img, dtype=np.float32)
    cx, cy = w / 2, h / 2
    max_dist = math.sqrt(cx * cx + cy * cy)
    y_coords, x_coords = np.ogrid[:h, :w]
    dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    vignette = 1 - (dist / max_dist) * strength
    vignette = np.clip(vignette, 0.4, 1.0)
    arr[:, :, 0] *= vignette
    arr[:, :, 1] *= vignette
    arr[:, :, 2] *= vignette
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# v5: Subtle scene-type color tinting on the background
SCENE_BG = {
    "hook":     {"top": (10, 12, 22), "bot": (20, 22, 42), "accent_line": C["accent"]},
    "promise":  {"top": (8,  11, 20), "bot": (18, 21, 38), "accent_line": C["gray"]},
    "scene_0":  {"top": (8,  12, 22), "bot": (16, 24, 44), "accent_line": C["green"]},
    "scene_1":  {"top": (12, 10, 20), "bot": (24, 18, 36), "accent_line": C["gold"]},
    "scene_2":  {"top": (8,  13, 24), "bot": (14, 26, 46), "accent_line": C["accent"]},
    "scene_3":  {"top": (14, 10, 18), "bot": (26, 20, 34), "accent_line": C["red"]},
    "scene_4":  {"top": (10, 14, 20), "bot": (18, 26, 40), "accent_line": C["green"]},
    "scene_5":  {"top": (12, 10, 22), "bot": (22, 18, 40), "accent_line": C["gold"]},
    "cta":      {"top": (8,  14, 20), "bot": (14, 28, 40), "accent_line": C["green"]},
}


def _make_clean_bg(label):
    """Create clean dark gradient background — v5 style (no particles, no noise)."""
    theme = SCENE_BG.get(label, SCENE_BG["scene_0"])
    img = _gradient_bg(W, H, theme["top"], theme["bot"])
    img = _vignette(img, 0.28)

    draw = ImageDraw.Draw(img)

    # Subtle top + bottom horizontal accent bars (like top creators' style)
    bar_col = tuple(min(255, v + 20) for v in theme["top"])
    draw.rectangle([(0, 0), (W, 4)], fill=theme["accent_line"])
    draw.rectangle([(0, H - 4), (W, H)], fill=theme["accent_line"])

    return img


# ============================================================
# v5 Scene Rendering — Large Bold Text Cards
# ============================================================
def _render_scene_v5(text, label, scene_number=None, total_scenes=None, is_hook=False, is_promise=False, is_cta=False):
    """
    Render a scene card in v5 style:
    - Hook: HUGE text, full center, accent underline
    - Promise: Medium text, subtitle style, gray
    - Body scenes: Large text with scene number pill on left
    - Midpoint scenes (scene_3/scene_4): Different accent color, "But wait..." feel
    - CTA: Green text + BroadFSC pill + website
    """
    img = _make_clean_bg(label)
    draw = ImageDraw.Draw(img)

    # ── BRAND TAG (top-right corner) ────────────────────────
    brand_font = _font(22, bold=True)
    brand_text = "BroadFSC"
    bw = draw.textbbox((0, 0), brand_text, font=brand_font)[2]
    bx = W - bw - 52
    draw.rounded_rectangle((bx - 12, 52, bx + bw + 12, 88), radius=14, fill=C["accent"])
    draw.text((bx + bw // 2, 70), brand_text, font=brand_font, fill=C["white"], anchor="mm")

    theme = SCENE_BG.get(label, SCENE_BG["scene_0"])
    accent_col = theme["accent_line"]

    if is_hook:
        # ──── HOOK: Giant text, full vertical center ─────────
        font_big = _font(80, bold=True)
        lines = _wrap(text, font_big, W - 100, draw)
        line_h = 98
        total_h = len(lines) * line_h
        y = (H // 2) - (total_h // 2) - 60

        for line in lines:
            # Shadow
            draw.text((66, y + 4), line, font=font_big, fill=(0, 0, 0))
            # Text
            draw.text((64, y), line, font=font_big, fill=C["white"])
            y += line_h

        # Bold accent underline
        draw.rectangle([(64, y + 20), (64 + 280, y + 26)], fill=accent_col)

        # Scroll hint at bottom
        hint_font = _font(26)
        draw.text((W // 2, H - 260), "watch to the end",
                  font=hint_font, fill=C["dim"], anchor="mm")
        draw.text((W // 2, H - 225), "▼",
                  font=hint_font, fill=C["dim"], anchor="mm")

    elif is_promise:
        # ──── PROMISE: Italic-feel subtitle style ────────────
        font_p = _font(46, bold=False)
        lines = _wrap(text, font_p, W - 120, draw)
        line_h = 62
        total_h = len(lines) * line_h
        y = (H // 2) - (total_h // 2)

        # Left accent line
        draw.rectangle([(48, y - 10), (54, y + total_h + 10)], fill=accent_col)

        for line in lines:
            draw.text((74, y), line, font=font_p, fill=C["gray"])
            y += line_h

    elif is_cta:
        # ──── CTA: Green + Website pill ──────────────────────
        font_cta = _font(60, bold=True)
        lines = _wrap(text, font_cta, W - 120, draw)
        line_h = 80
        total_h = len(lines) * line_h
        y = (H // 2) - (total_h // 2) - 100

        for line in lines:
            draw.text((66, y + 3), line, font=font_cta, fill=(0, 0, 0))
            draw.text((64, y), line, font=font_cta, fill=C["green"])
            y += line_h

        # Divider
        draw.rectangle([(W // 2 - 80, y + 36), (W // 2 + 80, y + 40)], fill=C["dim"])

        # Website pill button
        pill_w, pill_h_px = 580, 66
        pill_x = W // 2 - pill_w // 2
        pill_y = y + 70
        draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h_px),
                                radius=33, fill=C["accent"])
        url_font = _font(28, bold=True)
        draw.text((W // 2, pill_y + pill_h_px // 2), "broadfsc.com/different",
                  font=url_font, fill=C["white"], anchor="mm")

        # Telegram link
        tg_font = _font(22)
        draw.text((W // 2, pill_y + pill_h_px + 48), "Telegram: @BroadFSC",
                  font=tg_font, fill=C["gray"], anchor="mm")

        # Disclaimer (tiny, required)
        disc_font = _font(16)
        draw.text((W // 2, H - 150),
                  "For educational purposes only. Not financial advice.",
                  font=disc_font, fill=C["dim"], anchor="mm")

    else:
        # ──── BODY SCENE: Large text + scene number ──────────
        # Scene number pill (top-left)
        if scene_number is not None:
            num_font = _font(28, bold=True)
            pill_label = f"  {scene_number}  "
            pw = draw.textbbox((0, 0), pill_label, font=num_font)[2] + 4
            draw.rounded_rectangle((48, 52, 48 + pw, 92), radius=20, fill=accent_col)
            draw.text((48 + pw // 2, 72), pill_label, font=num_font, fill=(8, 10, 18), anchor="mm")

        font_body = _font(58, bold=True)
        lines = _wrap(text, font_body, W - 100, draw)
        line_h = 76
        total_h = len(lines) * line_h
        y = (H // 2) - (total_h // 2)

        for line in lines:
            # Shadow
            draw.text((66, y + 3), line, font=font_body, fill=(0, 0, 0))
            # Text
            draw.text((64, y), line, font=font_body, fill=C["white"])
            y += line_h

        # Accent bottom line under text
        draw.rectangle([(64, y + 28), (64 + 140, y + 32)], fill=accent_col)

    return img


# ============================================================
# Karaoke Subtitle Renderer — Word-by-word highlight
# ============================================================
class KaraokeRenderer:
    """
    Renders karaoke-style subtitles where each word highlights
    as it's being spoken. This is THE key feature that makes
    videos look professional.
    """

    def __init__(self, word_data, total_duration_sec, label=""):
        """
        word_data: list of {"text": ..., "offset_sec": ..., "duration_sec": ...}
        total_duration_sec: how long this scene lasts
        """
        self.words = word_data
        self.total_duration = total_duration_sec
        self.label = label
        self.full_text = "".join(w["text"] for w in word_data)

        # Pre-compute character positions for highlighting
        self._build_char_map()

    def _build_char_map(self):
        """Build map: char_index -> (word_idx, start_offset, end_offset)"""
        self.char_map = []
        char_pos = 0
        for wi, wd in enumerate(self.words):
            wstart = wd["offset_sec"]
            wend = wd["offset_sec"] + wd["duration_sec"]
            for ci, ch in enumerate(wd["text"]):
                self.char_map.append({
                    "char": ch,
                    "char_pos": char_pos,
                    "word_idx": wi,
                    "start": wstart,
                    "end": wend,
                    "abs_start": wstart,
                    "abs_end": wend,
                })
                char_pos += 1
            # Space between words
            if wi < len(self.words) - 1:
                next_start = self.words[wi + 1]["offset_sec"]
                self.char_map.append({
                    "char": " ",
                    "char_pos": char_pos,
                    "word_idx": -1,  # space
                    "start": wend,
                    "end": next_start,
                    "abs_start": wend,
                    "abs_end": next_start,
                })
                char_pos += 1

    def render_frame(self, base_frame_array, current_time_sec):
        """
        Render karaoke subtitle onto a video frame.
        base_frame_array: numpy array (H, W, 3) uint8
        current_time_sec: time position in seconds
        Returns: modified numpy array
        """
        img = Image.fromarray(base_frame_array.copy())
        draw = ImageDraw.Draw(img)

        # Subtitle bar area
        bar_y = H - 340
        bar_h = 110
        bar_margin_x = 48

        # Semi-transparent background for readability
        overlay = Image.new("RGBA", (W, bar_h), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        ov_draw.rounded_rectangle(
            [(0, 0), (W - 1, bar_h - 1)],
            radius=18,
            fill=(10, 12, 25, 200)
        )
        img.paste(Image.alpha_composite(Image.new("RGBA", (W, bar_h), (0, 0, 0, 0)), overlay),
                  (0, bar_y), overlay)

        draw = ImageDraw.Draw(img)

        # Determine which characters should be highlighted
        # Build highlighted vs unhighlighted text segments
        font = _font(38, bold=True)
        font_small = _font(34)

        # Calculate layout — we need to render each segment separately
        cursor_x = bar_margin_x
        cursor_y = bar_y + (bar_h - 46) // 2
        max_x = W - bar_margin_x

        for entry in self.char_map:
            ch = entry["char"]
            if ch == " ":
                cursor_x += font.getlength(" ")
                if cursor_x > max_x:
                    cursor_x = bar_margin_x
                    cursor_y += 50
                continue

            is_highlighted = (current_time_sec >= entry["start"] and
                              current_time_sec < entry["end"])

            # Progress within this character (for smooth color transition)
            if is_highlighted and entry["end"] > entry["start"]:
                progress = min(1.0, (current_time_sec - entry["start"]) /
                               (entry["end"] - entry["start"]))
            else:
                progress = 0.0

            if is_highlighted:
                # Highlighted: bright gold/yellow with glow
                color = self._lerp_color(C["white"], C["kara_hi"], progress)
                shadow = (0, 0, 0)
            else:
                # Unhighlighted: dim gray
                color = C["kara_lo"]
                shadow = None

            if shadow:
                draw.text((cursor_x + 1, cursor_y + 1), ch, font=font, fill=shadow)
            draw.text((cursor_x, cursor_y), ch, font=font, fill=color)

            char_w = font.getlength(ch)
            cursor_x += char_w

            if cursor_x > max_x:
                cursor_x = bar_margin_x
                cursor_y += 50

        # Progress indicator bar (thin line below text)
        if self.total_duration > 0:
            progress_pct = min(1.0, current_time_sec / self.total_duration)
            bar_width = int((W - 2 * bar_margin_x) * progress_pct)
            prog_y = bar_y + bar_h - 6
            # Background track
            draw.rounded_rectangle(
                [bar_margin_x, prog_y, W - bar_margin_x, prog_y + 4],
                radius=2, fill=(40, 45, 70)
            )
            # Progress fill
            if bar_width > 0:
                draw.rounded_rectangle(
                    [bar_margin_x, prog_y, bar_margin_x + bar_width, prog_y + 4],
                    radius=2, fill=C["accent"]
                )

        return np.array(img)

    def _lerp_color(self, c1, c2, t):
        """Linear interpolation between two colors."""
        t = max(0, min(1, t))
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ============================================================
# Audio Processing
# ============================================================
def _generate_silence(duration_sec, sr=24000):
    """Generate silence audio samples."""
    total_samples = int(sr * duration_sec)
    return [0] * total_samples


def _mix_audio_voice_only(voice_paths, gap_sec=0.5, sr=24000):
    """
    Mix all voice clips with gaps — NO background music (user feedback: too noisy).
    Returns path to mixed WAV file.
    """
    import wave

    temp_dir = tempfile.mkdtemp()
    mixed_path = os.path.join(temp_dir, "mixed_audio.wav")

    # Convert all MP3 to raw PCM samples
    all_clips = []
    for vp in voice_paths:
        if os.path.exists(vp) and os.path.getsize(vp) > 0:
            samples = _load_mp3_as_samples(vp)
            if samples:
                all_clips.append(samples)
        else:
            print(f"  WARNING: Missing audio file: {vp}")

    if not all_clips:
        print("  ERROR: No audio clips available!")
        return None

    # Concatenate voice clips with short silence gaps
    gap_samples = _generate_silence(gap_sec, sr)
    voice_final = []
    for i, clip in enumerate(all_clips):
        voice_final.extend(clip)
        if i < len(all_clips) - 1:
            voice_final.extend(gap_samples)

    total_sec = len(voice_final) / sr
    print(f"  Voice-only duration: {total_sec:.1f}s (no background music)")

    # Normalize
    peak = max(abs(v) for v in voice_final) or 1
    if peak > 30000:
        voice_final = [int(v * 28000 / peak) for v in voice_final]

    # Write WAV
    with wave.open(mixed_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        data = struct.pack('<' + 'h' * len(voice_final), *voice_final)
        wf.writeframes(data)

    sz = os.path.getsize(mixed_path)
    print(f"  Mixed audio: {mixed_path} ({sz} bytes, {total_sec:.1f}s)")
    return mixed_path


def _load_mp3_as_samples(mp3_path):
    """Load MP3 file and return PCM sample list."""
    try:
        # Use ffmpeg to convert mp3 to raw pcm via pipe
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        cmd = [ffmpeg_exe, '-i', mp3_path, '-ac', '1',
               '-ar', '24000', '-f', 's16le', 'pipe:1']
        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode != 0:
            print(f"  FFmpeg error: {result.stderr[:200]}")
            return None

        # Parse raw PCM data (16-bit signed LE mono)
        raw = result.stdout
        num_samples = len(raw) // 2
        samples = list(struct.unpack('<' + 'h' * num_samples, raw))
        return samples

    except Exception as e:
        print(f"  Failed to load MP3: {e}")
        return None


def merge_av_files(video_path, audio_path, output_path):
    """Merge video + audio using ffmpeg."""
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        cmd = [
            ffmpeg_exe, '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        ok = result.returncode == 0 and os.path.exists(output_path)
        if ok:
            print(f"  AV merged: {output_path} ({os.path.getsize(output_path)} bytes)")
        else:
            print(f"  AV merge failed: {result.stderr[:300]}")
        return ok
    except Exception as e:
        print(f"  AV merge error: {e}")
        return False


# ============================================================
# Video Generation — Voice-Synchronized
# ============================================================
def create_video_v5(script, audio_info, output_path):
    """
    Create TikTok video v5: clean bold text cards + voice + karaoke subtitles.
    NO background music. NO particles. Bold & clear like top creators.
    """
    if not HAS_IMAGEIO or not HAS_PILLOW:
        print("  Pillow + imageio required")
        return False

    try:
        temp_dir = tempfile.mkdtemp(prefix="tiktok_v5_")
        print(f"  Temp dir: {temp_dir}")

        # 1. Mix voice-only audio (no music)
        print("--- Mixing Audio (voice only) ---")
        voice_paths = [a[1] for a in audio_info]
        mixed_audio = _mix_audio_voice_only(voice_paths, gap_sec=0.55)

        if not mixed_audio:
            print("  Audio mix failed!")
            return False

        # 2. Calculate timing per scene
        print("--- Calculating Timings ---")
        scene_timings = []
        current_sec = 0.0
        gap = 0.55

        spoken_lines = build_spoken_lines(script)

        # Map labels to display metadata
        body_scene_count = sum(1 for lbl, _ in spoken_lines if lbl.startswith("scene_"))
        body_counter = [0]  # mutable counter for closure

        for idx, (label, text) in enumerate(spoken_lines):
            word_data = audio_info[idx][2] if idx < len(audio_info) else []

            if word_data:
                scene_dur = word_data[-1]["offset_sec"] + word_data[-1]["duration_sec"] + 0.3
            else:
                scene_dur = max(3.0, len(text.split()) * 0.4)

            abs_start = current_sec
            abs_end = current_sec + scene_dur

            abs_word_data = []
            for wd in word_data:
                abs_word_data.append({
                    "text": wd["text"],
                    "offset_sec": abs_start + wd["offset_sec"],
                    "duration_sec": wd["duration_sec"],
                })

            # Determine display type flags
            is_hook = (label == "hook")
            is_promise = (label == "promise")
            is_cta = (label == "cta")
            is_body = label.startswith("scene_")

            # Body scene number (1-based, only for actual body scenes)
            scene_num = None
            if is_body:
                body_counter[0] += 1
                scene_num = body_counter[0]

            scene_timings.append({
                "label": label,
                "text": text,
                "start": abs_start,
                "end": abs_end,
                "duration": scene_dur,
                "word_data": abs_word_data,
                "is_hook": is_hook,
                "is_promise": is_promise,
                "is_cta": is_cta,
                "scene_num": scene_num,
                "total_body": body_scene_count,
            })

            current_sec = abs_end + gap

        total_duration = current_sec - gap
        total_frames = int(total_duration * FPS)
        print(f"  Total: {total_duration:.1f}s, {total_frames} frames @ {FPS}fps")

        # 3. Pre-render static scene images
        print("--- Rendering Scene Cards ---")
        scene_images = {}
        for st in scene_timings:
            label = st["label"]
            img = _render_scene_v5(
                st["text"], label,
                scene_number=st["scene_num"],
                total_scenes=st["total_body"],
                is_hook=st["is_hook"],
                is_promise=st["is_promise"],
                is_cta=st["is_cta"],
            )
            scene_images[label] = img
            print(f"  [{label}] {st['text'][:60]}")

        # 4. Encode video frame by frame
        print("--- Encoding Video ---")
        temp_video = os.path.join(temp_dir, "video_noaudio.mp4")
        writer = iio.get_writer(
            temp_video, fps=FPS, codec='libx264',
            output_params=['-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '22']
        )

        for frame_num in range(total_frames):
            current_time = frame_num / FPS

            # Find active scene
            active_scene = None
            for st in scene_timings:
                if st["start"] <= current_time < st["end"]:
                    active_scene = st
                    break
            if active_scene is None:
                active_scene = scene_timings[-1]

            label = active_scene["label"]

            # Use pre-rendered static image as base
            frame = np.array(scene_images[label].copy())

            # Apply karaoke subtitles
            if active_scene["word_data"]:
                karaoke = KaraokeRenderer(
                    active_scene["word_data"],
                    active_scene["duration"],
                    label=label,
                )
                scene_time = current_time - active_scene["start"]
                frame = karaoke.render_frame(frame, scene_time)

            # Add global progress bar at very bottom
            prog = min(1.0, current_time / total_duration)
            bar_full_w = W - 96
            bar_w = int(bar_full_w * prog)
            bar_y = H - 28
            img_tmp = Image.fromarray(frame)
            dr = ImageDraw.Draw(img_tmp)
            dr.rounded_rectangle((48, bar_y, 48 + bar_full_w, bar_y + 8), radius=4, fill=C["dim"])
            if bar_w > 4:
                dr.rounded_rectangle((48, bar_y, 48 + bar_w, bar_y + 8), radius=4, fill=C["accent"])
            frame = np.array(img_tmp)

            writer.append_data(frame)

            if frame_num % 90 == 0:
                pct = frame_num / total_frames * 100
                print(f"  Frame {frame_num}/{total_frames} ({pct:.0f}%)")

        writer.close()

        # 5. Merge audio + video
        print("--- Merging A/V ---")
        success = merge_av_files(temp_video, mixed_audio, output_path)

        # Cleanup
        try:
            for f in [temp_video, mixed_audio]:
                if os.path.exists(f):
                    os.remove(f)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

        if success:
            sz = os.path.getsize(output_path)
            print(f"\n  SUCCESS: {output_path} ({sz // 1024}KB, {total_duration:.1f}s)")
            return True
        else:
            if os.path.exists(temp_video):
                try:
                    os.rename(temp_video, output_path)
                    print("  Saved video without audio")
                    return True
                except Exception:
                    pass
            return False

    except Exception as e:
        print(f"  Video v5 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# Postproxy API
# ============================================================
def post_tiktok_video_file(caption, video_path):
    """Post a TikTok video file via Postproxy API."""
    if not POSTPROXY_API_KEY:
        print("  TikTok: Missing POSTPROXY_API_KEY")
        return False
    if not os.path.exists(video_path):
        print("  TikTok: File not found: " + video_path)
        return False

    url = POSTPROXY_BASE_URL + "/posts"
    headers = {"Authorization": "Bearer " + POSTPROXY_API_KEY}

    try:
        with open(video_path, "rb") as f:
            files = {"media[]": (os.path.basename(video_path), f, "video/mp4")}
            data = {
                "post[body]": caption,
                "profiles[]": "tiktok",
                "platforms[tiktok][format]": "video",
                "platforms[tiktok][privacy_status]": "PUBLIC_TO_EVERYONE",
            }
            r = requests.post(url, headers=headers, data=data, files=files, timeout=120)

        if r.status_code in [200, 201]:
            post_id = r.json().get("id", "unknown")
            print("  TikTok: Posted! ID: " + str(post_id))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:400])
            return False
    except Exception as e:
        print("  TikTok: FAIL - " + str(e))
        return False


def notify_telegram(message):
    """Send notification to Telegram channel."""
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": message}, timeout=10)
    except Exception:
        pass


# ============================================================
# Main
# ============================================================
async def async_main():
    print("=" * 58)
    print(" BroadFSC TikTok Auto-Poster v5")
    print(" Viral Finance Content Engine")
    print("=" * 58)

    now = datetime.datetime.utcnow()
    print("UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print(f"TTS: {'YES (' + TTS_VOICE + ')' if HAS_TTS else 'NO'}")
    print(f"Pillow: {'YES' if HAS_PILLOW else 'NO'}")
    print(f"imageio: {'YES' if HAS_IMAGEIO else 'NO'}")
    print()

    # Step 1: Generate script
    print("--- Step 1: Generate Script ---")
    script = generate_script()
    print(f"  Type: {script.get('type', 'general')}")
    print("  Hook: " + script["hook"])
    if script.get("promise"):
        print("  Promise: " + script["promise"])
    print(f"  Scenes: {len(script['scenes'])}")
    for i, s in enumerate(script["scenes"]):
        print(f"    {i + 1}. {s[:70]}")
    print("  CTA: " + script["cta"])
    print()

    # Step 2: Generate caption
    print("--- Step 2: Generate Caption ---")
    caption = generate_caption(script)
    print("  " + caption)
    print()

    if not HAS_TTS:
        print("ERROR: edge-tts not installed! Run: pip install edge-tts")
        return False

    # Step 3: TTS for all lines
    print("--- Step 3: Generate Voice Over ---")
    spoken_lines = build_spoken_lines(script)
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tts_cache")
    os.makedirs(temp_dir, exist_ok=True)

    audio_info = await generate_all_audio(spoken_lines, temp_dir)
    print(f"  Generated {len(audio_info)} audio clips")
    print()

    # Step 4: Create video v5
    print("--- Step 4: Create Video (v5 Viral Engine) ---")
    video_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(video_dir, "tiktok_v5.mp4")

    success = False
    if HAS_PILLOW and HAS_IMAGEIO:
        if create_video_v5(script, audio_info, video_path):
            # Step 5: Post to TikTok
            print("--- Step 5: Post to TikTok ---")
            success = post_tiktok_video_file(caption, video_path)
            try:
                os.remove(video_path)
            except Exception:
                pass
        else:
            print("  Video creation failed!")

        # Cleanup TTS cache
        for _, ap, _ in audio_info:
            try:
                if os.path.exists(ap):
                    os.remove(ap)
            except Exception:
                pass
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass
    else:
        print("  Pillow + imageio required!")

    print()

    # Step 6: Notify & log
    script_type = script.get("type", "general")
    if success:
        notify_telegram(f"TikTok v5 [{script_type}] posted: {caption[:70]}")
        print(f"SUCCESS: TikTok v5 posted! ({script_type})")
        if HAS_ANALYTICS:
            log_post(platform="tiktok", post_type=f"video_v5_{script_type}",
                     content_preview=caption[:100], status="success")
    else:
        notify_telegram("TikTok v5 post FAILED")
        print("FAILED: TikTok v5 not posted.")
        if HAS_ANALYTICS:
            log_post(platform="tiktok", post_type=f"video_v5_{script_type}",
                     content_preview=caption[:100], status="failed", error_msg="Video creation failed")

    print()
    print("=" * 58)
    print("Done.")
    return success


def main():
    """Entry point — runs async TTS pipeline."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
