// BroadFSC Pro — Main App Logic
// Requires courses-data.js to be loaded first

// ============================================================
// KNOWLEDGE BASE (from /knowledge/ directory)
// ============================================================
const KB = {
  finance: {
    "support resistance": "Support/Resistance levels are key price zones where price repeatedly bounces. Support = floor, Resistance = ceiling. The more times price touches a level, the stronger it becomes.",
    "moving average": "Moving Averages smooth price action. MA5 < MA20 < MA60 for trend direction. When shorter MA crosses above longer MA = Golden Cross (bullish). Below = Death Cross (bearish).",
    "rsi": "RSI (Relative Strength Index) measures momentum 0-100. Above 70 = overbought (potential sell). Below 30 = oversold (potential buy). Divergence between RSI and price often signals reversals.",
    "macd": "MACD (Moving Average Convergence Divergence): When DIFF crosses above DEA = Golden Cross (buy signal). Crosses below = Death Cross (sell). Histogram shows momentum strength.",
    "bollinger bands": "Bollinger Bands: Upper band = overbought zone, Lower = oversold. When bands narrow (squeeze) = breakout coming. Price touching upper band in uptrend = normal.",
    "candlestick": "Candlestick patterns: Hammer (bullish reversal at bottom), Shooting Star (bearish at top), Doji (indecision), Engulfing (strong reversal). Best used at key S/R levels.",
    "pe ratio": "P/E Ratio = Stock Price ÷ Earnings Per Share. Low P/E = cheaper vs. peers (potentially undervalued). High P/E = growth expectations priced in. Compare within same industry.",
    "roe": "ROE (Return on Equity) = Net Income ÷ Shareholders' Equity. Warren Buffett's favorite metric. >15% consistently = excellent management. Look for sustained high ROE.",
    "cpi": "CPI (Consumer Price Index) measures inflation. High CPI → Fed may raise rates → typically bearish for stocks, bullish for USD. Watch monthly CPI releases closely.",
    "nfp": "NFP (Non-Farm Payrolls) released first Friday each month at 8:30 AM ET. Strongest US jobs report. Beat = USD up, possible rate hike expectations. Miss = USD down.",
    "gdp": "GDP (Gross Domestic Product) measures economic output. 2 consecutive quarters of negative GDP = recession. Markets often anticipate GDP trends 6 months ahead.",
    "fed": "Federal Reserve (Fed) sets US interest rates. Rate hikes = stronger USD, weaker bonds, mixed stocks. Rate cuts = weaker USD, stocks often rally. Watch FOMC meetings (8x/year).",
    "fibonacci": "Fibonacci retracements: Key levels are 23.6%, 38.2%, 50%, 61.8%, 78.6%. After a strong move, price often retraces to these levels before continuing. 61.8% = 'Golden Ratio'.",
    "head shoulders": "Head & Shoulders: Reversal pattern. Left shoulder + Head (higher) + Right shoulder. Break below neckline = bearish. Inverse H&S at bottoms = bullish reversal.",
    "double top bottom": "Double Top (M pattern) = bearish reversal at resistance. Double Bottom (W pattern) = bullish reversal at support. Both are among the most reliable patterns.",
    "risk management": "Core risk rules: 1) Never risk >1-2% per trade. 2) Always use stop-loss. 3) Reward:Risk ratio minimum 2:1. 4) Diversify across assets. 5) Never average down on losing trades.",
    "leverage": "Leverage amplifies gains AND losses. 100:1 leverage = 1% adverse move wipes your margin. Beginners: use max 10:1. Pros: 20-50:1 max. Always calculate position size FIRST.",
    "forex": "Forex market trades $6.6 trillion/day, 24/5. Major pairs: EUR/USD, GBP/USD, USD/JPY. Best times: London-NY overlap (8 AM-12 PM ET). Interest rates are the #1 driver.",
    "options": "Options: Call = right to buy, Put = right to sell. Key terms: Strike price, Expiration, Premium, Greeks (Delta, Theta, Vega). Options expire worthless if OTM at expiry.",
    "etf": "ETF (Exchange-Traded Fund) = basket of securities trading like a stock. SPY tracks S&P 500. QQQ tracks NASDAQ. Lower cost than mutual funds. Good for passive investing.",
  },
  broadfsc: {
    "what is broadfsc": "BroadFSC (Broad Investment Securities) is a globally regulated investment advisory and asset management firm. We offer professional investment services with licenses in major markets worldwide.",
    "regulated": "BroadFSC holds regulatory licenses in major financial markets globally. We operate under strict compliance standards to protect our clients.",
    "services": "BroadFSC offers: ✅ Investment Advisory ✅ Asset Management ✅ Research & Analysis ✅ Educational Resources ✅ AI-Powered Investment Tools. All available to global investors (excluding mainland China).",
    "how to start": "Getting started with BroadFSC: 1) Visit broadfsc.com 2) Complete registration 3) Verify identity (KYC) 4) Fund your account 5) Start with our educational resources. Our advisors guide you every step.",
    "fees": "BroadFSC is transparent about fees. No hidden charges. Competitive rates with full disclosure. Contact us for specific fee schedules for your investment type.",
    "contact": "Contact BroadFSC: 🌐 Website: broadfsc.com | 💬 Telegram: @BroadFSC | 🤖 AI Bot: @BroadInvestBot | This platform provides free educational resources 24/7.",
    "account types": "BroadFSC offers multiple account types for different investor profiles - from individual retail investors to institutional clients. Minimum requirements vary by account type.",
    "risk disclosure": "All investments carry risk. Past performance does not guarantee future results. BroadFSC provides risk management education and tools, but you are responsible for your investment decisions.",
  }
};

// ============================================================
// AI ADVISOR SYSTEM
// ============================================================
const ADVISORS = {
  alex: {
    name: "Alex Chen",
    role: "Technical Analysis Expert",
    avatar: "👨‍💼",
    color: "linear-gradient(135deg,#3b82f6,#10b981)",
    greeting: "Hi! I'm Alex Chen, your Technical Analysis Expert. I specialize in chart patterns, indicators, and trading strategies. What would you like to learn today?",
    expertise: ["candlestick", "technical", "chart", "indicator", "rsi", "macd", "moving average", "support", "resistance", "fibonacci", "pattern", "trend", "breakout"]
  },
  sarah: {
    name: "Sarah Kim",
    role: "Macro & Fundamentals",
    avatar: "👩‍💼",
    color: "linear-gradient(135deg,#8b5cf6,#ec4899)",
    greeting: "Hello! I'm Sarah Kim, specializing in macroeconomics and fundamental analysis. I can help you understand economic indicators, company valuations, and global market trends. What's on your mind?",
    expertise: ["fundamental", "macro", "economy", "gdp", "cpi", "nfp", "fed", "inflation", "pe ratio", "roe", "earnings", "valuation", "dividend"]
  },
  mike: {
    name: "Mike Torres",
    role: "Risk & Portfolio",
    avatar: "🧑‍💻",
    color: "linear-gradient(135deg,#f59e0b,#ef4444)",
    greeting: "Hey there! I'm Mike Torres, your Risk & Portfolio Management specialist. I help traders protect capital and build sustainable trading strategies. What risk challenge can I help you with?",
    expertise: ["risk", "portfolio", "position size", "stop loss", "leverage", "diversification", "drawdown", "risk management", "hedge", "allocation"]
  }
};

let currentAdvisor = 'alex';
let chatHistory = [];
let chatMemory = {}; // remembers user preferences
let isTyping = false;

function switchAdvisor(id) {
  currentAdvisor = id;
  // Update chips
  document.querySelectorAll('.advisor-chip').forEach(c => c.classList.remove('active'));
  const chip = document.getElementById('chip' + id.charAt(0).toUpperCase() + id.slice(1));
  if (chip) chip.classList.add('active');
  // Update chat header
  const adv = ADVISORS[id];
  const header = document.querySelector('.chat-header');
  if (header) {
    header.querySelector('.chat-avatar').style.background = adv.color;
    header.querySelector('.chat-avatar').textContent = adv.avatar;
    header.querySelector('h4').textContent = adv.name;
    header.querySelector('span').textContent = adv.role + ' · Online';
  }
  // Add advisor intro message
  addChatMessage(adv.greeting, 'bot');
}

function getAIResponse(userMsg) {
  const msg = userMsg.toLowerCase();
  const adv = ADVISORS[currentAdvisor];

  // Check BroadFSC KB first
  for (const [key, val] of Object.entries(KB.broadfsc)) {
    if (msg.includes(key) || key.split(' ').some(w => msg.includes(w))) {
      return val;
    }
  }

  // Check finance KB
  for (const [key, val] of Object.entries(KB.finance)) {
    if (msg.includes(key) || key.split(' ').some(w => w.length > 3 && msg.includes(w))) {
      return val;
    }
  }

  // Course recommendations
  if (msg.includes('beginner') || msg.includes('start') || msg.includes('new to') || msg.includes('learn')) {
    return "Great that you want to learn! I recommend starting with these courses:\n\n📈 **Stock Market Fundamentals** — The essential foundation\n💱 **Forex Trading 101** — Understand the world's largest market\n🕯️ **Candlestick Patterns** — Read price action like a pro\n\nClick the **Academy** section above to access all 30 courses for free!";
  }

  if (msg.includes('course') || msg.includes('lesson') || msg.includes('study')) {
    return "We have 30+ structured courses covering:\n\n🟢 **Beginner**: Stock basics, Forex 101, Candlesticks, Technical Analysis\n🟡 **Intermediate**: Options, Crypto, ETFs, Macro Economics\n🔴 **Advanced**: Algorithmic Trading, Portfolio Management, Derivatives\n\nAll courses are 100% free! Head to the Academy section.";
  }

  if (msg.includes('hello') || msg.includes('hi') || msg.includes('hey') || msg === 'sup') {
    const greetings = ["Hey! Great to have you here. What investment topic are you curious about today?", "Hello! Ready to learn something new about markets? Ask me anything!", "Hi there! I'm here to help you become a better investor. What's on your mind?"];
    return greetings[Math.floor(Math.random() * greetings.length)];
  }

  if (msg.includes('thank')) {
    return "You're welcome! Remember, consistent learning is the key to trading success. Any other questions? 🎯";
  }

  if (msg.includes('profit') || msg.includes('make money') || msg.includes('rich')) {
    return "Consistent profitability in trading comes from:\n\n1. **Education** — Know your instruments deeply\n2. **Risk Management** — Protect your capital first\n3. **Psychology** — Control emotions, stick to your plan\n4. **Strategy** — Backtested, rules-based approach\n5. **Patience** — Let setups come to you\n\nThere are no shortcuts. But with the right education and discipline, it's absolutely achievable. Start with our free courses! 📚";
  }

  if (msg.includes('crypto') || msg.includes('bitcoin') || msg.includes('btc') || msg.includes('eth')) {
    return "Crypto markets: Bitcoin (BTC) is digital gold — store of value, limited supply (21M). Ethereum (ETH) is programmable blockchain. Key differences from stocks:\n\n• 24/7 trading (no market close)\n• Much higher volatility\n• No fundamentals like P/E ratio\n• Technical analysis works well\n• Regulatory uncertainty adds risk\n\nCheck our Crypto Investing course in the Academy section for a full breakdown!";
  }

  if (msg.includes('stock') && (msg.includes('buy') || msg.includes('pick') || msg.includes('recommend'))) {
    return "I'm not licensed to give specific stock picks — that's personalized financial advice. But here's what professionals look for:\n\n✅ Strong revenue growth (>15% YoY)\n✅ Expanding margins\n✅ Low debt-to-equity\n✅ Competitive moat\n✅ Reasonable valuation (P/E vs sector)\n\nFor personalized investment advice, speak with a BroadFSC advisor at broadfsc.com 🌐";
  }

  // Expertise-based fallback
  const expertTopics = adv.expertise.join(', ');
  const responses = [
    `That's a great question! As ${adv.name}, my expertise is in ${expertTopics}. Could you be more specific about what you'd like to know? I'm here to help!`,
    `Interesting topic! I can help you with ${expertTopics} and much more. What specific aspect are you most curious about?`,
    `Let me help you with that. My specialty as ${adv.name} covers ${expertTopics}. For the most accurate guidance, could you clarify what you're looking to understand?`
  ];
  return responses[Math.floor(Math.random() * responses.length)];
}

function addChatMessage(text, type, isLoading = false) {
  const body = document.getElementById('chatBody');
  if (!body) return;
  const div = document.createElement('div');
  div.className = 'chat-msg ' + type;
  if (isLoading) {
    div.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    div.id = 'typingIndicator';
  } else {
    // Convert markdown-like formatting
    const formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    div.innerHTML = formatted;
  }
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
  return div;
}

function sendChat() {
  if (isTyping) return;
  const input = document.getElementById('chatInput');
  if (!input) return;
  const msg = input.value.trim();
  if (!msg) return;

  addChatMessage(msg, 'user');
  input.value = '';
  chatHistory.push({ role: 'user', content: msg });

  isTyping = true;
  const typingEl = addChatMessage('', 'bot', true);

  setTimeout(() => {
    if (typingEl) typingEl.remove();
    const response = getAIResponse(msg);
    addChatMessage(response, 'bot');
    chatHistory.push({ role: 'bot', content: response });
    isTyping = false;
  }, 800 + Math.random() * 600);
}

// ============================================================
// CANVAS ANIMATION (Hero Background)
// ============================================================
function initCanvas() {
  const canvas = document.getElementById('heroCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() {
    W = canvas.width = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.4;
      this.vy = -Math.random() * 0.6 - 0.2;
      this.alpha = Math.random() * 0.5 + 0.1;
      this.size = Math.random() * 2 + 0.5;
      this.color = Math.random() > 0.5 ? '#3b82f6' : '#10b981';
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.alpha -= 0.002;
      if (this.y < 0 || this.alpha <= 0) this.reset();
    }
    draw() {
      ctx.save();
      ctx.globalAlpha = this.alpha;
      ctx.fillStyle = this.color;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  for (let i = 0; i < 80; i++) particles.push(new Particle());

  function animate() {
    ctx.clearRect(0, 0, W, H);
    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 100) {
          ctx.save();
          ctx.globalAlpha = 0.05 * (1 - dist / 100);
          ctx.strokeStyle = '#3b82f6';
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
          ctx.restore();
        }
      }
    }
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animate);
  }
  animate();
}

// ============================================================
// COURSES SYSTEM
// ============================================================
let currentCourseCategory = 'all';

function renderCourses(category = 'all') {
  currentCourseCategory = category;
  const grid = document.getElementById('coursesGrid');
  if (!grid || typeof COURSES === 'undefined') return;

  // Update tabs
  document.querySelectorAll('.courses-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.cat === category);
  });

  const filtered = category === 'all' ? COURSES : COURSES.filter(c => c.level === category);
  const tagClass = { beginner: 'beg', intermediate: 'int', advanced: 'adv' };
  const tagLabel = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' };

  grid.innerHTML = filtered.map(c => `
    <div class="course-card" onclick="openCourse(${c.id})">
      <div class="tag ${tagClass[c.level] || 'beg'}">${tagLabel[c.level] || c.level}</div>
      <h3>${c.icon} ${c.title}</h3>
      <p>${c.desc}</p>
      <div class="course-meta">
        <span>⏱️ ${c.duration}</span>
        <span>📚 ${c.modules || c.lessons.length} Lessons</span>
        <span>✅ Free</span>
      </div>
    </div>
  `).join('');
}

function openCourse(id) {
  if (typeof COURSES === 'undefined') return;
  const course = COURSES.find(c => c.id === id);
  if (!course) return;
  const modal = document.getElementById('courseModal');
  const detail = document.getElementById('courseDetail');
  if (!modal || !detail) return;

  const tagClass = { beginner: 'beg', intermediate: 'int', advanced: 'adv' };
  const tagLabel = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' };

  const lessonsHTML = course.lessons.map((l, i) => `
    <li class="module-item" onclick="toggleLesson(this, ${i})">
      <div class="num">${i + 1}</div>
      <div class="info">
        <h4>${l.t}</h4>
        <p>Click to expand lesson content</p>
      </div>
      <span class="dur">⏱️ ${l.d}</span>
      <span class="expand-icon">▼</span>
    </li>
    <div class="module-content" id="lesson-${i}">${l.content}</div>
  `).join('');

  const quizHTML = course.quiz ? `
    <div class="quiz-section">
      <h3>🎯 Knowledge Check</h3>
      ${course.quiz.map((q, qi) => `
        <div class="quiz-q">
          <h4>Q${qi + 1}: ${q.q}</h4>
          <div class="quiz-opts">
            ${q.opts.map((o, oi) => `
              <div class="quiz-opt" onclick="checkAnswer(this, ${oi === q.ans})">${o}</div>
            `).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  ` : '';

  detail.innerHTML = `
    <button class="close-btn" onclick="closeCourse()">✕</button>
    <h2>${course.icon} ${course.title}</h2>
    <span class="tag ${tagClass[course.level] || 'beg'}">${tagLabel[course.level] || course.level} · ${course.duration}</span>
    <p style="color:var(--text2);font-size:.9em;margin-bottom:20px">${course.desc}</p>
    <h3 style="margin-bottom:12px;font-size:1em">📚 Lessons</h3>
    <ul class="module-list">${lessonsHTML}</ul>
    ${quizHTML}
  `;

  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function toggleLesson(el, idx) {
  el.classList.toggle('expanded');
  const content = document.getElementById('lesson-' + idx);
  if (content) content.classList.toggle('show');
}

function checkAnswer(el, isCorrect) {
  const parent = el.parentElement;
  parent.querySelectorAll('.quiz-opt').forEach(o => {
    o.style.pointerEvents = 'none';
  });
  el.classList.add(isCorrect ? 'correct' : 'wrong');
  if (!isCorrect) {
    // Highlight correct answer
    const opts = parent.querySelectorAll('.quiz-opt');
    // Can't easily find correct here without more data, just show wrong
  }
}

function closeCourse() {
  document.getElementById('courseModal').classList.remove('open');
  document.body.style.overflow = '';
}

// ============================================================
// GLOSSARY SYSTEM
// ============================================================
const GLOSSARY_TERMS = [
  {term:"Ask Price",def:"The lowest price a seller is willing to accept for an asset.",cat:"Trading"},
  {term:"Bear Market",def:"A market decline of 20%+ from recent highs, lasting at least 2 months.",cat:"Market"},
  {term:"Bid Price",def:"The highest price a buyer is willing to pay for an asset.",cat:"Trading"},
  {term:"Bollinger Bands",def:"Volatility bands placed above and below a moving average. Squeeze = incoming breakout.",cat:"Technical"},
  {term:"Bull Market",def:"A sustained market rise of 20%+ from recent lows with strong investor confidence.",cat:"Market"},
  {term:"Candlestick",def:"A price chart type showing open, high, low, and close prices for each period.",cat:"Technical"},
  {term:"Circuit Breaker",def:"Automatic halt in trading when market drops 7%, 13%, or 20% in a day.",cat:"Market"},
  {term:"CPI",def:"Consumer Price Index — measures average price changes of goods/services. Key inflation gauge.",cat:"Macro"},
  {term:"Day Trading",def:"Buying and selling financial instruments within the same trading day.",cat:"Strategy"},
  {term:"Diversification",def:"Spreading investments across different assets to reduce risk.",cat:"Portfolio"},
  {term:"Dividend",def:"A portion of company profits paid to shareholders, typically quarterly.",cat:"Stocks"},
  {term:"Doji",def:"Candlestick with same open and close price, indicating market indecision.",cat:"Technical"},
  {term:"EPS",def:"Earnings Per Share = Net Income ÷ Shares Outstanding. Higher = more profitable.",cat:"Fundamental"},
  {term:"ETF",def:"Exchange-Traded Fund — basket of securities that trades like a stock. Low cost, diversified.",cat:"Instrument"},
  {term:"Fed Funds Rate",def:"Interest rate at which US banks lend overnight. #1 driver of financial markets.",cat:"Macro"},
  {term:"Fibonacci Retracement",def:"Key retracement levels (23.6%, 38.2%, 61.8%) traders use to identify potential support/resistance.",cat:"Technical"},
  {term:"Forex",def:"Foreign Exchange market — $6.6 trillion/day. World's largest financial market.",cat:"Market"},
  {term:"GDP",def:"Gross Domestic Product — total value of goods/services produced. Key economic health indicator.",cat:"Macro"},
  {term:"Golden Cross",def:"Short-term MA crosses above long-term MA. Bullish signal (opposite = Death Cross).",cat:"Technical"},
  {term:"Hedge",def:"An investment that reduces the risk of adverse price movements in another asset.",cat:"Strategy"},
  {term:"Head & Shoulders",def:"Chart reversal pattern: left shoulder + head + right shoulder. Signals trend reversal.",cat:"Technical"},
  {term:"IPO",def:"Initial Public Offering — first time a company sells shares to the public.",cat:"Stocks"},
  {term:"Leverage",def:"Using borrowed funds to amplify returns (and losses). 100:1 = controlling $100k with $1k.",cat:"Trading"},
  {term:"Limit Order",def:"Order to buy/sell at a specific price or better. Controls price, not execution.",cat:"Trading"},
  {term:"Liquidity",def:"How quickly an asset can be bought/sold without impacting its price.",cat:"Market"},
  {term:"MACD",def:"Moving Average Convergence Divergence. Golden Cross = buy signal, Death Cross = sell.",cat:"Technical"},
  {term:"Margin",def:"Deposit required to open a leveraged position. Margin call = equity too low.",cat:"Trading"},
  {term:"Market Cap",def:"Total market value = Share Price × Total Shares. Large cap >$10B, Small cap <$2B.",cat:"Fundamental"},
  {term:"Market Order",def:"Order executed immediately at best available price. Fast but no price control.",cat:"Trading"},
  {term:"Moving Average",def:"Average price over a period. MA5, MA20, MA50, MA200 are most watched.",cat:"Technical"},
  {term:"NFP",def:"Non-Farm Payrolls — US jobs data released first Friday of month. Massive market mover.",cat:"Macro"},
  {term:"Options",def:"Contracts giving right (not obligation) to buy/sell at set price before expiry.",cat:"Instrument"},
  {term:"P/E Ratio",def:"Price-to-Earnings = Stock Price ÷ EPS. Compare within sector. High = expensive or high growth.",cat:"Fundamental"},
  {term:"Pip",def:"Smallest price move in forex. EUR/USD: 0.0001. JPY pairs: 0.01.",cat:"Forex"},
  {term:"Position Sizing",def:"Calculating how many shares/contracts to trade based on account risk tolerance.",cat:"Risk"},
  {term:"Resistance",def:"Price level where selling pressure historically overcomes buying. Ceiling for price.",cat:"Technical"},
  {term:"Risk/Reward Ratio",def:"Potential profit vs. potential loss. 2:1 = minimum standard. 3:1 = excellent.",cat:"Risk"},
  {term:"ROE",def:"Return on Equity = Net Income ÷ Equity. Buffett's favorite. >15% = excellent.",cat:"Fundamental"},
  {term:"RSI",def:"Relative Strength Index — momentum oscillator 0-100. >70 overbought, <30 oversold.",cat:"Technical"},
  {term:"Short Selling",def:"Selling borrowed shares hoping to buy back cheaper. Profit from price declines.",cat:"Strategy"},
  {term:"Spread",def:"Difference between bid and ask price. Narrow = liquid market. Wide = illiquid.",cat:"Trading"},
  {term:"Stop-Loss",def:"Order that automatically sells when price reaches a set level. Essential risk management.",cat:"Risk"},
  {term:"Support",def:"Price level where buying historically overcomes selling. Floor for price.",cat:"Technical"},
  {term:"Swing Trading",def:"Holding positions days to weeks, targeting intermediate price swings.",cat:"Strategy"},
  {term:"Trailing Stop",def:"Stop-loss that moves up with price in an uptrend, locking in profits.",cat:"Risk"},
  {term:"Volatility",def:"Measure of price fluctuation. High vol = large moves. VIX = 'Fear Index' for S&P 500.",cat:"Market"},
  {term:"Volume",def:"Number of shares/contracts traded. High volume confirms price moves.",cat:"Technical"},
  {term:"Yield",def:"Income return on investment. Bond yield = annual interest ÷ bond price.",cat:"Fundamental"},
];

let glossaryFilter = '';

function renderGlossary(filter = '') {
  glossaryFilter = filter.toLowerCase();
  const grid = document.getElementById('glossaryGrid');
  if (!grid) return;

  const filtered = GLOSSARY_TERMS.filter(t =>
    t.term.toLowerCase().includes(glossaryFilter) ||
    t.def.toLowerCase().includes(glossaryFilter) ||
    t.cat.toLowerCase().includes(glossaryFilter)
  );

  grid.innerHTML = filtered.map(t => `
    <div class="glossary-item">
      <div class="term">${t.term}</div>
      <div class="def">${t.def}</div>
      <span class="cat">${t.cat}</span>
    </div>
  `).join('');
}

// ============================================================
// RESEARCH SECTION
// ============================================================
const RESEARCH_DATA = [
  {type:'daily',title:'Market Pulse: S&P 500 Key Levels This Week',preview:'Technical analysis reveals critical support at 5,000. Watch Fed minutes Wednesday for direction clue.',date:'Apr 20, 2026',read:'3 min'},
  {type:'daily',title:'USD Strength: DXY Analysis & Currency Pairs Outlook',preview:'Dollar maintains momentum above 104. EUR/USD testing critical 1.07 support. JPY intervention risk.',date:'Apr 19, 2026',read:'4 min'},
  {type:'weekly',title:'Weekly Sector Rotation Report: Where Smart Money Flows',preview:'Technology outperforming YTD. Healthcare emerging as defensive rotation target. Energy pulling back.',date:'Apr 18, 2026',read:'8 min'},
  {type:'daily',title:'Crypto Market Structure: BTC Consolidation Analysis',preview:'Bitcoin forming potential ascending triangle. $65K resistance key. ETF flows remain positive.',date:'Apr 18, 2026',read:'3 min'},
  {type:'special',title:'Special Report: 2026 Rate Cut Timeline & Market Impact',preview:'Analyzing 3 scenarios: 2 cuts, 1 cut, no cut in 2026. Portfolio implications for each path.',date:'Apr 17, 2026',read:'12 min'},
  {type:'weekly',title:'Emerging Markets Weekly: Opportunities in Volatility',preview:'EM equities showing relative strength. India, Brazil, Mexico in focus. Currency risk management.',date:'Apr 16, 2026',read:'7 min'},
  {type:'daily',title:'Gold & Commodities: Inflation Trade Update',preview:'Gold near ATH on safe-haven demand. Oil inventory data key. Copper signals global growth.',date:'Apr 15, 2026',read:'4 min'},
  {type:'special',title:'AI Sector Deep Dive: Valuation vs. Growth Analysis',preview:'Separating AI hype from fundamentals. Revenue, margins, and competitive moats across 15 companies.',date:'Apr 14, 2026',read:'15 min'},
];

function renderResearch() {
  const grid = document.getElementById('researchGrid');
  if (!grid) return;
  grid.innerHTML = RESEARCH_DATA.map(r => `
    <div class="research-card" onclick="showResearchAlert()">
      <span class="type ${r.type}">${r.type.charAt(0).toUpperCase()+r.type.slice(1)}</span>
      <h3>${r.title}</h3>
      <p>${r.preview}</p>
      <div class="meta"><span>${r.date}</span><span>📖 ${r.read} read</span></div>
    </div>
  `).join('');
}

function showResearchAlert() {
  // Instead of alert, add a chat message
  addChatMessage("I'd like to read the full research report!", 'user');
  setTimeout(() => {
    addChatMessage("Great choice! Full research reports are available to BroadFSC account holders. Visit broadfsc.com to create your free account and get access to all research, tools, and personalized advisory services. 📊", 'bot');
  }, 600);
  // Scroll to hero / chat
  document.getElementById('home').scrollIntoView({behavior:'smooth'});
}

// ============================================================
// CALCULATORS
// ============================================================
const CALC_TEMPLATES = {
  position: {
    title: '📐 Position Size Calculator',
    fields: `
      <div class="calc-field"><label>Account Balance ($)</label><input type="number" id="c_balance" value="10000" placeholder="10000"></div>
      <div class="calc-field"><label>Risk Per Trade (%)</label><input type="number" id="c_risk" value="1" step="0.1" placeholder="1"></div>
      <div class="calc-field"><label>Entry Price ($)</label><input type="number" id="c_entry" value="100" placeholder="100"></div>
      <div class="calc-field"><label>Stop-Loss Price ($)</label><input type="number" id="c_stop" value="97" placeholder="97"></div>
      <button class="btn btn-p" style="width:100%;justify-content:center" onclick="calcPosition()">Calculate Position Size</button>
      <div class="calc-result" id="c_result" style="display:none"></div>
    `,
    calc: null
  },
  pnl: {
    title: '💰 Profit/Loss Calculator',
    fields: `
      <div class="calc-field"><label>Entry Price ($)</label><input type="number" id="c_entry" value="100" placeholder="100"></div>
      <div class="calc-field"><label>Exit Price ($)</label><input type="number" id="c_exit" value="115" placeholder="115"></div>
      <div class="calc-field"><label>Position Size (Units)</label><input type="number" id="c_size" value="100" placeholder="100"></div>
      <div class="calc-field"><label>Direction</label><select id="c_dir"><option value="long">Long (Buy)</option><option value="short">Short (Sell)</option></select></div>
      <button class="btn btn-p" style="width:100%;justify-content:center" onclick="calcPnL()">Calculate P&L</button>
      <div class="calc-result" id="c_result" style="display:none"></div>
    `
  },
  margin: {
    title: '🏦 Margin Calculator',
    fields: `
      <div class="calc-field"><label>Position Size ($)</label><input type="number" id="c_pos" value="100000" placeholder="100000"></div>
      <div class="calc-field"><label>Leverage</label><select id="c_lev">
        <option value="10">10:1</option><option value="20">20:1</option><option value="50">50:1</option><option value="100" selected>100:1</option>
      </select></div>
      <button class="btn btn-p" style="width:100%;justify-content:center" onclick="calcMargin()">Calculate Margin</button>
      <div class="calc-result" id="c_result" style="display:none"></div>
    `
  },
  currency: {
    title: '💱 Currency Converter',
    fields: `
      <div class="calc-field"><label>Amount</label><input type="number" id="c_amount" value="1000" placeholder="1000"></div>
      <div class="calc-field"><label>From</label><select id="c_from">
        <option value="USD">USD — US Dollar</option><option value="EUR">EUR — Euro</option>
        <option value="GBP">GBP — British Pound</option><option value="JPY">JPY — Japanese Yen</option>
        <option value="AUD">AUD — Australian Dollar</option><option value="CAD">CAD — Canadian Dollar</option>
        <option value="CHF">CHF — Swiss Franc</option><option value="CNH">CNH — Offshore Yuan</option>
        <option value="HKD">HKD — Hong Kong Dollar</option>
      </select></div>
      <div class="calc-field"><label>To</label><select id="c_to">
        <option value="EUR" selected>EUR — Euro</option><option value="USD">USD — US Dollar</option>
        <option value="GBP">GBP — British Pound</option><option value="JPY">JPY — Japanese Yen</option>
        <option value="AUD">AUD — Australian Dollar</option><option value="CAD">CAD — Canadian Dollar</option>
        <option value="CHF">CHF — Swiss Franc</option><option value="CNH">CNH — Offshore Yuan</option>
        <option value="HKD">HKD — Hong Kong Dollar</option>
      </select></div>
      <button class="btn btn-p" style="width:100%;justify-content:center" onclick="calcCurrency()">Convert</button>
      <div class="calc-result" id="c_result" style="display:none"></div>
      <p style="font-size:.72em;color:var(--text3);margin-top:8px;text-align:center">Note: Rates are indicative. For live rates, use a broker platform.</p>
    `
  }
};

function openCalc(type) {
  const modal = document.getElementById('calcModal');
  const box = document.getElementById('calcBox');
  const tmpl = CALC_TEMPLATES[type];
  if (!modal || !box || !tmpl) return;
  box.innerHTML = `
    <button class="calc-close" onclick="closeCalc()">✕</button>
    <h3>${tmpl.title}</h3>
    ${tmpl.fields}
  `;
  modal.classList.add('open');
}

function closeCalc() {
  document.getElementById('calcModal').classList.remove('open');
}

function showCalcResult(html) {
  const r = document.getElementById('c_result');
  if (r) { r.style.display = 'block'; r.innerHTML = html; }
}

function calcPosition() {
  const bal = parseFloat(document.getElementById('c_balance').value) || 0;
  const risk = parseFloat(document.getElementById('c_risk').value) || 1;
  const entry = parseFloat(document.getElementById('c_entry').value) || 0;
  const stop = parseFloat(document.getElementById('c_stop').value) || 0;
  if (!entry || !stop || entry === stop) { showCalcResult('<p style="color:var(--red)">Please fill all fields correctly</p>'); return; }
  const riskAmt = bal * risk / 100;
  const perShare = Math.abs(entry - stop);
  const shares = Math.floor(riskAmt / perShare);
  const totalValue = shares * entry;
  showCalcResult(`
    <div class="value">${shares.toLocaleString()} shares</div>
    <div class="label">Position Size</div>
    <div style="margin-top:10px;font-size:.82em;color:var(--text2)">
      Max Risk: <strong>$${riskAmt.toFixed(2)}</strong> (${risk}%)<br>
      Total Position Value: <strong>$${totalValue.toLocaleString()}</strong><br>
      Risk per share: <strong>$${perShare.toFixed(4)}</strong>
    </div>
  `);
}

function calcPnL() {
  const entry = parseFloat(document.getElementById('c_entry').value) || 0;
  const exit = parseFloat(document.getElementById('c_exit').value) || 0;
  const size = parseFloat(document.getElementById('c_size').value) || 0;
  const dir = document.getElementById('c_dir').value;
  const diff = dir === 'long' ? exit - entry : entry - exit;
  const pnl = diff * size;
  const pct = (diff / entry * 100).toFixed(2);
  const color = pnl >= 0 ? 'var(--green)' : 'var(--red)';
  showCalcResult(`
    <div class="value" style="background:${pnl >= 0 ? 'linear-gradient(135deg,#10b981,#059669)' : 'linear-gradient(135deg,#ef4444,#dc2626)'};-webkit-background-clip:text;-webkit-text-fill-color:transparent">${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}</div>
    <div class="label">${pnl >= 0 ? '✅ Profit' : '❌ Loss'} (${pct}%)</div>
  `);
}

function calcMargin() {
  const pos = parseFloat(document.getElementById('c_pos').value) || 0;
  const lev = parseFloat(document.getElementById('c_lev').value) || 100;
  const margin = pos / lev;
  showCalcResult(`
    <div class="value">$${margin.toLocaleString(undefined, {minimumFractionDigits:2,maximumFractionDigits:2})}</div>
    <div class="label">Required Margin</div>
    <div style="margin-top:10px;font-size:.82em;color:var(--text2)">
      Position: $${pos.toLocaleString()} at ${lev}:1 leverage<br>
      Margin %: <strong>${(100/lev).toFixed(2)}%</strong>
    </div>
  `);
}

function calcCurrency() {
  // Approximate rates vs USD (Apr 2026 indicative)
  const RATES = {USD:1,EUR:0.925,GBP:0.79,JPY:154.2,AUD:1.54,CAD:1.37,CHF:0.91,CNH:7.24,HKD:7.81};
  const amount = parseFloat(document.getElementById('c_amount').value) || 0;
  const from = document.getElementById('c_from').value;
  const to = document.getElementById('c_to').value;
  const inUSD = amount / RATES[from];
  const result = inUSD * RATES[to];
  showCalcResult(`
    <div class="value">${result.toLocaleString(undefined, {minimumFractionDigits:2,maximumFractionDigits:4})}</div>
    <div class="label">${amount.toLocaleString()} ${from} = ${result.toFixed(4)} ${to}</div>
    <div style="margin-top:8px;font-size:.78em;color:var(--text3)">Rate: 1 ${from} = ${(RATES[to]/RATES[from]).toFixed(5)} ${to}</div>
  `);
}

// ============================================================
// NAVIGATION & SCROLL
// ============================================================
function initNav() {
  const sections = ['home', 'courses', 'research', 'glossary', 'tools'];
  const navLinks = document.querySelectorAll('.nav-links a:not(.nav-cta)');

  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    let current = 'home';
    sections.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.offsetTop - 100 <= scrollY) current = id;
    });
    navLinks.forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === '#' + current);
    });
  });
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  // Init canvas
  initCanvas();

  // Init nav
  initNav();

  // Render courses
  renderCourses('all');

  // Render research
  renderResearch();

  // Render glossary
  renderGlossary();

  // Init glossary search
  const gsearch = document.getElementById('glossarySearch');
  if (gsearch) gsearch.addEventListener('input', e => renderGlossary(e.target.value));

  // Init chat input enter key
  const chatInput = document.getElementById('chatInput');
  if (chatInput) {
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') sendChat();
    });
  }

  // Welcome message
  setTimeout(() => {
    addChatMessage(ADVISORS[currentAdvisor].greeting, 'bot');
  }, 800);

  // Close modals on backdrop click
  document.getElementById('courseModal').addEventListener('click', function(e) {
    if (e.target === this) closeCourse();
  });
  document.getElementById('calcModal').addEventListener('click', function(e) {
    if (e.target === this) closeCalc();
  });

  // Sources section (render inline in HTML, skip here)
});
