"""
RTPeptide 付费推广素材生成器
================================
为肽产品（Research Use Only 科研化学品）生成:
  1. 每产品的「广告专用落地页」(docs/peptide-seo/landing/<slug>.html)
     - 符合 Google Ads 审核: 专用页、RUO 免责声明置顶、无疗效暗示、COA 提示
  2. 广告文案表 (ad_copy.csv): Google Search / LinkedIn / 原生广告(Outbrain/Taboola) 多组变体

用法: python peptide_paid_assets.py
付费渠道需你手动开户+充值, 但落地页与文案我全包, 接 key 即投。
"""

import os
import csv
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peptide_products import PRODUCTS
from peptide_channels import slugify

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "peptide-seo", "landing")
SEO_BASE = "https://msli2233bin.github.io/broadfsc-automation/peptide-seo"
CS_LINK = "https://t.me/rtpeptide_official"
SITE_LINK = "https://www.rawpeptidemfg.com"

LANDING_CSS = """
:root{--bg:#04121f;--card:#0c2236;--blue:#3b82f6;--cyan:#22d3ee;--muted:#9fb3c8;--line:rgba(255,255,255,.08)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#e8f1fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.65}
.wrap{max-width:820px;margin:0 auto;padding:28px 20px 60px}
header{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:22px}
.logo{font-size:24px;font-weight:800;background:linear-gradient(90deg,var(--blue),var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}
.disclaimer{background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.35);border-radius:10px;padding:12px 16px;font-size:13px;color:#f5e6c0;margin:16px 0}
h1{font-size:30px;margin:0 0 6px}
.cat{color:var(--cyan);font-size:13px;letter-spacing:.04em;text-transform:uppercase}
.spec{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:14px 0}
.kv{display:flex;gap:12px;padding:7px 0;border-bottom:1px dashed var(--line);font-size:14px}
.k{color:var(--muted);min-width:120px}.v{color:#e8f1fb;word-break:break-word}
.focus{background:rgba(34,211,238,.06);border-left:3px solid var(--cyan);padding:12px 16px;border-radius:8px;margin:14px 0;font-size:14px}
.cta{margin-top:24px;display:flex;gap:12px;flex-wrap:wrap}
.btn{background:linear-gradient(90deg,var(--blue),var(--cyan));color:#04121f;font-weight:700;padding:12px 22px;border-radius:999px;font-size:14px;text-decoration:none}
.btn.ghost{background:transparent;color:var(--cyan);border:1px solid var(--cyan)}
.coa{font-size:13px;color:var(--muted);margin-top:8px}
"""


def landing_html(p):
    slug = slugify(p["name"])
    name = p["name"]
    cat = p["category"]
    focus = p.get("research_focus", "")
    seq = p.get("sequence", "—")
    purity = p.get("purity", "—")
    cas = p.get("cas", "—")
    form = p.get("form", "—")
    title = f"{name} Research Peptide | {cat} | RTPeptide"
    desc = f"{name} ({cat}) research-grade peptide. Purity {purity}, lab study use. Research Use Only."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SEO_BASE}/landing/{slug}.html">
</head>
<body>
<div class="wrap">
<header>
  <div class="logo">RTPeptide</div>
  <div class="cat">{cat}</div>
</header>
<h1>{name}</h1>
<div class="disclaimer"><b>Research Use Only.</b> Not for human consumption, diagnostic, or therapeutic use. All products are laboratory research chemicals.</div>
<div class="spec">
  <div class="kv"><span class="k">Catalogue</span><span class="v">{cat}</span></div>
  <div class="kv"><span class="k">CAS</span><span class="v">{cas}</span></div>
  <div class="kv"><span class="k">Sequence</span><span class="v">{seq}</span></div>
  <div class="kv"><span class="k">Purity</span><span class="v">{purity}</span></div>
  <div class="kv"><span class="k">Form</span><span class="v">{form}</span></div>
</div>
<div class="focus"><b>Research focus:</b> {focus}</div>
<p>{name} is supplied as a research-grade material for <b>in vitro and laboratory investigation</b> only. Studies should cite batch-specific analytical documentation.</p>
<div class="coa">Every batch ships with a Certificate of Analysis (CoA) documenting purity and identity.</div>
<div class="cta">
  <a class="btn" href="{SITE_LINK}">Request specifications</a>
  <a class="btn ghost" href="{CS_LINK}">Talk to a specialist</a>
</div>
<div class="disclaimer" style="margin-top:28px">RTPeptide supplies compounds for scientific study. We do not provide dosing, protocol, or human-use guidance. Purchases are restricted to qualified research institutions and professionals.</div>
</div>
</body>
</html>"""


def ad_copy_rows():
    """生成 Google / LinkedIn / 原生广告 多组文案变体。"""
    rows = []
    headers = ["product", "channel", "variant", "headline", "body", "display_url"]
    for p in PRODUCTS:
        name = p["name"]
        cat = p["category"]
        focus = p.get("research_focus", "")[:90]
        slug = slugify(p["name"])
        lp = f"{SEO_BASE}/landing/{slug}.html"
        # Google Search (exact-match commercial intent, no claims)
        rows.append([name, "Google Search", "A",
                     f"{name} Research Peptide",
                     f"Lab-grade {name} ({cat}). Purity documented per batch. For scientific study. RUO.",
                     "rtpeptide.com"])
        rows.append([name, "Google Search", "B",
                     f"Buy {name} Peptide",
                     f"Research-grade {name}, {cat} catalogue. CoA per batch. Not for human use. Enquire.",
                     "rtpeptide.com"])
        # LinkedIn (B2B awareness)
        rows.append([name, "LinkedIn", "A",
                     f"{name} — research peptide for lab study",
                     f"Part of our {cat} research catalogue. Supplied with CoA for qualified institutions. Research Use Only.",
                     "rtpeptide.com"])
        # Native (Outbrain/Taboola)
        rows.append([name, "Native", "A",
                     f"What researchers should know about {name}",
                     f"A look at {name} ({cat}) as a laboratory material — purity, documentation, and research framing. RUO.",
                     "rtpeptide.com"])
        _ = lp  # landing page URL referenced by plan doc
    return headers, rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    n = 0
    for p in PRODUCTS:
        slug = slugify(p["name"])
        with open(os.path.join(OUT_DIR, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(landing_html(p))
        n += 1
    # ad copy csv
    headers, rows = ad_copy_rows()
    csv_path = os.path.join(os.path.dirname(OUT_DIR), "ad_copy.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"Built {n} RUO landing pages -> docs/peptide-seo/landing/")
    print(f"Built ad_copy.csv ({len(rows)} rows) -> docs/peptide-seo/ad_copy.csv")


if __name__ == "__main__":
    main()
