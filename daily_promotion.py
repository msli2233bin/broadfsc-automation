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
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

ALL_CHANNELS = [CHANNEL_ID]
if CHANNEL_ES:
    ALL_CHANNELS.append(CHANNEL_ES)
if CHANNEL_AR:
    ALL_CHANNELS.append(CHANNEL_AR)

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
        "cta": "Free education: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different",
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
        "cta": "Aprende gratis: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different",
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
        "cta": "https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different",
        "disclaimer": (
            "\n\n<i> .    .</i>"
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
            "Free education: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
            "Aprende gratis: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
            "Free education: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
            "Aprende gratis: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
            "Free education: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
            "Aprende gratis: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
            "Free education: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
            "Aprende gratis: https://msli2233bin.github.io/broadfsc-automation/ | broadfsc.com/different"
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
    """Use Groq API to generate market-specific briefing in the target language."""
    if not GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        lang_instruction = {
            "en": "Write in English.",
            "es": "Write in Spanish (Espanol).",
            "ar": "Write in Arabic.",
        }.get(lang, "Write in English.")

        region_title = LANG_CONFIG[lang]["region_names"].get(region, region + " BRIEFING")
        cta = LANG_CONFIG[lang]["cta"]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write a concise pre-market briefing for {region} markets.\n\n"
                    "Title: {title}\n\n"
                    "{focus}\n\n"
                    "Requirements:\n"
                    "- {lang_instr}\n"
                    "- Format as a Telegram message with clear bullet points\n"
                    "- Keep it under 500 characters\n"
                    "- Be specific with current market themes\n"
                    "- Use a professional but engaging tone\n"
                    "- End with: {cta}\n"
                    "- NEVER promise guaranteed returns"
                ).format(
                    region=region,
                    title=region_title,
                    focus=focus_text,
                    lang_instr=lang_instruction,
                    cta=cta,
                )
            }],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message.content
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

        print()

    print("Done!")


if __name__ == "__main__":
    main()

