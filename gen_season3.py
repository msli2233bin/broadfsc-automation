"""
BroadFSC TikTok Season 3 — Upgraded Video Engine v6

Major upgrades over Season 2:
1. REAL technical charts — matplotlib candlestick + indicators (MA, RSI, trend lines)
2. SENTENCE-level subtitles — whole sentences fade in/out, no word-by-word jitter
3. CHART ANIMATION — indicator lines draw progressively as narrator speaks
4. SPLIT LAYOUT — top 55% = animated chart, bottom 45% = text + subtitles

EP9:  Candlestick Patterns (Hammer, Doji, Engulfing)
EP10: MACD Strategy
EP11: Bollinger Bands
EP12: Volume Analysis
"""

import os
import sys
import asyncio
import datetime
import shutil
import tempfile
import math
import struct
import io
import random

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyArrowPatch
    import imageio.v2 as iio
    HAS_ALL = True
except ImportError as e:
    print(f"Missing dependency: {e}")
    HAS_ALL = False

try:
    import edge_tts
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

# ─────────────────────────────────────────────
# Canvas
# ─────────────────────────────────────────────
W, H    = 1088, 1920
FPS     = 30
CHART_H = int(H * 0.50)   # top 50% = chart
TEXT_H  = H - CHART_H     # bottom 50% = text

# Colours
BG      = (8,  10,  18)
BG2     = (14, 17,  30)
WHITE   = (255, 255, 255)
GRAY    = (130, 145, 175)
ACCENT  = (56,  134, 255)
GREEN   = (0,   214, 130)
RED     = (255,  60,  60)
GOLD    = (255, 196,   0)
DIM     = (50,   58,  85)

TTS_VOICE = "en-US-GuyNeural"
TTS_RATE  = "+8%"

DESKTOP = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")

# ─────────────────────────────────────────────
# Font helper
# ─────────────────────────────────────────────
_FONT_CACHE = {}
def _font(size, bold=True):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial Bold.ttf" if bold else "C:/Windows/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size)
                _FONT_CACHE[key] = f
                return f
            except:
                pass
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f

def _wrap(text, font, max_width, draw):
    words = text.split()
    lines, line = [], []
    for w in words:
        test = " ".join(line + [w])
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            line.append(w)
        else:
            if line:
                lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))
    return lines or [text]

# ─────────────────────────────────────────────
# Synthetic OHLCV generator (realistic random walk)
# ─────────────────────────────────────────────
def _gen_ohlcv(n=60, seed=42, trend=0.003):
    rng = random.Random(seed)
    close = 100.0
    data = []
    for i in range(n):
        o = close
        change = rng.gauss(trend, 0.018)
        c = o * (1 + change)
        hi = max(o, c) * (1 + abs(rng.gauss(0, 0.008)))
        lo = min(o, c) * (1 - abs(rng.gauss(0, 0.008)))
        vol = int(rng.gauss(1_200_000, 300_000))
        data.append({"o": o, "h": hi, "l": lo, "c": c, "v": max(vol, 100_000)})
        close = c
    return data

def _sma(data, n):
    closes = [d["c"] for d in data]
    result = []
    for i in range(len(closes)):
        if i < n - 1:
            result.append(None)
        else:
            result.append(sum(closes[i-n+1:i+1]) / n)
    return result

def _ema(data, n):
    closes = [d["c"] for d in data]
    result = [None] * (n - 1)
    seed_val = sum(closes[:n]) / n
    result.append(seed_val)
    k = 2 / (n + 1)
    for i in range(n, len(closes)):
        result.append(closes[i] * k + result[-1] * (1 - k))
    return result

def _rsi(data, n=14):
    closes = [d["c"] for d in data]
    result = [None] * n
    gains, losses = [], []
    for i in range(1, n + 1):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / n
    avg_loss = sum(losses) / n
    for i in range(n, len(closes)):
        diff = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (n - 1) + max(diff, 0)) / n
        avg_loss = (avg_loss * (n - 1) + max(-diff, 0)) / n
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        result.append(100 - 100 / (1 + rs))
    return result

def _macd(data, fast=12, slow=26, signal=9):
    ema_fast = _ema(data, fast)
    ema_slow = _ema(data, slow)
    macd_line = []
    for f, s in zip(ema_fast, ema_slow):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)
    # signal line = EMA9 of macd_line (on valid values only)
    valid_idx = [i for i, v in enumerate(macd_line) if v is not None]
    if not valid_idx:
        return macd_line, [None]*len(macd_line), [None]*len(macd_line)
    start = valid_idx[0]
    # build signal
    sig_line = [None] * len(macd_line)
    vals = [macd_line[i] for i in valid_idx]
    if len(vals) >= signal:
        ema_sig = [sum(vals[:signal]) / signal]
        k = 2 / (signal + 1)
        for v in vals[signal:]:
            ema_sig.append(v * k + ema_sig[-1] * (1 - k))
        offset = start + signal - 1
        for j, sv in enumerate(ema_sig):
            if offset + j < len(sig_line):
                sig_line[offset + j] = sv
    hist = []
    for m, s in zip(macd_line, sig_line):
        if m is not None and s is not None:
            hist.append(m - s)
        else:
            hist.append(None)
    return macd_line, sig_line, hist

def _bollinger(data, n=20, k=2):
    closes = [d["c"] for d in data]
    mid, upper, lower = [], [], []
    for i in range(len(closes)):
        if i < n - 1:
            mid.append(None); upper.append(None); lower.append(None)
        else:
            window = closes[i-n+1:i+1]
            m = sum(window) / n
            std = math.sqrt(sum((x - m)**2 for x in window) / n)
            mid.append(m)
            upper.append(m + k * std)
            lower.append(m - k * std)
    return mid, upper, lower

# ─────────────────────────────────────────────
# Chart renderers → PIL Image (CHART_H x W)
# ─────────────────────────────────────────────
def _render_chart_candlestick(ohlcv, reveal=1.0, highlight_idx=None, pattern_name=""):
    """Render candlestick chart with optional MA lines. reveal=0..1 draws progressively."""
    dpi = 100
    fig_w = W / dpi
    fig_h = CHART_H / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor('#080A12')
    ax.set_facecolor('#080A12')

    n = max(1, int(len(ohlcv) * reveal))
    sub = ohlcv[:n]
    xs = list(range(n))

    bw = 0.6
    for i, bar in enumerate(sub):
        color = '#00D682' if bar['c'] >= bar['o'] else '#FF3C3C'
        # Body
        ax.bar(i, abs(bar['c'] - bar['o']), bottom=min(bar['o'], bar['c']),
               width=bw, color=color, linewidth=0)
        # Wicks
        ax.plot([i, i], [bar['l'], min(bar['o'], bar['c'])], color=color, linewidth=1)
        ax.plot([i, i], [max(bar['o'], bar['c']), bar['h']], color=color, linewidth=1)

    # MA lines
    ma20 = _sma(ohlcv, 20)
    ma50 = _sma(ohlcv, 50)
    x_ma = list(range(n))
    y20 = [ma20[i] for i in range(n) if ma20[i] is not None]
    x20 = [i for i in range(n) if ma20[i] is not None]
    y50 = [ma50[i] for i in range(n) if ma50[i] is not None]
    x50 = [i for i in range(n) if ma50[i] is not None]
    if x20: ax.plot(x20, y20, color='#3886FF', linewidth=1.8, label='MA20', zorder=3)
    if x50: ax.plot(x50, y50, color='#FFC400', linewidth=1.8, label='MA50', zorder=3)

    # Highlight pattern candles (last 1-3 bars)
    if highlight_idx is not None and reveal >= 0.95:
        for hi in highlight_idx:
            if hi < n:
                bar = sub[hi]
                ax.add_patch(plt.Rectangle((hi - 0.5, bar['l']),
                                           1, bar['h'] - bar['l'],
                                           fill=False, edgecolor='#FFC400', linewidth=2, zorder=5))

    ax.set_xlim(-1, len(ohlcv))
    all_lows  = [b['l'] for b in sub]
    all_highs = [b['h'] for b in sub]
    pad = (max(all_highs) - min(all_lows)) * 0.1
    ax.set_ylim(min(all_lows) - pad, max(all_highs) + pad)

    ax.tick_params(colors='#828fa0', labelsize=8)
    ax.spines['bottom'].set_color('#1E2133')
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_color('#1E2133')
    ax.spines['right'].set_visible(False)
    ax.yaxis.label.set_color('#828fa0')
    ax.set_xticks([])

    # Legend
    if x20 and x50:
        leg = ax.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white', fontsize=9)

    # Pattern label
    if pattern_name and reveal >= 0.9:
        ax.text(n * 0.98, max(all_highs) + pad * 0.5, pattern_name,
                ha='right', va='top', color='#FFC400', fontsize=11, fontweight='bold',
                transform=ax.transData)

    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='#080A12', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert('RGB').resize((W, CHART_H), Image.LANCZOS)
    return img


def _render_chart_rsi(ohlcv, reveal=1.0):
    dpi = 100
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W/dpi, CHART_H/dpi), dpi=dpi,
                                   gridspec_kw={'height_ratios': [2, 1], 'hspace': 0.05})
    for ax in [ax1, ax2]:
        ax.set_facecolor('#080A12')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#1E2133')
        ax.spines['left'].set_color('#1E2133')
        ax.tick_params(colors='#828fa0', labelsize=8)
    fig.patch.set_facecolor('#080A12')

    n = max(1, int(len(ohlcv) * reveal))
    sub = ohlcv[:n]
    xs = list(range(n))
    closes = [d['c'] for d in sub]
    ax1.plot(xs, closes, color='#3886FF', linewidth=2)
    ax1.fill_between(xs, closes, alpha=0.1, color='#3886FF')
    ax1.set_xlim(-1, len(ohlcv)); ax1.set_xticks([])
    ax1.set_ylabel('Price', color='#828fa0', fontsize=9)

    rsi_full = _rsi(ohlcv, 14)
    rsi_vals = [rsi_full[i] for i in range(n) if rsi_full[i] is not None]
    rsi_xs   = [i for i in range(n) if rsi_full[i] is not None]
    if rsi_xs:
        ax2.plot(rsi_xs, rsi_vals, color='#A855F7', linewidth=2, label='RSI 14')
        ax2.axhline(70, color='#FF3C3C', linewidth=1, linestyle='--', alpha=0.8)
        ax2.axhline(30, color='#00D682', linewidth=1, linestyle='--', alpha=0.8)
        ax2.fill_between(rsi_xs, rsi_vals, 70,
                         where=[v > 70 for v in rsi_vals], alpha=0.25, color='#FF3C3C')
        ax2.fill_between(rsi_xs, rsi_vals, 30,
                         where=[v < 30 for v in rsi_vals], alpha=0.25, color='#00D682')
        ax2.text(len(ohlcv)*0.98, 71, 'Overbought 70', ha='right', va='bottom',
                 color='#FF3C3C', fontsize=8)
        ax2.text(len(ohlcv)*0.98, 29, 'Oversold 30', ha='right', va='top',
                 color='#00D682', fontsize=8)
    ax2.set_xlim(-1, len(ohlcv))
    ax2.set_ylim(0, 100)
    ax2.set_ylabel('RSI', color='#828fa0', fontsize=9)
    ax2.set_xticks([])

    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='#080A12', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGB').resize((W, CHART_H), Image.LANCZOS)


def _render_chart_macd(ohlcv, reveal=1.0):
    dpi = 100
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W/dpi, CHART_H/dpi), dpi=dpi,
                                   gridspec_kw={'height_ratios': [2, 1], 'hspace': 0.05})
    for ax in [ax1, ax2]:
        ax.set_facecolor('#080A12')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#1E2133'); ax.spines['left'].set_color('#1E2133')
        ax.tick_params(colors='#828fa0', labelsize=8)
    fig.patch.set_facecolor('#080A12')

    n = max(1, int(len(ohlcv) * reveal))
    sub = ohlcv[:n]
    xs = list(range(n))
    closes = [d['c'] for d in sub]
    ax1.plot(xs, closes, color='#3886FF', linewidth=2)
    ax1.fill_between(xs, closes, alpha=0.08, color='#3886FF')
    ax1.set_xlim(-1, len(ohlcv)); ax1.set_xticks([])
    ax1.set_ylabel('Price', color='#828fa0', fontsize=9)

    macd_f, sig_f, hist_f = _macd(ohlcv)
    macd_v = [macd_f[i] for i in range(n) if macd_f[i] is not None]
    macd_x = [i for i in range(n) if macd_f[i] is not None]
    sig_v  = [sig_f[i] for i in range(n) if sig_f[i] is not None]
    sig_x  = [i for i in range(n) if sig_f[i] is not None]
    hist_v = [hist_f[i] for i in range(n) if hist_f[i] is not None]
    hist_x = [i for i in range(n) if hist_f[i] is not None]

    if macd_x: ax2.plot(macd_x, macd_v, color='#3886FF', linewidth=2, label='MACD')
    if sig_x:  ax2.plot(sig_x, sig_v,   color='#FFC400', linewidth=2, label='Signal')
    if hist_x:
        colors = ['#00D682' if v >= 0 else '#FF3C3C' for v in hist_v]
        ax2.bar(hist_x, hist_v, color=colors, alpha=0.7, width=0.8)
    ax2.axhline(0, color='#828fa0', linewidth=0.8, linestyle='--')
    ax2.set_xlim(-1, len(ohlcv)); ax2.set_xticks([])
    ax2.set_ylabel('MACD', color='#828fa0', fontsize=9)
    if macd_x:
        leg = ax2.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white', fontsize=8)

    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='#080A12', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGB').resize((W, CHART_H), Image.LANCZOS)


def _render_chart_bollinger(ohlcv, reveal=1.0):
    dpi = 100
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W/dpi, CHART_H/dpi), dpi=dpi,
                                   gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.05})
    for ax in [ax1, ax2]:
        ax.set_facecolor('#080A12')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#1E2133'); ax.spines['left'].set_color('#1E2133')
        ax.tick_params(colors='#828fa0', labelsize=8)
    fig.patch.set_facecolor('#080A12')

    n = max(1, int(len(ohlcv) * reveal))
    sub = ohlcv[:n]
    xs = list(range(n))
    closes = [d['c'] for d in sub]
    mid, upper, lower = _bollinger(ohlcv, 20)
    mid_v   = [mid[i]   for i in range(n) if mid[i] is not None]
    upper_v = [upper[i] for i in range(n) if upper[i] is not None]
    lower_v = [lower[i] for i in range(n) if lower[i] is not None]
    bb_x    = [i for i in range(n) if mid[i] is not None]

    ax1.plot(xs, closes, color='#3886FF', linewidth=2, label='Price', zorder=3)
    if bb_x:
        ax1.plot(bb_x, mid_v,   color='#FFC400', linewidth=1.5, linestyle='--', label='BB Mid')
        ax1.plot(bb_x, upper_v, color='#A855F7', linewidth=1.5, label='Upper Band')
        ax1.plot(bb_x, lower_v, color='#A855F7', linewidth=1.5, label='Lower Band')
        ax1.fill_between(bb_x, lower_v, upper_v, alpha=0.08, color='#A855F7')
    ax1.set_xlim(-1, len(ohlcv)); ax1.set_xticks([])
    leg = ax1.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white', fontsize=8, ncol=2)

    # Volume bars
    vols = [d['v'] for d in sub]
    v_colors = ['#00D682' if sub[i]['c'] >= sub[i]['o'] else '#FF3C3C' for i in range(n)]
    ax2.bar(xs, vols, color=v_colors, alpha=0.7, width=0.8)
    ax2.set_xlim(-1, len(ohlcv)); ax2.set_xticks([])
    ax2.set_ylabel('Vol', color='#828fa0', fontsize=8)

    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='#080A12', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGB').resize((W, CHART_H), Image.LANCZOS)


def _render_chart_volume(ohlcv, reveal=1.0):
    dpi = 100
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W/dpi, CHART_H/dpi), dpi=dpi,
                                   gridspec_kw={'height_ratios': [2, 1], 'hspace': 0.05})
    for ax in [ax1, ax2]:
        ax.set_facecolor('#080A12')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#1E2133'); ax.spines['left'].set_color('#1E2133')
        ax.tick_params(colors='#828fa0', labelsize=8)
    fig.patch.set_facecolor('#080A12')

    n = max(1, int(len(ohlcv) * reveal))
    sub = ohlcv[:n]
    xs  = list(range(n))

    bw = 0.6
    for i, bar in enumerate(sub):
        color = '#00D682' if bar['c'] >= bar['o'] else '#FF3C3C'
        ax1.bar(i, abs(bar['c']-bar['o']), bottom=min(bar['o'],bar['c']),
                width=bw, color=color, linewidth=0)
        ax1.plot([i,i],[bar['l'],min(bar['o'],bar['c'])], color=color, linewidth=1)
        ax1.plot([i,i],[max(bar['o'],bar['c']),bar['h']], color=color, linewidth=1)
    ax1.set_xlim(-1, len(ohlcv)); ax1.set_xticks([])

    vols   = [d['v'] for d in sub]
    vma20  = _sma([{'c': d['v']} for d in sub], min(20, n))
    v_colors = ['#00D682' if sub[i]['c']>=sub[i]['o'] else '#FF3C3C' for i in range(n)]
    ax2.bar(xs, vols, color=v_colors, alpha=0.65, width=0.8, label='Volume')
    vma_v = [vma20[i] for i in range(n) if vma20[i] is not None]
    vma_x = [i for i in range(n) if vma20[i] is not None]
    if vma_x:
        ax2.plot(vma_x, vma_v, color='#FFC400', linewidth=2, label='Vol MA20')
    ax2.set_xlim(-1, len(ohlcv)); ax2.set_xticks([])
    ax2.set_ylabel('Volume', color='#828fa0', fontsize=8)
    if vma_x:
        leg = ax2.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white', fontsize=8)

    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='#080A12', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGB').resize((W, CHART_H), Image.LANCZOS)


# ─────────────────────────────────────────────
# Text panel renderer (bottom half)
# ─────────────────────────────────────────────
def _render_text_panel(scene_text, subtitle_text, scene_idx, total_scenes,
                       is_hook=False, is_cta=False, sub_alpha=1.0, ep_num=0):
    """Render the bottom text panel."""
    img = Image.new('RGB', (W, TEXT_H), BG2)
    draw = ImageDraw.Draw(img)

    # Top divider line
    draw.rectangle([(0, 0), (W, 3)], fill=ACCENT)

    # Brand pill top-right
    bfont = _font(22, bold=True)
    bt = "BroadFSC"
    bw = draw.textbbox((0, 0), bt, font=bfont)[2]
    bx = W - bw - 52
    draw.rounded_rectangle((bx-12, 18, bx+bw+12, 52), radius=12, fill=ACCENT)
    draw.text((bx + bw//2, 35), bt, font=bfont, fill=WHITE, anchor="mm")

    # Scene progress dots
    dot_y = 72
    dot_r = 7
    dot_gap = 22
    total_dots = total_scenes
    dots_w = total_dots * dot_r * 2 + (total_dots - 1) * dot_gap
    dx = (W - dots_w) // 2
    for di in range(total_dots):
        cx = dx + di * (dot_r * 2 + dot_gap) + dot_r
        if di < scene_idx:
            draw.ellipse((cx-dot_r, dot_y-dot_r, cx+dot_r, dot_y+dot_r), fill=ACCENT)
        elif di == scene_idx:
            draw.ellipse((cx-dot_r-2, dot_y-dot_r-2, cx+dot_r+2, dot_y+dot_r+2), fill=GOLD)
        else:
            draw.ellipse((cx-dot_r, dot_y-dot_r, cx+dot_r, dot_y+dot_r), fill=DIM)

    # Main scene text
    if is_hook:
        font_main = _font(72, bold=True)
        lines = _wrap(scene_text, font_main, W - 80, draw)
        lh = 90
        total_th = len(lines) * lh
        y = (TEXT_H - total_th) // 2 - 20
        for line in lines:
            draw.text((W//2, y), line, font=font_main, fill=WHITE, anchor="mm")
            y += lh
        # Accent underline
        draw.rectangle([(W//2 - 140, y + 8), (W//2 + 140, y + 14)], fill=GOLD)
    elif is_cta:
        font_cta = _font(54, bold=True)
        lines = _wrap(scene_text, font_cta, W - 80, draw)
        lh = 70
        total_th = len(lines) * lh
        y = 110
        for line in lines:
            draw.text((W//2, y), line, font=font_cta, fill=GREEN, anchor="mm")
            y += lh
        # Website pill
        url = "broadfsc.com/different"
        uf = _font(28, bold=False)
        uw = draw.textbbox((0, 0), url, font=uf)[2]
        ux = (W - uw) // 2
        draw.rounded_rectangle((ux-16, y+24, ux+uw+16, y+64), radius=14, fill=DIM)
        draw.text((W//2, y+44), url, font=uf, fill=GRAY, anchor="mm")
    else:
        font_main = _font(58, bold=True)
        lines = _wrap(scene_text, font_main, W - 80, draw)
        lh = 76
        total_th = len(lines) * lh
        y = 105
        for line in lines:
            draw.text((W//2, y), line, font=font_main, fill=WHITE, anchor="mm")
            y += lh

    # ── SENTENCE-LEVEL SUBTITLE (bottom of text panel) ──────
    if subtitle_text and sub_alpha > 0.01:
        sfont = _font(36, bold=False)
        slines = _wrap(subtitle_text, sfont, W - 80, draw)
        sub_y = TEXT_H - 120 - (len(slines) - 1) * 48

        # Background bar
        bar_top = sub_y - 14
        bar_bot = sub_y + len(slines) * 48 + 14
        sub_overlay = Image.new('RGBA', (W, TEXT_H), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(sub_overlay)
        ov_draw.rounded_rectangle(
            [(30, bar_top), (W-30, bar_bot)],
            radius=12, fill=(0, 0, 0, int(180 * sub_alpha))
        )
        img_rgba = img.convert('RGBA')
        img_rgba = Image.alpha_composite(img_rgba, sub_overlay)
        img = img_rgba.convert('RGB')
        draw = ImageDraw.Draw(img)

        for sl in slines:
            alpha_col = tuple(int(c * sub_alpha) for c in WHITE)
            draw.text((W//2, sub_y), sl, font=sfont, fill=alpha_col, anchor="mm")
            sub_y += 48

    return img


# ─────────────────────────────────────────────
# Compose full frame
# ─────────────────────────────────────────────
def _compose_frame(chart_img, text_img):
    frame = Image.new('RGB', (W, H), BG)
    frame.paste(chart_img, (0, 0))
    frame.paste(text_img, (0, CHART_H))
    return np.array(frame)


# ─────────────────────────────────────────────
# TTS with sentence boundary timing
# ─────────────────────────────────────────────
async def _gen_tts_sentence(text, out_path):
    """Generate TTS and return sentence-level timing (sec)."""
    if not HAS_TTS:
        return out_path, 3.0
    comm = edge_tts.Communicate(text, voice=TTS_VOICE, rate=TTS_RATE)
    await comm.save(out_path)
    # Estimate duration from file size (rough: ~32kbps mp3)
    if os.path.exists(out_path):
        size_bytes = os.path.getsize(out_path)
        duration = size_bytes / (32_000 / 8)  # 32kbps
        return out_path, max(2.0, duration)
    return out_path, len(text.split()) * 0.35


async def _gen_all_tts(sentences, tmp_dir):
    """Generate all TTS clips, return [(text, path, duration)]."""
    results = []
    for i, txt in enumerate(sentences):
        path = os.path.join(tmp_dir, f"tts_{i:02d}.mp3")
        _, dur = await _gen_tts_sentence(txt, path)
        results.append((txt, path, dur))
        print(f"  TTS {i+1}/{len(sentences)}: {dur:.1f}s — {txt[:50]}")
    return results


# ─────────────────────────────────────────────
# Audio mixer (pure Python WAV concat)
# ─────────────────────────────────────────────
def _mp3_to_pcm(path):
    """Use ffmpeg to decode mp3 → raw PCM s16le 44100 stereo."""
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = 'ffmpeg'
    cmd = [ffmpeg_exe, '-y', '-i', path, '-f', 's16le', '-acodec', 'pcm_s16le',
           '-ar', '44100', '-ac', '2', 'pipe:1']
    result = subprocess.run(cmd, capture_output=True)
    return result.stdout  # raw bytes

def _build_audio_concat(tts_clips, gap_sec=0.4, sr=44100, channels=2):
    """Concatenate PCM clips with silence gaps, return WAV bytes."""
    gap_samples = int(gap_sec * sr)
    gap_bytes = b'\x00' * (gap_samples * channels * 2)
    all_pcm = b''
    durations = []
    t = 0.0
    for text, path, est_dur in tts_clips:
        pcm = _mp3_to_pcm(path)
        dur = len(pcm) / (sr * channels * 2)
        durations.append((t, dur))
        all_pcm += pcm + gap_bytes
        t += dur + gap_sec
    total_dur = t
    # Wrap in WAV
    num_samples = len(all_pcm) // (channels * 2)
    wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(all_pcm), b'WAVE',
        b'fmt ', 16, 1, channels, sr, sr * channels * 2,
        channels * 2, 16, b'data', len(all_pcm))
    return wav_header + all_pcm, durations, total_dur


# ─────────────────────────────────────────────
# Episode definition
# ─────────────────────────────────────────────
EPISODES = [
    # ── EP9: Candlestick Patterns ───────────────────────────
    {
        "ep": 9,
        "title": "Candlestick Patterns",
        "chart_fn": lambda ohlcv, reveal: _render_chart_candlestick(
            ohlcv, reveal=reveal,
            highlight_idx=[-3, -2, -1],
            pattern_name="Bullish Engulfing"
        ),
        "ohlcv_seed": 7,
        "ohlcv_trend": 0.001,
        "scenes": [
            {
                "text": "One candle can change everything.",
                "subtitle": "Candlestick patterns are your edge.",
                "is_hook": True,
                "duration": 3.5,
            },
            {
                "text": "The HAMMER signals reversal after a downtrend.",
                "subtitle": "Small body, long lower wick — buyers fought back.",
                "duration": 5.5,
            },
            {
                "text": "The DOJI means indecision.",
                "subtitle": "Open and close are almost equal. A shift is coming.",
                "duration": 5.0,
            },
            {
                "text": "BULLISH ENGULFING is the most reliable pattern.",
                "subtitle": "A big green candle swallows the previous red one.",
                "duration": 5.5,
            },
            {
                "text": "Never trade patterns alone.",
                "subtitle": "Confirm with volume. High volume = real conviction.",
                "duration": 5.0,
            },
            {
                "text": "Follow for daily chart breakdowns.\nbroasfsc.com/different",
                "subtitle": "",
                "is_cta": True,
                "duration": 4.0,
            },
        ]
    },

    # ── EP10: MACD Strategy ─────────────────────────────────
    {
        "ep": 10,
        "title": "MACD Strategy",
        "chart_fn": lambda ohlcv, reveal: _render_chart_macd(ohlcv, reveal=reveal),
        "ohlcv_seed": 13,
        "ohlcv_trend": 0.004,
        "scenes": [
            {
                "text": "MACD tells you when momentum is shifting.",
                "subtitle": "Before the price moves — the indicator already knows.",
                "is_hook": True,
                "duration": 4.0,
            },
            {
                "text": "MACD = Fast EMA minus Slow EMA.",
                "subtitle": "Default: 12-day EMA minus 26-day EMA.",
                "duration": 5.0,
            },
            {
                "text": "The SIGNAL LINE is a 9-day EMA of MACD.",
                "subtitle": "When MACD crosses above Signal — momentum is turning bullish.",
                "duration": 6.0,
            },
            {
                "text": "Green histogram bars = bullish momentum building.",
                "subtitle": "Red bars = bears taking control. Size matters.",
                "duration": 5.5,
            },
            {
                "text": "Best entry: MACD crosses zero from below.",
                "subtitle": "Combined with a strong price breakout, this is powerful.",
                "duration": 5.5,
            },
            {
                "text": "Trade smarter. Follow BroadFSC.",
                "subtitle": "",
                "is_cta": True,
                "duration": 4.0,
            },
        ]
    },

    # ── EP11: Bollinger Bands ───────────────────────────────
    {
        "ep": 11,
        "title": "Bollinger Bands",
        "chart_fn": lambda ohlcv, reveal: _render_chart_bollinger(ohlcv, reveal=reveal),
        "ohlcv_seed": 21,
        "ohlcv_trend": -0.001,
        "scenes": [
            {
                "text": "When the bands squeeze — something big is coming.",
                "subtitle": "Bollinger Bands measure volatility in real time.",
                "is_hook": True,
                "duration": 4.0,
            },
            {
                "text": "Bands = Middle MA ± 2 Standard Deviations.",
                "subtitle": "95% of price action stays inside the bands.",
                "duration": 5.5,
            },
            {
                "text": "SQUEEZE = bands narrow = low volatility.",
                "subtitle": "This silence before the storm is your setup signal.",
                "duration": 5.5,
            },
            {
                "text": "Price touching UPPER band = overbought zone.",
                "subtitle": "But in strong uptrends, it can ride the band higher.",
                "duration": 5.5,
            },
            {
                "text": "The BAND WALK is the most profitable pattern.",
                "subtitle": "Price walks along one band during trending markets.",
                "duration": 5.5,
            },
            {
                "text": "More edge. Follow BroadFSC.",
                "subtitle": "",
                "is_cta": True,
                "duration": 4.0,
            },
        ]
    },

    # ── EP12: Volume Analysis ───────────────────────────────
    {
        "ep": 12,
        "title": "Volume Analysis",
        "chart_fn": lambda ohlcv, reveal: _render_chart_volume(ohlcv, reveal=reveal),
        "ohlcv_seed": 33,
        "ohlcv_trend": 0.002,
        "scenes": [
            {
                "text": "Price without volume is just noise.",
                "subtitle": "Volume is the only true confirmation signal.",
                "is_hook": True,
                "duration": 3.5,
            },
            {
                "text": "HIGH volume on a breakout = real move.",
                "subtitle": "Low volume breakouts fail more than 70% of the time.",
                "duration": 5.5,
            },
            {
                "text": "RISING price + FALLING volume = danger signal.",
                "subtitle": "Smart money is not participating. Exit soon.",
                "duration": 5.5,
            },
            {
                "text": "CLIMAX volume = exhaustion.",
                "subtitle": "Massive spike followed by reversal candle — trend is ending.",
                "duration": 5.5,
            },
            {
                "text": "Volume MA confirms conviction.",
                "subtitle": "Above average volume = institutional interest.",
                "duration": 5.0,
            },
            {
                "text": "Follow for more. broadfsc.com/different",
                "subtitle": "",
                "is_cta": True,
                "duration": 4.0,
            },
        ]
    },
]


# ─────────────────────────────────────────────
# Video generator
# ─────────────────────────────────────────────
async def generate_episode(ep_def, tmp_dir, output_path):
    ep_num = ep_def['ep']
    scenes = ep_def['scenes']
    ohlcv  = _gen_ohlcv(n=60, seed=ep_def['ohlcv_seed'], trend=ep_def['ohlcv_trend'])
    chart_fn = ep_def['chart_fn']

    print(f"\n{'='*58}")
    print(f" EP.{ep_num}: {ep_def['title']}")
    print(f"{'='*58}")

    # 1. Generate TTS for each scene (use scene text + subtitle combined for natural speech)
    tts_texts = []
    for sc in scenes:
        if sc.get('is_cta'):
            tts_texts.append("Follow BroadFSC for more trading education.")
        else:
            spoken = sc['text'].replace('\n', ' ')
            sub = sc.get('subtitle', '')
            if sub:
                spoken = spoken + ". " + sub
            tts_texts.append(spoken)

    print("--- Generating TTS ---")
    tts_clips = await _gen_all_tts(tts_texts, tmp_dir)

    # Use actual TTS durations
    for i, (text, path, dur) in enumerate(tts_clips):
        scenes[i]['duration'] = max(scenes[i].get('duration', 3.5), dur + 0.5)

    total_duration = sum(sc['duration'] for sc in scenes)
    print(f"  Total duration: {total_duration:.1f}s")

    # 2. Build scene timing map
    scene_timings = []
    t = 0.0
    for sc in scenes:
        scene_timings.append({
            "start": t,
            "end": t + sc['duration'],
            "duration": sc['duration'],
            **sc
        })
        t += sc['duration']

    # 3. Build audio (concat mp3s)
    print("--- Building Audio ---")
    audio_wav, clip_timings, _ = _build_audio_concat(tts_clips, gap_sec=0.3)
    # Update scene start times based on actual audio
    for i, (at, dur) in enumerate(clip_timings):
        if i < len(scene_timings):
            scene_timings[i]['audio_start'] = at
            scene_timings[i]['audio_dur'] = dur

    audio_path = os.path.join(tmp_dir, f"ep{ep_num}_audio.wav")
    with open(audio_path, 'wb') as f:
        f.write(audio_wav)
    print(f"  Audio saved: {len(audio_wav)//1024}KB")

    # 4. Pre-render scene text panels (static per scene)
    print("--- Pre-rendering Text Panels ---")
    total_scenes = len(scenes)
    text_panels = []
    for si, st in enumerate(scene_timings):
        panel = _render_text_panel(
            scene_text=st['text'],
            subtitle_text=st.get('subtitle', ''),
            scene_idx=si,
            total_scenes=total_scenes,
            is_hook=st.get('is_hook', False),
            is_cta=st.get('is_cta', False),
            sub_alpha=1.0,
            ep_num=ep_num,
        )
        text_panels.append(panel)
    print(f"  {len(text_panels)} panels pre-rendered")

    # 5. Render frames
    print("--- Rendering Video Frames ---")
    total_frames = int(total_duration * FPS)
    video_path = os.path.join(tmp_dir, f"ep{ep_num}_raw.mp4")

    writer = iio.get_writer(
        video_path, fps=FPS,
        codec='libx264',
        output_params=['-crf', '20', '-preset', 'fast', '-pix_fmt', 'yuv420p']
    )

    # Pre-render chart frames at key reveal points to avoid per-frame matplotlib calls
    # We render one chart per scene (chart reveal progresses with scenes)
    chart_cache = {}
    for si in range(total_scenes):
        reveal = (si + 1) / total_scenes
        ci = chart_fn(ohlcv, reveal)
        chart_cache[si] = ci
        if si % 2 == 0:
            print(f"  Chart {si+1}/{total_scenes} rendered")

    for fi in range(total_frames):
        t = fi / FPS

        # Find active scene
        active_si = 0
        for si, st in enumerate(scene_timings):
            if st['start'] <= t < st['end']:
                active_si = si
                break
        else:
            active_si = total_scenes - 1

        st = scene_timings[active_si]
        scene_t = t - st['start']
        scene_frac = scene_t / st['duration']

        # Subtitle fade (fade in first 0.3s, fade out last 0.3s)
        fade_dur = 0.3
        if scene_t < fade_dur:
            sub_alpha = scene_t / fade_dur
        elif scene_t > st['duration'] - fade_dur:
            sub_alpha = (st['duration'] - scene_t) / fade_dur
        else:
            sub_alpha = 1.0
        sub_alpha = max(0.0, min(1.0, sub_alpha))

        chart_img = chart_cache[active_si]

        # Rebuild text panel with current sub_alpha (only when fading)
        if abs(sub_alpha - 1.0) > 0.01:
            text_img = _render_text_panel(
                scene_text=st['text'],
                subtitle_text=st.get('subtitle', ''),
                scene_idx=active_si,
                total_scenes=total_scenes,
                is_hook=st.get('is_hook', False),
                is_cta=st.get('is_cta', False),
                sub_alpha=sub_alpha,
                ep_num=ep_num,
            )
        else:
            text_img = text_panels[active_si]

        frame = _compose_frame(chart_img, text_img)
        writer.append_data(frame)

        if fi % (FPS * 5) == 0:
            print(f"  Frame {fi}/{total_frames} ({t:.1f}s)")

    writer.close()
    print(f"  Video frames done: {video_path}")

    # 6. Mux audio + video with ffmpeg
    print("--- Muxing Audio + Video ---")
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = 'ffmpeg'
    cmd = [
        ffmpeg_exe, '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '192k',
        '-map', '0:v:0', '-map', '1:a:0',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFMPEG error: {result.stderr[-500:]}")
        # fallback: copy video without audio
        shutil.copy2(video_path, output_path)
    else:
        print(f"  Mux complete!")

    size_kb = os.path.getsize(output_path) // 1024 if os.path.exists(output_path) else 0
    print(f"  EP.{ep_num} done: {output_path} ({size_kb}KB)")
    return output_path


async def main():
    if not HAS_ALL:
        print("ERROR: Missing dependencies (numpy/PIL/matplotlib/imageio)")
        return
    if not HAS_TTS:
        print("WARNING: edge_tts not available — video will have no audio")

    print("=" * 58)
    print(" BroadFSC TikTok Season 3 — EP9-EP12")
    print(" Upgraded: Real Charts + Sentence Subtitles")
    print("=" * 58)

    tmp_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_s3_cache")
    os.makedirs(tmp_root, exist_ok=True)

    for ep_def in EPISODES:
        ep_num = ep_def['ep']
        ep_dir = os.path.join(tmp_root, f"ep{ep_num}")
        os.makedirs(ep_dir, exist_ok=True)
        out_path = os.path.join(DESKTOP, f"tiktok_ep{ep_num}_final.mp4")
        try:
            await generate_episode(ep_def, ep_dir, out_path)
        except Exception as e:
            import traceback
            print(f"  EP.{ep_num} FAILED: {e}")
            traceback.print_exc()

    # Cleanup
    try:
        shutil.rmtree(tmp_root, ignore_errors=True)
    except:
        pass

    print("\n" + "=" * 58)
    print(" DONE — Check your Desktop for EP9-EP12 videos!")
    print("=" * 58)


if __name__ == "__main__":
    asyncio.run(main())
