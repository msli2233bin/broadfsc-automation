"""
RTPeptide 多渠道推广引擎
================================
把肽产品科研内容自动发到多个渠道。每个渠道可独立开关（读环境变量），
没有凭据的渠道自动跳过，不会报错。

已验证可发: Telegram(在 peptide_promotion.py), Bluesky
代码就绪待 key: X/Twitter, LinkedIn, Pinterest

合规: 所有内容强制 Research Use Only 框架，绝不做疗效/人体使用暗示。
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peptide_products import PRODUCTS

SITE_URL = "https://www.rawpeptidemfg.com"
CHANNEL_URL = "https://t.me/rtpeptide_official"
SEO_BASE = "https://msli2233bin.github.io/broadfsc-automation/peptide-seo"

DISCLAIMER = "Research Use Only. Not for human consumption."


def slugify(name):
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -/" and out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


UA = {"User-Agent": "Mozilla/5.0 (compatible; RTPeptideBot/1.0)"}


def _post_json(url, payload, headers, timeout=20):
    data = json.dumps(payload).encode()
    h = dict(UA)
    h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        body = r.read().decode()
        return True, json.loads(body) if body else {"ok": True}
    except urllib.error.HTTPError as e:
        raw = e.fp.read().decode() if e.fp else ""
        try:
            detail = json.loads(raw) if raw else {"error": e.code, "reason": e.reason}
        except Exception:  # noqa
            detail = {"error": e.code, "reason": e.reason, "body": raw[:300]}
        return False, detail
    except Exception as e:  # noqa
        return False, {"error": str(e)}


# ---------------------------------------------------------------------------
# Bluesky (AT Protocol) — 已验证
# ---------------------------------------------------------------------------
def post_bluesky(text, dry_run=False):
    handle = os.environ.get("BLUESKY_HANDLE")
    pw = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not pw:
        return {"ok": False, "skip": True, "reason": "no BLUESKY_HANDLE/APP_PASSWORD"}
    if dry_run:
        return {"ok": True, "dry": True, "len": len(text)}
    # 1) create session
    ok, ses = _post_json(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        {"identifier": handle, "password": pw},
        {"Content-Type": "application/json"},
    )
    if not ok:
        return {"ok": False, "reason": "session failed", "detail": ses}
    jwt = ses["accessJwt"]
    did = ses["did"]
    # 2) create post record (<=300 graphemes)
    record = {
        "$type": "app.bsky.feed.post",
        "text": text[:300],
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    ok2, res = _post_json(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        {"repo": did, "collection": "app.bsky.feed.post", "record": record},
        {"Content-Type": "application/json", "Authorization": "Bearer " + jwt},
    )
    return {"ok": ok2, "detail": res} if ok2 else {"ok": False, "reason": "post failed", "detail": res}


# ---------------------------------------------------------------------------
# X / Twitter (API v2) — 待 BEARER_TOKEN
# ---------------------------------------------------------------------------
def post_x(text, dry_run=False):
    token = os.environ.get("X_BEARER_TOKEN")
    if not token:
        return {"ok": False, "skip": True, "reason": "no X_BEARER_TOKEN"}
    if dry_run:
        return {"ok": True, "dry": True, "len": len(text)}
    ok, res = _post_json(
        "https://api.twitter.com/2/tweets",
        {"text": text[:280]},
        {"Content-Type": "application/json", "Authorization": "Bearer " + token},
    )
    return {"ok": ok, "detail": res}


# ---------------------------------------------------------------------------
# LinkedIn (UGC Posts API) — 待 ACCESS_TOKEN + USER_URN
# ---------------------------------------------------------------------------
def post_linkedin(text, link="", dry_run=False):
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    urn = os.environ.get("LINKEDIN_USER_URN")
    if not token or not urn:
        return {"ok": False, "skip": True, "reason": "no LINKEDIN_ACCESS_TOKEN/USER_URN"}
    if dry_run:
        return {"ok": True, "dry": True, "len": len(text)}
    content = text
    if link:
        content += "\n\n" + link
    payload = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content[:1300]},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.visibility": "PUBLIC"},
    }
    ok, res = _post_json(
        "https://api.linkedin.com/rest/ugcPosts",
        payload,
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            "X-Restli-Protocol-Version": "2.0.0",
        },
    )
    return {"ok": ok, "detail": res}


# ---------------------------------------------------------------------------
# Pinterest (v5) — 待 ACCESS_TOKEN + BOARD_ID (+ 图片)
# ---------------------------------------------------------------------------
def post_pinterest(text, link="", image_url="", dry_run=False):
    token = os.environ.get("PINTEREST_ACCESS_TOKEN")
    board = os.environ.get("PINTEREST_BOARD_ID")
    if not token or not board:
        return {"ok": False, "skip": True, "reason": "no PINTEREST_ACCESS_TOKEN/BOARD_ID"}
    if not image_url:
        return {"ok": False, "skip": True, "reason": "Pinterest needs PINTEREST_IMAGE_BASE"}
    if dry_run:
        return {"ok": True, "dry": True}
    payload = {
        "board_id": board,
        "title": text[:100],
        "description": (text + "\n\n" + DISCLAIMER)[:500],
        "link": link,
        "media": {"image_url": image_url},
    }
    ok, res = _post_json(
        "https://api.pinterest.com/v5/pins",
        payload,
        {"Content-Type": "application/json", "Authorization": "Bearer " + token},
    )
    return {"ok": ok, "detail": res}


# ---------------------------------------------------------------------------
# Threads (Meta Graph API) — 凭据已就绪（长效 Token）
# ---------------------------------------------------------------------------
def post_threads(text, link="", dry_run=False):
    token = os.environ.get("THREADS_ACCESS_TOKEN")
    uid = os.environ.get("THREADS_USER_ID")
    if not token or not uid:
        return {"ok": False, "skip": True, "reason": "no THREADS_ACCESS_TOKEN/USER_ID"}
    content = text
    if link:
        content += "\n\n" + link
    if dry_run:
        return {"ok": True, "dry": True, "len": len(content)}
    # 1) 创建文本容器
    data = urllib.parse.urlencode(
        {"media_type": "text", "text": content[:500], "access_token": token}
    ).encode()
    req = urllib.request.Request(
        f"https://graph.threads.net/v1.0/{uid}/threads", data=data, headers=UA, method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=20)
        cid = json.loads(r.read().decode()).get("id")
    except urllib.error.HTTPError as e:
        raw = e.fp.read().decode() if e.fp else ""
        return {"ok": False, "reason": "container failed", "detail": raw[:300]}
    if not cid:
        return {"ok": False, "reason": "no container id"}
    # 2) 发布
    pub = urllib.parse.urlencode({"creation_id": cid, "access_token": token}).encode()
    req2 = urllib.request.Request(
        f"https://graph.threads.net/v1.0/{uid}/threads_publish", data=pub, headers=UA, method="POST"
    )
    try:
        r2 = urllib.request.urlopen(req2, timeout=20)
        return {"ok": True, "detail": json.loads(r2.read().decode())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "reason": "publish failed", "detail": e.read().decode()[:300]}


# ---------------------------------------------------------------------------
# Mastodon (去中心化) — 凭据已就绪
# ---------------------------------------------------------------------------
def post_mastodon(text, link="", dry_run=False):
    token = os.environ.get("MASTODON_ACCESS_TOKEN")
    inst = os.environ.get("MASTODON_INSTANCE")
    if not token or not inst:
        return {"ok": False, "skip": True, "reason": "no MASTODON_ACCESS_TOKEN/INSTANCE"}
    content = text
    if link:
        content += "\n\n" + link
    if dry_run:
        return {"ok": True, "dry": True, "len": len(content)}
    ok, res = _post_json(
        f"https://{inst}/api/v1/statuses",
        {"status": content[:500]},
        {"Content-Type": "application/json", "Authorization": "Bearer " + token},
    )
    return {"ok": ok, "detail": res}


# ---------------------------------------------------------------------------
# Discord (Bot) — 凭据已就绪
# ---------------------------------------------------------------------------
def post_discord(text, link="", dry_run=False):
    token = os.environ.get("DISCORD_BOT_TOKEN")
    cid = os.environ.get("DISCORD_CHANNEL_ID")
    if not token or not cid:
        return {"ok": False, "skip": True, "reason": "no DISCORD_BOT_TOKEN/CHANNEL_ID"}
    content = text
    if link:
        content += "\n\n" + link
    if dry_run:
        return {"ok": True, "dry": True, "len": len(content)}
    ok, res = _post_json(
        f"https://discord.com/api/v10/channels/{cid}/messages",
        {"content": content[:2000]},
        {"Content-Type": "application/json", "Authorization": "Bot " + token},
    )
    return {"ok": ok, "detail": res}


# ---------------------------------------------------------------------------
# 内容生成（复用 Groq，多渠道共享一条 hook）
# ---------------------------------------------------------------------------
def build_social_texts(product, hook=None):
    """返回各渠道要发的文本。hook 为可选 Groq 生成的一句话。"""
    name = product["name"]
    cat = product.get("category", "")
    focus = product.get("research_focus") or product.get("application", "")
    seo_link = f"{SEO_BASE}/products/{slugify(product['name'])}.html"
    lines = {
        "bluesky": f"🔬 {name} ({cat})\n{focus}\n{seo_link}\n\n{DISCLAIMER}",
        "x": f"🔬 {name} — {focus} {seo_link} {DISCLAIMER}",
        "linkedin": (
            f"Research spotlight: {name}\n\n{focus}\n\n"
            f"Part of our {cat} research-peptide catalogue. All materials are "
            f"lab-grade, sold for scientific study only.\n\n{seo_link}\n\n{DISCLAIMER}"
        ),
        "pinterest": f"{name} — research peptide ({cat}). {focus}",
        "threads": f"🔬 {name} — {focus}\n{seo_link}\n\n{DISCLAIMER}",
        "mastodon": f"🔬 {name} ({cat})\n{focus}\n{seo_link}\n\n{DISCLAIMER}",
        "discord": f"🔬 **{name}** ({cat})\n{focus}\n{seo_link}\n\n{DISCLAIMER}",
    }
    if hook:
        lines["bluesky"] = f"🔬 {hook}\n\n{name} ({cat}): {seo_link}\n\n{DISCLAIMER}"
        lines["x"] = f"🔬 {hook} {name} {seo_link} {DISCLAIMER}"
        lines["threads"] = f"🔬 {hook}\n{name}: {seo_link}\n\n{DISCLAIMER}"
        lines["mastodon"] = f"🔬 {hook}\n\n{name} ({cat}): {seo_link}\n\n{DISCLAIMER}"
        lines["discord"] = f"🔬 **{hook}**\n{name} ({cat}): {seo_link}\n\n{DISCLAIMER}"
    return lines


def run_all(product=None, dry_run=False, channels=None):
    """对所有启用渠道发帖。返回结果 dict。"""
    from peptide_promotion import get_product_of_day, generate_product_content

    if product is None:
        product = get_product_of_day()
    # Groq hook 用于 Bluesky/X（共用，省一次调用）
    hook = None
    try:
        hook = generate_product_content(product)
        # 取首句作为 hook
        hook = (hook or "").split("\n")[0][:180]
    except Exception:  # noqa
        hook = None

    texts = build_social_texts(product, hook)
    results = {}
    targets = channels or ["bluesky", "x", "linkedin", "pinterest", "threads", "mastodon", "discord"]
    dispatchers = {
        "bluesky": lambda: post_bluesky(texts["bluesky"], dry_run=dry_run),
        "x": lambda: post_x(texts["x"], dry_run=dry_run),
        "linkedin": lambda: post_linkedin(texts["linkedin"], link=SEO_BASE, dry_run=dry_run),
        "pinterest": lambda: post_pinterest(
            texts["pinterest"], link=f"{SEO_BASE}/products/{slugify(product['name'])}.html",
            image_url=os.environ.get("PINTEREST_IMAGE_BASE", ""), dry_run=dry_run),
        "threads": lambda: post_threads(texts["threads"], link=SEO_BASE, dry_run=dry_run),
        "mastodon": lambda: post_mastodon(texts["mastodon"], link=SEO_BASE, dry_run=dry_run),
        "discord": lambda: post_discord(texts["discord"], link=SEO_BASE, dry_run=dry_run),
    }
    ok, failed = [], []
    for ch in targets:
        fn = dispatchers.get(ch)
        if not fn:
            continue
        try:
            r = fn()
            results[ch] = r
            if isinstance(r, dict) and r.get("ok"):
                ok.append(ch)
            else:
                failed.append(ch)
        except Exception as e:  # noqa — 死凭据/网络问题不中断整轮
            results[ch] = {"ok": False, "error": str(e)}
            failed.append(ch)
    print(f"[channels] ok={ok} skipped/failed={failed}")
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="不真实发送，只校验")
    ap.add_argument("--channels", default="bluesky,x,linkedin,pinterest,threads,mastodon,discord")
    args = ap.parse_args()
    # 载入 .env
    envf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(envf):
        for line in open(envf, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()
    res = run_all(dry_run=args.dry, channels=[c.strip() for c in args.channels.split(",")])
    print(json.dumps(res, ensure_ascii=False, indent=2))
