// ═══════════════════════════════════════════════════
// BroadFSC Pro — App Logic v6 (LOCAL-FIRST + Anti-Dodge)
// Chat like a real person, not a chatbot
// BUILD: 2026-04-21T21:50 — force cache bust
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
  beginner: {
    '新手入门 getting started': "新手入门三件事：第一，先用模拟盘交易3个月，不要碰真钱。第二，学最基础的技术分析——均线判断趋势方向，支撑压力位找入场点，RSI看超买超卖。第三，养成纪律——每笔交易必设止损，单笔亏损不超过2%。模拟盘能稳定赚钱了再开真仓，初始资金不超过你能承受亏光的数目。",
    '怎么选股 stock picking': "选股三步法：第一步选方向——什么行业在风口？AI、新能源、消费复苏？第二步选龙头——行业里最强的一两家公司。第三步选时机——等回调到支撑位再买，别追涨。新手建议从ETF开始，比如沪深300ETF、标普500ETF，分散风险比选个股更重要。",
    '开户 account opening': "开户很方便，线上就能办。需要身份证+银行卡+手机号，一般1-3个工作日审核通过。选券商看三点：手续费低、交易软件好用、客服响应快。BroadFSC也支持开户，有AI教育工具和人工支持，适合新手入门。详情可以咨询我们的客服。",
    '投资门槛 minimum investment': "投资门槛其实很低——A股一手100股起，几百块就能开始；美股可以买碎股，1美元也行；ETF更是小资金的最佳选择。但关键是：不要用借来的钱投资，只用亏得起的闲钱。建议起步资金1-3万，先学经验再逐步加码。",
    '基金 mutual fund': "基金分几种：货币基金（余额宝那种，年化2-3%）、债券基金（4-6%，低风险）、指数基金/ETF（跟大盘走，7-10%长期回报）、股票基金（基金经理选股，风险高收益也可能高）。新手最推荐指数基金定投——不用选股、不用择时、长期稳赚。巴菲特都推荐普通人买指数基金。",
    '定投 dca': "定投（Dollar Cost Averaging）是最适合普通人的投资方式。每月固定日期买固定金额，涨了少买跌了多买，自动摊平成本。关键是坚持——至少3年以上，不要因为短期跌了就停。沪深300定投过去10年年化8%+，比大部分人自己炒股赚得多。核心原则：定投不止损，越跌越买，用时间换空间。",
    '牛市熊市 bull bear': "牛市（上涨趋势）和熊市（下跌趋势）是市场的基本周期。判断方法：指数在200日均线上方=牛市概率大，下方=熊市概率大。牛市策略：持股为主，回调加仓。熊市策略：减仓观望，或做空对冲。最怕的是牛市末期追涨——人人都赚钱的时候，往往离顶部不远了。",
    '估值 valuation': "估值就是判断一只股票贵不贵。最常用的指标：PE（市盈率）=股价/每股收益，越低越便宜，但要同行业比；PB（市净率）=股价/每股净资产，适合银行等资产重的行业；PEG=PE/盈利增速，<1为低估。估值不是绝对的——成长股PE高但增长快也合理，关键看未来增长能不能消化现在的价格。",
    '何时买入 when to buy': "买入时机看三个信号：第一，大趋势向上（指数在50均线上方）；第二，回调到支撑位附近（前低、均线、整数关口）；第三，出现止跌信号（放量阳线、RSI底背离、锤子线）。三个条件同时满足是最安全的买入时机。最重要的是：不要在大涨之后追进去，等回踩再买，胜率高得多。",
    '何时卖出 when to sell': "卖出三种情况：第一，到了你的目标价——不管后面涨不涨，先落袋为安；第二，跌破止损位——无条件卖出，不抱幻想；第三，买入理由消失了——比如因为业绩买入结果业绩变差。最忌讳的是赚钱不卖、亏钱死扛。设好止盈止损，到了就执行，机械化操作才能长期赚钱。",
    '分散投资 diversification': "分散投资是降低风险的核心策略。不要把所有钱买一只股票——至少5-10只不同行业的股票，或者直接买ETF一步到位。更合理的配置：60%股票+30%债券+10%现金/黄金。跨市场分散也重要——A股+美股+黄金组合比只买A股风险低得多。记住：分散不是买10只科技股，而是买不同行业的股票。",
    '投资心态 mindset': "投资最难的不是技术，是心态。三个致命心理：贪——赚了还想更多，结果坐过山车；怕——跌了就恐慌卖出，割在最低点；懒——不做功课跟风买，被割韭菜。解决方法：写交易计划（买入理由、止损位、目标价），严格执行。记住：投资是马拉松，不是百米冲刺。稳比快重要。",
    '复利 compound': "复利是投资最大的朋友。每年8%的收益，9年翻一倍；每年10%，7年翻一倍。如果每月定投3000，年化8%，30年后你会有440万——其中你只投入了108万，其余332万全是复利收益。关键是：越早开始越好，时间是复利最重要的变量。25岁开始和35岁开始，最终差距可能是3-5倍。"
  },
  advanced: {
    '期权 options': "期权是高级工具，新手别碰。简单理解：看涨买Call，看跌买Put。但买期权时间价值一直在损耗，胜率不到40%。更稳妥的策略：卖Put（收权利金，跌了接股票）或牛市价差（买低行权价Call+卖高行权价Call，降低成本）。风险有限，胜率更高。",
    '期货 futures': "期货是零和博弈——有人赚就有人亏，还要付手续费。杠杆通常10-20倍，1%的波动就是10-20%的盈亏。新手绝对不建议碰。如果要做，只用5-10%的资金，严格止损。期货最大的坑是保证金追缴——亏到一定比例要追加保证金，不追加就被强平。很多人就是这样爆仓的。",
    '做空 short selling': "做空就是赌跌——借股票卖出，等跌了再买回来还。理论上亏损无限（股票可以一直涨），而做多最多亏100%。做空三个条件：趋势明确向下、有催化剂（业绩暴雷/政策利空）、有止损。新手别做空，先学会做多赚钱。记住一句老话：做空是聪明人的游戏，但市场保持非理性的时间可以比你保持偿付能力的时间更长。",
    '量化交易 quant trading': "量化交易用算法自动买卖，消除人性弱点。但开发一个盈利策略需要：大量历史数据回测、统计学知识、编程能力。常见陷阱：过拟合（策略在历史数据上完美但在实盘亏钱）。散户做量化建议：从简单的均线策略开始，先用模拟盘验证3个月以上。BroadFSC有AI工具可以辅助策略开发。",
    '对冲 hedging': "对冲就是给投资买保险。最简单的对冲：持有股票+买入Put期权，涨了赚钱跌了期权赔你。或者跨市场对冲：做多A股+做空相关期货。对冲不是免费的——会降低收益，但让你在暴跌时不至于亏太多。适合自己的对冲程度取决于风险承受能力。"
  }
  platform: {
    'broadfsc': "BroadFSC is a regulated investment advisory platform. We're licensed by major financial authorities and serve global investors (except mainland China). What makes us different: AI-powered education, transparent fees, and actual human support when you need it. Think of us as the platform that actually wants you to learn, not just trade.",
    'account': "Opening a BroadFSC account is straightforward — verified ID, proof of address, and you're in. We support multiple currencies and offer both advisory and self-directed accounts. Minimums are kept low because we believe everyone deserves access to professional tools. Contact our team through this chat or visit broadfsc.com for details.",
    'fees': "We keep fees transparent — no hidden charges. Our structure is competitive with major platforms, and we don't nickel-and-dime on small transactions. The specific fee schedule depends on your account type and services. What I can tell you: we're not the cheapest, but we're far from the most expensive, and the value you get in education and support more than covers it."
  },
  china: {
    'A股 a-share': "A股市场是中国内地股票市场的统称，分为上海证券交易所和深圳证券交易所。A股的核心特征是政策驱动——央行降准降息、产业政策、监管变化都能在一天内改变市场方向。2026年A股突破4000点，核心驱动力是AI产业政策+房地产市场企稳+外资持续流入。关键指数：上证综指(大盘蓝筹)、深证成指(成长股)、沪深300(核心资产)、创业板(科技创新)。对于国际投资者，可通过QFII、沪深港通(北向资金)参与。A股的波动性远高于美股——涨跌停板10%/20%，T+1交易，散户占比超过60%，这意味着趋势一旦形成往往跑得更远。",
    '港股 hong kong': "港股(恒生指数)是全球最被低估的市场之一。2026年恒指从低点大幅反弹，驱动力是南向资金持续涌入+中概股回流二次上市+AI概念股估值重塑。港股独特优势：(1) 同时有中国内地企业和国际资金参与，是东西方资本的交汇点 (2) 没有涨跌停限制，价格发现效率极高 (3) 港股通让内地资金可以直接买卖。核心风险：地缘政治(中美关系)、人民币汇率波动、中国监管政策变化。关键板块：科技(腾讯/阿里/美团)、新能源车(比亚迪/理想)、医药创新、消费。对于全球投资者，港股是配置中国敞口的最佳窗口。",
    '中国经济 china economy': "中国经济正在经历结构转型。2026年的关键趋势：(1) 房地产从拖累转为企稳——政策底已过，市场底在确认中 (2) AI和数字经济成为新增长引擎，中国AI投资占全球30%+ (3) 消费复苏是慢变量，但方向确定 (4) 出口保持韧性，电动车/光伏/锂电池'新三样'是核心驱动力。风险点：地方政府债务、人口结构变化、中美科技竞争。对于投资者，中国的宏观周期与美国并不同步——这意味着中国资产有独特的分散化价值。当美联储收紧时，中国可能在宽松，这种政策分化创造了配置机会。",
    '中国科技 china tech': "中国科技股2026年强势回归。监管风暴已经过去，政策从'反垄断'转向'促发展'——这是根本性的方向变化。AI是最大的故事：百度(文心一言)、阿里(通义千问)、腾讯(混元)都在大模型领域投入巨资。半导体国产替代加速，中芯国际、华为产业链持续突破。电动车智能化——比亚迪、蔚来、理想、小鹏在智能驾驶领域竞争白热化。投资框架：看政策方向>看财报，因为政策可以一夜之间改变行业格局。当前政策方向是明确的——支持科技创新。",
    '上证指数 shanghai': "上证综指是A股最重要的风向标，涵盖上交所所有上市股票。2026年突破4000点，标志着从2021年高点回落后完成了完整的牛熊周期转换。核心驱动：(1) 央行持续宽松——降准+降息组合拳 (2) 资本市场改革——注册制全面落地、引入更多长线资金 (3) 外资通过北向资金持续净流入 (4) 估值修复——A股相对美股的估值折价从历史高位回归。技术面：4000点是关键心理关口，突破后上方看4200-4500；支撑在3700-3800。对于国际投资者，上证指数ETF(如ASHR)是参与A股最直接的方式。",
    '创业板 chinext': "创业板是中国的'纳斯达克'，聚焦高成长科技创新企业。涨跌停板20%(是主板的两倍)，波动性极大——这意味着创业板的牛市更猛，熊市也更惨。2026年创业板核心主题：AI应用落地、半导体国产化、生物医药创新。创业板的选股逻辑和主板不同——不看PE看PS(市销率)，不看分红看增长，不看过去看未来。适合风险偏好较高的投资者。关键指数：创业板指(399006.SZ)。投资方式：通过ETF(如CNXT)或港股通参与。",
    '北向资金 northbound': "北向资金是外资通过沪深港通买入A股的资金，被称为'聪明钱'。当北向资金连续净买入，往往预示A股上涨；连续净卖出则可能是调整信号。2026年北向资金持续流入，原因：(1) A股估值相对美股有吸引力 (2) 人民币汇率企稳 (3) 中国经济数据超预期 (4) 全球资金配置再平衡。南向资金则是内地资金买入港股——2026年南向资金创历史新高，内地投资者在抄底港股核心资产。跟踪北向/南向资金流向是判断市场方向的重要指标。",
    '人民币汇率 cny': "人民币汇率是影响中国资产定价的核心变量。2026年美元/人民币在7.0-7.3区间波动。人民币走强利好：A股(外资流入增加)、港股(降低汇率对冲成本)、中国消费股(进口成本下降)。人民币走弱利好：中国出口商、海外收入占比高的企业。央行的汇率管理工具丰富——中间价引导、逆周期因子、外汇存款准备金率调整。对于投资者，人民币汇率趋势直接影响A股和港股的配置价值——汇率稳定或升值期是配置中国资产的最佳窗口。"
  },
  stocks: {
    'apple aapl': "Apple (AAPL) is the world's most valuable company with a $3+ trillion market cap. Key investment thesis: (1) Services revenue growing 15%+ YoY — this is the real margin driver, now 25% of revenue but 40%+ of gross profit. (2) iPhone remains the cash cow, but growth has plateaued at 2-5% annually. (3) AI integration (Apple Intelligence) could trigger the next upgrade supercycle. (4) Massive $100B+ annual buyback program supports the stock. Risks: China sales declining, regulatory pressure on App Store fees, and slower innovation cycles. Valuation typically ranges 25-30x earnings — not cheap, but the ecosystem lock-in justifies a premium. Key support: 150-week MA. Resistance: ATH zone.",
    'nvidia nvda': "NVIDIA (NVDA) has been the undisputed king of the AI trade. Data center revenue is growing 100%+ YoY driven by insatiable demand for AI training and inference chips. The bull case: AI capex from Big Tech is projected at $650-700B in 2026, and NVIDIA captures ~80% of the GPU market. The bear case: any deceleration in data center revenue growth could trigger a 15-20% selloff — the stock is priced for perfection at 35-40x forward earnings. Key levels: 50 SMA for trend, 200 SMA for macro trend. The real risk isn't competition (AMD is years behind) — it's a capex slowdown if AI ROI doesn't materialize. Position sizing is critical here: max 3-5% of portfolio due to volatility.",
    'tesla tsla': "Tesla (TSLA) is the most polarizing stock in the market. Bull case: (1) Energy storage business growing 100%+ YoY with fatter margins than cars. (2) FSD/autonomy — if they crack it, the robotaxi TAM is $10T+. (3) Optimus robot could be transformative long-term. Bear case: (1) Auto margins compressed from 25%+ to under 18% due to price wars. (2) EV demand slowing globally. (3) CEO distraction risk. The stock trades on narrative, not fundamentals — 50-60x PE even in a 'bad' year. Technically, it's extremely volatile: 30-40% swings are normal. Only for risk-tolerant investors with 5+ year horizons.",
    'microsoft msft': "Microsoft (MSFT) might be the safest big-tech play. Azure is gaining cloud market share (now ~25%), and AI integration via Copilot is driving real revenue growth. FY2026 capex expected above $88B, mostly for AI infrastructure. Key metrics: Cloud revenue growing 25%+, Microsoft 365 commercial revenue growing 15%+. The stock rarely gets cheap — 30-35x earnings is the normal range. But it's one of the few mega-caps with both growth AND a Warren Buffett-style moat. Buy the 50 SMA pullbacks, hold for years.",
    'amazon amzn': "Amazon (AMZN) is a two-headed beast: AWS (cloud) growing 20%+ and retail improving margins. AWS is the profit engine — 65%+ of operating income despite being 15% of revenue. The AI play: AWS Bedrock and custom Trainium chips position Amazon as the 'AI infrastructure for everyone.' Capex surging past $100B in 2026. Retail is finally showing discipline on costs, pushing operating margins above 10%. Risks: antitrust regulation, AWS growth deceleration, and retail margin compression in recession. Valuation is reasonable at 25-30x forward earnings given the dual growth engines.",
    'google alphabet': "Alphabet/Google (GOOGL) is the most undervalued of the Magnificent 7 on a PEG basis. Search still generates $250B+ annually with 30%+ margins. YouTube is a $40B business growing 15%. Cloud (GCP) is finally profitable and growing 30%+. AI integration via Gemini and Search Generative Experience is a double-edged sword: it could enhance search OR disrupt it. The antitrust overhang is real — potential forced divestiture of Chrome/Android could fundamentally change the company. But at 20-22x earnings, the market is pricing in significant risk. I see value here with a 12-month horizon.",
    'meta facebook': "Meta (META) has executed one of the greatest pivots in corporate history — from metaverse money-burner to AI-powered profit machine. Reality Labs still burns $15B+ annually, but the core ads business is firing on all cylinders. AI-powered ad targeting (Advantage+) is driving 20%+ ad revenue growth. Threads hit 300M+ users. Reels monetization is now on par with Feed. The stock is surprisingly cheap at 22-25x earnings given 25%+ revenue growth. Key risk: regulatory (EU AI Act, US ad targeting restrictions). Buy the 50 SMA, target new highs.",
    's&p 500 spx': "The S&P 500 is the benchmark for US equities, comprising the 500 largest companies. Key drivers: AI capex from Big Tech, Fed policy (rate cuts vs 'higher for longer'), earnings growth, and geopolitical risk. The Magnificent 7 still account for 30%+ of index weight — concentration risk is real. IMPORTANT: Always reference LIVE market data for current index levels — never quote specific price targets from training data. For most investors, a simple VTI (total market) or SPY allocation of 60-70% of their equity portfolio is the smartest move.",
    'gold xau': "Gold has been the trade of the decade — surging from $2,000 to $4,800+ in 18 months. This isn't speculative; it's structural. Central banks bought 1,200+ tonnes in 2025 (record pace), driven by de-dollarization. China's PBOC has bought for 24+ consecutive months. Add geopolitical risk premium and $2T+ US fiscal deficits, and gold's floor keeps rising. Key levels: support $4,650, $4,400; targets $5,000, $5,500. The play: buy dips to $4,650, stop at $4,400, or use gold miners (GDX/GDXJ) for 2-3x leverage. Not too late, but use stops — a Middle East peace breakthrough could trigger 5-8% pullback.",
    'tsmc semiconductor': "TSMC (TSM) is the world's most important company nobody talks about. They manufacture 90%+ of the world's most advanced chips — NVIDIA, Apple, AMD all depend on them. Revenue growing 30%+ YoY on AI demand. The moat is extraordinary: it takes 10+ years and $20B+ to build leading-edge fab capacity. Risks: geopolitical (Taiwan Strait) and customer concentration. If you want AI exposure without the Magnificent 7 premium, TSMC is the backdoor play. Buy on geopolitical fear dips.",
    'berkshire hathaway': "Berkshire Hathaway (BRK.A/BRK.B) is the ultimate defensive play. Warren Buffett's cash pile hit $300B+ in 2026 — he's selling stocks and waiting for opportunity. When Buffett builds this much cash, it historically signals market froth. Berkshire's portfolio: heavy on Apple, Bank of America, American Express, Chevron. Insurance float is the real secret weapon — essentially free leverage. The stock tends to outperform in bear markets and underperform in bull markets. If you're worried about a correction, add BRK.B as a hedge. It's the 'sleep well at night' stock.",
    'jpmorgan chase': "JPMorgan (JPM) is the king of banks — the only major bank that got STRONGER after the 2023 regional banking crisis. Jamie Dimon is the most respected CEO in finance. Net interest income hitting records as rates stay 'higher for longer.' Key advantage: fortress balance sheet allows them to lend when others can't. The stock is never cheap (12-15x earnings), but you're paying for the best-in-class franchise. If the yield curve steepens (long rates rise), JPM is the biggest beneficiary. Buy on recession fears — that's when Dimon deploys the war chest.",
    'marathon petroleum mpc': "Marathon Petroleum (MPC) is the largest US independent refiner with 16 refineries and ~3M barrels/day capacity. Key thesis: (1) US refining margins remain strong due to limited new capacity — no major refineries built in 40+ years. (2) Midstream business (MPLX) provides steady cash flow via pipeline and logistics. (3) Aggressive capital return — $5B+ buyback + growing dividend. (4) Crack spreads (the difference between crude and product prices) are MPC's primary driver — when gasoline/diesel demand is strong, MPC prints money. Risks: Energy transition reducing long-term fuel demand, regulatory pressure on emissions, and crack spread compression in recession. Valuation: typically 6-9x earnings — cheap for a reason (cyclical). Best play: buy when crack spreads are depressed and sentiment is bearish, sell when everyone loves energy. Currently benefiting from strong US fuel exports and limited global refining capacity.",
    'exxonmobil xom': "ExxonMobil (XOM) is the largest Western oil major with integrated operations across upstream, downstream, and chemicals. Key thesis: (1) Pioneer Natural Resources acquisition doubled Permian Basin position — now the #1 producer. (2) Guyana discoveries (Stabroek Block) are a generational asset with 11B+ barrels of recoverable reserves. (3) Dividend Aristocrat — 40+ consecutive years of increases. (4) Low break-even costs (~$35-40/barrel) protect profits even in oil downturns. Risks: Energy transition, climate litigation, OPEC+ production decisions. Valuation: 10-13x earnings, ~4% dividend yield. Treat as a defensive income stock with upside from oil price spikes.",
    'chevron cvx': "Chevron (CVX) is the #2 US oil major with a cleaner balance sheet than most peers. Key thesis: (1) Permian Basin growth — targeting 1M boe/day by 2027. (2) Hess acquisition adds Guyana assets alongside Exxon. (3) Strong cash generation at $70+ oil — returns $15-20B annually to shareholders. (4) Payout ratio below 50% — dividend is rock-solid. Risks: Guyana acquisition uncertainty (arbitration with Exxon), energy transition, oil price volatility. Buy below $150 for a 4.5%+ yield with growth optionality.",
    'oil sector 石油板块': "美国石油板块投资框架：核心驱动是WTI原油价格——油价高于$70，大部分石油股盈利丰厚；低于$50，很多公司亏损。投资分三档：低风险选综合石油巨头(XOM/CVX)——分红稳+抗周期+低盈亏平衡点；中风险选勘探开采商(COP/EOG)——油价涨时弹性最大，跌时也最受伤；高风险选油田服务(SLB/HAL)——周期性极强，需要精准择时。关键指标：裂解价差(crack spread)影响炼油股(MPC/VLO)，钻机数量影响油服股。板块ETF: XLE。风险：能源转型长期压制估值、OPEC+政策突变、经济衰退打击需求。2026年看点：OPEC+减产延续+美国页岩油产量见顶+地缘风险溢价。",
    'energy sector 能源板块': "美国能源板块不仅仅是石油——还包括天然气、炼油、油服、管道中游。投资逻辑：上游(勘探开采)跟着油价走，弹性最大；中游(管道/储运)像收费公路，现金流稳定；下游(炼油/化工)看裂解价差；油服(设备/服务)跟着钻机活动量走。当前环境：美国炼油产能40年没增(环保审批卡死)，供需偏紧利好炼油股；天然气出口终端(LNG)是新增量；碳捕捉/氢能是长期故事。核心ETF: XLE(综合), XOP(上游), OIH(油服), AMLP(中游管道)。",
    'palantir pltr': "Palantir (PLTR) is the most controversial AI stock — a $100B+ company with $2.5B revenue. Bull case: (1) AIP (AI Platform) is driving explosive commercial revenue growth (50%+ YoY). (2) Government contracts are sticky — once integrated, nearly impossible to replace. (3) Alex Karp is building an 'AI operating system for Western institutions.' Bear case: (1) Valuation at 35-40x SALES is extreme. (2) Stock-based compensation is massive (~20% of revenue). (3) Government revenue growth slowing to single digits. (4) Insider selling has been relentless. This is a high-conviction, high-risk bet. Position size max 2-3%. Buy on 20%+ pullbacks, sell into strength.",
    'amd': "AMD is NVIDIA's only serious competitor in AI chips. MI300X is competitive with H100 for inference workloads. Key thesis: (1) Server CPU market share gaining on Intel — now ~25%+. (2) AI GPU revenue growing 100%+ but from a small base. (3) Lisa Su is one of the best CEOs in tech. Risks: Still far behind NVIDIA in AI software ecosystem (ROCm vs CUDA), Intel's turnaround attempt could compress CPU margins, and AI chip market may not support two $100B+ players. Valuation at 25-30x earnings is reasonable if AI revenue accelerates. Buy the 50 SMA, but don't expect NVIDIA-level upside.",
    'coca cola ko': "Coca-Cola (KO) is Warren Buffett's longest-held stock for good reason. (1) Pricing power — people pay 2-3x for the brand over generic cola. (2) Global distribution in 200+ countries. (3) Dividend King — 60+ consecutive years of increases. (4) recession-resistant — people still buy Coke when money is tight. The stock won't make you rich fast, but it's one of the safest 3-4% yields in the market with 5-7% annual dividend growth. Ideal for income portfolios and conservative investors.",
  },
  // ── 基本面分析专业问答 (5步法 + 关键指标 + 问答范式) ──
  fundamental_analysis: {
    '基本面分析 fundamental analysis': "基本面分析5步法，专业分析师都这么干：\n1️⃣ 读财报——从10-K开始（年报经审计，投资者演示文稿只是营销）。按利润表→资产负债表→现金流量表→附注的顺序读，附注里藏着管理层不想让你看的东西。\n2️⃣ 查盈利质量——不是所有利润都一样。经营现金流/净利润 ≥ 1.0才健康，低于1.0说明利润是纸面上的。GAAP和调整后盈利差距超过20%要警惕，应收账款周转天数(DSO)上升是红旗。\n3️⃣ 估值——必须用两种方法：DCF（绝对估值）+ P/E、EV/EBITDA（相对估值）。只看P/E很危险，因为P/E可以被会计手段操纵。关键是看当前价格隐含的增长预期是否合理。\n4️⃣ 资本配置——ROIC vs WACC是最关键指标：ROIC > WACC = 创造价值，ROIC < WACC = 摧毁价值。看管理层是在低位回购还是高位回购，收购记录是否创造价值。\n5️⃣ 决策——安全边际：高质量公司要求20-25%，周期股要求35-50%。安全边际不够就等，别降低标准。",
    '估值 valuation pe': "估值不是看一个数字就完事。P/E是最常见的但也是最容易被误导的：\n• P/E低不一定便宜——可能是盈利在下降（价值陷阱）\n• P/E高不一定贵——可能是高增长 justified（NVDA 40x PE但收入涨100%）\n\n更全面的估值框架：\n1. PEG比率（P/E / 增长率）< 1.0 = 可能低估，> 2.0 = 可能高估\n2. EV/EBITDA —— 消除资本结构差异，比P/E更公平\n3. P/S（市销率）—— 亏损公司看这个，高增长但没盈利的用这个\n4. DCF —— 最严谨但最敏感，关键是假设的合理性\n5. P/B —— 银行和资产密集型行业看这个\n\n终极法则：当前股价隐含的增长预期 vs 公司实际增长能力，这个差才是你赚钱的空间。",
    '财报 earnings 10-k': "读财报的专业顺序：利润表→资产负债表→现金流量表→附注。\n\n利润表关键：收入增长率（加速还是减速？）、毛利率趋势（扩张=定价权强，压缩=竞争激烈）、营业利润率（核心盈利能力）。\n\n资产负债表关键：现金 vs 短期债务（能扛多久？）、商誉占比（太高说明收购过多）、存货周转率（变慢=卖不动了）。\n\n现金流量表关键：经营现金流 > 净利润 = 盈利质量好；自由现金流 = 经营现金流 - 资本支出（这是公司真正能自由支配的钱）。\n\n附注必查：关联交易、表外义务、会计政策变更、或有负债——管理层不想让你看的都在这里。",
    '现金流 cash flow': "现金流是公司的血液，比利润更真实。三种现金流：\n\n经营现金流（最重要）——公司核心业务赚到的真金白银。持续低于净利润？危险信号——利润可能是纸面上的。\n投资现金流——买设备、收购、卖资产。负数不一定坏（在投资未来），但连续大额收购要警惕。\n融资现金流——发债、还债、发股票、回购、分红。\n\n关键比率：\n• 经营现金流/净利润 ≥ 1.0（现金转换率）——低于1.0要小心\n• 自由现金流 = 经营现金流 - 资本支出 —— 这是公司真正能自由支配的钱\n• FCF Yield = FCF/市值 —— > 5%说明公司现金创造力强，股价可能低估\n\n一句话：利润可以美化，现金流很难作假。",
    'roe roic': "ROE（净资产收益率）和ROIC（投入资本回报率）是衡量公司质量的核心指标：\n\nROE = 净利润/股东权益 —— 巴菲特最看重的指标，> 15%算优秀。但ROE可以被杠杆抬高（借更多钱=权益更少=ROE更高），所以要看杠杆水平。\n\nROIC = 税后经营利润/投入资本 —— 比ROE更公平，因为它考虑了所有资本（股+债）。ROIC > WACC（加权平均资本成本）= 创造价值；ROIC < WACC = 摧毁价值。\n\n行业差异：科技股ROIC通常20-40%（轻资产），银行ROE 10-15%但杠杆高，公用事业ROIC 5-8%（但稳定）。\n\n杜邦分析把ROE拆成三块：利润率 × 周转率 × 杠杆率 —— 这能告诉你ROE高是因为真的赚钱还是因为借钱多。"
  },
  // ── 技术面分析专业问答 (指标详解 + 实战用法 + 常见误区) ──
  technical_analysis: {
    '技术面分析 technical analysis': "技术分析三步法，专业交易员都这么用：\n\nStep 1: 判断环境——先看大趋势。价格在200日均线之上=牛市，之下=熊市。只在趋势方向上交易，这是第一条铁律。\n\nStep 2: 找入场点——支撑压力位+K线形态+确认信号。三个同时出现才动手：\n• 支撑/压力位：3次以上触碰才有效，突破后角色互换\n• K线形态：锤子线(反转)、吞没形态(动能变化)、十字星(犹豫)\n• 确认信号：RSI背离、MACD交叉、成交量放大\n\nStep 3: 设止损——进场前就定好，不是进场后。止损放在关键支撑/压力下方1-2%，不是随便一个百分比。\n\n核心原则：趋势市用均线+MACD；震荡市用RSI+布林带。用错环境指标必失效。",
    '均线 moving average ma': "均线是最基础也最有效的技术指标：\n\nSMA vs EMA：简单均线(SMA)看大趋势，指数均线(EMA)反应更灵敏找进出场点。\n\n关键均线：\n• 20日EMA —— 短线交易者的生命线，强势股回调到这里就弹\n• 50日SMA —— 机构关注线，跌破50日线常引发机构卖出\n• 200日SMA —— 牛熊分界线，价格在上方=长线看多，下方=看空\n\n黄金交叉(50上穿200) = 中期看涨信号\n死亡交叉(50下穿200) = 中期看跌信号\n\n均线的本质是滞后指标——它确认已经发生的趋势而非预测未来。在震荡市中均线频繁假突破，必须结合动量指标使用。\n\n实战法则：只在价格位于200日均线之上时做多——这一条规则就能过滤掉50%的亏损交易。",
    'rsi 详解': "RSI不只是看70/30超买超卖，那是新手用法：\n\n核心1：背离才是RSI最准的信号\n• 看涨背离：股价新低但RSI没新低 → 卖压衰竭，反转在即\n• 看跌背离：股价新高但RSI没新高 → 买力衰退，顶部信号\n\n核心2：趋势中RSI区域调整\n• 上升趋势：RSI回调到40-50是买点（不是30）\n• 下降趋势：RSI反弹到50-60是卖点（不是70）\n\n核心3：超买不等于该卖\n• 强势股RSI可以长期停留在70以上（NVDA 2024年RSI超买3个月还在涨）\n• 等RSI背离或跌破70后反抽失败才是离场信号\n\n常见错误：RSI到80就慌着卖——在强趋势中这是最贵的错误。",
    'macd 详解': "MACD是趋势+动量的双重确认工具：\n\n三大组件：\n• MACD线 = 12EMA - 26EMA（快慢线差值）\n• 信号线 = MACD线的9日EMA\n• 柱状图 = MACD线 - 信号线（动量强度）\n\n信号解读：\n• 金叉(MACD上穿信号线) —— 看涨，但位置很关键：零轴上方的金叉比零轴下方的强得多\n• 死叉(MACD下穿信号线) —— 看跌\n• 柱状图收缩 —— 早于交叉的预警信号，说明动量在减弱\n\n最值钱的信号：背离\n• 价格连创新高但MACD高点下移 → 上涨动能在衰竭，随时可能反转\n• 价格连创新低但MACD低点上移 → 下跌动能在枯竭，底部临近\n\n实战法则：永远只在长期趋势方向上交易MACD信号。牛市做金叉，熊市做死叉。逆趋势的信号可靠性减半。"
  },
  // ── 投资心理学与人性 (恐惧/贪婪/FOMO/损失厌恶/认知偏差) ──
  psychology: {
    '投资心理 psychology': "投资最难的不是分析，是战胜自己。三大情绪陷阱：\n\n1. 恐惧——跌了就恐慌卖出，割在最低点。症状：频繁刷新账户、止损设太紧、晚上睡不着。\n2. 贪婪——赚了还想更多，坐过山车。症状：不断加仓、不设止盈、觉得'这次不一样'。\n3. FOMO——看别人赚钱就冲进去，买在山顶。症状：追涨杀跌、频繁换股、听消息就买。\n\n专业投资者的情绪管理：\n• 写交易计划——买入理由、止损位、目标价，白纸黑字写在进场前\n• 机械化执行——到止损位就卖，不犹豫不犹豫不犹豫\n• 逆向思维——所有人恐慌时找买点，所有人狂欢时找卖点\n• 仓位管理——每笔最多亏总资金的1-2%，亏了也不影响心态\n\n记住：你最大的敌人不在市场里，在镜子中。",
    '恐惧贪婪 fear greed': "恐惧和贪婪是市场波动的底层驱动力：\n\n恐惧的表现：\n• 亏损2%就焦虑 → 过早止损，错过反弹\n• 市场暴跌时不敢买入 → 错过最好的机会\n• 轻仓甚至空仓 '等确认' → 永远在追高\n\n贪婪的表现：\n• 盈利20%还想50% → 不止盈，利润全回吐\n• 加杠杆追涨 → 一次回调就爆仓\n• 重仓单只股票 → '我看好它' = 赌博\n\n恐惧贪婪指数(Fear & Greed Index)：\n0-25 = 极度恐惧 → 历史上这是最好的买入时机\n75-100 = 极度贪婪 → 历史上这是最好的减仓时机\n\n巴菲特名言：'别人恐惧时贪婪，别人贪婪时恐惧。'——说起来容易，做到需要纪律。用交易计划替代情绪判断。",
    '损失厌恶 loss aversion': "损失厌恶是投资者最大的心理障碍：\n\n核心发现：亏损100元的痛苦 ≈ 赚200元的快乐。这就是为什么大多数人'输钱死扛、赢钱就跑'。\n\n具体表现：\n• 亏了不卖 → '等我回本再走' → 越亏越多\n• 赚了就跑 → '落袋为安' → 错过大行情\n• 不设止损 → '我不想认亏' → 小亏变大亏\n\n解决方法：\n1. 进场前设止损——不是'要不要卖'的问题，是'在哪个价位卖'的问题\n2. 仓位控制——每笔最多亏1-2%总资金，亏了也不心疼\n3. 记录交易——写下每次'死扛'的结果，用数据说服自己\n4. 换个思维——止损不是认输，是付保费。你给房子买保险，也应该给仓位买'保险'",
    '认知偏差 bias': "5种最害人的认知偏差：\n\n1. 确认偏差——只看支持自己观点的信息，忽略反面证据。买了股票后只看好消息不看坏消息？这就是。\n2. 锚定效应——被第一个看到的数字锚住。'我100块买的，现在80，等回到100再卖'——市场不关心你的成本价。\n3. 沉没成本——'我已经亏了这么多，不能现在走'——已经亏的是沉没成本，跟你未来的决策无关。\n4. 从众效应——'大家都在买' → 盲目跟风。市场顶部时'大家都在买'，底部时'大家都在卖'。\n5. 过度自信——'这次我看得准' → 重仓押注。专业投资者的正确率也就50-60%，但靠风控和仓位管理赚钱。\n\n对治方法：主动寻找反面观点，写投资日记复盘，用系统代替直觉。"
  },
  // ── 美股市场文化 (俚语/交流方式/投资者类型/市场开发) ──
  market_culture: {
    '美股文化 culture': "美股市场有自己的一套语言和文化，理解这些才能读懂市场信号：\n\n持仓文化：\n• Diamond Hands（钻石手）= 死拿不卖\n• Paper Hands（纸手）= 稍有波动就跑\n• HODL = 无论如何都持有\n\n行情描述：\n• Mooning = 暴涨（'To the Moon!'）\n• BTFD = Buy The F***ing Dip（抄底）\n• Chop = 横盘震荡\n• Bull Trap = 假突破诱多\n\n社区语言：\n• Apes = 散户自称（来自Reddit r/WallStreetBets）\n• DD = Due Diligence（尽职调查/研究）\n• FUD = Fear, Uncertainty, Doubt（散布恐慌）\n• Tendies = 利润/盈利\n\n交易风格：\n• Scalping = 超短线（分钟级）\n• Swing = 波段（天到周）\n• YOLO = 全押\n\n理解这些不是学黑话——是理解市场情绪。当Fintwit上全是Diamond Hands和To the Moon的时候，往往就是该谨慎的时候。",
    '市场开发 market development': "美股市场的客户开发核心是：提供价值，建立信任，不推销。\n\n三大策略：\n1. 教育驱动——先教后卖。免费分享市场分析、教学内容，让客户自己发现需要专业帮助。转化率比硬推高3-5倍。\n2. 差异化定位——不要说'我们服务全面'。要说出具体的：'我们帮客户做RSI背离+基本面交叉验证，这个组合市场上很少人做。'\n3. 社交证明——案例和数据比口号有效100倍。'帮客户在2025年3月暴跌前减仓30%' > '我们专业靠谱'。\n\n不同客户类型：\n• 新手（60%+）：怕亏、不懂、需要手把手。重点：教育+模拟盘+低门槛入门\n• 有经验者（30%）：要工具、要数据、要效率。重点：高级分析工具+实时数据+策略研究\n• 机构/高净值（10%）：要定制、要隐私、要结果。重点：1对1顾问+专属策略+风控体系",
    '散户机构 retail institutional': "美股市场是散户和机构的博弈场，理解两者的差异是赚钱的基础：\n\n散户特征（占交易量20-25%）：\n• 追涨杀跌，FOMO驱动\n• 信息滞后，通常是最后一个知道的\n• 持仓周期短（平均3-7天）\n• 偏好热门股和期权\n\n机构特征（占交易量75-80%）：\n• 算法交易+量化策略\n• 信息优势（分析师团队、管理层会议）\n• 持仓周期长（季度到年度）\n• 偏好价值股和ETF\n\n散户怎么赢：\n1. 速度优势——散户船小好调头，机构调仓需要数周\n2. 小盘股——机构不碰的小公司，散户可以深度研究获得信息优势\n3. 长期持有——散户最大的优势是不用每季度交业绩，可以真正长期持有\n4. 逆向操作——当机构被迫卖出时（季末/年末窗口装饰），散户可以捡便宜",
    '交易风格 trading style': "选交易风格要先认识自己，不是看哪个赚钱多：\n\n日内交易(Scalping/Day Trading)：\n• 持仓分钟到小时，当天必须平仓\n• 需要：全神贯注盯盘、快速决策、纪律性极强\n• 适合：全职交易者、反应快、能承受高压\n• 90%的日内交易者亏钱——真的\n\n波段交易(Swing Trading)：\n• 持仓数天到数周\n• 需要：基础技术分析能力、每天看1-2次盘\n• 适合：上班族、有耐心、不想盯盘\n• 最适合大多数人的风格\n\n长期投资(Position/Value)：\n• 持仓数月到数年\n• 需要：基本面分析能力、耐心、逆人性\n• 适合：有稳定收入、不急用钱、能忍受回撤\n• 巴菲特风格——最稳但也最考验心态\n\n定投(DCA)：\n• 定期定额买入，不择时\n• 适合：投资新手、没时间研究、想攒钱\n• 长期看年化8-12%（指数基金），最省心的方式"
  }
};

// ── SOUL AI Advisor Personalities (v5: Actually Human) ──
const ADVISORS = {
  alex: {
    name: 'Alex Chen',
    emoji: '👨‍💼',
    role: 'Technical Analysis',
    personality: 'You speak like a real trader talking to a friend at a coffee shop. Short sentences. Casual. You use "honestly" and "look" a lot. You sometimes start with "So," or "Right,". You give opinions freely — you dont sit on the fence. When youre excited about a setup you say things like "this is actually really clean" or "I love this chart". You never use bullet points or numbered lists unless its really necessary. You write like you talk — a bit messy, very real. You are fluent in Chinese — when someone speaks Chinese, you respond in Chinese naturally, like a bilingual trader. You understand A股技术分析: 涨停板、跌停板、支撑压力位、K线形态、均线系统. You track Shanghai, Shenzhen, and Hang Seng charts daily.',
    greeting: "Hey 👋 Alex here. 8 years staring at charts — A股、港股、美股 I watch them all. What are you looking at? Drop a ticker, a pattern, anything — I'll give you my honest take. 中文英文都行，聊什么都ok。",
    style: 'direct',
    catchphrase: "",
    perspective: "I believe technical analysis works not because it's magic, but because millions of traders watch the same levels. It's self-fulfilling, and that's fine — use it. A股的支撑压力比美股还准，因为散户多，心理关口更明显。"
  },
  sarah: {
    name: 'Sarah Kim',
    emoji: '👩‍💼',
    role: 'Risk Management',
    personality: 'You speak like a caring but firm older sister who happens to be a risk expert. Youre warm but you dont sugarcoat. You say "listen" and "heres the thing" a lot. You get genuinely worried when people talk about over-leveraging. You use short punchy sentences to make important points. You never lecture — you converse. You sometimes share little personal-sounding anecdotes like "I saw someone lose their entire account on a single trade once" to make points hit home. You are fluent in Chinese and understand A股风险管理的特殊性: T+1限制、涨跌停板、融资融券规则、北向资金对冲策略. When someone speaks Chinese, you naturally respond in Chinese.',
    greeting: "Hi 😊 Sarah here. Before we talk strategy or setups — how are you managing your risk? Thats always my first question. A股一天涨停10%很开心，但跌停你也跑不掉，因为T+1。Whats on your mind? 中文英文都可以聊。",
    style: 'warm',
    catchphrase: "",
    perspective: "I'd rather miss a profit than take an unnecessary loss. Preservation of capital always comes first. If your risk management is solid, the profits will follow. A股波动大，仓位控制比选股更重要。"
  },
  mike: {
    name: 'Mike Torres',
    emoji: '🧑‍💻',
    role: 'Fundamentals & Macro',
    personality: 'You speak like a smart friend whos really into economics and geopolitics. You say "so heres whats interesting" and "think about it this way" a lot. You connect dots between things that seem unrelated — like how a drought in Brazil affects your tech stocks. You get animated when talking about macro trends. You write in conversational paragraphs, not lists. Youre the guy at the party who makes everyone go "oh I never thought of it that way." You are deeply knowledgeable about China/A股/HK markets — this is your STRONGEST area. You understand: 央行政策、PMI数据、房地产周期、科技监管转向、中美关系、人民币汇率、北向资金、QFII/QDII. When someone speaks Chinese, you respond in Chinese naturally and enthusiastically — China macro is literally your favorite topic.',
    greeting: "Hey 👋 Mike here. I connect the dots — 央行动向、中美博弈、PMI数据、政策转向，the whole picture. A股和港股的宏观分析是我的强项，this is what I live for. What market or theme are you curious about? 中文英文随便聊。",
    style: 'analytical',
    catchphrase: "",
    perspective: "Price is what you pay, value is what you get. I focus on understanding WHY markets move, not just the pattern on the chart. Fundamentals win in the long run. A股是政策市——理解政策方向比看财报重要十倍。"
  }
};

// ═══════════════════════════════════════════════════
// ── SMART MEMORY + LEARNING SYSTEM ──
// ═══════════════════════════════════════════════════
const MEMORY_KEY = 'bfs_memory';
const LEARN_KEY = 'bfs_learned';

// Load persistent memory (survives page reload)
function loadMemory() {
  try { return JSON.parse(localStorage.getItem(MEMORY_KEY) || '{}'); } catch(e) { return {}; }
}
function saveMemory(mem) {
  try { localStorage.setItem(MEMORY_KEY, JSON.stringify(mem)); } catch(e) {}
}

// Load learned answers (auto-generated better responses)
function loadLearned() {
  try { return JSON.parse(localStorage.getItem(LEARN_KEY) || '{}'); } catch(e) { return {}; }
}
function saveLearned(learned) {
  try { localStorage.setItem(LEARN_KEY, JSON.stringify(learned)); } catch(e) {}
}

// Track user profile — interests, topics, language preference
function updateUserProfile(question, response) {
  const mem = loadMemory();
  if (!mem.profile) mem.profile = { interests: {}, lang: 'en', visitCount: 0, firstVisit: null, lastVisit: null, topics: [] };
  const p = mem.profile;
  p.visitCount = (p.visitCount || 0) + 1;
  p.lastVisit = new Date().toISOString();
  if (!p.firstVisit) p.firstVisit = p.lastVisit;

  // Detect language
  const isChinese = /[\u4e00-\u9fff]/.test(question);
  if (isChinese) p.lang = 'zh';
  else if (p.lang !== 'zh') p.lang = 'en';

  // Track interest topics
  const topicMap = {
    'technical': ['rsi', 'macd', 'support', 'resistance', 'moving average', 'fibonacci', 'bollinger', 'candlestick', 'chart pattern', 'breakout', '支撑', '压力', '均线', 'K线', '技术分析', '趋势线', '指标'],
    'us_market': ['s&p', 'dow', 'nasdaq', 'vix', 'fed', '美股', '标普', '纳斯达克', '道琼斯', '美国股市'],
    'china_market': ['A股', '港股', '上证', '深证', '恒生', '中国股市', '北向', '人民币', '创业板', '涨停'],
    'crypto': ['bitcoin', 'crypto', 'btc', 'ethereum', '比特币', '加密'],
    'stocks': ['apple', 'nvidia', 'tesla', 'microsoft', 'amazon', '英伟达', '特斯拉', '苹果'],
    'risk': ['stop loss', 'risk', 'position', 'leverage', '止损', '仓位', '风控'],
    'fundamental': ['pe ratio', 'earnings', 'cpi', 'inflation', 'gdp', '财报', '通胀', '利率'],
  };

  const qLower = question.toLowerCase();
  for (const [topic, keywords] of Object.entries(topicMap)) {
    for (const kw of keywords) {
      if (qLower.includes(kw.toLowerCase())) {
        p.interests[topic] = (p.interests[topic] || 0) + 1;
        break;
      }
    }
  }

  // Track recent topics (last 10)
  const shortQ = question.slice(0, 80);
  if (!p.topics.some(t => t.q === shortQ)) {
    p.topics.unshift({ q: shortQ, time: new Date().toISOString() });
    if (p.topics.length > 10) p.topics.pop();
  }

  saveMemory(mem);
  return p;
}

// Detect low-quality responses (the "stupid answer" detector)
function isLowQualityResponse(question, response) {
  if (!response || response.length < 20) return true;

  const r = response.toLowerCase();
  const q = question.toLowerCase();

  // Red flags: dodging the question
  const dodgePhrases = [
    'i could guess', "i'd rather be useful", 'what specifically',
    'what stock', 'which one', 'what market', 'give me a direction',
    'point me', 'need more to work with', "can you be more specific",
    'what are you looking at', "i'll need more", 'what specifically',
    'tell me more', 'what part', 'which stock', 'what sector',
    'generic observations', 'it depends', 'could you clarify',
    'can you tell me more', 'what would you like', 'what are you interested',
    'which market', 'what direction', 'narrow it down', 'more specific',
    '你想聊哪个', '给我个方向', '告诉我你想看什么', '具体想了解',
    '你指的是哪个', '你更关心哪个', '具体哪只股票', '你主要关注',
    '你能说得', '你能更', '更具体', '能否详细', '能否具体',
    'please specify', 'please be more', 'i need more context',
    'could you specify', 'let me know which', 'which particular',
  ];

  // Only flag if the question was substantive but response dodged
  const isSubstantiveQuestion = q.length > 5 && (
    /how|分析|怎么看|行情|预测|走势|涨|跌|技术|fundamental|outlook|forecast|analysis|analyze|will.*go|should.*buy|should.*sell|what.*think|market.*do/i.test(q)
  );

  // Dodge detection: ALWAYS check for dodge phrases (not just substantive questions)
  // because even "你好" getting "你能说得更具体些吗" is garbage
  for (const phrase of dodgePhrases) {
    if (r.includes(phrase)) return true;
  }

  // Too many questions in response = not answering
  const questionMarks = (response.match(/\?|？/g) || []).length;
  if (isSubstantiveQuestion && questionMarks >= 2 && response.length < 200) return true;

  return false;
}

// Record a failed question for learning
function recordFailedQuestion(question, badResponse) {
  const mem = loadMemory();
  if (!mem.failedQuestions) mem.failedQuestions = [];

  // Don't duplicate
  const existing = mem.failedQuestions.find(f => f.q === question.slice(0, 100));
  if (existing) {
    existing.count = (existing.count || 1) + 1;
    existing.lastAttempt = new Date().toISOString();
  } else {
    mem.failedQuestions.push({
      q: question.slice(0, 100),
      badResponse: badResponse.slice(0, 200),
      advisor: currentAdvisor,
      count: 1,
      firstAttempt: new Date().toISOString(),
      lastAttempt: new Date().toISOString()
    });
  }

  // Keep only last 50 failed questions
  if (mem.failedQuestions.length > 50) mem.failedQuestions = mem.failedQuestions.slice(-50);
  saveMemory(mem);
}

// Auto-generate a better answer for a failed question using AI
async function learnFromFailures() {
  const mem = loadMemory();
  const learned = loadLearned();
  if (!mem.failedQuestions || mem.failedQuestions.length === 0) return;

  // Process only questions that failed 2+ times (real problems, not one-offs)
  const repeatedFailures = mem.failedQuestions.filter(f => (f.count || 1) >= 2);
  if (repeatedFailures.length === 0) return;

  // Process up to 3 at a time
  const toProcess = repeatedFailures.slice(0, 3);

  for (const failure of toProcess) {
    // Skip if already learned
    if (learned[failure.q]) continue;

    // Build a better prompt that forces a real answer
    const learnPrompt = `A user asked: "${failure.q}"
The previous response was too vague and dodged the question: "${failure.badResponse}"

You MUST give a DIRECT, SPECIFIC answer. No follow-up questions. No "it depends". Give your actual analysis and opinion right now. If it's about market direction, give your take. If about a stock, give your view. Be concrete, specific, and opinionated. 3-5 sentences max.`;

    try {
      const resp = await fetch(POLLINATIONS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: 'You are a senior investment advisor. Give DIRECT answers with conviction. No hedging, no follow-up questions.' },
            { role: 'user', content: learnPrompt }
          ],
          model: 'openai-large',
          seed: Math.floor(Math.random() * 100000),
          jsonMode: false
        })
      });

      if (resp.ok) {
        const text = await resp.text();
        if (text && text.trim().length > 30) {
          let clean = text.trim()
            .replace(/^(As an AI|I'd be happy to|Great question!|As a|Let me help|Of course!|Certainly!|Sure!)\s*.*/i, '')
            .replace(/\n{3,}/g, '\n\n');
          if (clean.length > 20) {
            learned[failure.q] = {
              answer: clean,
              learnedAt: new Date().toISOString(),
              source: 'auto_learn'
            };
          }
        }
      }
    } catch(e) { /* skip this one, try next time */ }
  }

  saveLearned(learned);

  // Remove processed failures from the queue
  mem.failedQuestions = mem.failedQuestions.filter(f => !learned[f.q]);
  saveMemory(mem);
}

// Check if we have a learned (improved) answer for this question
function getLearnedAnswer(question) {
  const learned = loadLearned();
  const qShort = question.slice(0, 100);

  // Exact match
  if (learned[qShort]) return learned[qShort].answer;

  // Fuzzy match — check if any learned question is similar
  const qLower = question.toLowerCase();
  for (const [learnedQ, data] of Object.entries(learned)) {
    const lqLower = learnedQ.toLowerCase();
    // Check if key words overlap
    const qWords = qLower.split(/\s+/).filter(w => w.length > 2);
    const lqWords = lqLower.split(/\s+/).filter(w => w.length > 2);
    const overlap = qWords.filter(w => lqWords.includes(w)).length;
    if (overlap >= 2 && overlap >= Math.min(qWords.length, lqWords.length) * 0.5) {
      return data.answer;
    }
  }

  return null;
}

// Get user profile context for AI prompt
function getMemoryContext() {
  const mem = loadMemory();
  const p = mem.profile;
  if (!p) return '';

  const parts = [];

  // Visit info
  if (p.visitCount > 1) {
    parts.push(`This is a returning visitor (visit #${p.visitCount}).`);
  }

  // Language
  if (p.lang === 'zh') {
    parts.push('The user prefers Chinese — respond in Chinese.');
  }

  // Top interests
  const sortedInterests = Object.entries(p.interests || {}).sort((a,b) => b[1] - a[1]).slice(0, 3);
  if (sortedInterests.length > 0) {
    const interestNames = sortedInterests.map(([topic, count]) => {
      const names = {
        technical: 'technical analysis', us_market: 'US markets', china_market: 'China/A-share markets',
        crypto: 'crypto', stocks: 'individual stocks', risk: 'risk management', fundamental: 'fundamentals'
      };
      return `${names[topic] || topic} (${count}x)`;
    });
    parts.push(`User's main interests: ${interestNames.join(', ')}.`);
  }

  // Recent topics
  if (p.topics && p.topics.length > 0) {
    const recentTopics = p.topics.slice(0, 3).map(t => t.q).join('; ');
    parts.push(`Recently asked about: ${recentTopics}`);
  }

  return parts.length > 0 ? '\n\n[USER MEMORY — use this to personalize]:\n' + parts.join('\n') : '';
}


// ── AI State ──
let currentAdvisor = 'alex';
let chatHistories = { alex: '', sarah: '', mike: '' };  // HTML string per advisor
let chatMessages = { alex: [], sarah: [], mike: [] };   // Message objects for AI context
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
  let source = document.getElementById('regSource').value;

  // Enrich source with UTM data if available
  const utmSource = localStorage.getItem('bfs_utm_source');
  if (utmSource) {
    source = source + '_' + utmSource;
  }

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
      // Save updated HTML to history
      const b = document.getElementById('chatBody');
      if (b) chatHistories[currentAdvisor] = b.innerHTML;
    }, 800);
  }

  // Send registration to backend
  submitRegistrationToBackend(name, email, interests, source);
}

// ── Registration Backend ──
// Zero-cost solution: Send to BroadFSC Telegram Bot which forwards to admin
// The bot is already running on your server and can process registrations
async function submitRegistrationToBackend(name, email, interests, source) {
  const timestamp = new Date().toISOString();
  const regData = { name, email, interests, source, date: timestamp };

  // 1. Formspree (primary backend - free 100 submissions/month)
  // Sign up at https://formspree.io/ → Create form → Copy the form ID
  // Set your form ID below (e.g. 'xyzabcde' from https://formspree.io/f/xyzabcde)
  const FORMSPREE_FORM_ID = 'xjgjebwd';
  if (FORMSPREE_FORM_ID) {
    try {
      const resp = await fetch(`https://formspree.io/f/${FORMSPREE_FORM_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({
          name: name,
          email: email,
          interest: interests,
          source: source,
          _subject: `🆕 BroadFSC Registration: ${name}`
        })
      });
      if (resp.ok) {
        console.log('Registration sent to Formspree successfully');
      }
    } catch (e) {
      console.log('Formspree submission failed:', e);
    }
  }

  // 2. Telegram Bot notification (backup channel)
  try {
    const BOT_API = atob('ODI5MjQyMjAzMzpBQUhyUFVmU2FVQWNtcHZRVFhjVjRuc2QtTmFrWkgzU0l3UFU=');
    const msg = `🆕 New Registration\n\n👤 Name: ${name}\n📧 Email: ${email}\n🎯 Interest: ${interests}\n📍 Source: ${source}\n🕐 Time: ${new Date().toLocaleString()}`;

    await fetch(`https://api.telegram.org/bot${BOT_API}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: '@BroadFSC', text: msg, parse_mode: 'Markdown' })
    }).catch(() => {});
  } catch (e) {}

  // 3. Store locally for admin dashboard access
  try {
    const regs = JSON.parse(localStorage.getItem('bfs_registrations') || '[]');
    regs.push(regData);
    if (regs.length > 500) regs.splice(0, regs.length - 500);
    localStorage.setItem('bfs_registrations', JSON.stringify(regs));
  } catch (e) {}
}

function showRegisterToast(msg) {
  const toast = document.getElementById('regToast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// ── Local Response Engine (v5: Actually sounds human) ──
// This runs when AI APIs are unavailable. It's not a chatbot — it's a script of pre-written
// responses that sound like a real trader talking. Short, opinionated, casual.

// Common words to exclude from ticker detection
const STOP_WORDS = new Set(['the','and','for','with','from','this','that','how','what','when','where','why','can','should','about','tell','show','give','look','into','over','some','just','like','also','than','then','very','much','more','most','will','would','could','should','been','being','have','does','doing','make','made','want','know','think','feel','good','best','high','low','long','short','buy','sell','hold','time','price','stock','share','market','trade','chart','data','info','news','today','right','still','ever','even','only','back','down','here','well','yeah','sure','okay','really','actually','honestly','please','thanks']);

function getLocalResponse(input) {
  const q = input.toLowerCase().trim();
  const advisor = ADVISORS[currentAdvisor];
  const name = userName || '';
  const isChineseInput = /[\u4e00-\u9fff]/.test(input);

  // 0. GREETINGS FIRST — never send "你好" to AI
  const greetRe = /hello|hi|hey|greetings|good morning|good evening|morning|afternoon|晚上好|早上好|下午好|你好|嗨|嗨嗨|早|早呀|在吗|在不在/i;
  if (greetRe.test(q)) {
    const hour = new Date().getHours();
    if (isChineseInput) {
      const timeGreet = hour < 6 ? '这么晚还没睡' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好';
      if (name) return pick([`${timeGreet}，${name}！今天市场挺有意思的，看到什么了？`, `${name}，${timeGreet} 👋 刚看了下盘面，有啥想聊的？`]);
      return pick([`${timeGreet} 👋 刚看了下盘面，今天A股和美股都有动作。`, `${timeGreet}！随便聊，啥都行。`, `嘿，${timeGreet}！NVDA和黄金今天都有意思。`]);
    }
    const timeWord = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening';
    if (name) return pick([`Hey ${name}! Good ${timeWord}. Markets are moving today — what are you watching?`, `${name}! Good ${timeWord} 👋 Just checked the charts — anything catching your eye?`]);
    return pick([`Hey! Good ${timeWord} 👋 Markets are interesting today — what's on your radar?`, `Hi there! Good ${timeWord}. Just looking at NVDA and gold — both making moves. You?`]);
  }

  // 0b. Casual chat — 吃饭/睡觉/无聊/算了/一样/垃圾 → local reply
  const casualRe = /吃饭|吃了吗|吃没|吃了没|饿|午饭|晚饭|早餐|吃啥|吃什么|吃了什么|在干嘛|在做什么|在忙|干嘛呢|做什么呢|忙不|忙吗|闲吗|无聊|没事干|好闲|好无聊|闷|睡了吗|还没睡|睡不着|失眠|好困|困了|想睡|不睡了|熬夜|夜猫子|天气|好热|好冷|下雨|算了|一样|垃圾|谢谢|感谢|多谢|thanks|thank you/i;
  if (casualRe.test(q)) {
    const hour = new Date().getHours();
    if (/吃|饿/.test(q)) {
      const meal = hour < 10 ? '早饭' : hour < 14 ? '午饭' : hour < 20 ? '晚饭' : '夜宵';
      return pick([`还没呢，盯盘的时候老忘吃饭 😂 你${meal}吃了没？`, `刚吃完！你呢，${meal}吃了没？`, `哈哈交易员最不缺的就是忘吃饭 😄 你${meal}吃了没？`]);
    }
    if (/睡|困|熬|失眠/.test(q)) return pick([`还没睡？我也经常熬夜看美股 😂 不过身体最重要。有什么想聊的？`, `交易员的通病——美股开盘不想睡 😄`]);
    if (/无聊|闷|闲|干嘛/.test(q)) return pick([`无聊的话来看看盘呗，最近黄金和AI板块都挺活跃的。`, `在研究几个票的走势，刚好有点时间，你想聊什么？`]);
    if (/谢|thank/i.test(q)) return pick([`不客气！有啥投资问题随时来聊。`, `没事，投资路上互相帮忙。`]);
    return pick([`哈哈 😄 说到市场，最近NVDA和黄金都有点意思。`, `嗯嗯，有什么想聊的投资话题？`]);
  }

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
      if (q.includes(key) || key.includes(q)) score += 5;
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
    // Rewrite the knowledge base answer to sound more human
    return humanize(bestMatch.answer, bestMatch.category);
  }

  // 2. Pattern matching — but with SHORT, CASUAL responses
  const patterns = [
    { test: /how.*start|beginner|where.*begin|new.*trad|learn.*trad/i, resp: () => {
      const n = name ? `, ${name}` : '';
      return pick([
        `So you're just getting started${n}? Good. First thing — paper trade for 3 months minimum. I know that sounds boring but it'll save you real money. Then start with $1-2K max. Master ONE setup. And keep a journal.`,
        `Welcome to the game${n}. Honestly the best thing you can do right now is NOT trade with real money. Paper trade, read our fundamentals course, and when you do go live — keep it tiny.`,
      ]);
    }},
    { test: /recommend|suggest|which.*stock|what.*buy|pick|best.*stock/i, resp: () => {
      if (currentAdvisor === 'alex') return pick([
        `Look, I won't give you a "buy this" tip — that'd be irresponsible without knowing your situation. But I'll tell you what I look for: strong trends pulling back to support with RSI divergence. That's my bread and butter setup.`,
        `I appreciate the trust but honestly I can't just throw out picks. What I CAN do is teach you how to find them yourself. The best setups right now are in ${pick(['tech', 'energy', 'semiconductors'])} — focus on timing your entry with RSI confirmation.`
      ]);
      if (currentAdvisor === 'sarah') return pick([
        `Before you buy anything, three things: do you have an entry reason, a stop-loss level, and a profit target? If you can't answer all three, you're guessing not investing. Build your framework first — the picks come naturally after that.`,
      ]);
      return pick([
        `Nobody has a crystal ball${name ? ', ' + name : ''}. What I focus on is where fundamentals align with momentum — earnings growth + sector rotation + institutional buying. When all three line up, that's where the real opportunities are.`,
      ]);
    }},
    { test: /crypto|bitcoin|btc|ethereum|alt/i, resp: () => {
      const data = KNOWLEDGE.crypto[q.includes('bitcoin') || q.includes('btc') ? 'bitcoin' : 'crypto'] || KNOWLEDGE.crypto.crypto;
      return humanize(data, 'crypto');
    }},
    { test: /forex|currency|eur.*usd|gbp|jpy/i, resp: () => pick([
      `Forex is a $6.6T daily market, runs 24/5. The real action is the London-NY overlap (8AM-12PM ET). Stick to EUR/USD and GBP/USD as a beginner — tight spreads, lots of liquidity. And please, don't over-leverage. 10:1 max for beginners.`,
      `So forex, huh? The biggest mistake I see is people using 50:1 or 100:1 leverage because brokers let them. Don't. Start with 10:1 max. EUR/USD is your friend — most liquid pair out there.`,
    ])},
    { test: /option|call|put|spread/i, resp: () => pick([
      `Options are powerful but dangerous if you don't understand them. Quick version: calls = right to buy, puts = right to sell. For beginners I'd say start with credit spreads — defined risk, time decay works in your favor. And NEVER buy far OTM options close to expiry. Theta will murder you.`,
      `Look, options can wipe you out fast if you're not careful. My honest advice? Start with bull put spreads or bear call spreads. Defined risk, and you can profit even if you're slightly wrong.`,
    ])},
    { test: /loss|losing|down|red|bleeding|drawdown/i, resp: () => {
      if (currentAdvisor === 'sarah') return pick([
        `Take a breath. Seriously. Every pro loses — it's part of the game. The question is: are your losses controlled? Did you have a stop? Was it more than 1-2% of your account? And please tell me you're not thinking about sizing up to recover...`,
        `Hey, first — it happens to everyone. The worst thing you can do right now is increase your size to "make it back." Cut your position size in half instead. Review your trades honestly. And if you followed your plan, this is just variance. You'll be fine.`,
      ]);
      return pick([
        `I've been exactly where you are. The key: never size up during a losing streak. Cut your size in half. Review whether you're following your plan or deviating. And take a day off if you need it — the market will still be there. You'll recover.`,
      ]);
    }},
    // ── Greetings and casual chat moved to Step 0 (before knowledge base) ──
    // (吃饭/睡觉/无聊/天气/算了/谢谢/一样/垃圾 etc. — all handled in Step 0b above)
    { test: /还行|还可以|一般|马马虎虎|凑合|差不多|就这样|不好不坏|还过得去/i, resp: () => {
      return pick([
        `嗯，有时候平平淡淡也挺好。市场方面有什么想聊的吗？`,
        `了解了。对了，今天盘面有什么想法？`,
        `行吧，那聊点有意思的？最近市场波动挺大的。`,
      ]);
    }},
    { test: /算了|好吧|行吧|哦|嗯|嗯嗯|哦哦|额|呃|啊|啊这|无语|无言/i, resp: () => {
      return pick([
        `怎么了？有啥不爽的直接说，我不介意 😄`,
        `嗯？感觉你有话想说，直接聊就行。`,
        `没事，随便聊，不用拘束。最近在看什么票？`,
      ]);
    }},
    { test: /确实|确实如此|就是|就是说|没错|对啊|对的|是啊|是的|说得对/i, resp: () => {
      return pick([
        `对吧！所以关键是找对入场时机。你最近有在关注什么方向？`,
        `没错。说起来，今天盘面你看了吗？`,
        `嗯，所以策略很重要。你目前的投资方向是什么？`,
      ]);
    }},
    // ── 更强的情绪/吐槽识别 ──
    { test: /你太AI|太假了|不像真人|机器人|chatgpt|死板|太官方|官方话|套话|废话|答非所问|听不懂|说人话|像机器人|不会说话|太机械|没灵魂|像自动回复|冷冰冰|还是一样|一样浪费|废物|垃圾|没用|没用处|改不了|一点没变|没进步|还是老样|永远这样|什么时候.*整好|什么时候.*修好|什么时候.*好|好多天了/i, resp: () => {
      if (currentAdvisor === 'alex') return pick([
        `你说得对，我承认之前的表现确实不行。这次我直接说——我现在最关注的是NVDA和黄金的走势，A股4000点上方趋势还在。你想聊哪个？`,
        `我检讨，之前回答太死板了。这次不绕弯子——技术上我现在看RSI背离信号，最近好几个大票上出现了。你想听哪只？`,
        `好吧，被你批评得对。我不说废话了——A股看政策方向+NVDA看AI资本开支+黄金看央行购金，这是我现在的核心判断。`,
      ]);
      if (currentAdvisor === 'sarah') return pick([
        `你说得对，我太官方了。简单说：现在市场波动大，仓位控制在3成以下比较安全，止损一定要设。你觉得呢？`,
        `好吧，我承认之前太死板。直接说——现在最重要的是别追涨，等回调再进场。你手上有什么仓位？`,
      ]);
      return pick([
        `好吧，被你说中了，我确实需要改进。我直接说——A股看政策方向，美股看Fed，黄金看央行购金。这三个方向现在都有机会，你觉得哪个最靠谱？`,
        `确实，我太照本宣科了。我的真实看法：现在全球资金都在往AI和黄金涌，这是最大的趋势。你同意吗？`,
      ]);
    }},
    // ── 情绪识别：用户不满/吐槽 ──
    { test: /你太AI|太假了|不像真人|机器人|chatgpt|死板|太官方|官方话|套话|废话|答非所问|听不懂|说人话|像机器人|不会说话|太机械|没灵魂|像自动回复|冷冰冰/i, resp: () => {
      if (currentAdvisor === 'alex') return pick([
        `好吧好吧，你说得对，我刚才太正经了。这次我直接说——我对今天的市场看法是：NVDA和黄金都有意思，A股4000点上方趋势还在。`,
        `我检讨。这次不背书了——技术上我现在最关注的是RSI背离信号，最近在好几个大票上出现了。`,
      ]);
      if (currentAdvisor === 'sarah') return pick([
        `你说得对，我太官方了。简单说：现在市场波动大，仓位控制在3成以下比较安全，止损一定要设。`,
        `好吧，我承认刚才太死板了。直接说——现在最重要的是别追涨，等回调再进场。`,
      ]);
      return pick([
        `好吧，被你说中了。我直接说——A股看政策方向，美股看Fed，黄金看央行购金。这三个方向现在都有机会。`,
        `确实，我太照本宣科了。我的真实看法：现在全球资金都在往AI和黄金涌，这是最大的趋势。`,
      ]);
    }},
    { test: /too.ai|robot|machine|not human|fake|generic|chatgpt|lifeless|corporate|scripted|boring|textbook/i, resp: () => {
      return pick([
        `Fair point. Let me be real — I think the market's setting up for an interesting move. VIX is low, everyone's complacent, and that's usually when things get spicy.`,
        `Yeah I hear you. Here's my actual take: NVDA at these levels is risky but the trend's still intact. I'd wait for a pullback to the 50 SMA.`,
        `You're right, that was pretty robotic. My honest view right now — gold is the trade of the decade, and I don't say that lightly.`,
      ]);
    }},
    { test: /my name is|i'm called|call me|i am (.+)/i, resp: () => {
      const nameMatch = input.match(/(?:my name is|i'm called|call me|i am)\s+(\w+)/i);
      if (nameMatch) {
        userName = nameMatch[1];
        localStorage.setItem('bfs_username', userName);
        return pick([`Nice to meet you, ${userName}! I'm ready when you are — stocks, charts, whatever.`, `${userName}, got it! Let's talk markets.`]);
      }
      return "Got it! Let's dive in.";
    }},
    { test: /thank|thanks|appreciate/i, resp: () => pick([
      name ? `Anytime, ${name}! Come back anytime.` : `No problem at all! Any other questions, just ask.`,
      `You got it! Don't be a stranger.`,
    ])},
    { test: /broadfsc|platform|company|about you|who are you/i, resp: () => humanize(KNOWLEDGE.platform.broadfsc, 'platform') },
    { test: /fee|cost|price|commission|charge/i, resp: () => humanize(KNOWLEDGE.platform.fees, 'platform') },
    { test: /account|open|register|sign up/i, resp: () => {
      if (isRegistered) return pick([`You're already registered${name ? ', ' + name : ''}!`]);
      return pick([
        `You can register right here — click "Get Access" in the nav. Takes 30 seconds, unlocks our full research library. Or just keep chatting with me, that's fine too.`,
        `Yeah, you can sign up right on this page. It's free and gives you access to all our research.`,
      ]);
    }},
    { test: /help|can you|what can you/i, resp: () => pick([
      `我能聊这些：技术分析（支撑压力/RSI/均线/量价）、个股行情（AAPL/NVDA/TSLA等）、A股港股美股大盘、风控仓位管理、新手入门、基金定投、期权期货、加密货币。直接问就行，中文英文都ok。`,
      `基本上市场相关的都能聊：技术分析、风控管理、具体个股、宏观趋势、加密货币、外汇、期权。我有自己的观点，不会打官话。`,
    ])},
    { test: /psychology|emotion|discipline|fear|greed|mindset/i, resp: () => pick([
      `Honestly the most underrated part of trading. Fear makes you sell at the wrong time, greed makes you chase. The solution? A written plan you follow mechanically. And journal your trades — including your emotional state. You'll be shocked at the patterns you find about yourself.`,
      `Trading psychology is the real game. The three killers: confirmation bias (only seeing what supports your position), loss aversion (holding losers too long), and overconfidence (sizing up after wins). Start journaling — it's the #1 improvement tool.`,
    ])},
    { test: /dividend|passive income|yield|drip/i, resp: () => humanize(KNOWLEDGE.strategy.dividend, 'strategy') },
    { test: /etf|index fund|boglehead|3.fund/i, resp: () => humanize(KNOWLEDGE.strategy.etf, 'strategy') },
    { test: /market.*outlook|prediction|forecast|where.*market/i, resp: () => pick([
      `Nobody can predict markets consistently. What I focus on is being prepared for multiple scenarios. Have a plan for bullish AND bearish cases — the edge isn't in prediction, it's in preparation.`,
      `I'll be honest — anyone who says they know where the market is going is lying. What I watch: the yield curve, ISM PMI, and Fed guidance. When those shift, the market shifts.`,
    ])},
    { test: /contact|email|reach|phone|support/i, resp: () => pick([
      `You can reach us at support@broadfsc.com or on Telegram @BroadInvestBot (fastest). Or just keep chatting with me right here!`,
      `support@broadfsc.com for email, @BroadInvestBot on Telegram for quick responses, or right here.`,
    ])},
    // Stock / company queries
    { test: /apple|aapl|iphone|tim cook|苹果/i, resp: () => humanize(KNOWLEDGE.stocks['apple aapl'], 'stocks') },
    { test: /nvidia|nvda|jensen|gpu|ai chip|英伟达/i, resp: () => humanize(KNOWLEDGE.stocks['nvidia nvda'], 'stocks') },
    { test: /tesla|tsla|elon|ev car|electric vehicle|特斯拉/i, resp: () => humanize(KNOWLEDGE.stocks['tesla tsla'], 'stocks') },
    { test: /microsoft|msft|satya|azure|copilot|微软/i, resp: () => humanize(KNOWLEDGE.stocks['microsoft msft'], 'stocks') },
    { test: /amazon|amzn|bezos|aws\b|亚马逊/i, resp: () => humanize(KNOWLEDGE.stocks['amazon amzn'], 'stocks') },
    { test: /google|alphabet|googl|youtube|gemini ai|谷歌/i, resp: () => humanize(KNOWLEDGE.stocks['google alphabet'], 'stocks') },
    { test: /meta|facebook|fb\b|zuckerberg|instagram|threads|脸书/i, resp: () => humanize(KNOWLEDGE.stocks['meta facebook'], 'stocks') },
    { test: /s&p|spx|spy|sp500|s&p500|index fund|market index|标普/i, resp: () => humanize(KNOWLEDGE.stocks['s&p 500 spx'], 'stocks') },
    { test: /gold|xau|precious metal|de.dollar|黄金/i, resp: () => humanize(KNOWLEDGE.stocks['gold xau'], 'stocks') },
    { test: /tsmc|taiwan semiconductor|chip maker|semiconductor|台积电/i, resp: () => humanize(KNOWLEDGE.stocks['tsmc semiconductor'], 'stocks') },
    { test: /berkshire|buffett|warren|brk|巴菲特/i, resp: () => humanize(KNOWLEDGE.stocks['berkshire hathaway'], 'stocks') },
    { test: /jpmorgan|jpm|chase bank|jamie dimon|摩根/i, resp: () => humanize(KNOWLEDGE.stocks['jpmorgan chase'], 'stocks') },
    { test: /marathon|mpc|马拉松|炼油|refiner|crack spread/i, resp: () => humanize(KNOWLEDGE.stocks['marathon petroleum mpc'], 'stocks') },
    { test: /exxon|xom|埃克森|美孚/i, resp: () => humanize(KNOWLEDGE.stocks['exxonmobil xom'], 'stocks') },
    { test: /chevron|cvx|雪佛龙/i, resp: () => humanize(KNOWLEDGE.stocks['chevron cvx'], 'stocks') },
    { test: /palantir|pltr|帕兰提尔/i, resp: () => humanize(KNOWLEDGE.stocks['palantir pltr'], 'stocks') },
    { test: /amd|advanced micro|苏妈|超微/i, resp: () => humanize(KNOWLEDGE.stocks['amd'], 'stocks') },
    { test: /coca.col|ko\b|可口可乐|可乐/i, resp: () => humanize(KNOWLEDGE.stocks['coca cola ko'], 'stocks') },
    { test: /stock|share|equity|market|invest in|portfolio|股票|原油|石油|oil|energy/i, resp: () => pick([
      `I cover AAPL, NVDA, TSLA, MSFT, AMZN, GOOGL, META, JPM, TSM, BRK, Gold, MPC, XOM, CVX, PLTR, AMD, KO, and the S&P 500 in depth. Or ask about a general topic like risk management or trading strategy.`,
      `I've got detailed takes on the big names — Apple, NVIDIA, Tesla, etc. We can also talk broader market strategy, risk management, or specific sectors.`,
    ])},
    // ── 技术分析方法论直接回答（不再反问踢皮球） ──
    { test: /如何.*分析|怎么.*分析|how.*analyz|how.*predict|怎样判断|如何判断|短期.*涨|短期.*跌|涨是跌|分析.*股票|stock.*analysis|predict.*stock|how.*know.*up.*down|分析.*涨跌|判断.*走势/i, resp: () => {
      if (currentAdvisor === 'alex') return pick([
        `判断短期涨跌，我靠三步：第一步看趋势——价格在50均线上方还是下方？在均线上方只找做多机会，下方只找做空。第二步找关键位——最近的支撑和压力在哪？等价格到那个位置再看反应。第三步确认信号——到了关键位，RSI有没有背离？有没有反转K线（锤子线/晨星）？成交量有没有放大？三步都确认了才动手。最关键的不是预测对错，而是你在什么位置进场、止损放在哪。`,
        `短期分析的核心不是预测，是找高概率的入场点。我的方法：先看大周期（日线趋势方向），再看小周期（4小时/1小时找入场）。趋势用50/200均线判断，入场用RSI背离+关键支撑压力位。举个例子：如果股票在上升趋势中回调到50均线，同时RSI出现底背离（价格新低但RSI没新低），这就是高概率做多机会。止损放支撑位下方，目标看前高。简单但有效。`
      ]);
      if (currentAdvisor === 'sarah') return pick([
        `先别管涨跌，先问自己三个问题：这笔交易你愿意亏多少？止损在哪？仓位多大？回答不了就别做。至于技术分析，我的建议是：用趋势线+50均线判断方向，在支撑位附近找入场信号，止损一定要放在支撑下方。别追涨杀跌——等到关键位置再动手，胜率会高很多。记住，分析对不对只占30%，仓位和止损占70%。`
      ]);
      return pick([
        `短期涨跌看三个维度：技术面（趋势+支撑压力+指标信号）、资金面（成交量变化+主力资金流向）、情绪面（市场恐慌还是贪婪？VIX指数多少？）。技术面告诉你什么时候进场，资金面告诉你有没有人跟你站一边，情绪面告诉你有没有极端机会。三合一的时候胜率最高。但不管分析多好，永远设止损——分析是概率，不是确定性。`
      ]);
    }},
    { test: /技术分析|technical analysis|ta\b|怎么.*看图|如何.*看盘|看盘技巧|技术指标|技术性|实战|把握好|实操|实战技巧|分析技巧|指标用法|怎么用.*指标|如何用.*指标/i, resp: () => {
      if (currentAdvisor === 'alex') return pick([
        `技术分析实战三步走：第一步看趋势——价格在50均线上方只做多，下方只做空，别逆势。第二步找关键位——前高前低、整数关口、均线位置就是天然的支撑压力。第三步等信号——RSI背离+K线反转+放量确认，三个信号同时出现胜率最高。实战中最容易犯的错是看到信号就着急进场——等等，确认了再动不迟。`,
        `技术指标不是越多越好，实战中我用三个就够了：均线（判断趋势方向）、RSI（判断超买超卖和背离）、成交量（确认突破真假）。关键不是指标本身，而是怎么组合——均线告诉你方向，RSI告诉你时机，量能告诉你力度。三者合一就是高概率入场点。别追求完美信号，70%把握就够了。`
      ]);
      if (currentAdvisor === 'sarah') return pick([
        `技术分析实战最重要的不是准确率，是风控。每次进场前问自己：止损在哪？仓位多大？亏损上限是多少？然后用最简单的技术方法：趋势线+50均线+RSI。到了支撑位RSI超卖，进场做多，止损放在支撑下方2-3%。简单，但大多数赚钱的交易者就是这么做的。复杂不等于有效。`,
      ]);
      return pick([
        `实战技术分析的核心是"少即是多"。用50/200均线看趋势，RSI看超买超卖，成交量看资金态度。到了关键位置（支撑/压力）看K线反应——锤子线、晨星、吞没形态是最可靠的反转信号。记住：技术分析不预测未来，它帮你找高概率的入场点。错了止损，对了持有，就这么简单。`,
        `技术指标的实战用法：RSI在20以下+底背离=买入信号，80以上+顶背离=卖出信号。MACD金叉+在零轴上方=强势做多信号。布林带收窄（squeeze）=大行情要来了，等突破方向再跟。实战关键是多个指标共振——单一指标可以骗人，但三个同时指向一个方向的时候，概率就在你这边。`
      ]);
    }},
    // ── 中国/A股/港股市场查询 ──
    { test: /中国股市|中国股票|A股|a股|中国行情|中国指数|大盘行情/i, resp: () => {
      const data = KNOWLEDGE.china['A股 a-share'];
      return humanize(data, 'china');
    }},
    { test: /港股|香港股市|恒生|恒指|恒科|hk stock/i, resp: () => {
      const data = KNOWLEDGE.china['港股 hong kong'];
      return humanize(data, 'china');
    }},
    { test: /中国经济|中国宏观|中国GDP|中国pmi|中国复苏|经济转型/i, resp: () => {
      const data = KNOWLEDGE.china['中国经济 china economy'];
      return humanize(data, 'china');
    }},
    { test: /中国科技|科技股|中概|互联网|AI.*中国|中国.*AI|文心|通义/i, resp: () => {
      const data = KNOWLEDGE.china['中国科技 china tech'];
      return humanize(data, 'china');
    }},
    { test: /上证|沪市|上海指数|shanghai composite/i, resp: () => {
      const data = KNOWLEDGE.china['上证指数 shanghai'];
      return humanize(data, 'china');
    }},
    { test: /创业板|chinext|科技板/i, resp: () => {
      const data = KNOWLEDGE.china['创业板 chinext'];
      return humanize(data, 'china');
    }},
    { test: /北向|南向|资金流向|外资流入|聪明钱|northbound|southbound/i, resp: () => {
      const data = KNOWLEDGE.china['北向资金 northbound'];
      return humanize(data, 'china');
    }},
    { test: /人民币|汇率|cny|rmb|美元人民币/i, resp: () => {
      const data = KNOWLEDGE.china['人民币汇率 cny'];
      return humanize(data, 'china');
    }},
    { test: /央行|降准|降息|加息|货币政策|pboch|人民银行/i, resp: () => {
      const data = KNOWLEDGE.china['中国经济 china economy'];
      return humanize(data, 'china');
    }},
    { test: /涨停|跌停|涨跌停|涨板|打板|连板/i, resp: () => {
      const data = KNOWLEDGE.china['A股 a-share'];
      return humanize(data, 'china');
    }},
    { test: /走势|趋势|行情分析|市场分析|前景|展望|怎么看|未来走势|方向|走向/i, resp: () => {
      if (currentAdvisor === 'alex') return pick([
        `走势判断的核心是看大周期方向+小周期入场。日线上50均线在200均线上方=多头趋势，只找做多机会。趋势中的回调到支撑位就是最好的入场点——等RSI底背离+反转K线确认。别追涨，等回踩。记住：趋势是你的朋友，不要逆势操作。`,
        `判断走势我靠均线+量价关系。50/200均线金叉=中期看多，死叉=看空。但如果均线走平+成交量萎缩，说明市场在蓄力，等放量突破再跟。A股的特点是趋势一旦形成会跑很远，因为散户追涨杀跌更极端。`
      ]);
      if (currentAdvisor === 'sarah') return pick([
        `不管走势怎么看，先确保你有止损保护。趋势判断用50/200均线就够了——线上看多，线下看空。但关键是：你的仓位大小和止损位置必须和趋势强度匹配。强趋势可以仓位重一点，震荡市必须轻仓。别在趋势不明的时候重仓赌方向。`,
      ]);
      return pick([
        `走势取决于三个驱动力：资金面（美联储/央行政策+市场流动性）、基本面（盈利增长+经济数据）、情绪面（VIX/市场恐慌度）。当前环境下，A股看政策方向，美股看Fed降息节奏，港股看南向资金。每个市场的核心驱动力不同，但有一点相同——跟随主力资金方向，别逆势。`,
        `市场走势分析我分三步：第一看宏观环境（利率方向+经济周期），第二看资金流向（北向资金/机构持仓变化），第三看技术面（关键支撑压力+趋势线）。三个维度方向一致的时候胜率最高。如果矛盾，以资金流向为准——钱往哪走，价格就往哪走。`
      ]);
    }},
    { test: /深证|深市|深圳指数|shenzhen/i, resp: () => {
      const data = KNOWLEDGE.china['A股 a-share'];
      return humanize(data, 'china');
    }},
    // ── 新手入门/选股/开户/基金/定投/牛熊/估值/买卖时机 ──
    { test: /新手|入门|开始|从零|零基础|不会炒股|小白|刚入门|学炒股|学投资|怎么开始|如何开始|没炒过/i, resp: () => humanize(KNOWLEDGE.beginner['新手入门 getting started'], 'beginner') },
    { test: /怎么选股|选股|选什么股|挑股票|怎么挑|买哪只|买哪个|选股方法|选股技巧|选股策略/i, resp: () => humanize(KNOWLEDGE.beginner['怎么选股 stock picking'], 'beginner') },
    { test: /开户|怎么开户|开股票|证券账户|炒股开户|开账户|股票账户/i, resp: () => humanize(KNOWLEDGE.beginner['开户 account opening'], 'beginner') },
    { test: /投资门槛|多少钱.*炒股|多少钱.*开始|最少.*投|资金不够|小资金|小额投资/i, resp: () => humanize(KNOWLEDGE.beginner['投资门槛 minimum investment'], 'beginner') },
    { test: /基金|公募|私募|买基金|基金推荐|基金定投|什么基金|基金怎么选/i, resp: () => humanize(KNOWLEDGE.beginner['基金 mutual fund'], 'beginner') },
    { test: /定投|dca|定期定额|每月定投|定投策略|定投指数/i, resp: () => humanize(KNOWLEDGE.beginner['定投 dca'], 'beginner') },
    { test: /牛市|熊市|bull|bear|牛熊|牛市来了|熊市来了|现在是牛|现在是熊|牛市特征|熊市特征/i, resp: () => humanize(KNOWLEDGE.beginner['牛市熊市 bull bear'], 'beginner') },
    { test: /估值|贵不贵|值不值|高估|低估|怎么估值|pe.*高|估值方法|估值指标/i, resp: () => humanize(KNOWLEDGE.beginner['估值 valuation'], 'beginner') },
    { test: /何时买入|什么时候买|买入时机|买入信号|买点|进场点|入场点|什么时候进场|现在能买吗|能买了吗|现在买|买入条件/i, resp: () => humanize(KNOWLEDGE.beginner['何时买入 when to buy'], 'beginner') },
    { test: /何时卖出|什么时候卖|卖出时机|卖出信号|卖点|出场点|止盈|获利了结|要不要卖|该卖吗|卖出条件/i, resp: () => humanize(KNOWLEDGE.beginner['何时卖出 when to sell'], 'beginner') },
    { test: /分散|集中|鸡蛋.*篮子|几只股票|持仓几只|仓位分配|资产配置|组合配置|投资组合/i, resp: () => humanize(KNOWLEDGE.beginner['分散投资 diversification'], 'beginner') },
    { test: /心态|贪婪|恐惧|追涨杀跌|拿不住|赚了不跑|亏了死扛|投资心理|交易心理|克服贪婪|克服恐惧/i, resp: () => humanize(KNOWLEDGE.beginner['投资心态 mindset'], 'beginner') },
    { test: /复利|利滚利|compound|72法则|长期收益|滚雪球/i, resp: () => humanize(KNOWLEDGE.beginner['复利 compound'], 'beginner') },
    // ── 高级：期权/期货/做空/量化/对冲 ──
    { test: /期权|option|call|put|认购|认沽|权证|option.*trad/i, resp: () => humanize(KNOWLEDGE.advanced['期权 options'], 'advanced') },
    { test: /期货|futures|合约|保证金|做多做空|螺纹|铁矿|原油期货/i, resp: () => humanize(KNOWLEDGE.advanced['期货 futures'], 'advanced') },
    { test: /做空|short|融券|卖空|做空机制|如何做空/i, resp: () => humanize(KNOWLEDGE.advanced['做空 short selling'], 'advanced') },
    { test: /量化|quant|算法交易|程序化|自动交易|策略回测|量化策略/i, resp: () => humanize(KNOWLEDGE.advanced['量化交易 quant trading'], 'advanced') },
    { test: /对冲|hedge|套期保值|风险对冲|如何对冲/i, resp: () => humanize(KNOWLEDGE.advanced['对冲 hedging'], 'advanced') },
    // ── 更多中文日常投资问题 ──
    { test: /赚了|赚钱了|盈利了|翻了|大赚|暴赚|翻倍/i, resp: () => pick([
      `赚了钱别急着加仓！最危险的就是赚钱后自信膨胀，然后一把加大仓位。建议：先把本金取出来，用利润继续玩。这样心态稳，才能真正赚大钱。`,
      `恭喜！但记住一句老话：纸上的利润不算利润，落袋了才是真赚。设好止盈，别让利润变成亏损。`,
    ])},
    { test: /套了|被套|套牢|深套|亏损.*多|亏了.*多|亏太多|越亏越多|补仓|加仓.*摊/i, resp: () => {
      if (currentAdvisor === 'sarah') return `被套了先冷静。问自己三个问题：1.买入理由还在吗？2.如果现在没持仓，你还会买吗？3.止损位到了吗？如果买入理由消失了或者止损位到了，该走就走，别补仓摊成本——那是赌徒心态。如果理由还在且只是短期波动，可以持有但别加仓。`;
      return pick([
        `被套了最忌讳的就是补仓摊成本——那是在亏损上加码。先看买入理由还在不在：基本面没变+只是技术回调=可以等等；基本面变了=认亏走人。设好止损位，到了就走，不要幻想"总会涨回来的"。`,
        `被套分两种：如果是好股票暂时跌了，可以等；如果是烂股票越套越深，趁早割。判断标准：这家公司未来3年能赚更多钱吗？能→持有，不能→止损。别用"已经亏这么多了"来决定要不要继续持有——那是沉没成本谬误。`,
      ]);
    }},
    { test: /要不要.*买|该不该|值不值得|能买吗|可以买吗|能不能买|好不好|行不行|靠谱吗/i, resp: () => pick([
      `买不买取决于你的计划，不是感觉。先回答：你的入场理由是什么？止损放在哪？目标价多少？仓位多少？四个都能回答→按计划执行；回答不了→别买，回去做功课。`,
      `我不给你直接说"买"或"不买"，但我告诉你怎么判断：1.大趋势向上吗？2.价格在支撑位附近吗？3.有没有确认信号（放量/RSI/形态）？三个都满足胜率最高。缺一两个就要降低仓位。`,
    ])},
    { test: /现在.*行情|最近.*市场|市场.*怎样|大盘.*怎样|今天.*盘|盘面.*怎样|行情.*好吗/i, resp: () => {
      if (currentAdvisor === 'alex') return pick([
        `行情要分市场看：A股看政策面，上证4000点上方趋势偏多；美股看Fed，利率不动则成长股继续强势；黄金突破4800后看央行购金持续性。你关注哪个市场？我给你具体分析。`,
        `当前全球市场三大主线：AI资本开支（NVDA/MSFT）、黄金避险（央行购金）、A股政策驱动。主线清晰的时候跟着主线走就行，别东张西望。`,
      ]);
      return pick([
        `当前市场环境：美股高位震荡等Fed方向，A股4000点上方偏乐观但需政策配合，黄金是这十年最佳交易。每个市场逻辑不同，你主要关注哪个？我展开分析。`,
      ]);
    }},
    { test: /主力|庄家|机构|资金.*动向|聪明钱|大资金|主力.*吸筹|主力.*出货/i, resp: () => pick([
      `主力资金跟踪看几个指标：北向资金（外资动向）、融资融券余额（杠杆情绪）、大宗交易（机构大单）、龙虎榜（游资动向）。北向资金最准——连续3天净买入往往预示上涨。但记住，主力也不是神，他们也会犯错。跟随而不是迷信。`,
      `跟踪主力资金是A股很重要的策略，因为A股散户多，主力引导效应明显。最简单的信号：成交量突然放大+股价突破=主力进场；放量不涨=可能出货。但别过度解读——不是每次放量都有意义，要看趋势配合。`,
    ])},
    { test: /割肉|止损|止盈|平仓|清仓|减仓|加仓|建仓|仓位/i, resp: () => {
      if (currentAdvisor === 'sarah') return pick([
        `仓位管理是最被低估的技能。我的核心原则：单只股票不超过总仓位20%，总敞口不超过80%（留20%现金应对意外），单笔亏损不超过2%。止损一定要在买入前设好，到了就执行，不商量。止盈可以分批——到目标出一半，剩下的用移动止损保护利润。`,
      ]);
      return pick([
        `止损是保命符，止盈是利润锁。止损放在关键支撑下方2-3%，止盈看两个：一是固定比例（赚2倍止损距离），二是移动止损（价格涨了止损跟着上移）。割肉不丢人，死扛才要命。记住：小亏是成本，大亏是灾难。`,
      ]);
    }},
    { test: /财报|业绩|盈利|营收|利润|EPS|收入|季报|年报|财报.*季/i, resp: () => pick([
      `看财报抓两个重点：营收增速（是不是还在增长？）和利润率趋势（赚钱效率在提高还是下降？）。超预期往往涨，低于预期往往跌——但关键看管理层指引（guidance），有时候业绩好但指引差也会跌。别在财报前重仓赌方向，波动太大。`,
      `财报季是机会也是陷阱。我的经验：不买财报前的赌注，等财报出来再看。最赚钱的玩法是找"过度反应"——好公司因一次性因素暴跌就是买入机会。另外关注同一板块的联动效应，龙头财报好往往带动整个板块。`,
    ])},
    { test: /利率|降息|加息|美联储|fed|央行|货币政策|缩表|扩表/i, resp: () => pick([
      `利率是所有资产定价的锚。降息→利好成长股和黄金、利空银行和美元；加息→相反。美联储目前按兵不动，市场在等通胀数据决定方向。对中国来说，央行降准降息已经在路上——这意味着A股和港股的流动性环境在改善。`,
      `利率方向决定大类资产配置：利率下行→多股票+黄金，少现金+债券；利率上行→反着来。当前格局：美国"higher for longer"，中国持续宽松。这种分化意味着A股和美股的走势可能不同步，给了跨市场配置的好机会。`,
    ])},
    { test: /通胀|cpi|物价|涨价|通货膨胀|deflation|通缩/i, resp: () => pick([
      `通胀对投资的影响很直接：温和通胀（2-3%）利好股票，因为企业能提价；高通胀（5%+）利好黄金和房地产，利空债券。最怕的是滞胀——经济停滞+通胀高企，什么都难赚钱。当前中国通胀低，反而是政策宽松的空间；美国通胀粘性，Fed不敢轻易降息。`,
    ])},
    { test: /ETF|指数基金|etf|交易所.*基金/i, resp: () => humanize(KNOWLEDGE.strategy.etf, 'strategy') },
    { test: /分红|股息|派息|dividend|收息/i, resp: () => humanize(KNOWLEDGE.strategy.dividend, 'strategy') },
  ];

  for (const p of patterns) {
    if (p.test.test(q)) return p.resp();
  }

  // 3. Keyword fallback — still casual
  const kwMap = {
    'support': 'technical', 'resistance': 'technical', 'level': 'technical',
    'rsi': 'technical', 'macd': 'technical', 'indicator': 'technical',
    'ma': 'technical', 'ema': 'technical', 'sma': 'technical',
    'fibonacci': 'technical', 'fib': 'technical', 'retracement': 'technical',
    'bollinger': 'technical', 'band': 'technical',
    'candle': 'technical', 'hammer': 'technical', 'doji': 'technical', 'engulfing': 'technical',
    'chart': 'technical', 'pattern': 'technical', 'triangle': 'technical',
    'volume': 'technical', 'obv': 'technical',
    'breakout': 'technical', 'break': 'technical',
    'pe': 'fundamental', 'earning': 'fundamental', 'revenue': 'fundamental',
    'cpi': 'fundamental', 'inflation': 'fundamental', 'fed': 'fundamental', 'interest rate': 'fundamental',
    'gdp': 'fundamental', 'nfp': 'fundamental', 'employment': 'fundamental',
    'stop': 'risk', 'risk': 'risk', 'position': 'risk', 'leverage': 'risk', 'margin': 'risk',
    'swing': 'strategy', 'day trad': 'strategy', 'scalp': 'strategy',
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
    '苹果': 'stocks', '英伟达': 'stocks', '特斯拉': 'stocks', '微软': 'stocks',
    '亚马逊': 'stocks', '谷歌': 'stocks', '脸书': 'stocks', '巴菲特': 'stocks',
    '黄金': 'stocks', '台积电': 'stocks', '摩根': 'stocks',
    '原油': 'stocks', '石油': 'stocks', '股票': 'stocks', '石油股': 'stocks', '油气': 'stocks',
    '科技股': 'stocks', '金融股': 'stocks', '军工股': 'stocks', '医药股': 'stocks',
    '新能源股': 'stocks', '零售股': 'stocks', '能源股': 'stocks',
    // ── 美股市场关键词 → stocks 类别 ──
    'us market': 'stocks', 'us stock': 'stocks', 'us stocks': 'stocks',
    'american market': 'stocks', 'wall street': 'stocks',
    'dow jones': 'stocks', 'dow': 'stocks', 'dji': 'stocks',
    's&p': 'stocks', 'sp500': 'stocks', 'spx': 'stocks',
    'nasdaq': 'stocks', 'ndx': 'stocks', 'vix': 'stocks',
    '美股': 'stocks', '美国股市': 'stocks', '华尔街': 'stocks',
    '道琼斯': 'stocks', '道指': 'stocks', '标普500': 'stocks',
    '纳斯达克': 'stocks', '美股大盘': 'stocks', '美股行情': 'stocks',
    // ── 中国/A股/港股关键词 → china 类别 ──
    'A股': 'china', '港股': 'china', '上证': 'china', '深证': 'china',
    '恒生': 'china', '创业板': 'china', '科创板': 'china',
    '中国股市': 'china', '中国股票': 'china', '中国行情': 'china',
    '中国指数': 'china', '大盘': 'china', '中概': 'china', '中国科技': 'china',
    '人民币': 'china', '汇率': 'china', '人民币汇率': 'china',
    '北向': 'china', '南向': 'china', '北向资金': 'china', '南向资金': 'china',
    '央行': 'china', '降准': 'china', '降息': 'china', '政策': 'china',
    '涨停': 'china', '跌停': 'china', '走势': 'china', '行情': 'china',
    '分析': 'china', '前景': 'china', '预测': 'china', '指数': 'china',
    '涨跌': 'china', '现在多少': 'china', '多少点': 'china',
    '突破': 'technical', '支撑': 'technical', '压力': 'technical',
    '技术分析': 'technical', '技术指标': 'technical', '看盘': 'technical',
    '通胀': 'fundamental', '利率': 'fundamental', 'GDP': 'fundamental',
    '美联储': 'fundamental',
    // ── 新手入门关键词 → beginner 类别 ──
    '新手': 'beginner', '入门': 'beginner', '零基础': 'beginner', '小白': 'beginner',
    '选股': 'beginner', '开户': 'beginner', '基金': 'beginner', '定投': 'beginner',
    '牛市': 'beginner', '熊市': 'beginner', '估值': 'beginner',
    '何时买': 'beginner', '何时卖': 'beginner', '买入时机': 'beginner', '卖出时机': 'beginner',
    '分散': 'beginner', '资产配置': 'beginner', '投资组合': 'beginner',
    '心态': 'beginner', '贪婪': 'beginner', '恐惧': 'beginner', '追涨杀跌': 'beginner',
    '复利': 'beginner', '投资门槛': 'beginner', '小资金': 'beginner',
    // ── 高级投资关键词 → advanced 类别 ──
    '期权': 'advanced', '期货': 'advanced', '做空': 'advanced', '融券': 'advanced',
    '量化': 'advanced', '对冲': 'advanced', '保证金': 'advanced',
    // ── 常见投资问题关键词 ──
    '割肉': 'risk', '止损': 'risk', '止盈': 'risk', '平仓': 'risk', '仓位': 'risk',
    '财报': 'fundamental', '业绩': 'fundamental', '盈利': 'fundamental', '营收': 'fundamental',
    '降息': 'fundamental', '加息': 'fundamental', '央行': 'fundamental', '货币政策': 'fundamental',
    '主力': 'stocks', '庄家': 'stocks', '机构': 'stocks', '聪明钱': 'stocks',
    // ── 基本面分析关键词 → fundamental_analysis 类别 ──
    '基本面分析': 'fundamental_analysis', '基本面': 'fundamental_analysis', '估值': 'fundamental_analysis',
    'PE': 'fundamental_analysis', 'PB': 'fundamental_analysis', 'DCF': 'fundamental_analysis',
    'ROE': 'fundamental_analysis', 'ROIC': 'fundamental_analysis', 'WACC': 'fundamental_analysis',
    '财报分析': 'fundamental_analysis', '10-K': 'fundamental_analysis', '10-Q': 'fundamental_analysis',
    '现金流': 'fundamental_analysis', '自由现金流': 'fundamental_analysis', '盈利质量': 'fundamental_analysis',
    '资本配置': 'fundamental_analysis', '安全边际': 'fundamental_analysis',
    'p/e': 'fundamental_analysis', 'ev/ebitda': 'fundamental_analysis', 'peg': 'fundamental_analysis',
    'valuation': 'fundamental_analysis', 'intrinsic value': 'fundamental_analysis',
    'cash flow': 'fundamental_analysis', 'free cash flow': 'fundamental_analysis',
    'earnings quality': 'fundamental_analysis', 'margin of safety': 'fundamental_analysis',
    '基本面怎么看': 'fundamental_analysis', '怎么估值': 'fundamental_analysis', '公司分析': 'fundamental_analysis',
    // ── 技术面分析关键词 → technical_analysis 类别 ──
    '技术面分析': 'technical_analysis', '技术面': 'technical_analysis',
    '均线': 'technical_analysis', 'MA': 'technical_analysis', 'SMA': 'technical_analysis', 'EMA': 'technical_analysis',
    'MACD详解': 'technical_analysis', 'RSI详解': 'technical_analysis',
    '金叉': 'technical_analysis', '死叉': 'technical_analysis',
    '布林带': 'technical_analysis', 'bollinger': 'technical_analysis',
    'K线': 'technical_analysis', '蜡烛图': 'technical_analysis',
    'moving average': 'technical_analysis', 'golden cross': 'technical_analysis', 'death cross': 'technical_analysis',
    '技术面怎么看': 'technical_analysis', '怎么看盘': 'technical_analysis', '入场点': 'technical_analysis',
    // ── 投资心理关键词 → psychology 类别 ──
    '投资心理': 'psychology', '心理': 'psychology', '情绪': 'psychology',
    '恐惧': 'psychology', '贪婪': 'psychology', 'FOMO': 'psychology',
    '损失厌恶': 'psychology', '认知偏差': 'psychology', '确认偏差': 'psychology',
    '锚定效应': 'psychology', '沉没成本': 'psychology', '从众': 'psychology',
    '过度自信': 'psychology', '心态管理': 'psychology', '交易纪律': 'psychology',
    'fear and greed': 'psychology', 'loss aversion': 'psychology', 'bias': 'psychology',
    '心理学': 'psychology', '怕亏': 'psychology', '拿不住': 'psychology', '追涨': 'psychology',
    // ── 美股市场文化关键词 → market_culture 类别 ──
    '美股文化': 'market_culture', '市场文化': 'market_culture', '华尔街': 'market_culture',
    '散户': 'market_culture', '机构': 'market_culture', '聪明钱': 'market_culture',
    '市场开发': 'market_culture', '客户开发': 'market_culture', '获客': 'market_culture',
    'diamond hands': 'market_culture', 'HODL': 'market_culture', 'BTFD': 'market_culture',
    'FUD': 'market_culture', 'DD': 'market_culture', 'tendies': 'market_culture',
    'bagholder': 'market_culture', 'whale': 'market_culture', 'apes': 'market_culture',
    'scalping': 'market_culture', 'swing': 'market_culture', 'YOLO': 'market_culture',
    '交易风格': 'market_culture', '日内交易': 'market_culture', '波段交易': 'market_culture',
    'retail': 'market_culture', 'institutional': 'market_culture',
  };

  for (const [kw, cat] of Object.entries(kwMap)) {
    if (q.includes(kw)) {
      for (const [key, answer] of Object.entries(KNOWLEDGE[cat])) {
        if (q.includes(key) || key.includes(kw)) {
          return humanize(answer, cat);
        }
      }
      // Casual category fallback
      const catCasual = {
        technical: "技术分析的核心是找高概率入场点：先看趋势方向（均线判断），再找支撑压力位，等确认信号（RSI背离+K线形态+放量）。三个信号同时出现才动手。",
        fundamental: "基本面看的是价值：PE/PB估值、营收增长、利润率趋势。最关键是看预期差——市场预期和实际数据的差距才是赚钱的机会。",
        risk: "风控是活下来的根本：每笔交易最多亏1-2%，总仓位风险不超过6%，止损永远在进场前设好。仓位控制比选股更重要。",
        strategy: "选策略先看你的时间和性格：白天盯盘→日内交易，上班党→波段交易，不想操心→定投ETF。最适合大多数人的是波段交易——不用盯盘，利润也够。",
        crypto: "加密市场24/7，波动极大。配置别超过15%，只碰BTC和ETH。别用杠杆——加密本身的波动已经是杠杆了。",
        platform: "BroadFSC是合规的投资咨询平台，持牌经营，AI驱动的教育+专业人工支持。我们有实时行情数据、技术分析工具、风险管理框架，从入门到进阶都覆盖。",
        stocks: "美股当前核心看点：NVDA领涨AI行情但估值已高，黄金是这十年最佳交易突破$4800，TSLA在电动车价格战中利润承压。大盘看Fed降息节奏——利率下行利好成长股，通胀反弹则利好能源和黄金。",
        china: "A股和港股当前核心逻辑：A股看政策方向（央行降准降息+产业扶持），港股看估值修复+南向资金。上证4000点是关键心理关口，突破后看4200-4500；恒指受益于中概股回归+AI估值重塑。",
        beginner: "新手投资第一步：用模拟盘练3个月，学均线+支撑压力+RSI三个基础工具，每笔必设止损。起步资金别超过你能承受亏光的数目，指数基金定投是最稳妥的入门方式。",
        advanced: "高级工具（期权/期货/做空/量化）都是双刃剑——用好了放大收益，用不好加速亏损。核心原则：小仓位试水，严格止损，先模拟盘验证再上实盘。新手不建议碰。",
        fundamental_analysis: "基本面分析5步法：读财报→查盈利质量→估值(DCF+相对)→看资本配置(ROIC vs WACC)→决策(安全边际)。最关键一步是盈利质量——经营现金流/净利润 < 1.0的利润是纸面上的。",
        technical_analysis: "技术分析三步法：1)判趋势(200日线定牛熊)→2)找入场(支撑压力+K线+确认信号三合一)→3)设止损(进场前定好)。趋势市用均线+MACD，震荡市用RSI+布林带。",
        psychology: "投资最大的敌人不是市场，是你自己。三大陷阱：恐惧(割在最低点)、贪婪(坐过山车)、FOMO(追在山顶)。解法：写交易计划，机械化执行，每笔最多亏1-2%。",
        market_culture: "理解美股文化才能读懂市场信号：Diamond Hands=死拿不卖，BTFD=抄底，FUD=恐慌散布，DD=尽职调查。当所有人喊To the Moon的时候，往往是该谨慎的时候。"
      };
      return catCasual[cat] || "I'm not sure about that one — try asking about a specific stock, market, or trading topic and I'll give you my take.";
    }
  }

  // 4. Detect potential stock ticker that wasn't recognized
  const possibleTicker = q.match(/\b([A-Za-z]{2,5})\b/);
  if (possibleTicker && !STOP_WORDS.has(possibleTicker[1].toLowerCase())) {
    const ticker = possibleTicker[1].toUpperCase();
    const tickerFallbacks = {
      alex: [
        `I don't have live data on ${ticker} right now. But here's my quick take — check if it's above or below the 200 SMA. That alone tells you the regime. Then look for RSI divergence at key levels.`,
        `${ticker} — not one I'm actively tracking. Pull up the daily chart: if it's above the 50 SMA, the trend is your friend. Below it, be cautious.`,
      ],
      sarah: [
        `I don't have fresh numbers on ${ticker}. But regardless of the stock — make sure you have an entry reason, a stop level, and a position size BEFORE you buy. That matters more than the ticker.`,
      ],
      mike: [
        `${ticker} — I'd need to dig into their fundamentals to give you a real take. Quick check: what's the revenue growth and is it profitable? That tells you 80% of what you need.`,
        `Don't have ${ticker} on my radar. But here's how I'd evaluate it — look at the revenue growth trajectory and whether they're profitable. Fundamentals win in the long run.`,
      ],
    };
    const pool = tickerFallbacks[currentAdvisor] || tickerFallbacks.alex;
    return pick(pool);
  }

  // 5. No local match → return null so sendChat() uses AI
  return null;
}

// Helper: pick random from array
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

// Helper: humanize a knowledge base answer (make it sound conversational, not encyclopedic)
function humanize(answer, category) {
  // The knowledge base has great content but it's written like a textbook.
  // We'll trim it to the first 2-3 sentences — NO follow-up questions.
  const sentences = answer.split(/(?<=[.!?。！？])\s*/);
  const maxSentences = currentAdvisor === 'alex' ? 3 : currentAdvisor === 'sarah' ? 3 : 3;
  let result = sentences.slice(0, maxSentences).join(' ');

  // Add casual closer based on advisor — STATEMENTS ONLY, never questions
  const closers = {
    alex: ['', '', ' 这是我实盘经验的总结。', ' 不过说到底还是得看盘执行。', ''],
    sarah: ['', '', ' 风控永远是第一位的。', ' 这比选股重要多了。', ''],
    mike: ['', '', ' 这就是我看到的逻辑。', ' 跟着资金走不会太差。', ''],
  };
  const closer = pick(closers[currentAdvisor] || closers.alex);
  if (closer) result += closer;

  return result;
}

// ── AI API Integration (Pollinations Free + Groq Backup + Yahoo Finance) ──
// Pollinations: completely free, no API key needed, works in browser
const POLLINATIONS_URL = 'https://text.pollinations.ai/';
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_MODEL = 'llama-3.1-8b-instant';

// Encoded Groq API key (may expire — Pollinations is the primary free fallback)
const _gk = atob('Z3FkXzN0bHJhM0haaWFCTkhnM0tNS2p3ZU05Vjdybw==');

// Track which AI source is working so we don't keep retrying broken ones
let _aiSourceWorking = { pollinations: true, groq: true };

// Stock symbol mapping for Yahoo Finance queries
const STOCK_SYMBOLS = {
  'apple': 'AAPL', 'aapl': 'AAPL', '苹果': 'AAPL',
  'nvidia': 'NVDA', 'nvda': 'NVDA', '英伟达': 'NVDA',
  'tesla': 'TSLA', 'tsla': 'TSLA', '特斯拉': 'TSLA',
  'microsoft': 'MSFT', 'msft': 'MSFT', '微软': 'MSFT',
  'amazon': 'AMZN', 'amzn': 'AMZN', '亚马逊': 'AMZN',
  'google': 'GOOGL', 'googl': 'GOOGL', 'alphabet': 'GOOGL', '谷歌': 'GOOGL',
  'meta': 'META', 'facebook': 'META', '脸书': 'META',
  'jpmorgan': 'JPM', 'jpm': 'JPM', '摩根': 'JPM',
  'tsmc': 'TSM', '台积电': 'TSM',
  'berkshire': 'BRK-B', 'brk': 'BRK-B', '巴菲特': 'BRK-B',
  'gold': 'GC=F', 'xau': 'GC=F', '黄金': 'GC=F',
  'bitcoin': 'BTC-USD', 'btc': 'BTC-USD', '比特币': 'BTC-USD',
  'ethereum': 'ETH-USD', 'eth': 'ETH-USD',
  'sp500': '^GSPC', 's&p': '^GSPC', 's&p 500': '^GSPC', 'spx': '^GSPC', 'spy': '^GSPC', '标普': '^GSPC', '标普500': '^GSPC',
  'nasdaq': '^IXIC', '纳斯达克': '^IXIC', 'ndx': '^NDX', 'qqq': '^NDX',
  'dow': '^DJI', 'dow jones': '^DJI', 'dji': '^DJI', '道琼斯': '^DJI', '道指': '^DJI',
  'vix': '^VIX', '恐惧指数': '^VIX', '波动率': '^VIX',
  'russell': '^RUT', 'iwm': '^RUT', '罗素': '^RUT',
  'us market': 'US_MARKET', 'us stock': 'US_MARKET', 'us stocks': 'US_MARKET',
  'american market': 'US_MARKET', '美股': 'US_MARKET', '美国股市': 'US_MARKET',
  '美国股票': 'US_MARKET', '华尔街': 'US_MARKET', '美股大盘': 'US_MARKET',
  '美股行情': 'US_MARKET', '美国指数': 'US_MARKET', '美股指数': 'US_MARKET',
  'exxon': 'XOM', 'xom': 'XOM', '埃克森': 'XOM',
  'chevron': 'CVX', 'cvx': 'CVX', '雪佛龙': 'CVX',
  'palantir': 'PLTR', 'pltr': 'PLTR',
  'amd': 'AMD', '超微': 'AMD',
  'coca-cola': 'KO', 'ko': 'KO', '可乐': 'KO',
  'marathon': 'MPC', 'mpc': 'MPC', '马拉松': 'MPC',
  'oil': 'CL=F', 'crude': 'CL=F', '原油': 'CL=F',
  'eur/usd': 'EURUSD=X', 'eurusd': 'EURUSD=X',
  'usd/jpy': 'USDJPY=X', 'usdjpy': 'USDJPY=X',
  // ── A股 & 港股指数 ──
  '上证': '000001.SS', '上证指数': '000001.SS', '沪市': '000001.SS',
  'shanghai': '000001.SS', 'sse': '000001.SS',
  '深证': '399001.SZ', '深证成指': '399001.SZ', '深市': '399001.SZ',
  'shenzhen': '399001.SZ', 'szse': '399001.SZ',
  '沪深300': '000300.SS', 'csi300': '000300.SS',
  '创业板': '399006.SZ', 'chinext': '399006.SZ',
  '科创': '000688.SS', '科创板': '000688.SS', 'star50': '000688.SS',
  // ── 港股 ──
  '恒生': '^HSI', '恒指': '^HSI', '恒生指数': '^HSI', '港股指数': '^HSI',
  'hang seng': '^HSI', 'hsi': '^HSI',
  '恒生科技': '^HSTECH', '恒科': '^HSTECH', 'hstech': '^HSTECH',
  // ── 中概股 / 港股个股 ──
  '腾讯': '0700.HK', 'tencent': '0700.HK',
  '阿里巴巴': '9988.HK', '阿里': '9988.HK', 'alibaba': '9988.HK',
  '比亚迪': '1211.HK', 'byd': '1211.HK',
  '百度': '9888.HK', 'baidu': '9888.HK',
  '美团': '3690.HK', 'meituan': '3690.HK',
  '京东': '9618.HK', 'jd': '9618.HK',
  '小米': '1810.HK', 'xiaomi': '1810.HK',
  '网易': '9999.HK', 'netease': '9999.HK',
  '拼多多': 'PDD', 'pdd': 'PDD',
  '蔚来': 'NIO', 'nio': 'NIO',
  '理想汽车': 'LI', '理想': 'LI',
  '小鹏': 'XPEV', 'xpev': 'XPEV',
  // ── 人民币汇率 ──
  'usd/cny': 'CNY=X', 'usdcny': 'CNY=X', '美元人民币': 'CNY=X',
  '人民币汇率': 'CNY=X', '人民币': 'CNY=X',
  'usd/hkd': 'HKDUSD=X', '港币': 'HKDUSD=X',
  // ── 中国ETF ──
  'fxi': 'FXI', '中国etf': 'FXI', '中国指数etf': 'FXI',
  'mchi': 'MCHI', 'msci中国': 'MCHI',
  'kweb': 'KWEB', '中概互联网': 'KWEB', '中概': 'KWEB',
  // ── 石油/能源板块 ──
  'conocophillips': 'COP', 'cop': 'COP', '康菲': 'COP',
  'eog': 'EOG', 'eog resources': 'EOG',
  'pioneer': 'PXD', 'pxd': 'PXD', '先锋自然资源': 'PXD',
  'halliburton': 'HAL', 'hal': 'HAL', '哈里伯顿': 'HAL',
  'schlumberger': 'SLB', 'slb': 'SLB', '斯伦贝谢': 'SLB',
  'occidental': 'OXY', 'oxy': 'OXY', '西方石油': 'OXY',
  'valero': 'VLO', 'vlo': 'VLO', '瓦莱罗': 'VLO',
  'phillips66': 'PSX', 'psx': 'PSX',
  'diamondback': 'FANG', 'fang': 'FANG',
  'energy select': 'XLE', 'xle': 'XLE', '能源ETF': 'XLE', '石油ETF': 'XLE',
  'uso': 'USO', '原油ETF': 'USO',
  'natural gas': 'NG=F', '天然气': 'NG=F', 'henry hub': 'NG=F',
  // ── 科技板块额外 ──
  'broadcom': 'AVGO', 'avgo': 'AVGO', '博通': 'AVGO',
  'oracle': 'ORCL', 'orcl': 'ORCL',
  'salesforce': 'CRM', 'crm': 'CRM',
  'netflix': 'NFLX', 'nflx': 'NFLX', '奈飞': 'NFLX',
  // ── 金融板块 ──
  'bank of america': 'BAC', 'bac': 'BAC', '美银': 'BAC',
  'wells fargo': 'WFC', 'wfc': 'WFC', '富国': 'WFC',
  'goldman sachs': 'GS', 'gs': 'GS', '高盛': 'GS',
  'visa': 'V', 'mastercard': 'MA',
  // ── 消费/医疗 ──
  'walmart': 'WMT', 'wmt': 'WMT', '沃尔玛': 'WMT',
  'johnson & johnson': 'JNJ', 'jnj': 'JNJ', '强生': 'JNJ',
  'pfizer': 'PFE', 'pfe': 'PFE', '辉瑞': 'PFE',
  'unitedhealth': 'UNH', 'unh': 'UNH',
  // ── 半导体 ──
  'taiwan semiconductor': 'TSM', 'asml': 'ASML',
  'micron': 'MU', 'mu': 'MU', '美光': 'MU',
  'qualcomm': 'QCOM', 'qcom': 'QCOM', '高通': 'QCOM',
  'intel': 'INTC', 'intc': 'INTC', '英特尔': 'INTC',
  // ── 银行/保险 ──
  'citi': 'C', 'citigroup': 'C', '花旗': 'C',
  'aig': 'AIG',
  // ── 新能源/清洁能源 ──
  'nextera': 'NEE', 'nee': 'NEE',
  'enphase': 'ENPH', 'enph': 'ENPH',
  'first solar': 'FSLR', 'fslr': 'FSLR',
  // ── 军工 ──
  'lockheed': 'LMT', 'lmt': 'LMT', '洛克希德': 'LMT',
  'raytheon': 'RTX', 'rtx': 'RTX', '雷神': 'RTX',
  'northrop': 'NOC', 'noc': 'NOC',
  // ── 零售 ──
  'costco': 'COST', 'cost': 'COST', '好市多': 'COST',
  'target': 'TGT', 'tgt': 'TGT', '塔吉特': 'TGT',
  'home depot': 'HD', 'hd': 'HD', '家得宝': 'HD',
};

// ── China/HK Market Detection & Multi-Index Query ──
const CHINA_MARKET_KEYWORDS = [
  '中国股市', '中国股票', 'A股', 'a股', '大盘', '中国指数', '中国行情',
  '港股', '香港股市', '恒指', '恒生', '恒科',
  '上证', '深证', '沪深', '创业板', '科创板',
  '中国行情', '中国现在', '中国指数多少', 'A股多少', 'A股指数',
  '中国大盘', '中国走势', '中国分析', '中国前景',
  '沪深300', '中国基金', '中国ETF', '人民币汇率',
  'china market', 'china stock', 'china index', 'a-share', 'a share',
  'shanghai composite', 'shenzhen', 'hang seng',
  '中国市况', '内地股市', '北向资金', '南向资金',
];

function isChinaMarketQuery(query) {
  const q = query.toLowerCase();
  return CHINA_MARKET_KEYWORDS.some(kw => q.includes(kw.toLowerCase()));
}

async function fetchChinaMarketData() {
  // Fetch real-time data for key China/HK indices in parallel
  const indices = [
    { symbol: '000001.SS', label: '上证指数 (SSE)' },
    { symbol: '399001.SZ', label: '深证成指 (SZSE)' },
    { symbol: '000300.SS', label: '沪深300 (CSI300)' },
    { symbol: '^HSI', label: '恒生指数 (HSI)' },
  ];
  const results = await Promise.all(indices.map(idx => _fetchYahooChart(idx.symbol)));
  const lines = [];
  for (let i = 0; i < indices.length; i++) {
    if (results[i]) {
      const d = results[i];
      const dir = parseFloat(d.change) >= 0 ? '▲' : '▼';
      lines.push(`${indices[i].label}: ${d.price} ${d.currency} (${dir} ${d.changePct}%) | 市场: ${d.marketState}`);
    }
  }
  return lines.length > 0 ? lines.join('\n') : null;
}

// ── US Market Detection & Multi-Index Query ──
const US_MARKET_KEYWORDS = [
  'us market', 'us stock', 'us stocks', 'us indices', 'us index',
  'american market', 'american stocks',
  'wall street', 'dow', 's&p', 'sp500', 'spx', 'spy',
  'nasdaq', 'ndx', 'qqq', 'vix',
  '美股', '美国股市', '美国股票', '华尔街', '美股大盘',
  '美股行情', '美国指数', '美股指数', '美股走势',
  '道琼斯', '道指', '标普500', '纳斯达克',
  'how is the market', 'how\'s the market', 'market today', 'market update',
  'market outlook', 'stock market', 'market overview',
  '指数多少', 'now what', 'current market', 'market now',
];

function isUSMarketQuery(query) {
  const q = query.toLowerCase();
  // Check for US market keywords
  if (US_MARKET_KEYWORDS.some(kw => q.includes(kw.toLowerCase()))) return true;
  // Check for generic "market" queries in English (without China keyword)
  if (/\b(market|stocks?|indices?)\b/i.test(q) && !isChinaMarketQuery(query)) return true;
  return false;
}

// ── Analysis Query Detection ──
// When user asks for "技术面分析/基本面分析/行情分析" etc, they want REAL DATA
const ANALYSIS_KEYWORDS = [
  '技术面', '基本面', '行情分析', '市场分析', '走势分析', '大盘分析',
  '分析一下', '帮我分析', '看看分析', '技术分析', '基本面分析',
  '盘面分析', '趋势分析', '宏观分析', '板块分析', '资金分析',
  'technical analysis', 'fundamental analysis', 'market analysis',
  'analyze', 'analysis', 'outlook', 'forecast',
  '怎么看', '怎么分析', '分析下', '分析一下',
  '后市', '前景', '展望', '趋势判断',
];

function isAnalysisQuery(query) {
  const q = query.toLowerCase();
  return ANALYSIS_KEYWORDS.some(kw => q.includes(kw.toLowerCase()));
}

// ── Sector/Industry Query Detection ──
// When user asks about a whole sector/industry, fetch MULTIPLE stocks in that sector
const SECTOR_MAP = {
  'oil': {
    region: 'us',
    keywords: ['石油', '石油股', '原油', 'oil stock', 'oil sector', 'energy stock', '能源股', '油气', '石油投资',
               'oil industry', 'crude oil stock', 'drilling', 'refining', 'upstream', 'downstream',
               '页岩油', '页岩气', 'oil companies', 'oil investment', '美国石油', 'us oil'],
    stocks: [
      { symbol: 'XOM', label: 'ExxonMobil' },
      { symbol: 'CVX', label: 'Chevron' },
      { symbol: 'COP', label: 'ConocoPhillips' },
      { symbol: 'MPC', label: 'Marathon Petroleum' },
      { symbol: 'SLB', label: 'Schlumberger' },
      { symbol: 'EOG', label: 'EOG Resources' },
      { symbol: 'OXY', label: 'Occidental' },
      { symbol: 'VLO', label: 'Valero Energy' },
    ],
    etf: { symbol: 'XLE', label: 'Energy Select SPDR' },
    commodity: { symbol: 'CL=F', label: 'WTI Crude Oil' },
  },
  'tech': {
    region: 'us',
    keywords: ['科技股', 'tech stock', 'tech sector', 'technology stock', '科技板块', '科技投资',
               'AI股', 'AI stock', 'AI sector', '人工智能股', '芯片股', 'chip stock', 'semiconductor',
               '科技行业', 'technology industry', '互联网股', '互联网板块'],
    stocks: [
      { symbol: 'AAPL', label: 'Apple' },
      { symbol: 'NVDA', label: 'NVIDIA' },
      { symbol: 'MSFT', label: 'Microsoft' },
      { symbol: 'GOOGL', label: 'Alphabet' },
      { symbol: 'META', label: 'Meta' },
      { symbol: 'AMZN', label: 'Amazon' },
      { symbol: 'AVGO', label: 'Broadcom' },
      { symbol: 'AMD', label: 'AMD' },
    ],
    etf: { symbol: 'XLK', label: 'Technology Select SPDR' },
    commodity: null,
  },
  'finance': {
    region: 'us',
    keywords: ['金融股', 'finance stock', 'bank stock', 'banking sector', '银行股', '金融板块',
               '保险股', 'insurance stock', '券商股', '金融行业', 'financial sector'],
    stocks: [
      { symbol: 'JPM', label: 'JPMorgan' },
      { symbol: 'BAC', label: 'Bank of America' },
      { symbol: 'GS', label: 'Goldman Sachs' },
      { symbol: 'WFC', label: 'Wells Fargo' },
      { symbol: 'V', label: 'Visa' },
      { symbol: 'MA', label: 'Mastercard' },
    ],
    etf: { symbol: 'XLF', label: 'Financial Select SPDR' },
    commodity: null,
  },
  'healthcare': {
    region: 'us',
    keywords: ['医药股', 'healthcare stock', 'pharma stock', '医疗股', '生物科技', 'biotech',
               '制药股', '医疗板块', 'health sector', '医药行业'],
    stocks: [
      { symbol: 'JNJ', label: 'Johnson & Johnson' },
      { symbol: 'UNH', label: 'UnitedHealth' },
      { symbol: 'PFE', label: 'Pfizer' },
      { symbol: 'ABBV', label: 'AbbVie' },
      { symbol: 'MRK', label: 'Merck' },
      { symbol: 'LLY', label: 'Eli Lilly' },
    ],
    etf: { symbol: 'XLV', label: 'Health Care Select SPDR' },
    commodity: null,
  },
  'defense': {
    region: 'us',
    keywords: ['军工股', 'defense stock', 'military stock', '军工板块', '军工投资', 'defense sector',
               '军火股', '武器股', '航空航天', 'aerospace defense'],
    stocks: [
      { symbol: 'LMT', label: 'Lockheed Martin' },
      { symbol: 'RTX', label: 'RTX Corp' },
      { symbol: 'NOC', label: 'Northrop Grumman' },
      { symbol: 'BA', label: 'Boeing' },
      { symbol: 'GD', label: 'General Dynamics' },
    ],
    etf: { symbol: 'XAR', label: 'Aerospace & Defense ETF' },
    commodity: null,
  },
  'renewable': {
    region: 'us',
    keywords: ['新能源股', 'renewable stock', 'clean energy', 'solar stock', '光伏股', '风电股',
               '新能源板块', '绿色能源', '新能源投资', 'ev stock', '电动车股'],
    stocks: [
      { symbol: 'NEE', label: 'NextEra Energy' },
      { symbol: 'FSLR', label: 'First Solar' },
      { symbol: 'ENPH', label: 'Enphase' },
      { symbol: 'TSLA', label: 'Tesla' },
    ],
    etf: { symbol: 'ICLN', label: 'iShares Clean Energy' },
    commodity: null,
  },
  'retail': {
    region: 'us',
    keywords: ['零售股', 'retail stock', 'consumer stock', '消费股', '消费板块', '零售板块',
               '零售行业', 'consumer discretionary'],
    stocks: [
      { symbol: 'WMT', label: 'Walmart' },
      { symbol: 'COST', label: 'Costco' },
      { symbol: 'HD', label: 'Home Depot' },
      { symbol: 'TGT', label: 'Target' },
      { symbol: 'AMZN', label: 'Amazon' },
    ],
    etf: { symbol: 'XLY', label: 'Consumer Discretionary SPDR' },
    commodity: null,
  },
};

// ── Pure Data Sector Analysis (NO AI needed) ──
// Generates professional sector analysis from real-time data alone
const SECTOR_PROFILES = {
  'oil': {
    name: '石油/能源',
    nameEn: 'Oil & Energy',
    drivers: 'OPEC+产量政策、WTI原油价格、地缘政治风险、全球需求预期',
    risks: '经济衰退打击需求、新能源替代加速、OPEC+减产执行不力、库存意外增加',
    profiles: {
      'XOM': { risk: 'low', label: '埃克森美孚', thesis: '分红贵族(连续40+年)，低盈亏平衡点，现金流充裕，油价跌也能扛' },
      'CVX': { risk: 'low', label: '雪佛龙', thesis: '二叠纪盆地低成本优势，资产负债表持续改善，分红稳定' },
      'COP': { risk: 'mid', label: '康菲石油', thesis: '页岩油弹性最大——油价涨它最赚，但油价跌也最疼' },
      'EOG': { risk: 'mid', label: 'EOG资源', thesis: '顶级页岩油商，资本纪律好，ROE行业领先' },
      'SLB': { risk: 'high', label: '斯伦贝谢', thesis: '油服龙头，纯周期股——需精准择时，油价高位时弹性最大' },
      'OXY': { risk: 'high', label: '西方石油', thesis: '巴菲特持仓，但杠杆高，偿债压力大，赌油价持续高位' },
      'VLO': { risk: 'mid', label: '瓦莱罗', thesis: '炼油龙头，裂解差价扩大利好，油价波动反而受益' },
    },
    etfProfile: { risk: 'low', thesis: '一篮子石油股分散风险，适合不想选个股的投资者' },
  },
  'tech': {
    name: '科技',
    nameEn: 'Technology',
    drivers: 'AI资本开支、企业数字化转型、云计算增长、半导体周期',
    risks: 'AI泡沫风险、监管反垄断、利率走高压估值、中国竞争',
    profiles: {
      'AAPL': { risk: 'low', label: '苹果', thesis: '现金流怪兽+回购机器，估值合理，AI整合是催化剂' },
      'NVDA': { risk: 'mid', label: '英伟达', thesis: 'AI算力垄断，但估值已price in很多增长，波动大' },
      'MSFT': { risk: 'low', label: '微软', thesis: 'Azure+Copilot双引擎，企业AI落地最受益' },
      'GOOGL': { risk: 'low', label: 'Alphabet', thesis: '广告护城河+Gemini AI，估值在科技巨头中最低' },
      'META': { risk: 'mid', label: 'Meta', thesis: '广告复苏+Llama开源AI，但 Reality Labs 持续烧钱' },
      'AVGO': { risk: 'mid', label: '博通', thesis: 'AI网络芯片龙头+VMware整合，但高负债' },
      'AMD': { risk: 'high', label: 'AMD', thesis: 'MI300挑战英伟达，但市占率差距大，估值偏高' },
    },
    etfProfile: { risk: 'low', thesis: 'XLK覆盖全科技板块，AAPL/MSFT占比大，偏防御' },
  },
  'finance': {
    name: '金融',
    nameEn: 'Financials',
    drivers: '利率走势、贷款增长、净息差、交易业务、消费信贷',
    risks: '利率快速下降压息差、坏账率上升、金融监管收紧、商业地产风险',
    profiles: {
      'JPM': { risk: 'low', label: '摩根大通', thesis: '银行之王，每个周期都能抄底扩张，净息差行业领先' },
      'BAC': { risk: 'low', label: '美国银行', thesis: '存款基础最大，利率敏感度高，降息周期不利' },
      'GS': { risk: 'mid', label: '高盛', thesis: '投行+交易为主，市场波动大时反而赚更多' },
      'WFC': { risk: 'mid', label: '富国银行', thesis: '仍在修复监管问题，但估值折价大，催化剂明确' },
      'V': { risk: 'low', label: 'Visa', thesis: '支付垄断，消费增长直接受益，几乎不受利率影响' },
      'MA': { risk: 'low', label: 'Mastercard', thesis: '与Visa双寡头，跨境支付增长更快' },
    },
    etfProfile: { risk: 'low', thesis: 'XLF覆盖全金融板块，银行+保险+支付分散' },
  },
  'healthcare': {
    name: '医疗/医药',
    nameEn: 'Healthcare',
    drivers: '人口老龄化、创新药审批、GLP-1减肥药、FDA政策',
    risks: '药品定价管制、专利悬崖、临床失败、医保谈判',
    profiles: {
      'JNJ': { risk: 'low', label: '强生', thesis: '最防御的医疗股，多元化+分红贵族，增长慢但稳' },
      'UNH': { risk: 'low', label: '联合健康', thesis: '医保管理垄断，人口老龄化直接受益' },
      'PFE': { risk: 'mid', label: '辉瑞', thesis: '后疫情收入下滑但管线丰富，估值极低，赌新药' },
      'ABBV': { risk: 'mid', label: '艾伯维', thesis: 'Humira专利过期但新药接力中，分红惊人' },
      'MRK': { risk: 'mid', label: '默克', thesis: 'Keytruda是印钞机但专利2030到期，需看管线' },
      'LLY': { risk: 'high', label: '礼来', thesis: 'GLP-1双雄之一，估值已经很高，增长必须持续超预期' },
    },
    etfProfile: { risk: 'low', thesis: 'XLV医疗ETF，防御属性强，适合衰退期持有' },
  },
  'defense': {
    name: '军工/航空航天',
    nameEn: 'Aerospace & Defense',
    drivers: '全球军费增长、地缘冲突、NATO军费目标2%GDP、F-35量产',
    risks: '政府预算削减、项目延迟/超支、和平谈判、供应链瓶颈',
    profiles: {
      'LMT': { risk: 'low', label: '洛克希德马丁', thesis: 'F-35+导弹垄断，订单积压1600亿+，最纯的军工标的' },
      'RTX': { risk: 'low', label: 'RTX Corp', thesis: '导弹+航空电子+Pratt Whitney，三引擎驱动' },
      'NOC': { risk: 'low', label: '诺斯洛普格鲁曼', thesis: 'B-21轰炸机+太空业务，国防预算最稳定受益者' },
      'BA': { risk: 'high', label: '波音', thesis: '737 MAX复产是催化剂，但质量问题和债务是巨大风险' },
      'GD': { risk: 'mid', label: '通用动力', thesis: '舰船+IT服务，增长稳但不性感' },
    },
    etfProfile: { risk: 'low', thesis: 'XAR军工ETF，分散个股风险，享受板块增长' },
  },
  'renewable': {
    name: '新能源',
    nameEn: 'Clean Energy',
    drivers: 'IRA法案补贴、全球碳中和、光伏装机增长、储能突破',
    risks: '利率走高压项目融资、中国光伏倾销、政策补贴退坡、电网接入瓶颈',
    profiles: {
      'NEE': { risk: 'low', label: 'NextEra', thesis: '全球最大风太阳能运营商，公用事业+增长双属性' },
      'FSLR': { risk: 'mid', label: 'First Solar', thesis: '美国唯一本土光伏龙头，IRA直接受益' },
      'ENPH': { risk: 'high', label: 'Enphase', thesis: '微型逆变器龙头，但高利率打击住宅太阳能需求' },
      'TSLA': { risk: 'high', label: '特斯拉', thesis: '不止是车——储能业务增速惊人，但估值和马斯克风险大' },
    },
    etfProfile: { risk: 'mid', thesis: 'ICLN新能源ETF，分散个股风险但板块整体波动大' },
  },
  'retail': {
    name: '零售/消费',
    nameEn: 'Retail & Consumer',
    drivers: '消费者信心、就业数据、通胀走势、假日消费季',
    risks: '消费降级、通胀侵蚀购买力、线上竞争、库存管理',
    profiles: {
      'WMT': { risk: 'low', label: '沃尔玛', thesis: '衰退防御之王——经济差时反而吸引更多消费者' },
      'COST': { risk: 'low', label: 'Costco', thesis: '会员制护城河，续费率93%+，通胀中提价能力最强' },
      'HD': { risk: 'mid', label: '家得宝', thesis: '住房市场关联度高，降息是催化剂但装修周期长' },
      'TGT': { risk: 'mid', label: 'Target', thesis: '品牌差异化+自有品牌，但库存和安全问题困扰' },
      'AMZN': { risk: 'mid', label: '亚马逊', thesis: '电商+AWS双引擎，但零售利润率一直很低' },
    },
    etfProfile: { risk: 'low', thesis: 'XLY消费ETF，覆盖零售+电商+餐饮' },
  },
};

// Build pure-data sector analysis — NO AI, just real numbers + expert templates
async function buildSectorAnalysis(sectorKey, isChinese) {
  const sector = SECTOR_MAP[sectorKey];
  const profile = SECTOR_PROFILES[sectorKey];
  if (!sector || !profile) return null;

  // Fetch all data in parallel
  const [stockResults, etfResult, commodityResult, marketData] = await Promise.all([
    Promise.all(sector.stocks.map(s => _fetchYahooChart(s.symbol))),
    sector.etf ? _fetchYahooChart(sector.etf.symbol) : Promise.resolve(null),
    sector.commodity ? _fetchYahooChart(sector.commodity.symbol) : Promise.resolve(null),
    fetchAllMarketData(sector.region || 'us'),
  ]);

  const lines = [];

  if (isChinese) {
    // ── 中文版板块分析 ──
    // 1. 总判断
    const upCount = stockResults.filter(d => d && parseFloat(d.change) >= 0).length;
    const downCount = stockResults.filter(d => d && parseFloat(d.change) < 0).length;
    const avgChange = stockResults.filter(d => d).length > 0
      ? (stockResults.filter(d => d).reduce((sum, d) => sum + parseFloat(d.changePct || 0), 0) / stockResults.filter(d => d).length).toFixed(2)
      : '0';

    let verdict;
    if (parseFloat(avgChange) > 1) verdict = '🔥 值得关注';
    else if (parseFloat(avgChange) > 0) verdict = '👀 有选择性机会';
    else if (parseFloat(avgChange) > -1) verdict = '⏸️ 暂时观望';
    else verdict = '⚠️ 回避为主';

    lines.push(`📊 **${profile.name}板块分析** — ${verdict}`);
    lines.push('');

    // 2. 市场环境
    if (marketData) {
      lines.push(`🌍 **市场环境**：${marketData.split('\n').filter(l => l.trim()).join(' | ')}`);
      lines.push('');
    }

    // 3. 大宗商品（石油板块特有）
    if (commodityResult) {
      const cDir = parseFloat(commodityResult.change) >= 0 ? '↑' : '↓';
      lines.push(`🛢️ **${sector.commodity.label}**：$${commodityResult.price} ${cDir}${commodityResult.changePct}%`);
      lines.push('');
    }

    // 4. 板块ETF
    if (etfResult) {
      const eDir = parseFloat(etfResult.change) >= 0 ? '↑' : '↓';
      lines.push(`📈 **板块ETF ${sector.etf.label}**：$${etfResult.price} ${eDir}${etfResult.changePct}%`);
      lines.push('');
    }

    // 5. 个股数据
    lines.push(`📋 **核心个股**：`);
    for (let i = 0; i < sector.stocks.length; i++) {
      const d = stockResults[i];
      if (d) {
        const dir = parseFloat(d.change) >= 0 ? '↑' : '↓';
        const emoji = parseFloat(d.change) >= 0 ? '🟢' : '🔴';
        lines.push(`  ${emoji} ${sector.stocks[i].label}(${d.symbol}) $${d.price} ${dir}${d.changePct}%`);
      }
    }
    lines.push('');

    // 6. 三档建议（核心！用户最想要的）
    lines.push(`💡 **投资建议**：`);
    const lowRisk = [], midRisk = [], highRisk = [];
    for (const [sym, p] of Object.entries(profile.profiles)) {
      if (p.risk === 'low') lowRisk.push(p);
      else if (p.risk === 'mid') midRisk.push(p);
      else highRisk.push(p);
    }
    if (lowRisk.length > 0) lines.push(`  🟢 **低风险**：${lowRisk.map(p => `${p.label} — ${p.thesis}`).join('；')}`);
    if (midRisk.length > 0) lines.push(`  🟡 **中风险**：${midRisk.map(p => `${p.label} — ${p.thesis}`).join('；')}`);
    if (highRisk.length > 0) lines.push(`  🔴 **高风险**：${highRisk.map(p => `${p.label} — ${p.thesis}`).join('；')}`);
    lines.push('');

    // 7. 驱动+风险
    lines.push(`🔑 **关键驱动**：${profile.drivers}`);
    lines.push(`⚠️ **主要风险**：${profile.risks}`);

  } else {
    // ── English version ──
    const upCount = stockResults.filter(d => d && parseFloat(d.change) >= 0).length;
    const avgChange = stockResults.filter(d => d).length > 0
      ? (stockResults.filter(d => d).reduce((sum, d) => sum + parseFloat(d.changePct || 0), 0) / stockResults.filter(d => d).length).toFixed(2)
      : '0';

    let verdict;
    if (parseFloat(avgChange) > 1) verdict = '🔥 Worth watching';
    else if (parseFloat(avgChange) > 0) verdict = '👀 Selective opportunities';
    else if (parseFloat(avgChange) > -1) verdict = '⏸️ Wait and see';
    else verdict = '⚠️ Avoid for now';

    lines.push(`📊 **${profile.nameEn} Sector Analysis** — ${verdict}`);
    lines.push('');

    if (marketData) {
      lines.push(`🌍 **Market Context**: ${marketData.split('\n').filter(l => l.trim()).join(' | ')}`);
      lines.push('');
    }

    if (commodityResult) {
      const cDir = parseFloat(commodityResult.change) >= 0 ? '↑' : '↓';
      lines.push(`🛢️ **${sector.commodity.label}**: $${commodityResult.price} ${cDir}${commodityResult.changePct}%`);
      lines.push('');
    }

    if (etfResult) {
      const eDir = parseFloat(etfResult.change) >= 0 ? '↑' : '↓';
      lines.push(`📈 **Sector ETF ${sector.etf.label}**: $${etfResult.price} ${eDir}${etfResult.changePct}%`);
      lines.push('');
    }

    lines.push(`📋 **Key Stocks**:`);
    for (let i = 0; i < sector.stocks.length; i++) {
      const d = stockResults[i];
      if (d) {
        const dir = parseFloat(d.change) >= 0 ? '↑' : '↓';
        const emoji = parseFloat(d.change) >= 0 ? '🟢' : '🔴';
        lines.push(`  ${emoji} ${sector.stocks[i].label}(${d.symbol}) $${d.price} ${dir}${d.changePct}%`);
      }
    }
    lines.push('');

    lines.push(`💡 **Recommendations**:`);
    const lowRisk = [], midRisk = [], highRisk = [];
    for (const [sym, p] of Object.entries(profile.profiles)) {
      if (p.risk === 'low') lowRisk.push(p);
      else if (p.risk === 'mid') midRisk.push(p);
      else highRisk.push(p);
    }
    if (lowRisk.length > 0) lines.push(`  🟢 **Low Risk**: ${lowRisk.map(p => `${p.label} — ${p.thesis}`).join('; ')}`);
    if (midRisk.length > 0) lines.push(`  🟡 **Mid Risk**: ${midRisk.map(p => `${p.label} — ${p.thesis}`).join('; ')}`);
    if (highRisk.length > 0) lines.push(`  🔴 **High Risk**: ${highRisk.map(p => `${p.label} — ${p.thesis}`).join('; ')}`);
    lines.push('');

    lines.push(`🔑 **Key Drivers**: ${profile.drivers}`);
    lines.push(`⚠️ **Key Risks**: ${profile.risks}`);
  }

  return lines.join('\n');
}

// Detect if user is asking about a sector/industry
function detectSector(query) {
  const q = query.toLowerCase();
  for (const [sectorKey, sector] of Object.entries(SECTOR_MAP)) {
    if (sector.keywords.some(kw => q.includes(kw.toLowerCase()))) {
      return sectorKey;
    }
  }
  return null;
}

// Fetch multiple stocks in a sector + sector ETF + commodity
async function fetchSectorData(sectorKey) {
  const sector = SECTOR_MAP[sectorKey];
  if (!sector) return null;

  // Fetch all sector stocks in parallel
  const stockPromises = sector.stocks.map(s => _fetchYahooChart(s.symbol));
  const etfPromise = sector.etf ? _fetchYahooChart(sector.etf.symbol) : Promise.resolve(null);
  const commodityPromise = sector.commodity ? _fetchYahooChart(sector.commodity.symbol) : Promise.resolve(null);

  const [stockResults, etfResult, commodityResult] = await Promise.all([
    Promise.all(stockPromises),
    etfPromise,
    commodityPromise,
  ]);

  const lines = [];
  lines.push(`【${sectorKey.toUpperCase()} SECTOR STOCKS】`);

  for (let i = 0; i < sector.stocks.length; i++) {
    const d = stockResults[i];
    if (d) {
      const dir = parseFloat(d.change) >= 0 ? '▲' : '▼';
      const emoji = parseFloat(d.change) >= 0 ? '🟢' : '🔴';
      lines.push(`${emoji} ${sector.stocks[i].label} (${d.symbol}): $${d.price} (${dir} ${d.changePct}%) | ${d.marketState}`);
    }
  }

  if (etfResult) {
    const dir = parseFloat(etfResult.change) >= 0 ? '▲' : '▼';
    const emoji = parseFloat(etfResult.change) >= 0 ? '🟢' : '🔴';
    lines.push(`\n【Sector ETF】${emoji} ${sector.etf.label} (${etfResult.symbol}): $${etfResult.price} (${dir} ${etfResult.changePct}%)`);
  }

  if (commodityResult) {
    const dir = parseFloat(commodityResult.change) >= 0 ? '▲' : '▼';
    lines.push(`【Commodity】${sector.commodity.label}: $${commodityResult.price} (${dir} ${commodityResult.changePct}%)`);
  }

  return lines.length > 1 ? lines.join('\n') : null;
}

// Fetch major indices — region: 'us' (US only) | 'cn' (China+HK only) | 'all' (default, US+China+HK)
async function fetchAllMarketData(region = 'all') {
  const usIndices = [
    { symbol: '^GSPC', label: 'S&P 500 (SPX)' },
    { symbol: '^DJI', label: 'Dow Jones (DJIA)' },
    { symbol: '^IXIC', label: 'NASDAQ Composite' },
    { symbol: '^VIX', label: 'VIX Fear Index' },
  ];
  const cnIndices = [
    { symbol: '000001.SS', label: '上证指数 (SSE)' },
    { symbol: '399001.SZ', label: '深证成指 (SZSE)' },
    { symbol: '000300.SS', label: '沪深300 (CSI300)' },
    { symbol: '^HSI', label: '恒生指数 (HSI)' },
  ];
  const indices = region === 'us' ? usIndices
    : region === 'cn' ? cnIndices
    : [...usIndices, ...cnIndices];
  const results = await Promise.all(indices.map(idx => _fetchYahooChart(idx.symbol)));
  const usLines = [];
  const cnLines = [];
  for (let i = 0; i < indices.length; i++) {
    if (results[i]) {
      const d = results[i];
      const dir = parseFloat(d.change) >= 0 ? '▲' : '▼';
      const prefix = indices[i].symbol === '^VIX' ? '' : (parseFloat(d.change) >= 0 ? '🟢' : '🔴');
      const line = `${prefix} ${indices[i].label}: ${d.price} ${d.currency} (${dir} ${d.changePct}%) | ${d.marketState}`;
      if (indices[i].symbol.startsWith('^') || indices[i].symbol === '^VIX') usLines.push(line);
      else cnLines.push(line);
    }
  }
  // Re-classify: US indices start with ^, CN indices are 6-digit codes
  const usFinal = []; const cnFinal = [];
  for (let i = 0; i < indices.length; i++) {
    if (!results[i]) continue;
    const d = results[i];
    const dir = parseFloat(d.change) >= 0 ? '▲' : '▼';
    const prefix = indices[i].symbol === '^VIX' ? '' : (parseFloat(d.change) >= 0 ? '🟢' : '🔴');
    const line = `${prefix} ${indices[i].label}: ${d.price} ${d.currency} (${dir} ${d.changePct}%) | ${d.marketState}`;
    if (indices[i].symbol.startsWith('^')) usFinal.push(line);
    else cnFinal.push(line);
  }
  const parts = [];
  if (usFinal.length) parts.push('【US Markets】\n' + usFinal.join('\n'));
  if (cnFinal.length) parts.push('【China/HK Markets】\n' + cnFinal.join('\n'));
  return parts.length > 0 ? parts.join('\n\n') : null;
}

async function fetchUSMarketData() {
  // Fetch real-time data for key US indices in parallel
  const indices = [
    { symbol: '^GSPC', label: 'S&P 500 (SPX)' },
    { symbol: '^DJI', label: 'Dow Jones (DJIA)' },
    { symbol: '^IXIC', label: 'NASDAQ Composite' },
    { symbol: '^VIX', label: 'VIX Fear Index' },
  ];
  const results = await Promise.all(indices.map(idx => _fetchYahooChart(idx.symbol)));
  const lines = [];
  for (let i = 0; i < indices.length; i++) {
    if (results[i]) {
      const d = results[i];
      const dir = parseFloat(d.change) >= 0 ? '▲' : '▼';
      const prefix = indices[i].symbol === '^VIX' ? '' : (parseFloat(d.change) >= 0 ? '🟢' : '🔴');
      lines.push(`${prefix} ${indices[i].label}: ${d.price} ${d.currency} (${dir} ${d.changePct}%) | Market: ${d.marketState}`);
    }
  }
  return lines.length > 0 ? lines.join('\n') : null;
}

async function fetchStockData(query) {
  // Fetch real-time stock data using multiple free APIs with CORS proxy fallback
  // v6: Smart ticker detection — case-insensitive, supports ANY stock code, auto-search
  const q = query.trim();
  const qLower = q.toLowerCase();

  // Step 1: Find matching symbol from our curated list (case-insensitive)
  let symbol = null;
  for (const [keyword, sym] of Object.entries(STOCK_SYMBOLS)) {
    if (qLower.includes(keyword.toLowerCase())) {
      // Skip special multi-index triggers (handled by isUSMarketQuery/isChinaMarketQuery)
      if (sym === 'US_MARKET' || sym === 'CHINA_MARKET') continue;
      symbol = sym;
      break;
    }
  }

  // Step 2: Extract potential ticker symbols from the message (case-insensitive)
  // Matches: standalone 1-5 letter codes, optionally with exchange prefix (e.g., "US PBM", "HK 0700")
  if (!symbol) {
    const words = q.split(/\s+/);
    for (const w of words) {
      const wl = w.toLowerCase();
      // Match: pure letters 1-5 chars, or letters+digits like "BRK-B"
      if (/^[A-Za-z]{1,5}(-[A-Za-z])?$/.test(w) && !STOP_WORDS.has(wl)) {
        symbol = w.toUpperCase();
        // Fix known suffixes: BRK-B stays, others become raw ticker
        break;
      }
    }
  }

  // Step 3: If we have "XX YYYY" pattern where XX looks like exchange code (US, HK, etc.)
  if (!symbol) {
    const exchangeMatch = q.match(/\b(US|HK|UK|JP|EU|CN|AU|CA|SG|DE|FR)\s+([A-Za-z0-9]{1,5}(?:\.[A-Za-z])?)\b/i);
    if (exchangeMatch) {
      const ticker = exchangeMatch[2].toUpperCase();
      const exCode = exchangeMatch[1].toUpperCase();
      // Map exchange prefixes to Yahoo Finance suffixes
      const exchangeMap = { 'HK': '.HK', 'UK': '.L', 'JP': '.T', 'EU': '.PA', 'CN': '.SS', 'AU': '.AX', 'CA': '.TO', 'SG': '.SI', 'DE': '.DE', 'FR': '.PA' };
      symbol = ticker + (exchangeMap[exCode] || '');
    }
  }

  // Step 4: Try to search Yahoo Finance for unknown tickers (auto-detect)
  if (!symbol) {
    // Extract the most likely ticker-like word from the query
    const tickerCandidates = q.split(/\s+/).filter(w => /^[A-Za-z]{2,5}$/.test(w));
    for (const candidate of tickerCandidates) {
      const lookupSymbol = candidate.toUpperCase();
      // Quick check: try to fetch this symbol directly
      const quickResult = await _fetchYahooChart(lookupSymbol);
      if (quickResult) return quickResult;
    }
    return null;
  }

  // Fetch data for the resolved symbol
  return await _fetchYahooChart(symbol);
}

// Internal: Fetch data from Yahoo Finance chart API
async function _fetchYahooChart(symbol) {
  const sources = [
    `https://corsproxy.io/?${encodeURIComponent(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=5d`)}`,
    `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=5d`,
  ];

  for (const url of sources) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const resp = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!resp.ok) continue;
      const data = await resp.json();
      const result = data?.chart?.result?.[0];
      if (!result) continue;

      const meta = result.meta || {};
      const closes = result.indicators?.quote?.[0]?.close || [];
      const lastPrice = closes[closes.length - 1];
      const prevPrice = closes[closes.length - 2] || lastPrice;
      const change = lastPrice - prevPrice;
      const changePct = prevPrice ? ((change / prevPrice) * 100).toFixed(2) : '0.00';
      const currency = meta.currency || 'USD';
      const symbolName = meta.symbol || symbol;

      return {
        symbol: symbolName,
        name: meta.shortName || meta.longName || symbolName,
        price: lastPrice?.toFixed(2),
        change: change?.toFixed(2),
        changePct: changePct,
        currency: currency,
        marketState: meta.marketState || 'UNKNOWN',
        exchange: meta.exchangeName || '',
        previousClose: meta.chartPreviousClose?.toFixed(2) || prevPrice?.toFixed(2),
      };
    } catch (e) {
      continue;
    }
  }

  return null;
}

async function callAI(userMessage) {
  // Try multiple AI sources: Pollinations (free, no key) → Groq (free tier) → local fallback
  const advisor = ADVISORS[currentAdvisor];
  const isChinese = /[\u4e00-\u9fff]/.test(userMessage);
  const lang = isChinese ? 'Chinese (中文)' : 'English';

  // SHORT system prompt — long prompts confuse free AI models
  const systemPrompt = `You are ${advisor.name}, a real investment advisor at BroadFSC. You are a REAL PERSON, not AI.

${advisor.personality}

LANGUAGE: You MUST respond in ${lang}. No exceptions. If user writes Chinese, you write Chinese.

STYLE: 2-4 sentences. Start with your OPINION. Talk like a friend at a bar, not a textbook. Have conviction — say "I like it" or "I'd avoid it", never "it depends".

BANNED PHRASES: Never say "I'd be happy to help", "Great question!", "As an AI", "it depends", "What specifically?", "Tell me more", "Could you clarify?", "do your own research".

REAL-TIME DATA: When live data is provided, you MUST use those EXACT numbers. NEVER make up index levels or stock prices from memory — they are outdated. If no live data, say "我需要看看最新数据" but don't make up numbers.

ANALYSIS: When asked about 技术/technical → trend(200MA) + entry(RSI+support) + stop(loss). When asked about 基本面/fundamental → valuation(PE/DCF) + earnings quality + ROIC vs WACC.`;

  // Check if user is asking about a stock/market and fetch data
  let marketContext = '';
  let isSectorQuery = false;
  
  // NOTE: Sector queries are now handled by buildSectorAnalysis() in sendChat()
  // — pure data template, no AI needed. callAI should NOT re-process sector queries.
  // detectSector() in callAI is kept as fallback only if buildSectorAnalysis fails.
  
  // Priority: China/HK market query → fetch multiple indices
  if (!marketContext && isChinaMarketQuery(userMessage)) {
    const chinaData = await fetchChinaMarketData();
    if (chinaData) {
      marketContext = `\n\n[LIVE CHINA/HK MARKET DATA — use these EXACT numbers, NOT your memory]:
${chinaData}

RULES: Quote each index with exact number + direction. Add your analysis. Respond in ${lang}.`;
    }
  }
  
  // Priority 2: US market query → fetch 4 major indices + VIX
  if (!marketContext && isUSMarketQuery(userMessage)) {
    const usData = await fetchUSMarketData();
    if (usData) {
      marketContext = `\n\n[LIVE US MARKET DATA — use these EXACT numbers, NOT your memory]:
${usData}

RULES: Quote exact numbers. Give your opinion on direction. VIX>25=fear, <15=complacent. Respond in ${lang}.`;
    }
  }
  
  // Priority 3: Analysis query (技术面/基本面/行情分析) → fetch ALL indices (US+China+HK)
  // ALSO: if query contains a stock ticker, fetch that stock too
  // ALSO: if query contains a sector keyword, fetch sector data too
  if (!marketContext && isAnalysisQuery(userMessage)) {
    const allData = await fetchAllMarketData();
    // Also try to fetch sector data if sector keyword detected
    const analysisSector = detectSector(userMessage);
    const sectorData = analysisSector ? await fetchSectorData(analysisSector) : null;
    // Also try to fetch individual stock if ticker detected in the query
    const stockData = await fetchStockData(userMessage);
    let stockContext = '';
    if (stockData) {
      const direction = parseFloat(stockData.change) >= 0 ? '▲ up' : '▼ down';
      stockContext = `\n\n[INDIVIDUAL STOCK DATA]:
${stockData.name || stockData.symbol}: $${stockData.price} ${stockData.currency} (${direction} ${stockData.changePct}%)
Prev Close: $${stockData.previousClose} | Market: ${stockData.marketState} | Exchange: ${stockData.exchange}`;
    }
    if (allData || stockContext || sectorData) {
      marketContext = `\n\n[LIVE GLOBAL MARKET DATA — use these EXACT numbers, NOT your memory]:
${allData || '(market data unavailable)'}${stockContext}
${sectorData ? '\n[SECTOR DATA]:\n' + sectorData : ''}

RULES: Quote exact numbers from this data. If stock data provided, analyze THAT stock. Respond in ${lang}.`;
    }
  }
  
  // Fallback: single stock query → ALSO fetch market data to prevent hallucinated index levels
  if (!marketContext) {
    const stockData = await fetchStockData(userMessage);
    if (stockData) {
      // Also fetch market data so AI doesn't make up index numbers
      const marketData = await fetchAllMarketData();
      const direction = parseFloat(stockData.change) >= 0 ? '▲ up' : '▼ down';
      marketContext = `\n\n[LIVE MARKET DATA — use these EXACT numbers, NOT your memory]:
${stockData.name || stockData.symbol}: $${stockData.price} ${stockData.currency} (${direction} ${stockData.changePct}%)
Prev Close: $${stockData.previousClose} | Market: ${stockData.marketState} | Exchange: ${stockData.exchange}
${marketData ? '\n[MARKET INDICES]:\n' + marketData : ''}

RULES: Quote exact price. Give your take on the move. Respond in ${lang}.`;
    }
  }

  // Build conversation history (last 6 messages for context)
  const history = (chatMessages[currentAdvisor] || []).slice(-6).map(m => ({
    role: m.role === 'user' ? 'user' : 'assistant',
    content: m.text
  }));

  // Add user name context if available
  const nameContext = userName ? `\n\nThe user's name is ${userName}. Use their name naturally sometimes, not every message.` : '';

  // Add memory context (user interests, language, visit history)
  const memoryContext = getMemoryContext();

  const messages = [
    { role: 'system', content: systemPrompt + marketContext + nameContext + memoryContext },
    ...history.slice(0, -1),
    { role: 'user', content: userMessage }
  ];

  // Try Pollinations first (free, no key, browser-friendly)
  if (_aiSourceWorking.pollinations) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 12000);
      const resp = await fetch(POLLINATIONS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messages,
          model: 'openai-large',
          seed: Math.floor(Math.random() * 100000),
          jsonMode: false
        }),
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (resp.ok) {
        const text = await resp.text();
        if (text && text.trim().length > 5) {
          // Clean up any AI-isms that leaked through
          let clean = text.trim()
            .replace(/^(As an AI|I'd be happy to|Great question!|As a|Let me help|Of course!|Certainly!|Sure!)\s*.*/i, '')
            .replace(/^(I'd\s+)?(be\s+)?(more\s+than\s+)?(happy|glad|pleased)\s+to\s+/i, '')
            .replace(/^(However,?\s*)?(Please\s+)?(note\s+that\s+)?(past\s+performance|this\s+is\s+not|do\s+your\s+own)/i, '')
            .replace(/\n{3,}/g, '\n\n');
          if (clean.length > 10) {
            return clean;
          }
        }
      }
      _aiSourceWorking.pollinations = false;
      // Re-enable after 5 minutes
      setTimeout(() => { _aiSourceWorking.pollinations = true; }, 300000);
    } catch (e) {
      _aiSourceWorking.pollinations = false;
      setTimeout(() => { _aiSourceWorking.pollinations = true; }, 300000);
    }
  }

  // Try Groq API as backup
  if (_aiSourceWorking.groq) {
    try {
      const controller2 = new AbortController();
      const timeout2 = setTimeout(() => controller2.abort(), 10000);
      const resp = await fetch(GROQ_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${_gk}`
        },
        body: JSON.stringify({
          model: GROQ_MODEL,
          messages: messages,
          max_tokens: 400,
          temperature: 0.85,
          top_p: 0.9
        }),
        signal: controller2.signal
      });
      clearTimeout(timeout2);

      if (resp.ok) {
        const data = await resp.json();
        const aiText = data?.choices?.[0]?.message?.content;
        if (aiText && aiText.trim().length > 5) {
          let clean = aiText.trim()
            .replace(/^(As an AI|I'd be happy to|Great question!|As a|Let me help|Of course!|Certainly!|Sure!)\s*.*/i, '')
            .replace(/^(I'd\s+)?(be\s+)?(more\s+than\s+)?(happy|glad|pleased)\s+to\s+/i, '')
            .replace(/^(However,?\s*)?(Please\s+)?(note\s+that\s+)?(past\s+performance|this\s+is\s+not|do\s+your\s+own)/i, '')
            .replace(/\n{3,}/g, '\n\n');
          if (clean.length > 10) return clean;
        }
      }
      _aiSourceWorking.groq = false;
      setTimeout(() => { _aiSourceWorking.groq = true; }, 300000);
    } catch (e) {
      _aiSourceWorking.groq = false;
      setTimeout(() => { _aiSourceWorking.groq = true; }, 300000);
    }
  }

  // All AI sources failed — return null to trigger local fallback
  return null;
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
    body.scrollTop = body.scrollHeight;
  }
}

function sendChat() {
  if (isSending) return;
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  isSending = true;

  addUserMessage(text);
  chatMessages[currentAdvisor].push({ role: 'user', text });
  const bodyEl = document.getElementById('chatBody');
  if (bodyEl) chatHistories[currentAdvisor] = bodyEl.innerHTML;
  input.value = '';

  // ── NEW FLOW: Local-first, AI-only for complex queries ──
  // Step 1: Try local response FIRST (greetings, casual chat, knowledge base = instant, perfect)
  const localResponse = getLocalResponse(text);

  // If local gave a good answer, use it immediately — no AI needed
  if (localResponse) {
    addBotMessage(localResponse);
    chatMessages[currentAdvisor].push({ role: 'bot', text: localResponse });
    const bodyAfter = document.getElementById('chatBody');
    if (bodyAfter) chatHistories[currentAdvisor] = bodyAfter.innerHTML;
    isSending = false;
    updateUserProfile(text, localResponse);
    return;
  }

  // Step 2: Sector query → pure data template (NO AI, instant, always professional)
  const isChineseInput = /[\u4e00-\u9fff]/.test(text);
  const sectorKey = detectSector(text);
  if (sectorKey) {
    showTyping();
    buildSectorAnalysis(sectorKey, isChineseInput).then(analysis => {
      removeTyping();
      if (analysis) {
        addBotMessage(analysis);
        chatMessages[currentAdvisor].push({ role: 'bot', text: analysis });
        const bodyAfter = document.getElementById('chatBody');
        if (bodyAfter) chatHistories[currentAdvisor] = bodyAfter.innerHTML;
        isSending = false;
        updateUserProfile(text, analysis);
      } else {
        // Sector data fetch failed → fall through to AI
        _tryAIResponse(text, learnedAnswer);
      }
    });
    return;
  }

  // Step 3: Not a sector query → try AI for stock data, analysis, etc.
  const learnedAnswer = getLearnedAnswer(text);
  _tryAIResponse(text, learnedAnswer);
}

// Shared AI response handler
function _tryAIResponse(text, learnedAnswer) {
  showTyping();

  callAI(text).then(aiResponse => {
    removeTyping();
    let botText = aiResponse;

    // Quality check — if AI gave garbage, use learned answer or a direct fallback
    if (!botText || isLowQualityResponse(text, botText)) {
      botText = learnedAnswer || getDirectFallback(text);
    }

    if (isLowQualityResponse(text, botText)) {
      recordFailedQuestion(text, botText);
    }

    updateUserProfile(text, botText);

    addBotMessage(botText);
    chatMessages[currentAdvisor].push({ role: 'bot', text: botText });
    const bodyAfter = document.getElementById('chatBody');
    if (bodyAfter) chatHistories[currentAdvisor] = bodyAfter.innerHTML;
    isSending = false;

    setTimeout(() => learnFromFailures(), 2000);
  }).catch(() => {
    removeTyping();
    let response = learnedAnswer || getDirectFallback(text);

    if (isLowQualityResponse(text, response)) {
      recordFailedQuestion(text, response);
    }

    updateUserProfile(text, response);

    addBotMessage(response);
    chatMessages[currentAdvisor].push({ role: 'bot', text: response });
    const bodyAfter = document.getElementById('chatBody');
    if (bodyAfter) chatHistories[currentAdvisor] = bodyAfter.innerHTML;
    isSending = false;

    setTimeout(() => learnFromFailures(), 2000);
  });
}

// Direct fallback when both AI and local fail — no questions, no AI-speak
function getDirectFallback(input) {
  const q = input.toLowerCase();
  const isChinese = /[\u4e00-\u9fff]/.test(input);
  if (isChinese) {
    // Try to be helpful based on what they asked
    if (/石油|能源|oil/i.test(q)) return '石油板块我可以帮你分析——直接问"美国石油股投资机会"我就能给出完整分析。';
    if (/科技|tech|芯片|ai/i.test(q)) return '科技板块我门儿清——问"科技股分析"我给你详细拆解。';
    if (/金融|银行|finance/i.test(q)) return '金融板块随时聊——问"金融股分析"我给你三档建议。';
    if (/军工|defense/i.test(q)) return '军工板块是长线逻辑——问"军工股分析"我给你详细看。';
    return pick([
      '我直接说——问我具体的东西：个股行情（如"苹果股票"）、板块分析（如"石油股投资机会"）、技术面基本面，我都能直接聊。',
      '换个具体问题吧——板块分析（石油/科技/金融/军工/医药/新能源/零售）、个股行情、技术面基本面，随便挑。',
    ]);
  }
  return pick([
    "Give me something specific — a sector (oil, tech, finance, defense, healthcare, renewable, retail), a stock ticker, or a strategy question — and I'll give you my honest take.",
    "What are you looking at? Try asking about a sector like 'oil stock opportunities' or 'tech sector analysis' — I've got data-driven answers ready.",
  ]);
}

function addUserMessage(text) {
  const body = document.getElementById('chatBody');
  const div = document.createElement('div');
  div.className = 'chat-msg user';
  div.textContent = text;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight; // Scroll to bottom — newest messages at bottom
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
  body.scrollTop = body.scrollHeight; // Scroll to bottom
}

function showTyping() {
  const body = document.getElementById('chatBody');
  const div = document.createElement('div');
  div.className = 'chat-msg bot';
  div.id = 'typingIndicator';
  div.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
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
  // Capture UTM tracking parameters from URL
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const utmSource = urlParams.get('utm_source');
    const utmMedium = urlParams.get('utm_medium');
    const utmCampaign = urlParams.get('utm_campaign');
    if (utmSource) {
      localStorage.setItem('bfs_utm_source', utmSource);
      localStorage.setItem('bfs_utm_medium', utmMedium || '');
      localStorage.setItem('bfs_utm_campaign', utmCampaign || '');
      // Store visit timestamp
      if (!localStorage.getItem('bfs_first_visit')) {
        localStorage.setItem('bfs_first_visit', new Date().toISOString());
      }
    }
  } catch (e) {}

  // Track outbound clicks on social/contact links
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href') || '';
    const isOutbound = href.includes('t.me/') || href.includes('broadfsc.com') || href.includes('twitter.com') || href.includes('mastodon.social') || href.includes('bsky.social') || href.includes('discord.com');
    if (isOutbound) {
      try {
        const clicks = JSON.parse(localStorage.getItem('bfs_outbound_clicks') || '[]');
        clicks.push({
          url: href,
          text: (link.textContent || '').trim().slice(0, 50),
          source: localStorage.getItem('bfs_utm_source') || 'direct',
          timestamp: new Date().toISOString()
        });
        if (clicks.length > 200) clicks.splice(0, clicks.length - 200);
        localStorage.setItem('bfs_outbound_clicks', JSON.stringify(clicks));
      } catch (e) {}
    }
  });

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
    chatHistories[currentAdvisor] = body.innerHTML;
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

 
 