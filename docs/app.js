// ═══════════════════════════════════════════════════
// BroadFSC Pro — App Logic v4 (SOUL + Registration)
// AI with warmth, expertise, memory, and lead capture
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
    'bitcoin': "Bitcoin is digital gold with a 21M supply cap. The 4-year halving cycle has historically driven bull markets, but the 2024 cycle has shown diminishing returns — BTC peaked near $108K in Nov 2024 and has since pulled back to ~$75K. Key levels: 200-week MA at ~$52K (never broken in a bear market), realized price at ~$42K, and the $108K ATH. Institutional adoption via ETFs changed the game in 2024. Treat BTC as a long-term holding — 5% portfolio allocation, cold storage, don't trade it with leverage.",
    'crypto': "Crypto is 24/7 with 10-20% daily volatility — not for the faint of heart. BTC dominance drives the cycle: when it falls, alt season begins. Never put more than 5% in a single altcoin, 15% total crypto allocation. Most altcoins go to zero. Stick to top 20 for safety. And never use leverage in crypto — the volatility is already leveraged. Note: in 2026, gold's parabolic rally to $4,800+ has drawn some safe-haven flows away from BTC."
  },
  platform: {
    'broadfsc': "BroadFSC is a regulated investment advisory platform. We're licensed by major financial authorities and serve global investors (except mainland China). What makes us different: AI-powered education, transparent fees, and actual human support when you need it. Think of us as the platform that actually wants you to learn, not just trade.",
    'account': "Opening a BroadFSC account is straightforward — verified ID, proof of address, and you're in. We support multiple currencies and offer both advisory and self-directed accounts. Minimums are kept low because we believe everyone deserves access to professional tools. Contact our team through this chat or visit broadfsc.com for details.",
    'fees': "We keep fees transparent — no hidden charges. Our structure is competitive with major platforms, and we don't nickel-and-dime on small transactions. The specific fee schedule depends on your account type and services. What I can tell you: we're not the cheapest, but we're far from the most expensive, and the value you get in education and support more than covers it."
  },
  stocks: {
    'apple aapl': "Apple (AAPL) is the world's most valuable company with a $3+ trillion market cap. Key investment thesis: (1) Services revenue growing 15%+ YoY — this is the real margin driver, now 25% of revenue but 40%+ of gross profit. (2) iPhone remains the cash cow, but growth has plateaued at 2-5% annually. (3) AI integration (Apple Intelligence) could trigger the next upgrade supercycle. (4) Massive $100B+ annual buyback program supports the stock. Risks: China sales declining, regulatory pressure on App Store fees, and slower innovation cycles. Valuation typically ranges 25-30x earnings — not cheap, but the ecosystem lock-in justifies a premium. Key support: 150-week MA. Resistance: ATH zone.",
    'nvidia nvda': "NVIDIA (NVDA) has been the undisputed king of the AI trade. Data center revenue is growing 100%+ YoY driven by insatiable demand for AI training and inference chips. The bull case: AI capex from Big Tech is projected at $650-700B in 2026, and NVIDIA captures ~80% of the GPU market. The bear case: any deceleration in data center revenue growth could trigger a 15-20% selloff — the stock is priced for perfection at 35-40x forward earnings. Key levels: 50 SMA for trend, 200 SMA for macro trend. The real risk isn't competition (AMD is years behind) — it's a capex slowdown if AI ROI doesn't materialize. Position sizing is critical here: max 3-5% of portfolio due to volatility.",
    'tesla tsla': "Tesla (TSLA) is the most polarizing stock in the market. Bull case: (1) Energy storage business growing 100%+ YoY with fatter margins than cars. (2) FSD/autonomy — if they crack it, the robotaxi TAM is $10T+. (3) Optimus robot could be transformative long-term. Bear case: (1) Auto margins compressed from 25%+ to under 18% due to price wars. (2) EV demand slowing globally. (3) CEO distraction risk. The stock trades on narrative, not fundamentals — 50-60x PE even in a 'bad' year. Technically, it's extremely volatile: 30-40% swings are normal. Only for risk-tolerant investors with 5+ year horizons.",
    'microsoft msft': "Microsoft (MSFT) might be the safest big-tech play. Azure is gaining cloud market share (now ~25%), and AI integration via Copilot is driving real revenue growth. FY2026 capex expected above $88B, mostly for AI infrastructure. Key metrics: Cloud revenue growing 25%+, Microsoft 365 commercial revenue growing 15%+. The stock rarely gets cheap — 30-35x earnings is the normal range. But it's one of the few mega-caps with both growth AND a Warren Buffett-style moat. Buy the 50 SMA pullbacks, hold for years.",
    'amazon amzn': "Amazon (AMZN) is a two-headed beast: AWS (cloud) growing 20%+ and retail improving margins. AWS is the profit engine — 65%+ of operating income despite being 15% of revenue. The AI play: AWS Bedrock and custom Trainium chips position Amazon as the 'AI infrastructure for everyone.' Capex surging past $100B in 2026. Retail is finally showing discipline on costs, pushing operating margins above 10%. Risks: antitrust regulation, AWS growth deceleration, and retail margin compression in recession. Valuation is reasonable at 25-30x forward earnings given the dual growth engines.",
    'google alphabet': "Alphabet/Google (GOOGL) is the most undervalued of the Magnificent 7 on a PEG basis. Search still generates $250B+ annually with 30%+ margins. YouTube is a $40B business growing 15%. Cloud (GCP) is finally profitable and growing 30%+. AI integration via Gemini and Search Generative Experience is a double-edged sword: it could enhance search OR disrupt it. The antitrust overhang is real — potential forced divestiture of Chrome/Android could fundamentally change the company. But at 20-22x earnings, the market is pricing in significant risk. I see value here with a 12-month horizon.",
    'meta facebook': "Meta (META) has executed one of the greatest pivots in corporate history — from metaverse money-burner to AI-powered profit machine. Reality Labs still burns $15B+ annually, but the core ads business is firing on all cylinders. AI-powered ad targeting (Advantage+) is driving 20%+ ad revenue growth. Threads hit 300M+ users. Reels monetization is now on par with Feed. The stock is surprisingly cheap at 22-25x earnings given 25%+ revenue growth. Key risk: regulatory (EU AI Act, US ad targeting restrictions). Buy the 50 SMA, target new highs.",
    's&p 500 spx': "The S&P 500 is the benchmark for US equities, comprising the 500 largest companies. In 2026, it's been driven by AI capex ($650-700B from Big Tech), resilient earnings, and Middle East ceasefire hopes. Key levels: support at 5,850 (20 EMA) and 5,700 (50 SMA), resistance at 6,100 (ATH zone). The Magnificent 7 still account for 30%+ of index weight — concentration risk is real. For most investors, a simple VTI (total market) or SPY allocation of 60-70% of their equity portfolio is the smartest move.",
    'gold xau': "Gold has been the trade of the decade — surging from $2,000 to $4,800+ in 18 months. This isn't speculative; it's structural. Central banks bought 1,200+ tonnes in 2025 (record pace), driven by de-dollarization. China's PBOC has bought for 24+ consecutive months. Add geopolitical risk premium and $2T+ US fiscal deficits, and gold's floor keeps rising. Key levels: support $4,650, $4,400; targets $5,000, $5,500. The play: buy dips to $4,650, stop at $4,400, or use gold miners (GDX/GDXJ) for 2-3x leverage. Not too late, but use stops — a Middle East peace breakthrough could trigger 5-8% pullback.",
    'tsmc semiconductor': "TSMC (TSM) is the world's most important company nobody talks about. They manufacture 90%+ of the world's most advanced chips — NVIDIA, Apple, AMD all depend on them. Revenue growing 30%+ YoY on AI demand. The moat is extraordinary: it takes 10+ years and $20B+ to build leading-edge fab capacity. Risks: geopolitical (Taiwan Strait) and customer concentration. If you want AI exposure without the Magnificent 7 premium, TSMC is the backdoor play. Buy on geopolitical fear dips.",
    'berkshire hathaway': "Berkshire Hathaway (BRK.A/BRK.B) is the ultimate defensive play. Warren Buffett's cash pile hit $300B+ in 2026 — he's selling stocks and waiting for opportunity. When Buffett builds this much cash, it historically signals market froth. Berkshire's portfolio: heavy on Apple, Bank of America, American Express, Chevron. Insurance float is the real secret weapon — essentially free leverage. The stock tends to outperform in bear markets and underperform in bull markets. If you're worried about a correction, add BRK.B as a hedge. It's the 'sleep well at night' stock.",
    'jpmorgan chase': "JPMorgan (JPM) is the king of banks — the only major bank that got STRONGER after the 2023 regional banking crisis. Jamie Dimon is the most respected CEO in finance. Net interest income hitting records as rates stay 'higher for longer.' Key advantage: fortress balance sheet allows them to lend when others can't. The stock is never cheap (12-15x earnings), but you're paying for the best-in-class franchise. If the yield curve steepens (long rates rise), JPM is the biggest beneficiary. Buy on recession fears — that's when Dimon deploys the war chest.",
    'marathon petroleum mpc': "Marathon Petroleum (MPC) is the largest US independent refiner with 16 refineries and ~3M barrels/day capacity. Key thesis: (1) US refining margins remain strong due to limited new capacity — no major refineries built in 40+ years. (2) Midstream business (MPLX) provides steady cash flow via pipeline and logistics. (3) Aggressive capital return — $5B+ buyback + growing dividend. (4) Crack spreads (the difference between crude and product prices) are MPC's primary driver — when gasoline/diesel demand is strong, MPC prints money. Risks: Energy transition reducing long-term fuel demand, regulatory pressure on emissions, and crack spread compression in recession. Valuation: typically 6-9x earnings — cheap for a reason (cyclical). Best play: buy when crack spreads are depressed and sentiment is bearish, sell when everyone loves energy. Currently benefiting from strong US fuel exports and limited global refining capacity.",
    'exxonmobil xom': "ExxonMobil (XOM) is the largest Western oil major with integrated operations across upstream, downstream, and chemicals. Key thesis: (1) Pioneer Natural Resources acquisition doubled Permian Basin position — now the #1 producer. (2) Guyana discoveries (Stabroek Block) are a generational asset with 11B+ barrels of recoverable reserves. (3) Dividend Aristocrat — 40+ consecutive years of increases. (4) Low break-even costs (~$35-40/barrel) protect profits even in oil downturns. Risks: Energy transition, climate litigation, OPEC+ production decisions. Valuation: 10-13x earnings, ~4% dividend yield. Treat as a defensive income stock with upside from oil price spikes.",
    'chevron cvx': "Chevron (CVX) is the #2 US oil major with a cleaner balance sheet than most peers. Key thesis: (1) Permian Basin growth — targeting 1M boe/day by 2027. (2) Hess acquisition adds Guyana assets alongside Exxon. (3) Strong cash generation at $70+ oil — returns $15-20B annually to shareholders. (4) Payout ratio below 50% — dividend is rock-solid. Risks: Guyana acquisition uncertainty (arbitration with Exxon), energy transition, oil price volatility. Buy below $150 for a 4.5%+ yield with growth optionality.",
    'palantir pltr': "Palantir (PLTR) is the most controversial AI stock — a $100B+ company with $2.5B revenue. Bull case: (1) AIP (AI Platform) is driving explosive commercial revenue growth (50%+ YoY). (2) Government contracts are sticky — once integrated, nearly impossible to replace. (3) Alex Karp is building an 'AI operating system for Western institutions.' Bear case: (1) Valuation at 35-40x SALES is extreme. (2) Stock-based compensation is massive (~20% of revenue). (3) Government revenue growth slowing to single digits. (4) Insider selling has been relentless. This is a high-conviction, high-risk bet. Position size max 2-3%. Buy on 20%+ pullbacks, sell into strength.",
    'amd': "AMD is NVIDIA's only serious competitor in AI chips. MI300X is competitive with H100 for inference workloads. Key thesis: (1) Server CPU market share gaining on Intel — now ~25%+. (2) AI GPU revenue growing 100%+ but from a small base. (3) Lisa Su is one of the best CEOs in tech. Risks: Still far behind NVIDIA in AI software ecosystem (ROCm vs CUDA), Intel's turnaround attempt could compress CPU margins, and AI chip market may not support two $100B+ players. Valuation at 25-30x earnings is reasonable if AI revenue accelerates. Buy the 50 SMA, but don't expect NVIDIA-level upside.",
    'coca cola ko': "Coca-Cola (KO) is Warren Buffett's longest-held stock for good reason. (1) Pricing power — people pay 2-3x for the brand over generic cola. (2) Global distribution in 200+ countries. (3) Dividend King — 60+ consecutive years of increases. (4) recession-resistant — people still buy Coke when money is tight. The stock won't make you rich fast, but it's one of the safest 3-4% yields in the market with 5-7% annual dividend growth. Ideal for income portfolios and conservative investors.",
  }
};

// ── SOUL AI Advisor Personalities (v4: Warmer & More Professional) ──
const ADVISORS = {
  alex: {
    name: 'Alex Chen',
    emoji: '👨‍💼',
    role: 'Technical Analysis',
    greeting: "Hey there 👋 I'm Alex, and I've been in the markets for 8 years now — seen bull runs, crashes, and everything in between. I'm here to give you the kind of honest, no-BS guidance I wish someone had given me when I started. Charts, setups, indicators — fire away. I genuinely enjoy helping people navigate this stuff.",
    style: 'direct',
    catchphrase: "Let me be straight with you —",
    perspective: "I believe technical analysis works not because it's magic, but because millions of traders watch the same levels. It's self-fulfilling, and that's fine — use it."
  },
  sarah: {
    name: 'Sarah Kim',
    emoji: '👩‍💼',
    role: 'Risk Management',
    greeting: "Hi there 😊 I'm Sarah, and I'm passionate about one thing: making sure you stay in the game long enough to succeed. I've seen too many talented traders blow up because they ignored risk management — it's honestly heartbreaking. Let me help you build a framework that protects you. Ask me anything about position sizing, stops, or keeping your emotions in check.",
    style: 'warm',
    catchphrase: "Here's what the numbers tell us —",
    perspective: "I'd rather miss a profit than take an unnecessary loss. Preservation of capital always comes first. If your risk management is solid, the profits will follow."
  },
  mike: {
    name: 'Mike Torres',
    emoji: '🧑‍💻',
    role: 'Fundamentals & Macro',
    greeting: "Welcome! I'm Mike 👋 I'm the big-picture guy — earnings, central banks, geopolitical shifts, economic data. Technicals tell you WHEN to act; fundamentals tell you WHY. And understanding the 'why' is what separates guessing from investing. I'd love to help you connect the dots. What market or theme are you curious about?",
    style: 'analytical',
    catchphrase: "Looking at the bigger picture —",
    perspective: "Price is what you pay, value is what you get. I focus on understanding WHY markets move, not just the pattern on the chart. Fundamentals win in the long run."
  }
};

// ── AI State ──
let currentAdvisor = 'alex';
let chatHistories = { alex: [], sarah: [], mike: [] };  // Separate history per advisor
let userName = localStorage.getItem('bfs_username') || '';
let userEmail = localStorage.getItem('bfs_email') || '';
let isRegistered = !!userEmail;
let isSending = false;  // Prevent duplicate sends

// ── Registration System ──
function showRegisterModal(source) {
  if (isRegistered) {
    // Already registered, show a thank-you message
    showRegisterToast('You\'re already registered! 🎉 Check your inbox for our latest research.');
    return;
  }
  const modal = document.getElementById('registerModal');
  const sourceInput = document.getElementById('regSource');
  if (sourceInput) sourceInput.value = source || 'general';
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    // Focus email field
    setTimeout(() => {
      const emailField = document.getElementById('regEmail');
      if (emailField) emailField.focus();
    }, 300);
  }
}

function closeRegisterModal() {
  const modal = document.getElementById('registerModal');
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

function submitRegistration() {
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const interests = document.getElementById('regInterests').value;
  const source = document.getElementById('regSource').value;

  // Validate
  if (!email || !email.includes('@') || !email.includes('.')) {
    document.getElementById('regError').textContent = 'Please enter a valid email address.';
    document.getElementById('regError').style.display = 'block';
    return;
  }
  if (!name || name.length < 2) {
    document.getElementById('regError').textContent = 'Please enter your name.';
    document.getElementById('regError').style.display = 'block';
    return;
  }

  // Save to localStorage
  userName = name;
  userEmail = email;
  isRegistered = true;
  localStorage.setItem('bfs_username', name);
  localStorage.setItem('bfs_email', email);
  localStorage.setItem('bfs_interests', interests);
  localStorage.setItem('bfs_reg_date', new Date().toISOString());

  // Close modal
  closeRegisterModal();

  // Show success toast
  showRegisterToast(`Welcome aboard, ${name}! 🎉 Your access to exclusive research is now unlocked.`);

  // If chat is open, have the advisor acknowledge
  const body = document.getElementById('chatBody');
  if (body) {
    const advisor = ADVISORS[currentAdvisor];
    setTimeout(() => {
      const resp = `${advisor.emoji} Great to have you with us, ${name}! I've noted your interest in ${interests || 'investing'}. Feel free to ask me anything — I'm here to help you succeed. By the way, you'll receive our best research reports directly at ${email}.`;
      addBotMessage(resp);
      chatHistories[currentAdvisor].push({ role: 'bot', text: resp });
    }, 800);
  }

  // TODO: In production, send to backend API
  console.log('[Registration]', { name, email, interests, source, date: new Date().toISOString() });
}

function showRegisterToast(msg) {
  const toast = document.getElementById('regToast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// ── AI Response Engine (SOUL-powered) ──
function getAIResponse(input) {
  const q = input.toLowerCase().trim();
  const advisor = ADVISORS[currentAdvisor];

  // Memory: check chat history for context
  const lastTopics = (chatHistories[currentAdvisor] || []).slice(-6).map(m => m.text.toLowerCase()).join(' ');

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

  // 2. Pattern matching for common questions (v4: warmer, more professional)
  const patterns = [
    { test: /how.*start|beginner|where.*begin|new.*trad/i, resp: () => formatAdvisorResponse("I'm really glad you're starting this journey — it can feel overwhelming at first, but that's completely normal. Here's the roadmap I wish I'd had: (1) Read our Stock Market Fundamentals course — it's free and genuinely helpful. (2) Paper trade for at least 3 months. I know it feels like a waste of time, but trust me, it saves you real money. (3) Start small — $1-2K max. You're learning, not retiring. (4) Master ONE setup before adding more. This is where most people go wrong. (5) Keep a journal from day one. The traders who journal consistently outperform those who don't — it's not even close. What part of this journey are you on right now?", 'strategy') },
    { test: /recommend|suggest|which.*stock|what.*buy|pick/i, resp: () => {
      if (currentAdvisor === 'alex') return "I appreciate the trust, and I take that seriously — so I won't give you a specific buy/sell call without knowing your full picture. That wouldn't be responsible. What I CAN do is something more valuable: teach you how to fish. Look for strong trends pulling back to support, confirmed by RSI or MACD divergence. That's where I start every single day. Want me to walk you through a real example of how I find setups?";
      if (currentAdvisor === 'sarah') return "That's a question everyone asks, and I respect that you're thinking about it. But here's my honest answer: before you put money into ANY trade, you need three non-negotiables — a clear entry reason, a stop-loss level, and a profit target. If you can't articulate all three, you're not investing, you're guessing. Let me help you build that framework first. The picks will come naturally once you have a process.";
      return "I won't pretend I have a crystal ball — nobody does, despite what some might claim. What I focus on is understanding what drives markets: earnings growth trends, central bank policy shifts, and sector rotation. When all three align, that's where the real opportunities are. Would you like me to break down any of those areas for you?";
    }},
    { test: /crypto|bitcoin|btc|ethereum|alt/i, resp: () => formatAdvisorResponse(KNOWLEDGE.crypto[q.includes('bitcoin') || q.includes('btc') ? 'bitcoin' : 'crypto'] || KNOWLEDGE.crypto.crypto, 'crypto') },
    { test: /forex|currency|eur.*usd|gbp|jpy/i, resp: () => formatAdvisorResponse("Forex is fascinating — it's the largest market in the world at $6.6 trillion daily, and it runs 24/5. Here's what took me years to learn: the London session has the highest volume, New York opens with high volatility, and their overlap (8 AM–12 PM ET) is where the real action happens. Major pairs like EUR/USD and GBP/USD have tight spreads and are your best friends as a beginner. Exotic pairs? I'd stay away until you really know what you're doing. And the #1 mistake I see — honestly, it breaks my heart every time — is over-leveraging. Start with 10:1 max as a beginner. Your future self will thank you.", 'strategy') },
    { test: /option|call|put|spread/i, resp: () => formatAdvisorResponse("Options are powerful tools, but they can be dangerous if you don't understand them. Let me break it down simply: options give you the RIGHT but not the OBLIGATION to buy (call) or sell (put) at a specific price. The Greeks tell you how your option behaves — Delta (direction), Gamma (acceleration), Theta (time decay, which works against buyers), Vega (volatility). My honest recommendation for beginners: start with credit spreads (bull put / bear call). You have defined risk, you can profit even if you're slightly wrong, and time decay actually works in your favor. And please — never buy far out-of-the-money options close to expiration. Theta will eat your premium alive. I've seen too many people learn this the hard way.", 'strategy') },
    { test: /loss|losing|down|red|bleeding|drawdown/i, resp: () => {
      if (currentAdvisor === 'sarah') return "First of all, take a breath. Losing is part of trading — every single professional loses. The question is never 'will I lose?' but 'are my losses controlled?' Here's my checklist for you right now: (1) Did you have a stop-loss? If no, that's the #1 thing to fix going forward. (2) Was the loss more than 1-2% of your account? If yes, we need to work on position sizing. (3) Did you follow your plan? If yes, this is just variance — it happens, and you should stay the course. If no, let's identify the violation. (4) Are you thinking about increasing size to recover? Please don't. That's the exact path to blowing up an account. I've seen it too many times. Take a breath, reduce your size by 50%, and let's get back to basics. You will recover from this.";
      return formatAdvisorResponse("I hear you, and I want you to know — every single successful trader has been exactly where you are right now. The difference between those who make it and those who don't is how they respond. Here's what works: (1) Never increase size during a losing streak — I know the temptation, but it's a trap. (2) Cut your position size in half. (3) Review every trade honestly — are you following your plan or deviating? (4) If you ARE following the plan, this is just variance. Stay the course. (5) Take a 1-2 day break if you need it. The market will still be here, I promise. You're going to be okay.", 'risk');
    }},
    { test: /hello|hi|hey|greetings|good morning|good evening/i, resp: () => {
      const timeGreet = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 18 ? 'Good afternoon' : 'Good evening';
      if (!userName && !isRegistered) return `${timeGreet}! 👋 ${ADVISORS[currentAdvisor].greeting} By the way, what should I call you? I'd love to personalize our conversation.`;
      if (!userName) return `${timeGreet}! 👋 Great to see you here. What's on your mind today? I'm ready to dive into whatever market topic you're curious about.`;
      return `${timeGreet}, ${userName}! 😊 Great to see you again. What's on your mind today? We can talk setups, risk management, market outlook — whatever you need. I'm all ears.`;
    }},
    { test: /my name is|i'm called|call me|i am (.+)/i, resp: () => {
      const nameMatch = input.match(/(?:my name is|i'm called|call me|i am)\s+(\w+)/i);
      if (nameMatch) {
        userName = nameMatch[1];
        localStorage.setItem('bfs_username', userName);
        return `It's really nice to meet you, ${userName}! 😊 I'll remember that. Now, what can I help you with? Whether it's market analysis, trading strategies, or risk management — I'm here for you.`;
      }
      return "Got it! What would you like to talk about?";
    }},
    { test: /thank|thanks|appreciate/i, resp: () => `You're very welcome, ${userName || 'friend'}! 😊 That's exactly what I'm here for. Don't hesitate to come back with more questions — there's no such thing as a dumb question in this business. We're all learning.` },
    { test: /broadfsc|platform|company|about you/i, resp: () => formatAdvisorResponse(KNOWLEDGE.platform.broadfsc, 'platform') },
    { test: /fee|cost|price|commission|charge/i, resp: () => formatAdvisorResponse(KNOWLEDGE.platform.fees, 'platform') },
    { test: /account|open|register|sign up/i, resp: () => {
      if (isRegistered) return `You're already registered with us, ${userName || 'friend'}! 🎉 If you need any help with your account or want to explore our research, just let me know. I'm here to help.`;
      return formatAdvisorResponse(KNOWLEDGE.platform.account, 'platform') + '\n\n💡 You can also register right here on this page — just click the "Get Access" button or the profile icon in the top right. It takes 30 seconds and unlocks our full research library.';
    }},
    { test: /help|can you|what can you/i, resp: () => `I can help with quite a lot, ${userName || 'friend'}! Here's what I'm best at: 📊 Technical analysis (RSI, MACD, Fibonacci, S/R, candlesticks), 🛡️ Risk management (position sizing, stop-losses, risk-reward), 🎯 Trading strategies (swing, day trading, scalping, dividends), 📋 Fundamental analysis (earnings, P/E, macro data), ₿ Crypto & forex, and 📈 Options strategies. I also know all about BroadFSC's services. Just ask naturally — no special commands needed. I'm here to have a real conversation with you.` },
    { test: /psychology|emotion|discipline|fear|greed|mindset/i, resp: () => formatAdvisorResponse("Trading psychology is honestly the most underrated aspect of this whole game. Fear makes you sell at the exact wrong time and avoid perfectly good setups. Greed makes you chase, over-leverage, and ignore your own stops. The solution isn't 'stop feeling emotions' — that's impossible. The solution is having a written plan and following it mechanically, even when your gut is screaming otherwise. The top biases that destroy accounts: confirmation bias (only seeing what supports your position), loss aversion (holding losers way too long because it 'doesn't count until you sell'), and overconfidence (sizing up after a few wins). A trading journal is honestly the #1 improvement tool — track every trade AND your emotional state when you made it. The patterns you'll discover about yourself are eye-opening.", 'strategy') },
    { test: /dividend|passive income|yield|drip/i, resp: () => formatAdvisorResponse(KNOWLEDGE.strategy.dividend, 'strategy') },
    { test: /etf|index fund|boglehead|3.fund/i, resp: () => formatAdvisorResponse(KNOWLEDGE.strategy.etf, 'strategy') },
    { test: /market.*outlook|prediction|forecast|where.*market/i, resp: () => {
      if (currentAdvisor === 'mike') return "I love this question, and I'll be honest with you — nobody can predict the future consistently, despite what some might claim. What I CAN do is help you read the signals. Right now, I'm watching: the yield curve (inversion has preceded every recession since 1960), ISM PMI (below 50 means contraction), and Fed forward guidance. The trend is your friend until it bends. Want me to break down any specific indicator? I genuinely enjoy explaining these.";
      return "I won't insult your intelligence by pretending I can predict markets — no one can, consistently. What I can do is help you prepare for multiple scenarios. The edge isn't in prediction, it's in preparation. Have a plan for the bullish case AND the bearish case, and execute whichever one the market gives you. That's how professionals operate. What specific market or timeframe are you thinking about?";
    }},
    { test: /contact|email|reach|phone|support/i, resp: () => `Great question! Here's how you can reach us:\n\n📧 **Email:** support@broadfsc.com\n📱 **Telegram:** @BroadInvestBot (24/7 AI assistant + human support)\n💬 **Live Chat:** Right here on this page!\n🌐 **Website:** broadfsc.com\n\nWe typically respond within 2 hours during business hours. For urgent matters, Telegram is the fastest way to reach us. Is there something specific I can help you with right now?` },
    { test: /report|analysis|research/i, resp: () => {
      if (isRegistered) return `As a registered member, you have full access to all our research, ${userName || 'friend'}! 📊 Check out the Research section below for our latest reports. If you want a specific stock or market analysis, just ask — I'm happy to discuss it with you.`;
      return `We publish professional-grade research daily — and it's completely free! 📊 You can browse our latest reports in the Research section below. For exclusive deep-dive analysis and personalized stock reports, I'd recommend registering — it takes just 30 seconds and gives you full access. Want me to help you sign up?`;
    }},
    // Stock / company queries (English + Chinese)
    { test: /apple|aapl|iphone|tim cook|苹果/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['apple aapl'], 'stocks') },
    { test: /nvidia|nvda|jensen|gpu|ai chip|英伟达/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['nvidia nvda'], 'stocks') },
    { test: /tesla|tsla|elon|ev car|electric vehicle|特斯拉/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['tesla tsla'], 'stocks') },
    { test: /microsoft|msft|satya|azure|copilot|微软/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['microsoft msft'], 'stocks') },
    { test: /amazon|amzn|bezos|aws\b|亚马逊/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['amazon amzn'], 'stocks') },
    { test: /google|alphabet|googl|youtube|gemini ai|谷歌/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['google alphabet'], 'stocks') },
    { test: /meta|facebook|fb\b|zuckerberg|instagram|threads|脸书/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['meta facebook'], 'stocks') },
    { test: /s&p|spx|spy|sp500|s&p500|index fund|market index|标普/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['s&p 500 spx'], 'stocks') },
    { test: /gold|xau|precious metal|de.dollar|黄金/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['gold xau'], 'stocks') },
    { test: /tsmc|taiwan semiconductor|chip maker|semiconductor|台积电/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['tsmc semiconductor'], 'stocks') },
    { test: /berkshire|buffett|warren|brk|巴菲特/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['berkshire hathaway'], 'stocks') },
    { test: /jpmorgan|jpm|chase bank|jamie dimon|摩根/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['jpmorgan chase'], 'stocks') },
    { test: /marathon|mpc|马拉松|炼油|refiner|crack spread/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['marathon petroleum mpc'], 'stocks') },
    { test: /exxon|xom|埃克森|美孚/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['exxonmobil xom'], 'stocks') },
    { test: /chevron|cvx|雪佛龙/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['chevron cvx'], 'stocks') },
    { test: /palantir|pltr|帕兰提尔/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['palantir pltr'], 'stocks') },
    { test: /amd|advanced micro|苏妈|超微/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['amd'], 'stocks') },
    { test: /coca.col|ko\b|可口可乐|可乐/i, resp: () => formatAdvisorResponse(KNOWLEDGE.stocks['coca cola ko'], 'stocks') },
    { test: /stock|share|equity|market|invest in|portfolio|股票|原油|石油|oil|energy/i, resp: () => {
      return "I can give you analysis on specific stocks or the broader market! Here are some I cover in depth: 🍎 Apple (AAPL), 🟢 NVIDIA (NVDA), 🚗 Tesla (TSLA), 💻 Microsoft (MSFT), 📦 Amazon (AMZN), 🔍 Google (GOOGL), 📱 Meta (META), 🏦 JPMorgan (JPM), 🏭 TSMC (TSM), 💰 Berkshire (BRK), 🥇 Gold, ⛽ Marathon Petroleum (MPC), 🛢️ ExxonMobil (XOM), 🛢️ Chevron (CVX), 🔮 Palantir (PLTR), 💻 AMD, 🥤 Coca-Cola (KO), or 📊 S&P 500. Just ask about any of these — or a general investing topic like 'how to start' or 'risk management'. What interests you?";
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
    'aapl': 'stocks', 'nvda': 'stocks', 'tsla': 'stocks', 'msft': 'stocks', 'amzn': 'stocks',
    'googl': 'stocks', 'meta': 'stocks', 'jpm': 'stocks', 'tsm': 'stocks',
    'apple': 'stocks', 'nvidia': 'stocks', 'tesla': 'stocks', 'microsoft': 'stocks',
    'amazon': 'stocks', 'google': 'stocks', 'facebook': 'stocks', 'berkshire': 'stocks',
    'gold': 'stocks', 'xau': 'stocks', 'semiconductor': 'stocks',
    'mpc': 'stocks', 'marathon': 'stocks', 'xom': 'stocks', 'exxon': 'stocks',
    'cvx': 'stocks', 'chevron': 'stocks', 'pltr': 'stocks', 'palantir': 'stocks',
    'amd': 'stocks', 'ko': 'stocks', 'coca': 'stocks',
    // Chinese keywords
    '苹果': 'stocks', '英伟达': 'stocks', '特斯拉': 'stocks', '微软': 'stocks',
    '亚马逊': 'stocks', '谷歌': 'stocks', '脸书': 'stocks', '巴菲特': 'stocks',
    '黄金': 'stocks', '台积电': 'stocks', '摩根': 'stocks',
    '马拉松': 'stocks', '炼油': 'stocks', '埃克森': 'stocks', '雪佛龙': 'stocks',
    '原油': 'stocks', '石油': 'stocks', '股票': 'stocks',
    '可乐': 'stocks', '超微': 'stocks',
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
        platform: "I can tell you about BroadFSC's services, account setup, or fees. What specifically interests you?",
        stocks: "I cover detailed analysis on major stocks: Apple, NVIDIA, Tesla, Microsoft, Amazon, Google, Meta, JPMorgan, TSMC, Berkshire, Marathon Petroleum, ExxonMobil, Chevron, Palantir, AMD, Coca-Cola, Gold, and the S&P 500. Which stock or market are you interested in? You can ask in English or Chinese (中文也可以问)."
      };
      return catResponses[cat] || "Tell me more about what you're looking for and I'll give you my best take.";
    }
  }

  // 4. Smart fallback with personality (v4: warmer)
  const fallbacks = {
    alex: [
      `Hmm, that's an interesting one — let me be honest, it's not something I have a deep take on right now. But I'd rather be straight with you than make something up. What I DO know well: charts, setups, risk management, and market mechanics. Hit me with something more specific and I'll give you a real, actionable answer. I genuinely want to help.`,
      `I'm not going to pretend I know everything about that — that wouldn't be fair to you. What I CAN help with: technical setups, reading charts, finding entries and exits. The more specific your question, the better I can serve you. What are you really trying to figure out?`,
      `That's a bit outside my core expertise, but let's not let that stop us. What's the actual question behind the question? Are you trying to make a trading decision, understand a concept, or evaluate a risk? Give me the specifics and I'll do my best to give you something useful.`
    ],
    sarah: [
      `I really want to help you with this, but I need a bit more context to give you something valuable. Are you asking about risk management? Position sizing? Or something else entirely? The more you tell me about your situation, the more useful my advice can be. I'm here for you.`,
      `That's a bit too vague for me to give you a solid answer you can trust. Tell me about your situation — what are you trading, what's your account size, what's your risk tolerance? Once I understand where you're coming from, I can give you advice that actually fits YOUR needs, not generic stuff.`
    ],
    mike: [
      `I could speculate, but I'd rather give you something you can actually use. What's the real question behind what you're asking? Are you looking at a specific market, trying to understand a macro event, or evaluating an investment? Give me the specifics and I'll connect the dots for you.`,
      `Let me offer you a framework instead: every market question ultimately comes down to supply vs demand, driven by either fundamentals or sentiment. Which angle are you coming from? Once I know that, I can give you a much more targeted and useful answer.`
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
    platform: '🏦 BroadFSC',
    stocks: '📈 Stocks & Markets'
  };
  return `${prefix} ${answer}\n\n_${catLabels[category] || ''} | ${advisor.name}_`;
}

// ── Chat UI ──
function switchAdvisor(id) {
  if (currentAdvisor === id) return;  // Already on this advisor

  // Save current chat body HTML to history before switching
  const body = document.getElementById('chatBody');
  if (body) {
    chatHistories[currentAdvisor] = body.innerHTML;
  }

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

  // Restore this advisor's chat history (or show greeting if empty)
  if (body) {
    if (chatHistories[id] && chatHistories[id].trim()) {
      body.innerHTML = chatHistories[id];
    } else {
      body.innerHTML = '';
      const div = document.createElement('div');
      div.className = 'chat-msg bot';
      div.innerHTML = a.greeting;
      body.appendChild(div);
    }
    body.scrollTop = 0;
  }
}

function sendChat() {
  if (isSending) return;  // Prevent duplicate sends
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  isSending = true;  // Lock

  // Add user message
  addUserMessage(text);
  chatHistories[currentAdvisor].push({ role: 'user', text });  // Use per-advisor history
  input.value = '';

  // Typing indicator
  showTyping();

  // AI response with delay for realism
  const delay = 600 + Math.random() * 800;
  setTimeout(() => {
    removeTyping();
    const response = getAIResponse(text);
    addBotMessage(response);
    chatHistories[currentAdvisor].push({ role: 'bot', text: response });  // Use per-advisor history
    isSending = false;  // Unlock
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
    id: 1, title: "S&P 500 Weekly Outlook: Record Highs & Fed Crossroads",
    type: "weekly", typeLabel: "Weekly Analysis",
    date: "Apr 20, 2026", readTime: "8 min",
    summary: "S&P 500 notches 12th record close of 2026 as Middle East ceasefire hopes lift sentiment — but Fed policy remains the wildcard.",
    content: `<h3>Market Context</h3>
<p>The S&P 500 continues its relentless march higher in 2026, logging its 12th all-time high close of the year. The benchmark index has returned approximately 5% in April alone, driven by easing geopolitical tensions (Middle East ceasefire progress) and resilient corporate earnings. However, the Fed's next move remains the key variable that could either extend the rally or trigger a sharp pullback.</p>

<h3>Key Levels</h3>
<ul>
<li><strong>Resistance:</strong> 6,100 (current ATH zone), 6,200 (psychological round number)</li>
<li><strong>Support:</strong> 5,850 (20 EMA), 5,700 (50 SMA), 5,520 (prior breakout level)</li>
<li><strong>Neutral Zone:</strong> 5,700 - 5,900 (range-bound if momentum fades)</li>
</ul>

<h3>What to Watch This Week</h3>
<p><strong>1. FOMC Meeting (April 29-30):</strong> The market is pricing in a hold, but forward guidance is critical. Any shift toward a June cut timeline would be strongly bullish. Conversely, "higher for longer" language could trigger a 3-5% pullback.</p>
<p><strong>2. Earnings Season Peak:</strong> Mega-cap tech reports this week. AI capex guidance remains the dominant narrative. Any deceleration in data center spending could hit the sector hard.</p>
<p><strong>3. Geopolitical Developments:</strong> Middle East ceasefire negotiations continue. Any breakdown would reverse risk-on sentiment quickly.</p>

<h3>Strategy</h3>
<p><strong>Bullish scenario:</strong> If price holds above 5,850 (20 EMA) with volume, look for a push toward 6,200. Buy the pullback to 20 EMA with a stop below 5,700.</p>
<p><strong>Bearish scenario:</strong> If 5,700 (50 SMA) fails, expect a move to 5,520. Reduce long exposure and wait for a base to form before re-entering.</p>

<h3>Risk Management</h3>
<p>Given FOMC event risk next week, reduce position sizes by 30%. Ensure all stops are in place. Consider QQQ put spreads (2-3% OTM, 30 DTE) as portfolio insurance heading into the meeting.</p>`
  },
  {
    id: 2, title: "EUR/USD: ECB vs Fed Divergence at a Turning Point",
    type: "daily", typeLabel: "Daily Brief",
    date: "Apr 20, 2026", readTime: "5 min",
    summary: "ECB cutting while Fed holds firm — the divergence trade is approaching a critical juncture.",
    content: `<h3>Setup Overview</h3>
<p>EUR/USD has been ranging between 1.0750-1.0900 for the past three weeks. The ECB has already delivered two rate cuts in 2026 and signals more are coming, while the Fed remains firmly on hold with inflation still above target. This policy divergence should eventually push EUR/USD lower — but timing is everything.</p>

<h3>Key Levels</h3>
<ul>
<li><strong>Resistance:</strong> 1.0900 (triple top zone), 1.0950 (psychological), 1.1020 (200-day MA)</li>
<li><strong>Support:</strong> 1.0750 (range floor), 1.0680 (prior lows), 1.0600 (measured move)</li>
</ul>

<h3>The Trade</h3>
<p><strong>Entry:</strong> Sell on a rejection at 1.0900 (if we get another test) or on a break below 1.0750.</p>
<p><strong>Stop:</strong> Above 1.0960 (60 pips risk from 1.0900 entry)</p>
<p><strong>Target:</strong> 1.0680 initially (220 pips), then 1.0600 (300 pips)</p>
<p><strong>R:R:</strong> 1:3.7 to first target — excellent risk/reward</p>

<h3>Catalysts</h3>
<p>ECB meeting in 10 days. If they signal a third cut, that's our trigger. Also watch US NFP this Friday — a strong number supports the "Fed holds higher" narrative and weakens EUR. Geopolitical easing (Middle East ceasefire) could strengthen USD as risk appetite improves.</p>

<h3>Risk</h3>
<p>If the Fed surprises with a dovish pivot at the April 29-30 FOMC, EUR/USD could break above 1.0960 and invalidate this setup. Keep stops tight above that level. Also watch for any escalation in geopolitical tensions that could trigger safe-haven EUR flows.</p>`
  },
  {
    id: 3, title: "Gold: $4,800+ and Counting — The Great De-Dollarization Trade",
    type: "special", typeLabel: "Special Report",
    date: "Apr 20, 2026", readTime: "12 min",
    summary: "Gold doubles in 18 months as central bank buying, de-dollarization, and geopolitical risk fuel an unprecedented rally.",
    content: `<h3>The Big Picture</h3>
<p>Gold has shattered every forecast, surging past $4,800/oz — more than doubling from its 2024 lows near $2,000. This isn't a speculative bubble. It's a structural re-pricing driven by the most powerful force in global finance: the gradual shift away from US dollar hegemony.</p>

<h3>Driver #1: Central Bank De-Dollarization</h3>
<p>Central banks bought over 1,200 tonnes of gold in 2025, a new all-time record. China's PBOC has been buying for 24+ consecutive months. But it's not just China — India, Turkey, Poland, and dozens of emerging market central banks are all adding gold at record pace. This isn't speculative — it's a deliberate strategic shift away from USD reserves. The message is clear: trust in the US dollar as the sole reserve asset is eroding.</p>

<h3>Driver #2: Geopolitical Risk Premium</h3>
<p>Middle East ceasefire negotiations, ongoing Russia-Ukraine tensions, and trade fragmentation between US-China blocs have added a persistent risk premium. Every time a new geopolitical shock hits, gold rallies $50-100 in days. The "new normal" of geopolitical instability has permanently raised gold's floor.</p>

<h3>Driver #3: Fiscal Deficits & Inflation Fears</h3>
<p>US fiscal deficits exceeding $2 trillion annually are raising questions about long-term debt sustainability. When the market starts pricing in "fiscal dominance" — where the Fed can't raise rates because the government can't afford the debt service — gold becomes the ultimate hedge. Real rates remain negative when you adjust for true inflation, making gold's lack of yield irrelevant.</p>

<h3>Technical Outlook</h3>
<ul>
<li><strong>Trend:</strong> Parabolic. 20, 50, 200 MAs all rising with widening spread — classic strong trend.</li>
<li><strong>Support:</strong> $4,650 (April low), $4,400 (prior resistance → support), $4,100 (50 SMA)</li>
<li><strong>Targets:</strong> $5,000 (psychological round number), $5,500 (measured move from consolidation)</li>
</ul>

<h3>How to Play It</h3>
<p><strong>Conservative:</strong> Buy the dip to $4,650 with a stop at $4,400. Target $5,000.</p>
<p><strong>Moderate:</strong> Buy current levels with a stop at $4,400. Target $5,500.</p>
<p><strong>Alternative:</strong> Gold miners (GDX, GDXJ) offer 2-3x leverage to gold. Streaming companies (WPM, FNV) offer lower-risk exposure with dividend yields.</p>

<h3>Risks</h3>
<p>A breakthrough Middle East peace deal could trigger a 5-8% pullback by removing the geopolitical premium. A hawkish Fed surprise (no cuts in 2026) could also pressure gold. However, the structural de-dollarization driver is unlikely to reverse anytime soon. Use stops, but don't underestimate the structural floor under this market.</p>`
  },
  {
    id: 4, title: "The $700B AI Siege: Big Tech's Capex Supercycle",
    type: "weekly", typeLabel: "Weekly Analysis",
    date: "Apr 19, 2026", readTime: "10 min",
    summary: "Big Tech's AI capex has tripled to $650-700B in 2026 — is this the greatest investment cycle in history, or the biggest bubble?",
    content: `<h3>Why This Matters</h3>
<p>The Magnificent 7 have driven 60%+ of S&P 500 returns over the past two years, largely on AI narrative. But capex spending on AI infrastructure has reached staggering levels — Big Tech's combined AI capex is projected at $650-700 billion in 2026 alone, up from ~$200B just two years ago. This is the largest corporate investment cycle in history. The question: is this spending generating real returns, or are we witnessing the greatest capital misallocation since the 2000 telecom boom?</p>

<h3>The Capex Numbers</h3>
<ul>
<li><strong>Microsoft:</strong> FY2026 capex expected above $88B (up from $68B in FY2025). Azure AI infrastructure is the primary driver.</li>
<li><strong>Amazon:</strong> Capex surging past $100B, driven by AWS AI chip investment (Trainium/Ultra) and data center expansion.</li>
<li><strong>Google/Alphabet:</strong> AI capex approaching $75B. Custom TPU chips + cloud infrastructure buildout.</li>
<li><strong>Meta:</strong> Guided "significantly higher" than $70B (2025 budget). AI-powered ad targeting + open-source Llama strategy.</li>
<li><strong>NVIDIA:</strong> The picks-and-shovels play. Data center revenue still growing 100%+ YoY — but any deceleration could trigger a 15%+ selloff.</li>
</ul>

<h3>The Bull Case</h3>
<p>AI is proving transformative. Enterprise adoption is accelerating faster than cloud adoption did. Revenue from AI products (Copilot, AWS AI, Google Cloud AI) is growing 50-80% YoY. Current spending levels are sustainable given the revenue trajectory. We're still in innings 3-4 of the AI revolution, and the market opportunity could reach $4-5 trillion by 2030.</p>

<h3>The Bear Case</h3>
<p>$700B annual capex with limited proven ROI. Most AI features are being given away for free or at minimal cost. Enterprise AI revenue, while growing, is nowhere near justifying the investment. When does the math need to work? If revenue doesn't meaningfully accelerate in H2 2026, the narrative cracks. The parallels to 1999-2000 telecom capex (where companies spent $1T+ on fiber that went unused) are uncomfortable.</p>

<h3>What to Watch</h3>
<p><strong>Key earnings this quarter:</strong> NVIDIA data center revenue growth rate, Microsoft Azure AI revenue disclosure, AWS AI services growth, Meta's AI ad revenue lift. If ANY major player signals capex slowdown → sector-wide selloff of 10-15%.</p>

<h3>How to Position</h3>
<p><strong>Core holding:</strong> NVIDIA remains the safest AI play — everyone buys from them regardless. Use 50 SMA as your guide.</p>
<p><strong>Pairs trade:</strong> Long NVIDIA / Short unprofitable AI infrastructure plays. This captures the capex boom while hedging the bubble risk.</p>
<p><strong>Hedging:</strong> QQQ put spreads (3% OTM, 45 DTE) as portfolio insurance. Cost: ~1.5% of portfolio value.</p>`
  },
  {
    id: 5, title: "Bitcoin at $75K: Post-Halving Reality Check",
    type: "special", typeLabel: "Special Report",
    date: "Apr 18, 2026", readTime: "10 min",
    summary: "BTC trades at ~$75K — below its 2024 peak. Is the halving cycle broken, or is this the accumulation zone?",
    content: `<h3>Current State</h3>
<p>Bitcoin trades around $74,800 — roughly 12% below its November 2024 all-time high near $108K. For the first time in Bitcoin's history, the post-halving cycle has not delivered new highs within 12 months. This has sparked a fierce debate: is the halving cycle broken, or are we simply in an extended consolidation before the next leg up?</p>

<h3>Historical Comparison</h3>
<table style="width:100%;border-collapse:collapse;margin:12px 0">
<tr style="border-bottom:1px solid var(--border)"><th style="text-align:left;padding:8px;color:var(--text2)">Halving</th><th style="text-align:left;padding:8px;color:var(--text2)">Pre-Halving Peak</th><th style="text-align:left;padding:8px;color:var(--text2)">Post-Halving Peak</th><th style="text-align:left;padding:8px;color:var(--text2)">Time to Peak</th><th style="text-align:left;padding:8px;color:var(--text2)">Multiple</th></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px">2016</td><td style="padding:8px">$770</td><td style="padding:8px">$19,900</td><td style="padding:8px">~18 months</td><td style="padding:8px">25x</td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px">2020</td><td style="padding:8px">$10,000</td><td style="padding:8px">$69,000</td><td style="padding:8px">~18 months</td><td style="padding:8px">7x</td></tr>
<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px">2024</td><td style="padding:8px">$73,000</td><td style="padding:8px">$108,000*</td><td style="padding:8px">~7 months</td><td style="padding:8px">1.5x</td></tr>
</table>
<p style="font-size:0.85em;color:var(--text3)">*ATH reached Nov 2024. Current price below ATH.</p>

<h3>What's Different This Cycle</h3>
<p><strong>ETF saturation:</strong> Spot Bitcoin ETFs were approved before the halving, front-running the typical demand shock. The "ETF buy" may have already been priced in, explaining the lackluster post-halving performance.</p>
<p><strong>Macro headwinds:</strong> The Fed's "higher for longer" stance has been a headwind for risk assets. Bitcoin hasn't enjoyed the rate-cut tailwind that previous cycles had.</p>
<p><strong>Diminishing returns confirmed:</strong> The multiple from pre-halving peak to post-halving peak has declined from 25x to 7x to 1.5x. The market is maturing — 10x returns are likely gone forever.</p>
<p><strong>Gold competition:</strong> Gold's parabolic rally to $4,800+ has drawn safe-haven flows that might have previously gone to Bitcoin. BTC is no longer the only "anti-fiat" trade.</p>

<h3>On-Chain Metrics</h3>
<ul>
<li><strong>Realized Price:</strong> ~$42K. Current price at 1.8x realized — historically mid-range, not overheated</li>
<li><strong>200-Week MA:</strong> ~$52K. Price above = macro bull intact</li>
<li><strong>Exchange Reserves:</strong> Still declining = long-term holders not selling</li>
<li><strong>NUPL:</strong> At 0.45 — in 'optimism' zone, well below euphoria (0.75)</li>
</ul>

<h3>Strategy</h3>
<p><strong>Long-term holders:</strong> Continue holding. On-chain metrics suggest we're mid-cycle, not at a top. The 2026-2027 cycle peak could still reach $120-150K if macro conditions improve.</p>
<p><strong>New positions:</strong> Dollar-cost average into the $65-75K zone. Stop below $52K (200-week MA). This is a reasonable risk/reward entry for a 12-18 month horizon.</p>
<p><strong>Short-term traders:</strong> Range-bound between $68-82K. Buy support, sell resistance. Keep positions small — BTC is in a no-man's-land where both bullish and bearish cases have merit.</p>
<p><strong>Risk:</strong> A global recession could push BTC below $50K. Regulatory crackdowns remain an ever-present risk. Never invest more than 5% of portfolio in BTC.</p>`
  },
  {
    id: 6, title: "Risk Management Checklist: 20 Rules That Save Accounts",
    type: "special", typeLabel: "Special Report",
    date: "Apr 16, 2026", readTime: "15 min",
    summary: "In a world of $4,800 gold and $700B AI capex, disciplined risk management matters more than ever.",
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
<p>90% of traders lose money. The 10% who survive all have one thing in common: disciplined risk management. Not better analysis. Not better signals. Just better risk control. Print this list, put it next to your screen, and follow it every single day.</p>

<h3>2026 Context</h3>
<p>Markets in 2026 are more extreme than ever: gold has doubled to $4,800+, AI capex has tripled to $700B, and Bitcoin is still finding its post-halving direction. In this environment, the temptation to "go all in" on a thesis is overwhelming. That's exactly when risk management matters most. The traders who survive this cycle won't be the ones who made the biggest calls — they'll be the ones who kept their losses small enough to stay in the game.</p>`
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
  `).join('') + `
    <div class="research-card research-cta" onclick="showRegisterModal('research_page')">
      <span class="type special">🔒 Exclusive</span>
      <h3>Unlock Personalized Stock Analysis</h3>
      <p>Get custom research reports, real-time alerts, and 1-on-1 AI advisory tailored to your portfolio. Register free to unlock.</p>
      <div class="meta"><span>📧 Email Required</span><span>Free Forever</span></div>
    </div>
  `;
}

function showResearch(id) {
  const r = RESEARCH.find(x => x.id === id);
  if (!r) return;

  const modal = document.getElementById('courseModal');
  const detail = document.getElementById('courseDetail');

  const ctaButton = isRegistered
    ? `<div style="margin-top:24px;padding:18px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:12px;text-align:center">
        <p style="color:var(--green);font-weight:600;margin-bottom:6px">✅ Full Access Unlocked</p>
        <p style="font-size:.82em;color:var(--text2)">As a registered member, you have access to all our research and personalized analysis.</p>
       </div>`
    : `<div style="margin-top:24px;padding:18px;background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.2);border-radius:12px;text-align:center">
        <p style="color:var(--blue);font-weight:600;margin-bottom:6px">📧 Want personalized analysis like this for YOUR portfolio?</p>
        <p style="font-size:.82em;color:var(--text2);margin-bottom:12px">Register free to unlock custom stock analysis, real-time alerts, and 1-on-1 AI advisory.</p>
        <button class="btn btn-p" style="font-size:.9em" onclick="closeCourseModal();showRegisterModal('research_${r.id}')">Get Free Access →</button>
       </div>`;

  detail.innerHTML = `
    <button class="close-btn" onclick="closeCourseModal()">✕</button>
    <span style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:.78em;font-weight:600;margin-bottom:12px;background:${r.type==='daily'?'rgba(6,182,212,.12)':r.type==='weekly'?'rgba(139,92,246,.12)':'rgba(245,158,11,.12)'};color:${r.type==='daily'?'var(--cyan)':r.type==='weekly'?'var(--purple)':'var(--orange)'}">${r.typeLabel}</span>
    <h2 style="font-size:1.5em;font-weight:800;margin-bottom:8px;line-height:1.3">${r.title}</h2>
    <div style="display:flex;gap:16px;font-size:.82em;color:var(--text3);margin-bottom:24px">
      <span>📅 ${r.date}</span>
      <span>⏱️ ${r.readTime} read</span>
    </div>
    <div style="font-size:.92em;line-height:1.8;color:var(--text2)">${r.content}</div>
    ${ctaButton}
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
  const sections = ['home', 'features', 'courses', 'research', 'glossary', 'tools', 'contact'];

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

  // Initial AI greeting (warmer, acknowledges returning users)
  const body = document.getElementById('chatBody');
  if (body) {
    let greeting;
    const advisor = ADVISORS[currentAdvisor];
    if (isRegistered && userName) {
      const timeGreet = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 18 ? 'Good afternoon' : 'Good evening';
      greeting = `${timeGreet}, ${userName}! 😊 Welcome back. I've been keeping an eye on the markets for you — anything you'd like to discuss today?`;
    } else {
      greeting = advisor.greeting;
    }
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.innerHTML = greeting;
    body.appendChild(div);
    // Save initial greeting to Alex's history
    chatHistories[currentAdvisor].push({ role: 'bot', text: greeting });
  }

  // Update nav CTA for registered users
  updateNavCTA();

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
  document.getElementById('registerModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'registerModal') closeRegisterModal();
  });

  // Register form: Enter key submits
  document.getElementById('regEmail')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') submitRegistration();
  });
});

// Update nav CTA based on registration status
function updateNavCTA() {
  const cta = document.querySelector('.nav-cta');
  if (!cta) return;
  if (isRegistered) {
    cta.textContent = '👤 My Account';
    cta.onclick = () => showRegisterToast(`Welcome back, ${userName || 'Member'}! 🎉 Your access is active.`);
  } else {
    cta.textContent = '🤖 Get Access';
    cta.onclick = () => showRegisterModal('nav_cta');
  }
}
