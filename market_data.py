"""
📈 BroadFSC Real-Time Market Data Module
========================================
Uses yfinance (free, no API key) to fetch real-time stock/crypto/commodity/index data.
Automatically detects stock-related queries and injects live data into AI context.

Supported markets:
  - US Stocks (AAPL, TSLA, NVDA, etc.)
  - A-Shares (600519.SS, 000001.SZ, etc.)
  - HK Stocks (9988.HK, 0700.HK, etc.)
  - Crypto (BTC-USD, ETH-USD, etc.)
  - Commodities (GC=F Gold, CL=F Oil, SI=F Silver)
  - Forex (EURUSD=X, GBPUSD=X, USDJPY=X, USDCNY=X)
  - Indices (^GSPC S&P500, ^DJI Dow, ^IXIC Nasdaq, ^HSI HangSeng, 000001.SS SSE)
"""

import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ============================================================
# 📋 股票/市场关键词检测 — 中英文支持
# ============================================================

# 美股 ticker → 名称映射
US_STOCK_MAP = {
    "aapl": "AAPL", "apple": "AAPL", "苹果": "AAPL",
    "tsla": "TSLA", "tesla": "TSLA", "特斯拉": "TSLA",
    "nvda": "NVDA", "nvidia": "NVDA", "英伟达": "NVDA",
    "msft": "MSFT", "microsoft": "MSFT", "微软": "MSFT",
    "amzn": "AMZN", "amazon": "AMZN", "亚马逊": "AMZN",
    "googl": "GOOGL", "google": "GOOGL", "谷歌": "GOOGL",
    "goog": "GOOG",
    "meta": "META", "facebook": "META", "脸书": "META",
    "brk.b": "BRK-B", "brk.a": "BRK-A", "巴菲特": "BRK-B", "berkshire": "BRK-B",
    "jpm": "JPM", "摩根大通": "JPM",
    "v": "V", "visa": "V",
    "jnj": "JNJ", "强生": "JNJ",
    "wmt": "WMT", "沃尔玛": "WMT",
    "xom": "XOM", "exxon": "XOM", "埃克森": "XOM",
    "cvx": "CVX", "chevron": "CVX", "雪佛龙": "CVX",
    "mpc": "MPC", "marathon": "MPC", "马拉松": "MPC",
    "ko": "KO", "coca-cola": "KO", "可口可乐": "KO",
    "pltr": "PLTR", "palantir": "PLTR",
    "amd": "AMD", "超微": "AMD",
    "tsm": "TSM", "台积电": "TSM", "tsmc": "TSM",
    "nflx": "NFLX", "netflix": "NFLX",
    "dis": "DIS", "disney": "DIS",
    "ba": "BA", "boeing": "BA", "波音": "BA",
    "crm": "CRM", "salesforce": "CRM",
    "intc": "INTC", "intel": "INTC", "英特尔": "INTC",
}

# A股代码 → yfinance 格式
A_STOCK_MAP = {
    "600519": "600519.SS", "茅台": "600519.SS", "贵州茅台": "600519.SS",
    "000858": "000858.SZ", "五粮液": "000858.SZ",
    "300750": "300750.SZ", "宁德时代": "300750.SZ",
    "601318": "601318.SS", "中国平安": "601318.SS",
    "600036": "600036.SS", "招商银行": "600036.SS",
    "000001": "000001.SZ", "平安银行": "000001.SZ",
    "600900": "600900.SS", "长江电力": "600900.SS",
    "002594": "002594.SZ", "比亚迪": "002594.SZ",
    "601012": "601012.SS", "隆基绿能": "601012.SS",
    "000333": "000333.SZ", "美的集团": "000333.SZ",
    "600276": "600276.SS", "恒瑞医药": "600276.SS",
    "601398": "601398.SS", "工商银行": "601398.SS",
}

# 港股代码 → yfinance 格式
HK_STOCK_MAP = {
    "9988": "9988.HK", "9988.HK": "9988.HK", "阿里": "9988.HK", "阿里巴巴": "9988.HK",
    "0700": "0700.HK", "0700.HK": "0700.HK", "腾讯": "0700.HK",
    "9999": "9999.HK", "网易": "9999.HK",
    "3690": "3690.HK", "美团": "3690.HK",
    "9618": "9618.HK", "京东": "9618.HK",
    "1810": "1810.HK", "小米": "1810.HK",
    "9868": "9868.HK", "小鹏": "9868.HK",
    "9866": "9866.HK", "蔚来": "9866.HK",
    "0241": "0241.HK", "阿里健康": "0241.HK",
    "2382": "2382.HK", "舜宇光学": "2382.HK",
}

# 加密货币
CRYPTO_MAP = {
    "btc": "BTC-USD", "bitcoin": "BTC-USD", "比特币": "BTC-USD",
    "eth": "ETH-USD", "ethereum": "ETH-USD", "以太坊": "ETH-USD",
    "sol": "SOL-USD", "solana": "SOL-USD",
    "bnb": "BNB-USD", "xrp": "XRP-USD",
}

# 大宗商品
COMMODITY_MAP = {
    "gold": "GC=F", "黄金": "GC=F", "xau": "GC=F",
    "silver": "SI=F", "白银": "SI=F", "xag": "SI=F",
    "oil": "CL=F", "crude": "CL=F", "原油": "CL=F", "wti": "CL=F",
    "natural gas": "NG=F", "天然气": "NG=F",
    "copper": "HG=F", "铜": "HG=F",
}

# 外汇
FOREX_MAP = {
    "eurusd": "EURUSD=X", "欧元": "EURUSD=X",
    "gbpusd": "GBPUSD=X", "英镑": "GBPUSD=X",
    "usdjpy": "USDJPY=X", "日元": "USDJPY=X",
    "usdcny": "USDCNY=X", "人民币": "USDCNY=X", "usdcnh": "USDCNY=X",
    "audusd": "AUDUSD=X", "澳元": "AUDUSD=X",
}

# 指数
INDEX_MAP = {
    "s&p": "^GSPC", "sp500": "^GSPC", "标普": "^GSPC", "标普500": "^GSPC",
    "nasdaq": "^IXIC", "纳指": "^IXIC", "纳斯达克": "^IXIC",
    "dow": "^DJI", "道指": "^DJI", "道琼斯": "^DJI",
    "hsi": "^HSI", "恒指": "^HSI", "恒生": "^HSI",
    "sse": "000001.SS", "上证": "000001.SS", "上证指数": "000001.SS",
    "vix": "^VIX", "恐慌指数": "^VIX",
}

# 合并所有映射
ALL_MAPS = {**US_STOCK_MAP, **A_STOCK_MAP, **HK_STOCK_MAP, 
            **CRYPTO_MAP, **COMMODITY_MAP, **FOREX_MAP, **INDEX_MAP}

# ============================================================
# 🔍 股票查询意图检测
# ============================================================

# 股票相关关键词（触发实时数据查询）
STOCK_KEYWORDS = [
    # English
    "stock", "share", "price", "quote", "market", "ticker", "portfolio",
    "buy", "sell", "hold", "bull", "bear", "rally", "crash", "dip",
    "earnings", "revenue", "profit", "dividend", "pe ratio", "market cap",
    "support", "resistance", "moving average", "ma", "rsi", "macd",
    "gold", "oil", "bitcoin", "crypto", "forex", "index", "futures",
    "btc", "eth", "xau", "s&p", "nasdaq", "dow", "hsi",
    # Chinese
    "股价", "股票", "行情", "报价", "市值", "涨跌", "涨停", "跌停",
    "买入", "卖出", "持有", "牛市", "熊市", "反弹", "暴跌", "回调",
    "财报", "营收", "利润", "分红", "股息", "市盈率", "市净率",
    "支撑", "阻力", "均线", "技术面", "基本面", "资金流",
    "黄金", "原油", "比特币", "加密", "汇率", "指数", "期货",
    "分析", "走势", "预测", "目标价", "标普", "纳指", "恒指",
]

def detect_stock_query(message: str) -> list:
    """
    检测用户消息中是否包含股票/市场查询意图。
    返回需要查询的 yfinance ticker 列表。
    """
    msg_lower = message.lower().strip()
    tickers = []
    
    # 1. 直接匹配关键词映射
    for keyword, ticker in ALL_MAPS.items():
        if keyword in msg_lower:
            if ticker not in tickers:
                tickers.append(ticker)
    
    # 2. 检测纯 ticker 格式（如 "AAPL", "TSLA"）
    #    注意：需要排除被关键词映射已匹配到的部分（如 "9988.HK" 中的 "HK"）
    already_matched_parts = set()
    for t in tickers:
        for part in t.replace(".", " ").split():
            already_matched_parts.add(part.upper())
    
    ticker_pattern = r'\b([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\b'
    for match in re.finditer(ticker_pattern, message):
        candidate = match.group(1)
        # 排除常见英文单词
        common_words = {"THE", "AND", "FOR", "NOT", "ARE", "BUT", "ALL", "CAN", "HAS",
                       "THIS", "THAT", "WITH", "FROM", "HAVE", "WILL", "BEEN", "THEY",
                       "WANT", "LIKE", "JUST", "KNOW", "GOOD", "LOOK", "THAN", "MORE",
                       "SOME", "WHAT", "WHEN", "HOW", "WHY", "WHO", "YES", "BUY", "HOLD",
                       "SELL", "HIGH", "LOW", "BIG", "NEW", "OLD", "GET", "LET", "USE",
                       "HER", "HIM", "HIS", "OUR", "ITS", "MAY", "MIGHT", "ALSO", "BACK",
                       "STILL", "EACH", "VERY", "MUCH", "OWN", "SAID", "WENT", "CAME",
                       "MADE", "DID", "GOT", "SEE", "WAY", "DAY", "SAY", "TOO", "ANY",
                       "NOW", "OVER", "SUCH", "THROUGH", "INTO", "JUST", "ONLY",
                       # 排除交易所后缀（它们是已匹配 ticker 的一部分）
                       "HK", "SS", "SZ", "SH", "US"}
        # 排除太短的纯字母（2字母大多是介词/代词，除了已知的 US ticker）
        base = candidate.split('.')[0]
        if len(base) <= 2 and candidate not in US_STOCK_MAP:
            continue
        if candidate in common_words or candidate in already_matched_parts:
            continue
        if candidate not in tickers and 2 <= len(base) <= 5:
            tickers.append(candidate)
    
    # 3. 检测 A股代码格式（6位数字）
    a_stock_pattern = r'(\d{6})'
    for match in re.finditer(a_stock_pattern, message):
        code = match.group(1)
        if code in A_STOCK_MAP:
            ticker = A_STOCK_MAP[code]
            if ticker not in tickers:
                tickers.append(ticker)
        elif code.startswith(('6', '5')):
            ticker = f"{code}.SS"
            if ticker not in tickers:
                tickers.append(ticker)
        elif code.startswith(('0', '3')):
            ticker = f"{code}.SZ"
            if ticker not in tickers:
                tickers.append(ticker)
    
    # 4. 检测港股代码格式（4-5位数字+.HK）
    hk_pattern = r'(\d{4,5}\.HK)'
    for match in re.finditer(hk_pattern, message, re.IGNORECASE):
        ticker = match.group(1).upper()
        if ticker not in tickers:
            tickers.append(ticker)
    
    # 5. 如果消息包含股票关键词但没有匹配到具体 ticker，不返回任何 ticker
    #    （让 AI 用通用知识回答）
    
    # 限制最多 5 个 ticker（避免 API 过载）
    return tickers[:5]


def is_stock_related(message: str) -> bool:
    """判断消息是否与股票/市场相关"""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in STOCK_KEYWORDS)


# ============================================================
# 📊 实时数据获取
# ============================================================

# 数据缓存（避免短时间内重复查询同一 ticker）
_cache = {}
_CACHE_TTL = 120  # 2分钟缓存

def _is_cache_valid(cache_entry: dict) -> bool:
    """检查缓存是否仍然有效"""
    if not cache_entry:
        return False
    elapsed = (datetime.now(timezone.utc) - cache_entry.get("timestamp", datetime.min.replace(tzinfo=timezone.utc))).total_seconds()
    return elapsed < _CACHE_TTL


def fetch_stock_data(ticker: str) -> dict | None:
    """
    获取单只股票/资产的实时数据。
    返回字典格式的市场数据，失败返回 None。
    """
    # 检查缓存
    if ticker in _cache and _is_cache_valid(_cache[ticker]):
        return _cache[ticker]["data"]
    
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 尝试从 info 获取价格
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        
        # 如果 info 没有价格，用 history 获取
        if price is None:
            hist = stock.history(period="5d")
            if hist.empty:
                logger.warning(f"No data for {ticker}")
                return None
            price = float(hist['Close'].iloc[-1])
            if prev_close is None and len(hist) > 1:
                prev_close = float(hist['Close'].iloc[-2])
        
        # 计算涨跌
        change = None
        change_pct = None
        if price and prev_close and prev_close > 0:
            change = round(price - prev_close, 4)
            change_pct = round((change / prev_close) * 100, 2)
        
        result = {
            "symbol": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "price": round(price, 2) if price else None,
            "currency": info.get("currency", "USD"),
            "prev_close": round(prev_close, 2) if prev_close else None,
            "change": change,
            "change_pct": change_pct,
            "open": info.get("regularMarketOpen") or info.get("open"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "dividend_yield": info.get("dividendYield"),
            "exchange": info.get("exchange") or info.get("fullExchangeName"),
            "data_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        
        # 缓存
        _cache[ticker] = {
            "data": result,
            "timestamp": datetime.now(timezone.utc)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch {ticker}: {e}")
        return None


def fetch_multiple(tickers: list) -> list[dict]:
    """批量获取多只股票数据"""
    results = []
    for ticker in tickers:
        data = fetch_stock_data(ticker)
        if data:
            results.append(data)
    return results


def format_market_data_for_ai(tickers: list) -> str:
    """
    格式化实时市场数据，注入 AI system prompt。
    返回格式化的文本，AI 可以基于此数据回答用户问题。
    """
    if not tickers:
        return ""
    
    results = fetch_multiple(tickers)
    if not results:
        return ""
    
    lines = [
        "📈 REAL-TIME MARKET DATA (inject into your answer — use these ACTUAL numbers, do NOT fabricate data):",
        ""
    ]
    
    for r in results:
        symbol = r["symbol"]
        name = r["name"]
        price = r["price"]
        currency = r["currency"]
        change = r["change"]
        change_pct = r["change_pct"]
        data_time = r["data_time"]
        
        # 价格行
        price_str = f"  {name} ({symbol}): {currency} {price:,.2f}"
        if change is not None and change_pct is not None:
            arrow = "🔺" if change > 0 else "🔻" if change < 0 else "➡️"
            price_str += f"  {arrow} {change:+,.2f} ({change_pct:+.2f}%)"
        lines.append(price_str)
        
        # 详细信息
        details = []
        if r.get("open"):
            details.append(f"Open: {r['open']:,.2f}")
        if r.get("day_high") and r.get("day_low"):
            details.append(f"Range: {r['day_low']:,.2f} - {r['day_high']:,.2f}")
        if r.get("volume"):
            details.append(f"Vol: {r['volume']:,}")
        if r.get("market_cap"):
            mc = r['market_cap']
            if mc >= 1e12:
                details.append(f"MktCap: ${mc/1e12:.1f}T")
            elif mc >= 1e9:
                details.append(f"MktCap: ${mc/1e9:.1f}B")
        if r.get("pe_ratio"):
            details.append(f"P/E: {r['pe_ratio']:.1f}")
        if r.get("52w_high") and r.get("52w_low"):
            details.append(f"52w: {r['52w_low']:,.2f} - {r['52w_high']:,.2f}")
        if r.get("dividend_yield"):
            details.append(f"Div: {r['dividend_yield']*100:.2f}%")
        
        if details:
            lines.append(f"    {' | '.join(details)}")
    
    lines.append("")
    lines.append(f"⏰ Data as of: {results[0]['data_time']}")
    lines.append("⚠️ IMPORTANT: Use ONLY these real-time numbers. NEVER make up stock prices or financial data.")
    
    return "\n".join(lines)


# ============================================================
# 🧪 测试
# ============================================================

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    logging.basicConfig(level=logging.INFO)
    
    # Test detection
    test_messages = [
        "What's Apple stock price?",
        "帮我分析一下特斯拉",
        "BTC现在多少钱",
        "黄金走势怎么样",
        "How is the S&P 500 doing?",
        "600519贵州茅台",
        "9988.HK",
        "EURUSD汇率",
        "I want to invest in NVDA",
        "Hello, how are you?",  # 非股票消息
    ]
    
    print("=== Stock Query Detection ===")
    for msg in test_messages:
        tickers = detect_stock_query(msg)
        related = is_stock_related(msg)
        print(f"  '{msg}' → tickers={tickers}, related={related}")
    
    print("\n=== Real-Time Data Fetch ===")
    # Test fetching
    test_tickers = ["AAPL", "600519.SS", "BTC-USD", "GC=F"]
    for t in test_tickers:
        data = fetch_stock_data(t)
        if data:
            print(f"  ✅ {data['name']} ({data['symbol']}): {data['currency']} {data['price']:,.2f}")
        else:
            print(f"  ❌ {t}: No data")
    
    print("\n=== Formatted for AI ===")
    formatted = format_market_data_for_ai(["AAPL", "BTC-USD"])
    print(formatted)
