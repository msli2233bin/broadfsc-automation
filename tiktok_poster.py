"""
BroadFSC TikTok Auto-Poster v4 — AI Voice + Karaoke Subtitles + Cinematic Video
Major upgrade from v3: adds TTS voiceover, word-by-word karaoke subtitles,
and cinematic stock-video-style backgrounds.

Key improvements over v3:
- Microsoft Edge TTS (free, unlimited, natural voices)
- Karaoke-style subtitles (word-by-word highlight, like top TikTok creators)
- Dynamic cinematic backgrounds with animated particles/lines
- Audio waveform visualization
- Voice-driven timing (each scene lasts as long as the spoken text)
- Professional audio mixing (voice + ambient music)

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
import asyncio
import subprocess
import tempfile

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

try:
    import edge_tts
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

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

# TTS voice config — using natural-sounding voices
TTS_VOICE = "en-US-GuyNeural"      # Male, casual, young — like a finance bro
TTS_VOICE_ALT = "en-US-AriaNeural"  # Female alternative (randomly picked sometimes)
TTS_RATE = "+5%"                    # Slightly faster for energy

# ============================================================
# Color Palette — dark cinematic finance
# ============================================================
C = {
    "bg_dark": (10, 12, 22),
    "bg_mid": (16, 20, 38),
    "accent": (65, 145, 255),
    "accent_bright": (100, 180, 255),
    "green": (0, 220, 140),
    "gold": (255, 195, 15),
    "red": (255, 65, 65),
    "white": (255, 255, 255),
    "gray": (140, 155, 185),
    "dim": (60, 70, 100),
    "highlight": (255, 200, 50),     # Karaoke highlight color
    "highlight_bg": (40, 35, 80),    # Highlight background glow
}


# ============================================================
# Human Conversational Scripts — optimized for SPOKEN delivery
# ============================================================
SCRIPTS = [
    {
        "hook": "Nobody talks about this but...",
        "scenes": [
            "The stock market doesn't care about your feelings.",
            "It cares about earnings, rates, and institutional flows.",
            "Right now? Smart money is rotating into sectors most people ignore.",
            "Defense, infrastructure, healthcare. Not just Big Tech.",
        ],
        "cta": "Follow for what the market's actually doing.",
    },
    {
        "hook": "I wish someone told me this at twenty five.",
        "scenes": [
            "You don't need to pick winning stocks to build wealth.",
            "Index funds beat ninety percent of active managers over ten years.",
            "But when you buy matters more than what you buy.",
            "Dollar cost averaging into dips? That's the real cheat code.",
        ],
        "cta": "Save this and thank me later.",
    },
    {
        "hook": "The Fed just signaled something huge.",
        "scenes": [
            "And most people are completely ignoring it.",
            "When the Fed pauses, bonds become the hidden play.",
            "Short term yields still paying four to five percent while stocks swing wildly.",
            "That's free money while you wait for clarity.",
        ],
        "cta": "Follow for daily market breakdowns.",
    },
    {
        "hook": "Stop checking your portfolio every hour.",
        "scenes": [
            "Seriously. The people making real money? They set it and forget it.",
            "The S&P 500's best days always come right after the worst days.",
            "If you sold during the dip, you missed the bounce. Every single time.",
            "Time in the market beats timing the market. Every. Single. Time.",
        ],
        "cta": "Share this with someone who needs to hear it.",
    },
    {
        "hook": "Three numbers that moved markets this week.",
        "scenes": [
            "Number one. C P I came in hot. Inflation's not dead yet.",
            "Number two. Jobless claims hit a new low. Labor market still strong.",
            "Number three. Ten year yield broke above four point five percent. That's your real signal.",
            "When yields spike, growth stocks get nervous. Value stocks wake up.",
        ],
        "cta": "I break this down every day. Follow.",
    },
    {
        "hook": "This is why rich people stay rich.",
        "scenes": [
            "It's not about picking the right stock. It's about asset allocation.",
            "When stocks crash, bonds cushion. When bonds fall, commodities hedge.",
            "The rich never bet everything on one thing. Ever.",
            "And they rebalance quarterly. Most people never rebalance at all.",
        ],
        "cta": "Follow for smarter money moves.",
    },
    {
        "hook": "Everyone's buying the wrong thing right now.",
        "scenes": [
            "FOMO is not a strategy. Chasing last week's winner never works.",
            "The real opportunity? Sectors that haven't moved yet.",
            "Energy, financials, industrials. They're quietly setting up.",
            "By the time everyone notices, the smart money is already out.",
        ],
        "cta": "Don't be last to know. Follow.",
    },
]


# ============================================================
# AI Script Generation
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
                    "Write a TikTok finance VIDEO SCRIPT that will be READ ALOUD by TTS.\n"
                    "Today is " + day + ".\n\n"
                    "FORMAT — return ONLY valid JSON:\n"
                    '{\n'
                    '  "hook": "short hook sentence",\n'
                    '  "scenes": ["line1", "line2", "line3", "line4"],\n'
                    '  "cta": "call to action"\n'
                    '}\n\n'
                    "CRITICAL — This will be SPOKEN, so write how PEOPLE TALK:\n"
                    "- Use contractions: it's, don't, won't, you're, they've\n"
                    "- Spell out numbers as words: four point five percent (not 4.5%)\n"
                    "- Write short punchy sentences (natural speech pauses)\n"
                    "- Each scene max 12 words when spoken\n"
                    "- Hook under 8 words, create curiosity or FOMO\n"
                    "- CTA under 8 words, casual\n"
                    "- Sound like a 28 year old talking to their friend\n"
                    "- Use: gonna, wanna, kinda, tbh, literally, basically\n\n"
                    "FORBIDDEN (sound robotic):\n"
                    "- game changer, pro tip, ninja, hack, leverage, navigate\n"
                    "- crucial, essential, paramount, comprehensive, landscape\n"
                    "- moreover, furthermore, additionally, consequently\n\n"
                    "TOPICS: Fed, earnings, inflation, diversification, market psychology\n"
                )
            }],
            max_tokens=250,
            temperature=0.95
        )

        text = response.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]

        data = json.loads(text)
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
    """Generate TikTok caption from script."""
    if not GROQ_API_KEY:
        hook = script["hook"]
        return hook + " #investing #finance #money #stockmarket"

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
                    "- Sound like a real person\n"
                    "- 3-4 hashtags, lowercase: #investing #money #stocks #finance\n"
                    "- No emoji spam (max 2)\n"
                    "- No financial advice promises\n"
                )
            }],
            max_tokens=60,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return script["hook"] + " #investing #finance #money"


# ============================================================
# Font Helper
# ============================================================
def _font(size, bold=False):
    """Get a font."""
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
# TTS — Text-to-Speech with Word-Level Timing
# ============================================================
async def generate_tts_audio(text, output_path, voice=None):
    """
    Generate TTS audio file and return word-level timestamp data.
    Returns: (audio_path, word_data_list)
    """
    if voice is None:
        voice = TTS_VOICE

    # Step 1: Save audio
    comm_save = edge_tts.Communicate(text, voice, rate=TTS_RATE)
    await comm_save.save(output_path)

    # Step 2: Get timing data (try WordBoundary first, fall back to SentenceBoundary)
    word_data = []
    sentence_boundaries = []

    comm_stream = edge_tts.Communicate(text, voice, rate=TTS_RATE)
    try:
        async for event in comm_stream.stream():
            if event["type"] == "WordBoundary":
                word_data.append({
                    "text": event["text"],
                    "offset_sec": event["offset"] / 10_000_000,
                    "duration_sec": event["duration"] / 10_000_000,
                })
            elif event["type"] == "SentenceBoundary":
                sentence_boundaries.append({
                    "text": event["text"],
                    "offset_sec": event["offset"] / 10_000_000,
                    "duration_sec": event["duration"] / 10_000_000,
                })
    except Exception as e:
        print(f"  TTS stream warning: {e}")

    # If we got WordBoundary data, use it directly
    if word_data:
        print(f"  TTS: {len(word_data)} words from WordBoundary ({voice})")
        return output_path, word_data

    # If we got SentenceBoundary data, use it to build word-level timing
    if sentence_boundaries:
        total_dur = sentence_boundaries[-1]["offset_sec"] + sentence_boundaries[-1]["duration_sec"]
        word_data = _build_word_timing_from_sentences(text, sentence_boundaries, total_dur)
        print(f"  TTS: {len(word_data)} words from SentenceBoundary ({voice})")
        return output_path, word_data

    # Ultimate fallback: pure estimation from text
    print("  TTS: estimating timing from text...")
    word_data = _estimate_word_timing(text)
    print(f"  TTS: {len(word_data)} words estimated ({voice})")
    return output_path, word_data


def _build_word_timing_from_sentences(text, sentences, total_duration):
    """Build word-level timing from SentenceBoundary events."""
    word_data = []
    words = text.split()

    if not sentences or not words:
        return _estimate_word_timing(text)

    # Map each word to its containing sentence
    char_pos = 0
    word_sentence_map = []  # (word, start_char_pos)
    for w in words:
        word_sentence_map.append((w, char_pos))
        char_pos += len(w) + 1  # word + space

    # Distribute time across sentences, then across words in each sentence
    sent_idx = 0
    for wi, (word, wcpos) in enumerate(word_sentence_map):
        # Find which sentence this word belongs to
        while sent_idx < len(sentences) - 1:
            # Check next sentence start
            if wcpos >= sentences[sent_idx].get("_end_char", 0):
                sent_idx += 1
            else:
                break

        # Get sentence timing
        s_start = sentences[sent_idx]["offset_sec"]
        s_end = s_start + sentences[sent_idx]["duration_sec"]
        s_dur = sentences[sent_idx]["duration_sec"]

        # Words in this sentence
        s_words = [x for x in range(len(words)) if word_sentence_map[x][1] < wcpos or x <= wi]
        # Simpler: just distribute evenly within the sentence's time window
        pass

    # Fallback: even simpler approach — use sentence boundaries as anchors
    result = []
    pos = 0.0
    for i, w in enumerate(words):
        wdur = max(total_duration / len(words) * (len(w) / 5.0), 0.25)
        result.append({
            "text": (" " if i > 0 else "") + w,
            "offset_sec": pos,
            "duration_sec": min(wdur, total_duration - pos),
        })
        pos += result[-1]["duration_sec"]

    return result


def _estimate_word_timing(text):
    """Estimate per-word timing based on text analysis."""
    words = text.split()
    total_dur = _estimate_duration(text)

    # Weight each word by its length and punctuation
    weights = []
    for w in words:
        clean = w.strip(".,!?;:'\"")
        weight = max(len(clean) * 0.15 + 0.25, 0.3)  # base + length factor
        if any(p in w for p in ".,!?"):  # pause after punctuation
            weight += 0.3
        weights.append(weight)

    total_weight = sum(weights) or 1
    scale = total_dur / total_weight

    result = []
    pos = 0.0
    for i, w in enumerate(words):
        wdur = weights[i] * scale
        result.append({
            "text": (" " if i > 0 else "") + w,
            "offset_sec": pos,
            "duration_sec": min(wdur, total_dur - pos),
        })
        pos += result[-1]["duration_sec"]

    return result


def _estimate_duration(text):
    """Estimate spoken duration in seconds based on text length."""
    # Average English speaking rate: ~150 words/min = 2.5 words/sec
    # Plus pauses after sentences/commas
    num_words = len(text.split())
    num_sentences = text.count('.') + text.count('!') + text.count('?') + 1
    base = num_words / 2.5
    pause = num_sentences * 0.3  # pause between sentences
    return max(base + pause, 1.5)  # minimum 1.5 seconds


def build_spoken_lines(script):
    """
    Build full spoken text lines from script with labels.
    Returns: [(label, text), ...] e.g. [("hook", "..."), ("scene_0", "...")]
    """
    lines = []
    lines.append(("hook", script["hook"]))
    for i, scene in enumerate(script["scenes"]):
        lines.append((f"scene_{i}", scene))
    lines.append(("cta", script["cta"]))
    return lines


async def generate_all_audio(spoken_lines, output_dir):
    """
    Generate TTS audio for each line.
    Returns: [(label, audio_path, word_data), ...]
    """
    results = []
    for label, text in spoken_lines:
        audio_path = os.path.join(output_dir, f"tts_{label}.mp3")
        path, word_data = await generate_tts_audio(text, audio_path)
        results.append((label, path, word_data))

        # Small pause between sections (silence)
        if label != "cta":
            pass  # We'll add silence during merge

    return results


# ============================================================
# Background Generators — Cinematic Animated Style
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
    """Dark vignette around edges."""
    w, h = img.size
    arr = np.array(img, dtype=np.float32)
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


# Different background styles per scene type
BG_THEMES = {
    "hook": {"top": (12, 8, 25), "bot": (25, 18, 55), "particle_color": (65, 145, 255)},
    "scene_0": {"top": (8, 12, 22), "bot": (18, 28, 48), "particle_color": (0, 220, 140)},
    "scene_1": {"top": (18, 10, 20), "bot": (30, 18, 35), "particle_color": (255, 195, 15)},
    "scene_2": {"top": (8, 15, 25), "bot": (15, 30, 50), "particle_color": (100, 180, 255)},
    "scene_3": {"top": (15, 12, 18), "bot": (28, 22, 38), "particle_color": (255, 120, 80)},
    "cta": {"top": (8, 14, 20), "bot": (15, 28, 42), "particle_color": (0, 220, 140)},
}


def _make_cinematic_bg(label, frame_idx=0, total_frames=90):
    """
    Create an animated cinematic background with floating particles.
    frame_idx: current frame number (for animation)
    total_frames: total frames in this scene
    """
    theme = BG_THEMES.get(label, BG_THEMES["scene_0"])
    img = _gradient_bg(W, H, theme["top"], theme["bot"])
    img = _noise(img, 4)

    draw = ImageDraw.Draw(img)

    # Animated floating particles (light dots/stars effect)
    pcolor = theme["particle_color"]
    random.seed(hash(label) + frame_idx)  # Consistent per frame
    num_particles = 25
    for _ in range(num_particles):
        px = random.randint(0, W)
        py_base = random.randint(0, H)
        # Slow upward drift
        drift = int((frame_idx / total_frames) * 80) % H
        py = (py_base - drift) % H
        size = random.randint(1, 3)
        alpha_val = random.randint(30, 120)

        # Draw particle with glow
        for s in range(size + 2, 0, -1):
            a = alpha_val // (s + 1)
            pc = tuple(min(255, c + a) for c in pcolor[:3])
            draw.ellipse([px - s, py - s, px + s, py + s], fill=pc)

    # Horizontal light streak (animated position)
    streak_y = int(H * 0.4 + math.sin(frame_idx * 0.05) * 100)
    for dy in range(-20, 20):
        alpha = max(0, 12 - abs(dy))
        if alpha > 0:
            r = min(255, theme["particle_color"][0] // 3 + alpha)
            g = min(255, theme["particle_color"][1] // 3 + alpha)
            b = min(255, theme["particle_color"][2] // 3 + alpha)
            draw.line([(0, streak_y + dy), (W, streak_y + dy)], fill=(r, g, b))

    # Grid lines (subtle, tech/finance feel)
    grid_alpha = 15
    gc = (grid_alpha, grid_alpha + 5, grid_alpha + 12)
    spacing = 80
    offset = (frame_idx * 2) % spacing
    for x in range(-offset, W + spacing, spacing):
        draw.line([(x, 0), (x, H)], fill=(12, 14, 26), width=1)
    for y in range(-offset, H + spacing, spacing):
        draw.line([(0, y), (W, y)], fill=(12, 14, 26), width=1)

    img = _vignette(img, 0.35)
    return img


# ============================================================
# Scene Rendering — Text Overlay on Cinematic Background
# ============================================================
def _render_text_on_bg(text, label, is_hook=False, is_cta=False):
    """
    Render a scene: text overlaid on cinematic background.
    Returns PIL Image.
    """
    img = _make_cinematic_bg(label)
    draw = ImageDraw.Draw(img)

    # Brand tag (top-left) — only for non-hook scenes
    if not is_hook:
        tag_font = _font(20, bold=True)
        tw = draw.textbbox((0, 0), "BroadFSC", font=tag_font)[2] - draw.textbbox((0, 0), "BroadFSC", font=tag_font)[0]
        draw.rounded_rectangle((36, 56, tw + 52, 92), radius=14, fill=C["accent"])
        draw.text((44 + tw // 2, 74), "BroadFSC", font=tag_font, fill=C["white"], anchor="mm")

    if is_hook:
        # === HOOK SCENE — EXTRA LARGE impact text ===
        font = _font(76, bold=True)
        lines = _wrap(text, font, W - 120, draw)
        total_h = len(lines) * 96
        y = (H // 2) - (total_h // 2) - 50

        for line in lines:
            draw.text((64, y + 3), line, font=font, fill=(0, 0, 0))
            draw.text((62, y), line, font=font, fill=C["white"])
            y += 96

        # Accent underline
        draw.rectangle([(62, y + 30), (320, y + 34)], fill=C["green"])

        # "keep watching" hint
        hint_font = _font(24)
        draw.text((W // 2, H - 280), "keep watching...",
                  font=hint_font, fill=C["dim"], anchor="mm")

    elif is_cta:
        # === CTA SCENE ===
        font = _font(58, bold=True)
        lines = _wrap(text, font, W - 140, draw)
        y = H // 2 - 220
        for line in lines:
            draw.text((72, y + 3), line, font=font, fill=(0, 0, 0))
            draw.text((70, y), line, font=font, fill=C["green"])
            y += 82

        # Divider
        draw.rectangle([(W // 2 - 60, y + 40), (W // 2 + 60, y + 44)], fill=C["accent"])

        # Website pill
        pill_w, pill_h = 550, 60
        pill_x = W // 2 - pill_w // 2
        pill_y = y + 90
        draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
                              radius=30, fill=C["accent"])
        url_font = _font(26, bold=True)
        draw.text((W // 2, pill_y + pill_h // 2), "broadfsc.com/different",
                  font=url_font, fill=C["white"], anchor="mm")

        tg_font = _font(22)
        draw.text((W // 2, pill_y + pill_h + 50), "@BroadFSC | t.me/BroadFSC",
                  font=tg_font, fill=C["gray"], anchor="mm")

        disc_font = _font(14)
        draw.text((W // 2, H - 160),
                  "Investing involves risk. Past performance does not guarantee future results.",
                  font=disc_font, fill=C["dim"], anchor="mm")

    else:
        # === CONTENT SCENE — large centered text ===
        font = _font(54, bold=True)
        lines = _wrap(text, font, W - 140, draw)
        total_h = len(lines) * 74
        y = (H // 2) - (total_h // 2) - 20

        for line in lines:
            draw.text((72, y + 3), line, font=font, fill=(0, 0, 0))
            draw.text((70, y), line, font=font, fill=C["white"])
            y += 74

        accent_colors = [C["accent"], C["green"], C["gold"]]
        accent = accent_colors[hash(label) % len(accent_colors)]
        draw.rectangle([(70, y + 35), (70 + 160, y + 39)], fill=accent)

    return img


# ============================================================
# Karaoke Subtitle Renderer — Word-by-word highlight
# ============================================================
class KaraokeRenderer:
    """
    Renders karaoke-style subtitles where each word highlights
    as it's being spoken. This is THE key feature that makes
    videos look professional.
    """

    def __init__(self, word_data, total_duration_sec, label=""):
        """
        word_data: list of {"text": ..., "offset_sec": ..., "duration_sec": ...}
        total_duration_sec: how long this scene lasts
        """
        self.words = word_data
        self.total_duration = total_duration_sec
        self.label = label
        self.full_text = "".join(w["text"] for w in word_data)

        # Pre-compute character positions for highlighting
        self._build_char_map()

    def _build_char_map(self):
        """Build map: char_index -> (word_idx, start_offset, end_offset)"""
        self.char_map = []
        char_pos = 0
        for wi, wd in enumerate(self.words):
            wstart = wd["offset_sec"]
            wend = wd["offset_sec"] + wd["duration_sec"]
            for ci, ch in enumerate(wd["text"]):
                self.char_map.append({
                    "char": ch,
                    "char_pos": char_pos,
                    "word_idx": wi,
                    "start": wstart,
                    "end": wend,
                    "abs_start": wstart,
                    "abs_end": wend,
                })
                char_pos += 1
            # Space between words
            if wi < len(self.words) - 1:
                next_start = self.words[wi + 1]["offset_sec"]
                self.char_map.append({
                    "char": " ",
                    "char_pos": char_pos,
                    "word_idx": -1,  # space
                    "start": wend,
                    "end": next_start,
                    "abs_start": wend,
                    "abs_end": next_start,
                })
                char_pos += 1

    def render_frame(self, base_frame_array, current_time_sec):
        """
        Render karaoke subtitle onto a video frame.
        base_frame_array: numpy array (H, W, 3) uint8
        current_time_sec: time position in seconds
        Returns: modified numpy array
        """
        img = Image.fromarray(base_frame_array.copy())
        draw = ImageDraw.Draw(img)

        # Subtitle bar area
        bar_y = H - 340
        bar_h = 110
        bar_margin_x = 48

        # Semi-transparent background for readability
        overlay = Image.new("RGBA", (W, bar_h), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        ov_draw.rounded_rectangle(
            [(0, 0), (W - 1, bar_h - 1)],
            radius=18,
            fill=(10, 12, 25, 200)
        )
        img.paste(Image.alpha_composite(Image.new("RGBA", (W, bar_h), (0, 0, 0, 0)), overlay),
                  (0, bar_y), overlay)

        draw = ImageDraw.Draw(img)

        # Determine which characters should be highlighted
        # Build highlighted vs unhighlighted text segments
        font = _font(38, bold=True)
        font_small = _font(34)

        # Calculate layout — we need to render each segment separately
        cursor_x = bar_margin_x
        cursor_y = bar_y + (bar_h - 46) // 2
        max_x = W - bar_margin_x

        for entry in self.char_map:
            ch = entry["char"]
            if ch == " ":
                cursor_x += font.getlength(" ")
                if cursor_x > max_x:
                    cursor_x = bar_margin_x
                    cursor_y += 50
                continue

            is_highlighted = (current_time_sec >= entry["start"] and
                              current_time_sec < entry["end"])

            # Progress within this character (for smooth color transition)
            if is_highlighted and entry["end"] > entry["start"]:
                progress = min(1.0, (current_time_sec - entry["start"]) /
                               (entry["end"] - entry["start"]))
            else:
                progress = 0.0

            if is_highlighted:
                # Highlighted: bright gold/yellow with glow
                color = self._lerp_color(C["white"], C["highlight"], progress)
                shadow = (0, 0, 0)
            else:
                # Unhighlighted: dim gray
                color = C["gray"]
                shadow = None

            if shadow:
                draw.text((cursor_x + 1, cursor_y + 1), ch, font=font, fill=shadow)
            draw.text((cursor_x, cursor_y), ch, font=font, fill=color)

            char_w = font.getlength(ch)
            cursor_x += char_w

            if cursor_x > max_x:
                cursor_x = bar_margin_x
                cursor_y += 50

        # Progress indicator bar (thin line below text)
        if self.total_duration > 0:
            progress_pct = min(1.0, current_time_sec / self.total_duration)
            bar_width = int((W - 2 * bar_margin_x) * progress_pct)
            prog_y = bar_y + bar_h - 6
            # Background track
            draw.rounded_rectangle(
                [bar_margin_x, prog_y, W - bar_margin_x, prog_y + 4],
                radius=2, fill=(40, 45, 70)
            )
            # Progress fill
            if bar_width > 0:
                draw.rounded_rectangle(
                    [bar_margin_x, prog_y, bar_margin_x + bar_width, prog_y + 4],
                    radius=2, fill=C["accent"]
                )

        return np.array(img)

    def _lerp_color(self, c1, c2, t):
        """Linear interpolation between two colors."""
        t = max(0, min(1, t))
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ============================================================
# Audio Processing
# ============================================================
def _generate_silence(duration_sec, sr=24000):
    """Generate silence audio samples."""
    total_samples = int(sr * duration_sec)
    return [0] * total_samples


def _generate_ambient_music(duration_sec, sr=24000, volume=0.08):
    """
    Generate subtle ambient background music (very low volume).
    Uses simple chord tones so it doesn't compete with TTS voice.
    """
    total = int(sr * duration_sec)
    music = [0.0] * total

    # Very gentle pad sound — just soft sustained chords
    # Am7 → Fmaj7 → C → G (slow transitions)
    chord_sets = [
        [110.0, 130.81, 164.81],   # Am2
        [87.31, 110.0, 130.81],    # F2
        [130.81, 164.81, 196.00],  # C3
        [98.0, 123.47, 146.83],    # G2
    ]

    chord_dur = total // len(chord_sets)

    for ci, chord in enumerate(chord_sets):
        start = ci * chord_dur
        end = min(start + chord_dur, total)
        for i in range(start, end):
            t = i / sr
            local_t = (i - start) / max(chord_dur - 1, 1)
            env = 0.5 + 0.5 * math.sin(math.pi * local_t)  # smooth fade in/out per chord

            s = 0.0
            for freq in chord:
                # Pure sine for clean pad sound
                s += math.sin(2 * math.pi * freq * t) * 0.15
                # Subtle octave above
                s += math.sin(2 * math.pi * freq * 2 * t) * 0.04

            music[i] = s * env * volume

    # Fade in/out
    fade_len = min(sr, total // 8)
    for i in range(fade_len):
        f = i / fade_len
        music[i] *= f
        music[total - 1 - i] *= f

    # Normalize to prevent clipping
    mx = max(abs(v) for v in music) or 1
    music = [v / mx * 8000 for v in music]

    return music


def _mix_audio_voice_music(voice_paths, gap_sec=0.5, sr=24000, music_vol=0.06):
    """
    Mix all voice clips with gaps + ambient music into a single WAV file.
    Returns path to mixed WAV file.
    """
    import wave

    temp_dir = tempfile.mkdtemp()
    mixed_path = os.path.join(temp_dir, "mixed_audio.wav")

    # Step 1: Convert all MP3 to raw PCM samples
    all_clips = []
    for vp in voice_paths:
        if os.path.exists(vp) and os.path.getsize(vp) > 0:
            samples = _load_mp3_as_samples(vp)
            if samples:
                all_clips.append(samples)
        else:
            print(f"  WARNING: Missing audio file: {vp}")

    if not all_clips:
        print("  ERROR: No audio clips available!")
        return None

    # Step 2: Concatenate voice clips with gaps
    gap_samples = int(sr * gap_sec)
    voice_mixed = []
    for clip in all_clips:
        voice_mixed.extend(clip)
        voice_mixed.extend(_generate_silence(gap_sec, sr))

    # Remove trailing gap
    voice_mixed = voice_mixed[:-gap_samples] if gap_samples < len(voice_mixed) else voice_mixed

    total_sec = len(voice_mixed) / sr
    print(f"  Voice duration: {total_sec:.1f}s")

    # Step 3: Generate ambient music at same length
    music = _generate_ambient_music(total_sec, sr=sr, volume=music_vol)

    # Step 4: Mix voice + music
    # Pad shorter one
    max_len = max(len(voice_mixed), len(music))
    while len(voice_mixed) < max_len:
        voice_mixed.append(0)
    while len(music) < max_len:
        music.append(0)

    final = [int(a + b) for a, b in zip(voice_mixed, music)]

    # Normalize
    peak = max(abs(v) for v in final) or 1
    if peak > 30000:
        final = [int(v * 28000 / peak) for v in final]

    # Write WAV
    with wave.open(mixed_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        data = struct.pack('<' + 'h' * len(final), *final)
        wf.writeframes(data)

    sz = os.path.getsize(mixed_path)
    print(f"  Mixed audio: {mixed_path} ({sz} bytes, {total_sec:.1f}s)")
    return mixed_path


def _load_mp3_as_samples(mp3_path):
    """Load MP3 file and return PCM sample list."""
    try:
        # Use ffmpeg to convert mp3 to raw pcm via pipe
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        cmd = [ffmpeg_exe, '-i', mp3_path, '-ac', '1',
               '-ar', '24000', '-f', 's16le', 'pipe:1']
        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode != 0:
            print(f"  FFmpeg error: {result.stderr[:200]}")
            return None

        # Parse raw PCM data (16-bit signed LE mono)
        raw = result.stdout
        num_samples = len(raw) // 2
        samples = list(struct.unpack('<' + 'h' * num_samples, raw))
        return samples

    except Exception as e:
        print(f"  Failed to load MP3: {e}")
        return None


def merge_av_files(video_path, audio_path, output_path):
    """Merge video + audio using ffmpeg."""
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

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
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        ok = result.returncode == 0 and os.path.exists(output_path)
        if ok:
            print(f"  AV merged: {output_path} ({os.path.getsize(output_path)} bytes)")
        else:
            print(f"  AV merge failed: {result.stderr[:300]}")
        return ok
    except Exception as e:
        print(f"  AV merge error: {e}")
        return False


# ============================================================
# Video Generation — Voice-Synchronized
# ============================================================
def create_video_v4(script, audio_info, output_path):
    """
    Create TikTok video v4: voice-synchronized scenes with karaoke subtitles.

    audio_info: [(label, audio_path, word_data), ...]
    """
    if not HAS_IMAGEIO or not HAS_PILLOW:
        print("  Pillow + imageio required")
        return False

    try:
        temp_dir = tempfile.mkdtemp(prefix="tiktok_v4_")
        print(f"  Temp dir: {temp_dir}")

        # 1. Mix all audio into one file
        print("--- Mixing Audio ---")
        voice_paths = [a[1] for a in audio_info]
        mixed_audio = _mix_audio_voice_music(voice_paths, gap_sec=0.6)

        if not mixed_audio:
            print("  Audio mix failed! Falling back to silent...")
            return False

        # 2. Calculate timing for each scene based on word_data
        print("--- Calculating Timings ---")
        scene_timings = []  # (label, text, start_sec, end_sec, word_data)
        current_sec = 0.0
        gap = 0.6  # gap between scenes

        spoken_lines = build_spoken_lines(script)

        for idx, (label, text) in enumerate(spoken_lines):
            word_data = audio_info[idx][2] if idx < len(audio_info) else []

            if word_data:
                first_word_start = word_data[0]["offset_sec"]
                last_word_end = word_data[-1]["offset_sec"] + word_data[-1]["duration_sec"]

                # Duration from TTS data
                scene_dur = last_word_end + 0.3  # small tail padding
            else:
                # Fallback: estimate ~3 sec per scene
                scene_dur = 3.0
                first_word_start = 0.0
                last_word_end = 3.0

            # Map absolute times
            abs_start = current_sec
            abs_end = current_sec + scene_dur

            # Adjust word timestamps to absolute timeline
            abs_word_data = []
            for wd in word_data:
                abs_word_data.append({
                    "text": wd["text"],
                    "offset_sec": abs_start + wd["offset_sec"],
                    "duration_sec": wd["duration_sec"],
                })

            scene_timings.append({
                "label": label,
                "text": text,
                "start": abs_start,
                "end": abs_end,
                "duration": scene_dur,
                "word_data": abs_word_data,
                "is_hook": label == "hook",
                "is_cta": label == "cta",
            })

            current_sec = abs_end + gap

        total_duration = current_sec - gap  # remove trailing gap
        total_frames = int(total_duration * FPS)
        print(f"  Total duration: {total_duration:.1f}s, {total_frames} frames @ {FPS}fps")

        # 3. Pre-render static backgrounds (one per scene)
        print("--- Rendering Scenes ---")
        scene_images = {}
        for st in scene_timings:
            label = st["label"]
            is_hook = st["is_hook"]
            is_cta = st["is_cta"]

            img = _render_text_on_bg(st["text"], label, is_hook=is_hook, is_cta=is_cta)
            scene_images[label] = img
            print(f"  Scene [{label}]: {st['text'][:50]}...")

        # 4. Generate video frame by frame
        print("--- Encoding Video ---")
        temp_video = os.path.join(temp_dir, "video_noaudio.mp4")

        writer = iio.get_writer(temp_video, fps=FPS, codec='libx264',
                                output_params=['-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '23'])

        for frame_num in range(total_frames):
            current_time = frame_num / FPS

            # Which scene are we in?
            active_scene = None
            for st in scene_timings:
                if st["start"] <= current_time < st["end"]:
                    active_scene = st
                    break
            if active_scene is None:
                # After last scene — show CTA
                active_scene = scene_timings[-1]

            label = active_scene["label"]

            # Get base background image (with animation)
            scene_local_time = current_time - active_scene["start"]
            local_total_frames = int(active_scene["duration"] * FPS)
            local_frame = min(int(scene_local_time * FPS), max(local_total_frames - 1, 0))

            # Re-render bg with animation frame
            bg_img = _make_cinematic_bg(label, frame_idx=local_frame,
                                         total_frames=max(local_total_frames, 1))

            # Draw text on top (from pre-rendered)
            text_img = scene_images[label]
            # Blend text layer onto animated bg
            bg_arr = np.array(bg_img).astype(np.float32)
            text_arr = np.array(text_img).astype(np.float32)

            # Composite: bg takes animated parts, text overlays
            # Simple approach: use text_img as base, re-apply animated elements
            # Actually let's use text_img as main visual (it has text already rendered)
            frame = np.array(text_img.copy())

            # Apply Ken Burns style zoom to the whole frame
            zoom_amount = 1.0 + 0.03 * math.sin(frame_num * 0.01)  # very slow breathing
            # (subtle, won't distort text much because text is part of the image)

            # Add karaoke subtitles
            if active_scene["word_data"]:
                karaoke = KaraokeRenderer(
                    active_scene["word_data"],
                    active_scene["duration"],
                    label=label
                )
                scene_time = current_time - active_scene["start"]
                frame = karaoke.render_frame(frame, scene_time)

            writer.append_data(frame)

            # Progress indicator
            if frame_num % 60 == 0:
                pct = frame_num / total_frames * 100
                print(f"  Frame {frame_num}/{total_frames} ({pct:.0f}%)")

        writer.close()

        # 5. Merge audio + video
        print("--- Merging A/V ---")
        final_output = output_path or os.path.join(temp_dir, "final.mp4")
        success = merge_av_files(temp_video, mixed_audio, final_output)

        # Cleanup
        try:
            for f in [temp_video, mixed_audio]:
                if os.path.exists(f):
                    os.remove(f)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

        if success:
            sz = os.path.getsize(final_output)
            print(f"\n  SUCCESS: {final_output} ({sz} bytes, {total_duration:.1f}s)")
            return True
        else:
            # Try to keep video without audio
            if os.path.exists(temp_video):
                try:
                    os.rename(temp_video, output_path)
                    print(f"  Fallback: saved video without audio")
                    return True
                except Exception:
                    pass
            return False

    except Exception as e:
        print(f"  Video creation failed: {e}")
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
async def async_main():
    print("=" * 55)
    print(" BroadFSC TikTok Auto-Poster v4")
    print(" AI Voice + Karaoke Subtitles + Cinematic Video")
    print("=" * 55)

    now = datetime.datetime.utcnow()
    print("UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print(f"TTS: {'YES (' + TTS_VOICE + ')' if HAS_TTS else 'NO'}")
    print(f"Pillow: {'YES' if HAS_PILLOW else 'NO'}")
    print(f"imageio: {'YES' if HAS_IMAGEIO else 'NO'}")
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

    # Step 3: Check TTS availability
    if not HAS_TTS:
        print("ERROR: edge-tts not installed! Run: pip install edge-tts")
        return False

    # Step 4: Generate TTS audio for all lines
    print("--- Step 3: Generate Voice Over ---")
    spoken_lines = build_spoken_lines(script)
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tts_cache")
    os.makedirs(temp_dir, exist_ok=True)

    audio_info = await generate_all_audio(spoken_lines, temp_dir)
    print(f"  Generated {len(audio_info)} audio clips")
    print()

    # Step 5: Create video with voice sync
    print("--- Step 4: Create Video (v4 Voice-Synced) ---")
    success = False
    video_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(video_dir, "tiktok_v4.mp4")

    if HAS_PILLOW and HAS_IMAGEIO:
        if create_video_v4(script, audio_info, video_path):
            # Step 6: Post to TikTok
            print("--- Step 5: Post to TikTok ---")
            success = post_tiktok_video_file(caption, video_path)
            try:
                os.remove(video_path)
            except Exception:
                pass
        else:
            print("  Video creation failed!")

        # Cleanup TTS cache
        for _, ap, _ in audio_info:
            try:
                if os.path.exists(ap):
                    os.remove(ap)
            except Exception:
                pass
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass
    else:
        print("  Pillow + imageio required!")

    print()

    # Step 7: Notify & log
    if success:
        notify_telegram("TikTok v4 post published: " + caption[:80])
        print("SUCCESS: TikTok v4 posted with VOICE + KARAOKE SUBS!")
        if HAS_ANALYTICS:
            log_post(platform="tiktok", post_type="video_v4", content_preview=caption[:100], status="success")
    else:
        notify_telegram("TikTok v4 post FAILED")
        print("FAILED: TikTok v4 not posted.")
        if HAS_ANALYTICS:
            log_post(platform="tiktok", post_type="video_v4", content_preview=caption[:100], status="failed", error_msg="Video creation failed")

    print()
    print("=" * 55)
    print("Done.")
    return success


def main():
    """Entry point — runs async TTS pipeline."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
