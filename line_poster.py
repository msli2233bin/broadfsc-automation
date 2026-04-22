"""
BroadFSC LINE Official Account Auto-Poster
Posts market insights to LINE Official Account via Messaging API.

Supports:
- Broadcast messages (群发给所有好友)
- Narrowcast messages (按条件筛选推送)
- Push messages (给单个用户发消息)
- Multi-language: Japanese (jp) + Traditional Chinese (zh-tw)

LINE Messaging API docs:
https://developers.line.biz/en/docs/messaging-api/

Setup:
1. Create LINE Official Account at https://manager.line.biz/
2. Enable Messaging API in LINE Developers Console
3. Get Channel Access Token from Console
4. Set environment variables:
   - LINE_CHANNEL_ACCESS_TOKEN: from LINE Developers Console
   - GROQ_API_KEY: for AI content generation (optional, has fallback)
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
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

LINE_API_BASE = "https://api.line.me/v2/bot"

TELEGRAM_LINK = "https://t.me/BroadFSC"
WEBSITE_LINK = "https://www.broadfsc.com/different"
HUB_LINK = "https://www.broadfsc.com/different"

# ============================================================
# LINE Message Types
# ============================================================

def _get_headers():
    """Get LINE API headers with auth token."""
    return {
        "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }


def broadcast_text(text):
    """Broadcast a text message to all friends (群发文字)."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("  LINE: Missing LINE_CHANNEL_ACCESS_TOKEN")
        return False

    url = LINE_API_BASE + "/message/broadcast"
    payload = {
        "messages": [
            {
                "type": "text",
                "text": text,
            }
        ]
    }

    try:
        r = requests.post(url, headers=_get_headers(), json=payload, timeout=15)
        if r.status_code == 200:
            print("  LINE: Broadcast sent! (text)")
            if HAS_ANALYTICS:
                log_post(platform="line", post_type="broadcast_text", content_preview=text[:100], status="success")
            return True
        else:
            print("  LINE: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            if HAS_ANALYTICS:
                log_post(platform="line", post_type="broadcast_text", content_preview=text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print("  LINE: FAIL - " + str(e))
        if HAS_ANALYTICS:
            log_post(platform="line", post_type="broadcast_text", status="failed", error_msg=str(e)[:200])
        return False


def broadcast_flex(alt_text, flex_content):
    """Broadcast a Flex Message (图文卡片) to all friends.
    
    Flex Messages support rich layouts with images, buttons, and text.
    Perfect for market briefings with CTA buttons linking to website.
    """
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("  LINE: Missing LINE_CHANNEL_ACCESS_TOKEN")
        return False

    url = LINE_API_BASE + "/message/broadcast"
    payload = {
        "messages": [
            {
                "type": "flex",
                "altText": alt_text,
                "contents": flex_content,
            }
        ]
    }

    try:
        r = requests.post(url, headers=_get_headers(), json=payload, timeout=15)
        if r.status_code == 200:
            print("  LINE: Broadcast sent! (flex)")
            if HAS_ANALYTICS:
                log_post(platform="line", post_type="broadcast_flex", content_preview=alt_text[:100], status="success")
            return True
        else:
            print("  LINE: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            if HAS_ANALYTICS:
                log_post(platform="line", post_type="broadcast_flex", content_preview=alt_text[:100], status="failed", error_msg=f"HTTP {r.status_code}")
            return False
    except Exception as e:
        print("  LINE: FAIL - " + str(e))
        if HAS_ANALYTICS:
            log_post(platform="line", post_type="broadcast_flex", status="failed", error_msg=str(e)[:200])
        return False


def narrowcast_text(text, filter_demographic=None):
    """Send a narrowcast text message (按条件筛选推送).
    
    filter_demographic example:
    {
        "type": "age",
        "gte": "age_20",
        "lt": "age_55"
    }
    """
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("  LINE: Missing LINE_CHANNEL_ACCESS_TOKEN")
        return False

    url = LINE_API_BASE + "/message/narrowcast"
    payload = {
        "messages": [
            {
                "type": "text",
                "text": text,
            }
        ],
    }
    if filter_demographic:
        payload["filter"] = {"demographic": [filter_demographic]}

    try:
        r = requests.post(url, headers=_get_headers(), json=payload, timeout=15)
        if r.status_code == 200:
            print("  LINE: Narrowcast sent!")
            return True
        else:
            print("  LINE: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
            return False
    except Exception as e:
        print("  LINE: FAIL - " + str(e))
        return False


# ============================================================
# Flex Message Builder
# ============================================================

def build_market_briefing_flex(title, body_text, lang="en"):
    """Build a Flex Message for market briefing with CTA button.
    
    Creates a professional card layout:
    - Header: Title with emoji
    - Body: Market analysis text
    - Footer: CTA button linking to website
    """
    # Language-specific labels
    labels = {
        "en": {"learn_more": "Free Investment Education", "footer": "BroadFSC | Daily Market Insights"},
        "jp": {"learn_more": "無料投資教育はこちら", "footer": "BroadFSC | 毎日マーケット情報"},
        "zh-tw": {"learn_more": "免費投資教育", "footer": "BroadFSC | 每日市場洞察"},
        "es": {"learn_more": "Educacion Gratuita", "footer": "BroadFSC | Insights Diarios"},
        "ar": {"learn_more": "Learn More", "footer": "BroadFSC | Daily Insights"},
    }
    lbl = labels.get(lang, labels["en"])

    flex = {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "md",
                    "color": "#1D4ED8",
                    "wrap": True,
                }
            ],
            "backgroundColor": "#EFF6FF",
            "paddingAll": "12px",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": body_text,
                    "size": "sm",
                    "wrap": True,
                    "color": "#374151",
                    "lineSpacing": "18px",
                }
            ],
            "paddingAll": "12px",
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "uri",
                        "label": lbl["learn_more"],
                        "uri": WEBSITE_LINK,
                    },
                    "color": "#1D4ED8",
                    "margin": "none",
                },
                {
                    "type": "text",
                    "text": lbl["footer"],
                    "size": "xxs",
                    "color": "#9CA3AF",
                    "align": "center",
                    "margin": "sm",
                },
            ],
            "paddingAll": "8px",
        },
    }
    return flex


# ============================================================
# Content Generation
# ============================================================

def generate_content(lang="en"):
    """Generate a LINE market briefing post using AI or fallback."""
    if not GROQ_API_KEY:
        return get_fallback(lang)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        lang_instruction = {
            "en": "Write in English.",
            "jp": "Write in Japanese (日本語). Use professional financial terminology (日経平均, ドル円, 新NISA, 決算シーズン).",
            "zh-tw": "Write in Traditional Chinese (繁體中文). Use Taiwan market terminology (台股, 美股, 台積電, 法說會, 櫃買指數).",
            "es": "Write in Spanish (Espanol).",
            "ar": "Write in Arabic.",
        }.get(lang, "Write in English.")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write a concise daily market briefing for LINE Official Account.\n"
                    "Today is " + day + ".\n\n"
                    "Requirements:\n"
                    "- " + lang_instruction + "\n"
                    "- Maximum 400 characters\n"
                    "- Include 2-3 specific market observations\n"
                    "- Use bullet points for readability\n"
                    "- Professional but engaging tone\n"
                    "- Do NOT include any links (they go in the CTA button)\n"
                    "- Do NOT promise guaranteed returns\n"
                    "- Do NOT add hashtags"
                )
            }],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  LINE AI generation failed (" + lang + "): " + str(e))
        return get_fallback(lang)


def get_fallback(lang="en"):
    """Fallback content when AI is unavailable."""
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")

    fallbacks = {
        "en": (
            "Daily Market Briefing | " + date_str + "\n\n"
            "Key factors to watch today:\n"
            "\u2022 Central bank policy signals (Fed, ECB, BOJ)\n"
            "\u2022 Global equity futures direction\n"
            "\u2022 Key economic data releases\n"
            "\u2022 Geopolitical risk premiums in commodities\n"
            "\u2022 Cross-currency flow dynamics\n\n"
            "Stay ahead with daily pre-market briefings from BroadFSC."
        ),
        "jp": (
            "毎日マーケットレポート | " + date_str + "\n\n"
            "本日の注目ポイント:\n"
            "\u2022 日銀・FRB・ECBの政策シグナル\n"
            "\u2022 グローバル株価先物の方向感\n"
            "\u2022 主要経済指標の発表予定\n"
            "\u2022 コモディティの地政学リスクプレミアム\n"
            "\u2022 クロスカレンシーフローの動向\n\n"
            "BroadFSCの毎日プレマーケットレポートで情報優位を。"
        ),
        "zh-tw": (
            "每日市場速報 | " + date_str + "\n\n"
            "今日關注重點:\n"
            "\u2022 央行政策信號（Fed、ECB、日銀）\n"
            "\u2022 全球股指期貨方向\n"
            "\u2022 重要經濟數據公布\n"
            "\u2022 大宗商品地緣風險溢價\n"
            "\u2022 跨幣種資金流動\n\n"
            "BroadFSC每日盤前速報，掌握市場先機。"
        ),
    }
    return fallbacks.get(lang, fallbacks["en"])


# ============================================================
# Main
# ============================================================

def post_line(lang="en", use_flex=True):
    """Post a market briefing to LINE Official Account.
    
    Args:
        lang: Language code (en, jp, zh-tw)
        use_flex: If True, send Flex Message; if False, send plain text
    
    Returns:
        bool: Success status
    """
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("  LINE: Not configured (missing LINE_CHANNEL_ACCESS_TOKEN)")
        return False

    # Generate content
    content = generate_content(lang)

    if use_flex:
        # Build and send Flex Message
        titles = {
            "en": "\U0001f4c8 Daily Market Briefing",
            "jp": "\U0001f4c8 毎日マーケットレポート",
            "zh-tw": "\U0001f4c8 每日市場速報",
        }
        title = titles.get(lang, titles["en"])
        flex = build_market_briefing_flex(title, content, lang)
        return broadcast_flex(title, flex)
    else:
        # Plain text broadcast
        return broadcast_text(content)


def main():
    """Main entry point for standalone execution."""
    print("=" * 50)
    print("BroadFSC LINE Official Account Auto-Poster")
    print("=" * 50)

    now = datetime.datetime.utcnow()
    print("Current UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print("LINE_CHANNEL_ACCESS_TOKEN: " + ("SET" if LINE_CHANNEL_ACCESS_TOKEN else "NOT SET"))
    print("GROQ_API_KEY: " + ("SET" if GROQ_API_KEY else "NOT SET (using fallback)"))
    print()

    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("Cannot post without LINE_CHANNEL_ACCESS_TOKEN.")
        print()
        print("Setup instructions:")
        print("1. Create LINE Official Account: https://manager.line.biz/")
        print("2. Enable Messaging API in LINE Developers Console")
        print("3. Get Channel Access Token")
        print("4. Set env var: LINE_CHANNEL_ACCESS_TOKEN=your_token")
        return

    # Post in primary languages for Japan/Taiwan markets
    # Default: send Japanese first, then Traditional Chinese
    # (can be configured via LINE_LANG env var)
    langs_str = os.environ.get("LINE_LANG", "jp,zh-tw")
    langs = [l.strip() for l in langs_str.split(",") if l.strip()]

    for lang in langs:
        lang_name = {"en": "English", "jp": "Japanese", "zh-tw": "Traditional Chinese", "es": "Spanish"}.get(lang, lang)
        print("--- LINE: " + lang_name + " ---")
        success = post_line(lang=lang, use_flex=True)
        print("  Result: " + ("SUCCESS" if success else "FAILED"))
        print()

    print("=" * 50)
    print("LINE posting complete.")


if __name__ == "__main__":
    main()
