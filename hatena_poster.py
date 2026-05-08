"""
BroadFSC Hatena Blog Auto-Poster
Posts market analysis to はてなブログ via email (Brevo API).

はてなブログ メール投稿:
- Free tier supported (no Pro needed)
- Each blog has a unique posting email address (詳細設定 → 投稿メールアドレス)
- Email subject = post title, Email body = post content (Markdown/見たままモード)
- Images attached to email are uploaded to Hatena Fotolife
- Sender email can be any address (not limited to registered email)

Setup:
1. Register at https://blog.hatena.ne.jp/register (email only, no phone needed)
2. Create blog (e.g., broadfsc.hatenablog.com)
3. Get posting email: 設定 → 詳細設定 → 投稿メールアドレス → クリックして表示
4. Set environment variables: HATENA_POST_EMAIL, HATENA_BLOG_DOMAIN
5. Brevo API for sending: BREVO_API_KEY, BREVO_SENDER_EMAIL
"""

import os
import sys
import datetime
import requests
import json
import re

if sys.stdout.encoding and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
HATENA_POST_EMAIL = os.environ.get("HATENA_POST_EMAIL", "")
HATENA_BLOG_DOMAIN = os.environ.get("HATENA_BLOG_DOMAIN", "broadfsc.hatenablog.com")

# Brevo API (for sending emails)
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "msli2233bin+brevo@gmail.com")

# Fallback from .env
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            if key == "HATENA_POST_EMAIL" and not HATENA_POST_EMAIL:
                HATENA_POST_EMAIL = val
            elif key == "HATENA_BLOG_DOMAIN" and not HATENA_BLOG_DOMAIN:
                HATENA_BLOG_DOMAIN = val
            elif key == "BREVO_API_KEY" and not BREVO_API_KEY:
                BREVO_API_KEY = val
            elif key == "BREVO_SENDER_EMAIL" and not BREVO_SENDER_EMAIL:
                BREVO_SENDER_EMAIL = val

# AI
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    if os.path.exists(_env_path):
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GROQ_API_KEY="):
                    GROQ_API_KEY = line.strip().split("=", 1)[1]

# Analytics
try:
    from analytics_logger import log_post
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False


# ============================================================
# Email Posting via Brevo API
# ============================================================
def post_entry(title, content, draft=False, image_paths=None):
    """Post a blog entry to はてなブログ via email.

    Args:
        title: Post title (becomes email subject)
        content: Post body in Markdown format (becomes email body)
        draft: If True, use draft posting address (if configured)
        image_paths: Optional list of local image file paths to attach.
                     Hatena auto-uploads attachments to Fotolife and
                     embeds them in the post.

    Returns:
        (success: bool, message: str)
    """
    if not HATENA_POST_EMAIL:
        print("  Hatena: SKIP (missing HATENA_POST_EMAIL)")
        return False, "Missing HATENA_POST_EMAIL"

    if not BREVO_API_KEY:
        print("  Hatena: SKIP (missing BREVO_API_KEY)")
        return False, "Missing BREVO_API_KEY"

    # If image_paths provided, embed them in content as Markdown image references
    if image_paths:
        content = _embed_images_in_content(content, image_paths)

    # Send email via Brevo API
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    payload = {
        "sender": {"name": "BroadFSC", "email": BREVO_SENDER_EMAIL},
        "to": [{"email": HATENA_POST_EMAIL}],
        "subject": title,
        "textContent": content,
    }

    # Add image attachments if provided
    # Brevo API supports base64 attachments
    if image_paths:
        attachment_list = []
        for img_path in image_paths:
            if os.path.exists(img_path):
                try:
                    import base64
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode()
                    filename = os.path.basename(img_path)
                    attachment_list.append({
                        "content": img_data,
                        "name": filename,
                        "contentType": "image/png",
                    })
                except Exception as e:
                    print(f"  Hatena: ⚠️ Could not attach {img_path}: {e}")
        if attachment_list:
            payload["attachment"] = attachment_list

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)

        if r.status_code in (200, 201):
            msg_id = r.json().get("messageId", "")
            status = "draft" if draft else "published"
            blog_url = f"https://{HATENA_BLOG_DOMAIN}"
            print(f"  Hatena: ✅ {status} — '{title}' → {blog_url}")
            if HAS_ANALYTICS:
                log_post(platform="hatena", post_type="email", content_preview=title[:100],
                         status="success")
            return True, blog_url
        else:
            error_msg = f"Brevo HTTP {r.status_code}: {r.text[:300]}"
            print(f"  Hatena: ❌ Post failed — {error_msg}")
            if HAS_ANALYTICS:
                log_post(platform="hatena", post_type="email", content_preview=title[:100],
                         status="failed", error_msg=error_msg[:200])
            return False, error_msg

    except requests.exceptions.ConnectionError:
        print("  Hatena: ❌ Connection failed")
        return False, "Connection error"
    except Exception as e:
        print(f"  Hatena: ❌ Error: {e}")
        return False, str(e)


def _embed_images_in_content(content, image_paths):
    """Add Markdown image references to content for Hatena blog posts.

    Hatena Fotolife images attached to email are auto-uploaded,
    but for remote images we use Markdown syntax with public URLs.
    For attached images, Hatena auto-places them — we just add
    a placeholder reference for context.
    """
    chart_section = "\n\n---\n**📊 チャート分析**\n\n"
    for i, img_path in enumerate(image_paths):
        filename = os.path.basename(img_path)
        # Hatena email posting: attached images are auto-inserted
        # We add descriptive text before each auto-inserted image
        if 'candlestick' in filename:
            chart_section += "**ローソク足チャート & 主要レベル:**\n\n"
        elif 'indicators' in filename:
            chart_section += "**RSI & MACD 分析:**\n\n"
        elif 'bollinger' in filename:
            chart_section += "**ボリンジャーバンド分析:**\n\n"
        elif 'trend_card' in filename:
            chart_section += "**トレンドサマリー:**\n\n"
        else:
            chart_section += f"**チャート {i+1}:**\n\n"

    return content + chart_section


# ============================================================
# Content Generation — Japanese market analysis for Hatena
# ============================================================
def generate_hatena_content():
    """Generate Japanese market analysis content for はてなブログ.

    Returns:
        dict with 'title', 'content' (Markdown), 'categories' keys, or None on failure.
    """
    if not GROQ_API_KEY:
        print("  Hatena: No GROQ_API_KEY, using fallback")
        return _get_fallback_content()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        return _get_fallback_content()

    # Fetch real-time market data
    realtime = _fetch_market_snapshot()
    today = datetime.datetime.utcnow().strftime("%Y年%m月%d日")

    prompt = f"""あなたはBroadFSC（グローバル投資顧問）のシニアマーケットアナリストです。今日は{today}です。

ライブマーケットデータ:
{realtime}

タスク: 日本の投資家向けに、魅力的でデータ豊富なマーケット分析記事をMarkdown形式で書いてください。

構造:
1. タイトル: 具体的な数字や銘柄を含む、クリックしたくなるタイトル
2. リード文: 1-2文で今日の最重要ポイント
3. 本文（3-5段落）:
   - 米国市場と日本市場の連動性
   - 具体的な株価・指数・指標（5つ以上の数字）
   - 円相場・日経平均への影響
   - 新NISA投資家への示唆
   - コントラリアン視点（コンセンサスが見落としているもの）
4. 注目ポイント: 今週注目すべき3つのイベント/指標
5. CTA: 無料個別銘柄レポート → @BroadInvestBot

品質ルール:
- 日本語で書く（金融専門用語: 日経平均、ドル円、新NISA、決算期など）
- データは実際のマーケットスナップショットに基づくこと
- 「お伝えします」「注目です」などの無意味な定型句を避ける
- 意見を持つ — ふわっとした中立は退屈
- Markdown形式で構造化（## h2, - リスト, **太字**, [リンク](URL)）
- 免責事項は不要

出力はJSON形式のみ（他のテキストは一切不要）:
{{"title": "...", "content": "Markdown本文", "categories": ["投資", "..."]}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.85,
        )
        raw = response.choices[0].message.content.strip()

        # Robust JSON extraction
        if "```" in raw:
            raw = raw.split("```", 1)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            if "```" in raw:
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        raw = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', raw)
        result = json.loads(raw)

        print(f"  Hatena: Generated — '{result.get('title', '?')}' ({len(result.get('content', ''))} chars)")
        return result

    except (json.JSONDecodeError, Exception) as e:
        print(f"  Hatena: JSON parse failed: {e}")
        title_match = re.search(r'"title"\s*:\s*"([^"]+)"', raw if raw else "")
        content_match = re.search(r'"content"\s*:\s*"(.+?)"(?:\s*,|\s*})', raw if raw else "", re.DOTALL)
        if title_match and content_match:
            return {
                "title": title_match.group(1),
                "content": content_match.group(1),
                "categories": ["投資", "マーケット"],
            }
        return _get_fallback_content()
    except Exception as e:
        print(f"  Hatena: Generation failed: {e}")
        return _get_fallback_content()


def _fetch_market_snapshot():
    """Fetch real-time market data including JPY pairs for Japanese audience."""
    try:
        import yfinance as yf
    except ImportError:
        return ""

    snapshots = []
    tickers = {
        "日経平均": "^N225",
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "ドル円": "JPY=X",
        "ユーロ円": "EURJPY=X",
        "Gold": "GC=F",
        "Oil": "CL=F",
        "Bitcoin": "BTC-USD",
        "10Y利回り": "^TNX",
        "VIX": "^VIX",
        "AAPL": "AAPL",
        "NVDA": "NVDA",
        "7203.T(トヨタ)": "7203.T",
        "6758.T(ソニー)": "6758.T",
    }

    for name, symbol in tickers.items():
        try:
            tk = yf.Ticker(symbol)
            hist = tk.history(period="2d")
            if hist.empty:
                continue
            close = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[0] if len(hist) > 1 else close
            change = ((close - prev) / prev) * 100 if prev else 0
            arrow = "+" if change >= 0 else ""
            snapshots.append(f"{name}: {close:,.2f} ({arrow}{change:.1f}%)")
        except Exception:
            continue

    return " | ".join(snapshots) if snapshots else ""


def _get_fallback_content():
    """Fallback content when AI generation fails."""
    today = datetime.datetime.utcnow().strftime("%Y年%m月%d日")
    return {
        "title": f"マーケット速報 — {today}",
        "content": f"""## 本日のマーケット概覧

米国市場の動向と日本市場への影響を解説します。

## 注目ポイント

- 日経平均のテクニカル水準
- ドル円相場の方向性
- 新NISA投資家への示唆

---

📱 **Free Stock Research Report** → [@BroadInvestBot](https://t.me/BroadInvestBot) | [BroadFSC Channel](https://t.me/BroadFSC)

*投資にはリスクが伴います。詳細はライセンス保有のアドバイザーにご相談ください。*""",
        "categories": ["投資", "マーケット"],
    }


# ============================================================
# Main Entry Point
# ============================================================
def post_to_hatena(draft=False):
    """Main function: generate content and post to はてなブログ via email.

    Args:
        draft: If True, indicate draft mode (note: email posting publishes by default).

    Returns:
        True on success, False on failure.
    """
    print("--- はてなブログ (email) ---")
    if not HATENA_POST_EMAIL:
        print("  Hatena: Not configured (HATENA_POST_EMAIL missing)")
        print("  -> Register: https://blog.hatena.ne.jp/register")
        print("  -> Posting email: 設定 → 詳細設定 → 投稿メールアドレス")
        return False

    print(f"  Hatena: Configured ({HATENA_BLOG_DOMAIN})")
    print(f"  Posting email: {HATENA_POST_EMAIL[:15]}...@blog.hatena.ne.jp")

    # Generate Japanese content
    article = generate_hatena_content()
    if not article:
        print("  Hatena: Content generation failed")
        return False

    title = article.get("title", "Market Update")
    content = article.get("content", "")

    print(f"  Title: {title}")
    print(f"  Content: {len(content)} chars")
    print(f"  Mode: {'draft' if draft else 'publish'}")

    success, result = post_entry(
        title=title,
        content=content,
        draft=draft,
    )

    return success


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BroadFSC Hatena Blog Poster (via email)")
    parser.add_argument("--draft", action="store_true", help="Indicate draft mode")
    parser.add_argument("--test", action="store_true", help="Test email sending only")
    args = parser.parse_args()

    print("=" * 50)
    print("BroadFSC はてなブログ Poster (email)")
    print(f"Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    if args.test:
        print("\n📋 Testing email posting...")
        success, msg = post_entry(
            title="テスト投稿 — BroadFSC",
            content="これはテスト投稿です。\n\n- 日経平均\n- ドル円\n\n@BroadInvestBot",
        )
        if success:
            print("✅ Hatena email posting OK")
        else:
            print(f"❌ Hatena email posting failed: {msg}")
    else:
        post_to_hatena(draft=args.draft)
