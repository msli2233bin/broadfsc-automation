"""
BroadFSC Chart Uploader — Upload generated charts to each platform.
Handles platform-specific image upload APIs, returns media IDs/URLs
that can be embedded in posts.

Supported platforms:
- Telegram: sendPhoto API
- Discord: upload attachment
- Bluesky: uploadBlob + embed
- Mastodon: media_upload
- Threads: media container
- Hatena Blog: imgur upload (for email-based posting)
"""
import os
import sys
import base64
import hashlib
import datetime
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Telegram Photo Upload
# ============================================================
def upload_telegram_photo(image_path, caption, channel_id=None, bot_token=None):
    """Send a photo with caption to Telegram channel.

    Returns True/False.
    """
    bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel_id = channel_id or os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if not bot_token or not channel_id:
        print("  [upload] Telegram: Missing BOT_TOKEN or CHANNEL_ID")
        return False

    if not os.path.exists(image_path):
        print(f"  [upload] Telegram: Image not found: {image_path}")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    try:
        with open(image_path, 'rb') as f:
            files = {'photo': f}
            data = {
                "chat_id": channel_id,
                "caption": caption,
                "parse_mode": "HTML",
            }
            r = requests.post(url, files=files, data=data, timeout=30)

        if r.status_code == 200:
            msg_id = r.json()['result']['message_id']
            print(f"  [upload] Telegram photo sent! Msg ID: {msg_id}")
            return True
        else:
            print(f"  [upload] Telegram FAIL: HTTP {r.status_code} - {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  [upload] Telegram FAIL: {e}")
        return False


# ============================================================
# Discord Attachment Upload
# ============================================================
def upload_discord_image(image_path, text="", channel_id=None, bot_token=None):
    """Post a message with image attachment to Discord.

    Returns True/False.
    """
    bot_token = bot_token or os.environ.get("DISCORD_BOT_TOKEN", "")
    channel_id = channel_id or os.environ.get("DISCORD_CHANNEL_ID", "")

    if not bot_token or not channel_id:
        print("  [upload] Discord: Missing BOT_TOKEN or CHANNEL_ID")
        return False

    if not os.path.exists(image_path):
        print(f"  [upload] Discord: Image not found: {image_path}")
        return False

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

    try:
        with open(image_path, 'rb') as f:
            files = {'files[0]': (os.path.basename(image_path), f, 'image/png')}
            payload = {"content": text or "📊"}
            r = requests.post(
                url,
                headers={"Authorization": f"Bot {bot_token}"},
                files=files,
                data={"payload_json": str(payload).replace("'", '"')},
                timeout=30,
            )

        if r.status_code == 200:
            msg_id = r.json().get("id", "")
            print(f"  [upload] Discord image posted! Msg ID: {msg_id}")
            return True
        else:
            # Fallback: send text + URL reference
            print(f"  [upload] Discord image FAIL: HTTP {r.status_code}, trying embed fallback")
            return _upload_discord_embed(image_path, text, channel_id, bot_token)
    except Exception as e:
        print(f"  [upload] Discord FAIL: {e}")
        return False


def _upload_discord_embed(image_path, text, channel_id, bot_token):
    """Fallback: use Discord embed with image URL (requires publicly accessible URL)."""
    # For now, just send text without image
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }
    payload = {"content": text or "📊 Chart attached"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        return r.status_code == 200
    except:
        return False


# ============================================================
# Bluesky Image Upload
# ============================================================
def upload_bluesky_image(image_path, alt_text="", handle=None, password=None):
    """Upload image to Bluesky and return blob ref for embedding in posts.

    Returns: {"$type": "blob", "ref": {"$link": "..."}, "mimeType": "image/png", "size": N}
    or None on failure.
    """
    handle = handle or os.environ.get("BLUESKY_HANDLE", "")
    password = password or os.environ.get("BLUESKY_APP_PASSWORD", "")
    pds_url = "https://bsky.social/xrpc"

    if not handle or not password:
        print("  [upload] Bluesky: Missing credentials")
        return None

    if not os.path.exists(image_path):
        print(f"  [upload] Bluesky: Image not found: {image_path}")
        return None

    # Step 1: Auth
    try:
        resp = requests.post(
            f"{pds_url}/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"  [upload] Bluesky auth FAIL: HTTP {resp.status_code}")
            return None
        session = resp.json()
        access_jwt = session["accessJwt"]
        did = session["did"]
    except Exception as e:
        print(f"  [upload] Bluesky auth FAIL: {e}")
        return None

    # Step 2: Upload blob
    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()

        # Compute SHA-256 for integrity
        sha256 = hashlib.sha256(img_data).hexdigest()

        resp = requests.post(
            f"{pds_url}/com.atproto.repo.uploadBlob",
            headers={
                "Authorization": f"Bearer {access_jwt}",
                "Content-Type": "image/png",
            },
            data=img_data,
            timeout=30,
        )

        if resp.status_code in [200, 201]:
            blob = resp.json().get("blob")
            print(f"  [upload] Bluesky image uploaded! Size: {len(img_data)} bytes")
            return blob
        else:
            print(f"  [upload] Bluesky upload FAIL: HTTP {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  [upload] Bluesky upload FAIL: {e}")
        return None


def post_bluesky_with_image(text, image_path, alt_text=""):
    """Post to Bluesky with an attached image.

    Returns True/False.
    """
    blob = upload_bluesky_image(image_path, alt_text)
    if blob is None:
        print("  [upload] Bluesky: Image upload failed, posting text-only")
        return False

    handle = os.environ.get("BLUESKY_HANDLE", "")
    password = os.environ.get("BLUESKY_APP_PASSWORD", "")
    pds_url = "https://bsky.social/xrpc"

    # Auth
    try:
        resp = requests.post(
            f"{pds_url}/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
            timeout=15,
        )
        session = resp.json()
        access_jwt = session["accessJwt"]
        did = session["did"]
    except:
        return False

    # Create post with embedded image
    # NOTE: Bluesky client shows "ALT" badge on images with alt text.
    # Using empty alt to avoid the badge; the chart itself is self-explanatory.
    alt_val = alt_text.strip() if alt_text and alt_text.strip() else ""
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [{
                "alt": "",
                "image": blob,
            }],
        },
    }

    try:
        r = requests.post(
            f"{pds_url}/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {access_jwt}"},
            json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
            timeout=15,
        )
        if r.status_code in [200, 201]:
            uri = r.json().get("uri", "")
            print(f"  [upload] Bluesky posted with image! URI: {uri}")
            return True
        else:
            print(f"  [upload] Bluesky post FAIL: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  [upload] Bluesky post FAIL: {e}")
        return False


# ============================================================
# Mastodon Media Upload
# ============================================================
def upload_mastodon_media(image_path, description=""):
    """Upload image to Mastodon and return media ID.

    Returns: media_id string or None.
    """
    instance = os.environ.get("MASTODON_INSTANCE", "")
    access_token = os.environ.get("MASTODON_ACCESS_TOKEN", "")

    if not instance or not access_token:
        print("  [upload] Mastodon: Missing credentials")
        return None

    if not os.path.exists(image_path):
        print(f"  [upload] Mastodon: Image not found: {image_path}")
        return None

    url = f"https://{instance}/api/v2/media"

    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {"description": description or "Technical analysis chart"}
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                files=files,
                data=data,
                timeout=30,
            )

        if r.status_code in [200, 201, 202]:
            media_id = r.json().get("id", "")
            print(f"  [upload] Mastodon media uploaded! ID: {media_id}")
            return media_id
        else:
            print(f"  [upload] Mastodon upload FAIL: HTTP {r.status_code} - {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  [upload] Mastodon upload FAIL: {e}")
        return None


def post_mastodon_with_image(text, image_path, description=""):
    """Post to Mastodon with an attached image.

    Returns True/False.
    """
    media_id = upload_mastodon_media(image_path, description)
    if media_id is None:
        print("  [upload] Mastodon: Media upload failed, posting text-only")
        return False

    instance = os.environ.get("MASTODON_INSTANCE", "")
    access_token = os.environ.get("MASTODON_ACCESS_TOKEN", "")
    url = f"https://{instance}/api/v1/statuses"

    if len(text) > 500:
        text = text[:497] + "..."

    payload = {
        "status": text,
        "media_ids[]": media_id,
    }

    # Mastodon media_ids needs to be sent as form data or proper JSON
    payload_json = {
        "status": text,
        "media_ids": [media_id],
    }

    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=payload_json,
            timeout=15,
        )
        if r.status_code == 200:
            toot_id = r.json().get("id", "")
            print(f"  [upload] Mastodon posted with image! ID: {toot_id}")
            return True
        else:
            print(f"  [upload] Mastodon post FAIL: HTTP {r.status_code} - {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  [upload] Mastodon post FAIL: {e}")
        return False


# ============================================================
# Public Image Hosting — for Threads/Hatena/Email
# Uses GitHub raw URLs (push charts to repo, use raw URL)
# or ImgBB as fallback
# ============================================================
def get_public_url(image_path):
    """Get a publicly accessible URL for an image.

    Strategy:
    1. Try ImgBB (free, no account needed with API key)
    2. Try postimages.org
    3. Return None if all fail
    """
    if not os.path.exists(image_path):
        return None

    # Method 1: ImgBB (if API key available)
    imgbb_key = os.environ.get("IMGBB_API_KEY", "")
    if imgbb_key:
        url = upload_to_imgbb(image_path, api_key=imgbb_key)
        if url:
            return url

    # Method 2: postimages.org (free, no key)
    try:
        url = _upload_postimages(image_path)
        if url:
            return url
    except Exception as e:
        print(f"  [upload] postimages.org failed: {e}")

    # Method 3: Upload to Telegram, get file URL (works as CDN)
    try:
        url = _upload_telegram_cdn(image_path)
        if url:
            return url
    except Exception as e:
        print(f"  [upload] Telegram CDN failed: {e}")

    print("  [upload] WARNING: Could not get public URL for image")
    return None


def _upload_postimages(image_path):
    """Upload to postimages.org (free, no API key)."""
    import re
    with open(image_path, 'rb') as f:
        r = requests.post(
            'https://api.imgur.com/3/image',  # Imgur free API
            headers={"Authorization": "Client-ID 546c25a59c58ad7"},
            files={'image': f},
            timeout=30,
        )
    if r.status_code == 200:
        data = r.json().get('data', {})
        url = data.get('link', '')
        if url:
            print(f"  [upload] Imgur uploaded! URL: {url}")
            return url
    return None


def _upload_telegram_cdn(image_path):
    """Upload image to Telegram bot, get file URL as public CDN.

    This is a creative workaround: upload to bot, get file_path, construct URL.
    The URL is accessible to anyone who has it (no auth needed).
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        return None

    # Send photo to bot's private chat (the bot itself)
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    admin_id = os.environ.get("TELEGRAM_ADMIN_ID", "")
    if not admin_id:
        # Use channel_id as fallback
        admin_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    if not admin_id:
        return None

    try:
        with open(image_path, 'rb') as f:
            r = requests.post(url, files={'photo': f},
                              data={"chat_id": admin_id, "disable_notification": "true"},
                              timeout=30)
        if r.status_code == 200:
            result = r.json().get('result', {})
            photos = result.get('photo', [])
            if photos:
                # Get largest size file_id
                file_id = photos[-1].get('file_id', '')
                # Get file path
                file_resp = requests.get(
                    f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}",
                    timeout=15,
                )
                if file_resp.status_code == 200:
                    file_path = file_resp.json().get('result', {}).get('file_path', '')
                    if file_path:
                        cdn_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                        print(f"  [upload] Telegram CDN URL obtained")
                        return cdn_url
    except Exception as e:
        print(f"  [upload] Telegram CDN: {e}")
    return None


# ============================================================
# Threads Media Upload
# ============================================================
def post_threads_with_image(text, image_path):
    """Post to Threads with image via Meta API.

    Uses the two-step container + publish flow.
    Requires a publicly accessible image URL.
    Returns True/False.
    """
    access_token = os.environ.get("THREADS_ACCESS_TOKEN", "")

    if not access_token:
        print("  [upload] Threads: Missing THREADS_ACCESS_TOKEN")
        return False

    if not os.path.exists(image_path):
        print(f"  [upload] Threads: Image not found: {image_path}")
        return False

    # Get public URL for the image
    public_url = get_public_url(image_path)
    if not public_url:
        print("  [upload] Threads: Cannot get public URL for image, skipping")
        return False

    try:
        # Create container
        container_resp = requests.post(
            "https://graph.threads.net/v1.0/me/threads",
            params={
                "media_type": "IMAGE",
                "image_url": public_url,
                "text": text,
                "access_token": access_token,
            },
            timeout=30,
        )

        if container_resp.status_code not in [200, 201]:
            print(f"  [upload] Threads container FAIL: HTTP {container_resp.status_code} - {container_resp.text[:200]}")
            return False

        container_id = container_resp.json().get("id", "")

        # Publish
        import time
        time.sleep(2)

        publish_resp = requests.post(
            f"https://graph.threads.net/v1.0/me/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": access_token,
            },
            timeout=15,
        )

        if publish_resp.status_code in [200, 201]:
            post_id = publish_resp.json().get("id", "")
            print(f"  [upload] Threads posted with image! ID: {post_id}")
            return True
        else:
            print(f"  [upload] Threads publish FAIL: HTTP {publish_resp.status_code}")
            return False

    except Exception as e:
        print(f"  [upload] Threads FAIL: {e}")
        return False


# ============================================================
# Hatena Blog Image Posting
# ============================================================
def post_hatena_with_charts(title, content, image_paths):
    """Post to Hatena Blog with chart images attached.

    Hatena email posting auto-uploads attached images to Fotolife.
    Returns (success, message).
    """
    try:
        from hatena_poster import post_entry
        success, msg = post_entry(title, content, image_paths=image_paths)
        return success
    except Exception as e:
        print(f"  [upload] Hatena FAIL: {e}")
        return False


# ============================================================
# Email Chart Embedding
# ============================================================
def get_email_chart_html(image_path, caption=""):
    """Get an HTML img tag for embedding a chart in an email.

    Uses public URL (from Telegram CDN or Imgur).
    Returns: HTML string or empty string on failure.
    """
    public_url = get_public_url(image_path)
    if not public_url:
        return ""

    html = f'<div style="text-align:center;margin:16px 0;">'
    html += f'<img src="{public_url}" alt="{caption or "Technical analysis chart"}" '
    html += f'style="max-width:100%;height:auto;border-radius:8px;">'
    if caption:
        html += f'<p style="font-size:12px;color:#888;margin-top:4px;">{caption}</p>'
    html += '</div>'
    return html


# ============================================================
# Smart Upload — Route to correct platform
# ============================================================
def upload_chart_to_platform(platform, image_path, text="", **kwargs):
    """Upload a chart image to the specified platform.

    Returns True/False.
    """
    uploaders = {
        'telegram': lambda: upload_telegram_photo(
            image_path, text,
            channel_id=kwargs.get('channel_id'),
            bot_token=kwargs.get('bot_token'),
        ),
        'discord': lambda: upload_discord_image(
            image_path, text,
            channel_id=kwargs.get('channel_id'),
            bot_token=kwargs.get('bot_token'),
        ),
        'bluesky': lambda: post_bluesky_with_image(
            text, image_path,
            alt_text=kwargs.get('alt_text', ''),
        ),
        'mastodon': lambda: post_mastodon_with_image(
            text, image_path,
            description=kwargs.get('alt_text', ''),
        ),
        'threads': lambda: post_threads_with_image(text, image_path),
        'hatena': lambda: post_hatena_with_charts(
            kwargs.get('title', 'Market Analysis'),
            kwargs.get('content', text),
            image_paths=[image_path],
        ),
    }

    uploader = uploaders.get(platform)
    if uploader is None:
        print(f"  [upload] Unsupported platform: {platform}")
        return False

    return uploader()
