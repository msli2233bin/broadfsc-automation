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
    # Tech
    "aapl": "AAPL", "apple": "AAPL", "苹果": "AAPL",
    "tsla": "TSLA", "tesla": "TSLA", "特斯拉": "TSLA",
    "nvda": "NVDA", "nvidia": "NVDA", "英伟达": "NVDA",
    "msft": "MSFT", "microsoft": "MSFT", "微软": "MSFT",
    "amzn": "AMZN", "amazon": "AMZN", "亚马逊": "AMZN",
    "googl": "GOOGL", "google": "GOOGL", "谷歌": "GOOGL",
    "goog": "GOOG",
    "meta": "META", "facebook": "META", "脸书": "META",
    "pltr": "PLTR", "palantir": "PLTR",
    "amd": "AMD", "超微": "AMD", "超微半导体": "AMD",
    "tsm": "TSM", "台积电": "TSM", "tsmc": "TSM",
    "nflx": "NFLX", "netflix": "NFLX", "奈飞": "NFLX",
    "dis": "DIS", "disney": "DIS", "迪士尼": "DIS",
    "crm": "CRM", "salesforce": "CRM",
    "intc": "INTC", "intel": "INTC", "英特尔": "INTC",
    "avgo": "AVGO", "broadcom": "AVGO", "博通": "AVGO",
    "orcl": "ORCL", "oracle": "ORCL", "甲骨文": "ORCL",
    "adbe": "ADBE", "adobe": "ADBE",
    "ibm": "IBM", "ibm": "IBM",
    "pypl": "PYPL", "paypal": "PYPL", "贝宝": "PYPL",
    "sq": "SQ", "block": "SQ", "square": "SQ",
    "uber": "UBER", "优步": "UBER",
    "abnb": "ABNB", "airbnb": "ABNB",
    "spot": "SPOT", "spotify": "SPOT",
    "snap": "SNAP", "snowflake": "SNOW", "snow": "SNOW",
    "crwd": "CRWD", "crowdstrike": "CRWD",
    "panw": "PANW", "mdb": "MDB", "mongodb": "MDB",
    "shop": "SHOP", "shopify": "SHOP",
    "roi": "ROI", "roku": "ROKU",
    # Finance
    "brk.b": "BRK-B", "brk.a": "BRK-A", "巴菲特": "BRK-B", "berkshire": "BRK-B", "伯克希尔": "BRK-B",
    "jpm": "JPM", "摩根大通": "JPM",
    "v": "V", "visa": "V", "维萨": "V",
    "ma": "MA", "mastercard": "MA", "万事达": "MA",
    "gs": "GS", "goldman sachs": "GS", "高盛": "GS",
    "ms": "MS", "morgan stanley": "MS", "摩根士丹利": "MS",
    "bac": "BAC", "bank of america": "BAC", "美国银行": "BAC",
    "c": "C", "citigroup": "C", "花旗": "C",
    "wfc": "WFC", "wells fargo": "WFC", "富国银行": "WFC",
    "blk": "BLK", "blackrock": "BLK", "贝莱德": "BLK",
    "axp": "AXP", "amex": "AXP", "american express": "AXP", "美国运通": "AXP",
    # Healthcare / Pharma
    "jnj": "JNJ", "强生": "JNJ",
    "pfe": "PFE", "pfizer": "PFE", "辉瑞": "PFE",
    "unh": "UNH", "unitedhealth": "UNH", "联合健康": "UNH",
    "abbv": "ABBV", "abbvie": "ABBV", "艾伯维": "ABBV",
    "mrxn": "MRK", "merck": "MRK", "默沙东": "MRK", "默克": "MRK",
    "lly": "LLY", "lilly": "LLY", "礼来": "LLY",
    "roche": "RHHBY", "罗氏": "RHHBY",
    "novartis": "NVS", "诺华": "NVS",
    "azn": "AZN", "astrazeneca": "AZN", "阿斯利康": "AZN",
    "nvo": "NVO", "novo nordisk": "NVO", "诺和诺德": "NVO",
    "mrna": "MRNA", "moderna": "MRNA",
    "biontech": "BNTX", "bntx": "BNTX",
    "gild": "GILD", "gilead": "GILD", "吉利德": "GILD",
    "amgn": "AMGN", "amgen": "AMGN", "安进": "AMGN",
    "biib": "BIIB", "biogen": "BIIB",
    "regeneron": "REGN", "regn": "REGN",
    "mrk": "MRK",
    # Consumer
    "wmt": "WMT", "沃尔玛": "WMT",
    "ko": "KO", "coca-cola": "KO", "可口可乐": "KO",
    "pep": "PEP", "pepsico": "PEP", "百事": "PEP",
    "mcd": "MCD", "mcdonalds": "MCD", "麦当劳": "MCD",
    "sbux": "SBUX", "starbucks": "SBUX", "星巴克": "SBUX",
    "nke": "NKE", "nike": "NKE", "耐克": "NKE",
    "pg": "PG", "procter": "PG", "宝洁": "PG",
    "cost": "COST", "costco": "COST", "好市多": "COST",
    # Energy
    "xom": "XOM", "exxon": "XOM", "埃克森": "XOM", "埃克森美孚": "XOM",
    "cvx": "CVX", "chevron": "CVX", "雪佛龙": "CVX",
    "mpc": "MPC", "marathon": "MPC",
    "cop": "COP", "conocophillips": "COP",
    "slb": "SLB", "schlumberger": "SLB",
    # Industrial / Aerospace
    "ba": "BA", "boeing": "BA", "波音": "BA",
    "cat": "CAT", "caterpillar": "CAT", "卡特彼勒": "CAT",
    "ge": "GE", "general electric": "GE", "通用电气": "GE",
    "mmm": "MMM", "3m": "MMM",
    "hon": "HON", "honeywell": "HON", "霍尼韦尔": "HON",
    "rtx": "RTX", "raytheon": "RTX",
    "lmt": "LMT", "lockheed": "LMT", "洛克希德": "LMT",
    # Semis
    "mu": "MU", "micron": "MU", "美光": "MU",
    "qcom": "QCOM", "qualcomm": "QCOM", "高通": "QCOM",
    "txn": "TXN", "texas instruments": "TXN", "德州仪器": "TXN",
    "nxpi": "NXPI", "nxp": "NXPI",
    "asml": "ASML", "阿斯麦": "ASML",
}

# A股代码 → yfinance 格式
A_STOCK_MAP = {
    # 白酒/消费
    "600519": "600519.SS", "茅台": "600519.SS", "贵州茅台": "600519.SS",
    "000858": "000858.SZ", "五粮液": "000858.SZ",
    "000568": "000568.SZ", "泸州老窖": "000568.SZ",
    "603369": "603369.SS", "今世缘": "603369.SS",
    # 新能源/汽车
    "300750": "300750.SZ", "宁德时代": "300750.SZ",
    "002594": "002594.SZ", "比亚迪": "002594.SZ",
    "601012": "601012.SS", "隆基绿能": "601012.SS", "隆基": "601012.SS",
    "600438": "600438.SS", "通威股份": "600438.SS",
    "002475": "002475.SZ", "立讯精密": "002475.SZ",
    # 金融
    "601318": "601318.SS", "中国平安": "601318.SS",
    "600036": "600036.SS", "招商银行": "600036.SS",
    "000001": "000001.SZ", "平安银行": "000001.SZ",
    "601398": "601398.SS", "工商银行": "601398.SS",
    "601288": "601288.SS", "农业银行": "601288.SS",
    "600016": "600016.SS", "民生银行": "600016.SS",
    "601166": "601166.SS", "兴业银行": "601166.SS",
    "600000": "600000.SS", "浦发银行": "600000.SS",
    "601988": "601988.SS", "中国银行": "601988.SS",
    "601328": "601328.SS", "交通银行": "601328.SS",
    # 医药
    "600276": "600276.SS", "恒瑞医药": "600276.SS",
    "000538": "000538.SZ", "云南白药": "000538.SZ",
    "600422": "600422.SS", "昆药集团": "600422.SS", "昆药": "600422.SS",
    "300760": "300760.SZ", "迈瑞医疗": "300760.SZ",
    "603259": "603259.SS", "药明康德": "603259.SS",
    "300015": "300015.SZ", "爱尔眼科": "300015.SZ",
    "002007": "002007.SZ", "华兰生物": "002007.SZ",
    "300122": "300122.SZ", "智飞生物": "300122.SZ",
    "000963": "000963.SZ", "华东医药": "000963.SZ",
    "300347": "300347.SZ", "泰格医药": "300347.SZ",
    "688111": "688111.SS", "金山办公": "688111.SS",
    # 科技
    "000333": "000333.SZ", "美的集团": "000333.SZ", "美的": "000333.SZ",
    "000651": "000651.SZ", "格力电器": "000651.SZ", "格力": "000651.SZ",
    "002415": "002415.SZ", "海康威视": "002415.SZ",
    "600588": "600588.SS", "用友网络": "600588.SS",
    "688981": "688981.SS", "中芯国际": "688981.SS",
    # 电力/基建
    "600900": "600900.SS", "长江电力": "600900.SS",
    "601668": "601668.SS", "中国建筑": "601668.SS",
    "601669": "601669.SS", "中国电建": "601669.SS",
    "600585": "600585.SS", "海螺水泥": "600585.SS",
    # 地产
    "000002": "000002.SZ", "万科": "000002.SZ", "万科A": "000002.SZ",
    # 保险
    "601601": "601601.SS", "中国太保": "601601.SS",
    "601628": "601628.SS", "中国人寿": "601628.SS",
}

# 港股代码 → yfinance 格式
HK_STOCK_MAP = {
    # 互联网/科技
    "9988": "9988.HK", "9988.HK": "9988.HK", "阿里": "9988.HK", "阿里巴巴": "9988.HK",
    "0700": "0700.HK", "0700.HK": "0700.HK", "腾讯": "0700.HK",
    "9999": "9999.HK", "网易": "9999.HK",
    "3690": "3690.HK", "美团": "3690.HK",
    "9618": "9618.HK", "京东": "9618.HK",
    "1810": "1810.HK", "小米": "1810.HK",
    "9868": "9868.HK", "小鹏": "9868.HK", "小鹏汽车": "9868.HK",
    "9866": "9866.HK", "蔚来": "9866.HK", "蔚来汽车": "9866.HK",
    "0241": "0241.HK", "阿里健康": "0241.HK",
    "2382": "2382.HK", "舜宇光学": "2382.HK",
    "9992": "9992.HK", "泡泡玛特": "9992.HK",
    "1024": "1024.HK", "快手": "1024.HK",
    "9888": "9888.HK", "百度": "9888.HK",
    "0772": "0772.HK", "阅文集团": "0772.HK",
    # 医药
    "2269": "2269.HK", "药明生物": "2269.HK",
    "1093": "1093.HK", "石药集团": "1093.HK",
    "1177": "1177.HK", "中国生物制药": "1177.HK",
    "2359": "2359.HK", "药明康德h": "2359.HK",
    # 金融
    "2318": "2318.HK", "中国平安h": "2318.HK",
    "1398": "1398.HK", "工商银行h": "1398.HK",
    "3988": "3988.HK", "中国银行h": "3988.HK",
    # 消费
    "0291": "0291.HK", "华润啤酒": "0291.HK",
    "6862": "6862.HK", "海底捞": "6862.HK",
    "2020": "2020.HK", "安踏": "2020.HK", "安踏体育": "2020.HK",
    # 新能源
    "9618": "9618.HK",
    "0175": "0175.HK", "吉利汽车": "0175.HK",
    # 物业/地产
    "1209": "1209.HK", "华润万象": "1209.HK",
    "0688": "0688.HK", "中国海外发展": "0688.HK",
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
        
        # 公司简介截取（前200字符，避免太长）
        business_summary = info.get("longBusinessSummary") or info.get("businessSummary") or ""
        if len(business_summary) > 200:
            business_summary = business_summary[:200] + "..."

        result = {
            "symbol": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "long_name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector") or "",
            "industry": info.get("industry") or "",
            "business_summary": business_summary,
            "country": info.get("country") or "",
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
    包含：公司名、行业、简介、实时行情数据。
    """
    if not tickers:
        return ""
    
    results = fetch_multiple(tickers)
    if not results:
        return ""
    
    lines = [
        "📈 REAL-TIME MARKET DATA (CRITICAL: use ONLY these actual numbers and company info. NEVER fabricate stock prices, company descriptions, or industry information):",
        ""
    ]
    
    for r in results:
        symbol = r["symbol"]
        name = r["name"]
        long_name = r.get("long_name", name)
        price = r["price"]
        currency = r["currency"]
        change = r["change"]
        change_pct = r["change_pct"]
        data_time = r["data_time"]
        
        # 公司基本信息行（行业+简介 — 这是最关键的修复）
        sector = r.get("sector", "")
        industry = r.get("industry", "")
        country = r.get("country", "")
        business = r.get("business_summary", "")
        
        company_info = f"  🏢 {long_name} ({symbol})"
        if sector:
            company_info += f" | Sector: {sector}"
        if industry:
            company_info += f" | Industry: {industry}"
        if country:
            company_info += f" | Country: {country}"
        lines.append(company_info)
        
        if business:
            lines.append(f"  📋 About: {business}")
        
        # 价格行
        price_str = f"  💰 Price: {currency} {price:,.2f}"
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
            elif mc >= 1e6:
                details.append(f"MktCap: ${mc/1e6:.1f}M")
        if r.get("pe_ratio"):
            details.append(f"P/E: {r['pe_ratio']:.1f}")
        if r.get("52w_high") and r.get("52w_low"):
            details.append(f"52w: {r['52w_low']:,.2f} - {r['52w_high']:,.2f}")
        if r.get("dividend_yield"):
            details.append(f"Div: {r['dividend_yield']*100:.2f}%")
        
        if details:
            lines.append(f"    {' | '.join(details)}")
        
        lines.append("")  # 空行分隔
    
    lines.append(f"⏰ Data as of: {results[0]['data_time']}")
    lines.append("")
    lines.append("⚠️ CRITICAL RULES:")
    lines.append("  1. Use ONLY the company name, sector, industry, and description shown above. Do NOT substitute with different company info.")
    lines.append("  2. Use ONLY the real-time prices shown above. Do NOT make up or estimate stock prices.")
    lines.append("  3. If the user asks about a stock NOT listed above, say you don't have real-time data for it rather than guessing.")
    lines.append("  4. Clearly state the stock symbol and exchange when discussing any stock.")
    
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
