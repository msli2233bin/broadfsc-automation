"""
BroadFSC Global Market Pre-Market Briefing System (Multi-Language)
Sends targeted market insights 30 min before each major market opens.
Covers: US, Europe, Asia-Pacific, Middle East, Latin America.
Supports: English, Spanish, Arabic channels.

GitHub Actions cron schedule: runs every 30 minutes.
Only sends when it's 30 min before a market open.
"""

import os
import sys
import datetime
import requests
import json

# Analytics tracking
try:
    from analytics_logger import log_post
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# Main English channel
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")
# Optional language channels (leave empty to skip)
CHANNEL_ES = os.environ.get("TELEGRAM_CHANNEL_ES", "")
CHANNEL_AR = os.environ.get("TELEGRAM_CHANNEL_AR", "")
CHANNEL_JP = os.environ.get("TELEGRAM_CHANNEL_JP", "")
CHANNEL_ZH_TW = os.environ.get("TELEGRAM_CHANNEL_ZH_TW", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

ALL_CHANNELS = [CHANNEL_ID]
if CHANNEL_ES:
    ALL_CHANNELS.append(CHANNEL_ES)
if CHANNEL_AR:
    ALL_CHANNELS.append(CHANNEL_AR)
if CHANNEL_JP:
    ALL_CHANNELS.append(CHANNEL_JP)
if CHANNEL_ZH_TW:
    ALL_CHANNELS.append(CHANNEL_ZH_TW)

DISCLAIMER = (
    "\n\n<i>Risk Disclaimer: Investment involves risk. "
    "Past performance is not indicative of future results. "
    "Please consult a licensed advisor before investing.</i>"
)

# ============================================================
# Global Market Schedule (UTC times, 30 min before open)
# ============================================================
REGION_SESSIONS = {
    "APAC":     {"hour": 0, "minute": 0,  "markets": "Japan, South Korea, Hong Kong, Singapore, Australia, India"},
    "Middle East": {"hour": 5, "minute": 30, "markets": "Saudi Arabia (Tadawul), UAE (DFM/ADX)"},
    "Europe":   {"hour": 7, "minute": 0,  "markets": "UK (LSE), Germany (Xetra), France (Euronext)"},
    "Americas": {"hour": 13, "minute": 30, "markets": "US (NYSE/NASDAQ), Brazil (B3)"},
}

WEEKEND_SKIP = {
    "APAC":         [5, 6],
    "Middle East":  [5, 6],
    "Europe":       [5, 6],
    "Americas":     [5, 6],
}

REGION_FOCUS = {
    "APAC": (
        "Focus on: Asian market movers, China economic data, RBA/BOJ policy signals, "
        "Asia-Pacific trade flows, semiconductor and tech sector trends."
    ),
    "Middle East": (
        "Focus on: Oil price trends (Brent/WTI), OPEC+ developments, regional geopolitics, "
        "Saudi Vision 2030 sectors, UAE economic diversification, GCC sovereign bond moves."
    ),
    "Europe": (
        "Focus on: ECB policy signals, Eurozone inflation/GDP data, Bank of England decisions, "
        "European energy markets, EU regulatory changes, DAX/FTSE/CAC key levels."
    ),
    "Americas": (
        "Focus on: Fed policy expectations, US CPI/NFP/fomc minutes, S&P 500/NASDAQ/Dow futures, "
        "earnings season highlights, US Treasury yields, Latin America FX and commodity impacts."
    ),
}

REGION_EMOJIS = {
    "APAC": "\U0001f30f",
    "Middle East": "\U0001f30d",
    "Europe": "\U0001f1ea\U0001f1fa",
    "Americas": "\U0001f30e",
}

# ============================================================
# Language Config
# ============================================================
LANG_CONFIG = {
    "en": {
        "name": "English",
        "region_names": {
            "APAC": "ASIA PRE-MARKET BRIEFING",
            "Middle East": "MIDDLE EAST PRE-MARKET BRIEFING",
            "Europe": "EUROPE PRE-MARKET BRIEFING",
            "Americas": "AMERICAS PRE-MARKET BRIEFING",
        },
        "cta": "Free education: https://www.broadfsc.com/different | broadfsc.com/different",
        "disclaimer": DISCLAIMER,
    },
    "es": {
        "name": "Spanish",
        "region_names": {
            "APAC": "INFORME PRE-MERCADO ASIA",
            "Middle East": "INFORME PRE-MERCADO MEDIO ORIENTE",
            "Europe": "INFORME PRE-MERCADO EUROPA",
            "Americas": "INFORME PRE-MERCADO AMERICAS",
        },
        "cta": "Aprende gratis: https://www.broadfsc.com/different | broadfsc.com/different",
        "disclaimer": (
            "\n\n<i>Aviso de riesgo: La inversion implica riesgo. "
            "El rendimiento pasado no es indicativo de resultados futuros. "
            "Consulte a un asesor autorizado antes de invertir.</i>"
        ),
    },
    "ar": {
        "name": "Arabic",
        "region_names": {
            "APAC": "APAC - ",
            "Middle East": "MIDDLE EAST - ",
            "Europe": "EUROPE - ",
            "Americas": "AMERICAS - ",
        },
        "cta": "https://www.broadfsc.com/different | broadfsc.com/different",
        "disclaimer": (
            "\n\n<i> .    .</i>"
        ),
    },
    "jp": {
        "name": "Japanese",
        "region_names": {
            "APAC": "アジアプレマーケットレポート",
            "Middle East": "中東プレマーケットレポート",
            "Europe": "欧州プレマーケットレポート",
            "Americas": "米州プレマーケットレポート",
        },
        "cta": "投資教育は無料で: https://www.broadfsc.com/different",
        "disclaimer": (
            "\n\n<i>リスク開示: 投資にはリスクが伴います。過去の実績は将来の結果を示すものではありません。"
            "投資の前にライセンス保有のアドバイザーにご相談ください。</i>"
        ),
    },
    "zh-tw": {
        "name": "Traditional Chinese",
        "region_names": {
            "APAC": "亞太盤前速報",
            "Middle East": "中東盤前速報",
            "Europe": "歐洲盤前速報",
            "Americas": "美洲盤前速報",
        },
        "cta": "免費投資教育: https://www.broadfsc.com/different",
        "disclaimer": (
            "\n\n<i>風險聲明: 投資涉及風險。過往表現不代表未來收益。投資前請諮詢持牌顧問。</i>"
        ),
    },
}

# Map channels to languages
CHANNEL_LANG_MAP = {}
# Will be built dynamically based on which channels are configured


def build_channel_lang_map():
    """Build mapping of channel IDs to languages."""
    global CHANNEL_LANG_MAP
    CHANNEL_LANG_MAP = {}
    if CHANNEL_ID:
        CHANNEL_LANG_MAP[CHANNEL_ID] = "en"
    if CHANNEL_ES:
        CHANNEL_LANG_MAP[CHANNEL_ES] = "es"
    if CHANNEL_AR:
        CHANNEL_LANG_MAP[CHANNEL_AR] = "ar"
    if CHANNEL_JP:
        CHANNEL_LANG_MAP[CHANNEL_JP] = "jp"
    if CHANNEL_ZH_TW:
        CHANNEL_LANG_MAP[CHANNEL_ZH_TW] = "zh-tw"


# Fallback content templates per language
FALLBACK_TEMPLATES = {
    "APAC": {
        "en": (
            "{emoji} ASIA PRE-MARKET BRIEFING | {date}\n\n"
            "{markets}\n\n"
            "Key factors to watch today:\n"
            "- Overnight US market close and futures direction\n"
            "- BOJ/RBA/PBOC policy signals\n"
            "- China PMI and trade data releases\n"
            "- Semiconductor sector momentum (TSMC, Samsung)\n"
            "- Asia FX movements (JPY, CNY, AUD)\n\n"
            "Stay ahead of Asian session volatility.\n\n"
            "Free education: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "es": (
            "{emoji} INFORME PRE-MERCADO ASIA | {date}\n\n"
            "{markets}\n\n"
            "Factores clave a observar hoy:\n"
            "- Cierre nocturno del mercado estadounidense y direccion de futuros\n"
            "- Senales de politica de BOJ/RBA/PBOC\n"
            "- Datos de PMI y comercio de China\n"
            "- Momento del sector de semiconductores (TSMC, Samsung)\n"
            "- Movimientos FX en Asia (JPY, CNY, AUD)\n\n"
            "Mantengase adelante de la volatilidad de la sesion asiatica.\n\n"
            "Aprende gratis: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "ar": (
            "{emoji}  | {date}\n\n"
            "{markets}\n\n"
            ":\n"
            "-      \n"
            "- BOJ/RBA/PBOC\n"
            "-   PMI  \n"
            "-   (TSMC, Samsung)\n"
            "-   (JPY, CNY, AUD)\n\n"
            ".\n\n"
            "broadfsc.com/different"
        ),
        "jp": (
            "{emoji} アジアプレマーケットレポート | {date}\n\n"
            "{markets}\n\n"
            "本日の注目ポイント:\n"
            "- 米国市場の前日終値と先物の方向感\n"
            "- 日銀・豪準備銀行・人民銀の政策シグナル\n"
            "- 中国PMI・貿易統計発表\n"
            "- 半導体セクター動向（TSMC、サムスン）\n"
            "- アジア為替（ドル円、人民元、豪ドル）\n\n"
            "アジアセッションの変動に備えましょう。\n\n"
            "投資教育は無料で: https://www.broadfsc.com/different"
        ),
        "zh-tw": (
            "{emoji} 亞太盤前速報 | {date}\n\n"
            "{markets}\n\n"
            "今日關注重點:\n"
            "- 美股昨夜收盤與期貨方向\n"
            "- 央行政策信號（日銀/Fed/PBOC）\n"
            "- 中國PMI及貿易數據\n"
            "- 半導體板塊動態（台積電、三星）\n"
            "- 亞太匯率（美元/日圓、人民幣、澳幣）\n\n"
            "掌握亞太盤前關鍵資訊。\n\n"
            "免費投資教育: https://www.broadfsc.com/different"
        ),
    },
    "Middle East": {
        "en": (
            "{emoji} MIDDLE EAST PRE-MARKET BRIEFING | {date}\n\n"
            "{markets}\n\n"
            "Key factors to watch today:\n"
            "- Oil prices (Brent/WTI) and OPEC+ developments\n"
            "- Regional geopolitical updates\n"
            "- GCC equity fund flows\n"
            "- Saudi Aramco and regional blue chips\n"
            "- UAE real estate and tourism sector trends\n\n"
            "Position for Gulf market opportunities.\n\n"
            "Free education: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "es": (
            "{emoji} INFORME PRE-MERCADO MEDIO ORIENTE | {date}\n\n"
            "{markets}\n\n"
            "Factores clave a observar hoy:\n"
            "- Precios del petroleo (Brent/WTI) y desarrollos OPEP+\n"
            "- Actualizaciones geopoliticas regionales\n"
            "- Flujos de fondos de acciones del CCG\n"
            "- Saudi Aramco y blue chips regionales\n"
            "- Tendencias del sector inmobiliario y turistico de EAU\n\n"
            "Posicionese para las oportunidades del mercado del Golfo.\n\n"
            "Aprende gratis: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "ar": (
            "{emoji}  | {date}\n\n"
            "{markets}\n\n"
            ":\n"
            "-   (Brent/WTI)  OPEC+\n"
            "- \n"
            "-    \n"
            "-     \n"
            "-    UAE  \n\n"
            ".\n\n"
            "broadfsc.com/different"
        ),
        "jp": (
            "{emoji} 中東プレマーケットレポート | {date}\n\n"
            "{markets}\n\n"
            "本日の注目ポイント:\n"
            "- 原油価格（ブレント/WTI）とOPEC+動向\n"
            "- 中東地政学リスク更新\n"
            "- GCC株式ファンドフロー\n"
            "- サウジアラムコと地域ブルーチップ\n"
            "- UAE不動産・観光セクター動向\n\n"
            "中東市場のチャンスを見極めましょう。\n\n"
            "投資教育は無料で: https://www.broadfsc.com/different"
        ),
        "zh-tw": (
            "{emoji} 中東盤前速報 | {date}\n\n"
            "{markets}\n\n"
            "今日關注重點:\n"
            "- 油價（布蘭特/WTI）與OPEC+動態\n"
            "- 中東地緣政治更新\n"
            "- 海灣合作委員會資金流向\n"
            "- 沙烏地阿美與區域藍籌股\n"
            "- 阿聯酋房地產及旅遊趨勢\n\n"
            "掌握中東市場機會。\n\n"
            "免費投資教育: https://www.broadfsc.com/different"
        ),
    },
    "Europe": {
        "en": (
            "{emoji} EUROPE PRE-MARKET BRIEFING | {date}\n\n"
            "{markets}\n\n"
            "Key factors to watch today:\n"
            "- ECB rate decision expectations\n"
            "- Eurozone flash PMI and inflation data\n"
            "- Bank of England policy signals\n"
            "- European energy prices (TTF gas)\n"
            "- DAX 40, CAC 40, FTSE 100 key technicals\n\n"
            "Prepare for European session moves.\n\n"
            "Free education: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "es": (
            "{emoji} INFORME PRE-MERCADO EUROPA | {date}\n\n"
            "{markets}\n\n"
            "Factores clave a observar hoy:\n"
            "- Expectativas de decision de tasas del BCE\n"
            "- Datos flash de PMI e inflacion de la Eurozona\n"
            "- Senales de politica del Banco de Inglaterra\n"
            "- Precios de energia europea (gas TTF)\n"
            "- Tecnicos clave de DAX 40, CAC 40, FTSE 100\n\n"
            "Preparese para los movimientos de la sesion europea.\n\n"
            "Aprende gratis: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "ar": (
            "{emoji}  | {date}\n\n"
            "{markets}\n\n"
            ":\n"
            "-   BCE\n"
            "- PMI    \n"
            "-   \n"
            "-   (TTF)\n"
            "- DAX 40  CAC 40  FTSE 100\n\n"
            ".\n\n"
            "broadfsc.com/different"
        ),
        "jp": (
            "{emoji} 欧州プレマーケットレポート | {date}\n\n"
            "{markets}\n\n"
            "本日の注目ポイント:\n"
            "- ECB政策金利決定予想\n"
            "- ユーロ圏PMI速報値・インフレデータ\n"
            "- イングランド銀行の政策シグナル\n"
            "- 欧州エネルギー価格（TTFガス）\n"
            "- DAX 40・CAC 40・FTSE 100 テクニカル\n\n"
            "欧州セッションに備えましょう。\n\n"
            "投資教育は無料で: https://www.broadfsc.com/different"
        ),
        "zh-tw": (
            "{emoji} 歐洲盤前速報 | {date}\n\n"
            "{markets}\n\n"
            "今日關注重點:\n"
            "- ECB利率決議預期\n"
            "- 歐元區PMI速報及通膨數據\n"
            "- 英格蘭銀行政策信號\n"
            "- 歐洲能源價格（TTF天然氣）\n"
            "- DAX 40、CAC 40、FTSE 100關鍵技術面\n\n"
            "備戰歐洲盤。\n\n"
            "免費投資教育: https://www.broadfsc.com/different"
        ),
    },
    "Americas": {
        "en": (
            "{emoji} AMERICAS PRE-MARKET BRIEFING | {date}\n\n"
            "{markets}\n\n"
            "Key factors to watch today:\n"
            "- US stock futures (S&P, NASDAQ, Dow)\n"
            "- Fed policy expectations and FOMC minutes\n"
            "- Key economic releases (CPI, NFP, GDP)\n"
            "- Earnings season highlights\n"
            "- US 10Y Treasury yield and USD index\n"
            "- Latin America: BRL/MXN FX, Bovespa trends\n\n"
            "Get ready for the main session.\n\n"
            "Free education: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "es": (
            "{emoji} INFORME PRE-MERCADO AMERICAS | {date}\n\n"
            "{markets}\n\n"
            "Factores clave a observar hoy:\n"
            "- Futuros de acciones estadounidenses (S&P, NASDAQ, Dow)\n"
            "- Expectativas de politica de la Fed y minutos del FOMC\n"
            "- Publicaciones economicas clave (CPI, NFP, PIB)\n"
            "- Destacados de la temporada de resultados\n"
            "- Rendimiento del Treasury estadounidense a 10Y e indice USD\n"
            "- America Latina: FX BRL/MXN, tendencias de Bovespa\n\n"
            "Prepareses para la sesion principal.\n\n"
            "Aprende gratis: https://www.broadfsc.com/different | broadfsc.com/different"
        ),
        "ar": (
            "{emoji}  | {date}\n\n"
            "{markets}\n\n"
            ":\n"
            "-    (S&P, NASDAQ, Dow)\n"
            "-   FOMC\n"
            "-   (CPI, NFP, GDP)\n"
            "-   \n"
            "- 10Y   USD\n"
            "-   BRL/MXN  Bovespa\n\n"
            ".\n\n"
            "broadfsc.com/different"
        ),
        "jp": (
            "{emoji} 米州プレマーケットレポート | {date}\n\n"
            "{markets}\n\n"
            "本日の注目ポイント:\n"
            "- 米国株先物（S&P 500、NASDAQ、ダウ）\n"
            "- FRB政策予想とFOMC議事録\n"
            "- 経済指標発表（CPI、非農業部門雇用、GDP）\n"
            "- 決算シーズンハイライト\n"
            "- 米10年債利回りとドル指数\n"
            "- ラテンアメリカ: BRL/MXN為替、ボベスパ動向\n\n"
            "メインセッションに備えましょう。\n\n"
            "投資教育は無料で: https://www.broadfsc.com/different"
        ),
        "zh-tw": (
            "{emoji} 美洲盤前速報 | {date}\n\n"
            "{markets}\n\n"
            "今日關注重點:\n"
            "- 美股期貨（S&P 500、納斯達克、道瓊）\n"
            "- Fed政策預期與FOMC會議紀要\n"
            "- 重要經濟數據（CPI、非農、GDP）\n"
            "- 財報季亮點\n"
            "- 美國10年期國債收益率與美元指數\n"
            "- 拉丁美洲: BRL/MXN匯率、Bovespa趨勢\n\n"
            "備戰主交易時段。\n\n"
            "免費投資教育: https://www.broadfsc.com/different"
        ),
    },
}


# ============================================================
# Core Functions
# ============================================================

def check_which_session(now_utc):
    """Determine which market session briefing should run now."""
    matched = []
    for region, session in REGION_SESSIONS.items():
        if now_utc.hour == session["hour"] and now_utc.minute == session["minute"]:
            if now_utc.weekday() not in WEEKEND_SKIP[region]:
                matched.append(region)
    return matched


def generate_ai_content(region, focus_text, lang="en"):
    """Use Groq API to generate market-specific briefing in the target language.

    Voice system: Rotates daily among 4 analyst personas inspired by top Chinese finance KOLs,
    each adapted for international English-speaking audiences on US/global markets.
    """
    if not GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        date_str = now.strftime("%b %d")

        lang_instruction = {
            "en": "Write in English.",
            "es": "Write in Spanish (Espanol).",
            "ar": "Write in Arabic.",
            "jp": "Write in Japanese (日本語). Use professional financial terminology common in Japanese markets (e.g., 日経平均, ドル円, 新NISA).",
            "zh-tw": "Write in Traditional Chinese (繁體中文). Use terminology common in Taiwan markets (e.g., 台股, 美股, 台積電, 法說會).",
        }.get(lang, "Write in English.")

        region_title = LANG_CONFIG[lang]["region_names"].get(region, region + " BRIEFING")
        cta = LANG_CONFIG[lang]["cta"]

        # ============================================================
        # 4-Persona Voice System (rotates daily by day-of-year)
        # Inspired by top Chinese finance influencers, adapted for
        # international audiences covering US & global markets.
        # ============================================================
        PERSONAS = {
            "croc": {
                "name": "Alex 'The Croc' — Technical Hunter",
                "signature": "🐊",
                "style": (
                    "You are Alex, a razor-sharp technical trader who stalks the market like a crocodile — "
                    "patient, precise, then strikes fast. Your style: ultra-concise, chart-driven, give exact "
                    "levels (support/resistance/breakout). Skip macro fluff. Talk like a trader texting alpha "
                    "to a friend: 'SPX holding 5,200 = stay long. Break below = cut fast.' "
                    "Use short punchy sentences. Max 2 emojis. Never hedge with vague words like 'may' or 'could'."
                ),
                "hook_format": "Start with a specific price level or % move as the first line.",
            },
            "yang": {
                "name": "Thomas Yang — Value Compass",
                "signature": "📘",
                "style": (
                    "You are Thomas, a Buffett disciple who has managed money for 30+ years. "
                    "Your style: calm, philosophical, long-term. You question whether today's noise matters "
                    "in 5 years. Quote Buffett, Munger, or Graham when relevant. Push back on short-term panic. "
                    "Use rhetorical questions to make readers think: 'Is a 2% drop really a reason to sell a "
                    "company you'd own for a decade?' Always redirect to fundamentals: earnings quality, "
                    "balance sheet, moat. Measured, never sensational."
                ),
                "hook_format": "Start with a rhetorical question that challenges the short-term narrative.",
            },
            "hong": {
                "name": "Michael Hong — Macro Strategist",
                "signature": "🔭",
                "style": (
                    "You are Michael, a macro strategist who sees markets through the lens of cycles, "
                    "capital flows, and geopolitics. Your style: data-driven, intellectually rigorous, "
                    "connects dots others miss (e.g., bond yields → EM FX → commodity demand). "
                    "Use one specific data point (yield %, PMI, spread) to anchor your thesis. "
                    "Speak with quiet authority. Say what the consensus is missing. "
                    "Structure: 1 macro observation → 1 implication → 1 actionable takeaway."
                ),
                "hook_format": "Start with a macro data point (yield, spread, PMI, flow) that most miss.",
            },
            "warrior": {
                "name": "Iron Bull — Voice of the Retail Fighter",
                "signature": "⚔️",
                "style": (
                    "You are Iron Bull, the voice of the everyday investor fighting Wall Street. "
                    "Your style: passionate, relatable, emotionally resonant. You validate retail pain "
                    "('Yes, this market is confusing. Yes, it feels rigged.') then rally them with data. "
                    "Use 'we' — you're in this together. Celebrate small wins. Call out manipulation "
                    "with fire but back it with fact. Energy of a coach at halftime: honest about the "
                    "challenge, fierce about the opportunity. End with a battle cry or motivational close."
                ),
                "hook_format": "Start with empathy — name the fear or frustration most retail investors feel right now.",
            },
        }

        persona_keys = list(PERSONAS.keys())
        # Rotate persona by day-of-year (each persona gets ~91 days/year)
        # Also shift by region to add variety within the same day
        region_shift = {"APAC": 0, "Middle East": 1, "Europe": 2, "Americas": 3}
        day_offset = now.timetuple().tm_yday + region_shift.get(region, 0)
        persona_key = persona_keys[day_offset % len(persona_keys)]
        persona = PERSONAS[persona_key]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "PERSONA: " + persona["name"] + "\n"
                    "PERSONA STYLE: " + persona["style"] + "\n\n"
                    "Write a DEEP-DIVE pre-market briefing for " + region + " markets.\n\n"
                    "Title: " + persona["signature"] + " " + region_title + " | " + date_str + "\n\n"
                    "Market context: " + focus_text + "\n\n"
                    "Hook rule: " + persona["hook_format"] + "\n\n"
                    "Structure (follow this exactly):\n"
                    "1. HOOK — Bold opening claim or data point that grabs attention immediately\n"
                    "2. THE BIG PICTURE — 3-4 sentences of macro context (what's happening globally that affects this region)\n"
                    "3. WHY IT MATTERS — Connect the dots: how does this affect portfolios? What's the contrarian angle most miss?\n"
                    "4. BY THE NUMBERS — 3-5 specific data points with context (not just 'S&P up 1%' but 'S&P at 5,280 — testing resistance from the Jan 2022 double top')\n"
                    "5. THE TAKEAWAY — One clear, actionable conclusion for readers today\n\n"
                    "Rules:\n"
                    "- " + lang_instruction + "\n"
                    "- Format for Telegram: use <b>bold</b> for key points, bullet points, line breaks\n"
                    "- Maximum 1500 characters (deep analysis, not a headline)\n"
                    "- Stay 100% in character as " + persona["name"] + "\n"
                    "- Include 3-5 specific numbers (index levels, yield %, sector moves, economic data)\n"
                    "- End with this exact CTA: " + cta + "\n"
                    "- NEVER promise returns. NEVER use words like 'guaranteed' or 'certain'."
                )
            }],
            max_tokens=800,
            temperature=0.85
        )
        result = response.choices[0].message.content
        print("    Persona: " + persona["name"])
        return result
    except Exception as e:
        print("  AI generation failed (" + lang + "): " + str(e))
        return None


def get_fallback_content(region, lang="en"):
    """Generate fallback content when AI is unavailable."""
    now = datetime.datetime.utcnow()
    templates = FALLBACK_TEMPLATES.get(region, {})
    template = templates.get(lang, templates.get("en", ""))
    if not template:
        template = FALLBACK_TEMPLATES[region]["en"]

    session = REGION_SESSIONS[region]
    emoji = REGION_EMOJIS.get(region, "")
    return template.format(
        emoji=emoji,
        date=now.strftime("%Y-%m-%d"),
        markets=session["markets"]
    )


def send_telegram(text, channel_id):
    """Send message to a specific Telegram channel."""
    if not BOT_TOKEN or not channel_id:
        print("  FAIL: Missing BOT_TOKEN or channel_id")
        return False

    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text + DISCLAIMER,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            msg_id = r.json()['result']['message_id']
            print("  Sent to " + channel_id + " - Message ID: " + str(msg_id))
            if HAS_ANALYTICS:
                lang = CHANNEL_LANG_MAP.get(channel_id, 'en')
                log_post(platform=f"telegram_{lang}", post_type="briefing", channel=channel_id, content_preview=text[:100], post_id=str(msg_id), status="success")
            return True
        else:
            print("  FAIL [" + channel_id + "]: HTTP " + str(r.status_code) + " - " + r.text[:200])
            if HAS_ANALYTICS:
                lang = CHANNEL_LANG_MAP.get(channel_id, 'en')
                log_post(platform=f"telegram_{lang}", post_type="briefing", channel=channel_id, content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print("  FAIL [" + channel_id + "]: " + str(e))
        if HAS_ANALYTICS:
            lang = CHANNEL_LANG_MAP.get(channel_id, 'en')
            log_post(platform=f"telegram_{lang}", post_type="briefing", channel=channel_id, status="failed", error_msg=str(e)[:200])
        return False


def send_line(text, lang="en"):
    """Send market briefing to LINE Official Account via Flex Message."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("  LINE: Not configured (missing LINE_CHANNEL_ACCESS_TOKEN)")
        return False

    try:
        from line_poster import build_market_briefing_flex, broadcast_flex, broadcast_text
    except ImportError:
        print("  LINE: line_poster.py not found, skipping")
        return False

    titles = {
        "en": "\U0001f4c8 Pre-Market Briefing",
        "es": "\U0001f4c8 Informe Pre-Mercado",
        "ar": "\U0001f4c8 Pre-Market Briefing",
        "jp": "\U0001f4c8 プレマーケットレポート",
        "zh-tw": "\U0001f4c8 盤前速報",
    }
    title = titles.get(lang, titles["en"])
    flex = build_market_briefing_flex(title, text, lang)
    success = broadcast_flex(title, flex)
    if not success:
        print("  LINE: Flex failed, trying plain text...")
        success = broadcast_text(text)
    return success


# ============================================================
# Main
# ============================================================
def main():
    build_channel_lang_map()

    now_utc = datetime.datetime.utcnow()
    weekday = now_utc.weekday()
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    print("BroadFSC Pre-Market Briefing System (Multi-Language)")
    print("Current UTC: " + now_utc.strftime('%Y-%m-%d %H:%M') + " (" + weekday_names[weekday] + ")")
    print("BOT_TOKEN: " + ("SET" if BOT_TOKEN else "NOT SET"))
    print("Channels configured: " + str(len(ALL_CHANNELS)))
    for ch, lang in CHANNEL_LANG_MAP.items():
        print("  " + ch + " -> " + LANG_CONFIG[lang]["name"])
    print("GROQ_API_KEY: " + ("SET" if GROQ_API_KEY else "NOT SET (using fallback)"))
    print("LINE: " + ("Configured" if LINE_CHANNEL_ACCESS_TOKEN else "Not configured"))
    print()

    # Check which sessions should fire
    sessions = check_which_session(now_utc)

    if not sessions:
        print("No market session scheduled at this time.")
        print("Next sessions (UTC):")
        for region, s in REGION_SESSIONS.items():
            skip_days = [weekday_names[d] for d in WEEKEND_SKIP[region]]
            print("  " + region + ": " + str(s['hour']).zfill(2) + ":" + str(s['minute']).zfill(2) + " UTC (skip: " + ", ".join(skip_days) + ")")
        print("\nNo messages sent. Exiting.")
        return

    # Generate and send for each matched session + each channel
    for region in sessions:
        session = REGION_SESSIONS[region]
        focus = REGION_FOCUS[region]
        emoji = REGION_EMOJIS.get(region, "")

        print(emoji + " " + region + " Pre-Market Briefing")
        print("  Markets: " + session['markets'])

        # Send to each configured channel in its language
        for channel_id, lang in CHANNEL_LANG_MAP.items():
            print("  [" + LANG_CONFIG[lang]["name"] + " channel: " + channel_id + "]")

            # Try AI first, fallback to template
            content = generate_ai_content(region, focus, lang)
            if not content:
                content = get_fallback_content(region, lang)
                print("    Using fallback content")

            success = send_telegram(content, channel_id)
            print("    Result: " + ("SUCCESS" if success else "FAILED"))

        # Also send to LINE Official Account (JP + ZH-TW)
        if LINE_CHANNEL_ACCESS_TOKEN:
            print("  [LINE Official Account]")
            for line_lang in ["jp", "zh-tw"]:
                lang_name = LANG_CONFIG.get(line_lang, {}).get("name", line_lang)
                # Generate LINE-specific content
                line_content = generate_ai_content(region, focus, line_lang)
                if not line_content:
                    line_content = get_fallback_content(region, line_lang)
                line_success = send_line(line_content, lang=line_lang)
                print("    LINE [" + lang_name + "]: " + ("SUCCESS" if line_success else "FAILED"))

        print()

    print("Done!")


if __name__ == "__main__":
    main()

