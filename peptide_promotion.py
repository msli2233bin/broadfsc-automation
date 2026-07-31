# -*- coding: utf-8 -*-
"""
RTPeptide 肽产品全自动推广系统

复用 BroadFSC 的 Groq + Telegram 链路：
- Groq (llama-3.1-8b-instant) 生成产品科普内容
- Telegram Bot 发送到频道

区别：内容从金融盘前简报 换成 肽产品科研科普（Research Use Only）。
每日轮换一个主推产品，配分类聚焦。

环境变量（复用 .env）：
- TELEGRAM_BOT_TOKEN       复用现有 Bot Token
- TELEGRAM_CHANNEL_ID      默认频道（可设 TELEGRAM_PEPTIDE_CHANNEL_ID 覆盖）
- GROQ_API_KEY             复用现有 Groq Key
可选：
- PEPTIDE_SITE_URL        产品站链接（默认 https://www.rawpeptidemfg.com）
"""

import os
import sys
import datetime
import requests
import json

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peptide_products import PRODUCTS, CATEGORIES, get_product_of_day, products_by_category

# ============================================================
# Config
# ============================================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_PEPTIDE_CHANNEL_ID", "") or os.environ.get("TELEGRAM_CHANNEL_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SITE_URL = os.environ.get("PEPTIDE_SITE_URL", "https://www.rawpeptidemfg.com")

# 科研用途免责声明（必须带，不可做疗效承诺）
DISCLAIMER = (
    "\n\n<i>Research Use Only. Not for human consumption. "
    "All products are laboratory research chemicals. "
    "Visit " + SITE_URL + " for specifications.</i>"
)

# ============================================================
# Groq 内容生成（复用 daily_promotion 的 persona + 生成结构）
# ============================================================
def generate_product_content(product, lang="en"):
    """用 Groq 生成肽产品科研科普内容。"""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        date_str = now.strftime("%b %d, %Y")

        # 4 种科普声音轮换（按天）
        PERSONAS = {
            "scientist": {
                "name": "Dr. Peptide — Research Scientist",
                "signature": "🔬",
                "style": (
                    "You are a meticulous peptide research scientist. Precise, evidence-based, "
                    "never make therapeutic or medical claims. Explain mechanism of action at the "
                    "pathway level. Cite what is studied in vitro / preclinical models. Tone: "
                    "educational, credible, peer-respecting. No hype, no promises."
                ),
            },
            "formulator": {
                "name": "Lab Coat — Formulation Specialist",
                "signature": "🧪",
                "style": (
                    "You are a peptide formulation specialist. Focus on purity, lyophilization, "
                    "storage, stability, sequence integrity. Educational tone for fellow researchers "
                    "who care about compound quality. Never imply human use."
                ),
            },
            "explainer": {
                "name": "The Translator — Science Communicator",
                "signature": "📚",
                "style": (
                    "You are a science communicator who makes peptide mechanisms accessible. "
                    "Clear analogies, structured explainer style. Always frame as research context. "
                    "No medical advice, no dosage, no therapeutic claims."
                ),
            },
            "curator": {
                "name": "Catalog Curator — Category Guide",
                "signature": "🗂️",
                "style": (
                    "You are a research catalog curator. Present the product as part of a category "
                    "landscape — what family it belongs to, how researchers position it. Neutral, "
                    "informative, sourcing-focused."
                ),
            },
        }
        keys = list(PERSONAS.keys())
        persona = PERSONAS[keys[now.timetuple().tm_yday % len(keys)]]

        prompt = (
            "PERSONA: " + persona["name"] + "\n"
            "PERSONA STYLE: " + persona["style"] + "\n\n"
            "Write a Telegram product spotlight for a RESEARCH-ONLY peptide.\n\n"
            "PRODUCT: " + product["name"] + "\n"
            "CATEGORY: " + product["category"] + "\n"
            "SEQUENCE: " + product.get("sequence", "N/A") + "\n"
            "PURITY: " + product.get("purity", "N/A") + "\n"
            "FORM: " + product.get("form", "N/A") + "\n"
            "RESEARCH FOCUS: " + product.get("research_focus", "") + "\n"
            "KEY POINTS: " + " | ".join(product.get("key_points", [])) + "\n\n"
            "STRUCTURE (follow exactly):\n"
            "1. TITLE — " + persona["signature"] + " " + product["name"] + " | " + date_str + "\n"
            "2. WHAT IT IS — 1-2 sentences: peptide type, category\n"
            "3. MECHANISM — how it works at pathway level (research context)\n"
            "4. RESEARCH FOCUS — what preclinical/in-vitro studies explore\n"
            "5. SPEC HIGHLIGHTS — purity, form, sequence (bullet list)\n"
            "6. CATEGORY CONTEXT — where it sits among " + product["category"] + " peptides\n\n"
            "RULES:\n"
            "- Write in English.\n"
            "- Use <b>bold</b> for product name and key terms, bullet points, line breaks.\n"
            "- Max 1200 characters.\n"
            "- Research Use Only framing throughout. NEVER mention human dosage, therapeutic use, "
            "or medical outcomes. NEVER use 'cure', 'treat', 'heal', ' safe for human'.\n"
            "- End with CTA: Shop research peptides at " + SITE_URL + "\n"
        )

        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=750,
            temperature=0.8,
        )
        return r.choices[0].message.content
    except Exception as e:
        print("  AI generation failed: " + str(e))
        return None


def get_fallback_content(product):
    """Groq 不可用时的模板兜底。"""
    now = datetime.datetime.utcnow()
    lines = [
        f"🔬 {product['name']} | {now.strftime('%b %d, %Y')}",
        "",
        f"<b>Category:</b> {product['category']}",
        f"<b>Purity:</b> {product.get('purity','N/A')}  |  <b>Form:</b> {product.get('form','N/A')}",
        "",
        f"<b>Research focus:</b> {product.get('research_focus','')}",
        "",
        "<b>Spec highlights:</b>",
    ]
    for kp in product.get("key_points", []):
        lines.append(f"• {kp}")
    lines.append("")
    lines.append(f"Shop research peptides at {SITE_URL}")
    return "\n".join(lines)


# ============================================================
# Telegram 发送（复用 daily_promotion.send_telegram 结构）
# ============================================================
def send_telegram(text, channel_id):
    if not BOT_TOKEN or not channel_id:
        print("  FAIL: Missing BOT_TOKEN or channel_id")
        return False
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text + DISCLAIMER,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            msg_id = r.json()['result']['message_id']
            print("  Sent to " + channel_id + " - Message ID: " + str(msg_id))
            return True
        else:
            print("  FAIL [" + channel_id + "]: HTTP " + str(r.status_code) + " - " + r.text[:200])
            return False
    except Exception as e:
        print("  FAIL [" + channel_id + "]: " + str(e))
        return False


# ============================================================
# Main
# ============================================================
def main():
    print("RTPeptide Promotion System")
    print("UTC: " + datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M'))
    print("BOT_TOKEN: " + ("SET" if BOT_TOKEN else "NOT SET"))
    print("CHANNEL_ID: " + (CHANNEL_ID if CHANNEL_ID else "NOT SET"))
    print("GROQ_API_KEY: " + ("SET" if GROQ_API_KEY else "NOT SET (fallback mode)"))
    print("Products loaded: " + str(len(PRODUCTS)))
    print()

    product = get_product_of_day()
    print("📌 Product of the day: " + product["name"] + " (" + product["category"] + ")")

    content = generate_product_content(product)
    if not content:
        content = get_fallback_content(product)
        print("  Using fallback template")

    success = send_telegram(content, CHANNEL_ID)
    print("Result: " + ("SUCCESS" if success else "FAILED"))


if __name__ == "__main__":
    main()
