// ═══════════════════════════════════════════════════
// BroadFSC Pro — App Logic v3 (SOUL Edition)
// AI with personality, memory, and real knowledge
// ═══════════════════════════════════════════════════

// ── SOUL AI Knowledge Base ──
const KNOWLEDGE = {
  technical: {
    'support resistance': "Support is a price floor where buyers step in. Resistance is a ceiling where sellers dominate. The key insight most miss: when support breaks, it becomes resistance — and vice versa. This 'role reversal' is one of the most reliable principles in trading. Look for 3+ touches to confirm a level, and always wait for a candle close beyond the level before acting.",
    'rsi': "RSI measures momentum on a 0-100 scale. Most people just use 70/30 overbought/oversold — that's the basic stuff. The real edge is RSI divergence: when price makes a lower low but RSI makes a higher low, selling pressure is fading. That's often the best entry signal you'll get. In uptrends, RSI tends to stay 40-80; in downtrends, 20-60. Adjust your levels accordingly.",
    'macd': "MACD shows momentum shifts. The crossover signals are decent, but the real power is the histogram — when bars shrink for 3+ periods after expansion, momentum is fading. That's often the early warning before a crossover even happens. I always combine MACD with 200 SMA as a trend filter: only take buy signals above 200 SMA. That alone filters ~40% of false signals.",
    'moving average': "Moving averages are the simplest and most powerful tools. 200 SMA is the most important — above it is bull territory, below is bear. The 50/200 crossover (Golden/Death Cross) isn't an entry signal, it's a trend confirmation. For actual entries, I prefer 9/21 EMA crossovers with RSI confirmation. Pro tip: when price pulls back to the 20 EMA in a strong trend, that's often the best entry you'll get.",
    'fibonacci': "Fibonacci retracement works because millions of traders use the same levels — it's self-fulfilling. 61.8% (the Golden Ratio) is the most important level. If price retraces beyond 61.8%, the trend is probably broken. My favorite play: wait for a pullback to the 38.2-50% zone, look for a reversal candle, enter with a stop below 61.8%. Confluence with S/R or a moving average makes it even stronger.",
    'bollinger bands': "Bollinger Bands measure volatility. The squeeze — when bands contract to their narrowest in 6 months — is the most powerful BB signal. It means a big move is coming. Don't predict direction; wait for the breakout with volume. Also, in strong trends, price can 'ride the bands' for days. Don't short just because price touched the upper band in an uptrend — that's a common beginner mistake.",
    'candlestick': "Candlesticks tell the story of the battle between buyers and sellers. Single candles like hammers and shooting stars are signals, not confirmations — always wait for the next candle. The most reliable patterns are three-candle formations: Morning Star (bullish reversal) and Evening Star (bearish reversal). At key S/R levels, these patterns are the most reliable signals in all of technical analysis.",
    'chart pattern': "Head & Shoulders, Double Tops, Triangles — these work because they represent shifts in supply and demand. The key: always wait for the neckline break before entering. The target is the pattern height projected from the breakout. Volume should decrease during formation and increase on breakout. Longer formations produce larger moves.",
    'volume': "Volume is the fuel behind price moves. Price up + volume up = healthy trend. Price up + volume down = weak rally, be cautious. The most powerful volume signal is the climax — extremely high volume after an extended move often marks the end. Also watch OBV (On-Balance Volume): if OBV is rising while price is flat, smart money is accumulating. That's a leading signal.",
    'breakout': "Most breakouts fail. That's the uncomfortable truth. To filter false breakouts: (1) Wait for candle CLOSE beyond the level, not just a wick. (2) Volume should be 1.5x average. (3) The best strategy isn't trading the breakout itself — it's trading the retest. After a breakout, price often pulls back to test the broken level. That retest is a higher-probability entry with better risk/reward."
  },
  fundamental: {
    'pe ratio': "P/E ratio tells you how much you're paying per dollar of earnings. But comparing P/E across industries is meaningless — tech at 30x might be cheap, utilities at 15x might be expensive. Always compare within the same sector. Better yet, use PEG ratio (P/E divided by earnings growth rate). PEG below 1 suggests undervalued. Warren Buffett looks for companies with durable competitive advantages, not just low P/E.",
    'earnings': "Earnings season is where the action is. But here's what most miss: guidance often moves the stock more than actual earnings. A company can beat EPS but guide lower and tank. I never buy immediately after earnings — the initial reaction is often wrong. Wait for the gap fill or a pullback. Look for overreactions: stocks that drop 10%+ on merely 'in-line' results often bounce back.",
    'cpi inflation': "CPI is the inflation gauge the Fed watches most. Core CPI (ex-food/energy) matters more to policy. Higher than expected CPI = rate hike fears = stocks down, USD up, gold down. But the first reaction often reverses within 30 minutes. The real money is in understanding the trend, not the single print. If CPI is trending lower for 3+ months, the Fed pivot is coming — that's when you want to be long.",
    'fed interest rate': "The Fed's rate decisions are the single most important macro event. But the dot plot and forward guidance often matter more than the actual decision. Hawkish = USD up, stocks down, gold down. Dovish = opposite. The market is always pricing in expectations — the surprise is what moves things. When the market expects a hike and the Fed pauses, that's a massive shift.",
    'gdp': "GDP tells you where the economy has been, not where it's going. It's a lagging indicator. By the time GDP confirms a recession, stocks have usually already bottomed. More useful: ISM PMI (leading), yield curve (leading), employment trends. But GDP surprises do move markets — especially when they change the narrative about where we are in the cycle."
  },
  risk: {
    'stop loss': "Stop-losses are non-negotiable. Every trade needs one BEFORE you enter. The best stop placement is technical — below support for longs, above resistance for shorts. ATR-based stops (2x ATR below entry) adjust to volatility. The #1 mistake: widening your stop because you 'feel' the trade will work out. That's how small losses become big ones. You CAN tighten stops, but never widen them.",
    'position sizing': "Position sizing is what separates survivors from blowups. Formula: Position Size = (Account × Risk%) / (Entry - Stop). Example: $50K account, 1% risk, $3 risk per share = 166 shares. Without this math, you might buy 500 shares and risk 3%. The 1% rule isn't conservative — it's what keeps you in the game long enough to let your edge play out. Max 5-6% total open risk across all positions.",
    'risk reward': "The minimum risk-reward I'll accept is 1:2 for swing trades. That means even with a 40% win rate, you're profitable. Most beginners focus on win rate — wrong. Focus on R:R. A 60% win rate with 1:1 R:R is break-even after costs. A 40% win rate with 1:3 R:R is very profitable. If you can't find at least 1:2, don't take the trade. There's always another setup tomorrow.",
    'leverage margin': "Leverage is a double-edged sword that most people use to cut themselves. 2:1 leverage means a 50% drop wipes you out. 10:1 means a 10% drop does it. My rule: never use more than 2:1 on stocks, 10:1 on forex, 3:1 on crypto. And that's for experienced traders. Beginners should trade without leverage until they're profitable for 6+ months. The brokers offer 50:1 because they profit from your losses."
  },
  strategy: {
    'swing trading': "Swing trading is the sweet spot for most people — you don't need to watch screens all day, and the profits per trade are meaningful. My bread-and-butter setup: strong uptrend (50 SMA > 200 SMA), pullback to 20 EMA or 50 SMA, bullish reversal candle, enter on close. Stop below the swing low, target previous high or 1:2 R:R. Win rate around 55% with proper execution.",
    'day trading': "Day trading is the hardest style to master. 90%+ lose money. You need $25K for the PDT rule, 2+ hours daily, and iron discipline. The Opening Range Breakout is the most reliable setup: mark the first 15-30 minute range, trade the breakout with the daily trend. VWAP is your best friend intraday — price above VWAP is bullish, below is bearish. Most important: 3% daily loss limit. Hit it and walk away.",
    'scalping': "Scalping is not for beginners. You need 65%+ win rate because your R:R is often 1:1 or worse. Commissions eat your profits. You need lightning-fast execution and zero hesitation. If you're going to try it, stick to the most liquid instruments (EUR/USD, SPY, etc.) and never risk more than 0.5% per trade. Honestly, most people would be better off swing trading.",
    'dividend': "Dividend investing is the tortoise that wins the race. 40% of S&P 500's historical returns came from dividends. Look for Dividend Aristocrats (25+ years of increases), yield between 2.5-4.5%, payout ratio below 60%, and consistent 5-10% annual dividend growth. DRIP (reinvesting dividends) is the compound growth engine. $10K at 3% yield with DRIP becomes $24K in 30 years vs $19K without.",
    'etf': "ETFs are the simplest path to building wealth. A 3-fund portfolio (VTI + VXUS + BND) beats 90% of active managers over 10 years. Stock allocation ≈ 110 minus your age. The key is consistency: set it, contribute monthly, rebalance annually. Don't chase thematic ETFs (ARKK, etc.) — they're for your satellite allocation, max 20% of portfolio."
  },
  crypto: {
    'bitcoin': "Bitcoin is digital gold with a 21M supply cap. The 4-year halving cycle has historically driven bull markets. Key levels: 200-week MA (never broken in a bear market), realized price (average cost basis), and previous ATH. Institutional adoption via ETFs changed the game in 2024. Treat BTC as a long-term holding — 5% portfolio allocation, cold storage, don't trade it with leverage.",
    'crypto': "Crypto is 24/7 with 10-20% daily volatility — not for the faint of heart. BTC dominance drives the cycle: when it falls, alt season begins. Never put more than 5% in a single altcoin, 15% total crypto allocation. Most altcoins go to zero. Stick to top 20 for safety. And never use leverage in crypto — the volatility is already leveraged."
  },
  platform: {
    'broadfsc': "BroadFSC is a regulated investment advisory platform. We're licensed by major financial authorities and serve global investors (except mainland China). What makes us different: AI-powered education, transparent fees, and actual human support when you need it. Think of us as the platform that actually wants you to learn, not just trade.",
    'account': "Opening a BroadFSC account is straightforward — verified ID, proof of address, and you're in. We support multiple currencies and offer both advisory and self-directed accounts. Minimums are kept low because we believe everyone deserves access to professional tools. Contact our team through this chat or visit broadfsc.com for details.",
    'fees': "We keep fees transparent — no hidden charges. Our structure is competitive with major platforms, and we don't nickel-and-dime on small transactions. The specific fee schedule depends on your account type and services. What I can tell you: we're not the cheapest, but we're far from the most expensive, and the value you get in education and support more than covers it."
  }
};

// ── SOUL AI Advisor Personalities ──
const ADVISORS = {
  alex: {
    name: 'Alex Chen',
    emoji: '👨‍💼',
    role: 'Technical Analysis',
    greeting: "Hey, I'm Alex. I've been trading for 8 years and I'm not here to sugarcoat anything. Ask me about charts, indicators, setups — I'll give you my honest take. No fluff.",
    style: 'direct', // direct, warm, analytical
    catchphrase: "Here's what I'd actually do —",
    perspective: "I believe technical analysis works not because it's magic, but because millions of traders watch the same levels. It's self-fulfilling, and that's fine — use it."
  },
  sarah: {
    name: 'Sarah Kim',
    emoji: '👩‍💼',
    role: 'Risk Management',
    greeting: "Hi! I'm Sarah. I focus on keeping you in the game. Most traders fail because of poor risk management, not poor analysis. Let's make sure that's not you. Ask me about position sizing, stops, or anything risk-related.",
    style: 'warm',
    catchphrase: "The math says —",
    perspective: "I'd rather miss a profit than take an unnecessary loss. Preservation of capital always comes first. If your risk management is solid, the profits will follow."
  },
  mike: {
    name: 'Mike Torres',
    emoji: '🧑‍💻',
    role: 'Fundamentals & Macro',
    greeting: "Hey, Mike here. I look at the big picture — earnings, economic data, central banks, geopolitical shifts. Technicals tell you when; fundamentals tell you why. Ask me about any market or macro event.",
    style: 'analytical',
    catchphrase: "The bigger picture tells me —",
    perspective: "Price is what you pay, value is what you get. I focus on understanding WHY markets move, not just the pattern on the chart. Fundamentals win in the long run."
  }
};

// ── AI State ──
let currentAdvisor = 'alex';
let chatHistory = [];
let userName = localStorage.getItem('bfs_username') || '';

// ── AI Response Engine (SOUL-powered) ──
function getAIResponse(input) {
  const q = input.toLowerCase().trim();
  const advisor = ADVISORS[currentAdvisor];

  // Memory: check chat history for context
  const lastTopics = chatHistory.slice(-6).map(m => m.text.toLowerCase()).join(' ');

  // 1. Check knowledge base (deep match first)
  let bestMatch = null;
  let bestScore = 0;

  for (const [category, terms] of Object.entries(KNOWLEDGE)) {
    for (const [key, answer] of Object.entries(terms)) {
      const keywords = key.split(' ');
      let score = 0;
      for (const kw of keywords) {
        if (q.includes(kw)) score += 2;
      }
      // Also check for partial matches
      if (q.includes(key) || key.includes(q)) score += 5;
      // Check individual significant words
      const qWords = q.split(/\s+/);
      for (const word of qWords) {
        if (word.length > 3 && key.includes(word)) score += 1;
      }
      if (score > bestScore) {
        bestScore = score;
        bestMatch = { key, answer, category };
      }
    }
  }

  if (bestMatch && bestScore >= 2) {
    return formatAdvisorResponse(bestMatch.answer, bestMatch.category);
  }

  // 2. Pattern matching for common questions
  const patterns = [
    { test: /how.*start|beginner|where.*begin|new.*trad/i, resp: () => formatAdvisorResponse("Start with the basics — don't rush into live trading. Here's my honest roadmap: (1) Read our Stock Market Fundamentals course. (2) Paper trade for at least 3 months. (3) Start with a small account ($1-2K). (4) Master ONE setup before learning more. (5) Keep a journal from day one. The biggest mistake beginners make? Trying to learn everything at once. Pick one strategy, master it, then expand.", 'strategy') },
    { test: /recommend|suggest|which.*stock|what.*buy|pick/i, resp: () => {
      if (currentAdvisor === 'alex') return "I can't give specific buy/sell recommendations — that wouldn't be responsible without knowing your full situation. What I CAN do: teach you how to find your own setups. Look for strong trends pulling back to support, confirmed by RSI or MACD. That's where I start every day. Want me to walk you through the process?";
      if (currentAdvisor === 'sarah') return "I won't tell you what to buy, but I'll tell you this: before you put money into ANY trade, you need three things — a clear entry reason, a stop-loss level, and a profit target. If you can't articulate all three, you're not trading, you're gambling. Let's talk about how to build that framework.";
      return "Specific picks aren't my thing — I focus on understanding what drives markets. But here's what I watch: earnings growth trends, central bank policy shifts, and sector rotation. When all three align, that's when the big moves happen. Want to dive deeper into any of those?";
    }},
    { test: /crypto|bitcoin|btc|ethereum|alt/i, resp: () => formatAdvisorResponse(KNOWLEDGE.crypto[q.includes('bitcoin') || q.includes('btc') ? 'bitcoin' : 'crypto'] || KNOWLEDGE.crypto.crypto, 'crypto') },
    { test: /forex|currency|eur.*usd|gbp|jpy/i, resp: () => formatAdvisorResponse("Forex is the largest market ($6.6T daily) with 24/5 trading and high leverage. The key sessions: London (highest volume), New York (high volatility at open), and their overlap (8 AM–12 PM ET) is the golden window. Major pairs (EUR/USD, GBP/USD) have tight spreads and are best for beginners. Exotic pairs? Stay away until you know what you're doing. The #1 forex mistake: over-leveraging. Use 10:1 max as a beginner.", 'strategy') },
    { test: /option|call|put|spread/i, resp: () => formatAdvisorResponse("Options give you the RIGHT but not the OBLIGATION to buy (call) or sell (put) at a specific price. The Greeks: Delta (direction), Gamma (acceleration), Theta (time decay — works against buyers, for sellers), Vega (volatility). For beginners, I always recommend credit spreads (bull put / bear call): defined risk, profit even if slightly wrong, and time decay works in your favor. Never buy OTM options close to expiration — theta will eat your premium alive.", 'strategy') },
    { test: /loss|losing|down|red|bleeding|drawdown/i, resp: () => {
      if (currentAdvisor === 'sarah') return "Losing is part of trading — every pro loses. The question is: are your losses controlled? Here's my checklist: (1) Did you have a stop-loss? If no, that's the problem. (2) Was it more than 1-2% of your account? If yes, position sizing issue. (3) Did you follow your plan? If yes, it's just variance. Stay the course. If no, fix the violations. (4) Are you thinking about increasing size to recover? DON'T. That's how accounts blow up. Take a breath, reduce size by 50%, and get back to basics.";
      return formatAdvisorResponse("Losing streaks happen to everyone. The difference between pros and amateurs is how they respond. My rules: (1) Never increase size during a losing streak. (2) Reduce size by 50%. (3) Review every trade — are you following your plan? (4) If yes, it's variance. Stay the course. (5) Take a 1-2 day break if needed. The market will still be there when you come back.", 'risk');
    }},
    { test: /hello|hi|hey|greetings|good morning|good evening/i, resp: () => {
      if (!userName) return advisor.greeting + " By the way, what should I call you? I remember things better when I know who I'm talking to.";
      return `Hey ${userName}! Good to see you again. What's on your mind today? We can talk setups, risk management, market outlook — whatever you need.`;
    }},
    { test: /my name is|i'm called|call me|i am (.+)/i, resp: () => {
      const nameMatch = input.match(/(?:my name is|i'm called|call me|i am)\s+(\w+)/i);
      if (nameMatch) {
        userName = nameMatch[1];
        localStorage.setItem('bfs_username', userName);
        return `Nice to meet you, ${userName}! I'll remember that. Now, what can I help you with? Markets, strategies, risk — fire away.`;
      }
      return "Got it! What would you like to talk about?";
    }},
    { test: /thank|thanks|appreciate/i, resp: () => `You're welcome, ${userName || 'friend'}! That's what I'm here for. Any other questions, just ask — no such thing as a dumb question in trading.` },
    { test: /broadfsc|platform|company|about you/i, resp: () => formatAdvisorResponse(KNOWLEDGE.platform.broadfsc, 'platform') },
    { test: /fee|cost|price|commission|charge/i, resp: () => formatAdvisorResponse(KNOWLEDGE.platform.fees, 'platform') },
    { test: /account|open|register|sign up/i, resp: () => formatAdvisorResponse(KNOWLEDGE.platform.account, 'platform') },
    { test: /help|can you|what can you/i, resp: () => `I can help with a lot, ${userName || 'friend'}: technical analysis (RSI, MACD, Fibonacci, S/R, candlesticks), risk management (position sizing, stop-losses, R:R), trading strategies (swing, day trading, scalping, dividends), fundamental analysis (earnings, P/E, macro data), crypto, forex, and options. I also know about BroadFSC's services. Just ask naturally — no special commands needed.` },
    { test: /psychology|emotion|discipline|fear|greed|mindset/i, resp: () => formatAdvisorResponse("Trading psychology is the hidden edge. Fear makes you sell at bottoms and avoid good setups. Greed makes you chase, over-leverage, and ignore stops. The solution isn't 'be less emotional' — it's having a written plan and following it mechanically. Top biases to watch: confirmation bias (only seeing what supports your position), loss aversion (holding losers too long), and overconfidence (sizing up after wins). A trading journal is the #1 improvement tool — track every trade AND your emotional state.", 'strategy') },
    { test: /dividend|passive income|yield|drip/i, resp: () => formatAdvisorResponse(KNOWLEDGE.strategy.dividend, 'strategy') },
    { test: /etf|index fund|boglehead|3.fund/i, resp: () => formatAdvisorResponse(KNOWLEDGE.strategy.etf, 'strategy') },
    { test: /market.*outlook|prediction|forecast|where.*market/i, resp: () => {
      if (currentAdvisor === 'mike') return "I can't predict the future — nobody can, despite what they claim. What I DO: watch the yield curve (inversion = recession signal), ISM PMI (below 50 = contraction), and Fed forward guidance. Right now, focus on the trend and the data, not the narrative. The trend is your friend until it bends. Want me to break down a specific indicator?";
      return "Nobody can predict markets consistently — and anyone who says they can is selling something. What I can do is help you read the signals: trend direction, momentum shifts, and key levels. The edge isn't in prediction, it's in preparation. Have a plan for multiple scenarios, and execute the one the market gives you.";
    }},
  ];

  for (const p of patterns) {
    if (p.test.test(q)) return p.resp();
  }

  // 3. Keyword fallback
  const kwMap = {
    'support': 'technical', 'resistance': 'technical', 'level': 'technical',
    'rsi': 'technical', 'macd': 'technical', 'indicator': 'technical',
    'ma': 'technical', 'ema': 'technical', 'sma': 'technical',
    'fibonacci': 'technical', 'fib': 'technical', 'retracement': 'technical',
    'bollinger': 'technical', 'band': 'technical',
    'candle': 'technical', 'hammer': 'technical', 'doji': 'technical', 'engulfing': 'technical',
    'chart': 'technical', 'pattern': 'technical', 'triangle': 'technical', 'head shoulder': 'technical',
    'volume': 'technical', 'obv': 'technical',
    'breakout': 'technical', 'break': 'technical',
    'pe': 'fundamental', 'earning': 'fundamental', 'revenue': 'fundamental',
    'cpi': 'fundamental', 'inflation': 'fundamental', 'fed': 'fundamental', 'interest rate': 'fundamental',
    'gdp': 'fundamental', 'nfp': 'fundamental', 'employment': 'fundamental',
    'stop': 'risk', 'risk': 'risk', 'position': 'risk', 'leverage': 'risk', 'margin': 'risk',
    'swing': 'strategy', 'day trad': 'strategy', 'scalp': 'strategy',
    'dividend': 'strategy', 'etf': 'strategy',
    'bitcoin': 'crypto', 'crypto': 'crypto', 'btc': 'crypto', 'altcoin': 'crypto',
    'option': 'strategy', 'call': 'strategy', 'put': 'strategy',
  };

  for (const [kw, cat] of Object.entries(kwMap)) {
    if (q.includes(kw)) {
      // Find best match in that category
      for (const [key, answer] of Object.entries(KNOWLEDGE[cat])) {
        if (q.includes(key) || key.includes(kw)) {
          return formatAdvisorResponse(answer, cat);
        }
      }
      // Return a general response for the category
      const catResponses = {
        technical: "That's a technical analysis topic I can dig into. The key principle: always confirm with multiple signals. A single indicator or pattern isn't enough — look for confluence between S/R, volume, and momentum. What specifically about this would you like me to break down?",
        fundamental: "Fundamentals drive the long-term direction. The most impactful events: Fed rate decisions, CPI prints, and earnings reports. Short-term, the surprise vs consensus is what moves markets. Want me to explain how to trade any of these?",
        risk: "Risk management is where most traders fail. My non-negotiable rules: 1-2% max risk per trade, always have a stop-loss, and never risk more than 5-6% total across all positions. What's your current risk framework?",
        strategy: "Strategy depends on your style and available time. Swing trading is best for most people — 30 min/day, 2-14 day holds, and you can keep your day job. What's your situation?",
        crypto: "Crypto is its own beast — 24/7, extreme volatility, and most altcoins go to zero. Keep crypto to max 15% of portfolio, BTC/ETH only for beginners, and NEVER use leverage in crypto. The volatility is already leveraged enough.",
        platform: "I can tell you about BroadFSC's services, account setup, or fees. What specifically interests you?"
      };
      return catResponses[cat] || "Tell me more about what you're looking for and I'll give you my best take.";
    }
  }

  // 4. Smart fallback with personality
  const fallbacks = {
    alex: [
      `Hmm, that's not something I have a strong take on. But here's what I know: stick to what you understand, manage your risk, and don't chase. What specifically were you wondering about? I'm better with specific questions.`,
      `I'm not going to pretend I know everything about that. What I DO know: charts, setups, and risk management. Hit me with something more specific and I'll give you a real answer.`,
      `That's outside my wheelhouse, but let me steer you right — what are you actually trying to figure out? The more specific, the better I can help.`
    ],
    sarah: [
      `I want to help, but I need more context. Are you asking about risk? Position sizing? Or something else? The more specific you are, the more useful I can be.`,
      `That's a bit vague for me to give a solid answer. Tell me about your situation — what are you trading, what's your account size, what's your risk tolerance? Then I can give you real advice.`,
    ],
    mike: [
      `I could speculate, but I'd rather give you something useful. What's the actual question behind the question? Are you looking at a specific market, a macro event, or trying to understand a concept?`,
      `Let me give you a framework instead: every market question comes down to supply vs demand, driven by either fundamentals or sentiment. Which angle are you coming from?`
    ]
  };
  const pool = fallbacks[currentAdvisor] || fallbacks.alex;
  return pool[Math.floor(Math.random() * pool.length)];
}

function formatAdvisorResponse(answer, category) {
  const advisor = ADVISORS[currentAdvisor];
  const prefix = advisor.catchphrase;
  const catLabels = {
    technical: '📊 Technical',
    fundamental: '📋 Fundamental',
    risk: '🛡️ Risk',
    strategy: '🎯 Strategy',
    crypto: '₿ Crypto',
    platform: '🏦 BroadFSC'
  };
  return `${prefix} ${answer}\n\n_${catLabels[category] || ''} | ${advisor.name}_`;
}

// ── Chat UI ──
function switchAdvisor(id) {
  currentAdvisor = id;
  const a = ADVISORS[id];

  // Update UI
  document.getElementById('chatAvatar').textContent = a.emoji;
  document.getElementById('chatName').textContent = a.name;
  document.getElementById('chatStatus').textContent = `● Online • ${a.role}`;

  document.querySelectorAll('.advisor-chip').forEach(c => c.classList.remove('active'));
  const chipId = 'chip' + id.charAt(0).toUpperCase() + id.slice(1);
  const chip = document.getElementById(chipId);
  if (chip) chip.classList.add('active');

  // Add switch message
  addBotMessage(`Switched to ${a.name}. ${a.greeting}`);
}

function sendChat() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  // Add user message
  addUserMessage(text);
  chatHistory.push({ role: 'user', text });
  input.value = '';

  // Typing indicator
  showTyping();

  // AI response with delay for realism
  const delay = 600 + Math.random() * 800;
  setTimeout(() => {
    removeTyping();
    const response = getAIResponse(text);
    addBotMessage(response);
    chatHistory.push({ role: 'bot', text: response });
  }, delay);
}

function addUserMessage(text) {
  const body = document.getElementById('chatBody');
  const div = document.createElement('div');
  div.className = 'chat-msg user';
  div.textContent = text;
  body.appendChild(div);
  body.scrollTop = 0; // Keep at top, don't jump to bottom
}

function addBotMessage(text) {
  const body = document.getElementById('chatBody');
  const div = document.createElement('div');
  div.className = 'chat-msg bot';

  // Convert markdown-like formatting
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/_(.*?)_/g, '<em style="color:var(--text3);font-size:0.88em">$1</em>')
    .replace(/\n/g, '<br>');
  div.innerHTML = html;
  body.appendChild(div);
  body.scrollTop = 0;
}

function showTyping() {
  const body = document.getElementById('chatBody');
  const div = document.createElement('div');
  div.className = 'chat-msg bot';
  div.id = 'typingIndicator';
  div.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
  body.appendChild(div);
  body.scrollTop = 0;
}

function removeTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

// ── Research Reports with Full Content ──
const RESEARCH = [
  {
    id: 1, title: "S&P 500 Weekly Outlook: Key Levels to Watch",
    type: "weekly", typeLabel: "Weekly Analysis",
    date: "Apr 20, 2026", readTime: "8 min",
    summary: "S&P 500 sits at a critical junction with 200 SMA tested and Fed meeting ahead.",
    content: `<h3>Market Context</h3>
<p>The S&P 500 is trading at a pivotal level this week, testing the 200-day simple moving average — a line that has historically determined the macro trend. A decisive close above this level would confirm the bullish case, while a rejection could trigger a 5-8% pullback.</p>

<h3>Key Levels</h3>
<ul>
<li><strong>Resistance:</strong> 5,450 (prior swing high), 5,520 (all-time high)</li>
<li><strong>Support:</strong> 5,280 (200 SMA), 5,180 (50 SMA), 5,050 (prior lows)</li>
<li><strong>Neutral Zone:</strong> 5,180 - 5,380 (range-bound if stuck here)</li>
</ul>

<h3>What to Watch This Week</h3>
<p><strong>1. Fed Meeting Minutes (Wednesday):</strong> Markets will parse every word for rate cut timing. Dovish tone = bullish for equities. Any hawkish surprise could send the index below 200 SMA.</p>
<p><strong>2. Earnings Season Continues:</strong> Tech mega-caps report this week. Focus on capex guidance — AI spending is the narrative driver. Any slowdown in data center investment could hit the sector hard.</p>
<p><strong>3. Economic Data:</strong> Jobless claims and PMI data. A weakening labor market supports the rate cut narrative but raises recession concerns.</p>

<h3>Strategy</h3>
<p><strong>Bullish scenario:</strong> If price holds above 5,280 (200 SMA) with volume, look for a retest of 5,450. Buy the pullback to 200 SMA with a stop below 5,220.</p>
<p><strong>Bearish scenario:</strong> If 200 SMA fails, expect a move to 5,050. Reduce long exposure and wait for a base to form before re-entering.</p>

<h3>Risk Management</h3>
<p>Given the Fed event risk, reduce position sizes by 30-50% this week. Ensure all stops are in place before Wednesday. No new positions after 2 PM ET on Wednesday (Fed minutes release).</p>`
  },
  {
    id: 2, title: "EUR/USD: ECB vs Fed Divergence Trade",
    type: "daily", typeLabel: "Daily Brief",
    date: "Apr 20, 2026", readTime: "5 min",
    summary: "ECB cutting while Fed holds — the divergence trade is setting up nicely.",
    content: `<h3>Setup Overview</h3>
<p>EUR/USD has been ranging between 1.0800-1.0950 for three weeks. The setup: ECB is clearly in easing mode (two cuts this year already), while the Fed is holding rates higher for longer. This divergence should eventually push EUR/USD lower.</p>

<h3>Key Levels</h3>
<ul>
<li><strong>Resistance:</strong> 1.0950 (triple top), 1.1000 (psychological), 1.1080 (200-day MA)</li>
<li><strong>Support:</strong> 1.0800 (range floor), 1.0720 (prior lows), 1.0650 (measured move)</li>
</ul>

<h3>The Trade</h3>
<p><strong>Entry:</strong> Sell on a rejection at 1.0950 (if we get another test) or on a break below 1.0800.</p>
<p><strong>Stop:</strong> Above 1.1000 (50 pips risk from 1.0950 entry)</p>
<p><strong>Target:</strong> 1.0720 initially (180 pips), then 1.0650 (300 pips)</p>
<p><strong>R:R:</strong> 1:3.6 to first target — excellent setup</p>

<h3>Catalysts</h3>
<p>Next ECB meeting in 2 weeks. If they signal another cut, that's our trigger. Also watch US NFP this Friday — a strong number supports the Fed-holds narrative and weakens EUR.</p>

<h3>Risk</h3>
<p>If the Fed signals earlier-than-expected cuts, EUR/USD could break above 1.1000 and invalidate this setup. Keep stops tight above that level.</p>`
  },
  {
    id: 3, title: "Gold: $2,400 and Beyond — What's Driving the Rally",
    type: "special", typeLabel: "Special Report",
    date: "Apr 18, 2026", readTime: "12 min",
    summary: "Central bank buying, geopolitical risk, and rate cut expectations fuel gold's historic run.",
    content: `<h3>The Big Picture</h3>
<p>Gold has surged past $2,400, hitting all-time highs. This isn't just a blip — it's a structural shift driven by three powerful forces: central bank accumulation, geopolitical risk premium, and the market pricing in Fed rate cuts.</p>

<h3>Driver #1: Central Bank Buying</h3>
<p>Central banks bought over 1,000 tonnes of gold in 2025, the second-highest annual total on record. China's PBOC has been a consistent buyer for 18 consecutive months. This isn't speculative — it's a structural shift away from USD reserves. This demand provides a floor under gold prices that didn't exist a decade ago.</p>

<h3>Driver #2: Geopolitical Risk Premium</h3>
<p>Multiple ongoing conflicts, trade tensions, and election uncertainty across major economies have added a persistent risk premium. Gold historically performs well during periods of elevated geopolitical uncertainty, and current conditions are among the most uncertain in decades.</p>

<h3>Driver #3: Rate Cut Expectations</h3>
<p>The market is pricing in 2-3 Fed cuts this year. Lower real rates reduce the opportunity cost of holding non-yielding gold. If cuts materialize, gold goes higher. Even if they don't, the uncertainty itself supports gold.</p>

<h3>Technical Outlook</h3>
<ul>
<li><strong>Trend:</strong> Strongly bullish. 20, 50, 200 MAs all rising and aligned.</li>
<li><strong>Support:</strong> $2,350 (prior resistance → support), $2,280 (50 SMA), $2,180 (200 SMA)</li>
<li><strong>Targets:</strong> $2,500 (psychological), $2,600 (measured move from breakout)</li>
</ul>

<h3>How to Play It</h3>
<p><strong>Conservative:</strong> Buy the dip to $2,350 with a stop at $2,280. Target $2,500.</p>
<p><strong>Moderate:</strong> Buy current levels with a stop at $2,350. Target $2,600.</p>
<p><strong>Alternative:</strong> Gold miners (GDX, GDXJ) offer leverage to the gold price. More volatile but potentially higher returns.</p>

<h3>Risks</h3>
<p>A hot CPI print that kills rate cut expectations could trigger a 5-8% pullback. Also, if geopolitical tensions ease meaningfully, the risk premium could evaporate quickly. Always use stops.</p>`
  },
  {
    id: 4, title: "Tech Earnings Season: AI Capex Under the Microscope",
    type: "weekly", typeLabel: "Weekly Analysis",
    date: "Apr 17, 2026", readTime: "10 min",
    summary: "Big Tech's AI spending is the key variable. Any slowdown = sector-wide selloff.",
    content: `<h3>Why This Matters</h3>
<p>The Magnificent 7 have driven 60%+ of S&P 500 returns over the past year, largely on AI narrative. But capex spending on AI infrastructure has reached staggering levels — over $200B annually. The question: is this spending generating real returns, or are we in an AI investment bubble?</p>

<h3>Key Companies to Watch</h3>
<ul>
<li><strong>NVIDIA:</strong> The AI kingpin. Data center revenue is the number to watch. Any slowdown from the torrid 200%+ growth pace could trigger a 10-15% selloff.</li>
<li><strong>Microsoft:</strong> Azure cloud growth + Copilot adoption rates. Capex guidance is critical — if they pull back, it signals demand concerns.</li>
<li><strong>Google:</strong> Cloud growth + AI integration across products. Watch ad revenue too — if AI is cannibalizing search, that's a problem.</li>
<li><strong>Meta:</strong> AI-driven ad targeting improvements + Reality Labs losses. Their open-source AI strategy (Llama) is fascinating but unmonetized.</li>
<li><strong>Amazon:</strong> AWS growth + e-commerce margin expansion. Their AI chip investment (Trainium) is a direct challenge to NVIDIA.</li>
</ul>

<h3>The Bull Case</h3>
<p>AI is real and transformative. Enterprise adoption is accelerating. Capex is an investment that will pay off over 3-5 years. Current spending levels are sustainable given the revenue growth. We're in inning 3 of the AI revolution.</p>

<h3>The Bear Case</h3>
<p>$200B+ annual capex with limited proven ROI. Some AI features are being given away for free. When does the investment need to show returns? If enterprise AI revenue doesn't accelerate meaningfully this year, the narrative cracks. Parallels to 2000 telecom capex boom are uncomfortable.</p>

<h3>How to Position</h3>
<p><strong>Pre-earnings:</strong> Reduce tech exposure by 20-30%. Earnings volatility will be extreme. Don't try to guess the direction.</p>
<p><strong>Post-earnings:</strong> If capex guidance is maintained or increased AND revenue growth accelerates → buy the dip. If capex slows or revenue disappoints → consider puts or sector rotation to defensive names.</p>

<h3>Hedging</h3>
<p>Buy QQQ puts (2-3% OTM, 30-45 DTE) as portfolio insurance. Cost: ~1-2% of portfolio value. Or use XLK put spreads for cheaper protection.</p>`
  },
  {
    id: 5, title: "Bitcoin Halving Cycle: Where Are We Now?",
    type: "special", typeLabel: "Special Report",
    date: "Apr 15, 2026", readTime: "10 min",
    summary: "Post-halving analysis — historical patterns suggest the real move is still ahead.",
    content: `<h3>Halving Recap</h3>
<p>Bitcoin's most recent halving reduced the block reward from 6.25 to 3.125 BTC. Historically, halvings have been followed by significant bull runs, but the timing matters — the real move typically starts 6-12 months AFTER the halving, not before.</p>

<h3>Historical Comparison</h3>
<table style="width:100%;border-collapse:collapse;margin:12px 0">
<tr style="border-bottom:1px solid var(--border)"><th style="text-align:left;padding:8px;color:var(--text2)">Halving</th><th style="text-align:left;padding:8px;color:var(--text2)">Pre-Halving Peak</th><th style="text-align:left;padding:8px;color:var(--text2)">Post-Halving Peak</th><th style="text-align:left;padding:8px;color:var(--text2)">Time to Peak</th></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px">2016</td><td style="padding:8px">$770</td><td style="padding:8px">$19,900</td><td style="padding:8px">~18 months</td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px">2020</td><td style="padding:8px">$10,000</td><td style="padding:8px">$69,000</td><td style="padding:8px">~18 months</td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px">2024</td><td style="padding:8px">$73,000</td><td style="padding:8px">?</td><td style="padding:8px">In progress</td></tr>
</table>

<h3>What's Different This Time</h3>
<p><strong>ETFs:</strong> Spot Bitcoin ETFs have fundamentally changed demand dynamics. Daily ETF inflows can match or exceed new mining supply. This is the first halving with institutional demand via regulated products.</p>
<p><strong>Macro environment:</strong> Rate cuts could provide additional tailwind. Bitcoin has historically performed well in easing cycles.</p>
<p><strong>Diminishing returns:</strong> Each cycle's multiple has decreased (25x → 7x → ?). Even a 3-4x from pre-halving levels would put BTC at $200-300K.</p>

<h3>On-Chain Metrics</h3>
<ul>
<li><strong>Realized Price:</strong> ~$38K. Current price well above = profitable market</li>
<li><strong>200-Week MA:</strong> Never broken in a bear market. Current: ~$45K</li>
<li><strong>Exchange Reserves:</strong> Declining = less selling pressure (holders moving to cold storage)</li>
<li><strong>NUPL:</strong> At 0.55 — in 'optimism' zone. Historically goes to 0.75 ('euphoria') before major tops</li>
</ul>

<h3>Strategy</h3>
<p><strong>Long-term holders:</strong> Continue holding. The cycle peak likely isn't until late 2025 or 2026 based on historical timing. Take partial profits at 3x from entry (sell 50%).</p>
<p><strong>New positions:</strong> Buy on pullbacks to $55-60K zone (200-week MA area). Stop below $45K. Target: $150-200K over 12-18 months.</p>
<p><strong>Risk:</strong> Regulatory crackdowns, exchange failures, or a severe recession could break the cycle pattern. Never invest more than 5% of portfolio in BTC.</p>`
  },
  {
    id: 6, title: "Risk Management Checklist: 20 Rules That Save Accounts",
    type: "special", typeLabel: "Special Report",
    date: "Apr 14, 2026", readTime: "15 min",
    summary: "The complete risk management framework — print this, follow it, survive.",
    content: `<h3>The 20 Non-Negotiable Rules</h3>

<h4>Position Sizing</h4>
<ol>
<li><strong>1% Rule:</strong> Never risk more than 1% of your account on a single trade. 2% maximum for high-conviction setups.</li>
<li><strong>Use the formula:</strong> Position Size = (Account × Risk%) / (Entry - Stop-Loss)</li>
<li><strong>Maximum 5-6% total open risk</strong> across all positions at any time.</li>
<li><strong>No single position exceeds 10%</strong> of total portfolio value.</li>
</ol>

<h4>Stop-Losses</h4>
<ol start="5">
<li><strong>Every trade has a stop</strong> before entry. No exceptions.</li>
<li><strong>Technical stops over arbitrary ones:</strong> Place stops below support (long) or above resistance (short), not just a fixed percentage.</li>
<li><strong>ATR stops:</strong> Use 2× ATR below entry for volatility-adjusted stops.</li>
<li><strong>Never widen your stop.</strong> You CAN tighten it, but never move it further from entry.</li>
</ol>

<h4>Risk-Reward</h4>
<ol start="9">
<li><strong>Minimum 1:2 R:R</strong> for swing trades. 1:3+ for position trades.</li>
<li><strong>If you can't find 1:2,</strong> don't trade. There's always another setup tomorrow.</li>
<li><strong>Calculate R:R before entering.</strong> If it's not clear, it's not a trade.</li>
</ol>

<h4>Daily/Weekly Limits</h4>
<ol start="12">
<li><strong>Daily loss limit: 3%.</strong> Hit it, close everything, walk away.</li>
<li><strong>Weekly loss limit: 6%.</strong> Hit it, stop trading for the week. Reevaluate.</li>
<li><strong>3 consecutive losses:</strong> Take a break. Reduce size by 50%.</li>
</ol>

<h4>Portfolio Risk</h4>
<ol start="15">
<li><strong>Max sector concentration: 25%.</strong> Don't have all your positions in tech.</li>
<li><strong>Correlation check:</strong> Two highly correlated positions = one big position. Count them together.</li>
<li><strong>Keep 10-20% cash</strong> for opportunities. Being fully invested = no flexibility.</li>
</ol>

<h4>Emotional Rules</h4>
<ol start="18">
<li><strong>No revenge trading.</strong> After a big loss, don't try to 'win it back.' That's how accounts blow up.</li>
<li><strong>No trading when tired, angry, or distracted.</strong> Your judgment is compromised.</li>
<li><strong>Follow your written plan.</strong> If you don't have one, stop trading and write one first.</li>
</ol>

<h3>The Bottom Line</h3>
<p>90% of traders lose money. The 10% who survive all have one thing in common: disciplined risk management. Not better analysis. Not better signals. Just better risk control. Print this list, put it next to your screen, and follow it every single day.</p>`
  }
];

// ── Research Sources ──
const SOURCES = [
  { name: "Federal Reserve", url: "https://www.federalreserve.gov/", emoji: "🏛️", desc: "Official Fed data, speeches, and rate decisions" },
  { name: "Bureau of Labor Stats", url: "https://www.bls.gov/", emoji: "📊", desc: "CPI, NFP, and employment data" },
  { name: "TradingView", url: "https://www.tradingview.com/", emoji: "📈", desc: "Free charts, screeners, and community" },
  { name: "Investing.com", url: "https://www.investing.com/", emoji: "🌐", desc: "Economic calendar and live data" },
  { name: "Yahoo Finance", url: "https://finance.yahoo.com/", emoji: "📱", desc: "Stock quotes and financial news" },
  { name: "CoinGecko", url: "https://www.coingecko.com/", emoji: "₿", desc: "Crypto prices and market data" },
  { name: "Finviz", url: "https://finviz.com/", emoji: "🗺️", desc: "Stock screener and heat maps" },
  { name: "Investopedia", url: "https://www.investopedia.com/", emoji: "📚", desc: "Financial education and definitions" },
];

// ── Glossary Data ──
const GLOSSARY = [
  {term:"Support",def:"A price level where buying pressure prevents further decline. Formed by multiple touches and often coincides with moving averages or Fibonacci levels.",cat:"Technical"},
  {term:"Resistance",def:"A price ceiling where selling pressure prevents further advance. When broken, often becomes new support.",cat:"Technical"},
  {term:"RSI",def:"Relative Strength Index. Measures momentum on 0-100 scale. Above 70 = overbought, below 30 = oversold. Divergence is the strongest signal.",cat:"Technical"},
  {term:"MACD",def:"Moving Average Convergence Divergence. Shows momentum shifts via 12/26 EMA difference. Histogram shrinking = momentum fading.",cat:"Technical"},
  {term:"Moving Average",def:"Average of closing prices over N periods. SMA (equal weight) for trends, EMA (recent-heavy) for signals. 200 SMA is most important.",cat:"Technical"},
  {term:"Bollinger Bands",def:"Volatility bands at 2 standard deviations from 20 SMA. Squeeze = big move coming. Price stays within bands ~95% of time.",cat:"Technical"},
  {term:"Fibonacci Retracement",def:"Key levels: 23.6%, 38.2%, 50%, 61.8%. The Golden Ratio (61.8%) is most important. Beyond 61.8% = trend may be broken.",cat:"Technical"},
  {term:"Candlestick",def:"Price chart showing open, high, low, close. Body = open-to-close, wicks = high/low. Patterns signal reversals and continuations.",cat:"Technical"},
  {term:"Volume",def:"Number of shares/contracts traded. Rising volume confirms moves. Declining volume = weak conviction. OBV leads price by 1-3 days.",cat:"Technical"},
  {term:"Breakout",def:"Price moving beyond a key level. True breakouts close beyond the level with 1.5x+ volume. Most breakouts fail — trade the retest instead.",cat:"Technical"},
  {term:"Stop-Loss",def:"Order to sell when price hits a predetermined level. Essential risk management. Place below support (long) or above resistance (short).",cat:"Risk"},
  {term:"Position Sizing",def:"Calculating how many shares/units to trade based on risk tolerance. Formula: (Account × Risk%) / (Entry - Stop).",cat:"Risk"},
  {term:"Risk-Reward Ratio",def:"Potential profit vs potential loss. Minimum 1:2 for swing trades. With 1:2, you're profitable at just 40% win rate.",cat:"Risk"},
  {term:"Leverage",def:"Borrowing to amplify position size. 2:1 = double exposure. Double-edged: amplifies both gains AND losses. Use sparingly.",cat:"Risk"},
  {term:"Margin",def:"Collateral deposited with broker. Maintenance margin = minimum equity required. Margin call = deposit more or positions liquidated.",cat:"Risk"},
  {term:"Drawdown",def:"Peak-to-trough decline in account value. Max 20% drawdown target. If hit, reduce all positions by 50%.",cat:"Risk"},
  {term:"P/E Ratio",def:"Price-to-Earnings. Stock price ÷ EPS. Compare within same industry. PEG ratio (P/E ÷ growth rate) is better — below 1 = undervalued.",cat:"Fundamental"},
  {term:"EPS",def:"Earnings Per Share. Net income ÷ shares outstanding. Growing EPS = healthy company. Watch for non-recurring items that inflate it.",cat:"Fundamental"},
  {term:"ROE",def:"Return on Equity. Net income ÷ shareholder equity. Buffett's favorite metric — above 15% consistently = strong moat.",cat:"Fundamental"},
  {term:"CPI",def:"Consumer Price Index. Measures inflation. Core CPI (ex-food/energy) matters more to the Fed. Higher = rate hike fears.",cat:"Macro"},
  {term:"GDP",def:"Gross Domestic Product. Total economic output. Lagging indicator — by the time GDP confirms recession, stocks often already bottomed.",cat:"Macro"},
  {term:"NFP",def:"Non-Farm Payrolls. Monthly US jobs data, released first Friday at 8:30 AM ET. Massive market mover, especially forex.",cat:"Macro"},
  {term:"FOMC",def:"Federal Open Market Committee. Sets interest rates. 8 meetings/year. Dot plot and guidance often matter more than the decision.",cat:"Macro"},
  {term:"Yield Curve",def:"Plot of bond yields by maturity. Inversion (short > long) has predicted every recession since 1960 with one false signal.",cat:"Macro"},
  {term:"Pip",def:"Smallest forex price move. Most pairs: 0.0001. JPY pairs: 0.01. A 10-pip move in EUR/USD on a standard lot = $100.",cat:"Forex"},
  {term:"Spread",def:"Difference between bid and ask price. Narrower = more liquid. Major forex pairs: 0.1-1 pip. Exotic pairs: 5-20+ pips.",cat:"Forex"},
  {term:"Bull Market",def:"Sustained uptrend (+20% from lows). Average bull market lasts 5+ years. Longest: 2009-2020 (11 years).",cat:"General"},
  {term:"Bear Market",def:"Sustained decline (-20% from highs). Average bear lasts ~9.6 months. Occurs every 5.7 years on average.",cat:"General"},
  {term:"IPO",def:"Initial Public Offering. Company's first sale of shares to the public. Most underperform in first year — wait for lockup expiry.",cat:"General"},
  {term:"Dividend",def:"Cash payment from company to shareholders. Dividend Aristocrats raised dividends 25+ consecutive years. 40% of S&P returns came from dividends.",cat:"General"},
  {term:"ETF",def:"Exchange-Traded Fund. Basket of securities trading like a stock. Instant diversification, low fees (0.03-0.20%). 3-fund portfolio beats 90% of active managers.",cat:"General"},
  {term:"Options",def:"Right (not obligation) to buy (call) or sell (put) at specified price. 1 contract = 100 shares. Premium = cost. Greeks measure risk sensitivities.",cat:"Derivatives"},
  {term:"Call Option",def:"Right to buy at strike price. Profit when stock rises above strike + premium paid. Max loss = premium paid.",cat:"Derivatives"},
  {term:"Put Option",def:"Right to sell at strike price. Profit when stock falls below strike - premium. Like insurance for your portfolio.",cat:"Derivatives"},
  {term:"Implied Volatility",def:"Market's expectation of future price movement. High IV = expensive options. IV crush after earnings = option buyers lose even if right direction.",cat:"Derivatives"},
  {term:"Theta",def:"Time decay. Options lose value as expiration approaches. Accelerates in final 30 days. Option sellers profit from theta.",cat:"Derivatives"},
  {term:"Delta",def:"Option price change per $1 stock move. ATM call ≈ 0.50. Deep ITM ≈ 1.00. Position delta = directional exposure.",cat:"Derivatives"},
  {term:"ATR",def:"Average True Range. Measures volatility over 14 periods. Use 2× ATR for stop placement. Higher ATR = wider stops needed.",cat:"Technical"},
  {term:"VWAP",def:"Volume-Weighted Average Price. Most important intraday indicator. Price above VWAP = bullish. Resets daily.",cat:"Technical"},
  {term:"Swing Trading",def:"Holding 2-14 days. Best for most people — 30 min/day, don't need to watch screens. Pullback to MA in trend is the bread-and-butter setup.",cat:"Strategy"},
  {term:"Scalping",def:"Ultra-short-term trades (seconds to minutes). Needs 65%+ win rate. Highest failure rate. Commissions eat small profits. Not for beginners.",cat:"Strategy"},
  {term:"DCA",def:"Dollar-Cost Averaging. Fixed amount at regular intervals. Buys more when low, less when high. Reduces timing risk. Best for long-term investing.",cat:"Strategy"},
  {term:"ADR",def:"American Depositary Receipt. Buy foreign stocks on US exchanges. Levels I-III with increasing disclosure requirements.",cat:"General"},
  {term:"Sharpe Ratio",def:"Risk-adjusted return measure. (Return - Risk-free rate) / Standard deviation. Above 1.0 = good. Above 2.0 = excellent.",cat:"Risk"},
  {term:"Hedge",def:"Position that offsets risk in another position. Protective puts, inverse ETFs, gold. Budget 1-2% annually for portfolio protection.",cat:"Risk"},
  {term:"Contango",def:"Futures curve where later contracts are more expensive. Causes negative roll yield for commodity ETFs. Common in oil and natural gas.",cat:"Derivatives"},
  {term:"Backwardation",def:"Futures curve where earlier contracts are more expensive. Positive roll yield. Signals tight near-term supply.",cat:"Derivatives"},
];

// ── Render Functions ──

function renderResearch() {
  const grid = document.getElementById('researchGrid');
  if (!grid) return;
  grid.innerHTML = RESEARCH.map(r => `
    <div class="research-card" onclick="showResearch(${r.id})">
      <span class="type ${r.type}">${r.typeLabel}</span>
      <h3>${r.title}</h3>
      <p>${r.summary}</p>
      <div class="meta"><span>${r.date}</span><span>${r.readTime} read</span></div>
    </div>
  `).join('');
}

function showResearch(id) {
  const r = RESEARCH.find(x => x.id === id);
  if (!r) return;

  const modal = document.getElementById('courseModal');
  const detail = document.getElementById('courseDetail');

  detail.innerHTML = `
    <button class="close-btn" onclick="closeCourseModal()">✕</button>
    <span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78em;font-weight:600;margin-bottom:12px;background:${r.type==='daily'?'rgba(6,182,212,.12)':r.type==='weekly'?'rgba(139,92,246,.12)':'rgba(245,158,11,.12)'};color:${r.type==='daily'?'var(--cyan)':r.type==='weekly'?'var(--purple)':'var(--orange)'}">${r.typeLabel}</span>
    <h2 style="font-size:1.5em;font-weight:800;margin-bottom:8px;line-height:1.3">${r.title}</h2>
    <div style="display:flex;gap:16px;font-size:.82em;color:var(--text3);margin-bottom:24px">
      <span>📅 ${r.date}</span>
      <span>⏱️ ${r.readTime} read</span>
    </div>
    <div style="font-size:.92em;line-height:1.8;color:var(--text2)">${r.content}</div>
  `;

  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function renderSources() {
  const grid = document.getElementById('sourcesGrid');
  if (!grid) return;
  grid.innerHTML = SOURCES.map(s => `
    <a href="${s.url}" target="_blank" class="source-card">
      <div class="logo" style="background:rgba(59,130,246,.08)">${s.emoji}</div>
      <h4>${s.name}</h4>
      <p>${s.desc}</p>
      <span class="free-badge">Free</span>
    </a>
  `).join('');
}

function renderCourses(filter) {
  // Update tabs
  document.querySelectorAll('.courses-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.cat === filter);
  });

  const grid = document.getElementById('coursesGrid');
  if (!grid || typeof COURSES === 'undefined') return;

  const filtered = filter === 'all' ? COURSES : COURSES.filter(c => c.level === filter);
  grid.innerHTML = filtered.map(c => {
    const levelClass = c.level === 'beginner' ? 'beg' : c.level === 'intermediate' ? 'int' : 'adv';
    const levelLabel = c.level.charAt(0).toUpperCase() + c.level.slice(1);
    return `
      <div class="course-card" onclick="showCourse(${c.id})">
        <span class="tag ${levelClass}">${levelLabel}</span>
        <h3>${c.icon} ${c.title}</h3>
        <p>${c.desc}</p>
        <div class="course-meta">
          <span>📚 ${c.modules} modules</span>
          <span>⏱️ ${c.duration}</span>
        </div>
      </div>
    `;
  }).join('');
}

function showCourse(id) {
  const c = (typeof COURSES !== 'undefined') ? COURSES.find(x => x.id === id) : null;
  if (!c) return;

  const modal = document.getElementById('courseModal');
  const detail = document.getElementById('courseDetail');
  const levelClass = c.level === 'beginner' ? 'beg' : c.level === 'intermediate' ? 'int' : 'adv';
  const levelLabel = c.level.charAt(0).toUpperCase() + c.level.slice(1);

  detail.innerHTML = `
    <button class="close-btn" onclick="closeCourseModal()">✕</button>
    <span class="tag ${levelClass}">${levelLabel}</span>
    <h2>${c.icon} ${c.title}</h2>
    <p style="color:var(--text2);margin:8px 0 4px">${c.desc}</p>
    <div class="course-meta" style="margin-bottom:20px">
      <span>📚 ${c.modules} modules</span>
      <span>⏱️ ${c.duration}</span>
    </div>
    <ul class="module-list">
      ${c.lessons.map((l, i) => `
        <li class="module-item" onclick="toggleModule(this, ${c.id}, ${i})">
          <span class="num">${i + 1}</span>
          <div class="info"><h4>${l.t}</h4><p>${l.d}</p></div>
          <span class="dur">${l.d}</span>
          <span class="expand-icon">▼</span>
        </li>
        <div class="module-content" id="mod-${c.id}-${i}">${l.content}</div>
      `).join('')}
    </ul>
    ${c.quiz ? `
      <div class="quiz-section">
        <h3>📝 Quiz — Test Your Knowledge</h3>
        ${c.quiz.map((q, qi) => `
          <div class="quiz-q">
            <h4>${qi + 1}. ${q.q}</h4>
            <div class="quiz-opts">
              ${q.opts.map((o, oi) => `
                <div class="quiz-opt" onclick="checkQuiz(this, ${oi === q.ans})">${o}</div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    ` : ''}
  `;

  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function toggleModule(el, courseId, modIdx) {
  const content = document.getElementById(`mod-${courseId}-${modIdx}`);
  if (!content) return;
  const isShown = content.classList.contains('show');
  content.classList.toggle('show');
  el.classList.toggle('expanded');
}

function checkQuiz(el, isCorrect) {
  // Reset siblings
  const parent = el.parentElement;
  parent.querySelectorAll('.quiz-opt').forEach(o => {
    o.classList.remove('correct', 'wrong');
    o.style.pointerEvents = 'none';
  });

  if (isCorrect) {
    el.classList.add('correct');
  } else {
    el.classList.add('wrong');
    // Highlight correct answer
    const opts = parent.querySelectorAll('.quiz-opt');
    opts.forEach(o => {
      const idx = Array.from(opts).indexOf(o);
      // Can't easily get ans here, just mark the wrong one
    });
  }
}

function closeCourseModal() {
  document.getElementById('courseModal').classList.remove('open');
  document.body.style.overflow = '';
}

// ── Glossary ──
function renderGlossary(filter = '') {
  const grid = document.getElementById('glossaryGrid');
  if (!grid) return;

  const filtered = filter
    ? GLOSSARY.filter(g => g.term.toLowerCase().includes(filter.toLowerCase()) || g.def.toLowerCase().includes(filter.toLowerCase()))
    : GLOSSARY;

  grid.innerHTML = filtered.map(g => `
    <div class="glossary-item">
      <div class="term">${g.term}</div>
      <div class="def">${g.def}</div>
      <span class="cat">${g.cat}</span>
    </div>
  `).join('');
}

// ── Calculators ──
function openCalc(type) {
  const modal = document.getElementById('calcModal');
  const box = document.getElementById('calcBox');
  let html = '';

  switch(type) {
    case 'position':
      html = `
        <button class="calc-close" onclick="closeCalc()">✕</button>
        <h3>📐 Position Size Calculator</h3>
        <div class="calc-field"><label>Account Size ($)</label><input type="number" id="calcAccount" value="50000"></div>
        <div class="calc-field"><label>Risk Per Trade (%)</label><input type="number" id="calcRisk" value="1" step="0.5"></div>
        <div class="calc-field"><label>Entry Price ($)</label><input type="number" id="calcEntry" value="100"></div>
        <div class="calc-field"><label>Stop-Loss Price ($)</label><input type="number" id="calcStop" value="97"></div>
        <button class="btn btn-p" style="width:100%;margin-top:10px" onclick="calcPosition()">Calculate</button>
        <div class="calc-result" id="calcResult" style="display:none"><div class="value" id="calcValue"></div><div class="label" id="calcLabel"></div></div>`;
      break;
    case 'pnl':
      html = `
        <button class="calc-close" onclick="closeCalc()">✕</button>
        <h3>💰 Profit/Loss Calculator</h3>
        <div class="calc-field"><label>Entry Price ($)</label><input type="number" id="pnlEntry" value="100"></div>
        <div class="calc-field"><label>Exit Price ($)</label><input type="number" id="pnlExit" value="110"></div>
        <div class="calc-field"><label>Position Size (shares)</label><input type="number" id="pnlSize" value="100"></div>
        <div class="calc-field"><label>Direction</label><select id="pnlDir"><option value="long">Long</option><option value="short">Short</option></select></div>
        <button class="btn btn-p" style="width:100%;margin-top:10px" onclick="calcPnL()">Calculate</button>
        <div class="calc-result" id="calcResult" style="display:none"><div class="value" id="calcValue"></div><div class="label" id="calcLabel"></div></div>`;
      break;
    case 'margin':
      html = `
        <button class="calc-close" onclick="closeCalc()">✕</button>
        <h3>🏦 Margin Calculator</h3>
        <div class="calc-field"><label>Position Value ($)</label><input type="number" id="marginValue" value="100000"></div>
        <div class="calc-field"><label>Leverage</label><input type="number" id="marginLeverage" value="10"></div>
        <button class="btn btn-p" style="width:100%;margin-top:10px" onclick="calcMargin()">Calculate</button>
        <div class="calc-result" id="calcResult" style="display:none"><div class="value" id="calcValue"></div><div class="label" id="calcLabel"></div></div>`;
      break;
    case 'currency':
      html = `
        <button class="calc-close" onclick="closeCalc()">✕</button>
        <h3>💱 Currency Converter</h3>
        <div class="calc-field"><label>Amount</label><input type="number" id="currAmount" value="1000"></div>
        <div class="calc-field"><label>From</label><select id="currFrom"><option>USD</option><option>EUR</option><option>GBP</option><option>JPY</option><option>CNY</option><option>AUD</option><option>CAD</option><option>CHF</option></select></div>
        <div class="calc-field"><label>To</label><select id="currTo"><option>EUR</option><option>USD</option><option>GBP</option><option>JPY</option><option>CNY</option><option>AUD</option><option>CAD</option><option>CHF</option></select></div>
        <button class="btn btn-p" style="width:100%;margin-top:10px" onclick="calcCurrency()">Convert</button>
        <div class="calc-result" id="calcResult" style="display:none"><div class="value" id="calcValue"></div><div class="label" id="calcLabel"></div></div>`;
      break;
  }

  box.innerHTML = html;
  modal.classList.add('open');
}

function closeCalc() {
  document.getElementById('calcModal').classList.remove('open');
}

function calcPosition() {
  const account = parseFloat(document.getElementById('calcAccount').value);
  const risk = parseFloat(document.getElementById('calcRisk').value);
  const entry = parseFloat(document.getElementById('calcEntry').value);
  const stop = parseFloat(document.getElementById('calcStop').value);

  const riskAmount = account * (risk / 100);
  const perShareRisk = Math.abs(entry - stop);
  const shares = Math.floor(riskAmount / perShareRisk);

  document.getElementById('calcResult').style.display = 'block';
  document.getElementById('calcValue').textContent = shares + ' shares';
  document.getElementById('calcLabel').textContent = `Risk: $${riskAmount.toFixed(0)} | Per share: $${perShareRisk.toFixed(2)} | Total position: $${(shares * entry).toFixed(0)}`;
}

function calcPnL() {
  const entry = parseFloat(document.getElementById('pnlEntry').value);
  const exit = parseFloat(document.getElementById('pnlExit').value);
  const size = parseFloat(document.getElementById('pnlSize').value);
  const dir = document.getElementById('pnlDir').value;

  const pnl = dir === 'long' ? (exit - entry) * size : (entry - exit) * size;
  const pct = dir === 'long' ? ((exit - entry) / entry * 100) : ((entry - exit) / entry * 100);

  document.getElementById('calcResult').style.display = 'block';
  document.getElementById('calcValue').textContent = (pnl >= 0 ? '+' : '') + '$' + pnl.toFixed(2);
  document.getElementById('calcValue').style.background = pnl >= 0
    ? 'linear-gradient(135deg,#10b981,#059669)' : 'linear-gradient(135deg,#ef4444,#dc2626)';
  document.getElementById('calcValue').style['-webkit-background-clip'] = 'text';
  document.getElementById('calcLabel').textContent = `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}% | ${dir === 'long' ? 'Long' : 'Short'}`;
}

function calcMargin() {
  const value = parseFloat(document.getElementById('marginValue').value);
  const leverage = parseFloat(document.getElementById('marginLeverage').value);
  const margin = value / leverage;

  document.getElementById('calcResult').style.display = 'block';
  document.getElementById('calcValue').textContent = '$' + margin.toLocaleString();
  document.getElementById('calcLabel').textContent = `Leverage: ${leverage}:1 | Margin: ${(100/leverage).toFixed(1)}% | A ${((100/leverage)).toFixed(1)}% move = 100% of margin`;
}

function calcCurrency() {
  const rates = {USD:1,EUR:0.92,GBP:0.79,JPY:151.5,CNY:7.24,AUD:1.53,CAD:1.37,CHF:0.88};
  const amount = parseFloat(document.getElementById('currAmount').value);
  const from = document.getElementById('currFrom').value;
  const to = document.getElementById('currTo').value;

  const result = amount * (rates[to] / rates[from]);

  document.getElementById('calcResult').style.display = 'block';
  document.getElementById('calcValue').textContent = result.toFixed(2) + ' ' + to;
  document.getElementById('calcLabel').textContent = `${amount} ${from} = ${result.toFixed(2)} ${to} (approximate rate)`;
}

// ── Canvas Particle Background ──
function initCanvas() {
  const canvas = document.getElementById('heroCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  const count = 60;

  function resize() {
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      r: Math.random() * 2 + 1,
      a: Math.random() * 0.5 + 0.1
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(59,130,246,${p.a})`;
      ctx.fill();

      // Connect nearby particles
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(59,130,246,${0.08 * (1 - dist/120)})`;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
}

// ── Navigation ──
function initNav() {
  const links = document.querySelectorAll('.nav-links a:not(.nav-cta)');
  const sections = ['home', 'features', 'courses', 'research', 'glossary', 'tools'];

  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY + 100;
    let current = 'home';
    for (const id of sections) {
      const el = document.getElementById(id);
      if (el && el.offsetTop <= scrollY) current = id;
    }
    links.forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === '#' + current);
    });
  });
}

// ── Mike Advisor Chip (add if missing) ──
function addMikeChip() {
  const row = document.querySelector('.advisors-row');
  if (!row || document.getElementById('chipMike')) return;
  const mikeChip = document.createElement('div');
  mikeChip.className = 'advisor-chip';
  mikeChip.id = 'chipMike';
  mikeChip.setAttribute('onclick', "switchAdvisor('mike')");
  mikeChip.innerHTML = '<div class="av" style="background:linear-gradient(135deg,#f59e0b,#ef4444)">🧑‍💻</div><div><div class="name">Mike Torres</div><div class="role">Fundamentals & Macro</div><div class="online">Online</div></div>';
  row.appendChild(mikeChip);
}

// ── Initialize ──
document.addEventListener('DOMContentLoaded', () => {
  // Render sections
  renderCourses('all');
  renderResearch();
  renderSources();
  renderGlossary();
  initCanvas();
  initNav();
  addMikeChip();

  // Initial AI greeting
  const body = document.getElementById('chatBody');
  if (body) {
    const greeting = ADVISORS.alex.greeting;
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.innerHTML = greeting;
    body.appendChild(div);
  }

  // Glossary search
  const searchInput = document.getElementById('glossarySearch');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      renderGlossary(e.target.value);
    });
  }

  // Close modals on click outside
  document.getElementById('courseModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'courseModal') closeCourseModal();
  });
  document.getElementById('calcModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'calcModal') closeCalc();
  });
});
