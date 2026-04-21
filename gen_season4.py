"""
BroadFSC TikTok Season 4 — Professional Financial Education Video Engine v7

KEY UPGRADES over Season 3:
1. CHART-AS-HERO — Full-screen chart with glassmorphism text overlay (not 50/50 split)
2. ANNOTATED CHARTS — Arrows, circles, highlight boxes pointing to EXACT chart features being discussed
3. DYNAMIC SUBTITLES — Smooth typewriter with word-by-word reveal + glassmorphism backdrop
4. SCENE-DRIVEN CHART ANIMATION — Each scene reveals new chart elements with annotations
5. CINEMATIC TRANSITIONS — Smooth fade/dissolve between scenes
6. PROPER PACING — Hook(3s) → Teach(4 scenes × 5s) → CTA(3s) ≈ 26s optimal TikTok

EP9:  Candlestick Patterns (Hammer, Doji, Engulfing)
EP10: MACD Strategy
EP11: Bollinger Bands
EP12: Volume Analysis
"""

import os
import sys
import asyncio
import shutil
import tempfile
import math
import struct
import io
import random

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    import matplotlib.patheffects as pe
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
# Canvas — Full 1080x1920 TikTok
# ─────────────────────────────────────────────
W, H = 1088, 1920
FPS   = 30

# Color Palette — Professional dark trading UI
BG         = (8,   10,  18)
BG_GLASS   = (12,  15,  28, 180)  # RGBA for glassmorphism
WHITE      = (255, 255, 255)
GRAY       = (160, 175, 200)
DIM_GRAY   = (80,  90,  110)
ACCENT     = (56,  134, 255)
GREEN      = (0,   214, 130)
RED        = (255, 60,  60)
GOLD       = (255, 196, 0)
PURPLE     = (168, 85,  247)
DIM        = (40,  48,  70)

TTS_VOICE = "en-US-GuyNeural"
TTS_RATE  = "+5%"

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
# Glassmorphism helper
# ─────────────────────────────────────────────
def _draw_glass_panel(img, box, radius=20, alpha=170, border_color=(255,255,255,30)):
    """Draw a glassmorphism panel on an RGBA image."""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = box
    # Glass fill
    ov_draw.rounded_rectangle(box, radius=radius, fill=(12, 15, 28, alpha))
    # Border
    ov_draw.rounded_rectangle(box, radius=radius, outline=border_color, width=1)
    # Blur for glass effect
    blurred = overlay.filter(ImageFilter.GaussianBlur(radius=4))
    # Combine: use the blurred version but keep the text-readable center
    result = Image.alpha_composite(img, blurred)
    # Re-draw the border on top (crisp)
    final_draw = ImageDraw.Draw(result)
    final_draw.rounded_rectangle(box, radius=radius, outline=border_color, width=1)
    return result

def _draw_text_on_rgba(img, pos, text, font, fill=(255,255,255,255), anchor="la"):
    """Draw text on an RGBA image."""
    draw = ImageDraw.Draw(img)
    draw.text(pos, text, font=font, fill=fill, anchor=anchor)
    return img


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
    valid_idx = [i for i, v in enumerate(macd_line) if v is not None]
    if not valid_idx:
        return macd_line, [None]*len(macd_line), [None]*len(macd_line)
    start = valid_idx[0]
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
# CHART RENDERERS — Full-screen with annotations
# ─────────────────────────────────────────────
def _render_chart_full(ohlcv, chart_type="candlestick", reveal=1.0,
                       annotations=None, scene_label=""):
    """Render a FULL-HEIGHT chart (W x H) with annotations.

    annotations: list of dicts:
        - type: "circle" | "arrow" | "box" | "label"
        - idx: bar index (0-based)
        - text: label text
        - color: RGB tuple
        - sub_panel: "main" | "sub"  (which panel to annotate)
    """
    dpi = 100
    fig_w = W / dpi
    fig_h = H / dpi

    if chart_type == "candlestick":
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
        fig.patch.set_facecolor('#080A12')
        ax.set_facecolor('#080A12')
        n = max(1, int(len(ohlcv) * reveal))
        sub = ohlcv[:n]
        bw = 0.6
        for i, bar in enumerate(sub):
            color = '#00D682' if bar['c'] >= bar['o'] else '#FF3C3C'
            ax.bar(i, abs(bar['c'] - bar['o']), bottom=min(bar['o'], bar['c']),
                   width=bw, color=color, linewidth=0, alpha=0.95)
            ax.plot([i, i], [bar['l'], min(bar['o'], bar['c'])], color=color, linewidth=1.2)
            ax.plot([i, i], [max(bar['o'], bar['c']), bar['h']], color=color, linewidth=1.2)
        # MA lines
        ma20 = _sma(ohlcv, 20)
        ma50 = _sma(ohlcv, 50)
        x20 = [i for i in range(n) if ma20[i] is not None]
        y20 = [ma20[i] for i in range(n) if ma20[i] is not None]
        x50 = [i for i in range(n) if ma50[i] is not None]
        y50 = [ma50[i] for i in range(n) if ma50[i] is not None]
        if x20: ax.plot(x20, y20, color='#3886FF', linewidth=2, label='MA20', zorder=3)
        if x50: ax.plot(x50, y50, color='#FFC400', linewidth=2, label='MA50', zorder=3)
        ax.set_xlim(-1, len(ohlcv))
        all_lows = [b['l'] for b in sub]; all_highs = [b['h'] for b in sub]
        pad = (max(all_highs) - min(all_lows)) * 0.12
        ax.set_ylim(min(all_lows) - pad, max(all_highs) + pad)
        ax.tick_params(colors='#828fa0', labelsize=9)
        ax.spines['bottom'].set_color('#1E2133'); ax.spines['top'].set_visible(False)
        ax.spines['left'].set_color('#1E2133'); ax.spines['right'].set_visible(False)
        ax.set_xticks([])
        if x20 and x50:
            leg = ax.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white',
                            fontsize=10, loc='upper left',
                            path_effects=[pe.withStroke(linewidth=2, foreground='#080A12')])

    elif chart_type == "macd":
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_w, fig_h), dpi=dpi,
                                        gridspec_kw={'height_ratios': [2.5, 1], 'hspace': 0.08})
        for ax in [ax1, ax2]:
            ax.set_facecolor('#080A12')
            ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#1E2133'); ax.spines['left'].set_color('#1E2133')
            ax.tick_params(colors='#828fa0', labelsize=8)
        fig.patch.set_facecolor('#080A12')
        n = max(1, int(len(ohlcv) * reveal))
        sub = ohlcv[:n]; xs = list(range(n))
        closes = [d['c'] for d in sub]
        ax1.plot(xs, closes, color='#3886FF', linewidth=2.5)
        ax1.fill_between(xs, closes, alpha=0.08, color='#3886FF')
        ax1.set_xlim(-1, len(ohlcv)); ax1.set_xticks([])
        ax1.set_ylabel('Price', color='#828fa0', fontsize=10)
        macd_f, sig_f, hist_f = _macd(ohlcv)
        macd_v = [macd_f[i] for i in range(n) if macd_f[i] is not None]
        macd_x = [i for i in range(n) if macd_f[i] is not None]
        sig_v  = [sig_f[i] for i in range(n) if sig_f[i] is not None]
        sig_x  = [i for i in range(n) if sig_f[i] is not None]
        hist_v = [hist_f[i] for i in range(n) if hist_f[i] is not None]
        hist_x = [i for i in range(n) if hist_f[i] is not None]
        if macd_x: ax2.plot(macd_x, macd_v, color='#3886FF', linewidth=2.5, label='MACD')
        if sig_x:  ax2.plot(sig_x, sig_v,   color='#FFC400', linewidth=2.5, label='Signal')
        if hist_x:
            colors = ['#00D682' if v >= 0 else '#FF3C3C' for v in hist_v]
            ax2.bar(hist_x, hist_v, color=colors, alpha=0.7, width=0.8)
        ax2.axhline(0, color='#828fa0', linewidth=0.8, linestyle='--')
        ax2.set_xlim(-1, len(ohlcv)); ax2.set_xticks([])
        ax2.set_ylabel('MACD', color='#828fa0', fontsize=10)
        if macd_x:
            leg = ax2.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white', fontsize=9)
        ax1 = ax1  # annotations target
        ax2 = ax2

    elif chart_type == "bollinger":
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_w, fig_h), dpi=dpi,
                                        gridspec_kw={'height_ratios': [2.5, 1], 'hspace': 0.08})
        for ax in [ax1, ax2]:
            ax.set_facecolor('#080A12')
            ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#1E2133'); ax.spines['left'].set_color('#1E2133')
            ax.tick_params(colors='#828fa0', labelsize=8)
        fig.patch.set_facecolor('#080A12')
        n = max(1, int(len(ohlcv) * reveal))
        sub = ohlcv[:n]; xs = list(range(n))
        closes = [d['c'] for d in sub]
        mid, upper, lower = _bollinger(ohlcv, 20)
        mid_v   = [mid[i]   for i in range(n) if mid[i] is not None]
        upper_v = [upper[i] for i in range(n) if upper[i] is not None]
        lower_v = [lower[i] for i in range(n) if lower[i] is not None]
        bb_x    = [i for i in range(n) if mid[i] is not None]
        ax1.plot(xs, closes, color='#3886FF', linewidth=2.5, label='Price', zorder=3)
        if bb_x:
            ax1.plot(bb_x, mid_v,   color='#FFC400', linewidth=1.8, linestyle='--', label='BB Mid')
            ax1.plot(bb_x, upper_v, color='#A855F7', linewidth=1.8, label='Upper Band')
            ax1.plot(bb_x, lower_v, color='#A855F7', linewidth=1.8, label='Lower Band')
            ax1.fill_between(bb_x, lower_v, upper_v, alpha=0.08, color='#A855F7')
        ax1.set_xlim(-1, len(ohlcv)); ax1.set_xticks([])
        leg = ax1.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white', fontsize=9, ncol=2)
        vols = [d['v'] for d in sub]
        v_colors = ['#00D682' if sub[i]['c'] >= sub[i]['o'] else '#FF3C3C' for i in range(n)]
        ax2.bar(xs, vols, color=v_colors, alpha=0.7, width=0.8)
        ax2.set_xlim(-1, len(ohlcv)); ax2.set_xticks([])
        ax2.set_ylabel('Vol', color='#828fa0', fontsize=8)

    elif chart_type == "volume":
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_w, fig_h), dpi=dpi,
                                        gridspec_kw={'height_ratios': [2.5, 1], 'hspace': 0.08})
        for ax in [ax1, ax2]:
            ax.set_facecolor('#080A12')
            ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#1E2133'); ax.spines['left'].set_color('#1E2133')
            ax.tick_params(colors='#828fa0', labelsize=8)
        fig.patch.set_facecolor('#080A12')
        n = max(1, int(len(ohlcv) * reveal))
        sub = ohlcv[:n]; xs = list(range(n))
        bw = 0.6
        for i, bar in enumerate(sub):
            color = '#00D682' if bar['c'] >= bar['o'] else '#FF3C3C'
            ax1.bar(i, abs(bar['c']-bar['o']), bottom=min(bar['o'],bar['c']),
                    width=bw, color=color, linewidth=0, alpha=0.95)
            ax1.plot([i,i],[bar['l'],min(bar['o'],bar['c'])], color=color, linewidth=1.2)
            ax1.plot([i,i],[max(bar['o'],bar['c']),bar['h']], color=color, linewidth=1.2)
        ax1.set_xlim(-1, len(ohlcv)); ax1.set_xticks([])
        vols = [d['v'] for d in sub]
        vma20 = _sma([{'c': d['v']} for d in sub], min(20, n))
        v_colors = ['#00D682' if sub[i]['c']>=sub[i]['o'] else '#FF3C3C' for i in range(n)]
        ax2.bar(xs, vols, color=v_colors, alpha=0.65, width=0.8, label='Volume')
        vma_v = [vma20[i] for i in range(n) if vma20[i] is not None]
        vma_x = [i for i in range(n) if vma20[i] is not None]
        if vma_x:
            ax2.plot(vma_x, vma_v, color='#FFC400', linewidth=2.5, label='Vol MA20')
        ax2.set_xlim(-1, len(ohlcv)); ax2.set_xticks([])
        ax2.set_ylabel('Volume', color='#828fa0', fontsize=8)
        if vma_x:
            leg = ax2.legend(facecolor='#0E111E', edgecolor='#1E2133', labelcolor='white', fontsize=9)

    # ── Apply annotations ──
    if annotations:
        # Determine target axes
        if chart_type == "candlestick":
            axes_list = [ax]
        else:
            axes_list = [ax1, ax2]

        for ann in annotations:
            target_ax = axes_list[0] if ann.get('sub_panel', 'main') == 'main' else axes_list[-1]
            idx = ann['idx']
            if idx >= n:
                continue
            atype = ann['type']
            ann_color = ann.get('color', '#FFC400')
            text = ann.get('text', '')

            if atype == 'circle':
                # Get bar data for y position
                if chart_type == "candlestick" or ann.get('sub_panel') == 'main':
                    bar = sub[idx] if idx < len(sub) else sub[-1]
                    y_pos = (bar['h'] + bar['l']) / 2
                    radius = (bar['h'] - bar['l']) * 0.8
                else:
                    # For sub-panel indicators
                    if chart_type == "macd" and idx < len(hist_v):
                        y_pos = hist_v[hist_x.index(idx)] if idx in hist_x else 0
                        radius = abs(y_pos) * 0.5 + 0.1
                    else:
                        y_pos = 0
                        radius = 0.5
                circle = plt.Circle((idx, y_pos), radius,
                                   fill=False, edgecolor=ann_color, linewidth=3, zorder=10)
                target_ax.add_patch(circle)
                if text:
                    target_ax.text(idx, y_pos + radius * 1.3, text,
                                  ha='center', va='bottom', color=ann_color,
                                  fontsize=12, fontweight='bold',
                                  path_effects=[pe.withStroke(linewidth=3, foreground='#080A12')],
                                  zorder=11)

            elif atype == 'arrow':
                # Arrow pointing down to the bar
                if chart_type == "candlestick" or ann.get('sub_panel') == 'main':
                    bar = sub[idx] if idx < len(sub) else sub[-1]
                    y_to = bar['h'] + (bar['h'] - bar['l']) * 0.1
                    y_from = y_to + (max(all_highs) - min(all_lows)) * 0.15
                else:
                    y_to = 0.5
                    y_from = 1.0
                target_ax.annotate(text if text else '',
                                  xy=(idx, y_to), xytext=(idx, y_from),
                                  ha='center',
                                  arrowprops=dict(arrowstyle='->', color=ann_color, lw=2.5),
                                  fontsize=12, fontweight='bold', color=ann_color,
                                  path_effects=[pe.withStroke(linewidth=3, foreground='#080A12')],
                                  zorder=11)

            elif atype == 'box':
                # Highlight a range of bars
                idx_end = ann.get('idx_end', idx + 2)
                if chart_type == "candlestick" or ann.get('sub_panel') == 'main':
                    bars_in_box = [sub[i] for i in range(idx, min(idx_end+1, n))]
                    if bars_in_box:
                        y_lo = min(b['l'] for b in bars_in_box)
                        y_hi = max(b['h'] for b in bars_in_box)
                        pad_y = (y_hi - y_lo) * 0.15
                        rect = plt.Rectangle((idx - 0.5, y_lo - pad_y),
                                            idx_end - idx + 1, y_hi - y_lo + 2*pad_y,
                                            fill=False, edgecolor=ann_color, linewidth=2.5,
                                            linestyle='--', zorder=10)
                        target_ax.add_patch(rect)
                        if text:
                            target_ax.text((idx + idx_end) / 2, y_hi + pad_y * 1.5, text,
                                          ha='center', va='bottom', color=ann_color,
                                          fontsize=11, fontweight='bold',
                                          path_effects=[pe.withStroke(linewidth=3, foreground='#080A12')],
                                          zorder=11)

            elif atype == 'hline':
                # Horizontal line with label
                y_val = ann['y_val']
                target_ax.axhline(y_val, color=ann_color, linewidth=2, linestyle='--', alpha=0.9, zorder=8)
                if text:
                    target_ax.text(len(ohlcv) * 0.98, y_val, text,
                                  ha='right', va='bottom', color=ann_color, fontsize=10,
                                  path_effects=[pe.withStroke(linewidth=2, foreground='#080A12')],
                                  zorder=11)

            elif atype == 'label':
                # Just a text label at position
                y_val = ann.get('y_val', 0)
                target_ax.text(idx, y_val, text,
                              ha='center', va='bottom', color=ann_color,
                              fontsize=12, fontweight='bold',
                              path_effects=[pe.withStroke(linewidth=3, foreground='#080A12')],
                              zorder=11)

    # ── Scene label (top-left) ──
    if scene_label:
        fig.text(0.04, 0.96, scene_label,
                ha='left', va='top', color='#FFC400', fontsize=16, fontweight='bold',
                path_effects=[pe.withStroke(linewidth=4, foreground='#080A12')],
                transform=fig.transFigure)

    fig.tight_layout(pad=0.5)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='#080A12', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGB').resize((W, H), Image.LANCZOS)


# ─────────────────────────────────────────────
# Text overlay compositor (glassmorphism on top of chart)
# ─────────────────────────────────────────────
def _compose_overlay(chart_img, overlay_config):
    """Add glassmorphism text overlays on top of the chart image.

    overlay_config: dict with:
        - title: str (main heading, big text)
        - subtitle: str (smaller explanation)
        - subtitle_progress: float 0..1 (typewriter progress for subtitle)
        - brand: bool (show BroadFSC branding)
        - cta: bool (show CTA)
        - scene_idx: int
        - total_scenes: int
        - hook: bool (is this the hook scene)
        - alpha: float (overall scene fade 0..1)
    """
    frame = chart_img.convert('RGBA')
    draw = ImageDraw.Draw(frame)

    alpha = overlay_config.get('alpha', 1.0)
    if alpha < 0.01:
        return chart_img

    # ── Top bar: Brand + Episode tag ──
    if overlay_config.get('brand', True):
        # Glassmorphism top bar
        top_bar_h = 80
        frame = _draw_glass_panel(frame, (0, 0, W, top_bar_h), radius=0, alpha=140)

        bfont = _font(24, bold=True)
        draw = ImageDraw.Draw(frame)
        draw.text((24, top_bar_h // 2), "BroadFSC", font=bfont, fill=(255,255,255,int(255*alpha)), anchor="lm")

        # Episode tag
        ep_text = overlay_config.get('ep_tag', '')
        if ep_text:
            ef = _font(18, bold=False)
            ew = draw.textbbox((0,0), ep_text, font=ef)[2]
            pill_x = W - ew - 48
            draw.rounded_rectangle((pill_x-12, 20, pill_x+ew+12, 56), radius=10,
                                   fill=(56, 134, 255, int(200*alpha)))
            draw.text((pill_x + ew//2, 38), ep_text, font=ef,
                     fill=(255,255,255,int(255*alpha)), anchor="mm")

    # ── Progress dots ──
    scene_idx = overlay_config.get('scene_idx', 0)
    total_scenes = overlay_config.get('total_scenes', 6)
    dot_y = 104
    dot_r = 6
    dot_gap = 20
    total_dots = total_scenes
    dots_w = total_dots * dot_r * 2 + (total_dots - 1) * dot_gap
    dx = (W - dots_w) // 2
    for di in range(total_dots):
        cx = dx + di * (dot_r * 2 + dot_gap) + dot_r
        if di < scene_idx:
            draw.ellipse((cx-dot_r, dot_y-dot_r, cx+dot_r, dot_y+dot_r),
                        fill=(56, 134, 255, int(255*alpha)))
        elif di == scene_idx:
            draw.ellipse((cx-dot_r-2, dot_y-dot_r-2, cx+dot_r+2, dot_y+dot_r+2),
                        fill=(255, 196, 0, int(255*alpha)))
        else:
            draw.ellipse((cx-dot_r, dot_y-dot_r, cx+dot_r, dot_y+dot_r),
                        fill=(40, 48, 70, int(255*alpha)))

    # ── Main text area (bottom third with glassmorphism) ──
    is_hook = overlay_config.get('hook', False)
    is_cta = overlay_config.get('cta', False)
    title = overlay_config.get('title', '')
    subtitle = overlay_config.get('subtitle', '')
    sub_progress = overlay_config.get('subtitle_progress', 1.0)

    if is_hook:
        # Hook: big centered text with glassmorphism panel
        glass_h = 420
        glass_y = H - glass_h - 200
        frame = _draw_glass_panel(frame, (30, glass_y, W-30, glass_y + glass_h), radius=24, alpha=160)

        draw = ImageDraw.Draw(frame)
        font_main = _font(68, bold=True)
        lines = _wrap(title, font_main, W - 120, draw)
        lh = 88
        total_th = len(lines) * lh
        ty = glass_y + (glass_h - total_th) // 2 - 20
        for line in lines:
            draw.text((W//2, ty), line, font=font_main,
                     fill=(255,255,255,int(255*alpha)), anchor="mm")
            ty += lh

        # Accent underline
        draw.rectangle([(W//2 - 140, ty + 10), (W//2 + 140, ty + 16)],
                      fill=(255, 196, 0, int(255*alpha)))

        # Subtitle
        if subtitle and sub_progress > 0.01:
            sfont = _font(30, bold=False)
            vis_chars = max(1, int(len(subtitle) * sub_progress))
            vis_text = subtitle[:vis_chars]
            slines = _wrap(vis_text, sfont, W - 120, draw)
            sy = ty + 40
            for sl in slines:
                draw.text((W//2, sy), sl, font=sfont,
                         fill=(160, 175, 200, int(255*alpha)), anchor="mm")
                sy += 42

    elif is_cta:
        # CTA: green text + URL pill
        glass_h = 360
        glass_y = H - glass_h - 240
        frame = _draw_glass_panel(frame, (30, glass_y, W-30, glass_y + glass_h), radius=24, alpha=160)

        draw = ImageDraw.Draw(frame)
        font_cta = _font(52, bold=True)
        lines = _wrap(title, font_cta, W - 120, draw)
        lh = 68
        ty = glass_y + 60
        for line in lines:
            draw.text((W//2, ty), line, font=font_cta,
                     fill=(0, 214, 130, int(255*alpha)), anchor="mm")
            ty += lh

        # URL pill
        url = "broadfsc.com/different"
        uf = _font(26, bold=False)
        uw = draw.textbbox((0, 0), url, font=uf)[2]
        ux = (W - uw) // 2
        pill_top = ty + 30
        draw.rounded_rectangle((ux-20, pill_top, ux+uw+20, pill_top+48), radius=14,
                              fill=(40, 48, 70, int(200*alpha)))
        draw.text((W//2, pill_top + 24), url, font=uf,
                 fill=(160, 175, 200, int(255*alpha)), anchor="mm")

    else:
        # Normal scene: title + animated subtitle
        glass_h = 380
        glass_y = H - glass_h - 160
        frame = _draw_glass_panel(frame, (30, glass_y, W-30, glass_y + glass_h), radius=24, alpha=150)

        draw = ImageDraw.Draw(frame)

        # Title
        font_main = _font(48, bold=True)
        lines = _wrap(title, font_main, W - 120, draw)
        lh = 64
        ty = glass_y + 50
        for line in lines:
            draw.text((W//2, ty), line, font=font_main,
                     fill=(255,255,255,int(255*alpha)), anchor="mm")
            ty += lh

        # Animated subtitle (typewriter)
        if subtitle and sub_progress > 0.01:
            sfont = _font(28, bold=False)
            vis_chars = max(1, int(len(subtitle) * sub_progress))
            vis_text = subtitle[:vis_chars]

            # Add blinking cursor effect
            if sub_progress < 0.99:
                vis_text += "|"  # cursor

            slines = _wrap(vis_text, sfont, W - 120, draw)
            sy = max(ty + 24, glass_y + glass_h - 140)
            for sl in slines:
                draw.text((W//2, sy), sl, font=sfont,
                         fill=(160, 175, 200, int(230*alpha)), anchor="mm")
                sy += 40

    return frame.convert('RGB')


# ─────────────────────────────────────────────
# TTS with sentence boundary timing
# ─────────────────────────────────────────────
async def _gen_tts_sentence(text, out_path):
    if not HAS_TTS:
        return out_path, 3.0
    comm = edge_tts.Communicate(text, voice=TTS_VOICE, rate=TTS_RATE)
    await comm.save(out_path)
    if os.path.exists(out_path):
        size_bytes = os.path.getsize(out_path)
        duration = size_bytes / (32_000 / 8)
        return out_path, max(2.0, duration)
    return out_path, len(text.split()) * 0.35

async def _gen_all_tts(sentences, tmp_dir):
    results = []
    for i, txt in enumerate(sentences):
        path = os.path.join(tmp_dir, f"tts_{i:02d}.mp3")
        _, dur = await _gen_tts_sentence(txt, path)
        results.append((txt, path, dur))
        print(f"  TTS {i+1}/{len(sentences)}: {dur:.1f}s — {txt[:50]}")
    return results


# ─────────────────────────────────────────────
# Audio mixer
# ─────────────────────────────────────────────
def _mp3_to_pcm(path):
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = 'ffmpeg'
    cmd = [ffmpeg_exe, '-y', '-i', path, '-f', 's16le', '-acodec', 'pcm_s16le',
           '-ar', '44100', '-ac', '2', 'pipe:1']
    result = subprocess.run(cmd, capture_output=True)
    return result.stdout

def _build_audio_concat(tts_clips, gap_sec=0.4, sr=44100, channels=2):
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
    num_samples = len(all_pcm) // (channels * 2)
    wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(all_pcm), b'WAVE',
        b'fmt ', 16, 1, channels, sr, sr * channels * 2,
        channels * 2, 16, b'data', len(all_pcm))
    return wav_header + all_pcm, durations, total_dur


# ─────────────────────────────────────────────
# Episode definitions — WITH ANNOTATIONS
# ─────────────────────────────────────────────
EPISODES = [
    # ── EP9: Candlestick Patterns ───────────────────────────
    {
        "ep": 9,
        "title": "Candlestick Patterns",
        "chart_type": "candlestick",
        "ohlcv_seed": 7,
        "ohlcv_trend": 0.001,
        "scenes": [
            {
                "title": "One candle can\ntell the whole story.",
                "subtitle": "Learn the 3 most powerful candlestick patterns.",
                "is_hook": True,
                "reveal": 0.35,
                "annotations": [],
                "duration": 3.5,
            },
            {
                "title": "THE HAMMER",
                "subtitle": "Small body at top, long lower wick. Buyers rejected lower prices after a downtrend. This is your reversal signal.",
                "reveal": 0.50,
                "annotations": [
                    {"type": "circle", "idx": 25, "text": "HAMMER", "color": "#FFC400", "sub_panel": "main"},
                    {"type": "arrow", "idx": 25, "text": "", "color": "#00D682", "sub_panel": "main"},
                ],
                "duration": 6.0,
            },
            {
                "title": "THE DOJI",
                "subtitle": "Open equals close. The market can't decide. A big move is coming next — stay alert.",
                "reveal": 0.65,
                "annotations": [
                    {"type": "circle", "idx": 35, "text": "DOJI", "color": "#A855F7", "sub_panel": "main"},
                    {"type": "box", "idx": 33, "idx_end": 37, "text": "Indecision Zone", "color": "#A855F7", "sub_panel": "main"},
                ],
                "duration": 6.0,
            },
            {
                "title": "BULLISH ENGULFING",
                "subtitle": "A big green candle completely swallows the previous red one. Bears are done. Bulls take over.",
                "reveal": 0.80,
                "annotations": [
                    {"type": "box", "idx": 44, "idx_end": 46, "text": "Engulfing Pattern", "color": "#FFC400", "sub_panel": "main"},
                    {"type": "arrow", "idx": 46, "text": "Bullish!", "color": "#00D682", "sub_panel": "main"},
                ],
                "duration": 6.0,
            },
            {
                "title": "ALWAYS CONFIRM\nWITH VOLUME",
                "subtitle": "Patterns without volume confirmation fail 70% of the time. High volume = real conviction behind the move.",
                "reveal": 1.0,
                "annotations": [
                    {"type": "circle", "idx": 46, "text": "High Vol!", "color": "#00D682", "sub_panel": "main"},
                    {"type": "arrow", "idx": 46, "text": "", "color": "#00D682", "sub_panel": "main"},
                ],
                "duration": 5.5,
            },
            {
                "title": "Trade smarter with\nBroadFSC",
                "subtitle": "",
                "is_cta": True,
                "reveal": 1.0,
                "annotations": [],
                "duration": 3.5,
            },
        ]
    },

    # ── EP10: MACD Strategy ─────────────────────────────────
    {
        "ep": 10,
        "title": "MACD Strategy",
        "chart_type": "macd",
        "ohlcv_seed": 13,
        "ohlcv_trend": 0.004,
        "scenes": [
            {
                "title": "MACD catches\nmomentum BEFORE price.",
                "subtitle": "The indicator that professional traders trust most.",
                "is_hook": True,
                "reveal": 0.30,
                "annotations": [],
                "duration": 3.5,
            },
            {
                "title": "HOW MACD WORKS",
                "subtitle": "MACD Line = 12 EMA minus 26 EMA. When the fast line pulls away from slow, momentum is building.",
                "reveal": 0.45,
                "annotations": [
                    {"type": "label", "idx": 20, "y_val": 2, "text": "MACD Line", "color": "#3886FF", "sub_panel": "sub"},
                    {"type": "label", "idx": 20, "y_val": -1, "text": "Signal Line", "color": "#FFC400", "sub_panel": "sub"},
                ],
                "duration": 6.0,
            },
            {
                "title": "THE GOLDEN CROSS",
                "subtitle": "When MACD crosses above the Signal Line — momentum is turning bullish. This is your buy signal.",
                "reveal": 0.60,
                "annotations": [
                    {"type": "circle", "idx": 30, "text": "Golden Cross!", "color": "#00D682", "sub_panel": "sub"},
                ],
                "duration": 6.0,
            },
            {
                "title": "READ THE HISTOGRAM",
                "subtitle": "Green bars = bullish momentum growing. Red bars = bears taking control. Bar size = conviction strength.",
                "reveal": 0.80,
                "annotations": [
                    {"type": "box", "idx": 38, "idx_end": 46, "text": "Bullish Momentum", "color": "#00D682", "sub_panel": "sub"},
                ],
                "duration": 6.0,
            },
            {
                "title": "ZERO LINE CROSS",
                "subtitle": "MACD crossing zero from below = strongest buy signal. Combine with a price breakout for maximum edge.",
                "reveal": 1.0,
                "annotations": [
                    {"type": "hline", "idx": 0, "y_val": 0, "text": "Zero Line", "color": "#828fa0", "sub_panel": "sub"},
                    {"type": "arrow", "idx": 40, "text": "Zero Cross!", "color": "#FFC400", "sub_panel": "sub"},
                ],
                "duration": 5.5,
            },
            {
                "title": "Trade smarter with\nBroadFSC",
                "subtitle": "",
                "is_cta": True,
                "reveal": 1.0,
                "annotations": [],
                "duration": 3.5,
            },
        ]
    },

    # ── EP11: Bollinger Bands ───────────────────────────────
    {
        "ep": 11,
        "title": "Bollinger Bands",
        "chart_type": "bollinger",
        "ohlcv_seed": 21,
        "ohlcv_trend": -0.001,
        "scenes": [
            {
                "title": "When bands squeeze,\nsomething BIG is coming.",
                "subtitle": "Bollinger Bands measure volatility in real time.",
                "is_hook": True,
                "reveal": 0.30,
                "annotations": [],
                "duration": 3.5,
            },
            {
                "title": "HOW BANDS WORK",
                "subtitle": "Middle Band = 20 SMA. Upper & Lower = Middle ± 2 Standard Deviations. 95% of price stays inside.",
                "reveal": 0.50,
                "annotations": [
                    {"type": "label", "idx": 25, "y_val": 0, "text": "Upper Band", "color": "#A855F7", "sub_panel": "main"},
                    {"type": "label", "idx": 25, "y_val": 0, "text": "Lower Band", "color": "#A855F7", "sub_panel": "main"},
                ],
                "duration": 6.0,
            },
            {
                "title": "THE SQUEEZE",
                "subtitle": "Bands narrowing = low volatility = coiled spring. This silence before the storm is your setup signal.",
                "reveal": 0.60,
                "annotations": [
                    {"type": "box", "idx": 30, "idx_end": 38, "text": "Squeeze Zone", "color": "#FFC400", "sub_panel": "main"},
                ],
                "duration": 6.0,
            },
            {
                "title": "UPPER BAND TOUCH",
                "subtitle": "Price touching upper band = overbought zone. But in strong uptrends, price can ride the band higher.",
                "reveal": 0.80,
                "annotations": [
                    {"type": "circle", "idx": 46, "text": "Overbought!", "color": "#FF3C3C", "sub_panel": "main"},
                ],
                "duration": 6.0,
            },
            {
                "title": "THE BAND WALK",
                "subtitle": "Price walks along one band during trending markets. This is the most profitable Bollinger pattern.",
                "reveal": 1.0,
                "annotations": [
                    {"type": "box", "idx": 42, "idx_end": 55, "text": "Band Walk", "color": "#00D682", "sub_panel": "main"},
                ],
                "duration": 5.5,
            },
            {
                "title": "More edge with\nBroadFSC",
                "subtitle": "",
                "is_cta": True,
                "reveal": 1.0,
                "annotations": [],
                "duration": 3.5,
            },
        ]
    },

    # ── EP12: Volume Analysis ───────────────────────────────
    {
        "ep": 12,
        "title": "Volume Analysis",
        "chart_type": "volume",
        "ohlcv_seed": 33,
        "ohlcv_trend": 0.002,
        "scenes": [
            {
                "title": "Price without volume\nis just noise.",
                "subtitle": "Volume is the only truth in the market.",
                "is_hook": True,
                "reveal": 0.30,
                "annotations": [],
                "duration": 3.5,
            },
            {
                "title": "HIGH VOL BREAKOUT",
                "subtitle": "Breakout on high volume = real move. Low volume breakouts fail more than 70% of the time.",
                "reveal": 0.50,
                "annotations": [
                    {"type": "circle", "idx": 25, "text": "Breakout!", "color": "#00D682", "sub_panel": "sub"},
                ],
                "duration": 6.0,
            },
            {
                "title": "DIVERGENCE = DANGER",
                "subtitle": "Rising price + falling volume = no conviction. Smart money is not participating. Prepare to exit.",
                "reveal": 0.65,
                "annotations": [
                    {"type": "box", "idx": 35, "idx_end": 42, "text": "Low Volume Rally", "color": "#FF3C3C", "sub_panel": "sub"},
                ],
                "duration": 6.0,
            },
            {
                "title": "CLIMAX VOLUME",
                "subtitle": "Massive volume spike after a long trend = exhaustion. The last buyers are piling in. Reversal ahead.",
                "reveal": 0.80,
                "annotations": [
                    {"type": "arrow", "idx": 48, "text": "Climax!", "color": "#FFC400", "sub_panel": "sub"},
                ],
                "duration": 6.0,
            },
            {
                "title": "VOLUME MA = FILTER",
                "subtitle": "Above-average volume confirms institutional interest. Below average = retail noise. Always check.",
                "reveal": 1.0,
                "annotations": [
                    {"type": "hline", "idx": 0, "y_val": 0, "text": "Vol MA20", "color": "#FFC400", "sub_panel": "sub"},
                    {"type": "box", "idx": 50, "idx_end": 58, "text": "Above Average", "color": "#00D682", "sub_panel": "sub"},
                ],
                "duration": 5.5,
            },
            {
                "title": "Follow for more.\nBroadFSC",
                "subtitle": "",
                "is_cta": True,
                "reveal": 1.0,
                "annotations": [],
                "duration": 3.5,
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
    chart_type = ep_def['chart_type']

    print(f"\n{'='*58}")
    print(f" EP.{ep_num}: {ep_def['title']}")
    print(f"{'='*58}")

    # 1. Generate TTS
    tts_texts = []
    for sc in scenes:
        if sc.get('is_cta'):
            tts_texts.append("Follow BroadFSC for more trading education.")
        else:
            spoken = sc['title'].replace('\n', ' ')
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

    # 3. Build audio
    print("--- Building Audio ---")
    audio_wav, clip_timings, _ = _build_audio_concat(tts_clips, gap_sec=0.3)
    for i, (at, dur) in enumerate(clip_timings):
        if i < len(scene_timings):
            scene_timings[i]['audio_start'] = at
            scene_timings[i]['audio_dur'] = dur

    audio_path = os.path.join(tmp_dir, f"ep{ep_num}_audio.wav")
    with open(audio_path, 'wb') as f:
        f.write(audio_wav)
    print(f"  Audio saved: {len(audio_wav)//1024}KB")

    # 4. Pre-render chart images (one per scene with its annotations)
    print("--- Pre-rendering Charts with Annotations ---")
    total_scenes = len(scenes)
    chart_cache = {}
    for si in range(total_scenes):
        st = scene_timings[si]
        scene_label = f"EP{ep_num} | {st['title'].replace(chr(10), ' '}"[:40]
        ci = _render_chart_full(
            ohlcv,
            chart_type=chart_type,
            reveal=st.get('reveal', 1.0),
            annotations=st.get('annotations', []),
            scene_label=scene_label,
        )
        chart_cache[si] = ci
        print(f"  Chart {si+1}/{total_scenes} rendered (reveal={st.get('reveal',1.0):.0%})")

    # 5. Render frames
    print("--- Rendering Video Frames ---")
    total_frames = int(total_duration * FPS)
    video_path = os.path.join(tmp_dir, f"ep{ep_num}_raw.mp4")

    writer = iio.get_writer(
        video_path, fps=FPS,
        codec='libx264',
        output_params=['-crf', '20', '-preset', 'fast', '-pix_fmt', 'yuv420p']
    )

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

        # ── Scene transition fade ──
        fade_dur = 0.4
        if scene_t < fade_dur:
            alpha = scene_t / fade_dur
        elif scene_t > st['duration'] - fade_dur:
            alpha = (st['duration'] - scene_t) / fade_dur
        else:
            alpha = 1.0
        alpha = max(0.0, min(1.0, alpha))

        # ── Subtitle typewriter progress ──
        subtitle = st.get('subtitle', '')
        if subtitle:
            # Typewriter: start after 0.3s, complete by 60% of scene
            type_start = 0.3
            type_end = st['duration'] * 0.6
            if scene_t < type_start:
                sub_progress = 0.0
            elif scene_t > type_end:
                sub_progress = 1.0
            else:
                sub_progress = (scene_t - type_start) / (type_end - type_start)
        else:
            sub_progress = 0.0

        chart_img = chart_cache[active_si]

        # Compose overlay
        overlay_config = {
            'title': st['title'],
            'subtitle': st.get('subtitle', ''),
            'subtitle_progress': sub_progress,
            'brand': True,
            'cta': st.get('is_cta', False),
            'hook': st.get('is_hook', False),
            'scene_idx': active_si,
            'total_scenes': total_scenes,
            'alpha': alpha,
            'ep_tag': f"EP{ep_num} · {ep_def['title']}",
        }
        frame = _compose_overlay(chart_img, overlay_config)

        writer.append_data(np.array(frame))

        if fi % (FPS * 5) == 0:
            print(f"  Frame {fi}/{total_frames} ({t:.1f}s)")

    writer.close()
    print(f"  Video frames done: {video_path}")

    # 6. Mux audio + video
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
    print(" BroadFSC TikTok Season 4 — EP9-EP12")
    print(" Professional Financial Education Engine v7")
    print("=" * 58)

    tmp_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_s4_cache")
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
