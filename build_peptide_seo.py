# -*- coding: utf-8 -*-
"""
RTPeptide 肽产品 SEO 静态站生成器（v2 — 程序化长尾引擎）

读取 peptide_products.py，生成搜索引擎友好的静态页矩阵：
- index.html                          首页（分类导航 + 最新文章 + 强 CTA）
- <category>.html                    8 个分类落地页
- products/<slug>.html               20 个产品页（含 JSON-LD Product + 面包屑）
- countries/<slug>.html              12 个国家/地区长尾页
- compare/<a>-vs-<b>.html            10 个对比页
- faq.html                           通用 FAQ（FAQPage 结构化数据）
- blog/<slug>.html                   12 篇科研科普文章（BlogPosting + RSS）
- rss.xml                            文章订阅源
- sitemap.xml / robots.txt / urls.txt

原则（不踩合规雷）：
- 全部 Research Use Only / Not for human consumption
- 不含价格、不含报价表单（报价系统独立开发，此处不碰）
- 只做科研科普 + 引流（Telegram 频道 + 官网）
"""

import os
import html
import json
import datetime

sys_path = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, sys_path)
from peptide_products import PRODUCTS, CATEGORIES, products_by_category

BASE_URL = "https://msli2233bin.github.io/broadfsc-automation/peptide-seo"
OUT_DIR = os.path.join(sys_path, "docs", "peptide-seo")
PRODUCTS_DIR = os.path.join(OUT_DIR, "products")
CAT_DIR = OUT_DIR
COUNTRY_DIR = os.path.join(OUT_DIR, "countries")
COMPARE_DIR = os.path.join(OUT_DIR, "compare")
BLOG_DIR = os.path.join(OUT_DIR, "blog")

SITE_NAME = "RTPeptide"
SITE_DESC = ("Research-grade peptides for laboratory study. Browse research peptides by "
             "category with sequences, purity and research focus. Research Use Only.")
CS_LINK = "https://t.me/rtpeptide_official"
SITE_LINK = "https://www.rawpeptidemfg.com"
UPDATED = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

DISCLAIMER_HTML = """
<div class="disclaimer">
  <b>Research Use Only.</b> All peptides listed are laboratory research chemicals and are not intended for
  human consumption, diagnostic, or therapeutic use. Product information is provided for research context only.
  Researchers must comply with all applicable regulations.
</div>
"""

CSS = """
:root{--bg:#04121f;--card:#0c2236;--blue:#3b82f6;--cyan:#22d3ee;--muted:#9fb3c8;--line:rgba(255,255,255,.08)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#e8f1fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.65}
a{color:var(--cyan);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:940px;margin:0 auto;padding:28px 20px 64px}
header{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.logo{font-size:25px;font-weight:800;background:linear-gradient(90deg,var(--blue),var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}
.tag{font-size:12px;color:var(--muted);border:1px solid var(--line);padding:3px 10px;border-radius:999px}
nav.top a{margin-left:14px;font-size:13px;color:var(--muted)}
h1{font-size:30px;margin:0 0 10px;line-height:1.25}
h2{font-size:21px;margin:30px 0 12px;color:#cfe9ff}
h3{font-size:17px;margin:22px 0 8px;color:#bfe2ff}
p{color:#dce8f4}
.small{font-size:13px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
@media(max-width:640px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:12px 0}
.cat{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;transition:.15s}
.cat:hover{border-color:rgba(34,211,238,.5);text-decoration:none;transform:translateY(-2px)}
.cat b{color:#e8f1fb;font-size:16px}
.cat span{display:block;color:var(--muted);font-size:13px;margin-top:4px}
.kv{display:flex;gap:10px;padding:6px 0;border-bottom:1px dashed var(--line);font-size:14px}
.kv .k{color:var(--muted);min-width:120px}
.kv .v{color:#e8f1fb;word-break:break-word}
.spec{background:rgba(34,211,238,.06);border-left:3px solid var(--cyan);padding:12px 16px;border-radius:8px;margin:14px 0;font-size:14px}
.disclaimer{margin-top:30px;padding:16px 18px;background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.3);border-radius:12px;font-size:13px;color:#f5e6c0}
.cta{margin-top:22px;display:flex;gap:12px;flex-wrap:wrap}
.btn{background:linear-gradient(90deg,var(--blue),var(--cyan));color:#04121f;font-weight:700;padding:11px 20px;border-radius:999px;font-size:14px;display:inline-block}
.btn.ghost{background:transparent;color:var(--cyan);border:1px solid var(--cyan)}
ul{margin:8px 0;padding-left:20px}
li{margin:5px 0}
.breadcrumb{font-size:13px;color:var(--muted);margin-bottom:14px}
.breadcrumb a{color:var(--muted)}
.faq{margin:10px 0}
.faq h3{margin-bottom:4px}
.faq p{margin-top:2px;color:#cfe0f0}
table.cmp{width:100%;border-collapse:collapse;font-size:14px;margin:14px 0}
table.cmp th,table.cmp td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}
table.cmp th{background:rgba(34,211,238,.08);color:#cfe9ff}
.related{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}
.related a{background:var(--card);border:1px solid var(--line);padding:8px 12px;border-radius:10px;font-size:13px}
.meta{font-size:12px;color:var(--muted);margin-top:6px}
footer{margin-top:40px;border-top:1px solid var(--line);padding-top:18px;color:var(--muted);font-size:13px}
"""

# ----------------------------------------------------------------------------
# 工具函数
# ----------------------------------------------------------------------------

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


def jld(obj):
    return json.dumps(obj, ensure_ascii=False)


def breadcrumb(prefix, trail):
    """trail: list of (name, rel_href, abs_path). 最后一个不链接。"""
    parts = []
    item_list = []
    n = len(trail)
    for i, (name, rel, abs_) in enumerate(trail, start=1):
        if i == n:
            parts.append(f'<span>{esc(name)}</span>')
        else:
            parts.append(f'<a href="{prefix}{rel}">{esc(name)}</a>')
        item = {"@type": "ListItem", "position": i, "name": name}
        if i < n:
            item["item"] = BASE_URL + "/" + abs_
        item_list.append(item)
    html_bc = ' &rsaquo; '.join(parts)
    json_bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": item_list}
    return f'<div class="breadcrumb">{html_bc}</div>', jld(json_bc)


def page_shell(title, description, body, canonical_rel, json_ld=None, nav_prefix=""):
    ld = ""
    if json_ld:
        if isinstance(json_ld, list):
            for x in json_ld:
                ld += f"\n<script type=\"application/ld+json\">{x}</script>"
        else:
            ld += f"\n<script type=\"application/ld+json\">{json_ld}</script>"
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
{ld}
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="logo">{SITE_NAME}</div>
  <nav class="top">
    <a href="{nav_prefix}index.html">Home</a>
    <a href="{nav_prefix}faq.html">FAQ</a>
    <a href="{nav_prefix}blog/index.html">Blog</a>
    <a href="{CS_LINK}">Telegram</a>
  </nav>
</header>
{body}
<footer>
  {SITE_NAME} supplies laboratory research chemicals. All products are Research Use Only and not for human consumption.
  &copy; {datetime.datetime.now(datetime.timezone.utc).year} {SITE_NAME}. &middot; <a href="{SITE_LINK}">rawpeptidemfg.com</a>
</footer>
</div>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# 首页
# ----------------------------------------------------------------------------

def build_index():
    cats_html = []
    for c in CATEGORIES:
        items = products_by_category(c)
        prods = "".join(
            f'<li><a href="products/{slugify(p["name"])}.html">{esc(p["name"])}</a></li>'
            for p in items
        )
        cats_html.append(f"""
<div class="card">
  <h2 style="margin-top:0"><a href="{slugify(c)}.html" style="color:#cfe9ff">{esc(c)} Research Peptides</a></h2>
  <ul>{prods}</ul>
  <p class="small"><a href="{slugify(c)}.html">Explore the {esc(c)} research catalogue &rarr;</a></p>
</div>""")
    articles = BLOG_ARTICLES[:5]
    art_html = "".join(
        f'<li><a href="blog/{a["slug"]}.html">{esc(a["title"])}</a></li>' for a in articles
    )
    body = f"""
<h1>Research-Grade Peptides by Category</h1>
<p>{esc(SITE_DESC)}</p>
<div class="cta">
  <a class="btn" href="{CS_LINK}">Talk to our team on Telegram</a>
  <a class="btn ghost" href="{SITE_LINK}">Visit {SITE_NAME}</a>
</div>
<div class="grid">{"".join(cats_html)}</div>
<div class="card">
  <h2 style="margin-top:0">From the Research Blog</h2>
  <ul>{art_html}</ul>
  <p class="small"><a href="blog/index.html">Read all articles &rarr;</a></p>
</div>
{DISCLAIMER_HTML}
"""
    return page_shell(
        f"{SITE_NAME} — Research-Grade Peptides by Category",
        SITE_DESC,
        body,
        "/index.html",
        json_ld=jld({"@context": "https://schema.org", "@type": "WebSite",
                     "name": SITE_NAME, "url": BASE_URL + "/",
                     "description": SITE_DESC}),
    )


# ----------------------------------------------------------------------------
# 产品页
# ----------------------------------------------------------------------------

def build_product(p):
    slug = slugify(p["name"])
    cat_slug = slugify(p["category"])
    seq = p.get("sequence", "N/A")
    kps = "".join(f"<li>{esc(k)}</li>" for k in p.get("key_points", []))
    related = [x for x in products_by_category(p["category"]) if x["name"] != p["name"]][:4]
    rel_html = "".join(
        f'<a href="{slugify(x["name"])}.html">{esc(x["name"])}</a>' for x in related
    )
    bc, bc_ld = breadcrumb("../", [("Home", "index.html", "index.html"),
                                    (p["category"], f"{cat_slug}.html", f"{cat_slug}.html"),
                                    (p["name"], f"products/{slug}.html", f"products/{slug}.html")])
    faq = [
        ("What is " + p["name"] + " used for in research?",
         f"{p['name']} is studied in laboratory settings for its " + p["research_focus"].split('.')[0].lower() + ". All work is conducted in vitro or in approved preclinical models under Research Use Only conditions."),
        ("Is " + p["name"] + " intended for human consumption?",
         "No. " + p["name"] + " is supplied strictly as a laboratory research chemical. It is not for human consumption, diagnostic, or therapeutic use."),
        ("What purity and form is " + p["name"] + " supplied in?",
         f"{p['name']} is supplied as a {esc(p.get('form','lyophilized powder'))} at {esc(p.get('purity','>=98%'))} purity, suitable for analytical and research applications."),
    ]
    faq_html = "".join(f'<div class="faq"><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in faq)
    faq_ld = jld({"@context": "https://schema.org", "@type": "FAQPage",
                  "mainEntity": [{"@type": "Question", "name": q,
                                  "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    prod_ld = jld({
        "@context": "https://schema.org", "@type": "Product",
        "name": p["name"], "description": p["research_focus"], "category": p["category"],
        "brand": {"@type": "Brand", "name": SITE_NAME},
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "CAS", "value": p.get("cas", "N/A")},
            {"@type": "PropertyValue", "name": "Purity", "value": p.get("purity", "N/A")},
            {"@type": "PropertyValue", "name": "Form", "value": p.get("form", "N/A")},
        ],
    })
    body = f"""
{bc}
<h1>{esc(p["name"])}</h1>
<p><b>Category:</b> <a href="../{cat_slug}.html">{esc(p["category"])}</a> &middot; <span class="small">Research peptide &middot; Last updated {UPDATED}</span></p>
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
<h2>Related {esc(p['category'])} Research Peptides</h2>
<div class="related">{rel_html}</div>
<h2>Frequently Asked Questions</h2>
{faq_html}
<div class="cta">
  <a class="btn" href="{CS_LINK}">Contact a specialist</a>
  <a class="btn ghost" href="{SITE_LINK}">Full specifications</a>
</div>
{DISCLAIMER_HTML}
"""
    title = f"{p['name']} — Research Peptide | {SITE_NAME}"
    desc = (f"{p['name']} research peptide ({p['category']}). "
            f"Sequence, purity and research focus for laboratory study. Research Use Only.")
    return page_shell(title, desc, body, f"/products/{slug}.html",
                      json_ld=[prod_ld, bc_ld, faq_ld], nav_prefix="../")


# ----------------------------------------------------------------------------
# 分类页
# ----------------------------------------------------------------------------

def build_category(c):
    cat_slug = slugify(c)
    items = products_by_category(c)
    cards = []
    for p in items:
        cards.append(f"""
<div class="card">
  <h3 style="margin-top:0"><a href="products/{slugify(p['name'])}.html" style="color:#bfe2ff">{esc(p['name'])}</a></h3>
  <p class="small">{esc(p.get('research_focus',''))}</p>
  <p class="small">CAS {esc(p.get('cas','N/A'))} &middot; Purity {esc(p.get('purity','N/A'))}</p>
</div>""")
    bc, bc_ld = breadcrumb("", [("Home", "index.html", "index.html"),
                                 (c, f"{cat_slug}.html", f"{cat_slug}.html")])
    intro = CATEGORY_INTRO.get(c, f"The {c} research area covers laboratory peptides studied for their role in {c.lower()} pathways.")
    faq = [
        (f"What peptides are studied in {c} research?",
         f"Our {c} research catalogue includes " + ", ".join(esc(p["name"]) for p in items) + ". Each is supplied as a laboratory research chemical under Research Use Only conditions."),
        (f"Are {c} peptides for human use?",
         "No. All peptides in this category are research chemicals, not for human consumption, diagnostic, or therapeutic use."),
    ]
    faq_html = "".join(f'<div class="faq"><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in faq)
    faq_ld = jld({"@context": "https://schema.org", "@type": "FAQPage",
                  "mainEntity": [{"@type": "Question", "name": q,
                                  "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    body = f"""
{bc}
<h1>{esc(c)} Research Peptides</h1>
<p>{esc(intro)}</p>
<div class="grid">{"".join(cards)}</div>
<h2>Frequently Asked Questions</h2>
{faq_html}
<div class="cta">
  <a class="btn" href="{CS_LINK}">Discuss your research needs</a>
  <a class="btn ghost" href="index.html">All categories</a>
</div>
{DISCLAIMER_HTML}
"""
    title = f"{c} Research Peptides | {SITE_NAME}"
    desc = f"{c} research peptides for laboratory study. Browse sequences, purity and research focus. Research Use Only."
    return page_shell(title, desc, body, f"/{cat_slug}.html", json_ld=[bc_ld, faq_ld])


# ----------------------------------------------------------------------------
# 国家/地区长尾页
# ----------------------------------------------------------------------------

COUNTRIES = [
    ("United States", "united-states"),
    ("United Kingdom", "united-kingdom"),
    ("Canada", "canada"),
    ("Australia", "australia"),
    ("Germany", "germany"),
    ("France", "france"),
    ("Netherlands", "netherlands"),
    ("Switzerland", "switzerland"),
    ("Sweden", "sweden"),
    ("Singapore", "singapore"),
    ("Japan", "japan"),
    ("New Zealand", "new-zealand"),
]

def build_country(name, cslug):
    bc, bc_ld = breadcrumb("../", [("Home", "index.html", "index.html"),
                                   (name, f"countries/{cslug}.html", f"countries/{cslug}.html")])
    cat_links = "".join(
        f'<li><a href="../{slugify(c)}.html">{esc(c)} research peptides</a></li>' for c in CATEGORIES
    )
    body = f"""
{bc}
<h1>Research Peptides in {esc(name)}</h1>
<p>{SITE_NAME} supplies research-grade peptides to laboratories and research institutions in {esc(name)}.
All materials are provided strictly for scientific study under Research Use Only conditions — not for human
consumption, diagnostic, or therapeutic use.</p>
<h2>Browse by Research Area</h2>
<ul>{cat_links}</ul>
<h2>Responsible Research Supply</h2>
<p>We support {esc(name)}-based research teams with documented laboratory chemicals, consistent purity, and
clear chain-of-custody information. Orders are handled through verified research channels only.</p>
<div class="cta">
  <a class="btn" href="{CS_LINK}">Contact our team</a>
  <a class="btn ghost" href="../index.html">Full catalogue</a>
</div>
{DISCLAIMER_HTML}
"""
    title = f"Research Peptides in {name} | {SITE_NAME}"
    desc = f"Research-grade peptides supplied to laboratories in {name}. Browse by research area. Research Use Only."
    return page_shell(title, desc, body, f"/countries/{cslug}.html", json_ld=bc_ld, nav_prefix="../")


# ----------------------------------------------------------------------------
# 对比页
# ----------------------------------------------------------------------------

COMPARES = [
    ("Semaglutide", "Tirzepatide"),
    ("Semaglutide", "Retatrutide"),
    ("Tirzepatide", "Retatrutide"),
    ("BPC-157", "TB-500 (Thymosin Beta-4)"),
    ("BPC-157", "GHK-Cu"),
    ("CJC-1295 (no DAC)", "Ipamorelin"),
    ("CJC-1295 (no DAC)", "GHRP-6"),
    ("Ipamorelin", "GHRP-6"),
    ("Semax", "Selank"),
    ("Melanotan II", "PT-141 (Bremelanotide)"),
]

def find_prod(name):
    for p in PRODUCTS:
        if p["name"] == name:
            return p
    return None

def build_compare(a_name, b_name):
    a, b = find_prod(a_name), find_prod(b_name)
    if not a or not b:
        return None
    sa, sb = slugify(a["name"]), slugify(b["name"])
    bc, bc_ld = breadcrumb("../", [("Home", "index.html", "index.html"),
                                   (f"{a_name} vs {b_name}", f"compare/{sa}-vs-{sb}.html",
                                    f"compare/{sa}-vs-{sb}.html")])
    rows = []
    for label, key in [("Category", "category"), ("CAS", "cas"), ("Sequence", "sequence"),
                       ("Purity", "purity"), ("Form", "form"), ("Research Focus", "research_focus")]:
        rows.append(f"<tr><th>{label}</th><td>{esc(a.get(key,'N/A'))}</td><td>{esc(b.get(key,'N/A'))}</td></tr>")
    body = f"""
{bc}
<h1>{esc(a_name)} vs {esc(b_name)} — Research Peptide Comparison</h1>
<p>Both {esc(a_name)} and {esc(b_name)} are supplied as laboratory research chemicals for scientific study.
This page compares their documented research characteristics. Research Use Only — not for human consumption.</p>
<table class="cmp">
  <tr><th>Attribute</th><th><a href="../products/{sa}.html">{esc(a_name)}</a></th><th><a href="../products/{sb}.html">{esc(b_name)}</a></th></tr>
  {"".join(rows)}
</table>
<h2>Research Context</h2>
<p><b>{esc(a_name)}:</b> {esc(a.get('research_focus',''))}</p>
<p><b>{esc(b_name)}:</b> {esc(b.get('research_focus',''))}</p>
<div class="cta">
  <a class="btn" href="{CS_LINK}">Ask a specialist</a>
  <a class="btn ghost" href="../index.html">All peptides</a>
</div>
{DISCLAIMER_HTML}
"""
    title = f"{a_name} vs {b_name} — Research Peptide Comparison | {SITE_NAME}"
    desc = f"Compare {a_name} and {b_name} research peptides: category, CAS, sequence, purity and research focus. Research Use Only."
    return page_shell(title, desc, body, f"/compare/{sa}-vs-{sb}.html", json_ld=bc_ld, nav_prefix="../")


# ----------------------------------------------------------------------------
# FAQ 页
# ----------------------------------------------------------------------------

FAQS = [
    ("What does Research Use Only mean?",
     "Research Use Only (RUO) means the material is supplied exclusively for scientific laboratory research. It is not a drug, food, supplement, or diagnostic, and is not for human or animal consumption."),
    ("Are RTPeptide products for human consumption?",
     "No. Every peptide we list is a laboratory research chemical. We do not sell products for human therapeutic, diagnostic, or consumptive use."),
    ("What information is provided for each peptide?",
     "Each product page lists the peptide name, research category, sequence, CAS number, purity, form, and a summary of its documented research focus. Pricing and ordering are handled through separate verified channels."),
    ("How are peptides supplied?",
     "Peptides are supplied as lyophilized powders at documented purity levels, suitable for analytical and research applications in controlled laboratory environments."),
    ("Do you ship internationally for research?",
     "We support research institutions globally with documented laboratory chemicals. All handling complies with applicable regulations for research-grade materials."),
    ("How should research peptides be stored?",
     "Lyophilized research peptides are typically stored under recommended cold, dry conditions. Specific handling guidance should follow your institution's laboratory protocols."),
]

def build_faq():
    bc, bc_ld = breadcrumb("", [("Home", "index.html", "index.html"), ("FAQ", "faq.html", "faq.html")])
    faq_html = "".join(f'<div class="faq"><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in FAQS)
    faq_ld = jld({"@context": "https://schema.org", "@type": "FAQPage",
                  "mainEntity": [{"@type": "Question", "name": q,
                                  "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]})
    body = f"""
{bc}
<h1>Frequently Asked Questions</h1>
<p>General information about {SITE_NAME} research peptides and responsible laboratory supply.</p>
{faq_html}
<div class="cta">
  <a class="btn" href="{CS_LINK}">Contact our team</a>
  <a class="btn ghost" href="index.html">Browse catalogue</a>
</div>
{DISCLAIMER_HTML}
"""
    return page_shell("FAQ — Research Peptides | " + SITE_NAME,
                      "Answers about Research Use Only peptides, supply, storage and compliance. Research Use Only.",
                      body, "/faq.html", json_ld=[bc_ld, faq_ld])


# ----------------------------------------------------------------------------
# 博客 / 科普文章
# ----------------------------------------------------------------------------

CATEGORY_INTRO = {
    "Weight Management": "The Weight Management research area covers incretin and metabolic peptides studied for appetite, glucose, and energy-balance pathways in preclinical models.",
    "Healing & Repair": "The Healing & Repair research area covers peptides studied for tissue regeneration, angiogenesis, and wound-healing pathways in vitro.",
    "Anti-Aging": "The Anti-Aging research area covers mitochondrial, telomerase, and sirtuin-pathway peptides studied in cellular aging models.",
    "Growth Hormone": "The Growth Hormone research area covers GHRH analogs and GH secretagogues studied for endocrine and release-pulse patterns.",
    "Cognitive & Mood": "The Cognitive & Mood research area covers nootropic and anxiolytic peptides studied for CNS, neuroprotection, and BDNF pathways.",
    "Skin & Beauty": "The Skin & Beauty research area covers pigmentation and regeneration peptides studied for photoprotection and tissue models.",
    "Sexual Health": "The Sexual Health research area covers melanocortin agonists studied for central pathways in research models.",
    "Sleep & Recovery": "The Sleep & Recovery research area covers peptides studied for sleep architecture and stress-response regulation.",
}

BLOG_ARTICLES = [
    {"slug": "understanding-glp1-receptor-agonists", "title": "Understanding GLP-1 Receptor Agonists in Metabolic Research",
     "cat": "Weight Management",
     "paras": [
        "Glucagon-like peptide-1 (GLP-1) receptor agonists are among the most studied classes of metabolic research peptides. In laboratory models they are examined for their effects on appetite-regulation pathways and glucose-metabolism signaling.",
        "Semaglutide and Tirzepatide are frequently referenced in metabolic research. While Tirzepatide is studied as a dual GIP/GLP-1 receptor agonist, Retatrutide extends the model to a triple-agonist approach (GLP-1/GIP/glucagon). Each is supplied strictly as a research chemical.",
        "Researchers investigating metabolic pathways typically compare receptor selectivity, sequence structure, and documented in-vitro behavior. Our catalogue provides sequence, CAS, and purity data to support that comparison.",
        "All metabolic peptides discussed here are Research Use Only and are not for human consumption, diagnostic, or therapeutic use."]},
    {"slug": "tissue-repair-peptides-wound-healing", "title": "The Role of Tissue Repair Peptides in Wound-Healing Models",
     "cat": "Healing & Repair",
     "paras": [
        "Tissue repair peptides represent a major research area for regeneration and angiogenesis studies. BPC-157, a 15-amino-acid gastric peptide, is extensively studied for tissue-repair pathways in vitro.",
        "TB-500 (a Thymosin Beta-4 fragment) and GHK-Cu (a copper peptide) are also common subjects, examined respectively for cell-migration and collagen-synthesis pathways.",
        "Because these peptides target distinct mechanisms, research teams often study them in combination to model complex wound-healing environments. Documented purity and sequence data are essential for reproducible work.",
        "These materials are laboratory research chemicals only — not for human consumption."]},
    {"slug": "mitochondrial-peptides-cellular-aging", "title": "Mitochondrial Peptides and Cellular Aging: A Research Overview",
     "cat": "Anti-Aging",
     "paras": [
        "Mitochondrial-derived peptides have become a focus of cellular-aging research. MOTS-c, for example, is studied for metabolic homeostasis and insulin-sensitivity pathways.",
        "Alongside MOTS-c, Epitalon (a tetrapeptide) is researched for telomerase activation and circadian-rhythm regulation, while NAD+ is studied for mitochondrial energy metabolism and sirtuin-pathway support.",
        "Aging research benefits from comparing peptides that act on different nodes of the same network. Our product pages document the research focus of each agent to aid that comparison.",
        "All listed peptides are Research Use Only and not for human consumption."]},
    {"slug": "growth-hormone-secretagogues", "title": "Growth Hormone Secretagogues: Mechanisms and Research Applications",
     "cat": "Growth Hormone",
     "paras": [
        "Growth hormone (GH) secretagogues are studied for their ability to stimulate endogenous GH release patterns in endocrine research. CJC-1295 (no DAC) is a GHRH analog examined for sustained GH pulse patterns.",
        "Ipamorelin is a selective GH secretagogue researched for GH release without prolactin or cortisol spikes, while GHRP-6 is a hexapeptide studied for GH stimulation and appetite pathways.",
        "Comparing selectivity profiles helps researchers choose appropriate models. Sequence and purity documentation supports reproducible endocrine studies.",
        "These peptides are laboratory research chemicals, not for human consumption."]},
    {"slug": "cognitive-peptides-semax-selank", "title": "Cognitive Peptides: Semax and Selank in CNS Research",
     "cat": "Cognitive & Mood",
     "paras": [
        "Cognitive research peptides target central nervous system pathways. Semax, a synthetic nootropic peptide, is studied for neuroprotection and cognitive-function pathways.",
        "Selank, an anxiolytic peptide, is researched for anxiety regulation and BDNF expression in CNS models. The two are often compared for their distinct mechanistic profiles.",
        "CNS research demands high-purity, well-characterized materials. Our catalogue provides CAS, sequence, and purity for each cognitive peptide.",
        "Supplied as Research Use Only laboratory chemicals — not for human consumption."]},
    {"slug": "anti-aging-peptide-research", "title": "Anti-Aging Peptide Research: Telomerase and Sirtuin Pathways",
     "cat": "Anti-Aging",
     "paras": [
        "Anti-aging peptide research spans multiple pathways. Epitalon is studied for telomerase activation, while NAD+ is examined for sirtuin-pathway and mitochondrial-energy support.",
        "MOTS-c adds a mitochondrial dimension, linking metabolic homeostasis to cellular-ageing models. Together these agents let researchers probe aging from several angles.",
        "Reproducible aging research depends on documented purity and storage conditions. Product pages summarize each peptide's research focus for reference.",
        "All materials are Research Use Only, not for human consumption."]},
    {"slug": "peptide-purity-lyophilization", "title": "Peptide Purity and Lyophilization in Laboratory Research",
     "cat": "Healing & Repair",
     "paras": [
        "Purity and formulation are foundational to reproducible peptide research. Most research peptides are supplied as lyophilized powders, which stabilize the material for storage and transport.",
        "Documented purity (commonly ≥98% or ≥99%) and verified sequence are critical for interpreting experimental results. CAS numbers provide a standard identifier across studies.",
        "Our catalogue lists purity, form, and CAS for every peptide to support laboratory documentation and chain-of-custody requirements.",
        "These are research chemicals only — not for human consumption."]},
    {"slug": "research-use-only-compliance", "title": "Research Use Only: Compliance and Responsible Handling",
     "cat": "Sexual Health",
     "paras": [
        "'Research Use Only' (RUO) is a strict supply classification. It means a material is provided exclusively for scientific laboratory study and is not a drug, food, supplement, or diagnostic.",
        "RUO peptides must not be used for human or animal consumption. Laboratories handling them should follow institutional protocols for storage, documentation, and disposal.",
        "Responsible suppliers provide clear labeling, documented purity, and transparent research-context information — never therapeutic or consumption claims.",
        "RTPeptide lists every peptide under Research Use Only conditions, with no human-use claims."]},
    {"slug": "dual-triple-incretin-agonists", "title": "Comparing Dual and Triple Incretin Agonists in Metabolic Studies",
     "cat": "Weight Management",
     "paras": [
        "Incretin-based metabolic research has evolved from single to multi-receptor agonists. Semaglutide targets GLP-1; Tirzepatide adds GIP (dual); Retatrutide adds glucagon (triple).",
        "Each design is studied for how receptor combination affects metabolic signaling in preclinical models. Researchers compare selectivity, sequence architecture, and documented behavior.",
        "Our comparison pages let teams place these agents side by side with their CAS, sequence, and research focus for reference.",
        "All are Research Use Only laboratory chemicals, not for human consumption."]},
    {"slug": "copper-peptides-skin-regeneration", "title": "Copper Peptides (GHK-Cu) in Skin and Tissue Regeneration Research",
     "cat": "Skin & Beauty",
     "paras": [
        "GHK-Cu is a copper-peptide complex studied for collagen-synthesis and skin-tissue regeneration pathways. It is a common subject in regeneration research models.",
        "Its mechanism is distinct from gastric repair peptides such as BPC-157, making it useful for comparative tissue-engineering studies.",
        "Documented purity and sequence are important for regeneration assays. Product pages provide this data for reference.",
        "GHK-Cu is supplied as a Research Use Only laboratory chemical, not for human consumption."]},
    {"slug": "sleep-recovery-peptides-dsip", "title": "Sleep and Recovery Peptides: DSIP and Mechanisms",
     "cat": "Sleep & Recovery",
     "paras": [
        "Sleep and recovery research includes peptides studied for sleep architecture and stress-response regulation. DSIP (delta sleep-inducing peptide) is a representative example.",
        "Such peptides are examined in models of sleep-stage regulation rather than as consumable products. Mechanistic clarity depends on well-characterized materials.",
        "Our catalogue documents the research focus of each sleep-related peptide to support study design.",
        "These are Research Use Only chemicals, not for human consumption."]},
    {"slug": "sourcing-research-chemicals", "title": "Sourcing Research-Grade Peptides: What Laboratories Should Verify",
     "cat": "Growth Hormone",
     "paras": [
        "Sourcing research-grade peptides requires verifying several fundamentals: documented purity, verified sequence, CAS identification, and transparent research-context information.",
        "Reputable research suppliers avoid therapeutic or consumption claims and label everything Research Use Only. Chain-of-custody and storage guidance further support reproducible science.",
        "Our catalogue is structured to give laboratories quick access to sequence, CAS, purity, and research-focus data for each peptide.",
        "RTPeptide supplies laboratory research chemicals only — never for human consumption."]},
]

def build_blog_index():
    items = "".join(
        f'<li><a href="{a["slug"]}.html">{esc(a["title"])}</a> <span class="small">&middot; {esc(a["cat"])}</span></li>'
        for a in BLOG_ARTICLES
    )
    bc, bc_ld = breadcrumb("../", [("Home", "index.html", "index.html"),
                                   ("Blog", "blog/index.html", "blog/index.html")])
    body = f"""
{bc}
<h1>RTPeptide Research Blog</h1>
<p>Educational articles on peptide research areas, mechanisms, and responsible laboratory supply. Research Use Only.</p>
<ul>{items}</ul>
<div class="cta">
  <a class="btn" href="{CS_LINK}">Talk to our team</a>
  <a class="btn ghost" href="../index.html">Peptide catalogue</a>
</div>
{DISCLAIMER_HTML}
"""
    return page_shell("RTPeptide Research Blog | " + SITE_NAME,
                      "Educational articles on peptide research areas, mechanisms, and responsible laboratory supply. Research Use Only.",
                      body, "/blog/index.html", json_ld=bc_ld, nav_prefix="../")


def build_blog_article(a):
    bc, bc_ld = breadcrumb("../", [("Home", "index.html", "index.html"),
                                   ("Blog", "blog/index.html", "blog/index.html"),
                                   (a["title"], f"blog/{a['slug']}.html", f"blog/{a['slug']}.html")])
    paras = "".join(f"<p>{esc(t)}</p>" for t in a["paras"])
    art_ld = jld({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": a["title"], "datePublished": UPDATED, "dateModified": UPDATED,
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "description": a["paras"][0],
        "mainEntityOfPage": {"@type": "WebPage", "@id": BASE_URL + "/blog/" + a["slug"] + ".html"},
    })
    body = f"""
{bc}
<h1>{esc(a["title"])}</h1>
<p class="meta">Research area: <a href="../{slugify(a['cat'])}.html">{esc(a['cat'])}</a> &middot; Updated {UPDATED}</p>
{paras}
<div class="cta">
  <a class="btn" href="{CS_LINK}">Discuss with our team</a>
  <a class="btn ghost" href="../{slugify(a['cat'])}.html">{esc(a['cat'])} peptides</a>
</div>
{DISCLAIMER_HTML}
"""
    return page_shell(a["title"] + " | " + SITE_NAME, a["paras"][0], body, f"/blog/{a['slug']}.html",
                      json_ld=[bc_ld, art_ld], nav_prefix="../")


def build_rss():
    items = []
    for a in BLOG_ARTICLES:
        link = BASE_URL + "/blog/" + a["slug"] + ".html"
        desc = esc(a["paras"][0])
        items.append(f"""  <item>
    <title>{esc(a['title'])}</title>
    <link>{link}</link>
    <guid>{link}</guid>
    <pubDate>{datetime.datetime(2026,1,1).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
    <description>{desc}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{SITE_NAME} Research Blog</title>
  <link>{BASE_URL}/blog/index.html</link>
  <description>Educational articles on peptide research. Research Use Only.</description>
{''.join(items)}
</channel>
</rss>
"""


# ----------------------------------------------------------------------------
# Sitemap / robots / urls
# ----------------------------------------------------------------------------

def all_urls():
    urls = [BASE_URL + "/index.html", BASE_URL + "/faq.html", BASE_URL + "/blog/index.html"]
    for c in CATEGORIES:
        urls.append(f"{BASE_URL}/{slugify(c)}.html")
    for p in PRODUCTS:
        urls.append(f"{BASE_URL}/products/{slugify(p['name'])}.html")
    for _, cslug in COUNTRIES:
        urls.append(f"{BASE_URL}/countries/{cslug}.html")
    for a, b in COMPARES:
        urls.append(f"{BASE_URL}/compare/{slugify(a)}-vs-{slugify(b)}.html")
    for a in BLOG_ARTICLES:
        urls.append(f"{BASE_URL}/blog/{a['slug']}.html")
    return urls


def build_sitemap():
    urls = all_urls()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f"  <url><loc>{u}</loc><lastmod>{UPDATED}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>")
    lines.append("</urlset>")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    os.makedirs(PRODUCTS_DIR, exist_ok=True)
    os.makedirs(COUNTRY_DIR, exist_ok=True)
    os.makedirs(COMPARE_DIR, exist_ok=True)
    os.makedirs(BLOG_DIR, exist_ok=True)

    written = 0
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index()); written += 1
    with open(os.path.join(OUT_DIR, "faq.html"), "w", encoding="utf-8") as f:
        f.write(build_faq()); written += 1
    with open(os.path.join(BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_blog_index()); written += 1

    for c in CATEGORIES:
        with open(os.path.join(OUT_DIR, slugify(c) + ".html"), "w", encoding="utf-8") as f:
            f.write(build_category(c)); written += 1

    for p in PRODUCTS:
        with open(os.path.join(PRODUCTS_DIR, slugify(p["name"]) + ".html"), "w", encoding="utf-8") as f:
            f.write(build_product(p)); written += 1

    for name, cslug in COUNTRIES:
        with open(os.path.join(COUNTRY_DIR, cslug + ".html"), "w", encoding="utf-8") as f:
            f.write(build_country(name, cslug)); written += 1

    for a, b in COMPARES:
        html_doc = build_compare(a, b)
        if html_doc:
            with open(os.path.join(COMPARE_DIR, f"{slugify(a)}-vs-{slugify(b)}.html"), "w", encoding="utf-8") as f:
                f.write(html_doc); written += 1

    for a in BLOG_ARTICLES:
        with open(os.path.join(BLOG_DIR, a["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(build_blog_article(a)); written += 1

    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap())
    with open(os.path.join(OUT_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(build_rss())
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    with open(os.path.join(OUT_DIR, "urls.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(all_urls()))

    print(f"Built {written} HTML pages + sitemap + rss + robots into peptide-seo/")


if __name__ == "__main__":
    main()
