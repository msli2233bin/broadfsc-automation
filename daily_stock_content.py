"""
Daily Stock TA Content Generator
Fetches real market data via yfinance for 5 high-attention US stocks,
generates platform-specific TA analysis posts, and saves to content queue.

Runs once daily before social_poster. Replaces generic "market update" content
with stock-specific technical analysis that drives engagement and CTAs.
"""
import os
import sys
import json
import datetime
import random
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
SCRIPT_DIR = Path(__file__).parent
QUEUE_DIR = SCRIPT_DIR / 'knowledge' / 'content_queue'
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

# High-attention stocks that generate engagement
WATCHLIST = [
    "NVDA", "AAPL", "TSLA", "MSFT", "META",
    "AMD", "AMZN", "GOOGL", "PLTR", "COIN"
]

# Pick 5 per day
DAILY_PICKS = 5

# Platform content lengths
PLATFORM_LIMITS = {
    'twitter': 280,     # Per tweet in thread
    'mastodon': 500,
    'bluesky': 300,
    'discord': 1800,
    'threads': 500,
    'stocktwits': 140,
    'telegram': 2000,
}

CORE_CTA = "📱 Free TA signals: t.me/BroadInvestBot"

def get_stock_data(symbol):
    """Fetch real stock data and calculate TA indicators."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    info = ticker.info
    hist = ticker.history(period="90d")

    if hist.empty or len(hist) < 20:
        return None

    close = hist['Close']
    high = hist['High']
    low = hist['Low']
    volume = hist['Volume']

    # Current data
    current_price = close.iloc[-1]
    prev_close = close.iloc[-2] if len(close) > 1 else current_price

    # RSI(14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Moving Averages
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean() if len(close) >= 200 else close.expanding().mean()

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    macd_signal = macd_line.ewm(span=9).mean()

    # Bollinger Bands
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std

    # Support/Resistance (90-day)
    resistance = float(high.max())
    support = float(low.min())

    # Volume comparison
    avg_vol = volume.rolling(20).mean().iloc[-1]
    current_vol = volume.iloc[-1]
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1

    # Performance
    change_5d = ((current_price / close.iloc[-6]) - 1) * 100 if len(close) >= 6 else 0
    change_20d = ((current_price / close.iloc[-21]) - 1) * 100 if len(close) >= 21 else 0

    # Determine setup
    rsi_val = float(rsi.iloc[-1])
    macd_val = float(macd_line.iloc[-1])
    macd_sig_val = float(macd_signal.iloc[-1])
    price_vs_ma20 = current_price - float(ma20.iloc[-1])
    bb_pos = (current_price - float(bb_lower.iloc[-1])) / (float(bb_upper.iloc[-1]) - float(bb_lower.iloc[-1])) if float(bb_upper.iloc[-1]) != float(bb_lower.iloc[-1]) else 0.5

    # Trend classification
    if rsi_val < 35:
        trend_short = "oversold bounce setup"
        bias = "bullish"
    elif rsi_val > 70:
        trend_short = "overbought, watching for pullback"
        bias = "cautious"
    elif price_vs_ma20 > 0 and macd_val > macd_sig_val:
        trend_short = "uptrend intact"
        bias = "bullish"
    elif price_vs_ma20 < 0 and macd_val < macd_sig_val:
        trend_short = "correction in play"
        bias = "bearish"
    else:
        trend_short = "consolidation"
        bias = "neutral"

    company_name = info.get('shortName', info.get('longName', symbol))
    sector = info.get('sector', 'Technology')
    market_cap = info.get('marketCap', 0)

    return {
        'symbol': symbol,
        'name': company_name,
        'sector': sector,
        'price': round(current_price, 2),
        'change_pct': round(((current_price / prev_close) - 1) * 100, 2),
        'day_range': f"${low.iloc[-1]:.2f}-${high.iloc[-1]:.2f}",
        'rsi': round(rsi_val, 1),
        'ma20': round(float(ma20.iloc[-1]), 2),
        'ma50': round(float(ma50.iloc[-1]), 2),
        'ma200': round(float(ma200.iloc[-1]), 2),
        'macd': round(macd_val, 4),
        'macd_signal': round(macd_sig_val, 4),
        'bb_upper': round(float(bb_upper.iloc[-1]), 2),
        'bb_lower': round(float(bb_lower.iloc[-1]), 2),
        'bb_position': round(bb_pos * 100, 1),
    'resistance': round(float(high.max()), 2),
    'support': round(float(low.min()), 2),
        'vol_ratio': round(vol_ratio, 1),
        'change_5d': round(change_5d, 2),
        'change_20d': round(change_20d, 2),
        'bias': bias,
        'trend_short': trend_short,
        'market_cap': market_cap,
    }


def format_market_cap(mcap):
    """Format market cap to human readable."""
    if mcap >= 1e12:
        return f"${mcap/1e12:.2f}T"
    elif mcap >= 1e9:
        return f"${mcap/1e9:.1f}B"
    else:
        return f"${mcap/1e6:.0f}M"


def generate_twitter_thread(data):
    """Generate Twitter thread (4 tweets) with specific TA analysis."""
    s = data['symbol']
    p = data['price']
    rsi = data['rsi']
    ma20 = data['ma20']
    bias = data['bias']
    trend = data['trend_short']
    chg = data['change_pct']
    chg5 = data['change_5d']
    chg20 = data['change_20d']
    res = data['resistance']
    sup = data['support']
    vol = data['vol_ratio']
    bb_pos = data['bb_position']
    mcap = format_market_cap(data['market_cap'])

    # Determine RSI description
    if rsi < 30:
        rsi_desc = f"oversold (RSI {rsi})"
        rsi_action = "watch for reversal"
    elif rsi < 45:
        rsi_desc = f"cooling (RSI {rsi})"
        rsi_action = "near support"
    elif rsi < 60:
        rsi_desc = f"neutral (RSI {rsi})"
        rsi_action = "room to run"
    elif rsi < 75:
        rsi_desc = f"momentum zone (RSI {rsi})"
        rsi_action = "trend strong, watch OB"
    else:
        rsi_desc = f"overbought (RSI {rsi})"
        rsi_action = "pullback likely"

    # MACD description
    macd_val = data['macd']
    macd_sig = data['macd_signal']
    if macd_val > macd_sig and macd_val > 0:
        macd_desc = "bullish, above signal"
    elif macd_val > macd_sig:
        macd_desc = "turning bullish"
    elif macd_val < macd_sig and macd_val < 0:
        macd_desc = "bearish, below signal"
    else:
        macd_desc = "weakening"

    bi = "🟢" if chg > 0 else "🔴"
    tweets = [
        f"1/ ${s} {bi} {p} ({chg:+.1f}%) | {mcap}\n\n{trend.upper()}. {rsi_desc}, MACD {macd_desc}. {rsi_action}.",
        f"2/ KEY LEVELS:\nResistance: ${res}\nSupport: ${sup}\nMA20: ${ma20} ({'above' if p > ma20 else 'below'})\n5D: {chg5:+.1f}% | 20D: {chg20:+.1f}%\nVol: {vol}x avg",
        f"3/ SETUP: {bias.upper()}\nBB position: {bb_pos}%\n\n{'Bounce from support → target $' + str(res) if 'oversold' in trend else 'Holding above MA20 → momentum continuation' if 'uptrend' in trend else 'Compression → breakout imminent'}",
        f"4/ TRADE: Only enter with confirmation. Respect the levels.\n\n📱 More ${s} signals + 4 more stocks: t.me/BroadInvestBot",
    ]
    return tweets


def generate_mastodon_post(data):
    """Generate Mastodon post (500 chars) with TA analysis."""
    s = data['symbol']
    n = data['name']
    p = data['price']
    chg = data['change_pct']
    rsi = data['rsi']
    ma20 = data['ma20']
    macd_desc = "bullish" if data['macd'] > data['macd_signal'] else "bearish"
    bias = data['bias'].upper()
    res = data['resistance']
    sup = data['support']
    trend = data['trend_short']
    vol = data['vol_ratio']
    chg5 = data['change_5d']

    content = (
        f"${s} {n}\n\n"
        f"💰 {p} ({chg:+.1f}%) | 5D: {chg5:+.1f}%\n"
        f"📊 RSI: {rsi} | MACD: {macd_desc}\n"
        f"📈 MA20: ${ma20} ({'above' if p > ma20 else 'below'})\n"
        f"🎯 Resistance: ${res} | Support: ${sup}\n"
        f"📢 Vol: {vol}x avg\n\n"
        f"Setup: {trend} → bias: {bias}\n\n"
        f"{CORE_CTA}\n"
        f"#${s} #Trading #TechnicalAnalysis #Stocks"
    )
    return content


def generate_discord_post(data):
    """Generate Discord post (1800 chars) with structured TA analysis."""
    s = data['symbol']
    n = data['name']
    p = data['price']
    chg = data['change_pct']
    rsi = data['rsi']
    ma20 = data['ma20']
    ma50 = data['ma50']
    ma200 = data['ma200']
    macd_val = data['macd']
    macd_sig = data['macd_signal']
    bb_upper = data['bb_upper']
    bb_lower = data['bb_lower']
    res = data['resistance']
    sup = data['support']
    bias = data['bias']
    trend = data['trend_short']
    vol = data['vol_ratio']
    chg5 = data['change_5d']
    chg20 = data['change_20d']
    bb_pos = data['bb_position']

    macd_desc = "Bullish (above signal)" if macd_val > macd_sig else "Bearish (below signal)"
    bias_emoji = "🟢" if bias == "bullish" else "🔴" if bias == "bearish" else "🟡"

    content = (
        f"## {bias_emoji} ${s} — {n} | ${p} ({chg:+.1f}%)\n\n"
        f"**Setup:** {trend} → Bias: **{bias.upper()}**\n\n"
        f"### 📊 Technical Indicators\n"
        f"| Indicator | Value | Signal |\n"
        f"|-----------|-------|--------|\n"
        f"| RSI(14) | {rsi} | {'Oversold ⚠️' if rsi < 30 else 'Overbought ⚠️' if rsi > 70 else 'Neutral ✅'} |\n"
        f"| MACD | {macd_val} | {macd_desc} |\n"
        f"| BB Position | {bb_pos}% | {'Near upper' if bb_pos > 80 else 'Near lower' if bb_pos < 20 else 'Mid-range'} |\n"
        f"| Volume | {vol}x avg | {'High' if vol > 1.5 else 'Normal' if vol > 0.8 else 'Low'} |\n\n"
        f"### 📈 Key Levels\n"
        f"| Level | Price |\n"
        f"|-------|-------|\n"
        f"| Resistance | ${res} |\n"
        f"| MA20 | ${ma20} |\n"
        f"| MA50 | ${ma50} |\n"
        f"| MA200 | ${ma200} |\n"
        f"| Support | ${sup} |\n\n"
        f"### 📉 Performance\n"
        f"1D: {chg:+.1f}% | 5D: {chg5:+.1f}% | 20D: {chg20:+.1f}%\n\n"
        f"### 🎯 Bollinger Bands\n"
        f"Upper: ${bb_upper} | Lower: ${bb_lower}\n\n"
        f"---\n"
        f"📱 Get daily TA signals for 5 stocks → **t.me/BroadInvestBot**\n"
        f"Free. No spam. Just levels that matter."
    )
    return content


def generate_bluesky_post(data):
    """Generate Bluesky thread (3 posts, 300 chars each)."""
    s = data['symbol']
    n = data['name']
    p = data['price']
    chg = data['change_pct']
    rsi = data['rsi']
    bias = data['bias']
    trend = data['trend_short']
    res = data['resistance']
    sup = data['support']
    macd = data['macd']
    macd_sig = data['macd_signal']
    vol = data['vol_ratio']

    macd_short = "bullish" if macd > macd_sig else "bearish"
    posts = [
        f"1/ ${s} {n} 💰 {p} ({chg:+.1f}%)\n\nSetup: {trend}\nRSI: {rsi} | MACD: {macd_short}\nVol: {vol}x avg",
        f"2/ Key levels:\n🎯 Resistance: ${res}\n🛡️ Support: ${sup}\n\nBias: {bias.upper()}\n\nWatch these. Respect them.",
        f"3/ More ${s} + 4 other tickers every day → t.me/BroadInvestBot\n\nFree TA signals. No BS.",
    ]
    return posts


def generate_threads_post(data):
    """Generate Threads thread (4 posts, 500 chars each)."""
    s = data['symbol']
    n = data['name']
    p = data['price']
    chg = data['change_pct']
    rsi = data['rsi']
    ma20 = data['ma20']
    ma50 = data['ma50']
    macd = data['macd']
    macd_sig = data['macd_signal']
    res = data['resistance']
    sup = data['support']
    bias = data['bias']
    trend = data['trend_short']
    vol = data['vol_ratio']
    chg5 = data['change_5d']
    chg20 = data['change_20d']

    macd_desc = "MACD bullish, momentum intact" if macd > macd_sig else "MACD bearish, caution warranted"
    mcap = format_market_cap(data['market_cap'])

    posts = [
        f"1/ ${s} — {n}\n\n{p} ({chg:+.1f}% today) | {mcap}\n\n{trend.upper()}. This is the setup you need to see.",
        f"2/ Technical snapshot:\nRSI {rsi} — momentum zone\n{macd_desc}\nMA20 ${ma20} | MA50 ${ma50}\nVolume: {vol}x avg\n5D: {chg5:+.1f}% | 20D: {chg20:+.1f}%",
        f"3/ The trade:\nResistance: ${res}\nSupport: ${sup}\nBias: {bias.upper()}\n\n{'Bounce play if support holds' if bias == 'bullish' else 'Wait for confirmation before entry' if bias == 'neutral' else 'Risk-off until trend reverses'}",
        f"4/ I post TA signals for 5 stocks daily.\n\n📱 Get them free: t.me/BroadInvestBot",
    ]
    return posts


def generate_telegram_post(data):
    """Generate Telegram channel post (2000 chars, detailed TA)."""
    s = data['symbol']
    n = data['name']
    p = data['price']
    chg = data['change_pct']
    rsi = data['rsi']
    ma20 = data['ma20']
    ma50 = data['ma50']
    ma200 = data['ma200']
    macd_val = data['macd']
    macd_sig = data['macd_signal']
    bb_upper = data['bb_upper']
    bb_lower = data['bb_lower']
    bb_pos = data['bb_position']
    res = data['resistance']
    sup = data['support']
    bias = data['bias']
    trend = data['trend_short']
    vol = data['vol_ratio']
    chg5 = data['change_5d']
    chg20 = data['change_20d']
    mcap = format_market_cap(data['market_cap'])

    bias_emoji = "🟢" if bias == "bullish" else "🔴" if bias == "bearish" else "🟡"

    content = (
        f"{bias_emoji} <b>${s} Technical Analysis</b> — {n}\n\n"
        f"💰 Price: ${p} ({chg:+.1f}%) | Cap: {mcap}\n"
        f"📊 Setup: <b>{trend}</b> | Bias: <b>{bias.upper()}</b>\n\n"
        f"<b>Indicators:</b>\n"
        f"• RSI(14): {rsi}{' — ⚠️ Oversold' if rsi < 30 else ' — ⚠️ Overbought' if rsi > 70 else ''}\n"
        f"• MACD: {macd_val:.2f} (Signal: {macd_sig:.2f}) — {'Bullish' if macd_val > macd_sig else 'Bearish'}\n"
        f"• BB: ${bb_lower} — ${bb_upper} (Position: {bb_pos}%)\n"
        f"• Volume: {vol}x average\n\n"
        f"<b>Moving Averages:</b>\n"
        f"• MA20: ${ma20} | MA50: ${ma50} | MA200: ${ma200}\n"
        f"• {'Price above all MAs ✅' if p > ma20 and p > ma50 and p > ma200 else 'Mixed alignment ⚠️' if p > ma200 else 'Bearish alignment ❌'}\n\n"
        f"<b>Performance:</b>\n"
        f"• 1D: {chg:+.1f}% | 5D: {chg5:+.1f}% | 20D: {chg20:+.1f}%\n\n"
        f"<b>Key Levels:</b>\n"
        f"• Resistance: ${res}\n"
        f"• Support: ${sup}\n\n"
        f"<b>Trade Idea:</b>\n"
        f"{'Bounce entry at $' + str(round(sup*1.02, 2)) + ' with stop below $' + str(round(sup*0.98, 2)) if bias == 'bullish' and rsi < 40 else 'Breakout entry above $' + str(round(res, 2)) + ' on volume confirmation' if bias == 'bullish' else 'Wait for support confirmation at $' + str(round(sup*1.01, 2))}\n\n"
        f"📱 <b>Free daily TA signals</b> — message @BroadInvestBot"
    )
    return content


def generate_stocktwits_post(data):
    """Generate StockTwits message (140 chars, cashtag required)."""
    s = data['symbol']
    p = data['price']
    chg = data['change_pct']
    rsi = data['rsi']
    bias = data['bias']
    trend = data['trend_short']
    res = data['resistance']
    sup = data['sup']

    if len(trend) > 25:
        trend_short = trend[:22] + ".."

    content = (
        f"${s} {p} ({chg:+.1f}%) RSI{rsi} {trend}. "
        f"R:{res} S:{sup}. {bias.upper()}. "
        f"Bot: t.me/BroadInvestBot"
    )
    # StockTwits has 140 char limit
    if len(content) > 140:
        content = content[:137] + ".."
    return content


def generate_content_for_platform(data, platform):
    """Generate platform-specific content for a stock."""
    generators = {
        'twitter': lambda d: generate_twitter_thread(d),
        'mastodon': lambda d: generate_mastodon_post(d),
        'discord': lambda d: generate_discord_post(d),
        'bluesky': lambda d: generate_bluesky_post(d),
        'threads': lambda d: generate_threads_post(d),
        'telegram': lambda d: generate_telegram_post(d),
        'stocktwits': lambda d: generate_stocktwits_post(d),
    }

    gen = generators.get(platform)
    if gen is None:
        return None

    return gen(data)


def save_to_queue(platform, symbol, content):
    """Save generated content to the knowledge queue."""
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H%M%S')

    # For thread-based platforms, content is a list. Join with delimiter.
    if isinstance(content, list):
        # Remove the numbering for queue storage (already formatted)
        content_str = "---THREAD_BREAK---".join(content)
        content_type = "thread"
    else:
        content_str = content
        content_type = "single"

    queue_entry = {
        "platform": platform,
        "topic": f"{symbol}_ta_analysis",
        "agent": "daily_stock_content",
        "content": content_str,
        "content_type": content_type,
        "symbol": symbol,
        "created": now.isoformat(),
        "used": False,
    }

    filename = f"{date_str}_{time_str}_{platform}_{symbol}_ta.json"
    filepath = QUEUE_DIR / filename

    filepath.write_text(json.dumps(queue_entry, ensure_ascii=False, indent=2), encoding='utf-8')
    return filepath


def main():
    print("=" * 60)
    print("Daily Stock TA Content Generator")
    print("=" * 60)

    # Randomly pick 5 stocks from watchlist
    picks = random.sample(WATCHLIST, min(DAILY_PICKS, len(WATCHLIST)))
    print(f"\nSelected symbols: {', '.join(picks)}")

    platforms = ['twitter', 'mastodon', 'discord', 'bluesky', 'threads', 'telegram', 'stocktwits']
    generated = 0
    stocks_fetched = 0

    for symbol in picks:
        print(f"\n--- ${symbol} ---")

        # Fetch real data
        try:
            data = get_stock_data(symbol)
        except Exception as e:
            print(f"  ❌ Data fetch failed: {e}")
            continue

        if data is None:
            print(f"  ⚠️ Insufficient data (need 20+ days), skipping")
            continue

        print(f"  ✅ ${data['price']} ({data['change_pct']:+.1f}%) | RSI: {data['rsi']} | Bias: {data['bias']}")
        stocks_fetched += 1

        # Generate content for each platform
        for platform in platforms:
            try:
                content = generate_content_for_platform(data, platform)
                if content is None:
                    continue

                filepath = save_to_queue(platform, symbol, content)
                print(f"  📝 {platform:12s} → {filepath.name}")
                generated += 1
            except Exception as e:
                print(f"  ❌ {platform}: generation failed - {e}")

    print(f"\n{'=' * 60}")
    print(f"Done: {stocks_fetched} stocks → {generated} posts across {len(platforms)} platforms")
    print(f"Queue: {QUEUE_DIR}")

    # Summary stats
    queue_files = list(QUEUE_DIR.glob("*.json"))
    unused = sum(1 for f in queue_files if f.name != "README.md"
                 and json.loads(f.read_text(encoding='utf-8')).get('used', False) is False)
    print(f"Queue status: {len(queue_files) - 1} files, {unused} unused")
    print("=" * 60)


if __name__ == "__main__":
    main()
