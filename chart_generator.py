"""
BroadFSC Chart Generator — Real Data, Zero AI Traces
Generates professional financial charts from yfinance real data:
1. Candlestick chart with MA overlays + volume
2. RSI + MACD indicator panel
3. Bollinger Band squeeze/breakout visualization
4. Trend summary infographic card

Style: Dark theme, professional financial media look.
No watermarks, no AI text, no generic labels — just clean data.
"""
import os
import sys
import io
import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import mplfinance as mpf
import yfinance as yf
import pandas as pd
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Style Config — Professional Dark Theme
# ============================================================
# Colors: dark background, clean lines, no flashy gradients
BG_COLOR = '#1a1a2e'
PANEL_COLOR = '#16213e'
GRID_COLOR = '#2a2a4a'
TEXT_COLOR = '#e0e0e0'
ACCENT_GREEN = '#00c853'
ACCENT_RED = '#ff1744'
ACCENT_GOLD = '#ffd740'
MA_COLORS = {'ma20': '#42a5f5', 'ma50': '#ab47bc', 'ma200': '#ff7043'}
VOLUME_UP = '#00c85380'
VOLUME_DOWN = '#ff174480'

SCRIPT_DIR = Path(__file__).parent
CHART_DIR = SCRIPT_DIR / 'charts'
CHART_DIR.mkdir(exist_ok=True)


def _apply_style(ax):
    """Apply consistent dark style to an axis."""
    ax.set_facecolor(PANEL_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.spines['bottom'].set_color(GRID_COLOR)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, color=GRID_COLOR, alpha=0.3, linewidth=0.5)


def get_stock_data(symbol, period='6mo'):
    """Fetch real stock data with TA indicators."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    info = ticker.info

    if hist.empty or len(hist) < 50:
        return None

    close = hist['Close']
    high = hist['High']
    low = hist['Low']
    volume = hist['Volume']

    # Moving Averages
    hist['MA20'] = close.rolling(20).mean()
    hist['MA50'] = close.rolling(50).mean()
    hist['MA200'] = close.rolling(200).mean() if len(close) >= 200 else close.expanding().mean()

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss
    hist['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    hist['MACD'] = ema12 - ema26
    hist['MACD_Signal'] = hist['MACD'].ewm(span=9).mean()
    hist['MACD_Hist'] = hist['MACD'] - hist['MACD_Signal']

    # Bollinger Bands
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    hist['BB_Upper'] = bb_mid + 2 * bb_std
    hist['BB_Lower'] = bb_mid - 2 * bb_std
    hist['BB_Mid'] = bb_mid

    # Support / Resistance
    lookback = min(90, len(hist))
    hist['Resistance'] = high.iloc[-lookback:].max()
    hist['Support'] = low.iloc[-lookback:].min()

    # Volume ratio
    avg_vol = volume.rolling(20).mean()

    company_name = info.get('shortName', info.get('longName', symbol))

    return {
        'symbol': symbol,
        'name': company_name,
        'hist': hist,
        'current_price': float(close.iloc[-1]),
        'rsi': float(hist['RSI'].iloc[-1]),
        'macd': float(hist['MACD'].iloc[-1]),
        'macd_signal': float(hist['MACD_Signal'].iloc[-1]),
        'resistance': float(hist['Resistance'].iloc[-1]),
        'support': float(hist['Support'].iloc[-1]),
        'bb_upper': float(hist['BB_Upper'].iloc[-1]),
        'bb_lower': float(hist['BB_Lower'].iloc[-1]),
    }


# ============================================================
# Chart 1: Candlestick + MA + Volume (mplfinance)
# ============================================================
def generate_candlestick_chart(symbol, data=None, save_path=None):
    """Generate professional candlestick chart with MA overlays and volume."""
    if data is None:
        data = get_stock_data(symbol)
    if data is None:
        print(f"  [chart] No data for ${symbol}, skipping candlestick")
        return None

    df = data['hist'].copy()
    # Last 60 trading days for clarity
    df = df.iloc[-60:]

    # Determine trend color for the title
    price = data['current_price']
    ma20 = df['MA20'].iloc[-1]
    bias = 'Bullish' if price > ma20 else 'Bearish'
    bias_color = ACCENT_GREEN if bias == 'Bullish' else ACCENT_RED

    # Custom style
    style = mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        marketcolors=mpf.make_marketcolors(
            up=ACCENT_GREEN, down=ACCENT_RED,
            edge={'up': ACCENT_GREEN, 'down': ACCENT_RED},
            wick={'up': ACCENT_GREEN, 'down': ACCENT_RED},
            volume={'up': VOLUME_UP, 'down': VOLUME_DOWN},
        ),
        gridcolor=GRID_COLOR,
        gridstyle='--',
        y_on_right=False,
    )

    # MA lines
    apds = [
        mpf.make_addplot(df['MA20'], color=MA_COLORS['ma20'], width=1.2, label='MA20'),
        mpf.make_addplot(df['MA50'], color=MA_COLORS['ma50'], width=1.2, label='MA50'),
    ]
    # Only add MA200 if we have enough data and it's not all NaN
    if 'MA200' in df.columns and df['MA200'].notna().any():
        apds.append(
            mpf.make_addplot(df['MA200'], color=MA_COLORS['ma200'], width=1.2, label='MA200')
        )

    # Add support/resistance lines as scatter (horizontal lines hack)
    # mplfinance doesn't natively support hlines in addplot, so we use fill_between
    resistance = data['resistance']
    support = data['support']

    if save_path is None:
        filepath = CHART_DIR / f'{symbol}_candlestick_{datetime.datetime.now().strftime("%Y%m%d")}.png'
    else:
        filepath = Path(save_path)

    fig, axes = mpf.plot(
        df,
        type='candle',
        style=style,
        title=f'\n${symbol}  {price:.2f}',
        volume=True,
        addplot=apds,
        figsize=(12, 8),
        returnfig=True,
        panel_ratios=(3, 1),
    )

    ax = axes[0]
    # Draw support/resistance on the price axis
    xmin, xmax = ax.get_xlim()
    ax.hlines(resistance, xmin, xmax, colors=ACCENT_RED, linewidths=1, linestyles='--', alpha=0.7)
    ax.hlines(support, xmin, xmax, colors=ACCENT_GREEN, linewidths=1, linestyles='--', alpha=0.7)

    # Labels
    ax.text(xmax + 0.5, resistance, f'  R ${resistance:.0f}', color=ACCENT_RED, fontsize=9, va='center')
    ax.text(xmax + 0.5, support, f'  S ${support:.0f}', color=ACCENT_GREEN, fontsize=9, va='center')

    # Bias badge
    ax.text(0.02, 0.95, bias.upper(), transform=ax.transAxes,
            fontsize=14, fontweight='bold', color=bias_color,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=BG_COLOR, edgecolor=bias_color, alpha=0.9))

    # Date format
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', color=TEXT_COLOR, fontsize=8)

    # Legend
    ax.legend(loc='upper left', fontsize=8, facecolor=PANEL_COLOR, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, framealpha=0.8)

    fig.set_facecolor(BG_COLOR)
    fig.tight_layout()
    fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)

    print(f"  [chart] Candlestick saved: {filepath}")
    return str(filepath)


# ============================================================
# Chart 2: RSI + MACD Panel
# ============================================================
def generate_indicator_panel(symbol, data=None, save_path=None):
    """Generate RSI + MACD technical indicator panel."""
    if data is None:
        data = get_stock_data(symbol)
    if data is None:
        print(f"  [chart] No data for ${symbol}, skipping indicators")
        return None

    df = data['hist'].copy()
    df = df.iloc[-60:]

    if save_path is None:
        filepath = CHART_DIR / f'{symbol}_indicators_{datetime.datetime.now().strftime("%Y%m%d")}.png'
    else:
        filepath = Path(save_path)

    fig = plt.figure(figsize=(12, 7), facecolor=BG_COLOR)
    gs = gridspec.GridSpec(3, 1, height_ratios=[2, 1, 1], hspace=0.3)

    # --- Price mini chart (context) ---
    ax_price = fig.add_subplot(gs[0])
    _apply_style(ax_price)
    ax_price.plot(df.index, df['Close'], color=TEXT_COLOR, linewidth=1.5, label='Price')
    ax_price.plot(df.index, df['MA20'], color=MA_COLORS['ma20'], linewidth=1, alpha=0.8, label='MA20')
    ax_price.fill_between(df.index, df['BB_Lower'], df['BB_Upper'], alpha=0.15, color=ACCENT_GOLD, label='Bollinger')
    ax_price.set_ylabel('Price ($)', color=TEXT_COLOR, fontsize=10)
    ax_price.set_title(f'${symbol}  —  RSI & MACD Analysis', color=TEXT_COLOR, fontsize=14, fontweight='bold', pad=10)
    ax_price.legend(loc='upper left', fontsize=8, facecolor=PANEL_COLOR, edgecolor=GRID_COLOR,
                    labelcolor=TEXT_COLOR, framealpha=0.8)

    # --- RSI ---
    ax_rsi = fig.add_subplot(gs[1])
    _apply_style(ax_rsi)
    ax_rsi.plot(df.index, df['RSI'], color=ACCENT_GOLD, linewidth=1.5)
    ax_rsi.axhline(70, color=ACCENT_RED, linewidth=1, linestyle='--', alpha=0.7)
    ax_rsi.axhline(30, color=ACCENT_GREEN, linewidth=1, linestyle='--', alpha=0.7)
    ax_rsi.axhline(50, color=GRID_COLOR, linewidth=0.5, linestyle=':', alpha=0.5)
    ax_rsi.fill_between(df.index, 70, df['RSI'], where=df['RSI'] >= 70, alpha=0.2, color=ACCENT_RED)
    ax_rsi.fill_between(df.index, 30, df['RSI'], where=df['RSI'] <= 30, alpha=0.2, color=ACCENT_GREEN)
    ax_rsi.set_ylabel('RSI(14)', color=TEXT_COLOR, fontsize=10)
    ax_rsi.set_ylim(10, 90)

    # Current RSI value label
    rsi_val = data['rsi']
    rsi_label = 'OB' if rsi_val > 70 else 'OS' if rsi_val < 30 else ''
    ax_rsi.text(0.98, 0.9, f'{rsi_val:.1f} {rsi_label}', transform=ax_rsi.transAxes,
                fontsize=11, fontweight='bold', color=ACCENT_RED if rsi_val > 70 else ACCENT_GREEN if rsi_val < 30 else TEXT_COLOR,
                ha='right', va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=BG_COLOR, edgecolor=GRID_COLOR, alpha=0.9))

    # --- MACD ---
    ax_macd = fig.add_subplot(gs[2])
    _apply_style(ax_macd)
    ax_macd.plot(df.index, df['MACD'], color=MA_COLORS['ma20'], linewidth=1.2, label='MACD')
    ax_macd.plot(df.index, df['MACD_Signal'], color=ACCENT_RED, linewidth=1.2, label='Signal')
    macd_hist = df['MACD_Hist']
    colors = [ACCENT_GREEN if v >= 0 else ACCENT_RED for v in macd_hist]
    ax_macd.bar(df.index, macd_hist, color=colors, alpha=0.6, width=0.8)
    ax_macd.axhline(0, color=GRID_COLOR, linewidth=0.5)
    ax_macd.set_ylabel('MACD', color=TEXT_COLOR, fontsize=10)
    ax_macd.legend(loc='upper left', fontsize=8, facecolor=PANEL_COLOR, edgecolor=GRID_COLOR,
                   labelcolor=TEXT_COLOR, framealpha=0.8)

    # Date formatting
    for ax in [ax_price, ax_rsi, ax_macd]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', color=TEXT_COLOR, fontsize=8)

    fig.tight_layout()
    fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)

    print(f"  [chart] Indicators saved: {filepath}")
    return str(filepath)


# ============================================================
# Chart 3: Bollinger Band Squeeze/Breakout
# ============================================================
def generate_bollinger_chart(symbol, data=None, save_path=None):
    """Generate Bollinger Band width analysis chart."""
    if data is None:
        data = get_stock_data(symbol)
    if data is None:
        print(f"  [chart] No data for ${symbol}, skipping Bollinger")
        return None

    df = data['hist'].copy()
    df = df.iloc[-60:]

    if save_path is None:
        filepath = CHART_DIR / f'{symbol}_bollinger_{datetime.datetime.now().strftime("%Y%m%d")}.png'
    else:
        filepath = Path(save_path)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), facecolor=BG_COLOR,
                                     gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.25})

    # --- Price with BB ---
    _apply_style(ax1)
    ax1.plot(df.index, df['Close'], color=TEXT_COLOR, linewidth=1.5, label='Price')
    ax1.plot(df.index, df['BB_Upper'], color=ACCENT_GOLD, linewidth=1, linestyle='--', alpha=0.7, label='Upper Band')
    ax1.plot(df.index, df['BB_Lower'], color=ACCENT_GOLD, linewidth=1, linestyle='--', alpha=0.7, label='Lower Band')
    ax1.plot(df.index, df['BB_Mid'], color=ACCENT_GOLD, linewidth=0.8, alpha=0.5, label='MA20')
    ax1.fill_between(df.index, df['BB_Lower'], df['BB_Upper'], alpha=0.1, color=ACCENT_GOLD)

    # Mark current price position
    price = data['current_price']
    bb_upper = data['bb_upper']
    bb_lower = data['bb_lower']
    bb_range = bb_upper - bb_lower
    bb_pos = ((price - bb_lower) / bb_range * 100) if bb_range > 0 else 50

    pos_label = 'Near Upper' if bb_pos > 80 else 'Near Lower' if bb_pos < 20 else 'Mid-Range'
    pos_color = ACCENT_RED if bb_pos > 80 else ACCENT_GREEN if bb_pos < 20 else ACCENT_GOLD

    ax1.text(0.98, 0.95, f'BB Position: {bb_pos:.0f}%\n{pos_label}',
             transform=ax1.transAxes, fontsize=11, fontweight='bold', color=pos_color,
             ha='right', va='top',
             bbox=dict(boxstyle='round,pad=0.4', facecolor=BG_COLOR, edgecolor=pos_color, alpha=0.9))

    ax1.set_title(f'${symbol}  —  Bollinger Band Analysis', color=TEXT_COLOR, fontsize=14, fontweight='bold', pad=10)
    ax1.set_ylabel('Price ($)', color=TEXT_COLOR, fontsize=10)
    ax1.legend(loc='upper left', fontsize=8, facecolor=PANEL_COLOR, edgecolor=GRID_COLOR,
               labelcolor=TEXT_COLOR, framealpha=0.8)

    # --- BB Width (squeeze indicator) ---
    _apply_style(ax2)
    bb_width = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid'] * 100)
    ax2.plot(df.index, bb_width, color=ACCENT_GOLD, linewidth=1.5)
    ax2.fill_between(df.index, 0, bb_width, alpha=0.2, color=ACCENT_GOLD)

    # Low volatility zone
    width_20ma = bb_width.rolling(20).mean()
    squeeze_threshold = width_20ma * 0.7
    ax2.axhline(float(squeeze_threshold.iloc[-1]), color=ACCENT_GREEN, linewidth=1, linestyle='--', alpha=0.6)
    ax2.text(0.02, 0.85, 'Squeeze Zone', transform=ax2.transAxes, fontsize=8, color=ACCENT_GREEN, alpha=0.8)

    ax2.set_ylabel('BB Width %', color=TEXT_COLOR, fontsize=10)

    # Date formatting
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', color=TEXT_COLOR, fontsize=8)

    fig.tight_layout()
    fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)

    print(f"  [chart] Bollinger saved: {filepath}")
    return str(filepath)


# ============================================================
# Chart 4: Trend Summary Infographic Card
# ============================================================
def generate_trend_card(symbol, data=None, save_path=None):
    """Generate a compact trend summary infographic card — great for social media."""
    if data is None:
        data = get_stock_data(symbol)
    if data is None:
        print(f"  [chart] No data for ${symbol}, skipping trend card")
        return None

    if save_path is None:
        filepath = CHART_DIR / f'{symbol}_trend_card_{datetime.datetime.now().strftime("%Y%m%d")}.png'
    else:
        filepath = Path(save_path)

    price = data['current_price']
    rsi = data['rsi']
    macd = data['macd']
    macd_sig = data['macd_signal']
    resistance = data['resistance']
    support = data['support']
    bb_upper = data['bb_upper']
    bb_lower = data['bb_lower']

    # Determine bias
    if rsi < 35:
        bias, bias_color = 'OVERSOLD', ACCENT_GREEN
    elif rsi > 70:
        bias, bias_color = 'OVERBOUGHT', ACCENT_RED
    elif price > data['hist']['MA20'].iloc[-1] and macd > macd_sig:
        bias, bias_color = 'BULLISH', ACCENT_GREEN
    elif price < data['hist']['MA20'].iloc[-1] and macd < macd_sig:
        bias, bias_color = 'BEARISH', ACCENT_RED
    else:
        bias, bias_color = 'NEUTRAL', ACCENT_GOLD

    # Draw card
    fig, ax = plt.subplots(figsize=(6, 8), facecolor=BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')
    fig.patch.set_facecolor(BG_COLOR)

    # Header — Symbol + Price
    ax.text(5, 13, f'${symbol}', fontsize=32, fontweight='bold', color=TEXT_COLOR,
            ha='center', va='center', fontfamily='monospace')
    ax.text(5, 12, f'${price:.2f}', fontsize=22, color=TEXT_COLOR,
            ha='center', va='center')

    # Bias badge
    badge = FancyBboxPatch((3.2, 10.7), 3.6, 0.8, boxstyle='round,pad=0.1',
                           facecolor=BG_COLOR, edgecolor=bias_color, linewidth=2)
    ax.add_patch(badge)
    ax.text(5, 11.1, bias, fontsize=16, fontweight='bold', color=bias_color,
            ha='center', va='center')

    # Divider
    ax.plot([1, 9], [10.2, 10.2], color=GRID_COLOR, linewidth=1)

    # RSI
    rsi_color = ACCENT_RED if rsi > 70 else ACCENT_GREEN if rsi < 30 else TEXT_COLOR
    ax.text(1.5, 9.5, 'RSI(14)', fontsize=11, color=TEXT_COLOR, va='center')
    ax.text(8.5, 9.5, f'{rsi:.1f}', fontsize=14, fontweight='bold', color=rsi_color,
            ha='right', va='center')

    # RSI bar
    bar_bg = FancyBboxPatch((1.5, 8.8), 7, 0.4, boxstyle='round,pad=0.05',
                            facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, linewidth=0.5)
    ax.add_patch(bar_bg)
    bar_width = max(0.1, min(rsi / 100 * 7, 7))
    bar_fill = FancyBboxPatch((1.5, 8.8), bar_width, 0.4, boxstyle='round,pad=0.05',
                              facecolor=rsi_color, edgecolor='none', alpha=0.6)
    ax.add_patch(bar_fill)

    # MACD
    macd_label = 'Bullish' if macd > macd_sig else 'Bearish'
    macd_color = ACCENT_GREEN if macd > macd_sig else ACCENT_RED
    ax.text(1.5, 8.0, 'MACD', fontsize=11, color=TEXT_COLOR, va='center')
    ax.text(8.5, 8.0, macd_label, fontsize=13, fontweight='bold', color=macd_color,
            ha='right', va='center')

    # Key Levels
    ax.plot([1, 9], [7.3, 7.3], color=GRID_COLOR, linewidth=1)
    ax.text(5, 6.8, 'KEY LEVELS', fontsize=12, fontweight='bold', color=ACCENT_GOLD,
            ha='center', va='center')

    ax.text(1.5, 6.0, 'Resistance', fontsize=10, color=ACCENT_RED, va='center')
    ax.text(8.5, 6.0, f'${resistance:.0f}', fontsize=13, fontweight='bold', color=ACCENT_RED,
            ha='right', va='center')

    ax.text(1.5, 5.2, 'Support', fontsize=10, color=ACCENT_GREEN, va='center')
    ax.text(8.5, 5.2, f'${support:.0f}', fontsize=13, fontweight='bold', color=ACCENT_GREEN,
            ha='right', va='center')

    # Bollinger
    ax.plot([1, 9], [4.5, 4.5], color=GRID_COLOR, linewidth=1)
    ax.text(5, 4.0, 'BOLLINGER', fontsize=12, fontweight='bold', color=ACCENT_GOLD,
            ha='center', va='center')
    ax.text(1.5, 3.2, 'Upper', fontsize=10, color=TEXT_COLOR, va='center')
    ax.text(8.5, 3.2, f'${bb_upper:.0f}', fontsize=12, color=TEXT_COLOR, ha='right', va='center')
    ax.text(1.5, 2.5, 'Lower', fontsize=10, color=TEXT_COLOR, va='center')
    ax.text(8.5, 2.5, f'${bb_lower:.0f}', fontsize=12, color=TEXT_COLOR, ha='right', va='center')

    # Footer
    ax.text(5, 1.2, 't.me/BroadInvestBot', fontsize=9, color=GRID_COLOR,
            ha='center', va='center', fontfamily='monospace')

    fig.tight_layout(pad=0.5)
    fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)

    print(f"  [chart] Trend card saved: {filepath}")
    return str(filepath)


# ============================================================
# Batch Generate All Charts for a Symbol
# ============================================================
def generate_all_charts(symbol, save_dir=None):
    """Generate all 4 chart types for a symbol. Returns dict of paths."""
    print(f"\n📊 Generating charts for ${symbol}...")

    data = get_stock_data(symbol)
    if data is None:
        print(f"  ❌ No data available for ${symbol}")
        return None

    kwargs = {'data': data}
    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        kwargs['candlestick_save'] = str(save_dir / f'{symbol}_candlestick_{date_str}.png')
        kwargs['indicators_save'] = str(save_dir / f'{symbol}_indicators_{date_str}.png')
        kwargs['bollinger_save'] = str(save_dir / f'{symbol}_bollinger_{date_str}.png')
        kwargs['trend_card_save'] = str(save_dir / f'{symbol}_trend_card_{date_str}.png')

    results = {}

    candlestick_path = generate_candlestick_chart(symbol, data=data,
                                                   save_path=kwargs.get('candlestick_save'))
    if candlestick_path:
        results['candlestick'] = candlestick_path

    indicators_path = generate_indicator_panel(symbol, data=data,
                                               save_path=kwargs.get('indicators_save'))
    if indicators_path:
        results['indicators'] = indicators_path

    bollinger_path = generate_bollinger_chart(symbol, data=data,
                                              save_path=kwargs.get('bollinger_save'))
    if bollinger_path:
        results['bollinger'] = bollinger_path

    trend_card_path = generate_trend_card(symbol, data=data,
                                          save_path=kwargs.get('trend_card_save'))
    if trend_card_path:
        results['trend_card'] = trend_card_path

    print(f"  ✅ Generated {len(results)} charts for ${symbol}")
    return results


# ============================================================
# Main — CLI Usage
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='BroadFSC Chart Generator')
    parser.add_argument('symbols', nargs='+', help='Stock symbols (e.g., NVDA AAPL TSLA)')
    parser.add_argument('--type', choices=['all', 'candlestick', 'indicators', 'bollinger', 'card'],
                        default='all', help='Chart type to generate')
    parser.add_argument('--output', '-o', default=None, help='Output directory')
    args = parser.parse_args()

    for symbol in args.symbols:
        if args.type == 'all':
            generate_all_charts(symbol, save_dir=args.output)
        elif args.type == 'candlestick':
            generate_candlestick_chart(symbol, save_path=args.output)
        elif args.type == 'indicators':
            generate_indicator_panel(symbol, save_path=args.output)
        elif args.type == 'bollinger':
            generate_bollinger_chart(symbol, save_path=args.output)
        elif args.type == 'card':
            generate_trend_card(symbol, save_path=args.output)
