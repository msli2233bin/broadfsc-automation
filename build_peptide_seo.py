# -*- coding: utf-8 -*-
"""
RTPeptide 肽产品 SEO 静态站生成器

读取 peptide_products.py 的产品数据，生成搜索引擎友好的静态页：
- peptide-seo/index.html        分类落地页（长尾入口）
- peptide-seo/products/<slug>.html  每个产品一个页
- peptide-seo/sitemap.xml
- peptide-seo/robots.txt

原则（不踩合规雷）：
- 全部 Research Use Only / Not for human consumption
- 不含价格、不含报价表单（报价系统独立开发，此处不碰）
- 只做科研科普 + 引流（Telegram 频道 + 官网）
"""

import os
import html
import datetime

sys_path = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, sys_path)
from peptide_products import PRODUCTS, CATEGORIES, products_by_category

BASE_URL = "https://msli2233bin.github.io/broadfsc-automation"
OUT_DIR = os.path.join(sys_path, "peptide-seo")
PRODUCTS_DIR = os.path.join(OUT_DIR, "products")

SITE_NAME = "RTPeptide"
SITE_DESC = ("Research-grade peptides for laboratory study. Browse research peptides by "
             "category with sequences, purity and research focus. Research Use Only.")

CS_LINK = "https://t.me/rtpeptide_official"
SITE_LINK = "https://www.rawpeptidemfg.com"

CSS = """
:root{--bg:#04121f;--card:#0c2236;--blue:#3b82f6;--cyan:#22d3ee;--muted:#9fb3c8;--line:rgba(255,255,255,.08)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#e8f1fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.6}
a{color:var(--cyan);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:920px;margin:0 auto;padding:32px 20px 64px}
header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:28px}
.logo{font-size:26px;font-weight:800;background:linear-gradient(90deg,var(--blue),var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}
.tag{display:inline-block;margin-top:8px;font-size:12px;color:var(--muted);border:1px solid var(--line);padding:3px 10px;border-radius:999px}
h1{font-size:30px;margin:0 0 10px}
h2{font-size:20px;margin:30px 0 12px;color:#cfe9ff}
p{color:#dce8f4}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
@media(max-width:640px){.grid{grid-template-columns:1fr}}
.cat{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;transition:.15s}
.cat:hover{border-color:rgba(34,211,238,.5);text-decoration:none;transform:translateY(-2px)}
.cat b{color:#e8f1fb;font-size:16px}
.cat span{display:block;color:var(--muted);font-size:13px;margin-top:4px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin:16px 0}
.kv{display:flex;gap:10px;padding:6px 0;border-bottom:1px dashed var(--line);font-size:14px}
.kv .k{color:var(--muted);min-width:110px}
.kv .v{color:#e8f1fb;word-break:break-word}
.spec{background:rgba(34,211,238,.06);border-left:3px solid var(--cyan);padding:12px 16px;border-radius:8px;margin:14px 0;font-size:14px}
.disclaimer{margin-top:34px;padding:16px 18px;background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.3);border-radius:12px;font-size:13px;color:#f5e6c0}
.cta{margin-top:22px;display:flex;gap:12px;flex-wrap:wrap}
.btn{background:linear-gradient(90deg,var(--blue),var(--cyan));color:#04121f;font-weight:700;padding:11px 20px;border-radius:999px;font-size:14px}
.btn.ghost{background:transparent;color:var(--cyan);border:1px solid var(--cyan)}
ul{margin:8px 0;padding-left:20px}
li{margin:4px 0}
footer{margin-top:40px;border-top:1px solid var(--line);padding-top:18px;color:var(--muted);font-size:13px}
"""


def slugify(name):
    s = name.lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in " -/":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def esc(t):
    return html.escape(str(t))


def page_shell(title, description, body, canonical_rel):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{BASE_URL}{canonical_rel}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta name="robots" content="index,follow">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="logo">{SITE_NAME}</div>
  <div class="tag">Research-grade peptides · Research Use Only</div>
</header>
{body}
<footer>
  {SITE_NAME} supplies laboratory research chemicals. All products are Research Use Only and not for human consumption.
  &copy; {datetime.datetime.now(datetime.timezone.utc).year} {SITE_NAME}.
</footer>
</div>
</body>
</html>
"""


def build_index():
    cats_html = []
    for c in CATEGORIES:
        items = products_by_category(c)
        cat_link = f"#cat-{slugify(c)}"
        # list products under category on index
        prods = "".join(
            f'<li><a href="products/{slugify(p["name"])}.html">{esc(p["name"])}</a></li>'
            for p in items
        )
        cats_html.append(f"""
<div class="card" id="cat-{slugify(c)}">
  <h2 style="margin-top:0">{esc(c)}</h2>
  <ul>{prods}</ul>
</div>""")
    body = f"""
<h1>Research-Grade Peptides by Category</h1>
<p>{esc(SITE_DESC)}</p>
<div class="cta">
  <a class="btn" href="{CS_LINK}">Talk to our team on Telegram</a>
  <a class="btn ghost" href="{SITE_LINK}">Visit {SITE_NAME}</a>
</div>
{''.join(cats_html)}
<div class="disclaimer">
  <b>Research Use Only.</b> All peptides listed are laboratory research chemicals and are not intended for
  human consumption, diagnostic, or therapeutic use. Product information is provided for research context only.
</div>
"""
    return page_shell(
        f"{SITE_NAME} — Research-Grade Peptides by Category",
        SITE_DESC,
        body,
        "/",
    )


def build_product(p):
    slug = slugify(p["name"])
    seq = p.get("sequence", "N/A")
    kps = "".join(f"<li>{esc(k)}</li>" for k in p.get("key_points", []))
    body = f"""
<h1>{esc(p["name"])}</h1>
<p><b>Category:</b> <a href="../#cat-{slugify(p['category'])}">{esc(p['category'])}</a></p>

<div class="spec">
  <div class="kv"><span class="k">Sequence</span><span class="v">{esc(seq)}</span></div>
  <div class="kv"><span class="k">Purity</span><span class="v">{esc(p.get('purity','N/A'))}</span></div>
  <div class="kv"><span class="k">Form</span><span class="v">{esc(p.get('form','N/A'))}</span></div>
  <div class="kv"><span class="k">CAS</span><span class="v">{esc(p.get('cas','N/A'))}</span></div>
</div>

<h2>Research Focus</h2>
<p>{esc(p.get('research_focus',''))}</p>

<h2>Key Research Points</h2>
<ul>{kps}</ul>

<div class="cta">
  <a class="btn" href="{CS_LINK}">Contact a specialist</a>
  <a class="btn ghost" href="{SITE_LINK}">Full specifications</a>
</div>

<div class="disclaimer">
  <b>Research Use Only.</b> {esc(p['name'])} is supplied as a laboratory research chemical. Not for human
  consumption, diagnostic, or therapeutic use. Researchers must comply with all applicable regulations.
</div>
"""
    title = f"{p['name']} — Research Peptide | {SITE_NAME}"
    desc = (f"{p['name']} research peptide ({p['category']}). "
            f"Sequence, purity and research focus for laboratory study. Research Use Only.")
    return page_shell(title, desc, body, f"/products/{slug}.html")


def build_sitemap():
    urls = [BASE_URL + "/"]
    for p in PRODUCTS:
        urls.append(f"{BASE_URL}/products/{slugify(p['name'])}.html")
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq></url>")
    lines.append("</urlset>")
    return "\n".join(lines)


def main():
    os.makedirs(PRODUCTS_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index())
    count = 0
    for p in PRODUCTS:
        slug = slugify(p["name"])
        with open(os.path.join(PRODUCTS_DIR, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(build_product(p))
        count += 1
    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap())
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    print(f"Built {count} product pages + index + sitemap into peptide-seo/")


if __name__ == "__main__":
    main()
