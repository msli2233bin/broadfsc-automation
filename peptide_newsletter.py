"""
RTPeptide 科研简报 (Newsletter) 生成器
========================================
- 用 Groq 生成一期「肽研究周报」(3 个产品科普 + 行业动态口吻)
- 发到 Telegram 频道 (复用 bot)
- 同时产出 docs/peptide-seo/newsletter/latest.html, 可直接粘到 Substack / 邮件

免费、可靠、ROI 最高(研究: 邮件可达 30x)。合规: Research Use Only。
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env BEFORE importing peptide_promotion (its BOT_TOKEN is read at module level)
_ENVF = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_ENVF):
    for _line in open(_ENVF, encoding="utf-8"):
        _line = _line.strip()
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

from peptide_products import PRODUCTS, products_by_category
from peptide_promotion import generate_product_content, send_telegram

SITE_URL = "https://www.rawpeptidemfg.com"
CHANNEL_URL = "https://t.me/rtpeptide_official"
NEWSLETTER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "peptide-seo", "newsletter")

SYS_PROMPT = (
    "You are the editorial writer for RTPeptide, a supplier of research-grade peptides "
    "for laboratory study only. Write a concise 'Peptide Research Weekly' digest in English. "
    "Pick 3 distinct peptides from the provided list. For each: 1 short paragraph on what it is "
    "and its research context (structure/function language only, NO human benefit or therapeutic claims). "
    "End with a one-line note that all materials are Research Use Only, not for human consumption. "
    "Tone: professional, scientific, neutral. Under 600 words total. Use plain text with '- ' bullets."
)


def build_digest():
    import random
    picks = random.sample(PRODUCTS, min(3, len(PRODUCTS)))
    listing = "\n".join(f"- {p['name']} ({p['category']}): {p.get('research_focus','')}" for p in picks)
    try:
        import groq
        client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYS_PROMPT},
                {"role": "user", "content": "Available peptides:\n" + listing},
            ],
            max_tokens=700,
            temperature=0.7,
        )
        return r.choices[0].message.content.strip(), picks
    except Exception as e:  # noqa
        # fallback: deterministic digest
        lines = ["Peptide Research Weekly — Research Use Only digest.\n"]
        for p in picks:
            lines.append(f"- {p['name']} ({p['category']}): {p.get('research_focus','')}")
        lines.append("\nAll materials are Research Use Only. Not for human consumption.")
        return "\n".join(lines), picks


def to_html(title, body):
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    paras = body.replace("\n", "</p>\n<p>")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{title} — {date}</title></head>
<body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:680px;margin:0 auto;padding:24px;color:#1a1a1a">
<h1 style="color:#0c2236">RTPeptide — Peptide Research Weekly</h1>
<p style="color:#667">{date} · Research Use Only</p>
<p>{paras}</p>
<hr>
<p style="font-size:13px;color:#667">RTPeptide supplies research-grade peptides for laboratory investigation only. Not for human consumption. <a href="{CHANNEL_URL}">Telegram</a> · <a href="{SITE_URL}">Website</a></p>
</body></html>"""


def main():
    body, picks = build_digest()
    title = "Peptide Research Weekly"
    # Telegram (HTML-ish, strip tags)
    import re
    tg_text = re.sub("<[^>]+>", "", body)
    tg_text += f"\n\n🔬 RTPeptide Research Weekly · {CHANNEL_URL}\n<i>Research Use Only. Not for human consumption.</i>"
    send_telegram(tg_text, os.environ.get("TELEGRAM_PEPTIDE_CHANNEL_ID", os.environ.get("TELEGRAM_CHANNEL_ID", "")))
    # HTML for Substack
    os.makedirs(NEWSLETTER_DIR, exist_ok=True)
    with open(os.path.join(NEWSLETTER_DIR, "latest.html"), "w", encoding="utf-8") as f:
        f.write(to_html(title, body))
    print("Newsletter sent to Telegram + HTML saved to docs/peptide-seo/newsletter/latest.html")
    print("Products featured:", ", ".join(p["name"] for p in picks))


if __name__ == "__main__":
    # load .env
    envf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(envf):
        for line in open(envf, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()
    main()
