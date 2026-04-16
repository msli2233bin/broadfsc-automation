"""
BroadFSC TikTok Auto-Poster via Postproxy API
Posts daily market insights as TikTok videos (image-to-video slideshow).

Postproxy API: https://postproxy.dev/reference/posts/
- Bearer Token auth
- TikTok ONLY supports video (not image carousels)
- This script: AI generates text slides → Pillow renders images → imageio makes MP4 → Postproxy posts video

Modes:
1. SLIDESHOW mode (default, zero-cost): AI generates text → branded slide images → MP4 video slideshow
2. VIDEO mode: Post a video from URL or local file

Environment variables:
  POSTPROXY_API_KEY - Required. Your Postproxy API key
  GROQ_API_KEY - Optional. For AI-generated captions
  TELEGRAM_BOT_TOKEN - Optional. For notifications
  TELEGRAM_CHANNEL_ID - Optional. For notifications
  TIKTOK_VIDEO_URL - Optional. Direct video URL for video mode
"""

import os
import sys
import datetime
import requests
import json
import random
import base64
import struct
import math

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import imageio.v2 as iio
    import numpy as np
    HAS_IMAGEIO = True
except ImportError:
    HAS_IMAGEIO = False

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
POSTPROXY_API_KEY = os.environ.get("POSTPROXY_API_KEY", "")
POSTPROXY_BASE_URL = "https://api.postproxy.dev/api"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TIKTOK_VIDEO_URL = os.environ.get("TIKTOK_VIDEO_URL", "")

# Notification
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Post mode: "slideshow" (default) or "video"
TIKTOK_MODE = os.environ.get("TIKTOK_MODE", "slideshow").lower()

WEBSITE_LINK = "https://www.broadfsc.com/different"
TELEGRAM_LINK = "https://t.me/BroadFSC"

# ============================================================
# Content Topics (rotated daily)
# ============================================================
CONTENT_TOPICS = [
    {
        "title": "Why Diversification Matters in 2026",
        "points": [
            "Global markets are more correlated than ever",
            "Geopolitical risks create sudden sector shifts",
            "Multi-asset strategies reduce drawdown risk",
            "BroadFSC: Expert guidance for global portfolios"
        ],
    },
    {
        "title": "Fed Rate Decisions: What Investors Need to Know",
        "points": [
            "Rate decisions affect ALL asset classes",
            "Bond yields move inversely to prices",
            "Equity sectors react differently to policy",
            "Stay informed with BroadFSC daily briefings"
        ],
    },
    {
        "title": "Emerging Markets: Opportunity or Risk?",
        "points": [
            "EM equities trading at historic discounts",
            "Currency risk can amplify or erode returns",
            "Political stability varies widely by region",
            "BroadFSC: Navigate EM with professional insight"
        ],
    },
    {
        "title": "How to Read Market Sentiment",
        "points": [
            "VIX index: The market's fear gauge",
            "Put/Call ratios reveal trader positioning",
            "Fund flows show where smart money goes",
            "Daily sentiment analysis at BroadFSC"
        ],
    },
    {
        "title": "Gold in 2026: Safe Haven or Overvalued?",
        "points": [
            "Gold hits new highs amid global uncertainty",
            "Central banks continue accumulating reserves",
            "Real yields remain the key driver",
            "Get expert commodity analysis at BroadFSC"
        ],
    },
    {
        "title": "Tech Earnings: What They Signal",
        "points": [
            "Mega-cap earnings drive index performance",
            "AI spending boom continues across sectors",
            "Cloud revenue growth remains robust",
            "BroadFSC: Daily earnings insights & analysis"
        ],
    },
    {
        "title": "5 Investment Mistakes to Avoid",
        "points": [
            "Chasing past performance blindly",
            "Ignoring fees and total cost of ownership",
            "Letting emotions override your strategy",
            "Failing to rebalance your portfolio",
            "BroadFSC: Professional guidance, zero hype"
        ],
    },
]


# ============================================================
# AI Caption Generation
# ============================================================
def generate_tiktok_caption():
    """Generate a TikTok caption using Groq AI."""
    if not GROQ_API_KEY:
        return get_fallback_caption()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        day_of_year = now.timetuple().tm_yday
        topic_idx = day_of_year % len(CONTENT_TOPICS)
        topic = CONTENT_TOPICS[topic_idx]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a financial content creator for BroadFSC on TikTok. "
                    "Write an engaging TikTok caption for a post about: " + topic["title"] + "\n\n"
                    "Key points to reference:\n"
                    + "\n".join(["- " + p for p in topic["points"]]) + "\n\n"
                    "Requirements:\n"
                    "- Maximum 300 characters\n"
                    "- Use 2-3 relevant hashtags\n"
                    "- Engaging hook in the first line\n"
                    "- Include a call to action\n"
                    "- Do NOT promise guaranteed returns\n"
                    "- Today is " + day
                )
            }],
            max_tokens=120,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI caption generation failed: " + str(e))
        return get_fallback_caption()


def get_fallback_caption():
    """Fallback TikTok captions."""
    captions = [
        "Want to invest smarter in 2026? Here's what the pros watch every morning \U0001f4c8 "
        "Daily global market briefings - FREE. Link in bio! #Investing #StockMarket #FinanceTips",

        "Markets move FAST. Don't get caught off guard \u26a1 "
        "Pre-market briefings for Asia, Europe, Middle East & Americas. "
        "Subscribe free! #Trading #Investing #MarketAnalysis",

        "3 things smart investors check before markets open \U0001f4ca "
        "1. Overnight futures 2. Central bank signals 3. Key economic data. "
        "Get all this daily at BroadFSC #Investing #StockMarket #WealthBuilding",
    ]
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(captions)
    return captions[idx]


# ============================================================
# Image Generation (Pillow + Fallback)
# ============================================================

# Brand palette
BRAND_COLORS = {
    "dark_navy": (15, 23, 42),
    "deep_blue": (30, 58, 138),
    "accent_blue": (59, 130, 246),
    "accent_green": (16, 185, 129),
    "gold": (245, 158, 11),
    "white": (255, 255, 255),
    "light_gray": (148, 163, 184),
    "red": (239, 68, 68),
}

SLIDE_W, SLIDE_H = 1088, 1920  # TikTok 9:16, width must be divisible by 16 for video


def _get_font(size, bold=False):
    """Get a font, trying system fonts first, falling back to default."""
    font_names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in font_names:
        if os.path.exists(name):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + (" " if current else "") + word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _create_title_slide(topic):
    """Create a title slide with topic name and BroadFSC branding."""
    img = Image.new("RGB", (SLIDE_W, SLIDE_H), BRAND_COLORS["dark_navy"])
    draw = ImageDraw.Draw(img)

    # Gradient overlay at bottom
    for y in range(SLIDE_H // 2, SLIDE_H):
        ratio = (y - SLIDE_H // 2) / (SLIDE_H // 2)
        r = int(BRAND_COLORS["dark_navy"][0] + (BRAND_COLORS["deep_blue"][0] - BRAND_COLORS["dark_navy"][0]) * ratio)
        g = int(BRAND_COLORS["dark_navy"][1] + (BRAND_COLORS["deep_blue"][1] - BRAND_COLORS["dark_navy"][1]) * ratio)
        b = int(BRAND_COLORS["dark_navy"][2] + (BRAND_COLORS["deep_blue"][2] - BRAND_COLORS["dark_navy"][2]) * ratio)
        draw.line([(0, y), (SLIDE_W, y)], fill=(r, g, b))

    # Top accent bar
    draw.rectangle([(0, 0), (SLIDE_W, 8)], fill=BRAND_COLORS["accent_blue"])

    # BroadFSC logo text (top)
    logo_font = _get_font(56, bold=True)
    draw.text((SLIDE_W // 2, 200), "BroadFSC", font=logo_font,
              fill=BRAND_COLORS["accent_blue"], anchor="mm")

    # Subtitle
    sub_font = _get_font(28)
    draw.text((SLIDE_W // 2, 270), "INVESTMENT INSIGHTS", font=sub_font,
              fill=BRAND_COLORS["light_gray"], anchor="mm")

    # Divider line
    draw.rectangle([(SLIDE_W // 2 - 120, 320), (SLIDE_W // 2 + 120, 324)],
                   fill=BRAND_COLORS["accent_blue"])

    # Title (centered, wrapped)
    title_font = _get_font(72, bold=True)
    lines = _wrap_text(topic["title"], title_font, SLIDE_W - 160, draw)
    y_start = SLIDE_H // 2 - len(lines) * 50
    for line in lines:
        draw.text((SLIDE_W // 2, y_start), line, font=title_font,
                  fill=BRAND_COLORS["white"], anchor="mm")
        y_start += 100

    # Date
    date_font = _get_font(32)
    date_str = datetime.datetime.utcnow().strftime("%B %d, %Y")
    draw.text((SLIDE_W // 2, SLIDE_H - 280), date_str, font=date_font,
              fill=BRAND_COLORS["light_gray"], anchor="mm")

    # CTA at bottom
    cta_font = _get_font(30)
    draw.text((SLIDE_W // 2, SLIDE_H - 180), "Swipe for key insights \u2192",
              font=cta_font, fill=BRAND_COLORS["accent_green"], anchor="mm")

    # Bottom accent bar
    draw.rectangle([(0, SLIDE_H - 8), (SLIDE_W, SLIDE_H)], fill=BRAND_COLORS["accent_blue"])

    return img


def _create_point_slide(point, index, total, topic_title):
    """Create a content point slide."""
    img = Image.new("RGB", (SLIDE_W, SLIDE_H), BRAND_COLORS["dark_navy"])
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([(0, 0), (SLIDE_W, 8)], fill=BRAND_COLORS["accent_blue"])

    # Point number badge
    badge_size = 120
    badge_x, badge_y = 80, 160
    _draw_rounded_rect(draw, (badge_x, badge_y, badge_x + badge_size, badge_y + badge_size),
                       radius=20, fill=BRAND_COLORS["accent_blue"])
    num_font = _get_font(60, bold=True)
    draw.text((badge_x + badge_size // 2, badge_y + badge_size // 2),
              str(index + 1), font=num_font, fill=BRAND_COLORS["white"], anchor="mm")

    # Topic reference (small)
    ref_font = _get_font(24)
    draw.text((80, 320), topic_title[:50], font=ref_font,
              fill=BRAND_COLORS["light_gray"])

    # Main content text (large, wrapped)
    content_font = _get_font(52, bold=True)
    lines = _wrap_text(point, content_font, SLIDE_W - 160, draw)
    y_start = 440
    for line in lines:
        draw.text((80, y_start), line, font=content_font,
                  fill=BRAND_COLORS["white"])
        y_start += 72

    # Decorative accent line
    draw.rectangle([(80, y_start + 30), (300, y_start + 34)],
                   fill=BRAND_COLORS["accent_green"])

    # Page indicator dots
    dot_y = SLIDE_H - 200
    dot_start_x = SLIDE_W // 2 - (total * 30) // 2
    for i in range(total):
        color = BRAND_COLORS["accent_blue"] if i == index else BRAND_COLORS["light_gray"]
        cx = dot_start_x + i * 30 + 8
        draw.ellipse([(cx, dot_y), (cx + 16, dot_y + 16)], fill=color)

    # BroadFSC watermark
    wm_font = _get_font(22)
    draw.text((SLIDE_W // 2, SLIDE_H - 100), "BroadFSC.com", font=wm_font,
              fill=BRAND_COLORS["light_gray"], anchor="mm")

    # Bottom accent bar
    draw.rectangle([(0, SLIDE_H - 8), (SLIDE_W, SLIDE_H)], fill=BRAND_COLORS["accent_blue"])

    return img


def _create_cta_slide():
    """Create a call-to-action slide."""
    img = Image.new("RGB", (SLIDE_W, SLIDE_H), BRAND_COLORS["deep_blue"])
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([(0, 0), (SLIDE_W, 8)], fill=BRAND_COLORS["accent_green"])

    # BroadFSC branding
    brand_font = _get_font(64, bold=True)
    draw.text((SLIDE_W // 2, 350), "BroadFSC", font=brand_font,
              fill=BRAND_COLORS["white"], anchor="mm")

    # Tagline
    tag_font = _get_font(32)
    draw.text((SLIDE_W // 2, 440), "Expert Investment Guidance", font=tag_font,
              fill=BRAND_COLORS["accent_green"], anchor="mm")

    # Divider
    draw.rectangle([(SLIDE_W // 2 - 100, 500), (SLIDE_W // 2 + 100, 504)],
                   fill=BRAND_COLORS["white"])

    # CTA lines
    cta_lines = [
        ("Start Your Journey Today", 600, 44, True, BRAND_COLORS["white"]),
        ("Free daily market briefings", 720, 34, False, BRAND_COLORS["light_gray"]),
        ("Professional portfolio analysis", 780, 34, False, BRAND_COLORS["light_gray"]),
        ("Multi-asset global strategies", 840, 34, False, BRAND_COLORS["light_gray"]),
    ]
    for text, y, size, bold, color in cta_lines:
        f = _get_font(size, bold=bold)
        draw.text((SLIDE_W // 2, y), text, font=f, fill=color, anchor="mm")

    # Website box
    box_y = 1020
    _draw_rounded_rect(draw, (SLIDE_W // 2 - 320, box_y, SLIDE_W // 2 + 320, box_y + 90),
                       radius=16, outline=BRAND_COLORS["accent_blue"], width=3)
    url_font = _get_font(36, bold=True)
    draw.text((SLIDE_W // 2, box_y + 45), "www.broadfsc.com/different",
              font=url_font, fill=BRAND_COLORS["accent_blue"], anchor="mm")

    # Telegram link
    tg_font = _get_font(32)
    draw.text((SLIDE_W // 2, 1240), "Join us on Telegram", font=tg_font,
              fill=BRAND_COLORS["white"], anchor="mm")
    draw.text((SLIDE_W // 2, 1300), "t.me/BroadFSC", font=_get_font(36, bold=True),
              fill=BRAND_COLORS["accent_blue"], anchor="mm")

    # Disclaimer
    disc_font = _get_font(18)
    draw.text((SLIDE_W // 2, SLIDE_H - 250),
              "Investing involves risk. Past performance does not guarantee future results.",
              font=disc_font, fill=BRAND_COLORS["light_gray"], anchor="mm")
    draw.text((SLIDE_W // 2, SLIDE_H - 210),
              "BroadFSC is a licensed investment advisory firm.",
              font=disc_font, fill=BRAND_COLORS["light_gray"], anchor="mm")

    # Bottom accent bar
    draw.rectangle([(0, SLIDE_H - 8), (SLIDE_W, SLIDE_H)], fill=BRAND_COLORS["accent_green"])

    return img


def generate_carousel_images_pillow():
    """
    Generate TikTok carousel images using Pillow (with text overlay).
    Returns list of (filename, PNG bytes) tuples.
    """
    now = datetime.datetime.utcnow()
    day_of_year = now.timetuple().tm_yday
    topic_idx = day_of_year % len(CONTENT_TOPICS)
    topic = CONTENT_TOPICS[topic_idx]

    images = []

    # Slide 1: Title
    img1 = _create_title_slide(topic)
    buf1 = _img_to_bytes(img1)
    images.append(("title_slide.png", buf1))

    # Slides 2-5: Content points
    total_points = min(len(topic["points"]), 4)
    for i in range(total_points):
        img = _create_point_slide(topic["points"][i], i, total_points, topic["title"])
        buf = _img_to_bytes(img)
        images.append(("point_" + str(i + 1) + ".png", buf))

    # Last slide: CTA
    img_cta = _create_cta_slide()
    buf_cta = _img_to_bytes(img_cta)
    images.append(("cta_slide.png", buf_cta))

    return images


def _img_to_bytes(img):
    """Convert PIL Image to PNG bytes."""
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# --- Legacy fallback for non-Pillow environments ---

def create_solid_png(width, height, r, g, b):
    """Create a minimal valid PNG file with a solid color."""
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        import zlib
        crc = struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
        return struct.pack('>I', len(data)) + chunk + crc

    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    # IDAT - raw pixel data
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte
        raw_data += bytes([r, g, b]) * width

    import zlib
    compressed = zlib.compress(raw_data)
    idat = make_chunk(b'IDAT', compressed)

    # IEND
    iend = make_chunk(b'IEND', b'')

    return signature + ihdr + idat + iend


def create_gradient_png(width, height, r1, g1, b1, r2, g2, b2):
    """Create a PNG with a vertical gradient from color1 (top) to color2 (bottom)."""
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        import zlib
        crc = struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
        return struct.pack('>I', len(data)) + chunk + crc

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    raw_data = b''
    for y in range(height):
        ratio = y / max(height - 1, 1)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        raw_data += b'\x00'
        raw_data += bytes([r, g, b]) * width

    import zlib
    compressed = zlib.compress(raw_data)
    idat = make_chunk(b'IDAT', compressed)
    iend = make_chunk(b'IEND', b'')

    return signature + ihdr + idat + iend


def generate_carousel_images():
    """
    Generate TikTok carousel images as PNG bytes.
    Uses Pillow (with text overlay) if available, falls back to solid colors.
    Returns list of (filename, PNG bytes) tuples.
    """
    if HAS_PILLOW:
        print("  [Pillow] Generating branded slides with text overlay")
        return generate_carousel_images_pillow()

    # Fallback: solid/gradient PNGs (no text)
    print("  [Fallback] Pillow not available, generating solid-color slides")
    now = datetime.datetime.utcnow()
    day_of_year = now.timetuple().tm_yday
    topic_idx = day_of_year % len(CONTENT_TOPICS)
    topic = CONTENT_TOPICS[topic_idx]

    GRADIENT_TOP = (15, 23, 42)
    GRADIENT_BOTTOM = (30, 58, 138)
    DARK_BG = (15, 23, 42)

    images = []

    # Slide 1: Title slide (gradient background)
    img1 = create_gradient_png(1080, 1920, *GRADIENT_TOP, *GRADIENT_BOTTOM)
    images.append(("title_slide.png", img1))

    # Slides 2-4: Content slides (dark background with accent)
    for i, point in enumerate(topic["points"][:3]):
        img = create_solid_png(1080, 1920, *DARK_BG)
        images.append(("point_" + str(i + 1) + ".png", img))

    # Slide 5: CTA slide
    img5 = create_gradient_png(1080, 1920, *GRADIENT_BOTTOM, *GRADIENT_TOP)
    images.append(("cta_slide.png", img5))

    return images


def upload_images_to_temp(images):
    """
    Save images locally and return file paths.
    Postproxy supports direct file upload via multipart, so no external hosting needed.
    Returns list of local file paths.
    """
    paths = []
    script_dir = os.path.dirname(os.path.abspath(__file__))

    for filename, img_data in images:
        try:
            temp_path = os.path.join(script_dir, "temp_" + filename)
            with open(temp_path, "wb") as f:
                f.write(img_data)
            paths.append(temp_path)
            print("  Saved " + filename + " (" + str(len(img_data)) + " bytes)")
        except Exception as e:
            print("  Save error (" + filename + "): " + str(e))

    return paths


# ============================================================
# Image-to-Video Slideshow Generator
# ============================================================
def images_to_video(image_paths, output_path, fps=30, seconds_per_slide=3):
    """
    Convert a list of image files into an MP4 video slideshow.
    Each slide is shown for `seconds_per_slide` seconds at `fps` frames per second.
    TikTok requires 24-30fps minimum, so we duplicate frames to reach target fps.
    Uses imageio + ffmpeg (bundled, no system install needed).
    """
    if not HAS_IMAGEIO:
        print("  imageio not available, cannot create video")
        return False

    try:
        frames = []
        frames_per_slide = fps * seconds_per_slide  # e.g. 30fps * 3s = 90 frames per slide
        
        for path in image_paths:
            img = Image.open(path).convert("RGB")
            # Ensure size matches SLIDE_W x SLIDE_H (divisible by 16)
            if img.size != (SLIDE_W, SLIDE_H):
                img = img.resize((SLIDE_W, SLIDE_H), Image.LANCZOS)
            arr = np.array(img)
            for _ in range(frames_per_slide):
                frames.append(arr)

        total_duration = len(frames) // fps
        writer = iio.get_writer(output_path, fps=fps, codec='libx264',
                                output_params=['-pix_fmt', 'yuv420p'])
        for frame in frames:
            writer.append_data(frame)
        writer.close()

        file_size = os.path.getsize(output_path)
        print("  Video created: " + output_path + " (" + str(file_size) + " bytes, " +
              str(len(frames)) + " frames @ " + str(fps) + "fps = " + str(total_duration) + "s)")
        return True
    except Exception as e:
        print("  Video creation failed: " + str(e))
        return False


# ============================================================
# Postproxy API
# ============================================================
def post_tiktok_image(caption, image_paths):
    """Post a TikTok image carousel via Postproxy API using direct file upload."""
    if not POSTPROXY_API_KEY:
        print("  TikTok: Missing POSTPROXY_API_KEY")
        return False

    if not image_paths:
        print("  TikTok: No image paths provided")
        return False

    api_url = POSTPROXY_BASE_URL + "/posts"
    headers = {
        "Authorization": "Bearer " + POSTPROXY_API_KEY,
    }

    # Build multipart form data
    data = {
        "post[body]": caption,
        "profiles[]": "tiktok",
        "platforms[tiktok][format]": "image",
        "platforms[tiktok][privacy_status]": "PUBLIC_TO_EVERYONE",
        "platforms[tiktok][auto_add_music]": "true",
        "platforms[tiktok][disable_comment]": "false",
    }

    files = []
    open_files = []
    try:
        for path in image_paths:
            f = open(path, "rb")
            open_files.append(f)
            files.append(("media[]", (os.path.basename(path), f, "image/png")))

        r = requests.post(api_url, headers=headers, data=data, files=files, timeout=60)
        if r.status_code in [200, 201]:
            result = r.json()
            post_id = result.get("id", "unknown")
            print("  TikTok: Image carousel posted! ID: " + str(post_id))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:400])
            return False
    except Exception as e:
        print("  TikTok: FAIL - " + str(e))
        return False
    finally:
        for f in open_files:
            try:
                f.close()
            except Exception:
                pass


def post_tiktok_video(caption, video_url):
    """Post a TikTok video via Postproxy API."""
    if not POSTPROXY_API_KEY:
        print("  TikTok: Missing POSTPROXY_API_KEY")
        return False

    if not video_url:
        print("  TikTok: No video URL provided")
        return False

    url = POSTPROXY_BASE_URL + "/posts"
    headers = {
        "Authorization": "Bearer " + POSTPROXY_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "post": {
            "body": caption,
        },
        "profiles": ["tiktok"],
        "media": [video_url],
        "platforms": {
            "tiktok": {
                "format": "video",
                "privacy_status": "PUBLIC_TO_EVERYONE",
                "disable_comment": False,
                "disable_duet": False,
                "disable_stitch": False,
            }
        }
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code in [200, 201]:
            data = r.json()
            post_id = data.get("id", "unknown")
            print("  TikTok: Video posted! ID: " + str(post_id))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:400])
            return False
    except Exception as e:
        print("  TikTok: FAIL - " + str(e))
        return False


def post_tiktok_video_file(caption, video_file_path):
    """Post a TikTok video from local file via Postproxy API (multipart)."""
    if not POSTPROXY_API_KEY:
        print("  TikTok: Missing POSTPROXY_API_KEY")
        return False

    if not os.path.exists(video_file_path):
        print("  TikTok: Video file not found: " + video_file_path)
        return False

    url = POSTPROXY_BASE_URL + "/posts"
    headers = {
        "Authorization": "Bearer " + POSTPROXY_API_KEY,
    }

    try:
        with open(video_file_path, "rb") as f:
            files = {
                "media[]": (os.path.basename(video_file_path), f, "video/mp4"),
            }
            data = {
                "post[body]": caption,
                "profiles[]": "tiktok",
            }
            # Note: platform params as form fields
            data["platforms[tiktok][format]"] = "video"
            data["platforms[tiktok][privacy_status]"] = "PUBLIC_TO_EVERYONE"

            r = requests.post(url, headers=headers, data=data, files=files, timeout=120)

        if r.status_code in [200, 201]:
            post_id = r.json().get("id", "unknown")
            print("  TikTok: Video file posted! ID: " + str(post_id))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:400])
            return False
    except Exception as e:
        print("  TikTok: FAIL - " + str(e))
        return False


# ============================================================
# Free Stock Chart Image Generator
# ============================================================
def get_free_stock_chart_urls():
    """
    Get free stock chart image URLs from public sources.
    These can be used as TikTok carousel images.
    """
    # Using finviz.com free chart screenshots (publicly accessible)
    tickers = ["SPY", "QQQ", "DIA", "IWM", "GLD"]
    chart_type = "c"  # daily candle
    # finviz charts are publicly accessible, no API key needed
    urls = []
    for ticker in random.sample(tickers, min(3, len(tickers))):
        url = "https://finviz.com/chart.ashx?t=" + ticker + "&ty=" + chart_type + "&ta=1&p=d"
        urls.append((ticker + "_chart", url))
    return urls


def download_chart_images():
    """Download stock chart images from free sources."""
    chart_urls = get_free_stock_chart_urls()
    image_urls = []

    for name, url in chart_urls:
        try:
            r = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }, timeout=15)
            if r.status_code == 200 and len(r.content) > 1000:
                # Save and re-upload to temp hosting
                temp_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "temp_" + name + ".png"
                )
                with open(temp_path, "wb") as f:
                    f.write(r.content)

                # Upload to catbox.moe for public URL
                with open(temp_path, "rb") as f:
                    upload_r = requests.post(
                        "https://catbox.moe/user/api.php",
                        files={"fileToUpload": (name + ".png", f, "image/png")},
                        data={"reqtype": "fileupload"},
                        timeout=30
                    )
                    if upload_r.status_code == 200 and upload_r.text.strip().startswith("http"):
                        public_url = upload_r.text.strip()
                        image_urls.append(public_url)
                        print("  Chart " + name + " uploaded: " + public_url)

                # Clean up
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        except Exception as e:
            print("  Chart download error (" + name + "): " + str(e))

    return image_urls


# ============================================================
# Telegram Notification
# ============================================================
def notify_telegram(message):
    """Send notification to Telegram channel."""
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": message}, timeout=10)
    except Exception:
        pass


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 50)
    print("BroadFSC TikTok Auto-Poster")
    print("=" * 50)

    now = datetime.datetime.utcnow()
    print("Current UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print("POSTPROXY_API_KEY: " + ("SET" if POSTPROXY_API_KEY else "NOT SET"))
    print("GROQ_API_KEY: " + ("SET" if GROQ_API_KEY else "NOT SET (using fallback)"))
    print("Mode: " + TIKTOK_MODE.upper())
    print("Pillow: " + ("YES" if HAS_PILLOW else "NO"))
    print("imageio: " + ("YES" if HAS_IMAGEIO else "NO"))
    print()

    # Step 1: Generate caption
    print("--- Step 1: Generate Caption ---")
    caption = generate_tiktok_caption()
    print("  Caption: " + caption[:100] + ("..." if len(caption) > 100 else ""))
    print()

    # Step 2: Post based on mode
    success = False

    if TIKTOK_MODE == "video":
        # --- DIRECT VIDEO MODE ---
        print("--- Step 2: Direct Video Mode ---")
        video_url = TIKTOK_VIDEO_URL

        if video_url:
            print("  Video URL: " + video_url[:80] + "...")
            success = post_tiktok_video(caption, video_url)
        else:
            # Check for local video file
            video_dir = os.path.dirname(os.path.abspath(__file__))
            video_path = os.path.join(video_dir, "tiktok_video.mp4")
            if os.path.exists(video_path):
                print("  Video file: " + video_path)
                success = post_tiktok_video_file(caption, video_path)
            else:
                print("  No video URL or file found!")
                print("  Set TIKTOK_VIDEO_URL env var or place tiktok_video.mp4 in script directory")
                print("  Falling back to slideshow mode...")
                TIKTOK_MODE_ACTUAL = "slideshow"

    if TIKTOK_MODE != "video" or not success:
        # --- SLIDESHOW MODE (default) ---
        # TikTok only supports VIDEO, so we create images → convert to MP4 → post
        print("--- Step 2: Slideshow-to-Video Mode ---")

        # Generate branded carousel images
        print("  Generating carousel images...")
        images = generate_carousel_images()
        print("  Created " + str(len(images)) + " slides")

        # Save images locally
        print("  Saving images...")
        image_paths = upload_images_to_temp(images)

        if image_paths:
            if HAS_IMAGEIO:
                # Convert images to video
                print("  Converting images to MP4 video...")
                video_dir = os.path.dirname(os.path.abspath(__file__))
                video_path = os.path.join(video_dir, "tiktok_slideshow.mp4")
                if images_to_video(image_paths, video_path, fps=30, seconds_per_slide=3):
                    # Post the video file
                    success = post_tiktok_video_file(caption, video_path)

                    # Clean up video
                    try:
                        os.remove(video_path)
                    except Exception:
                        pass
                else:
                    print("  Video creation failed, trying image post as fallback...")
                    success = post_tiktok_image(caption, image_paths)
            else:
                # Fallback: try image post (will likely fail on TikTok)
                print("  imageio not available, attempting image post (may fail on TikTok)...")
                success = post_tiktok_image(caption, image_paths)

            # Clean up temp images
            for path in image_paths:
                try:
                    os.remove(path)
                except Exception:
                    pass
        else:
            print("  Image generation failed!")

    print()

    # Step 3: Notify
    if success:
        notify_telegram("\u2705 TikTok post published: " + caption[:80])
        print("SUCCESS: TikTok post published!")
    else:
        notify_telegram("\u274c TikTok post FAILED")
        print("FAILED: TikTok post could not be published.")

    print()
    print("=" * 50)
    print("TikTok posting complete.")


if __name__ == "__main__":
    main()
