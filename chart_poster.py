"""
BroadFSC Chart Poster — Generate charts from real data and post to all platforms.

Standalone script that:
1. Picks today's top tickers
2. Generates 4 types of charts per ticker (candlestick, indicators, bollinger, trend card)
3. Posts chart+text to all supported platforms

Can run independently or be called from daily_stock_content / social_poster.

Usage:
  python chart_poster.py                    # Auto-pick 3 stocks, post charts
  python chart_poster.py NVDA AAPL TSLA     # Specific stocks
  python chart_poster.py --generate-only    # Generate charts without posting
  python chart_poster.py --platform telegram # Only post to telegram
"""
import os
import sys
import datetime
import random
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent

# ============================================================
# Chart type → platform mapping
# ============================================================
# Each platform gets the most suitable chart type:
# - Telegram/Discord: trend_card (compact, visual) + candlestick (detailed)
# - Bluesky/Mastodon/Threads: trend_card (square, social-friendly)
# - Hatena/Substack/Email: candlestick + indicators (detailed analysis)

PLATFORM_CHART_MAP = {
    'telegram':   ['trend_card', 'candlestick'],
    'discord':    ['trend_card', 'candlestick'],
    'bluesky':    ['trend_card'],
    'mastodon':   ['trend_card'],
    'threads':    ['trend_card'],
    'hatena':     ['candlestick', 'indicators'],
    'substack':   ['candlestick', 'indicators'],
    'email':      ['trend_card'],
}

# High-attention stocks
WATCHLIST = [
    "NVDA", "AAPL", "TSLA", "MSFT", "META",
    "AMD", "AMZN", "GOOGL", "PLTR", "COIN"
]


def generate_caption(symbol, chart_type, data=None):
    """Generate a natural-sounding caption for the chart.

    No AI-generated feel — just clean, factual, professional.
    """
    if data is None:
        try:
            from chart_generator import get_stock_data
            data = get_stock_data(symbol)
        except:
            pass

    if chart_type == 'candlestick':
        if data:
            return f"📊 ${symbol} ${data['current_price']:.2f} — 60D Price Action & Key Levels"
        return f"📊 ${symbol} — 60D Price Action & Key Levels"

    elif chart_type == 'indicators':
        if data:
            rsi = data['rsi']
            rsi_tag = "⚠️ Oversold" if rsi < 30 else "⚠️ Overbought" if rsi > 70 else ""
            return f"📈 ${symbol} RSI {rsi:.0f} {rsi_tag} | MACD {'Bullish' if data['macd'] > data['macd_signal'] else 'Bearish'}"
        return f"📈 ${symbol} — RSI & MACD Analysis"

    elif chart_type == 'bollinger':
        if data:
            bb_range = data['bb_upper'] - data['bb_lower']
            bb_pos = ((data['current_price'] - data['bb_lower']) / bb_range * 100) if bb_range > 0 else 50
            return f"📉 ${symbol} Bollinger Band Position: {bb_pos:.0f}%"
        return f"📉 ${symbol} — Bollinger Band Analysis"

    elif chart_type == 'trend_card':
        if data:
            rsi = data['rsi']
            if rsi < 35:
                bias = "OVERSOLD"
            elif rsi > 70:
                bias = "OVERBOUGHT"
            elif data['macd'] > data['macd_signal']:
                bias = "BULLISH"
            elif data['macd'] < data['macd_signal']:
                bias = "BEARISH"
            else:
                bias = "NEUTRAL"
            return f"${symbol} ${data['current_price']:.2f} — {bias}\n\n📱 Free daily signals: t.me/BroadInvestBot"
        return f"${symbol} — Technical Analysis\n\n📱 t.me/BroadInvestBot"

    return f"${symbol} — Technical Analysis"


def post_charts_to_platform(symbol, chart_paths, platform, data=None):
    """Post charts to a specific platform using chart_uploader."""
    from chart_uploader import upload_chart_to_platform

    chart_types = PLATFORM_CHART_MAP.get(platform, ['trend_card'])
    posted = 0

    for chart_type in chart_types:
        img_path = chart_paths.get(chart_type)
        if not img_path or not os.path.exists(img_path):
            continue

        caption = generate_caption(symbol, chart_type, data=data)

        try:
            success = upload_chart_to_platform(
                platform=platform,
                image_path=img_path,
                text=caption,
                alt_text=f"${symbol} {chart_type} chart",
            )
            if success:
                posted += 1
                print(f"  ✅ {platform}: {chart_type} posted")
            else:
                print(f"  ⚠️ {platform}: {chart_type} upload failed")
        except Exception as e:
            print(f"  ❌ {platform}: {chart_type} error: {e}")

    return posted


def run(symbols=None, platforms=None, generate_only=False):
    """Main execution.

    Args:
        symbols: List of ticker symbols. Auto-picks 3 if None.
        platforms: List of platform names. All if None.
        generate_only: Only generate charts, don't post.
    """
    if symbols is None:
        symbols = random.sample(WATCHLIST, min(3, len(WATCHLIST)))

    all_platforms = ['telegram', 'discord', 'bluesky', 'mastodon', 'threads']
    if platforms is None:
        platforms = all_platforms

    print("=" * 60)
    print(f"📊 BroadFSC Chart Poster — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Symbols: {', '.join('$' + s for s in symbols)}")
    print(f"   Platforms: {', '.join(platforms)}")
    print("=" * 60)

    from chart_generator import generate_all_charts, get_stock_data

    total_posted = 0

    for symbol in symbols:
        print(f"\n--- ${symbol} ---")

        # Generate charts
        chart_results = generate_all_charts(symbol)
        if not chart_results:
            print(f"  ⚠️ No charts generated for ${symbol}")
            continue

        # Get data for captions
        data = get_stock_data(symbol)

        if generate_only:
            print(f"  📁 Charts saved (not posting):")
            for ctype, cpath in chart_results.items():
                print(f"    {ctype}: {cpath}")
            continue

        # Post to each platform
        for platform in platforms:
            try:
                n = post_charts_to_platform(symbol, chart_results, platform, data=data)
                total_posted += n
            except Exception as e:
                print(f"  ❌ {platform}: {e}")

    print(f"\n{'=' * 60}")
    print(f"📊 Done: {total_posted} chart posts across {len(platforms)} platforms")
    print("=" * 60)

    return total_posted


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='BroadFSC Chart Poster')
    parser.add_argument('symbols', nargs='*', default=None, help='Stock symbols')
    parser.add_argument('--generate-only', action='store_true', help='Only generate, do not post')
    parser.add_argument('--platform', '-p', default=None, help='Single platform name')
    args = parser.parse_args()

    symbols = args.symbols if args.symbols else None
    platforms = [args.platform] if args.platform else None

    run(symbols=symbols, platforms=platforms, generate_only=args.generate_only)
