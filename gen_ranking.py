"""
BroadFSC TikTok — K-Line Pattern RANKING Video
Style: Tier list / ranking format (weakest to strongest)
Inspired by Douyin finance ranking videos

Format:
- Full-screen dark trading UI background
- Left side: Large K-line pattern illustration (PIL-drawn)
- Right side: Rank number + Pattern name + Brief explanation
- Animated: each pattern slides in from bottom
- Ranking from WEAKEST to STRONGEST signal

EP9:  Single Candle Rankings (Weakest → Strongest)
EP10: MACD Signal Rankings  
EP11: Bollinger Band Pattern Rankings
EP12: Volume Signal Rankings
"""

import os, sys, asyncio, shutil, math, struct, io, random, tempfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import imageio.v2 as iio
    HAS_ALL = True
except ImportError as e:
    print(f"Missing: {e}"); HAS_ALL = False

try:
    import edge_tts
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

# Canvas
W, H = 1088, 1920
FPS = 30
DESKTOP = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")

# Colors — Professional dark trading UI
BG       = (8, 10, 18)
BG2      = (14, 17, 30)
WHITE    = (255, 255, 255)
GRAY     = (150, 165, 190)
DIM      = (50, 58, 85)
ACCENT   = (56, 134, 255)
GREEN    = (0, 214, 130)
RED      = (255, 60, 60)
GOLD     = (255, 196, 0)
PURPLE   = (168, 85, 247)
TEAL     = (20, 184, 166)
ORANGE   = (255, 140, 0)

# Tier colors (from weakest to strongest)
TIER_COLORS = [
    (120, 130, 150),  # #6 gray - weakest
    (168, 85, 247),   # purple
    (56, 134, 255),   # blue
    (20, 184, 166),   # teal
    (0, 214, 130),    # green
    (255, 196, 0),    # gold - strongest
]

TTS_VOICE = "en-US-GuyNeural"
TTS_RATE = "+5%"

# Font
_FC = {}
def font(size, bold=True):
    key = (size, bold)
    if key in _FC: return _FC[key]
    for p in (["C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/Arial Bold.ttf"] if bold
              else ["C:/Windows/Fonts/arial.ttf","C:/Windows/Fonts/Arial.ttf"]):
        if os.path.exists(p):
            try: _FC[key] = ImageFont.truetype(p, size); return _FC[key]
            except: pass
    _FC[key] = ImageFont.load_default(); return _FC[key]


# ─────────────────────────────────────────────
# K-Line Pattern Drawing Functions
# Each draws a single candlestick pattern on a PIL image
# ─────────────────────────────────────────────
def _draw_candle(draw, cx, body_top, body_bot, wick_top, wick_bot, 
                 body_w=80, color=GREEN, shadow=True):
    """Draw a single candlestick on PIL draw object."""
    half = body_w // 2
    # Shadow/glow
    if shadow:
        for offset in range(3, 0, -1):
            alpha_col = tuple(min(255, c + 30) for c in color)
            draw.rectangle([(cx-half-offset, body_top-offset), 
                           (cx+half+offset, body_bot+offset)],
                          fill=None, outline=(*alpha_col, 40))
    # Body
    draw.rectangle([(cx-half, body_top), (cx+half, body_bot)], fill=color, outline=color)
    # Upper wick
    draw.line([(cx, wick_top), (cx, body_top)], fill=color, width=4)
    # Lower wick
    draw.line([(cx, body_bot), (cx, wick_bot)], fill=color, width=4)


def _draw_doji(draw, cx, mid_y, wick_h=160, body_w=80):
    """Doji: open ≈ close, long wicks."""
    draw.line([(cx, mid_y - wick_h), (cx, mid_y + wick_h)], fill=GRAY, width=4)
    draw.rectangle([(cx - body_w//2, mid_y - 3), (cx + body_w//2, mid_y + 3)], fill=GRAY)


def _draw_hammer(draw, cx, body_top, body_bot, wick_bot, body_w=80):
    """Hammer: small body at top, long lower wick, no upper wick."""
    half = body_w // 2
    draw.rectangle([(cx-half, body_top), (cx+half, body_bot)], fill=GREEN)
    draw.line([(cx, body_bot), (cx, wick_bot)], fill=GREEN, width=4)
    # tiny upper wick
    draw.line([(cx, body_top), (cx, body_top - 10)], fill=GREEN, width=4)


def _draw_shooting_star(draw, cx, body_top, body_bot, wick_top, body_w=80):
    """Shooting star: small body at bottom, long upper wick."""
    half = body_w // 2
    draw.rectangle([(cx-half, body_top), (cx+half, body_bot)], fill=RED)
    draw.line([(cx, body_top), (cx, wick_top)], fill=RED, width=4)
    draw.line([(cx, body_bot), (cx, body_bot + 10)], fill=RED, width=4)


def _draw_engulfing(draw, cx, body1_top, body1_bot, body2_top, body2_bot,
                    wick1_top, wick1_bot, wick2_top, wick2_bot, body_w=80):
    """Bullish engulfing: red candle followed by bigger green candle."""
    half = body_w // 2
    # Red candle (day 1)
    draw.line([(cx-body_w, wick1_top), (cx-body_w, wick1_bot)], fill=RED, width=3)
    draw.rectangle([(cx-body_w-half, body1_top), (cx-body_w+half, body1_bot)], fill=RED)
    # Green candle (day 2) - bigger
    draw.line([(cx, wick2_top), (cx, wick2_bot)], fill=GREEN, width=4)
    draw.rectangle([(cx-half-10, body2_top), (cx+half+10, body2_bot)], fill=GREEN)


def _draw_morning_star(draw, cx, body_w=80):
    """Morning star: big red → small body → big green."""
    half = body_w // 2
    # Red candle
    draw.line([(cx-100, 300), (cx-100, 600)], fill=RED, width=3)
    draw.rectangle([(cx-100-half, 340), (cx-100+half, 560)], fill=RED)
    # Small doji
    draw.line([(cx, 360), (cx, 480)], fill=GRAY, width=3)
    draw.rectangle([(cx-20, 410), (cx+20, 430)], fill=GRAY)
    # Green candle
    draw.line([(cx+100, 280), (cx+100, 580)], fill=GREEN, width=3)
    draw.rectangle([(cx+100-half, 300), (cx+100+half, 520)], fill=GREEN)


def _draw_dragonfly_doji(draw, cx, mid_y, wick_h=180):
    """Dragonfly doji: long lower wick, no upper wick, open=close at top."""
    draw.line([(cx, mid_y), (cx, mid_y + wick_h)], fill=GREEN, width=4)
    draw.rectangle([(cx-40, mid_y-3), (cx+40, mid_y+3)], fill=GREEN)


def _draw_marubozu_green(draw, cx, body_top, body_bot, body_w=80):
    """Green marubozu: no wicks, pure bullish conviction."""
    half = body_w // 2
    draw.rectangle([(cx-half, body_top), (cx+half, body_bot)], fill=GREEN)


# ─────────────────────────────────────────────
# Render a single ranking card
# ─────────────────────────────────────────────
def render_ranking_card(rank, pattern_name, description, pattern_fn,
                        tier_color, total_ranks, card_alpha=1.0):
    """Render one ranking card as PIL Image (W x H).
    
    Layout:
    ┌────────────────────────────────┐
    │  [Header: "SINGLE CANDLE RANKING"]  │
    │  [Progress bar]                    │
    │                                    │
    │  ┌──────────┐  RANK #5            │
    │  │          │  "HAMMER"            │
    │  │  K-LINE  │  ★★☆☆☆             │
    │  │ PATTERN  │                      │
    │  │  ILLUSTR │  "Small body at top" │
    │  │          │  "Long lower wick"   │
    │  └──────────┘  "Buyers fought back"│
    │                                    │
    │  [BroadFSC]              [EP9]     │
    └────────────────────────────────┘
    """
    img = Image.new('RGBA', (W, H), BG + (255,))
    draw = ImageDraw.Draw(img)
    
    a = card_alpha  # alpha multiplier
    tier_c = tier_color
    
    # ── Background gradient effect ──
    for y_line in range(H):
        frac = y_line / H
        r = int(BG[0] + (tier_c[0] - BG[0]) * 0.06 * (1 - frac))
        g = int(BG[1] + (tier_c[1] - BG[1]) * 0.06 * (1 - frac))
        b = int(BG[2] + (tier_c[2] - BG[2]) * 0.06 * (1 - frac))
        draw.line([(0, y_line), (W, y_line)], fill=(r, g, b, int(255*a)))
    
    # ── Top section: Header ──
    header_y = 60
    
    # Brand pill (top-left)
    bf = font(22, bold=True)
    draw.rounded_rectangle((24, header_y, 180, header_y+40), radius=10,
                          fill=ACCENT + (int(220*a),))
    draw.text((102, header_y+20), "BroadFSC", font=bf, 
             fill=WHITE + (int(255*a),), anchor="mm")
    
    # EP tag (top-right)
    ef = font(16, bold=False)
    ep_text = f"EP9 · Candlestick"
    ew = draw.textbbox((0,0), ep_text, font=ef)[2]
    draw.rounded_rectangle((W-ew-48, header_y, W-24, header_y+36), radius=10,
                          fill=DIM + (int(180*a),))
    draw.text((W-36-ew//2, header_y+18), ep_text, font=ef,
             fill=GRAY + (int(220*a),), anchor="mm")
    
    # ── Title: "SINGLE CANDLE RANKING" ──
    title_y = 140
    tf = font(38, bold=True)
    draw.text((W//2, title_y), "SINGLE CANDLE RANKING", font=tf,
             fill=tier_c + (int(255*a),), anchor="mm")
    
    # ── Progress bar ──
    bar_y = 190
    bar_w = W - 120
    bar_h = 8
    bar_x0 = 60
    # Background
    draw.rounded_rectangle((bar_x0, bar_y, bar_x0+bar_w, bar_y+bar_h), 
                          radius=4, fill=DIM + (int(120*a),))
    # Filled portion
    fill_w = int(bar_w * rank / total_ranks)
    if fill_w > 0:
        draw.rounded_rectangle((bar_x0, bar_y, bar_x0+fill_w, bar_y+bar_h),
                              radius=4, fill=tier_c + (int(255*a),))
    # Rank dots
    for ri in range(total_ranks):
        dot_x = bar_x0 + int(bar_w * (ri + 1) / total_ranks)
        dot_r = 8 if ri == rank - 1 else 5
        dot_col = tier_c if ri < rank else DIM
        draw.ellipse((dot_x-dot_r, bar_y+bar_h//2-dot_r, 
                      dot_x+dot_r, bar_y+bar_h//2+dot_r),
                     fill=dot_col + (int(255*a),))
    
    # ── Main content area ──
    content_y = 260
    
    # Left side: K-line pattern illustration (glassmorphism card)
    card_left = 40
    card_right = W // 2 + 20
    card_top = content_y
    card_bot = content_y + 800
    
    # Glass card background
    draw.rounded_rectangle((card_left, card_top, card_right, card_bot),
                          radius=24, fill=(18, 22, 38, int(200*a)),
                          outline=tier_c + (int(60*a),), width=2)
    
    # Draw the pattern illustration inside the card
    # We'll use pattern_fn callback to draw the specific pattern
    pattern_img = Image.new('RGBA', (W, H), (0,0,0,0))
    p_draw = ImageDraw.Draw(pattern_img)
    pattern_fn(p_draw)
    # Composite pattern onto main image
    img = Image.alpha_composite(img, pattern_img)
    draw = ImageDraw.Draw(img)
    
    # Right side: Rank info
    right_x = W // 2 + 60
    
    # Rank number (huge)
    rank_y = content_y + 60
    rank_f = font(140, bold=True)
    rank_text = f"#{rank}"
    draw.text((right_x, rank_y), rank_text, font=rank_f,
             fill=tier_c + (int(255*a),), anchor="la")
    
    # Pattern name
    name_y = rank_y + 160
    name_f = font(52, bold=True)
    draw.text((right_x, name_y), pattern_name, font=name_f,
             fill=WHITE + (int(255*a),), anchor="la")
    
    # Signal strength stars
    star_y = name_y + 70
    filled_stars = rank  # rank 1 = weakest (1 star), rank 6 = strongest (6 stars)
    star_f = font(36, bold=False)
    stars = "★" * filled_stars + "☆" * (total_ranks - filled_stars)
    draw.text((right_x, star_y), stars, font=star_f,
             fill=tier_c + (int(220*a),), anchor="la")
    
    # Strength label
    strength_labels = ["WEAKEST", "WEAK", "MODERATE", "STRONG", "VERY STRONG", "STRONGEST"]
    sl_y = star_y + 55
    sl_f = font(24, bold=True)
    sl_text = strength_labels[min(rank-1, len(strength_labels)-1)]
    sl_w = draw.textbbox((0,0), sl_text, font=sl_f)[2]
    draw.rounded_rectangle((right_x-8, sl_y-4, right_x+sl_w+16, sl_y+34),
                          radius=8, fill=tier_c + (int(60*a),))
    draw.text((right_x+4, sl_y+15), sl_text, font=sl_f,
             fill=tier_c + (int(255*a),), anchor="lm")
    
    # Description lines
    desc_y = sl_y + 70
    desc_f = font(28, bold=False)
    desc_lines = description.split('\n')
    for dl in desc_lines:
        if not dl.strip(): continue
        draw.text((right_x, desc_y), dl.strip(), font=desc_f,
                 fill=GRAY + (int(220*a),), anchor="la")
        desc_y += 42
    
    # ── Bottom: Summary / Key takeaway ──
    bottom_y = H - 220
    # Glassmorphism bottom bar
    draw.rounded_rectangle((40, bottom_y, W-40, bottom_y+100),
                          radius=16, fill=(18, 22, 38, int(180*a)),
                          outline=ACCENT + (int(40*a),), width=1)
    
    tip_f = font(24, bold=False)
    tip_text = f"#{rank}/{total_ranks} — Higher rank = more reliable signal"
    draw.text((W//2, bottom_y+50), tip_text, font=tip_f,
             fill=GRAY + (int(180*a),), anchor="mm")
    
    # Website
    url_f = font(18, bold=False)
    draw.text((W//2, H-60), "broadfsc.com/different", font=url_f,
             fill=DIM + (int(150*a),), anchor="mm")
    
    return img.convert('RGB')


# ─────────────────────────────────────────────
# Pattern drawing callbacks for each rank
# ─────────────────────────────────────────────

def _pattern_doji(p_draw):
    """Doji - Rank 1 (weakest)"""
    cx, cy = W//4 + 30, 580
    _draw_doji(p_draw, cx, cy, wick_h=140)
    # Label
    label_f = font(20, bold=False)
    p_draw.text((cx, cy+180), "DOJI", font=label_f, fill=GRAY+(180,), anchor="mm")
    # "Open = Close" annotation
    ann_f = font(16, bold=False)
    p_draw.text((cx, cy-170), "Open ≈ Close", font=ann_f, fill=GRAY+(140,), anchor="mm")

def _pattern_spinning_top(p_draw):
    """Spinning Top - Rank 2"""
    cx, cy = W//4 + 30, 580
    half = 30
    # Small body
    p_draw.rectangle([(cx-half, cy-12), (cx+half, cy+12)], fill=GRAY)
    # Equal wicks
    p_draw.line([(cx, cy-12), (cx, cy-130)], fill=GRAY, width=4)
    p_draw.line([(cx, cy+12), (cx, cy+130)], fill=GRAY, width=4)
    label_f = font(20, bold=False)
    p_draw.text((cx, cy+180), "SPINNING TOP", font=label_f, fill=GRAY+(180,), anchor="mm")
    ann_f = font(16, bold=False)
    p_draw.text((cx, cy-160), "Indecision", font=ann_f, fill=PURPLE+(140,), anchor="mm")

def _pattern_shooting_star(p_draw):
    """Shooting Star - Rank 3"""
    cx = W//4 + 30
    _draw_shooting_star(p_draw, cx, 540, 600, 320, body_w=70)
    label_f = font(20, bold=False)
    p_draw.text((cx, 720), "SHOOTING STAR", font=label_f, fill=RED+(180,), anchor="mm")
    ann_f = font(16, bold=False)
    p_draw.text((cx, 280), "Bearish Reversal", font=ann_f, fill=ACCENT+(140,), anchor="mm")

def _pattern_hammer(p_draw):
    """Hammer - Rank 4"""
    cx = W//4 + 30
    _draw_hammer(p_draw, cx, 400, 480, 700, body_w=70)
    label_f = font(20, bold=False)
    p_draw.text((cx, 720), "HAMMER", font=label_f, fill=GREEN+(180,), anchor="mm")
    ann_f = font(16, bold=False)
    p_draw.text((cx, 340), "Bullish Reversal", font=ann_f, fill=TEAL+(140,), anchor="mm")

def _pattern_engulfing(p_draw):
    """Bullish Engulfing - Rank 5"""
    cx = W//4 + 30
    _draw_engulfing(p_draw, cx, 420, 580, 360, 620, 360, 620, 320, 660, body_w=60)
    label_f = font(20, bold=False)
    p_draw.text((cx, 720), "BULLISH ENGULFING", font=label_f, fill=GREEN+(180,), anchor="mm")
    ann_f = font(16, bold=False)
    p_draw.text((cx, 280), "Strong Reversal", font=ann_f, fill=GREEN+(140,), anchor="mm")

def _pattern_morning_star(p_draw):
    """Morning Star - Rank 6 (strongest)"""
    cx = W//4 + 30
    _draw_morning_star(p_draw, cx, body_w=55)
    label_f = font(20, bold=False)
    p_draw.text((cx, 720), "MORNING STAR", font=label_f, fill=GOLD+(180,), anchor="mm")
    ann_f = font(16, bold=False)
    p_draw.text((cx, 250), "Highly Reliable", font=ann_f, fill=GOLD+(140,), anchor="mm")


# ─────────────────────────────────────────────
# Hook / CTA renderers
# ─────────────────────────────────────────────
def render_hook(title, subtitle, alpha=1.0):
    """Full-screen hook/intro card."""
    img = Image.new('RGBA', (W, H), BG + (255,))
    draw = ImageDraw.Draw(img)
    a = alpha
    
    # Animated gradient lines (decorative)
    for i in range(5):
        y = 200 + i * 280
        w_line = W - 200 - i * 100
        if w_line > 0:
            draw.rounded_rectangle((100, y, 100+w_line, y+3), radius=2,
                                  fill=ACCENT + (int(30*a),))
    
    # Brand pill
    bf = font(26, bold=True)
    draw.rounded_rectangle((W//2-90, 80, W//2+90, 124), radius=12,
                          fill=ACCENT + (int(220*a),))
    draw.text((W//2, 102), "BroadFSC", font=bf, fill=WHITE+(int(255*a),), anchor="mm")
    
    # Main title
    tf = font(72, bold=True)
    lines = title.split('\n')
    ly = H//2 - 80
    for line in lines:
        draw.text((W//2, ly), line, font=tf, fill=WHITE+(int(255*a),), anchor="mm")
        ly += 96
    
    # Accent underline
    draw.rounded_rectangle((W//2-120, ly+10, W//2+120, ly+16), radius=3,
                          fill=GOLD+(int(255*a),))
    
    # Subtitle
    sf = font(32, bold=False)
    draw.text((W//2, ly+60), subtitle, font=sf, fill=GRAY+(int(200*a),), anchor="mm")
    
    # Bottom hint
    hf = font(22, bold=False)
    draw.text((W//2, H-120), "Swipe up to see the rankings", font=hf,
             fill=DIM+(int(150*a),), anchor="mm")
    
    return img.convert('RGB')


def render_cta(alpha=1.0):
    """Full-screen CTA card."""
    img = Image.new('RGBA', (W, H), BG + (255,))
    draw = ImageDraw.Draw(img)
    a = alpha
    
    # Brand
    bf = font(30, bold=True)
    draw.text((W//2, H//2-120), "BroadFSC", font=bf, fill=ACCENT+(int(255*a),), anchor="mm")
    
    # CTA text
    cf = font(56, bold=True)
    draw.text((W//2, H//2-20), "Trade Smarter.", font=cf, fill=GREEN+(int(255*a),), anchor="mm")
    draw.text((W//2, H//2+60), "Trade with Edge.", font=cf, fill=GREEN+(int(255*a),), anchor="mm")
    
    # URL pill
    url = "broadfsc.com/different"
    uf = font(26, bold=False)
    uw = draw.textbbox((0,0), url, font=uf)[2]
    px = (W-uw)//2
    draw.rounded_rectangle((px-20, H//2+140, px+uw+20, H//2+186), radius=14,
                          fill=DIM+(int(200*a),))
    draw.text((W//2, H//2+163), url, font=uf, fill=GRAY+(int(220*a),), anchor="mm")
    
    # Follow hint
    ff = font(22, bold=False)
    draw.text((W//2, H-140), "Follow for daily rankings", font=ff,
             fill=DIM+(int(150*a),), anchor="mm")
    
    return img.convert('RGB')


# ─────────────────────────────────────────────
# EPISODE DEFINITIONS
# ─────────────────────────────────────────────
EPISODES = [
    {
        "ep": 9,
        "title": "Candlestick\nRankings",
        "hook_sub": "From weakest to strongest signal",
        "header": "SINGLE CANDLE RANKING",
        "ranks": [
            {
                "rank": 1,
                "name": "DOJI",
                "desc": "Open equals close.\nPure indecision.\nNo directional bias.",
                "draw_fn": _pattern_doji,
            },
            {
                "rank": 2,
                "name": "SPINNING TOP",
                "desc": "Small real body.\nEqual wicks up & down.\nMarket is confused.",
                "draw_fn": _pattern_spinning_top,
            },
            {
                "rank": 3,
                "name": "SHOOTING STAR",
                "desc": "Long upper wick.\nSmall body at bottom.\nBearish reversal signal.",
                "draw_fn": _pattern_shooting_star,
            },
            {
                "rank": 4,
                "name": "HAMMER",
                "desc": "Small body at top.\nLong lower wick.\nBuyers fought back hard.",
                "draw_fn": _pattern_hammer,
            },
            {
                "rank": 5,
                "name": "ENGULFING",
                "desc": "Big candle swallows\nthe previous one.\nStrong reversal signal.",
                "draw_fn": _pattern_engulfing,
            },
            {
                "rank": 6,
                "name": "MORNING STAR",
                "desc": "3-candle pattern.\nRed → Doji → Green.\nMost reliable reversal.",
                "draw_fn": _pattern_morning_star,
            },
        ],
    },
    # EP10-12 follow the same pattern with different themes
    # (Will be implemented after EP9 test)
]


# ─────────────────────────────────────────────
# TTS + Audio
# ─────────────────────────────────────────────
async def _gen_tts(text, out_path):
    if not HAS_TTS: return out_path, 3.0
    comm = edge_tts.Communicate(text, voice=TTS_VOICE, rate=TTS_RATE)
    await comm.save(out_path)
    if os.path.exists(out_path):
        dur = os.path.getsize(out_path) / (32000/8)
        return out_path, max(2.0, dur)
    return out_path, len(text.split()) * 0.35

async def _gen_all_tts(sentences, tmp_dir):
    results = []
    for i, txt in enumerate(sentences):
        path = os.path.join(tmp_dir, f"tts_{i:02d}.mp3")
        _, dur = await _gen_tts(txt, path)
        results.append((txt, path, dur))
        print(f"  TTS {i+1}/{len(sentences)}: {dur:.1f}s — {txt[:50]}")
    return results

def _mp3_to_pcm(path):
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except: ffmpeg_exe = 'ffmpeg'
    cmd = [ffmpeg_exe, '-y', '-i', path, '-f', 's16le', '-acodec', 'pcm_s16le',
           '-ar', '44100', '-ac', '2', 'pipe:1']
    return subprocess.run(cmd, capture_output=True).stdout

def _build_audio(tts_clips, gap=0.5, sr=44100, ch=2):
    gap_bytes = b'\x00' * (int(gap*sr) * ch * 2)
    all_pcm = b''; durations = []; t = 0.0
    for text, path, _ in tts_clips:
        pcm = _mp3_to_pcm(path)
        dur = len(pcm) / (sr*ch*2)
        durations.append((t, dur))
        all_pcm += pcm + gap_bytes
        t += dur + gap
    hdr = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36+len(all_pcm), b'WAVE', b'fmt ', 16, 1, ch, sr, sr*ch*2, ch*2, 16, b'data', len(all_pcm))
    return hdr + all_pcm, durations, t


# ─────────────────────────────────────────────
# Video generator
# ─────────────────────────────────────────────
async def generate_episode(ep_def, tmp_dir, output_path):
    ep_num = ep_def['ep']
    ranks = ep_def['ranks']
    total_ranks = len(ranks)
    
    print(f"\n{'='*58}")
    print(f" EP.{ep_num}: {ep_def['title'].replace(chr(10),' ')}")
    print(f"{'='*58}")
    
    # Build scene list: Hook → Rank1 → Rank2 → ... → CTA
    scenes = []
    
    # Hook
    scenes.append({
        'type': 'hook',
        'title': ep_def['title'],
        'subtitle': ep_def['hook_sub'],
        'tts': f"Candlestick pattern rankings. From weakest to strongest. Let's go!",
        'duration': 4.0,
    })
    
    # Each rank
    for r in ranks:
        scenes.append({
            'type': 'rank',
            'rank': r['rank'],
            'name': r['name'],
            'desc': r['desc'],
            'draw_fn': r['draw_fn'],
            'tts': f"Rank number {r['rank']}. {r['name']}. {r['desc'].replace(chr(10), ' ')}",
            'duration': 4.5,
        })
    
    # CTA
    scenes.append({
        'type': 'cta',
        'tts': "Follow BroadFSC for more trading education.",
        'duration': 3.5,
    })
    
    # Generate TTS
    print("--- Generating TTS ---")
    tts_texts = [s['tts'] for s in scenes]
    tts_clips = await _gen_all_tts(tts_texts, tmp_dir)
    
    # Update durations from TTS
    for i, (_, _, dur) in enumerate(tts_clips):
        scenes[i]['duration'] = max(scenes[i]['duration'], dur + 0.5)
    
    total_dur = sum(s['duration'] for s in scenes)
    print(f"  Total duration: {total_dur:.1f}s ({len(scenes)} scenes)")
    
    # Build audio
    print("--- Building Audio ---")
    audio_wav, clip_times, _ = _build_audio(tts_clips, gap=0.3)
    audio_path = os.path.join(tmp_dir, f"ep{ep_num}_audio.wav")
    with open(audio_path, 'wb') as f: f.write(audio_wav)
    print(f"  Audio: {len(audio_wav)//1024}KB")
    
    # Pre-render all scene images
    print("--- Pre-rendering Scenes ---")
    scene_imgs = []
    for si, sc in enumerate(scenes):
        if sc['type'] == 'hook':
            img = render_hook(sc['title'], sc['subtitle'])
        elif sc['type'] == 'cta':
            img = render_cta()
        elif sc['type'] == 'rank':
            tier_c = TIER_COLORS[min(sc['rank']-1, len(TIER_COLORS)-1)]
            img = render_ranking_card(
                rank=sc['rank'],
                pattern_name=sc['name'],
                description=sc['desc'],
                pattern_fn=sc['draw_fn'],
                tier_color=tier_c,
                total_ranks=total_ranks,
            )
        scene_imgs.append(img)
        print(f"  Scene {si+1}/{len(scenes)}: {sc['type']} rendered")
    
    # Render video frames
    print("--- Rendering Frames ---")
    total_frames = int(total_dur * FPS)
    video_path = os.path.join(tmp_dir, f"ep{ep_num}_raw.mp4")
    
    writer = iio.get_writer(video_path, fps=FPS, codec='libx264',
        output_params=['-crf', '20', '-preset', 'fast', '-pix_fmt', 'yuv420p'])
    
    # Scene timing
    scene_starts = []
    t = 0.0
    for sc in scenes:
        scene_starts.append(t)
        t += sc['duration']
    
    for fi in range(total_frames):
        t = fi / FPS
        
        # Find active scene
        active = 0
        for si in range(len(scenes)):
            if t >= scene_starts[si]:
                active = si
        if active >= len(scenes): active = len(scenes) - 1
        
        sc = scenes[active]
        scene_t = t - scene_starts[active]
        
        # Transition: fade in 0.3s, fade out 0.3s
        fade = 0.3
        if scene_t < fade:
            alpha = scene_t / fade
        elif scene_t > sc['duration'] - fade:
            alpha = (sc['duration'] - scene_t) / fade
        else:
            alpha = 1.0
        alpha = max(0.0, min(1.0, alpha))
        
        # Slide-in effect for rank cards (from bottom)
        if sc['type'] == 'rank' and scene_t < 0.5:
            # Slide from bottom
            slide_offset = int((1 - scene_t / 0.5) * 200)
            base_img = Image.new('RGB', (W, H), BG)
            card = scene_imgs[active]
            if slide_offset > 0:
                base_img.paste(card, (0, slide_offset))
            else:
                base_img = card
        else:
            base_img = scene_imgs[active]
        
        # Apply fade (blend with black)
        if alpha < 0.99:
            black = Image.new('RGB', (W, H), BG)
            frame = Image.blend(black, base_img, alpha)
        else:
            frame = base_img
        
        writer.append_data(np.array(frame))
        
        if fi % (FPS * 5) == 0:
            print(f"  Frame {fi}/{total_frames} ({t:.1f}s)")
    
    writer.close()
    
    # Mux audio
    print("--- Muxing ---")
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except: ffmpeg_exe = 'ffmpeg'
    cmd = [ffmpeg_exe, '-y', '-i', video_path, '-i', audio_path,
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
           '-map', '0:v:0', '-map', '1:a:0', output_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FFmpeg err: {r.stderr[-300:]}")
        shutil.copy2(video_path, output_path)
    else:
        print("  Mux OK!")
    
    size_kb = os.path.getsize(output_path) // 1024
    print(f"  EP.{ep_num} done: {output_path} ({size_kb}KB)")
    return output_path


async def main():
    if not HAS_ALL:
        print("ERROR: Missing numpy/PIL/imageio"); return
    if not HAS_TTS:
        print("WARNING: No edge_tts — no audio")
    
    print("=" * 58)
    print(" BroadFSC TikTok — K-Line Ranking Videos")
    print(" Style: Tier List / Weakest → Strongest")
    print("=" * 58)
    
    tmp_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_rank_cache")
    os.makedirs(tmp_root, exist_ok=True)
    
    for ep_def in EPISODES:
        ep_num = ep_def['ep']
        ep_dir = os.path.join(tmp_root, f"ep{ep_num}")
        os.makedirs(ep_dir, exist_ok=True)
        out = os.path.join(DESKTOP, f"tiktok_ep{ep_num}_final.mp4")
        try:
            await generate_episode(ep_def, ep_dir, out)
        except Exception as e:
            import traceback
            print(f"  EP.{ep_num} FAILED: {e}")
            traceback.print_exc()
    
    try: shutil.rmtree(tmp_root, ignore_errors=True)
    except: pass
    
    print("\n" + "=" * 58)
    print(" DONE — Check Desktop for videos!")
    print("=" * 58)

if __name__ == "__main__":
    asyncio.run(main())
