"""
BroadFSC TikTok Auto-Poster v3 — Viral Finance Style
Posts daily market insights as TikTok videos in the style of top finance creators.

Style reference: @thinkarytok — fast-paced, text-overlay, conversational, human-like
Key principles:
- 2-3 second cuts (fast pacing, no stale frames)
- Big bold text overlays on dark/cinematic backgrounds
- Conversational script — like talking to a friend, NOT a lecture
- Ken Burns zoom + smooth crossfade transitions
- Ambient background music with subtle beat
- Bottom subtitles for silent viewers (80% watch on mute)
- Hook in first 1 second, CTA in last 2 seconds
- 15-25 seconds total (optimal for completion rate)

Postproxy API: https://postproxy.dev/reference/posts/
Environment variables:
  POSTPROXY_API_KEY - Required
  GROQ_API_KEY - Optional. For AI-generated scripts
  TELEGRAM_BOT_TOKEN - Optional. For notifications
  TELEGRAM_CHANNEL_ID - Optional. For notifications
"""

import os
import sys
import datetime
import requests
import json
import random
import struct
import math
import io

# Analytics tracking
try:
    from analytics_logger import log_post
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

WEBSITE_LINK = "https://www.broadfsc.com/different"
TELEGRAM_LINK = "https://t.me/BroadFSC"

# Video settings — optimized for TikTok algorithm
W, H = 1088, 1920  # 9:16, width divisible by 16
FPS = 30
SECONDS_PER_SCENE = 3  # Fast! 2-3 sec per scene
TRANSITION_FRAMES = 12  # 0.4s crossfade — snappy
TOTAL_SCENES = 6  # hook + 4 points + CTA

# ============================================================
# Color Palette — cinematic dark finance
# ============================================================
C = {
    "bg_dark": (10, 12, 22),
    "bg_mid": (16, 20, 38),
    "bg_warm": (22, 18, 32),
    "accent": (65, 145, 255),  # electric blue
    "green": (0, 220, 140),
    "gold": (255, 195, 15),
    "red": (255, 65, 65),
    "white": (255, 255, 255),
    "gray": (140, 155, 185),
    "dim": (60, 70, 100),
    "overlay": (0, 0, 0),
}


# ============================================================
# Human Conversational Scripts — NOT AI-sounding
# ============================================================
SCRIPTS = [
    {
        "hook": "Nobody talks about this but...",
        "scenes": [
            "The stock market doesn't care about your feelings",
            "It cares about earnings, rates, and institutional flows",
            "Right now? Smart money is rotating into sectors most people ignore",
            "Defense, infrastructure, healthcare — not just Big Tech",
        ],
        "cta": "Follow for what the market's actually doing",
    },
    {
        "hook": "I wish someone told me this at 25...",
        "scenes": [
            "You don't need to pick winning stocks to build wealth",
            "Index funds beat 90% of active managers over 10 years",
            "But WHEN you buy matters more than WHAT you buy",
            "Dollar-cost averaging into dips? That's the real cheat code",
        ],
        "cta": "Save this and thank me later",
    },
    {
        "hook": "The Fed just signaled something huge",
        "scenes": [
            "And most people are completely ignoring it",
            "When the Fed pauses, bonds become the hidden play",
            "Short-term yields still paying 4-5% while stocks swing wildly",
            "That's free money while you wait for clarity",
        ],
        "cta": "Follow for daily market breakdowns",
    },
    {
        "hook": "Stop checking your portfolio every hour",
        "scenes": [
            "Seriously. The people making real money? They set it and forget it",
            "The S&P 500's best days always come right after the worst days",
            "If you sold during the dip, you missed the bounce. Every. Single. Time.",
            "Time in the market beats timing the market. Every. Single. Time.",
        ],
        "cta": "Share this with someone who needs to hear it",
    },
    {
        "hook": "3 numbers that moved markets this week",
        "scenes": [
            "Number one — CPI came in hot. Inflation's not dead yet",
            "Number two — jobless claims hit a new low. Labor market still strong",
            "Number three — 10-year yield broke above 4.5%. That's your real signal",
            "When yields spike, growth stocks get nervous. Value stocks wake up",
        ],
        "cta": "I break this down every day — follow",
    },
    {
        "hook": "This is why rich people stay rich",
        "scenes": [
            "It's not about picking the right stock. It's about asset allocation",
            "When stocks crash, bonds cushion. When bonds fall, commodities hedge",
            "The rich never bet everything on one thing. Ever.",
            "And they rebalance quarterly. Most people never rebalance at all",
        ],
        "cta": "Follow for smarter money moves",
    },
    {
        "hook": "Everyone's buying the wrong thing right now",
        "scenes": [
            "FOMO is not a strategy. Chasing last week's winner never works",
            "The real opportunity? Sectors that haven't moved yet",
            "Energy, financials, industrials — they're quietly setting up",
            "By the time everyone notices, the smart money is already out",
        ],
        "cta": "Don't be last to know — follow",
    },
]


# ============================================================
# AI Script Generation — Ultra-conversational
# ============================================================
def generate_script():
    """Generate today's video script. AI first, fallback to library."""
    if not GROQ_API_KEY:
        return _pick_script()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "Write a TikTok finance video script. Today is " + day + ".\n\n"
                    "FORMAT — return ONLY valid JSON, nothing else:\n"
                    '{\n'
                    '  "hook": "1 short sentence that makes people stop scrolling",\n'
                    '  "scenes": ["line1", "line2", "line3", "line4"],\n'
                    '  "cta": "1 short call to action"\n'
                    '}\n\n'
                    "CRITICAL STYLE — write like a 28-year-old talking to their friend at a bar:\n"
                    "- Use 'gonna', 'wanna', 'gotta', 'kinda', 'dude', 'man', 'tbh', 'ngl'\n"
                    "- Start sentences with 'So', 'Like', 'But', 'And', 'Look'\n"
                    "- Break grammar rules on purpose (it sounds more human)\n"
                    "- Each scene: max 10 words, raw and punchy\n"
                    "- The hook: under 6 words, must create FOMO or curiosity\n"
                    "- CTA: max 6 words, casual like 'follow for more' or 'save this rn'\n"
                    "\n"
                    "FORBIDDEN WORDS (these scream 'AI wrote this'):\n"
                    "- game changer, pro tip, ninja, hack, you wont believe\n"
                    "- navigate, landscape, leverage, unlock, dive, delve\n"
                    "- crucial, vital, essential, paramount, comprehensive\n"
                    "- moreover, furthermore, additionally, consequently\n"
                    "- in today's, in this, let's explore, let's dive\n"
                    "\n"
                    "TOPICS: Fed, earnings, rates, inflation, diversification, market psychology, index funds\n"
                    "- Pick a topic relevant to " + day + "\n"
                    "- Do NOT promise returns or give buy/sell advice"
                )
            }],
            max_tokens=200,
            temperature=0.95
        )

        text = response.choices[0].message.content.strip()
        # Try to parse JSON from the response
        # Sometimes AI wraps in markdown code block
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        # Try to extract JSON object even if surrounding text exists
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]

        data = json.loads(text)
        # Validate structure
        if "hook" in data and "scenes" in data and "cta" in data and len(data["scenes"]) >= 3:
            return data
        else:
            return _pick_script()

    except Exception as e:
        print("  AI script generation failed: " + str(e))
        return _pick_script()


def _pick_script():
    """Pick a script from the library based on day."""
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(SCRIPTS)
    return SCRIPTS[idx]


def generate_caption(script):
    """Generate TikTok caption from script — casual, hashtag-light."""
    if not GROQ_API_KEY:
        hook = script["hook"]
        return hook + " #investing #finance #money"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "Write a TikTok caption for a FINANCE video:\n"
                    "Hook: " + script["hook"] + "\n\n"
                    "Rules:\n"
                    "- Max 150 characters\n"
                    "- MUST be about investing/money/markets — this is a finance channel\n"
                    "- Sound like a real person, not a brand\n"
                    "- 2-3 hashtags max, lowercase like #investing #money\n"
                    "- No emoji spam (1 emoji max)\n"
                    "- FORBIDDEN: game changer, you wont believe, pro tip, hack\n"
                    "- FORBIDDEN: navigate, landscape, leverage, unlock, dive, delve\n"
                    "- No financial advice or return promises"
                )
            }],
            max_tokens=60,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception:
        hook = script["hook"]
        return hook + " #investing #finance"


# ============================================================
# Font Helper
# ============================================================
def _font(size, bold=False):
    """Get a font — prefer bold Impact/Arial for TikTok style."""
    paths = []
    if bold:
        paths = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(text, font, max_w, draw):
    """Word-wrap text to fit within max_w pixels."""
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + (" " if cur else "") + w
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ============================================================
# Background Generators — Cinematic & Varied
# ============================================================
def _gradient_bg(w, h, top, bot):
    """Smooth vertical gradient."""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * r) for i in range(3))
        draw.line([(0, y), (w, y)], fill=c)
    return img


def _noise(img, intensity=6):
    """Add subtle noise texture."""
    arr = np.array(img).copy()
    noise = np.random.randint(-intensity, intensity + 1, arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _vignette(img, strength=0.4):
    """Add dark vignette around edges — cinematic look."""
    w, h = img.size
    arr = np.array(img, dtype=np.float32)
    # Create radial gradient
    cx, cy = w / 2, h / 2
    max_dist = math.sqrt(cx * cx + cy * cy)
    y_coords, x_coords = np.ogrid[:h, :w]
    dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    vignette = 1 - (dist / max_dist) * strength
    vignette = np.clip(vignette, 0.3, 1.0)
    arr[:, :, 0] *= vignette
    arr[:, :, 1] *= vignette
    arr[:, :, 2] *= vignette
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# Background style variations — each scene gets a different look
BG_STYLES = [
    # (top_color, bottom_color, pattern)
    {"top": (8, 10, 20), "bot": (18, 25, 55), "style": "clean"},
    {"top": (15, 10, 30), "bot": (25, 20, 50), "style": "warm"},
    {"top": (5, 15, 30), "bot": (20, 35, 65), "style": "cool"},
    {"top": (18, 12, 12), "bot": (35, 22, 25), "style": "warm_red"},
    {"top": (8, 18, 15), "bot": (15, 35, 30), "style": "green_tint"},
    {"top": (12, 10, 25), "bot": (28, 25, 55), "style": "purple"},
]


def _make_bg(scene_idx):
    """Create a cinematic background for a scene."""
    style = BG_STYLES[scene_idx % len(BG_STYLES)]
    img = _gradient_bg(W, H, style["top"], style["bot"])
    img = _noise(img, 5)
    img = _vignette(img, 0.35)

    draw = ImageDraw.Draw(img)

    # Subtle horizontal light streak (lens flare feel)
    if scene_idx % 2 == 0:
        streak_y = random.randint(H // 3, 2 * H // 3)
        for dy in range(-30, 30):
            alpha = max(0, 15 - abs(dy))
            if alpha > 0:
                draw.line([(0, streak_y + dy), (W, streak_y + dy)],
                         fill=(alpha, alpha, alpha + 5))

    return img


# ============================================================
# Scene Rendering — Big Text Overlay Style (thinkarytok-style)
# ============================================================
def _render_hook_scene(script):
    """Opening hook — BIG text, maximum impact, minimal clutter."""
    img = _make_bg(0)
    draw = ImageDraw.Draw(img)

    # Small tag top-left
    tag_font = _font(22, bold=True)
    draw.rounded_rectangle((40, 60, 220, 100), radius=20, fill=C["accent"])
    draw.text((130, 80), "BroadFSC", font=tag_font, fill=C["white"], anchor="mm")

    # Hook text — EXTRA LARGE, centered, white
    hook_font = _font(78, bold=True)
    lines = _wrap(script["hook"], hook_font, W - 120, draw)

    total_h = len(lines) * 100
    y = (H // 2) - (total_h // 2) - 40

    for line in lines:
        # Shadow
        draw.text((62, y + 3), line, font=hook_font, fill=(0, 0, 0))
        # Main text
        draw.text((60, y), line, font=hook_font, fill=C["white"])
        y += 100

    # Accent underline
    draw.rectangle([(60, y + 30), (300, y + 35)], fill=C["green"])

    # "Keep watching" hint
    hint_font = _font(24)
    draw.text((W // 2, H - 280), "keep watching...",
              font=hint_font, fill=C["dim"], anchor="mm")

    return img


def _render_scene(text, idx, total, hook_text):
    """Content scene — big text, minimal design, conversational feel."""
    img = _make_bg(idx + 1)
    draw = ImageDraw.Draw(img)

    # Scene number indicator — small, top-right
    num_font = _font(20, bold=True)
    draw.rounded_rectangle((W - 130, 60, W - 40, 95), radius=17, fill=C["dim"])
    draw.text((W - 85, 77), str(idx + 1) + "/" + str(total),
              font=num_font, fill=C["white"], anchor="mm")

    # Main text — big, centered, white
    text_font = _font(58, bold=True)
    lines = _wrap(text, text_font, W - 140, draw)

    total_h = len(lines) * 78
    y = (H // 2) - (total_h // 2) - 20

    for line in lines:
        # Shadow for depth
        draw.text((72, y + 3), line, font=text_font, fill=(0, 0, 0))
        # White text
        draw.text((70, y), line, font=text_font, fill=C["white"])
        y += 78

    # Decorative accent line
    accent_colors = [C["accent"], C["green"], C["gold"]]
    accent = accent_colors[idx % len(accent_colors)]
    draw.rectangle([(70, y + 35), (70 + 180, y + 39)], fill=accent)

    # Subtle context from hook — very small, bottom
    ctx_font = _font(18)
    draw.text((W // 2, H - 300), hook_text[:50],
              font=ctx_font, fill=C["dim"], anchor="mm")

    return img


def _render_cta_scene(script):
    """CTA scene — clean, warm, inviting."""
    img = _make_bg(5)
    draw = ImageDraw.Draw(img)

    # CTA text — big
    cta_font = _font(60, bold=True)
    lines = _wrap(script["cta"], cta_font, W - 140, draw)

    y = H // 2 - 200
    for line in lines:
        draw.text((72, y + 3), line, font=cta_font, fill=(0, 0, 0))
        draw.text((70, y), line, font=cta_font, fill=C["green"])
        y += 82

    # Divider
    draw.rectangle([(W // 2 - 60, y + 40), (W // 2 + 60, y + 44)], fill=C["accent"])

    # Website in pill
    pill_w, pill_h = 550, 60
    pill_x = W // 2 - pill_w // 2
    pill_y = y + 90
    draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
                          radius=30, fill=C["accent"])
    url_font = _font(26, bold=True)
    draw.text((W // 2, pill_y + pill_h // 2), "broadfsc.com/different",
              font=url_font, fill=C["white"], anchor="mm")

    # Telegram
    tg_font = _font(22)
    draw.text((W // 2, pill_y + pill_h + 50), "t.me/BroadFSC",
              font=tg_font, fill=C["gray"], anchor="mm")

    # Disclaimer — tiny, bottom
    disc_font = _font(14)
    draw.text((W // 2, H - 160),
              "Investing involves risk. Past performance does not guarantee future results.",
              font=disc_font, fill=C["dim"], anchor="mm")

    return img


# ============================================================
# Video Generation — Fast-paced, Professional
# ============================================================
def _ken_burns(img, frame, total, zoom_s=1.0, zoom_e=1.06, pan_x=0.0, pan_y=0.02):
    """Apply Ken Burns (slow zoom + pan) for one frame."""
    t = frame / max(total - 1, 1)
    t = t * t * (3 - 2 * t)  # smoothstep ease

    zoom = zoom_s + (zoom_e - zoom_s) * t
    px = pan_x * t
    py = pan_y * t

    w, h = img.size
    nw = int(w / zoom)
    nh = int(h / zoom)

    cx = w // 2 + int(px * w)
    cy = h // 2 + int(py * h)

    left = max(0, cx - nw // 2)
    top = max(0, cy - nh // 2)
    if left + nw > w:
        left = w - nw
    if top + nh > h:
        top = h - nh
    left = max(0, left)
    top = max(0, top)

    cropped = img.crop((left, top, left + nw, top + nh))
    return cropped.resize((W, H), Image.LANCZOS)


def _crossfade(a, b, alpha):
    """Blend two frames."""
    aa = np.array(a, dtype=np.float32)
    bb = np.array(b, dtype=np.float32)
    return np.clip(aa * (1 - alpha) + bb * alpha, 0, 255).astype(np.uint8)


def _subtitle_frame(frame, text, idx, total):
    """Add bottom subtitle bar with fade-in/out."""
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)

    # Fade envelope
    fade = max(total // 8, 1)
    if idx < fade:
        a = idx / fade
    elif idx > total - fade:
        a = (total - idx) / fade
    else:
        a = 1.0

    # Semi-transparent bar
    bar_y = H - 250
    bar_h = 90
    # Dark overlay
    overlay = Image.new("RGBA", (W, bar_h), (0, 0, 0, int(180 * a)))
    bg = Image.new("RGB", (W, bar_h), C["bg_dark"])
    blended = Image.blend(bg, Image.new("RGB", (W, bar_h), C["overlay"]), 0.75)
    img.paste(blended, (0, bar_y))

    # Text
    sub_font = _font(36, bold=True)
    lines = _wrap(text, sub_font, W - 100, draw)
    ty = bar_y + (bar_h - len(lines) * 46) // 2

    # Color with alpha
    r = int(255 * a)
    g = int(255 * a)
    b = int(255 * a)
    for line in lines:
        draw.text((50, ty + 2), line, font=sub_font, fill=(0, 0, 0))
        draw.text((50, ty), line, font=sub_font, fill=(r, g, b))
        ty += 46

    return np.array(img)


def _generate_music(duration_sec, sr=44100):
    """Generate ambient background music with subtle beat."""
    total = int(sr * duration_sec)
    music = [0.0] * total

    # Chord progression: Am → F → C → G (moody, cinematic)
    chords = [
        [220.00, 261.63, 329.63],  # Am
        [174.61, 220.00, 261.63],  # F
        [261.63, 329.63, 392.00],  # C
        [196.00, 246.94, 293.66],  # G
    ]

    chord_dur = total // len(chords)

    for ci, chord in enumerate(chords):
        start = ci * chord_dur
        end = min(start + chord_dur, total)

        for i in range(start, end):
            t = i / sr
            local_t = (i - start) / chord_dur
            env = math.sin(math.pi * local_t)

            s = 0
            for freq in chord:
                s += math.sin(2 * math.pi * freq * t) * 0.06
                s += math.sin(2 * math.pi * freq * 1.003 * t) * 0.03  # chorus
                s += math.sin(2 * math.pi * freq * 0.997 * t) * 0.03  # detune

            # Subtle bass pulse (60 BPM feel)
            beat_env = 0.5 + 0.5 * math.sin(2 * math.pi * 1.0 * t)
            s += math.sin(2 * math.pi * 55 * t) * 0.04 * beat_env  # sub bass

            music[i] += s * env * 0.3

    # Global fade
    fade = min(sr, total // 5)
    for i in range(fade):
        f = i / fade
        music[i] *= f
        music[total - 1 - i] *= f

    # Normalize
    mx = max(abs(v) for v in music) or 1
    music = [int(v / mx * 10000) for v in music]

    return music


def _save_wav(samples, path, sr=44100):
    """Save audio as WAV."""
    import wave
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        data = struct.pack('<' + 'h' * len(samples), *samples)
        wf.writeframes(data)


def _merge_av(video_path, audio_path, output_path):
    """Merge audio WAV + video MP4 using ffmpeg."""
    try:
        import subprocess
        ffmpeg_exe = None
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
        if not ffmpeg_exe:
            return False

        cmd = [
            ffmpeg_exe, '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print("  Audio merge failed: " + str(e))
        return False


def create_video(script, output_path):
    """Create a TikTok-optimized video: fast-paced, text-overlay, cinematic."""
    if not HAS_IMAGEIO or not HAS_PILLOW:
        print("  Pillow + imageio required")
        return False

    try:
        # 1. Render all scene images
        print("  Rendering scenes...")
        scenes = []

        # Hook
        hook_img = _render_hook_scene(script)
        scenes.append(("hook", script["hook"], hook_img))

        # Content scenes
        total = len(script["scenes"])
        for i, line in enumerate(script["scenes"]):
            img = _render_scene(line, i, total, script["hook"])
            scenes.append(("scene_" + str(i), line, img))

        # CTA
        cta_img = _render_cta_scene(script)
        scenes.append(("cta", script["cta"], cta_img))

        print("  Created " + str(len(scenes)) + " scenes")

        # 2. Animate frames — fast pacing
        frames_per_scene = FPS * SECONDS_PER_SCENE  # 3s × 30fps = 90 frames
        all_frames = []

        print("  Rendering frames with Ken Burns + transitions...")
        for si, (name, subtitle, img) in enumerate(scenes):
            # Randomize Ken Burns per scene for variety
            zoom_e = 1.0 + random.uniform(0.03, 0.08)
            pan_x = random.uniform(-0.02, 0.02)
            pan_y = random.uniform(0.0, 0.025)

            scene_frames = []
            for f in range(frames_per_scene):
                kb = _ken_burns(img, f, frames_per_scene,
                               zoom_s=1.0, zoom_e=zoom_e, pan_x=pan_x, pan_y=pan_y)
                scene_frames.append(np.array(kb))

            # Add subtitles
            for f in range(frames_per_scene):
                scene_frames[f] = _subtitle_frame(scene_frames[f], subtitle, f, frames_per_scene)

            # Crossfade with previous scene
            if all_frames and si > 0:
                for t in range(TRANSITION_FRAMES):
                    alpha = t / TRANSITION_FRAMES
                    prev_idx = len(all_frames) - TRANSITION_FRAMES + t
                    if 0 <= prev_idx < len(all_frames):
                        all_frames[prev_idx] = _crossfade(
                            all_frames[prev_idx], scene_frames[t], alpha)

            all_frames.extend(scene_frames)

        total_frames = len(all_frames)
        total_sec = total_frames // FPS
        print("  Total: " + str(total_frames) + " frames (" + str(total_sec) + "s)")

        # 3. Write video (no audio)
        temp_video = output_path + ".noaudio.mp4"
        print("  Encoding MP4...")
        writer = iio.get_writer(temp_video, fps=FPS, codec='libx264',
                                output_params=['-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '22'])
        for frame in all_frames:
            writer.append_data(frame)
        writer.close()

        # 4. Generate + merge music
        print("  Generating background music...")
        music = _generate_music(total_sec)
        temp_audio = output_path + ".temp.wav"
        _save_wav(music, temp_audio)

        merged = _merge_av(temp_video, temp_audio, output_path)

        if merged:
            for f in [temp_video, temp_audio]:
                try:
                    os.remove(f)
                except Exception:
                    pass
            sz = os.path.getsize(output_path)
            print("  Video: " + output_path + " (" + str(sz) + " bytes, " +
                  str(total_frames) + "f @ " + str(FPS) + "fps = " + str(total_sec) + "s)")
            return True
        else:
            # Use video without audio
            try:
                os.rename(temp_video, output_path)
                try:
                    os.remove(temp_audio)
                except Exception:
                    pass
            except Exception:
                pass
            sz = os.path.getsize(output_path)
            print("  Video (no audio): " + output_path + " (" + str(sz) + " bytes)")
            return True

    except Exception as e:
        print("  Video creation failed: " + str(e))
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# Postproxy API
# ============================================================
def post_tiktok_video_file(caption, video_path):
    """Post a TikTok video file via Postproxy API."""
    if not POSTPROXY_API_KEY:
        print("  TikTok: Missing POSTPROXY_API_KEY")
        return False
    if not os.path.exists(video_path):
        print("  TikTok: File not found: " + video_path)
        return False

    url = POSTPROXY_BASE_URL + "/posts"
    headers = {"Authorization": "Bearer " + POSTPROXY_API_KEY}

    try:
        with open(video_path, "rb") as f:
            files = {"media[]": (os.path.basename(video_path), f, "video/mp4")}
            data = {
                "post[body]": caption,
                "profiles[]": "tiktok",
                "platforms[tiktok][format]": "video",
                "platforms[tiktok][privacy_status]": "PUBLIC_TO_EVERYONE",
            }
            r = requests.post(url, headers=headers, data=data, files=files, timeout=120)

        if r.status_code in [200, 201]:
            post_id = r.json().get("id", "unknown")
            print("  TikTok: Posted! ID: " + str(post_id))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:400])
            return False
    except Exception as e:
        print("  TikTok: FAIL - " + str(e))
        return False


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
    print("BroadFSC TikTok Auto-Poster v3")
    print("Viral Finance Style")
    print("=" * 50)

    now = datetime.datetime.utcnow()
    print("UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print("POSTPROXY_API_KEY: " + ("SET" if POSTPROXY_API_KEY else "NOT SET"))
    print("GROQ_API_KEY: " + ("SET" if GROQ_API_KEY else "NOT SET"))
    print("Pillow: " + ("YES" if HAS_PILLOW else "NO"))
    print("imageio: " + ("YES" if HAS_IMAGEIO else "NO"))
    print()

    # Step 1: Generate script
    print("--- Step 1: Generate Script ---")
    script = generate_script()
    print("  Hook: " + script["hook"])
    print("  Scenes: " + str(len(script["scenes"])))
    for i, s in enumerate(script["scenes"]):
        print("    " + str(i + 1) + ". " + s)
    print("  CTA: " + script["cta"])
    print()

    # Step 2: Generate caption
    print("--- Step 2: Generate Caption ---")
    caption = generate_caption(script)
    print("  " + caption)
    print()

    # Step 3: Create + post video
    print("--- Step 3: Create & Post Video ---")
    success = False
    video_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(video_dir, "tiktok_slideshow.mp4")

    if HAS_PILLOW and HAS_IMAGEIO:
        if create_video(script, video_path):
            success = post_tiktok_video_file(caption, video_path)
            try:
                os.remove(video_path)
            except Exception:
                pass
        else:
            print("  Video creation failed!")
    else:
        print("  Pillow + imageio required!")

    print()

    # Step 4: Notify
    if success:
        notify_telegram("TikTok v3 post published: " + caption[:80])
        print("SUCCESS: TikTok post published!")
        if HAS_ANALYTICS:
            log_post(platform="tiktok", post_type="video", content_preview=caption[:100], status="success")
    else:
        notify_telegram("TikTok v3 post FAILED")
        print("FAILED: TikTok post not published.")
        if HAS_ANALYTICS:
            log_post(platform="tiktok", post_type="video", content_preview=caption[:100], status="failed", error_msg="Postproxy upload failed")

    print()
    print("=" * 50)
    print("Done.")


if __name__ == "__main__":
    main()
