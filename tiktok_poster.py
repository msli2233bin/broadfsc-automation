"""
BroadFSC TikTok Auto-Poster v2 — Professional Video Edition
Posts daily market insights as TikTok videos with animations, music & subtitles.

Postproxy API: https://postproxy.dev/reference/posts/
- Bearer Token auth
- TikTok ONLY supports video (not image carousels)
- Pipeline: AI generates conversational script → Pillow renders frames → 
  Ken Burns animations + transitions + subtitles + music → MP4 → Postproxy posts video

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
import struct
import math
import io

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
TIKTOK_VIDEO_URL = os.environ.get("TIKTOK_VIDEO_URL", "")

# Notification
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Post mode: "slideshow" (default) or "video"
TIKTOK_MODE = os.environ.get("TIKTOK_MODE", "slideshow").lower()

WEBSITE_LINK = "https://www.broadfsc.com/different"
TELEGRAM_LINK = "https://t.me/BroadFSC"

# Video settings
SLIDE_W, SLIDE_H = 1088, 1920  # TikTok 9:16, width must be divisible by 16
FPS = 30
SECONDS_PER_SLIDE = 4  # Each slide shows for 4 seconds
TRANSITION_FRAMES = 15  # 0.5s crossfade transition
INTRO_FRAMES = 30  # 1s intro animation
OUTRO_FRAMES = 30  # 1s outro animation

# ============================================================
# Brand palette — sleek dark finance aesthetic
# ============================================================
BRAND_COLORS = {
    "dark_navy": (12, 18, 35),
    "deep_blue": (20, 40, 100),
    "accent_blue": (50, 120, 230),
    "accent_green": (0, 200, 130),
    "gold": (255, 180, 0),
    "white": (255, 255, 255),
    "light_gray": (160, 175, 200),
    "warm_white": (240, 238, 235),
    "red_accent": (255, 70, 70),
    "subtle_bg": (18, 25, 48),
}


# ============================================================
# Conversational Content — Human, not AI-ish
# ============================================================
CONTENT_TOPICS = [
    {
        "hook": "Real talk — everyone says diversify but nobody tells you HOW",
        "script": [
            "So here's the thing about diversification in 2026",
            "Global markets are way more connected than they used to be",
            "One geopolitical event and suddenly everything moves together",
            "That's why multi-asset strategies actually matter now",
            "Not just stocks — bonds, commodities, currencies all play a role",
        ],
        "cta": "Follow for daily market breakdowns",
    },
    {
        "hook": "The Fed just made a move and you probably missed what it means",
        "script": [
            "Every time the Fed meets, people panic or celebrate",
            "But here's what actually matters for your portfolio",
            "Bond yields and prices move opposite — when rates go up, bonds drop",
            "Different stock sectors react completely differently to rate changes",
            "The key is knowing which sectors to watch before the decision",
        ],
        "cta": "We break this down daily — link in bio",
    },
    {
        "hook": "Emerging markets are on sale right now — but should you buy?",
        "script": [
            "EM stocks are trading at some of the cheapest valuations in years",
            "Sounds tempting right? But there's a catch",
            "Currency swings can wipe out your gains in weeks",
            "And political risk varies wildly from country to country",
            "The opportunity is real but you need professional navigation",
        ],
        "cta": "Follow for smarter EM analysis",
    },
    {
        "hook": "3 things smart investors check before the market even opens",
        "script": [
            "First — overnight futures. They tell you where things are heading",
            "Second — central bank signals. A single word can move markets",
            "Third — economic data releases. Jobs, CPI, GDP all matter",
            "Most retail investors skip all of this and just buy at the open",
            "That's literally the worst time to make decisions",
        ],
        "cta": "Get the morning briefing — link in bio",
    },
    {
        "hook": "Gold keeps hitting new highs — is it too late to get in?",
        "script": [
            "Gold has been on an absolute tear and everyone's asking the same thing",
            "Central banks are still hoarding it — that tells you something",
            "Real yields are still the main driver behind gold prices",
            "When real rates drop, gold shines. When they rise, gold struggles",
            "Right now? The macro setup still favors gold",
        ],
        "cta": "Follow for weekly commodity deep dives",
    },
    {
        "hook": "Tech earnings season is here and the numbers are wild",
        "script": [
            "Mega-cap tech literally drives the entire index at this point",
            "AI spending? Still booming. Companies are throwing billions at it",
            "Cloud revenue growth hasn't slowed down one bit",
            "But here's the real signal — what they say about NEXT quarter",
            "Forward guidance matters way more than beating earnings",
        ],
        "cta": "Daily earnings breakdowns — follow now",
    },
    {
        "hook": "5 investment mistakes I see people make over and over",
        "script": [
            "Number one — chasing last year's winners. Past returns don't repeat",
            "Two — ignoring fees. Even 1% extra eats your returns over decades",
            "Three — letting emotions drive your trades. Fear and greed are expensive",
            "Four — never rebalancing. Your 60/40 can become 80/20 without you noticing",
            "Five — no plan at all. Investing without a strategy is just gambling",
        ],
        "cta": "We help you avoid all of these — link in bio",
    },
]


# ============================================================
# AI Caption Generation — Conversational & Human
# ============================================================
def generate_tiktok_caption():
    """Generate a TikTok caption using Groq AI — conversational, not robotic."""
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
                    "Write a short TikTok caption for a finance video. Topic: " + topic["hook"] + "\n\n"
                    "Rules:\n"
                    "- Sound like a real person, NOT a corporate account\n"
                    "- Use casual language, like talking to a friend\n"
                    "- Maximum 200 characters\n"
                    "- Include 2-3 relevant hashtags\n"
                    "- No emoji spam (1-2 max)\n"
                    "- No clichés like 'game changer' or 'you won't believe'\n"
                    "- Today is " + day + "\n"
                    "- Do NOT promise returns or give financial advice"
                )
            }],
            max_tokens=80,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("  AI caption generation failed: " + str(e))
        return get_fallback_caption()


def get_fallback_caption():
    """Fallback TikTok captions — casual, human-sounding."""
    captions = [
        "Markets don't wait for you to be ready. Here's what I check every morning before the bell #investing #stocks",
        "The Fed makes a move and everyone panics. Here's what actually matters for your portfolio #finance #investing",
        "Smart money checks 3 things before markets open. Most people skip all of them #trading #investingtips",
    ]
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(captions)
    return captions[idx]


# ============================================================
# Font Helper
# ============================================================
def _get_font(size, bold=False):
    """Get a font, trying system fonts first, falling back to default."""
    font_names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
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


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


# ============================================================
# Frame Rendering — High Quality Slide Designs
# ============================================================

def _create_gradient_bg(w, h, color_top, color_bot):
    """Create a smooth gradient background image."""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        ratio = y / max(h - 1, 1)
        r = int(color_top[0] + (color_bot[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bot[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bot[2] - color_top[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _add_noise_texture(img, intensity=8):
    """Add subtle noise texture to make background less flat."""
    arr = np.array(img).copy()
    noise = np.random.randint(-intensity, intensity + 1, arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _add_subtle_grid(img, color=(30, 45, 80), spacing=120):
    """Add subtle grid lines for a tech/finance feel."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=color, width=1)
    return img


def _draw_brand_tag(draw, y=80):
    """Draw small BroadFSC brand tag at top."""
    tag_font = _get_font(26, bold=True)
    # Small pill-shaped tag
    tag_w = 200
    tag_h = 44
    tag_x = SLIDE_W // 2 - tag_w // 2
    _draw_rounded_rect(draw, (tag_x, y, tag_x + tag_w, y + tag_h),
                       radius=22, fill=BRAND_COLORS["accent_blue"])
    draw.text((SLIDE_W // 2, y + tag_h // 2), "BroadFSC",
              font=tag_font, fill=BRAND_COLORS["white"], anchor="mm")


def _draw_progress_bar(draw, progress, y=1840):
    """Draw a thin progress bar at bottom of slide."""
    bar_h = 6
    bar_w = int(SLIDE_W * progress)
    # Background
    draw.rectangle([(0, y), (SLIDE_W, y + bar_h)], fill=(30, 40, 70))
    # Progress
    draw.rectangle([(0, y), (bar_w, y + bar_h)], fill=BRAND_COLORS["accent_blue"])


def create_hook_slide(topic):
    """Create the opening hook slide — big text, minimal design."""
    img = _create_gradient_bg(SLIDE_W, SLIDE_H,
                              BRAND_COLORS["dark_navy"],
                              BRAND_COLORS["subtle_bg"])
    img = _add_subtle_grid(img)
    img = _add_noise_texture(img, 5)
    draw = ImageDraw.Draw(img)

    # Brand tag
    _draw_brand_tag(draw, y=100)

    # Decorative line above hook
    line_y = SLIDE_H // 2 - 200
    draw.rectangle([(100, line_y), (250, line_y + 4)],
                   fill=BRAND_COLORS["accent_green"])

    # Hook text — large, impactful
    hook_font = _get_font(64, bold=True)
    lines = _wrap_text(topic["hook"], hook_font, SLIDE_W - 180, draw)
    y_start = SLIDE_H // 2 - len(lines) * 50
    for line in lines:
        draw.text((90, y_start), line, font=hook_font,
                  fill=BRAND_COLORS["white"])
        y_start += 88

    # Decorative line below hook
    draw.rectangle([(100, y_start + 40), (400, y_start + 44)],
                   fill=BRAND_COLORS["accent_blue"])

    # Subtle prompt
    prompt_font = _get_font(28)
    draw.text((SLIDE_W // 2, SLIDE_H - 200), "keep watching...",
              font=prompt_font, fill=BRAND_COLORS["light_gray"], anchor="mm")

    return img


def create_script_slide(line, index, total, hook_text):
    """Create a script/content slide — one talking point per slide."""
    # Alternate background tones slightly
    if index % 2 == 0:
        img = _create_gradient_bg(SLIDE_W, SLIDE_H,
                                  BRAND_COLORS["dark_navy"],
                                  BRAND_COLORS["subtle_bg"])
    else:
        img = _create_gradient_bg(SLIDE_W, SLIDE_H,
                                  BRAND_COLORS["subtle_bg"],
                                  BRAND_COLORS["dark_navy"])
    img = _add_subtle_grid(img)
    img = _add_noise_texture(img, 4)
    draw = ImageDraw.Draw(img)

    # Brand tag
    _draw_brand_tag(draw, y=80)

    # Quote mark decoration
    quote_font = _get_font(120, bold=True)
    draw.text((80, 180), "\u201c", font=quote_font,
              fill=(*BRAND_COLORS["accent_blue"], 60))

    # Main text — conversational, like someone talking
    text_font = _get_font(52, bold=True)
    lines = _wrap_text(line, text_font, SLIDE_W - 160, draw)
    y_start = 340
    for line_text in lines:
        draw.text((90, y_start), line_text, font=text_font,
                  fill=BRAND_COLORS["warm_white"])
        y_start += 72

    # Accent line after text
    draw.rectangle([(90, y_start + 30), (350, y_start + 34)],
                   fill=BRAND_COLORS["accent_green"])

    # Subtle context reference
    ref_font = _get_font(22)
    draw.text((90, y_start + 60), hook_text[:55],
              font=ref_font, fill=BRAND_COLORS["light_gray"])

    # Progress bar
    progress = (index + 1) / (total + 1)
    _draw_progress_bar(draw, progress)

    # Slide number
    num_font = _get_font(24)
    draw.text((SLIDE_W - 90, 90), str(index + 1) + "/" + str(total),
              font=num_font, fill=BRAND_COLORS["light_gray"], anchor="mm")

    return img


def create_cta_slide(topic):
    """Create the closing CTA slide — warm, inviting."""
    img = _create_gradient_bg(SLIDE_W, SLIDE_H,
                              BRAND_COLORS["deep_blue"],
                              BRAND_COLORS["dark_navy"])
    img = _add_noise_texture(img, 4)
    draw = ImageDraw.Draw(img)

    # Brand tag
    _draw_brand_tag(draw, y=200)

    # Main CTA text
    cta_font = _get_font(56, bold=True)
    lines = _wrap_text(topic["cta"], cta_font, SLIDE_W - 160, draw)
    y_start = 500
    for line_text in lines:
        draw.text((SLIDE_W // 2, y_start), line_text, font=cta_font,
                  fill=BRAND_COLORS["white"], anchor="mm")
        y_start += 80

    # Divider
    draw.rectangle([(SLIDE_W // 2 - 80, y_start + 40), (SLIDE_W // 2 + 80, y_start + 44)],
                   fill=BRAND_COLORS["accent_green"])

    # Website URL in a pill
    pill_w = 600
    pill_h = 70
    pill_x = SLIDE_W // 2 - pill_w // 2
    pill_y = y_start + 100
    _draw_rounded_rect(draw, (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
                       radius=35, fill=BRAND_COLORS["accent_blue"])
    url_font = _get_font(30, bold=True)
    draw.text((SLIDE_W // 2, pill_y + pill_h // 2), "broadfsc.com/different",
              font=url_font, fill=BRAND_COLORS["white"], anchor="mm")

    # Telegram
    tg_font = _get_font(28)
    draw.text((SLIDE_W // 2, pill_y + pill_h + 80), "t.me/BroadFSC",
              font=tg_font, fill=BRAND_COLORS["accent_green"], anchor="mm")

    # Disclaimer — small, at bottom
    disc_font = _get_font(16)
    draw.text((SLIDE_W // 2, SLIDE_H - 180),
              "Investing involves risk. Past performance does not guarantee future results.",
              font=disc_font, fill=BRAND_COLORS["light_gray"], anchor="mm")
    draw.text((SLIDE_W // 2, SLIDE_H - 150),
              "BroadFSC is a licensed investment advisory firm.",
              font=disc_font, fill=BRAND_COLORS["light_gray"], anchor="mm")

    # Progress bar — full
    _draw_progress_bar(draw, 1.0)

    return img


# ============================================================
# Advanced Video Generation — Ken Burns + Transitions + Subtitles
# ============================================================

def _ken_burns_frame(img, frame_idx, total_frames, zoom_start=1.0, zoom_end=1.08, pan_x=0.0, pan_y=0.02):
    """Apply Ken Burns effect (slow zoom + pan) to a slide image for one frame."""
    progress = frame_idx / max(total_frames - 1, 1)
    # Ease in-out
    progress = progress * progress * (3 - 2 * progress)  # smoothstep
    
    zoom = zoom_start + (zoom_end - zoom_start) * progress
    px = pan_x * progress
    py = pan_y * progress
    
    w, h = img.size
    # Calculate crop region
    new_w = int(w / zoom)
    new_h = int(h / zoom)
    
    # Center + pan offset
    center_x = w // 2 + int(px * w)
    center_y = h // 2 + int(py * h)
    
    left = max(0, center_x - new_w // 2)
    top = max(0, center_y - new_h // 2)
    
    # Ensure crop doesn't exceed image bounds
    if left + new_w > w:
        left = w - new_w
    if top + new_h > h:
        top = h - new_h
    left = max(0, left)
    top = max(0, top)
    
    cropped = img.crop((left, top, left + new_w, top + new_h))
    return cropped.resize((SLIDE_W, SLIDE_H), Image.LANCZOS)


def _crossfade(frame_a, frame_b, alpha):
    """Crossfade between two frames. alpha=0→frame_a, alpha=1→frame_b."""
    arr_a = np.array(frame_a, dtype=np.float32)
    arr_b = np.array(frame_b, dtype=np.float32)
    blended = arr_a * (1 - alpha) + arr_b * alpha
    return np.clip(blended, 0, 255).astype(np.uint8)


def _render_subtitle_frame(base_frame, text, frame_idx, total_frames):
    """Render subtitle text at bottom of frame with fade-in/out."""
    img = Image.fromarray(base_frame)
    draw = ImageDraw.Draw(img)
    
    # Subtitle fade in/out (first/last 10% of frames)
    fade_frames = max(total_frames // 10, 1)
    if frame_idx < fade_frames:
        alpha = frame_idx / fade_frames
    elif frame_idx > total_frames - fade_frames:
        alpha = (total_frames - frame_idx) / fade_frames
    else:
        alpha = 1.0
    
    # Semi-transparent background bar
    bar_y = SLIDE_H - 260
    bar_h = 100
    overlay = Image.new("RGBA", (SLIDE_W, bar_h), (0, 0, 0, int(160 * alpha)))
    img.paste(Image.blend(Image.new("RGB", (SLIDE_W, bar_h), (0, 0, 0)), 
                           Image.new("RGB", (SLIDE_W, bar_h), (*BRAND_COLORS["dark_navy"],)), 0.7),
              (0, bar_y))
    
    # Subtitle text
    sub_font = _get_font(38, bold=True)
    lines = _wrap_text(text, sub_font, SLIDE_W - 120, draw)
    text_y = bar_y + (bar_h - len(lines) * 50) // 2
    
    # Apply alpha via color
    r = int(BRAND_COLORS["white"][0] * alpha)
    g = int(BRAND_COLORS["white"][1] * alpha)
    b = int(BRAND_COLORS["white"][2] * alpha)
    
    for line in lines:
        draw.text((60, text_y), line, font=sub_font, fill=(r, g, b))
        text_y += 50
    
    return np.array(img)


def _generate_tone(freq, duration_ms, sample_rate=44100, volume=0.15):
    """Generate a simple sine wave tone."""
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Gentle fade in/out
        envelope = 1.0
        fade_samples = min(num_samples // 10, 1000)
        if i < fade_samples:
            envelope = i / fade_samples
        elif i > num_samples - fade_samples:
            envelope = (num_samples - i) / fade_samples
        sample = volume * envelope * math.sin(2 * math.pi * freq * t)
        samples.append(int(sample * 32767))
    return samples


def _generate_background_music(duration_sec, sample_rate=44100):
    """Generate simple ambient background music — soft pads."""
    total_samples = int(sample_rate * duration_sec)
    music = [0.0] * total_samples
    
    # Chord progression (C major → Am → F → G) — very gentle
    chords = [
        [261.63, 329.63, 392.00],  # C major
        [220.00, 261.63, 329.63],  # Am
        [174.61, 220.00, 261.63],  # F
        [196.00, 246.94, 293.66],  # G
    ]
    
    chord_duration = total_samples // len(chords)
    
    for chord_idx, chord in enumerate(chords):
        start = chord_idx * chord_duration
        end = min(start + chord_duration, total_samples)
        
        for i in range(start, end):
            t = i / sample_rate
            # Envelope for chord transitions
            local_t = (i - start) / chord_duration
            envelope = math.sin(math.pi * local_t)  # smooth rise/fall
            
            sample = 0
            for freq in chord:
                # Soft pad sound — combine sine with slight detuning
                sample += math.sin(2 * math.pi * freq * t) * 0.08
                sample += math.sin(2 * math.pi * freq * 1.002 * t) * 0.04  # slight chorus
                sample += math.sin(2 * math.pi * freq * 0.998 * t) * 0.04  # detune
            
            music[i] += sample * envelope * 0.3
    
    # Global fade in/out
    fade_samples = min(sample_rate, total_samples // 5)
    for i in range(fade_samples):
        factor = i / fade_samples
        music[i] *= factor
        music[total_samples - 1 - i] *= factor
    
    # Normalize
    max_val = max(abs(v) for v in music) or 1
    music = [int(v / max_val * 12000) for v in music]  # comfortable volume
    
    return music


def _save_wav(samples, filepath, sample_rate=44100):
    """Save audio samples as a WAV file."""
    import wave
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = struct.pack('<' + 'h' * len(samples), *samples)
        wf.writeframes(data)


def _merge_audio_video(video_path, audio_path, output_path):
    """Merge audio WAV with video MP4 using imageio ffmpeg."""
    try:
        # Use imageio-ffmpeg to mux audio + video
        import subprocess
        # Find ffmpeg binary
        ffmpeg_exe = None
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            print("  Found ffmpeg via imageio_ffmpeg: " + str(ffmpeg_exe))
        except Exception as e:
            print("  imageio_ffmpeg import failed: " + str(e))
        if not ffmpeg_exe:
            try:
                ffmpeg_exe = iio.get_ffmpeg_exe()
                print("  Found ffmpeg via imageio: " + str(ffmpeg_exe))
            except Exception as e:
                print("  imageio get_ffmpeg_exe failed: " + str(e))
        if not ffmpeg_exe:
            print("  No ffmpeg found, skipping audio merge")
            return False
        
        print("  Merging audio + video with ffmpeg...")
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
        if result.returncode == 0 and os.path.exists(output_path):
            return True
        else:
            print("  Audio merge stderr: " + result.stderr.decode('utf-8', errors='replace')[:200])
            return False
    except Exception as e:
        print("  Audio merge failed: " + str(e))
        return False


def create_professional_video(topic, output_path):
    """
    Create a professional TikTok video with:
    - Ken Burns animation (slow zoom/pan on each slide)
    - Crossfade transitions between slides
    - Subtitle overlay on each slide
    - Background music
    - Hook → Script → CTA structure
    """
    if not HAS_IMAGEIO or not HAS_PILLOW:
        print("  Pillow + imageio required for professional video")
        return False

    try:
        # 1. Generate all slide images
        print("  Creating slide images...")
        slides = []
        
        # Hook slide
        hook_img = create_hook_slide(topic)
        slides.append(("hook", topic["hook"], hook_img))
        
        # Script slides
        total_script = len(topic["script"])
        for i, line in enumerate(topic["script"]):
            img = create_script_slide(line, i, total_script, topic["hook"])
            slides.append(("script_" + str(i), line, img))
        
        # CTA slide
        cta_img = create_cta_slide(topic)
        slides.append(("cta", topic["cta"], cta_img))
        
        print("  Created " + str(len(slides)) + " slides")
        
        # 2. Generate animated frames
        frames_per_slide = FPS * SECONDS_PER_SLIDE  # 30fps * 4s = 120 frames
        all_frames = []
        slide_subtitles = []  # track which subtitle belongs to which frame range
        
        print("  Rendering animation frames...")
        for slide_idx, (name, subtitle, img) in enumerate(slides):
            # Randomize Ken Burns parameters slightly per slide
            zoom_start = 1.0
            zoom_end = 1.0 + random.uniform(0.04, 0.10)
            pan_x = random.uniform(-0.02, 0.02)
            pan_y = random.uniform(0.0, 0.03)
            
            slide_frames = []
            for f in range(frames_per_slide):
                kb_frame = _ken_burns_frame(img, f, frames_per_slide, 
                                            zoom_start, zoom_end, pan_x, pan_y)
                slide_frames.append(np.array(kb_frame))
            
            # Add subtitles to frames
            for f in range(frames_per_slide):
                slide_frames[f] = _render_subtitle_frame(slide_frames[f], subtitle, f, frames_per_slide)
            
            # Crossfade transition with previous slide
            if all_frames and slide_idx > 0:
                for t in range(TRANSITION_FRAMES):
                    alpha = t / TRANSITION_FRAMES
                    # Blend last frames of previous slide with first frames of current
                    prev_idx = len(all_frames) - TRANSITION_FRAMES + t
                    if prev_idx >= 0 and prev_idx < len(all_frames):
                        blended = _crossfade(all_frames[prev_idx], slide_frames[t], alpha)
                        all_frames[prev_idx] = blended
            
            all_frames.extend(slide_frames)
            slide_subtitles.append((len(all_frames) - frames_per_slide, len(all_frames), subtitle))
        
        total_frames = len(all_frames)
        total_duration = total_frames // FPS
        print("  Total frames: " + str(total_frames) + " (" + str(total_duration) + "s)")
        
        # 3. Write video (no audio first)
        temp_video = output_path + ".noaudio.mp4"
        print("  Encoding video...")
        writer = iio.get_writer(temp_video, fps=FPS, codec='libx264',
                                output_params=['-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '23'])
        for frame in all_frames:
            writer.append_data(frame)
        writer.close()
        
        # 4. Generate and merge background music
        print("  Generating background music...")
        music_samples = _generate_background_music(total_duration)
        temp_audio = output_path + ".temp.wav"
        _save_wav(music_samples, temp_audio)
        
        merged = _merge_audio_video(temp_video, temp_audio, output_path)
        
        if merged:
            # Clean up temp files
            try:
                os.remove(temp_video)
                os.remove(temp_audio)
            except Exception:
                pass
            file_size = os.path.getsize(output_path)
            print("  Video created: " + output_path + " (" + str(file_size) + " bytes, " +
                  str(total_frames) + " frames @ " + str(FPS) + "fps = " + str(total_duration) + "s)")
            return True
        else:
            # Use video without audio as fallback
            try:
                os.rename(temp_video, output_path)
                try:
                    os.remove(temp_audio)
                except Exception:
                    pass
            except Exception:
                pass
            file_size = os.path.getsize(output_path)
            print("  Video created (no audio): " + output_path + " (" + str(file_size) + " bytes)")
            return True
            
    except Exception as e:
        print("  Professional video creation failed: " + str(e))
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# Legacy: Simple slideshow video (fallback)
# ============================================================
def images_to_video(image_paths, output_path, fps=30, seconds_per_slide=3):
    """Simple slideshow video — fallback if professional mode fails."""
    if not HAS_IMAGEIO:
        print("  imageio not available, cannot create video")
        return False

    try:
        frames = []
        frames_per_slide = fps * seconds_per_slide
        
        for path in image_paths:
            img = Image.open(path).convert("RGB")
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


def post_tiktok_video(caption, video_url):
    """Post a TikTok video via Postproxy API (URL mode)."""
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
        "post": {"body": caption},
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
            post_id = r.json().get("id", "unknown")
            print("  TikTok: Video posted! ID: " + str(post_id))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:400])
            return False
    except Exception as e:
        print("  TikTok: FAIL - " + str(e))
        return False


def post_tiktok_image(caption, image_paths):
    """Post a TikTok image carousel via Postproxy API (legacy, likely fails)."""
    if not POSTPROXY_API_KEY or not image_paths:
        return False

    api_url = POSTPROXY_BASE_URL + "/posts"
    headers = {"Authorization": "Bearer " + POSTPROXY_API_KEY}
    data = {
        "post[body]": caption,
        "profiles[]": "tiktok",
        "platforms[tiktok][format]": "image",
        "platforms[tiktok][privacy_status]": "PUBLIC_TO_EVERYONE",
        "platforms[tiktok][auto_add_music]": "true",
    }

    open_files = []
    files = []
    try:
        for path in image_paths:
            f = open(path, "rb")
            open_files.append(f)
            files.append(("media[]", (os.path.basename(path), f, "image/png")))
        r = requests.post(api_url, headers=headers, data=data, files=files, timeout=60)
        if r.status_code in [200, 201]:
            print("  TikTok: Image posted! ID: " + r.json().get("id", "unknown"))
            return True
        else:
            print("  TikTok: FAIL HTTP " + str(r.status_code) + " - " + r.text[:300])
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
    print("BroadFSC TikTok Auto-Poster v2")
    print("Professional Video Edition")
    print("=" * 50)

    now = datetime.datetime.utcnow()
    print("Current UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print("POSTPROXY_API_KEY: " + ("SET" if POSTPROXY_API_KEY else "NOT SET"))
    print("GROQ_API_KEY: " + ("SET" if GROQ_API_KEY else "NOT SET (using fallback)"))
    print("Mode: " + TIKTOK_MODE.upper())
    print("Pillow: " + ("YES" if HAS_PILLOW else "NO"))
    print("imageio: " + ("YES" if HAS_IMAGEIO else "NO"))
    print()

    # Step 1: Pick today's topic
    day_of_year = now.timetuple().tm_yday
    topic_idx = day_of_year % len(CONTENT_TOPICS)
    topic = CONTENT_TOPICS[topic_idx]
    print("--- Step 1: Today's Topic ---")
    print("  Hook: " + topic["hook"])
    print("  Script lines: " + str(len(topic["script"])))
    print()

    # Step 2: Generate caption
    print("--- Step 2: Generate Caption ---")
    caption = generate_tiktok_caption()
    print("  Caption: " + caption[:100] + ("..." if len(caption) > 100 else ""))
    print()

    # Step 3: Create and post video
    success = False

    if TIKTOK_MODE == "video":
        print("--- Step 3: Direct Video Mode ---")
        video_url = TIKTOK_VIDEO_URL
        if video_url:
            success = post_tiktok_video(caption, video_url)
        else:
            video_dir = os.path.dirname(os.path.abspath(__file__))
            video_path = os.path.join(video_dir, "tiktok_video.mp4")
            if os.path.exists(video_path):
                success = post_tiktok_video_file(caption, video_path)
            else:
                print("  No video URL or file found, falling back to slideshow...")

    if TIKTOK_MODE != "video" or not success:
        print("--- Step 3: Professional Video Mode ---")
        video_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(video_dir, "tiktok_slideshow.mp4")

        if HAS_PILLOW and HAS_IMAGEIO:
            # Professional video with animations, subtitles, music
            if create_professional_video(topic, video_path):
                success = post_tiktok_video_file(caption, video_path)
                try:
                    os.remove(video_path)
                except Exception:
                    pass
            else:
                print("  Professional video failed, trying simple slideshow...")
                # Fallback to simple slideshow
                success = _fallback_simple_slideshow(caption, video_dir)
        else:
            print("  Pillow/imageio not available for professional mode")
            success = _fallback_simple_slideshow(caption, video_dir)

    print()

    # Step 4: Notify
    if success:
        notify_telegram("✅ TikTok v2 post published: " + caption[:80])
        print("SUCCESS: TikTok post published!")
    else:
        notify_telegram("❌ TikTok v2 post FAILED")
        print("FAILED: TikTok post could not be published.")

    print()
    print("=" * 50)
    print("TikTok posting complete.")


def _fallback_simple_slideshow(caption, video_dir):
    """Fallback: simple image slideshow without animations."""
    print("  Using simple slideshow fallback...")
    now = datetime.datetime.utcnow()
    day_of_year = now.timetuple().tm_yday
    topic_idx = day_of_year % len(CONTENT_TOPICS)
    topic = CONTENT_TOPICS[topic_idx]
    
    # Generate simple slides
    images = []
    hook_img = create_hook_slide(topic)
    buf = io.BytesIO()
    hook_img.save(buf, format="PNG")
    images.append(("hook.png", buf.getvalue()))
    
    for i, line in enumerate(topic["script"]):
        img = create_script_slide(line, i, len(topic["script"]), topic["hook"])
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        images.append(("script_" + str(i) + ".png", buf.getvalue()))
    
    cta_img = create_cta_slide(topic)
    buf = io.BytesIO()
    cta_img.save(buf, format="PNG")
    images.append(("cta.png", buf.getvalue()))
    
    # Save to temp files
    paths = []
    for filename, data in images:
        path = os.path.join(video_dir, "temp_" + filename)
        with open(path, "wb") as f:
            f.write(data)
        paths.append(path)
    
    success = False
    if HAS_IMAGEIO and paths:
        video_path = os.path.join(video_dir, "tiktok_slideshow.mp4")
        if images_to_video(paths, video_path, fps=30, seconds_per_slide=3):
            success = post_tiktok_video_file(caption, video_path)
            try:
                os.remove(video_path)
            except Exception:
                pass
    
    # Clean up
    for path in paths:
        try:
            os.remove(path)
        except Exception:
            pass
    
    return success


if __name__ == "__main__":
    main()
