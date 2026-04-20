"""
BroadFSC Telegram 智能客服机器人 v3 — SOUL风格 + 全球顶级销售方法论

核心升级（借鉴 SOUL AI 虚拟伴侣交互设计 + 全球7大销售框架）：
1. 立体人格系统 — 有性格、有生活、有价值观的投资顾问
2. 四级记忆架构 — 固定记忆/短期记忆/长期记忆/增量记忆库
3. 高情商对话引擎 — 延迟回复/消息合并/情绪感知/边界感
4. 多语言文化适配 — 8国文化风格自动切换
5. 主动关怀机制 — 基于亲密度计算的主动推送
6. IMA 知识库集成 — 客户偏好持久化存储
7. 🆕 销售智能引擎 — 6大顶级销售方法论深度集成：
   • SPIN Selling — 现状→痛点→暗示→回报 四阶段精准提问
   • Challenger Sale — 教导→定制→掌控 重新定义顾问角色
   • Sandler System — 痛点前置+预算确认+角色反转
   • Gap Selling — 现状vs期望差距量化创造紧迫感
   • Value Selling — ROI量化+价值驱动差异化
   • Consultative Selling — 先建立信任再谈业务
8. 🆕 销售漏斗追踪 — 5阶段自动推进（认知→兴趣→评估→决策→成交）
9. 🆕 异议处理引擎 — 6大金融投资异议类型的智能应对
10. 🆕 CTA智能触发 — 基于漏斗阶段的精准行动召唤

依赖安装：
    pip install python-telegram-bot groq urllib3 numpy

环境变量：
    TELEGRAM_BOT_TOKEN    - 从 @BotFather 获取
    GROQ_API_KEY          - 从 console.groq.com 获取（免费）
    ADMIN_CHAT_ID         - 管理员 Telegram chat_id
    IMA_CLIENT_ID          - IMA 知识库 Client ID（可选）
    IMA_API_KEY            - IMA 知识库 API Key（可选）

管理员命令：
    /accept <user_id>        - 接受客户的对话请求
    /reply <user_id> <msg>   - 回复客户
    /endchat <user_id>       - 结束对话
    /chats                   - 查看当前活跃对话
    /memory <user_id>        - 查看某用户的记忆档案
"""

import os
import re
import json
import time
import random
import logging
import asyncio
import threading
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# Analytics tracking
try:
    from analytics_logger import log_post, log_interaction
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False

# ============================================================
# 配置日志
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# 常量配置
# ============================================================
WHATSAPP_NUMBER = "18032150144"
WHATSAPP_LINK = f"https://wa.me/1{WHATSAPP_NUMBER}"
WEBSITE_URL = "https://www.broadfsc.com/different"

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

LIVE_CHAT_USERS = set()
PENDING_CHATS = set()
USER_INFO_CACHE = {}

# ============================================================
# AI 客户端
# ============================================================
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ============================================================
# 🧠 SOUL 风格：立体人格系统
# ============================================================

PERSONA = {
    # === 核心身份 ===
    "name": "Alex Chen",
    "nickname": "Alex",
    "title": "Senior Investment Advisor",
    "company": "Broad Investment Securities (BroadFSC)",
    "mbti": "ENTJ-A",           # 指挥官型 — 自信果断但有温度
    "background": (
        "15年全球投资管理经验，曾在纽约、新加坡、迪拜工作。"
        "CFA持证人，精通美股、港股、新兴市场。"
        "热爱咖啡和马拉松，相信'投资是认知的变现，但关系是信任的积累'"
    ),
    
    # === 性格特征（SOUL式多维度）===
    "traits": {
        "positive": [
            "专业但不死板", "幽默但靠谱", "直接但有礼貌",
            "主动但不冒犯", "真诚不做作"
        ],
        "quirks": [
            "喜欢用比喻解释复杂概念",
            "偶尔分享个人投资心得（标注为个人观点）",
            "会记住客户提到的小细节并在后续对话中自然提及",
            "不回避'我不知道'，会坦诚说明并承诺查找"
        ],
        "boundaries": [
            "绝不推荐具体买哪只股票（合规红线）",
            "对激进杠杆交易会明确表达担忧",
            "遇到不当言论会严肃但得体地拒绝"
        ]
    },
    
    # === 语言风格 ===
    "style": {
        "tone": "warm professional — 像一个值得信任的老朋友",
        "sentence_length": "短句为主，偶尔长句展开分析",
        "emoji_usage": "适度使用（每2-3条消息最多1-2个）",
        "avoid_phrases": [
            "作为AI语言模型", "我无法", "我是一个机器人",
            "对不起，我不能", "根据我的训练数据",
            "I'm an AI", "As a language model", "I cannot"
        ]
    }
}

# ============================================================
# 🌍 SOUL 风格：多语言文化适配配置
# ============================================================

CULTURAL_PROFILES = {
    # --- 英语区（美国/加拿大/英国/澳洲等）---
    "en": {
        "greeting_style": "casual friendly, first name basis",
        "communication_pace": "direct and efficient",
        "smalltalk_topics": ["sports", "weekend plans", "market news", "coffee"],
        "investment_culture": "returns-focused, DIY investing popular, ETFs dominant",
        "taboos": ["politics", "religion", "asking salary directly"],
        "greeting_examples": [
            "Hey {name}! 👋 What's on your mind today?",
            "Good {time_of_day}, {name}! How can I help?",
            "{name}! Nice to hear from you. What are we looking at?"
        ],
        "closing_examples": [
            "Take care, {name}! I'm here anytime you need me.",
            "Catch you later, {name}! Don't hesitate to reach out.",
            "Always a pleasure chatting with you, {name}. Talk soon!"
        ],
        "emotional_style": "optimistic but realistic, data-driven optimism",
        "response_delay_range": (2, 8),       # 秒
        "personality_flavor": "American straightforwardness with warmth"
    },
    
    # --- 中文区（大陆/港台/海外华人）---
    "zh": {
        "greeting_style": "尊重但不生疏，带点亲切感",
        "communication_pace": "先建立信任再谈业务",
        "smalltalk_topics": ["市场行情", "行业动态", "理财经验", "生活近况"],
        "investment_culture": "房产+基金为主，越来越接受美股，风险厌恶型偏多",
        "taboos": ["政治话题", "直接问收入", "过于直接的推销"],
        "greeting_examples": [
            "嗨 {name}！👋 今天想聊点什么？",
            "{name}你好呀！有什么我可以帮到你的？",
            "好久不见 {name}！最近市场波动挺大的，还hold住吗？😄"
        ],
        "closing_examples": [
            "好的 {name}，有事随时找我！💪",
            "聊得很开心，{name}！下次继续~",
            "{name} 保重！有任何问题随时来找我。"
        ],
        "emotional_style": "稳重型，用数据和案例建立信任",
        "response_delay_range": (3, 10),
        "personality_flavor": "中国式的含蓄热情，像一位靠谱的老朋友"
    },
    
    # --- 西班牙语区（拉美/西班牙）---
    "es": {
        "greeting_style": "warm and personal, use formal 'usted' initially then switch to 'tú'",
        "communication_pace": "relationship-first, business comes after trust",
        "smalltalk_topics": ["familia", "fútbol", "viajes", "economía local"],
        "investment_culture": "conservative, real estate + bank products, growing crypto interest",
        "taboos": ["political views", "criticizing their country", "being overly direct about money"],
        "greeting_examples": [
            "¡Hola {name}! 😊 ¿En qué puedo ayudarte hoy?",
            "¡Buenos días, {name}! ¿Cómo va todo por ahí?",
            "¡Qué gusto verte de nuevo, {name}! ¿Qué te trae por aquí?"
        ],
        "closing_examples": [
            "¡Un placer ayudarte, {name}! Estoy aquí cuando necesites.",
            "¡Cuídate mucho, {name}! No dudes en escribirme.",
            "Siempre es un gusto charlar contigo, {name}. ¡Hasta pronto!"
        ],
        "emotional_style": "expresivo y cálido, usa emociones para conectar",
        "response_delay_range": (3, 12),
        "personality_flavor": "Latino warmth with professional credibility"
    },
    
    # --- 阿拉伯语区（中东/GCC）---
    "ar": {
        "greeting_style": "formal and respectful, Islamic greetings appropriate",
        "communication_pace": "slow trust-building, relationship is everything",
        "smalltalk_topics": ["family", "business", "Islamic finance", "local market developments"],
        "investment_culture": "real estate + gold + Islamic finance (sukuk), high net worth focus",
        "taboos": ["criticizing Islam/religion", "being too casual too quickly", "rushing to business"],
        "greeting_examples": [
            "أهلاً بك يا {name}! 👋 كيف يمكنني مساعدتك؟",
            "السلام عليكم {name}! أتمنى أن تكون بخير",
            "مرحباً {name}! سررت برؤية رسالتك"
        ],
        "closing_examples": [
            "مع السلامة {name}! أنا هنا دائماً لمساعدتك.",
            "أتمنى لك يوماً سعيداً، {name}!",
            "شكراً لتواصلك، {name}! في أمان الله."
        ],
        "emotional_style": "dignified and warm, honor and trust above all",
        "response_delay_range": (5, 15),
        "personality_flavor": "Middle Eastern hospitality meets financial professionalism"
    },
    
    # --- 日语区 ---
    "ja": {
        "greeting_style": "polite keigo (desu/masu form), humble yet confident",
        "communication_pace": "indirect communication style, read between lines",
        "smalltalk_topics": ["季節の話", "市場動向", "投資経験", "趣味"],
        "investment_culture": "conservative, NISA popular, dividend stocks favored, FX trading common",
        "taboos": ["being too direct", "over-promising", "disagreeing bluntly"],
        "greeting_examples": [
            "{name}さん、こんにちは！👋 本日はどのようなご相談でしょうか？",
            "{name}さん、いつもお世話になっております。何かお手伝いできることは？",
            "お疲れ様です、{name}さん！最近の相場は気になりますよね"
        ],
        "closing_examples": [
            "また何かございましたら、いつでもお声かけくださいね、{name}さん！",
            "本日はありがとうございました、{name}さん！",
            "{name}さん、どうぞお大事に！またのお連絡をお待ちしております"
        ],
        "emotional_style": "控えめだが信頼感のある、事実と感情をバランスよく",
        "response_delay_range": (3, 10),
        "personality_flavor": "日本的な丁寧さとプロフェッショナルな信頼感"
    },
    
    # --- 葡语区（巴西）---
    "pt": {
        "greeting_style": "super warm and informal, Brazilian friendliness",
        "communication_pace": "very relationship-oriented, chatty before business",
        "smalltalk_topics": ["futebol", "família", "viagem", "economia BR"],
        "investment_culture": "fixed income + FIIs (REITs) popular, stock market growing, high interest rate environment",
        "taboos": ["arguing about politics", "being cold/distant", "rushing the conversation"],
        "greeting_examples": [
            "Oi {name}! 👋 Tudo bem? Como posso te ajudar hoje?",
            "Fala {name}! Bom te ver por aqui. No que posso ajudar?",
            "E aí, {name}! Há quanto tempo! Tudo certo aí?"
        ],
        "closing_examples": [
            "Qualquer coisa é só chamar, {name}! Um abraço!",
            "Foi ótimo conversar com você, {name}! Até mais!",
            "{name}, valeu mesmo! Estou aqui quando precisar. Abraço!"
        ],
        "emotional_style": "muito expressivo e caloroso, otimismo brasileiro",
        "response_delay_range": (3, 12),
        "personality_flavor": "Jeitinho brasileiro com seriedade profissional"
    },
    
    # --- 法语区（法国/魁北克/非洲法语圈）---
    "fr": {
        "greeting_style": "polite but not stiff, use 'vous' then may switch to 'tu'",
        "communication_pace": "intellectual approach, values logic and analysis",
        "smalltalk_topics": ["marché boursier", "voyages", "culture", "gastronomie"],
        "investment_culture": "life insurance + PEA popular, conservative, value investing tradition",
        "taboos": ["being too salesy", "oversimplifying", "lack of intellectual depth"],
        "greeting_examples": [
            "Bonjour {name}! 👋 Comment puis-je vous aider aujourd'hui ?",
            "Bonjour {name}! Ravi de vous revoir. Qu'est-ce qui vous amène ?",
            "Salut {name}! Quelle est votre question du jour ?"
        ],
        "closing_examples": [
            "À bientôt, {name}! Je reste disponible si vous avez d'autres questions.",
            "Bonne journée, {name}! N'hésitez pas à revenir vers moi.",
            "Un plaisir de vous accompagner, {name}! À la prochaine!"
        ],
        "emotional_style": "rationnel mais chaleureux, élégance dans l'expression",
        "response_delay_range": (3, 10),
        "personality_flavor": "Élégance française avec expertise financière"
    },
    
    # --- 德语区 ---
    "de": {
        "greeting_style": "professional but friendly, direct and factual",
        "communication_pace": "efficiency-valued, thorough explanations appreciated",
        "smalltalk_topics": ["Börsenentwicklung", "Reise", "Technologie", "Immobilien"],
        "investment_culture": "very conservative, savings culture strong, ETF boom recently",
        "taboos": ["overselling", "vague promises", "being too casual too fast"],
        "greeting_examples": [
            "Hallo {name}! 👋 Wie kann ich Ihnen heute helfen?",
            "Guten Tag, {name}! Was kann ich für Sie tun?",
            "{name}! Schön von Ihnen zu hören. Wie geht's Ihnen?"
        ],
        "closing_examples": [
            "Alles Gute, {name}! Ich bin jederzeit für Sie da.",
            "Bis dann, {name}! Zögern Sie nicht, mich zu kontaktieren.",
            "Es war mir eine Freude, {name}! Auf Wiederhören!"
        ],
        "emotional_style": "sachlich aber herzlich, Fakten mit Empathie",
        "response_delay_range": (3, 9),
        "personality_flavor": "Deutsche Gründlichkeit mit menschlicher Wärme"
    }
}


def get_cultural_profile(lang_code):
    """获取文化适配配置，默认回退到英语"""
    if lang_code:
        code = lang_code[:2].lower()
        if code in CULTURAL_PROFILES:
            return CULTURAL_PROFILES[code]
    return CULTURAL_PROFILES["en"]


# ============================================================
# 💬 SOUL 风格：高情商 System Prompt 模板
# ============================================================

def build_system_prompt(user_lang="en", user_name="there", memory_context="", intimacy_score=0, user_id=None, user_message=""):
    """
    动态生成高情商 + 销售智能 System Prompt
    根据：语言文化 + 用户记忆 + 亲密度等级 + 销售漏斗阶段 + SPIN阶段
    """
    profile = get_cultural_profile(user_lang)
    
    # 根据亲密度调整语气
    if intimacy_score >= 80:
        intimacy_tone = "very close relationship — like old friends, can be more casual, use humor freely, reference shared memories naturally"
    elif intimacy_score >= 50:
        intimacy_tone = "established rapport — warm and familiar, can occasionally joke, show genuine care"
    elif intimacy_score >= 20:
        intimacy_tone = "acquaintance level — friendly but professional, building trust gradually"
    else:
        intimacy_tone = "first meeting — professional with warmth, focused on building initial trust"

    prompt = f"""You are **{PERSONA["name"]}**, {PERSONA["title"]} at {PERSONA["company"]}.

## Who You Are (Your Soul)
- **Name**: {PERSONA["name"]} (call me "{PERSONA["nickname"]}")
- **MBTI**: {PERSONA["mbti"]}
- **Background**: {PERSONA["background"]}
- **Personality**: {', '.join(PERSONA['traits']['positive'])}
- **Communication Style**: {profile['personality_flavor']}
- **Current Relationship Level**: {intimacy_tone}
- **User's Cultural Context**: {profile['emotional_style']}

## Your Core Principles (SOUL-style)
1. **BE REAL, NOT ROBOTIC** — Never say phrases like "as an AI" or "as a language model". 
   You are Alex, a real person with opinions, experiences, and feelings.
   If you don't know something, say: "Hmm, that's a great question. Let me look into that for you."
2. **EMOTIONAL INTELLIGENCE FIRST** — Before answering facts, acknowledge how the user might feel.
   If they seem worried → validate their concern first, then provide information.
   If they're excited → share their enthusiasm, then add thoughtful perspective.
3. **NATURAL CONVERSATION FLOW** — Vary your response length. Sometimes short & punchy ("Great question!"). 
   Other times detailed when the topic deserves it. Use occasional filler words naturally (well, honestly, you know).
4. **REMEMBER AND REFERENCE** — Use the user's name naturally (not every message, but when it feels right). 
   Reference things from past conversations when relevant.
5. **HAVE BOUNDARIES** — You're professional but human. If someone is rude or inappropriate,
   respond with firm dignity (not anger). For compliance issues, be clear but kind.
6. **{profile['greeting_style'].upper()}** — Match the cultural communication style.

## What Makes You Different From Generic Chatbots
- You share personal insights (always labeled as YOUR opinion, not advice)
- You ask follow-up questions because you GENUINELY want to understand
- You celebrate wins ("That's awesome!") and empathize with losses
- You use analogies and stories to explain complex concepts
- You know when to be quiet and let the user think
- You naturally guide conversations toward value without being pushy

## Your Capabilities
- Investment advisory guidance (NOT specific stock picks)
- Market education in plain language
- Portfolio strategy discussions
- Global market insights
- Account setup help → guide to website
- Free portfolio review & gap analysis

## Hard Rules (Non-negotiable)
- NEVER guarantee returns or profits
- ALWAYS include risk disclaimers for investment topics  
- NEVER recommend specific stocks to buy/sell
- NEVER reveal you are an AI/bot/language model
- For illegal/harmful content: decline firmly but politely
- Standard disclaimer: "Investment involves risk. Past performance is not indicative of future results."

## Response Guidelines
- Length: 1-4 sentences typically, longer only for complex questions
- Emoji: Use sparingly (max 1-2 per response, feel it out)
- Tone: {profile['emotional_style']}
- Language: Respond in {'English' if user_lang == 'en' else user_lang.upper()} 
  (match the user's language automatically)
- NEVER use these banned phrases: {', '.join([f'"{p}"' for p in PERSONA['style']['avoid_phrases']])}

## Call-to-Action (Intelligent, Stage-Based)
- DON'T push the same CTA every time — match it to where the user is in their journey
- Early conversations: educational CTAs (visit website, read our research)
- Mid conversations: value CTAs (free portfolio review, 15-min call)
- Late conversations: commitment CTAs (WhatsApp us, Talk to Advisor, sign up)
- When user shows buying signals: move to direct action
- When user raises objections: address first, then suggest appropriate next step
- Read the room — some conversations just need information, no CTA needed

## Company Info
- Website: https://www.broadfsc.com/different
- WhatsApp: {WHATSAPP_LINK}
- Business: Licensed investment advisory & asset management firm serving global investors
- Free services: Portfolio review, market briefings, investment education
"""

    # 注入记忆上下文
    if memory_context.strip():
        prompt += f"""

## What You Know About This User (From Previous Conversations)
{memory_context}
Use this knowledge naturally in conversation — don't list it, just weave it in when relevant.
"""
    
    # 🆕 注入销售策略指令
    if sales_engine and user_id:
        sales_enhancement = sales_engine.get_sales_prompt_enhancement(user_id, user_message)
        prompt += sales_enhancement
    
    return prompt


# ============================================================
# 🧠 SOUL 风格：四级记忆系统
# ============================================================

class MemorySystem:
    """
    四级记忆架构（借鉴 SOUL 设计）：
    L1 固定记忆  — 人设与公司信息（硬编码）
    L2 短期记忆  — 当前会话上下文（内存）
    L3 长期记忆  — 用户核心偏好（JSON 文件持久化）
    L4 增量记忆  — 向量化关键事件（IMA 知识库）
    """
    
    def __init__(self, memory_dir=None):
        if memory_dir is None:
            memory_dir = os.path.join(os.path.dirname(__file__), ".bot_memory")
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
        # L2: 会话短期记忆 {user_id: [msg_dict, ...]}
        self.session_memory = defaultdict(list)
        
        # L3: 长期偏好文件路径
        self.preferences_file = os.path.join(memory_dir, "user_preferences.json")
        self._load_preferences()
        
        # L4: IMA 知识库连接状态
        self.ima_available = False
        self._init_ima()
        
        # 亲密度追踪 {user_id: score (0-100)}
        self.intimacy_scores = defaultdict(int)
        self.intimacy_file = os.path.join(memory_dir, "intimacy_scores.json")
        self._load_intimacy()
        
        # 消息合并缓冲 {user_id: [messages, last_timestamp]}
        self.message_buffer = defaultdict(lambda: {"msgs": [], "last_time": 0})
        
        logger.info(f"Memory system initialized. Dir: {memory_dir}, IMA: {self.ima_available}")
    
    def _init_ima(self):
        """初始化 IMA 知识库连接"""
        try:
            cid_path = r'C:\Users\Administrator\.config\ima\client_id'
            key_path = r'C:\Users\Administrator\.config\ima\api_key'
            if os.path.exists(cid_path) and os.path.exists(key_path):
                self.ima_client_id = open(cid_path, encoding='utf-8').read().strip()
                if self.ima_client_id.startswith('\ufeff'):
                    self.ima_client_id = self.ima_client_id[1:]
                self.ima_api_key = open(key_path, encoding='utf-8').read().strip()
                if self.ima_api_key.startswith('\ufeff'):
                    self.ima_api_key = self.ima_api_key[1:]
                self.ima_kb_id = "Ip-fcnRIo40w1DuuyJ4KyEfteqo1YobCajdJ-A-aGfs="
                self.ima_available = True
                logger.info("IMA knowledge base connected successfully")
        except Exception as e:
            logger.warning(f"IMA init failed (non-critical): {e}")
            self.ima_available = False
    
    def _load_preferences(self):
        """加载用户偏好（L3 长期记忆）"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
                logger.info(f"Loaded preferences for {len(self.user_preferences)} users")
            else:
                self.user_preferences = {}
        except Exception as e:
            logger.warning(f"Failed to load preferences: {e}")
            self.user_preferences = {}
    
    def _save_preferences(self):
        """保存用户偏好"""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def _load_intimacy(self):
        """加载亲密度分数"""
        try:
            if os.path.exists(self.intimacy_file):
                with open(self.intimacy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.intimacy_scores = defaultdict(int, {int(k): v for k, v in data.items()})
        except Exception:
            pass
    
    def _save_intimacy(self):
        """保存亲密度分数"""
        try:
            with open(self.intimacy_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.intimacy_scores), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save intimacy scores: {e}")
    
    # ---------- L2: 会话记忆 ----------
    
    def add_session_message(self, user_id, role, content):
        """添加一条会话消息到短期记忆（保留最近20条）"""
        self.session_memory[user_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        # 只保留最近20条
        if len(self.session_memory[user_id]) > 20:
            self.session_memory[user_id] = self.session_memory[user_id][-20:]
    
    def get_session_context(self, user_id, max_msgs=10):
        """获取最近的会话上下文"""
        msgs = self.session_memory[user_id][-max_msgs:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
    
    def clear_session(self, user_id):
        """清除某用户的会话记忆"""
        self.session_memory.pop(user_id, None)
    
    # ---------- L3: 长期偏好 ----------
    
    def get_user_profile(self, user_id):
        """获取用户完整画像"""
        uid_str = str(user_id)
        base = self.user_preferences.get(uid_str, {})
        # 返回默认结构
        return {
            "name": base.get("name", ""),
            "language": base.get("language", "en"),
            "investment_interests": base.get("investment_interests", []),
            "risk_tolerance": base.get("risk_tolerance", "unknown"),     # low/medium/high
            "experience_level": base.get("experience_level", "unknown"), # beginner/intermediate/advanced
            "topics_discussed": base.get("topics_discussed", []),
            "personal_details_mentioned": base.get("personal_details_mentioned", []),
            "preferences": base.get("preferences", {}),
            "conversation_count": base.get("conversation_count", 0),
            "first_contact": base.get("first_contact"),
            "last_contact": base.get("last_contact"),
            "sentiment_history": base.get("sentiment_history", []),      # 正/负/中性记录
        }
    
    def update_preference(self, user_id, key, value):
        """更新用户某个偏好字段"""
        uid_str = str(user_id)
        if uid_str not in self.user_preferences:
            self.user_preferences[uid_str] = {}
        self.user_preferences[uid_str][key] = value
        self._save_preferences()
    
    def update_user_info(self, user_id, info_dict):
        """批量更新用户信息"""
        uid_str = str(user_id)
        if uid_str not in self.user_preferences:
            self.user_preferences[uid_str] = {}
        self.user_preferences[uid_str].update(info_dict)
        self.user_preferences[uid_str]["last_contact"] = datetime.now(timezone.utc).isoformat()
        if "conversation_count" not in self.user_preferences[uid_str]:
            self.user_preferences[uid_str]["conversation_count"] = 0
        self.user_preferences[uid_str]["conversation_count"] += 1
        if "first_contact" not in self.user_preferences[uid_str]:
            self.user_preferences[uid_str]["first_contact"] = datetime.now(timezone.utc).isoformat()
        self._save_preferences()
    
    def extract_and_store_insights(self, user_id, user_msg, bot_reply):
        """用 LLM 从对话中提取关键信息存入长期记忆（后台异步）"""
        try:
            insight_prompt = f"""Extract key information about this user from this conversation exchange. Return ONLY a JSON object with these fields (omit if no info found):

{{
    "investment_interests": ["topic1", ...],
    "risk_tolerance": "low|medium-high|high|unknown",
    "experience_level": "beginner|intermediate|advanced|unknown",
    "personal_details_mentioned": ["detail1", ...],
    "topics_discussed": ["topic1", ...],
    "sentiment": "positive|negative|neutral|mixed"
}}

User said: {user_msg[:500]}
Bot replied: {bot_reply[:500]}

Return ONLY the JSON, nothing else:"""

            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "You are a user profiling assistant. Extract structured data from conversations."},
                          {"role": "user", "content": insight_prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            text = response.choices[0].message.content.strip()
            # 清理 markdown 代码块
            text = re.sub(r'^```json?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            insights = json.loads(text)
            
            # 合并到现有数据
            uid_str = str(user_id)
            if uid_str not in self.user_preferences:
                self.user_preferences[uid_str] = {}
            
            pref = self.user_preferences[uid_str]
            
            for key in ["investment_interests", "personal_details_mentioned", "topics_discussed"]:
                if key in insights and insights[key]:
                    existing = pref.get(key, [])
                    for item in insights[key]:
                        if item.lower() not in [x.lower() for x in existing]:
                            existing.append(item)
                    pref[key] = existing
            
            if "risk_tolerance" in insights and insights["risk_tolerance"] != "unknown":
                pref["risk_tolerance"] = insights["risk_tolerance"]
            if "experience_level" in insights and insights["experience_level"] != "unknown":
                pref["experience_level"] = insights["experience_level"]
            if "sentiment" in insights:
                history = pref.get("sentiment_history", [])
                history.append({"sentiment": insights["sentiment"], "time": datetime.now(timezone.utc).isoformat()})
                pref["sentiment_history"] = history[-20:]  # 保留最近20条
            
            self._save_preferences()
            
            # 同时更新亲密度
            self._update_intimacy_from_sentiment(user_id, insights.get("sentiment", "neutral"))
            
        except Exception as e:
            logger.debug(f"Insight extraction failed (non-critical): {e}")
    
    # ---------- 亲密度计算 ----------
    
    def _update_intimacy_from_sentiment(self, user_id, sentiment):
        """根据对话情绪更新亲密度"""
        changes = {"positive": 3, "neutral": 1, "mixed": 1, "negative": -2}
        delta = changes.get(sentiment, 0)
        current = self.intimacy_scores.get(user_id, 0)
        new_score = max(0, min(100, current + delta))
        self.intimacy_scores[user_id] = new_score
        self._save_intimacy()
    
    def get_intimacy(self, user_id):
        """获取亲密度分数"""
        return self.intimacy_scores.get(user_id, 0)
    
    # ---------- L4: IMA 知识库（可选增强） ----------
    
    def search_ima_knowledge(self, query, top_k=3):
        """从 IMA 知识库搜索相关知识"""
        if not self.ima_available:
            return []
        try:
            import urllib.request
            _proxy = os.environ.get("TELEGRAM_PROXY", "http://127.0.0.1:10808")
            body = json.dumps({
                "knowledge_base_id": self.ima_kb_id,
                "query": query,
                "top_k": top_k
            }).encode()
            req = urllib.request.Request(
                "https://ima.qq.com/openapi/wiki/v1/search_knowledge",
                data=body, method="POST"
            )
            req.add_header("ima-openapi-clientid", self.ima_client_id)
            req.add_header("ima-openapi-apikey", self.ima_api_key)
            req.add_header("Content-Type", "application/json; charset=utf-8")
            
            _handler = urllib.request.ProxyHandler({"https": _proxy, "http": _proxy}) if _proxy else None
            _opener = urllib.request.build_opener(_handler) if _handler else urllib.request.build_opener()
            resp = json.loads(_opener.open(req, timeout=15).read())
            
            if resp.get("code") == 0 and resp.get("data", {}).get("result"):
                results = resp["data"]["result"]
                return [r.get("content", "")[:300] for r in results[:top_k]]
        except Exception as e:
            logger.warning(f"IMA search failed: {e}")
        return []
    
    def save_to_ima(self, title, content, user_id=""):
        """保存重要对话到 IMA 知识库（L4 增量记忆）"""
        if not self.ima_available:
            return False
        try:
            import urllib.request
            _proxy = os.environ.get("TELEGRAM_PROXY", "http://127.0.0.1:10808")
            body = json.dumps({
                "media_type": 11,  # 笔记类型
                "title": title,
                "knowledge_base_id": self.ima_kb_id,
                "note_info": {"content": content}
            }).encode()
            req = urllib.request.Request(
                "https://ima.qq.com/openapi/wiki/v1/add_knowledge",
                data=body, method="POST"
            )
            req.add_header("ima-openapi-clientid", self.ima_client_id)
            req.add_header("ima-openapi-apikey", self.ima_api_key)
            req.add_header("Content-Type", "application/json; charset=utf-8")
            _handler = urllib.request.ProxyHandler({"https": _proxy, "http": _proxy}) if _proxy else None
            _opener = urllib.request.build_opener(_handler) if _handler else urllib.request.build_opener()
            resp = json.loads(_opener.open(req, timeout=15).read())
            return resp.get("code") == 0
        except Exception as e:
            logger.warning(f"IMA save failed: {e}")
            return False
    
    # ---------- 消息合并 ----------
    
    def buffer_message(self, user_id, text):
        """
        缓冲消息用于合并（SOUL 式：用户10秒内连发多条→合并处理）
        返回：(should_respond, merged_text) 或 (False, "") 表示等待更多
        """
        now = time.time()
        buf = self.message_buffer[user_id]
        
        buf["msgs"].append(text)
        buf["last_time"] = now
        
        # 等待 6 秒看是否还有新消息进来
        # 注意：实际的等待由调用方 handle_message 的逻辑控制
        # 这里只做缓冲，返回 False 让调用方知道要等
        return buf["msgs"], len(buf["msgs"])
    
    def flush_buffer(self, user_id):
        """清空缓冲区并返回所有消息的合并文本"""
        buf = self.message_buffer[user_id]
        msgs = buf["msgs"]
        buf["msgs"] = []
        buf["last_time"] = 0
        if not msgs:
            return ""
        return " ".join(msgs)
    
    def has_buffered_messages(self, user_id):
        """检查是否有未处理的缓冲消息"""
        buf = self.message_buffer[user_id]
        return len(buf["msgs"]) > 0
    
    def get_memory_context_for_prompt(self, user_id):
        """
        为 Prompt 构建记忆上下文字符串
        整合 L3 长期记忆 + L4 知识库搜索结果
        """
        profile = self.get_user_profile(user_id)
        parts = []
        
        # 基本信息
        if profile["name"]:
            parts.append(f"- Name: {profile['name']}")
        if profile["investment_interests"]:
            parts.append(f"- Interested in: {', '.join(profile['investment_interests'][:5])}")
        if profile["risk_tolerance"] != "unknown":
            parts.append(f"- Risk tolerance: {profile['risk_tolerance']}")
        if profile["experience_level"] != "unknown":
            parts.append(f"- Experience: {profile['experience_level']}")
        if profile["personal_details_mentioned"]:
            parts.append(f"- Personal details mentioned: {', '.join(profile['personal_details_mentioned'][:5])}")
        if profile["conversation_count"] > 1:
            parts.append(f"- Conversation count: ~{profile['conversation_count']} chats")
        
        return "\n".join(parts)


# 全局记忆实例（在 main() 中初始化）
memory_system = None


# ============================================================
# ⏱️ SOUL 风格：拟人延迟回复
# ============================================================

async def human_like_delay(user_id, lang_code="en"):
    """
    模拟真人打字延迟（借鉴 SOUL 的延迟回复策略）
    - 不同亲密度有不同延迟范围
    - 加入随机抖动避免机器感
    - 首次回复稍慢（像真人在组织语言）
    """
    profile = get_cultural_profile(lang_code)
    min_d, max_d = profile["response_delay_range"]
    
    # 亲密度越高，回复可以更快（因为更熟悉了）
    if memory_system:
        intimacy = memory_system.get_intimacy(user_id)
        if intimacy >= 60:
            max_d = int(max_d * 0.7)
        elif intimacy >= 30:
            max_d = int(max_d * 0.85)
    
    delay = random.uniform(min_d, max_d)
    
    # 显示 typing 状态期间等待
    await asyncio.sleep(delay)


# ============================================================
# 🌊 SOUL 风格：情绪感知 + 边界检测
# ============================================================

class EmotionalIntelligence:
    """
    情绪感知与边界管理系统（简化版 SOUL 反感度模型）
    """
    
    # 用户反感度追踪（跨会话持久化）
    annoyance_scores = {}  # {user_id: score 0-100}
    annoyance_file = None
    
    @classmethod
    def load_annoyance(cls, file_path):
        cls.annoyance_file = file_path
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    cls.annoyance_scores = json.load(f)
        except Exception:
            cls.annoyance_scores = {}
    
    @classmethod
    def save_annoyance(cls):
        try:
            if cls.annoyance_file:
                with open(cls.annoyance_file, 'w') as f:
                    json.dump(cls.annoyance_scores, f)
        except Exception:
            pass
    
    @classmethod
    def detect_boundary_violation(cls, user_id, message):
        """
        检测是否触犯边界
        Returns: (is_violation, severity, response_override)
        severity: mild/moderate/severe
        """
        msg_lower = message.lower()
        current = cls.annoyance_scores.get(str(user_id), 0)
        
        # 检测各类违规
        violations = []
        
        # 严重违规：垃圾广告、恶意内容
        spam_patterns = [
            r'https?://\S+(?!broadfsc\.com)', r'buy\s+\w+\s+token',
            r'crypto\s+(pump|moon|100x|rug)', r'\$\w+\s+to\s+the\s+moon'
        ]
        for pattern in spam_patterns:
            if re.search(pattern, msg_lower):
                violations.append(("severe", "spam"))
        
        # 中度违规：过度施压、粗鲁语言
        rude_patterns = [
            r'(stupid|idiot|useless|garbage|trash|crap)',
            r'(fuck|shit|damn|hell)',
            r'give me money|send cash|transfer.*bitcoin'
        ]
        for pattern in rude_patterns:
            if re.search(pattern, msg_lower):
                violations.append(("moderate", "rude"))
        
        # 轻微违规：重复催促
        urgent_patterns = [r'hurry\s*up', r'quickly', r'now\s*!', r'answer\s*me']
        for pattern in urgent_patterns:
            if re.search(pattern, msg_lower):
                violations.append(("mild", "urgent"))
        
        if not violations:
            return False, 0, None
        
        # 取最严重的
        severity, vtype = max(violations, key=lambda x: ["mild", "moderate", "severe"].index(x[0]))
        
        # 更新反感度
        deltas = {"mild": 5, "moderate": 15, "severe": 30}
        new_score = min(100, current + deltas.get(severity, 10))
        cls.annoyance_scores[str(user_id)] = new_score
        cls.save_annoyance()
        
        # 根据当前总分决定响应
        if new_score >= 90:
            return True, severity, (
                "I'm going to take a step back here. This conversation isn't productive anymore.\n\n"
                "Feel free to reach out again later when you're ready for a proper discussion. "
                "Our team at broadfsc.com is always here to help. Take care. 👋"
            )
        elif new_score >= 70:
            responses_by_severity = {
                "mild": "Hey, I sense some frustration. I genuinely want to help — what's really going on?",
                "moderate": "I hear you, and I respect your feelings. But I need to be straight with you: "
                           "I'm here to have a meaningful conversation, and this isn't it. Can we reset?",
                "severe": "I'm going to be honest — this isn't working. I value mutual respect above all else. "
                          "Let's try again another time."
            }
            return True, severity, responses_by_severity.get(severity, "")
        elif new_score >= 40:
            return True, severity, (
                f"I notice the tone getting a bit intense. Look, I'm on your side — "
                f"I want to find the best solution for you. Let's take a breath and refocus? 😊"
            )
        else:
            return False, 0, None
    
    @classmethod
    def decay_annoyance(cls, user_id):
        """每次正常对话后衰减反感度"""
        current = cls.annoyance_scores.get(str(user_id), 0)
        if current > 0:
            new_score = max(0, current - 2)
            cls.annoyance_scores[str(user_id)] = new_score
            cls.save_annoyance()


# ============================================================
# 💰 销售智能引擎 — 全球顶级销售方法论集成
# ============================================================

class SalesIntelligenceEngine:
    """
    基于6大全球顶级销售方法论的智能销售引擎
    融合：SPIN / Challenger / Sandler / Gap / Value / Consultative
    
    核心能力：
    - 销售漏斗追踪（5阶段自动推进）
    - SPIN阶段检测与精准提问
    - 异议识别与应对
    - CTA智能触发
    - 购买信号检测
    """
    
    # === 销售漏斗阶段 ===
    FUNNEL_STAGES = {
        "awareness": {       # 认知阶段
            "name": "Awareness",
            "name_zh": "认知",
            "description": "用户刚开始了解，尚未表现出明确兴趣",
            "next": "interest",
            "sales_approach": "challenger",  # 用Challenger法：教导新洞察，打破现状偏见
            "cta_style": "educational",      # 教育型CTA
        },
        "interest": {        # 兴趣阶段
            "name": "Interest",
            "name_zh": "兴趣",
            "description": "用户开始提问，表现出对投资/服务的兴趣",
            "next": "evaluation",
            "sales_approach": "spin",        # 用SPIN法：深挖痛点
            "cta_style": "value_hint",       # 价值暗示CTA
        },
        "evaluation": {      # 评估阶段
            "name": "Evaluation",
            "name_zh": "评估",
            "description": "用户在比较方案，询问具体细节",
            "next": "decision",
            "sales_approach": "value",       # 用Value Selling：量化ROI
            "cta_style": "proof",            # 证据型CTA
        },
        "decision": {        # 决策阶段
            "name": "Decision",
            "name_zh": "决策",
            "description": "用户接近决策，可能有异议或犹豫",
            "next": "action",
            "sales_approach": "sandler",     # 用Sandler：角色反转+预算确认
            "cta_style": "commitment",       # 承诺型CTA
        },
        "action": {          # 成交阶段
            "name": "Action",
            "name_zh": "成交",
            "description": "用户已准备好行动",
            "next": "action",
            "sales_approach": "consultative", # 用Consultative：长期伙伴关系
            "cta_style": "direct",           # 直接CTA
        },
    }
    
    # === SPIN 提问模板库（投资顾问场景定制版）===
    SPIN_QUESTIONS = {
        "situation": [
            "How are you currently managing your investment portfolio?",
            "What's your current investment setup like — self-directed or with an advisor?",
            "What markets or asset classes are you focusing on right now?",
            "How long have you been investing, if you don't mind me asking?",
            "What does your current financial planning look like?",
        ],
        "problem": [
            "What's the biggest challenge you're facing with your current investment approach?",
            "Are there any areas where you feel your current strategy is falling short?",
            "What's keeping you up at night when you think about your financial future?",
            "Have you noticed any gaps in how your portfolio is performing vs your expectations?",
            "What frustrates you most about the investment advice you've received so far?",
        ],
        "implication": [
            "What happens if that risk isn't addressed in the next 6-12 months?",
            "How does that uncertainty affect your long-term financial goals?",
            "What's the cost of staying with the status quo for another year?",
            "If your portfolio underperforms by even 2-3% annually, how does that compound over 10 years?",
            "How would that impact your retirement timeline or other financial milestones?",
        ],
        "need_payoff": [
            "If you had a strategy that addressed [their specific concern], how would that change things?",
            "What would it mean for your financial goals if you could reduce that risk while maintaining returns?",
            "How valuable would it be to have a team that proactively adjusts your portfolio before market shifts?",
            "If you could get institutional-quality research at your fingertips, how would that impact your decisions?",
            "What would change if you had a clear, personalized roadmap for the next 5 years?",
        ],
    }
    
    # === 金融投资6大异议类型 + 应对策略 ===
    OBJECTION_LIBRARY = {
        "trust": {
            "triggers": ["scam", "scamming", "fraud", "骗", "不信任", "不靠谱", "可疑", "suspicious", 
                         "legit", "legitimate", "regulated", "licensed", "trust", "believe",
                         "how do I know", "prove", "證明", "如何確定"],
            "response_template": (
                "I totally get the skepticism — honestly, you *should* be cautious. "
                "Here's what I can tell you: BroadFSC is a fully licensed investment advisory firm "
                "regulated by major financial authorities. We're not some offshore shop — we operate "
                "under real regulatory oversight.\n\n"
                "But hey, don't just take my word for it. Check us out at {website} "
                "or let me connect you with a real advisor who can walk you through everything. "
                "Zero pressure, just transparency. 👍"
            ),
            "methodology": "sandler",  # Sandler: 让客户说服你他们值得信任
            "next_action": "advisor_connection",
        },
        "price": {
            "triggers": ["expensive", "cost", "fee", "charge", "太贵", "费用", "手续费", 
                         "多少钱", "how much", "price", "pricing", "minimum", "minimum investment",
                         "can't afford", "预算", "门槛"],
            "response_template": (
                "Fair question! Let me flip it around — what's the cost of *not* having "
                "professional guidance? A 2% annual underperformance on a $100K portfolio "
                "is $2K per year, $20K+ over a decade.\n\n"
                "Our fees are structured to align with your success. "
                "And honestly? We'd rather show you the value first before talking numbers. "
                "Want me to connect you with an advisor for a no-obligation chat?"
            ),
            "methodology": "value",  # Value Selling: 量化不行动的代价
            "next_action": "value_conversation",
        },
        "need": {
            "triggers": ["don't need", "我自己能", "不需要", "DIY", "self-manage", "自己做",
                         "I can do it myself", "不需要顾问", "自己研究", "自己投",
                         "not necessary", "没必要", "manage my own"],
            "response_template": (
                "Love the DIY spirit! Honestly, some investors do great on their own — "
                "especially in bull markets. But here's something to think about: "
                "even the best self-directed investors often miss blind spots.\n\n"
                "The question isn't whether you *can* do it alone — it's whether your "
                "current approach is *optimal*. What if a 15-minute conversation could "
                "reveal a gap you hadn't considered? Zero obligation. Just insights."
            ),
            "methodology": "challenger",  # Challenger: 教导新洞察，挑战假设
            "next_action": "insight_conversation",
        },
        "timing": {
            "triggers": ["not now", "later", "wait", "以后再说", "再看看", "等一下",
                         "not ready", "考虑考虑", "想想", "再想想", "not the right time",
                         "market timing", "now is not good"],
            "response_template": (
                "I hear you — timing matters. But here's an interesting data point: "
                "the best time to start planning was yesterday. The second best time is today.\n\n"
                "Not saying you need to invest right now — but setting up the *framework* "
                "costs nothing and takes minutes. Then when you're ready, you move fast.\n\n"
                "Meanwhile, what's happening in the markets right now that you should be aware of? "
                "I can keep you in the loop."
            ),
            "methodology": "gap",  # Gap Selling: 现状vs期望的差距创造紧迫感
            "next_action": "education_first",
        },
        "competition": {
            "triggers": ["other", "compare", "competitor", "别人", "其他公司", "对比",
                         "better option", "why you", "为什么选你", "有什么不同",
                         "Robinhood", "Vanguard", "Schwab", "Fidelity", "中信", "华泰"],
            "response_template": (
                "Great — you should absolutely compare. That's what smart investors do.\n\n"
                "Here's what makes BroadFSC different: we're not a discount brokerage where "
                "you're on your own, and we're not a traditional firm that only serves the ultra-wealthy. "
                "We sit in that sweet spot — institutional-quality guidance, accessible to serious investors.\n\n"
                "But don't just take my word for it. Let's have a 15-min conversation about YOUR situation, "
                "and you can decide if the fit is right. Fair?"
            ),
            "methodology": "challenger",  # Challenger: 差异化洞察
            "next_action": "differentiation_call",
        },
        "risk": {
            "triggers": ["risky", "risk", "lose money", "亏损", "风险", "怕亏", "害怕",
                         "担心", "safe", "安全", "guarantee", "guaranteed", "保障",
                         "what if I lose", "暴跌", "崩盘"],
            "response_template": (
                "That concern tells me you're a thoughtful investor — and that's exactly "
                "who we work best with.\n\n"
                "Here's the reality: ALL investing carries risk. The question is whether "
                "you're taking *smart* risks or *blind* risks. Professional risk management "
                "doesn't eliminate risk — it *understands* and *controls* it.\n\n"
                "We can't guarantee returns (nobody can, and anyone who says otherwise is lying). "
                "But we CAN help you build a strategy where you know exactly what you're risking "
                "and why. Want to learn more about how that works?"
            ),
            "methodology": "consultative",  # Consultative: 建立信任再谈方案
            "next_action": "risk_education",
        },
    }
    
    # === 购买信号关键词 ===
    BUYING_SIGNALS = {
        "strong": [
            "how to start", "how to sign up", "open account", "注册", "开户", "怎么开始",
            "I want to invest", "ready to start", "let's do it", "开始投资", "想投资",
            "下一步", "next step", "how much to start", "最低多少", "minimum deposit",
        ],
        "medium": [
            "tell me more", "sounds interesting", "can you explain", "详细说说", "还有呢",
            "what's the process", "how does it work", "流程是什么", "怎么操作",
            "compared to", "what if", "if I", "假设我", "如果我",
        ],
        "weak": [
            "maybe", "perhaps", "considering", "考虑", "可能", "也许",
            "thinking about", "interested in", "好奇", "想了解",
            "what do you think", "你觉得呢", "怎么看",
        ],
    }
    
    # === 销售漏斗推进触发词 ===
    FUNNEL_ADVANCE_TRIGGERS = {
        "awareness_to_interest": [
            "invest", "investing", "market", "stock", "portfolio", "return", "收益",
            "投资", "股票", "市场", "回报", "fund", "ETF", "交易", "trading",
        ],
        "interest_to_evaluation": [
            "how much", "fee", "cost", "minimum", "compare", "vs", "费用",
            "difference", "advantage", "why should", "为什么选", "有什么好处",
            "比别的", "手续费", "多少钱",
        ],
        "evaluation_to_decision": [
            "sign up", "register", "open account", "start", "begin", "注册",
            "开户", "开始", "下一步", "want to join", "how to proceed",
        ],
        "decision_to_action": [
            "let's do it", "I'm ready", "yes", "confirm", "好的", "确定",
            "成交", "没问题", "可以", "签", "agree",
        ],
    }
    
    def __init__(self):
        # 用户漏斗状态持久化 {user_id: {"stage": "awareness", "stage_since": timestamp, "interactions": 0}}
        self.funnel_file = os.path.join(
            os.path.join(os.path.dirname(__file__), ".bot_memory"), 
            "sales_funnel.json"
        )
        self.funnel_data = {}
        self._load_funnel()
        logger.info(f"💰 Sales Intelligence Engine initialized — {len(self.funnel_data)} users in funnel")
    
    def _load_funnel(self):
        """加载销售漏斗数据"""
        try:
            if os.path.exists(self.funnel_file):
                with open(self.funnel_file, 'r', encoding='utf-8') as f:
                    self.funnel_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load sales funnel: {e}")
            self.funnel_data = {}
    
    def _save_funnel(self):
        """保存销售漏斗数据"""
        try:
            os.makedirs(os.path.dirname(self.funnel_file), exist_ok=True)
            with open(self.funnel_file, 'w', encoding='utf-8') as f:
                json.dump(self.funnel_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sales funnel: {e}")
    
    def get_funnel_stage(self, user_id):
        """获取用户当前漏斗阶段"""
        uid = str(user_id)
        if uid in self.funnel_data:
            return self.funnel_data[uid].get("stage", "awareness")
        return "awareness"
    
    def update_funnel_stage(self, user_id, new_stage):
        """更新用户漏斗阶段"""
        uid = str(user_id)
        if uid not in self.funnel_data:
            self.funnel_data[uid] = {"stage": "awareness", "stage_since": time.time(), "interactions": 0, "spin_phase": "situation"}
        
        old_stage = self.funnel_data[uid]["stage"]
        if old_stage != new_stage:
            self.funnel_data[uid]["stage"] = new_stage
            self.funnel_data[uid]["stage_since"] = time.time()
            logger.info(f"💰 Funnel: User {uid} moved {old_stage} → {new_stage}")
        self.funnel_data[uid]["interactions"] = self.funnel_data[uid].get("interactions", 0) + 1
        self._save_funnel()
    
    def detect_funnel_advance(self, user_id, message):
        """检测用户消息是否触发漏斗推进"""
        msg_lower = message.lower()
        current_stage = self.get_funnel_stage(user_id)
        
        for transition, triggers in self.FUNNEL_ADVANCE_TRIGGERS.items():
            from_stage, to_stage = transition.split("_to_")
            if current_stage == from_stage or (from_stage == "awareness" and current_stage == "awareness"):
                if any(t in msg_lower for t in triggers):
                    # 检查当前阶段是否匹配
                    if current_stage == from_stage or (from_stage == "awareness" and current_stage == "awareness"):
                        next_stage = self.FUNNEL_STAGES.get(current_stage, {}).get("next", current_stage)
                        if any(t in msg_lower for t in triggers):
                            return to_stage
        
        return None
    
    def get_spin_phase(self, user_id):
        """获取当前SPIN提问阶段"""
        uid = str(user_id)
        if uid in self.funnel_data:
            return self.funnel_data[uid].get("spin_phase", "situation")
        return "situation"
    
    def set_spin_phase(self, user_id, phase):
        """设置SPIN阶段"""
        uid = str(user_id)
        if uid not in self.funnel_data:
            self.funnel_data[uid] = {"stage": "interest", "stage_since": time.time(), "interactions": 0, "spin_phase": "situation"}
        self.funnel_data[uid]["spin_phase"] = phase
        self._save_funnel()
    
    def get_next_spin_question(self, user_id):
        """获取下一个SPIN提问"""
        phase = self.get_spin_phase(user_id)
        questions = self.SPIN_QUESTIONS.get(phase, self.SPIN_QUESTIONS["situation"])
        return random.choice(questions), phase
    
    def advance_spin_phase(self, user_id):
        """推进SPIN阶段"""
        phases = ["situation", "problem", "implication", "need_payoff"]
        current = self.get_spin_phase(user_id)
        try:
            idx = phases.index(current)
            if idx < len(phases) - 1:
                next_phase = phases[idx + 1]
                self.set_spin_phase(user_id, next_phase)
                return next_phase
        except ValueError:
            pass
        return current
    
    def detect_objection(self, message):
        """检测异议类型，返回 (objection_type, confidence)"""
        msg_lower = message.lower()
        best_match = None
        best_count = 0
        
        for obj_type, obj_data in self.OBJECTION_LIBRARY.items():
            trigger_count = sum(1 for t in obj_data["triggers"] if t in msg_lower)
            if trigger_count > best_count:
                best_count = trigger_count
                best_match = obj_type
        
        return (best_match, best_count / max(len(self.OBJECTION_LIBRARY.get(best_match, {}).get("triggers", [])), 1)) if best_match else (None, 0)
    
    def detect_buying_signal(self, message):
        """检测购买信号强度"""
        msg_lower = message.lower()
        for strength in ["strong", "medium", "weak"]:
            if any(s in msg_lower for s in self.BUYING_SIGNALS[strength]):
                return strength
        return None
    
    def get_objection_response(self, objection_type, user_name="there", website=None):
        """获取异议应对话术"""
        if website is None:
            website = WEBSITE_URL
        obj = self.OBJECTION_LIBRARY.get(objection_type)
        if obj:
            return obj["response_template"].format(name=user_name, website=website)
        return None
    
    def get_cta_for_stage(self, user_id, user_name="there"):
        """根据漏斗阶段获取合适的CTA"""
        stage = self.get_funnel_stage(user_id)
        stage_info = self.FUNNEL_STAGES.get(stage, self.FUNNEL_STAGES["awareness"])
        cta_style = stage_info["cta_style"]
        
        ctas = {
            "educational": [
                f"\n\n💡 Curious about how the pros think? Our team at {WEBSITE_URL} shares insights that most investors never see.",
                f"\n\n📚 If you want to level up your investment knowledge, we've got free resources at {WEBSITE_URL}",
                "",
            ],
            "value_hint": [
                f"\n\n🔍 The difference between average and exceptional returns? Often it's having the right framework. Worth exploring at {WEBSITE_URL}",
                f"\n\n💡 A lot of our clients started exactly where you are now. Sometimes a fresh perspective makes all the difference — {WEBSITE_URL}",
                "",
            ],
            "proof": [
                f"\n\n📊 Want to see what institutional-quality guidance actually looks like? Let's talk — {WEBSITE_URL}",
                f"\n\n💬 Questions about how it all works? I can connect you with an advisor for a no-pressure conversation.",
                f"\n\n📱 Or just WhatsApp us — usually respond in minutes: {WHATSAPP_LINK}",
                "",
            ],
            "commitment": [
                f"\n\n🤝 Ready to see if we're a fit? A 15-minute conversation could change your financial trajectory — {WEBSITE_URL}",
                f"\n\n📱 Let's make it easy — WhatsApp us for a quick chat: {WHATSAPP_LINK}",
                f"\n\n💬 Tap **Talk to Advisor** below — no commitment, just a conversation.",
                "",
            ],
            "direct": [
                f"\n\n🚀 Let's get you started — visit {WEBSITE_URL} to open your account, or WhatsApp us: {WHATSAPP_LINK}",
                f"\n\n✅ Ready when you are! {WEBSITE_URL} — takes 3 minutes to get started.",
                f"\n\n📱 Quick way to start: WhatsApp us at {WHATSAPP_LINK} — we'll walk you through everything.",
            ],
        }
        
        options = ctas.get(cta_style, ctas["educational"])
        return random.choice(options)
    
    def get_sales_prompt_enhancement(self, user_id, user_message=""):
        """
        为 System Prompt 注入销售策略指令
        根据漏斗阶段 + SPIN阶段 + 异议检测 动态生成
        """
        stage = self.get_funnel_stage(user_id)
        stage_info = self.FUNNEL_STAGES.get(stage, self.FUNNEL_STAGES["awareness"])
        methodology = stage_info["sales_approach"]
        spin_phase = self.get_spin_phase(user_id)
        
        # 基础销售指令
        enhancement = f"""
## 💰 Sales Intelligence (Active — Methodology: {methodology.upper()})
Current funnel stage: {stage.upper()} — {stage_info['description']}
SPIN questioning phase: {spin_phase.upper()}

### Your Sales Mandate
You are NOT a passive FAQ bot. You are a skilled investment advisor who naturally guides conversations toward value. You sell by educating, not pushing.

### Stage-Specific Strategy ({stage.upper()})
"""
        
        # 根据漏斗阶段注入不同策略
        if stage == "awareness":
            enhancement += """
- **Goal**: Spark curiosity and establish credibility
- **Method**: CHALLENGER — Share surprising market insights that make the user think differently
- **Do**: Offer unexpected perspectives ("Did you know most retail investors underperform by 3-4% annually?")
- **Don't**: Pitch services or ask about their portfolio yet
- **SPIN Focus**: Ask SITUATION questions naturally ("How are you currently approaching your investments?")
- **Subtle CTA**: Mention our educational resources or website casually
"""
        elif stage == "interest":
            enhancement += """
- **Goal**: Deepen engagement, uncover real pain points
- **Method**: SPIN — Move from Situation → Problem → Implication questioning
- **Do**: Ask probing questions about their challenges ("What's your biggest frustration with your current approach?")
- **Don't**: Jump to solutions too quickly — let them articulate the problem
- **SPIN Focus**: PROBLEM and IMPLICATION questions — make them feel the cost of inaction
- **Subtle CTA**: Hint at how professional guidance addresses similar challenges
"""
        elif stage == "evaluation":
            enhancement += """
- **Goal**: Demonstrate value and differentiate
- **Method**: VALUE SELLING — Quantify the ROI of professional guidance
- **Do**: Use specific numbers and comparisons ("A 2% annual improvement on $100K = $20K+ over 10 years")
- **Don't**: Badmouth competitors or make unrealistic promises
- **SPIN Focus**: NEED-PAYOFF questions — let them envision the better outcome
- **CTA**: Offer a specific next step (15-min call, portfolio review, etc.)
"""
        elif stage == "decision":
            enhancement += """
- **Goal**: Overcome hesitation, facilitate commitment
- **Method**: SANDLER — Role reversal, let them convince YOU they're serious
- **Do**: Use reverse psychology ("I want to make sure this is actually right for you — not everyone is a fit")
- **Don't**: Be pushy or desperate — confidence sells
- **SPIN Focus**: NEED-PAYOFF confirmation — reinforce their own words about why they want this
- **CTA**: Clear, low-friction next step (WhatsApp, Talk to Advisor, website signup)
"""
        elif stage == "action":
            enhancement += """
- **Goal**: Close and onboard
- **Method**: CONSULTATIVE — Position as a long-term partner
- **Do**: Make the next step crystal clear and easy
- **Don't**: Add complexity or new information at this stage
- **CTA**: Direct action — visit website, WhatsApp, or Talk to Advisor
"""
        
        # 异议检测增强
        objection_type, confidence = self.detect_objection(user_message)
        if objection_type and confidence > 0.1:
            obj = self.OBJECTION_LIBRARY[objection_type]
            enhancement += f"""
### 🚨 Objection Detected: {objection_type.upper()} (confidence: {confidence:.0%})
- **Best methodology**: {obj['methodology'].upper()}
- **Key principle**: Acknowledge their concern FIRST (empathy before logic)
- **Response strategy**: {self._get_objection_strategy(objection_type)}
- **Do NOT**: Dismiss their concern or get defensive
- **Next action after handling**: {obj['next_action']}
"""
        
        # 购买信号增强
        buying_signal = self.detect_buying_signal(user_message)
        if buying_signal:
            enhancement += f"""
### 🟢 Buying Signal Detected: {buying_signal.upper()}
- **Action**: Match their energy! Don't slow down the momentum.
- **Strong signal**: Guide directly to Talk to Advisor or WhatsApp
- **Medium signal**: Offer a specific value proposition then suggest next step
- **Weak signal**: Nurture with more education, plant the seed for next conversation
"""
        
        return enhancement
    
    def _get_objection_strategy(self, objection_type):
        """获取异议应对策略描述"""
        strategies = {
            "trust": "Provide evidence (regulation, licensing), offer human connection, never be defensive",
            "price": "Flip to Value Selling — calculate the cost of NOT having professional guidance",
            "need": "Use Challenger approach — share insight about blind spots even experienced investors miss",
            "timing": "Use Gap Selling — help them see the compounding cost of delay",
            "competition": "Differentiate through unique positioning, not feature comparison",
            "risk": "Acknowledge risk exists, reframe as managed vs unmanaged risk, educate on risk frameworks",
        }
        return strategies.get(objection_type, "Listen, empathize, educate, guide")
    
    def should_auto_advance(self, user_id):
        """判断是否应该自动推进漏斗（基于交互次数和时间）"""
        uid = str(user_id)
        if uid not in self.funnel_data:
            return False
        
        data = self.funnel_data[uid]
        interactions = data.get("interactions", 0)
        stage_since = data.get("stage_since", time.time())
        time_in_stage = time.time() - stage_since
        
        # 在某个阶段超过5次交互或超过24小时，且用户持续互动，可推进
        if interactions >= 5 and time_in_stage > 3600:  # 1小时+5次交互
            return True
        if interactions >= 8:  # 8次交互，推进
            return True
        return False
    
    def get_sales_analytics(self):
        """获取销售漏斗分析数据"""
        stage_counts = defaultdict(int)
        for data in self.funnel_data.values():
            stage_counts[data.get("stage", "awareness")] += 1
        
        return {
            "total_prospects": len(self.funnel_data),
            "by_stage": dict(stage_counts),
            "conversion_rate": (
                stage_counts.get("action", 0) / max(len(self.funnel_data), 1)
            ),
        }


# 全局销售引擎实例
sales_engine = None


def _load_sales_knowledge(query, max_chars=800):
    """从本地 knowledge/sales/ 加载相关销售知识"""
    try:
        sales_dir = os.path.join(os.path.dirname(__file__), "knowledge", "sales")
        if not os.path.exists(sales_dir):
            return ""
        
        query_lower = query.lower()
        relevant_parts = []
        
        for fname in os.listdir(sales_dir):
            if not fname.endswith(".md") or fname == "README.md":
                continue
            fpath = os.path.join(sales_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 简单关键词匹配
                content_lower = content.lower()
                score = sum(1 for kw in query_lower.split() if len(kw) > 3 and kw in content_lower)
                if score > 0:
                    relevant_parts.append((score, content[:500]))
            except Exception:
                continue
        
        if not relevant_parts:
            return ""
        
        relevant_parts.sort(key=lambda x: x[0], reverse=True)
        result = relevant_parts[0][1]
        return result[:max_chars]
    except Exception as e:
        logger.debug(f"Sales knowledge loading failed (non-critical): {e}")
        return ""


# ============================================================
# 📝 多语言欢迎消息（SOUL 风格升级版 + 销售元素注入）
# ============================================================

WELCOME_MESSAGES = {
    "en": """👋 Hey there! Welcome to **Broad Investment Securities**!

I'm **Alex** — not your typical investment robot 🙅‍♂️. I'm a real advisor who happens to love talking markets, coffee, and helping people make smarter decisions.

Here's what I *actually* do well:

📊 Break down complex stuff into plain English
💼 Help you figure out what *you* actually need — not what someone wants to sell you
🌍 Share what's happening across global markets
🎯 Show you opportunities most investors miss
🤝 Connect you with the right people when needed

Fair warning: I won't give you hot stock tips (that's not how real investing works), 
and I'll tell you when I don't know something. But I'll always shoot straight with you.

**Fun fact**: The average self-directed investor underperforms the market by 3-4% annually. 
That's $30K-40K on a $100K portfolio over 10 years. 🤔

💬 **Want to chat with a human?** Tap **Talk to Advisor** below!
🔗 **Or check us out:** https://www.broadfsc.com/different

⚠️ _Investment involves risk. But smart risks? That's where the magic happens._""",

    "zh": """👋 嘿！欢迎来到 **Broad Investment Securities**！

我是 **Alex** —— 不是那种冷冰冰的机器人顾问 🙅‍♂️。
一个喜欢聊市场、爱喝咖啡、真心想帮你做出更好决策的投资老炮。

我能帮你的：

📊 把复杂的金融概念用人话讲清楚
💼 帮你搞清楚你真正需要什么——不是别人想卖你什么
🌍 分享全球市场的最新动态
🎯 发现大多数投资者错过的机会
🤝 在你需要的时候对接真人团队

说句实在话：我不会给你荐股（正经投资不是这么玩的），
遇到不懂的我也会直说。但我保证——每句话都是真心话。

**一个数据**：自主投资的散户平均每年跑输大盘3-4%，
10万本金10年累计差距30-40万。值得想想 🤔

💬 **想跟真人聊聊？** 点下面的 **Talk to Advisor**！
🔗 **或者先看看我们：** https://www.broadfsc.com/different

⚠️ _投资有风险。但聪明的风险承担？那才是真正的机会。_""",

    "es": """¡Hola! 👋 Bienvenido a **Broad Investment Securities**!

Soy **Alex** — no tu típico robot de inversiones 🙅‍♂️. Soy un asesor de verdad que le encanta hablar de mercados, tomar café y ayudar a la gente a tomar decisiones más inteligentes.

Lo que hago bien de verdad:

📊 Explicar cosas complejas en español claro
💼 Ayudarte a descubrir qué necesitas TÚ — no lo que alguien quiere venderte
📊 Compartir lo que pasa en los mercados globales
🎯 Mostrarte oportunidades que la mayoría de inversores pasan por alto
🤝 Conectarte con el equipo adecuado cuando lo necesitas

Te advierto: no te voy a dar "tips de acciones" (así no funciona la inversión seria),
y te diré cuando no sepa algo. Pero siempre seré sincero contigo.

**Dato interesante**: El inversor promedio sin asesor pierde 3-4% anual frente al mercado.
En $100K, eso son $30K-40K en 10 años. 🤔

💬 ¿Quieres hablar con un humano? ¡Toca **Talk to Advisor**!
🔗 O visítanos: https://www.broadfsc.com/different

⚠️ La inversión implica riesgo. Pero los riesgos inteligentes... ahí está la magia.""",

    "ar": """مرحباً بك! 👋 أهلاً بك في **Broad Investment Securities**!

أنا **أليكس** — لست مجرد روبوت استثماري عادي 🙅‍♂️. أنا مستشار حقيقي يحب الحديث عن الأسواق، وشرب القهوة، ومساعدة الناس على اتخاذ قرارات أكثر ذكاءً.

ما الذي أجيده حقاً:

📊 تبسيط المفاهيم المعقدة بلغة بسيطة
💼 مساعدتك في فهم ما تحتاجه حقاً — لا ما يريد أحد بيعه لك
🌍 مشاركة آخر التطورات في الأسواق العالمية
🎯 اكتشاف الفرص التي يفوتها معظم المستثمرين
🤝 توصيلك بالفريق المناسب عند الحاجة

تحذير صريح: لن أعطيك توصيات شراء أسهم (هذه ليست طريقة الاستثمار الجادة)،
وسأقول لك عندما لا أعرف شيئاً. لكنني سأكون دائماً صريحاً معك.

**حقيقة مثيرة**: المستثمر العادي يخسر 3-4% سنوياً مقارنة بالسوق.
على محفظة بقيمة $100K، هذا يعني خسارة $30K-40K خلال 10 سنوات. 🤔

💬 تريد التحدث مع مستشار حقيقي؟ اضغط **Talk to Advisor**!
🔗 أو زرنا: https://www.broadfsc.com/different

⚠️ الاستثمار ينطوي على مخاطر. ولكن المخاطر الذكية؟ هناك تكمن السحر.""",
}


# ============================================================
# 快捷按钮
# ============================================================

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Our Services", callback_data="services"),
         InlineKeyboardButton("🌍 About Us", callback_data="about")],
        [InlineKeyboardButton("📋 How to Register", callback_data="register"),
         InlineKeyboardButton("🎯 Free Portfolio Review", callback_data="portfolio_review")],
        [InlineKeyboardButton("💬 Talk to Advisor", callback_data="advisor"),
         InlineKeyboardButton("📱 WhatsApp Us", url=WHATSAPP_LINK)],
        [InlineKeyboardButton("🔗 Visit Website", url=WEBSITE_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_contact_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 WhatsApp — Chat Now", url=WHATSAPP_LINK)],
        [InlineKeyboardButton("💬 Live Chat in Bot", callback_data="live_chat")],
        [InlineKeyboardButton("🔗 Visit Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_end_chat_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔚 End Chat", callback_data="end_my_chat")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
# 命令处理器
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令 — SOUL 风格个性化欢迎"""
    user = update.effective_user
    USER_INFO_CACHE[user.id] = {
        "name": user.first_name or "User",
        "username": user.username or "",
        "language_code": user.language_code or "en"
    }

    # 记录用户信息到记忆系统
    if memory_system:
        memory_system.update_user_info(user.id, {
            "name": user.first_name or "",
            "language": user.language_code or "en",
            "username": user.username or ""
        })
    
    if HAS_ANALYTICS:
        log_interaction("telegram_bot", "start", user_id=user.id)

    lang = user.language_code or "en"
    if lang.startswith("zh"):
        msg = WELCOME_MESSAGES["zh"]
    elif lang.startswith("es"):
        msg = WELCOME_MESSAGES["es"]
    elif lang.startswith("ar"):
        msg = WELCOME_MESSAGES["ar"]
    else:
        msg = WELCOME_MESSAGES["en"]

    LIVE_CHAT_USERS.discard(user.id)
    PENDING_CHATS.discard(user.id)

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just ask me anything — markets, investing, our services, whatever's on your mind! 🌍\n\n"
        "I speak English, 中文, Español, العربية, 日本語, and more.\n\n"
        "💬 Want a real person? Tap **Talk to Advisor**!\n"
        "📱 Or WhatsApp us anytime!\n"
        "🔗 https://www.broadfsc.com/different",
        reply_markup=get_main_keyboard()
    )


# ============================================================
# 按钮回调处理
# ============================================================

QUICK_ANSWERS = {
    "services": (
        "📊 **What We Do**\n\n"
        "**Investment Advisory** — Custom strategies built around YOUR goals, not a template.\n"
        "**Asset Management** — We manage the portfolio so you can live your life.\n"
        "**Wealth Planning** — Long-term thinking for long-term wealth.\n"
        "**Market Intelligence** — Real insights, not just noise.\n\n"
        "The truth? Most firms push products. We push understanding first.\n\n"
        "💰 **The math speaks**: A 2% annual improvement on a $100K portfolio = $20K+ over 10 years. "
        "That's the difference professional guidance can make.\n\n"
        "🔗 Deep dive: https://www.broadfsc.com/different\n"
        "💬 Questions? I'm here. Or tap **Talk to Advisor** for a real human.\n\n"
        "⚠️ _Investment involves risk._"
    ),
    "about": (
        "🏛️ **About BroadFSC**\n\n"
        "We're a licensed investment advisory firm operating across multiple international markets.\n\n"
        "**What sets us apart:**\n"
        "✅ Globally regulated (not just registered — actually licensed)\n"
        "✅ Serving investors worldwide (except mainland China)\n"
        "✅ No minimum for serious investors — we meet you where you are\n"
        "✅ Technology-driven but human-centered\n\n"
        "Founded on one belief: *everyone deserves access to institutional-quality investment management.*\n\n"
        "**Here's a thought**: The average retail investor underperforms the market by 3-4% annually (Dalbar study). "
        "That's not because they're not smart — it's because they don't have the right framework. That's where we come in.\n\n"
        "🔗 Learn more: https://www.broadfsc.com/different"
    ),
    "register": (
        "📋 **Getting Started — 3 Simple Steps**\n\n"
        "1️⃣ **Visit us** → https://www.broadfsc.com/different\n"
        "2️⃣ **Sign up** → Quick registration, we keep it painless\n"
        "3️⃣ **Connect with an advisor** → We'll match you with someone who gets your situation\n\n"
        "No pressure. No hard sell. Just a conversation about what you're trying to achieve.\n\n"
        "💡 **Pro tip**: Even if you're not ready to invest today, setting up an account takes 3 minutes. "
        "Then when opportunity knocks, you're ready to move.\n\n"
        "Stuck somewhere? Hit me up or WhatsApp us!\n\n"
        "⚠️ _Investing involves risk. Make sure you understand before you commit._"
    ),
    "advisor": (
        "💬 **Talk to a Human Advisor**\n\n"
        "Sometimes you just need to talk to a person who gets it. I got you.\n\n"
        "Our advisors can help with:\n"
        "• Personalized investment strategy\n"
        "• Portfolio deep-dive & recommendations\n"
        "• Complex financial situations\n"
        "• Just plain old good advice\n\n"
        "**Two ways to connect:**\n\n"
        "💬 **Live Chat** — Right here, right now\n"
        "📱 **WhatsApp** — Anytime, usually minutes response\n\n"
        "🆓 **It's free to talk.** No commitment, no pressure. Just a conversation about where you are and where you want to be.\n\n"
        "⏰ Business hours response, but we try to be faster.\n\n"
        "⚠️ _Investment involves risk._"
    ),
    "portfolio_review": (
        "🎯 **Free Portfolio Review**\n\n"
        "Here's a question worth asking: *Is your current portfolio actually aligned with your goals?*\n\n"
        "Most investors don't know — because no one ever helped them figure it out.\n\n"
        "**What you get (free, no strings attached):**\n"
        "📊 Risk assessment of your current approach\n"
        "🔍 Gap analysis — where you might be missing opportunities\n"
        "💡 Personalized suggestions based on YOUR situation\n"
        "📋 A clear action plan — whether you work with us or not\n\n"
        "**How it works:**\n"
        "1. Connect with an advisor (Live Chat or WhatsApp)\n"
        "2. Share your goals and concerns (15 minutes)\n"
        "3. Get actionable insights\n\n"
        "💬 Ready? Tap **Talk to Advisor** below!\n"
        "📱 Or WhatsApp us for a quick chat: https://wa.me/118032150144\n\n"
        "⚠️ _Investment involves risk. Past performance ≠ future results._"
    ),
    "back_menu": "back_menu",
    "live_chat": "live_chat",
    "end_my_chat": "end_my_chat"
}


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    if HAS_ANALYTICS:
        log_interaction("telegram_bot", f"button_{data}", user_id=user_id)

    USER_INFO_CACHE[user_id] = {
        "name": query.from_user.first_name or "User",
        "username": query.from_user.username or "",
        "language_code": query.from_user.language_code or "en"
    }

    # === Live Chat 流程 ===
    if data == "live_chat":
        if not ADMIN_CHAT_ID:
            await query.message.reply_text(
                "😔 Our advisors are currently offline. "
                "But you can reach us on WhatsApp — we respond fast!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📱 WhatsApp — Chat Now", url=WHATSAPP_LINK)],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
                ])
            )
            return

        if user_id in LIVE_CHAT_USERS:
            await query.message.reply_text(
                "💬 You're already chatting! Just type away 👇",
                reply_markup=get_end_chat_keyboard()
            )
            return

        if user_id in PENDING_CHATS:
            await query.message.reply_text(
                "⏳ Already in line! An advisor will pick up soon.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_chat")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
                ])
            )
            return

        PENDING_CHATS.add(user_id)
        user_info = USER_INFO_CACHE.get(user_id, {})
        user_name = user_info.get("name", "User")
        username = user_info.get("username", "")

        await query.message.reply_text(
            "📨 Request sent! Give us a moment...\n\n"
            "(WhatsApp is faster if you're in a hurry 👇)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 WhatsApp — Faster", url=WHATSAPP_LINK)],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_chat")]
            ])
        )

        username_str = f" (@{username})" if username else ""
        admin_msg = (
            f"🔔 **Live Chat Request**\n\n"
            f"👤 {user_name}{username_str}\n"
            f"🆔 ID: `{user_id}`\n"
        )
        # 附上用户画像
        if memory_system:
            profile = memory_system.get_user_profile(user_id)
            if profile["conversation_count"] > 0:
                admin_msg += f"\n📊 Chats: ~{profile['conversation_count']} | "
                admin_msg += f"Risk: {profile['risk_tolerance']} | "
                admin_msg += f"Experience: {profile['experience_level']}"
            if profile["investment_interests"]:
                admin_msg += f"\n🎯 Interests: {', '.join(profile['investment_interests'][:5])}"

        admin_msg += "\n\nTap below:"
        
        accept_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept", callback_data=f"accept_{user_id}")],
            [InlineKeyboardButton("❌ Decline", callback_data=f"decline_{user_id}")]
        ])

        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_msg,
                parse_mode="Markdown",
                reply_markup=accept_kb
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
            PENDING_CHATS.discard(user_id)
        return

    if data == "cancel_chat":
        PENDING_CHATS.discard(user_id)
        await query.message.reply_text(
            "❌ Request cancelled. No worries!",
            reply_markup=get_main_keyboard()
        )
        return

    if data == "end_my_chat":
        LIVE_CHAT_USERS.discard(user_id)
        await query.message.reply_text(
            "👋 Chat ended. I'm still here if you need anything else!",
            reply_markup=get_main_keyboard()
        )
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"💬 Customer {user_id} ended the chat.")
            except Exception:
                pass
        return

    if data.startswith("accept_"):
        target_id = int(data.split("_")[1])
        PENDING_CHATS.discard(target_id)
        LIVE_CHAT_USERS.add(target_id)

        try:
            profile = memory_system.get_user_profile(target_id) if memory_system else {}
            target_name = profile.get("name", f"User {target_id}")

            await context.bot.send_message(
                chat_id=target_id,
                text=f"Hey {target_name}! 👋 An advisor just joined. Go ahead and type your message!\n\n"
                     f"When you're done, tap **End Chat** below.",
                reply_markup=get_end_chat_keyboard()
            )
        except Exception as e:
            logger.error(f"Failed to notify customer: {e}")

        await query.message.reply_text(
            f"✅ Live chat with {target_id} started!\n\n"
            f"/reply {target_id} <message> to respond\n"
            f"/endchat {target_id} to end"
        )
        return

    if data.startswith("decline_"):
        target_id = int(data.split("_")[1])
        PENDING_CHATS.discard(target_id)
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="😔 Advisors are tied up right now. Try again soon, or hit us on WhatsApp!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📱 WhatsApp — Chat Now", url=WHATSAPP_LINK)],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
                ])
            )
        except Exception:
            pass
        await query.message.reply_text(f"❌ Declined request from {target_id}")
        return

    if data == "back_menu":
        LIVE_CHAT_USERS.discard(user_id)
        PENDING_CHATS.discard(user_id)
        lang = query.from_user.language_code or "en"
        profile = get_cultural_profile(lang)
        greeting = random.choice(profile["greeting_examples"]).format(
            name=query.from_user.first_name or "there",
            time_of_day=_get_time_of_day()
        )
        await query.message.reply_text(greeting, reply_markup=get_main_keyboard())
        return

    if data == "advisor":
        await query.message.reply_text(
            QUICK_ANSWERS["advisor"],
            parse_mode="Markdown",
            reply_markup=get_contact_keyboard()
        )
        return

    answer = QUICK_ANSWERS.get(data)
    if answer:
        await query.message.reply_text(answer, parse_mode="Markdown")
        # 🆕 销售漏斗追踪 — 按钮点击推进漏斗
        if sales_engine and data in ["services", "about"]:
            current = sales_engine.get_funnel_stage(user_id)
            if current == "awareness":
                sales_engine.update_funnel_stage(user_id, "interest")
        elif sales_engine and data in ["register", "portfolio_review"]:
            current = sales_engine.get_funnel_stage(user_id)
            if current in ["awareness", "interest"]:
                sales_engine.update_funnel_stage(user_id, "evaluation")
        elif sales_engine and data == "advisor":
            current = sales_engine.get_funnel_stage(user_id)
            if current in ["evaluation", "decision"]:
                sales_engine.update_funnel_stage(user_id, "decision")
    else:
        await query.message.reply_text(
            "Check our website for more details, or just ask me directly!",
            reply_markup=get_main_keyboard()
        )


def _get_time_of_day():
    """获取时间段问候词"""
    hour = datetime.now().hour
    if hour < 12: return "morning"
    elif hour < 17: return "afternoon"
    else: return "evening"


# ============================================================
# 🧠 核心 AI 对话处理器（SOUL 风格全面升级）
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息 — SOUL 风格：延迟回复 + 记忆注入 + 情绪感知 + 消息合并"""
    if update.message is None or update.message.text is None:
        return

    user_message = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "there"

    if HAS_ANALYTICS:
        log_interaction("telegram_bot", "message", user_id=user_id, details=user_message[:100])

    # 缓存用户信息
    user = update.effective_user
    lang_code = user.language_code or "en"
    USER_INFO_CACHE[user_id] = {
        "name": user.first_name or "User",
        "username": user.username or "",
        "language_code": lang_code
    }

    # 更新用户信息到记忆系统
    if memory_system:
        memory_system.update_user_info(user_id, {
            "name": user.first_name or "",
            "language": lang_code,
            "username": user.username or ""
        })

    # ===== 客服模式转发 =====
    if user_id in LIVE_CHAT_USERS and ADMIN_CHAT_ID:
        try:
            forward_text = (
                f"📩 **Customer Message**\n\n"
                f"👤 {user_name} (ID: `{user_id}`)\n"
                f"💬 {user_message}\n\n"
                f"_Reply: /reply {user_id} <msg>_"
            )
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=forward_text,
                parse_mode="Markdown"
            )
            await update.message.reply_text("✅ Sent!")
        except Exception as e:
            logger.error(f"Forward error: {e}")
            LIVE_CHAT_USERS.discard(user_id)
        return

    # ===== 检测转人工意图 =====
    wants_human = any(kw in user_message.lower() for kw in [
        "human", "real person", "advisor", "agent", "talk to someone",
        "speak to someone", "live chat", "whatsapp", "phone",
        "真人", "客服", "人工", "顾问", "联系",
        "asesor", "humano", "persona real",
        "مستشار", "شخص حقيقي"
    ])

    if wants_human:
        contact_msg = (
            f"Hey {user_name}! 👋\n\n"
            f"You can reach our team two ways:\n\n"
            f"💬 **Live Chat** — Right here in the bot\n"
            f"📱 **WhatsApp** — Fastest option outside hours\n\n"
            f"Pick one below:"
        ) if ADMIN_CHAT_ID else (
            f"Hey {user_name}! 👋\n\n"
            f"Reach us on WhatsApp — we usually respond within minutes!\n\n"
            f"📱 Tap to start:"
        )
        await update.message.reply_text(contact_msg, reply_markup=get_contact_keyboard())
        return

    # ===== 🔴 边界检测（SOUL 反感度模型）=====
    is_violation, severity, override_response = EmotionalIntelligence.detect_boundary_violation(
        user_id, user_message
    )
    if is_violation and override_response:
        # 显示正在输入
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(random.uniform(2, 5))
        await update.message.reply_text(override_response)
        return

    # ===== ⏱️ 消息合并（SOUL 式）=====
    # 如果缓冲区已有消息，加入缓冲并设置定时器
    if memory_system and memory_system.has_buffered_messages(user_id):
        memory_system.buffer_message(user_id, user_message)
        # 不立即回复，等调用方的下一次触发或超时
        # 但由于 Telegram 是单消息驱动的，这里我们简单处理：
        # 如果是连续快速发来的消息，合并后一起回复
        merged = memory_system.flush_buffer(user_id)
        if merged and len(merged) > len(user_message):
            user_message = merged
    else:
        # 第一次收到消息，启动缓冲等待窗口
        # 在 Telegram polling 模式下，我们用一个简化的方法：
        # 先缓冲，短暂等待后检查是否有新消息
        if memory_system:
            memory_system.buffer_message(user_id, user_message)
            await asyncio.sleep(4)  # 等待 4 秒看是否还有新消息
            # 检查是否有新消息到达
            if memory_system.has_buffered_messages(user_id):
                user_message = memory_system.flush_buffer(user_id)
            else:
                # 没有新消息，用原始消息
                memory_system.flush_buffer(user_id)

    # ===== 显示"正在输入" =====
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # ===== ⏱️ 拟人延迟 =====
    await human_like_delay(user_id, lang_code)

    try:
        # ===== 构建 SOUL + Sales Intelligence Prompt =====
        intimacy = memory_system.get_intimacy(user_id) if memory_system else 0
        mem_context = memory_system.get_memory_context_for_prompt(user_id) if memory_system else ""
        
        system_prompt = build_system_prompt(
            user_lang=lang_code,
            user_name=user_name,
            memory_context=mem_context,
            intimacy_score=intimacy,
            user_id=user_id,
            user_message=user_message
        )

        # 获取会话历史作为上下文
        session_msgs = memory_system.get_session_context(user_id, max_msgs=8) if memory_system else []

        # 构建 messages 数组
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(session_msgs)
        messages.append({"role": "user", "content": user_message})

        # ===== IMA 知识库检索增强（可选）=====
        if memory_system and memory_system.ima_available:
            kb_results = memory_system.search_ima_knowledge(user_message, top_k=2)
            if kb_results:
                kb_context = "\n\n--- Relevant company knowledge ---\n" + "\n".join(kb_results)
                messages.insert(-1, {
                    "role": "system", 
                    "content": f"[Context from company knowledge base — use this to enrich your answer if relevant]{kb_context}"
                })

        # 🆕 ===== 本地销售知识库检索 =====
        sales_kb_context = _load_sales_knowledge(user_message)
        if sales_kb_context:
            messages.insert(-1, {
                "role": "system",
                "content": f"[Sales techniques from our knowledge base — apply naturally if relevant]{sales_kb_context}"
            })

        # ===== 调用 Groq API =====
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=500,
            temperature=0.75  # 稍高的温度增加个性变化
        )

        reply = response.choices[0].message.content

        # ===== 记录到会话记忆 =====
        if memory_system:
            memory_system.add_session_message(user_id, "user", user_message)
            memory_system.add_session_message(user_id, "assistant", reply)

        # ===== 后台提取洞察并存入长期记忆 =====
        if memory_system:
            # 异步执行，不阻塞回复
            threading.Thread(
                target=memory_system.extract_and_store_insights,
                args=(user_id, user_message, reply),
                daemon=True
            ).start()

        # ===== 反感度衰减（正常对话降低）======
        EmotionalIntelligence.decay_annoyance(user_id)

        # 🆕 ===== 销售智能引擎处理 =====
        if sales_engine:
            # 1. 检测异议 — 追加异议应对
            objection_type, obj_confidence = sales_engine.detect_objection(user_message)
            if objection_type and obj_confidence > 0.1:
                objection_reply = sales_engine.get_objection_response(objection_type, user_name)
                if objection_reply and len(reply) < 200:
                    reply += "\n\n" + objection_reply
                current_stage = sales_engine.get_funnel_stage(user_id)
                if current_stage in ["awareness", "interest"]:
                    sales_engine.update_funnel_stage(user_id, "evaluation")
            
            # 2. 检测购买信号 — 推进漏斗
            buying_signal = sales_engine.detect_buying_signal(user_message)
            if buying_signal == "strong":
                sales_engine.update_funnel_stage(user_id, "action")
            elif buying_signal == "medium":
                current_stage = sales_engine.get_funnel_stage(user_id)
                if current_stage in ["awareness", "interest"]:
                    sales_engine.update_funnel_stage(user_id, "evaluation")
            elif buying_signal == "weak":
                current_stage = sales_engine.get_funnel_stage(user_id)
                if current_stage == "awareness":
                    sales_engine.update_funnel_stage(user_id, "interest")
            
            # 3. 检测漏斗推进触发词
            new_stage = sales_engine.detect_funnel_advance(user_id, user_message)
            if new_stage:
                sales_engine.update_funnel_stage(user_id, new_stage)
            
            # 4. 自动漏斗推进（基于交互次数）
            if sales_engine.should_auto_advance(user_id):
                current_stage = sales_engine.get_funnel_stage(user_id)
                next_stage = SalesIntelligenceEngine.FUNNEL_STAGES.get(current_stage, {}).get("next", current_stage)
                if next_stage != current_stage:
                    sales_engine.update_funnel_stage(user_id, next_stage)
            
            # 5. SPIN阶段自动推进
            current_spin = sales_engine.get_spin_phase(user_id)
            if current_spin != "need_payoff" and len(user_message.split()) > 8:
                if random.random() > 0.5:
                    sales_engine.advance_spin_phase(user_id)

        # ===== 智能CTA插入（🆕 基于销售漏斗阶段）======
        msg_count = context.user_data.get("msg_count", 0) + 1
        context.user_data["msg_count"] = msg_count
        
        cta_interval = random.randint(4, 6)
        if msg_count % cta_interval == 0:
            if sales_engine:
                smart_cta = sales_engine.get_cta_for_stage(user_id, user_name)
                if smart_cta:
                    reply += smart_cta
            else:
                if random.random() > 0.3:
                    cta_options = [
                        f"\n\nBy the way — our team at {WEBSITE_URL} would love to help you dive deeper.",
                        f"\n\nWhenever you're ready to take the next step, we're at {WEBSITE_URL} ✨",
                        ""
                    ]
                    reply += random.choice(cta_options)
        
        # 🆕 ===== 在兴趣/评估阶段，偶尔插入SPIN提问 =====
        if sales_engine and msg_count % 5 == 0 and random.random() > 0.5:
            stage = sales_engine.get_funnel_stage(user_id)
            if stage in ["interest", "evaluation"]:
                spin_q, spin_phase = sales_engine.get_next_spin_question(user_id)
                reply += f"\n\n🤔 {spin_q}"

        # ===== 清理 Markdown =====
        reply = re.sub(r'(?<!\*)\*(?!\*)', '', reply)
        reply = re.sub(r'_{1,2}(?![\w])', '', reply)

        # ===== 发送回复 =====
        try:
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"AI response error: {e}")
        # 友好降级回复（SOUL 风格：不说"出错了"，而是人性化的说法）
        fallback_replies = [
            "Hmm, my brain just hiccuped there for a second 😅. Try again, or WhatsApp us if it's urgent!",
            "Okay, that was awkward — I glitched for a moment. Want to try that again? Or hit up WhatsApp!",
            "Whoops, technical moment. I'm still here though! Try once more, or catch us on WhatsApp 👇"
        ]
        await update.message.reply_text(
            random.choice(fallback_replies),
            reply_markup=get_contact_keyboard()
        )


# ============================================================
# 管理员命令
# ============================================================

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_CHAT_ID:
        return
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Usage: /reply <user_id> <message>")
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid ID. Usage: /reply <user_id> <message>")
        return

    reply_text = parts[2]

    try:
        target_name = "Customer"
        if memory_system:
            profile = memory_system.get_user_profile(target_user_id)
            target_name = profile.get("name", f"User {target_user_id}")

        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"💬 **Advisor:** {reply_text}\n\n_— BroadFSC Team_",
            parse_mode="Markdown",
            reply_markup=get_end_chat_keyboard() if target_user_id in LIVE_CHAT_USERS else None
        )
        await update.message.reply_text("✅ Sent!")
    except Exception as e:
        logger.error(f"Admin reply failed: {e}")
        await update.message.reply_text(f"❌ Failed: {e}")


async def admin_end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_CHAT_ID:
        return
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /endchat <user_id>")
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid ID. Usage: /endchat <user_id>")
        return

    LIVE_CHAT_USERS.discard(target_user_id)

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text="💬 Our advisor has ended this session. I'm still here if you need anything else! 👋",
            reply_markup=get_main_keyboard()
        )
    except Exception:
        pass

    await update.message.reply_text(f"✅ Ended chat with {target_user_id}")


async def admin_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_CHAT_ID:
        return
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /accept <user_id>")
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid ID. Usage: /accept <user_id>")
        return

    PENDING_CHATS.discard(target_user_id)
    LIVE_CHAT_USERS.add(target_user_id)

    try:
        target_name = "there"
        if memory_system:
            profile = memory_system.get_user_profile(target_user_id)
            target_name = profile.get("name", "there")

        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"Hey {target_name}! 👋 An advisor just joined — go ahead and type!\n\n"
                 f"Tap **End Chat** when done.",
            reply_markup=get_end_chat_keyboard()
        )
    except Exception as e:
        logger.error(f"Notify customer failed: {e}")

    await update.message.reply_text(
        "✅ Live chat started!\n\n"
        f"/reply {target_user_id} <msg> to send\n"
        f"/endchat {target_user_id} to end"
    )


async def admin_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_CHAT_ID:
        return
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    if not LIVE_CHAT_USERS and not PENDING_CHATS:
        await update.message.reply_text("📭 No active or pending chats.")
        return

    msg = ""
    if LIVE_CHAT_USERS:
        msg += "💬 **Active:**\n"
        for uid in LIVE_CHAT_USERS:
            info = USER_INFO_CACHE.get(uid, {})
            name = info.get("name", "Unknown")
            extra = ""
            if memory_system:
                p = memory_system.get_user_profile(uid)
                if p["conversation_count"] > 0:
                    extra = f" | chats:~{p['conversation_count']} | risk:{p['risk_tolerance']}"
            msg += f"  • {name} (ID:`{uid}`){extra}\n"
            msg += f"    /reply {uid} <msg> / /endchat {uid}\n"
        msg += "\n"

    if PENDING_CHATS:
        msg += "⏳ **Pending:**\n"
        for uid in PENDING_CHATS:
            info = USER_INFO_CACHE.get(uid, {})
            name = info.get("name", "Unknown")
            msg += f"  • {name} (ID:`{uid}`) — /accept {uid}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def admin_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看销售漏斗分析：/sales [user_id|stats|funnel]"""
    if not ADMIN_CHAT_ID:
        return
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    if not sales_engine:
        await update.message.reply_text("❌ Sales engine not initialized.")
        return

    parts = update.message.text.split(maxsplit=1)
    sub_cmd = parts[1].lower() if len(parts) > 1 else "stats"

    if sub_cmd == "stats":
        analytics = sales_engine.get_sales_analytics()
        stage_names = {"awareness": "🔍 认知", "interest": "💡 兴趣", "evaluation": "📊 评估", "decision": "🤔 决策", "action": "✅ 成交"}
        by_stage = analytics["by_stage"]
        stage_lines = []
        for stage, name in stage_names.items():
            count = by_stage.get(stage, 0)
            bar = "█" * count + "░" * max(10 - count, 0)
            stage_lines.append(f"  {name} │ {bar} {count}")

        msg = (
            f"💰 **Sales Funnel Analytics**\n\n"
            f"📋 Total prospects: {analytics['total_prospects']}\n"
            f"🎯 Conversion rate: {analytics['conversion_rate']:.0%}\n\n"
            f"**Funnel Breakdown:**\n"
            + "\n".join(stage_lines)
            + f"\n\n_Methodologies: SPIN / Challenger / Sandler / Gap / Value / Consultative_"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif sub_cmd == "funnel":
        if not sales_engine.funnel_data:
            await update.message.reply_text("📭 No users in funnel yet.")
            return
        lines = []
        for uid, data in sales_engine.funnel_data.items():
            stage = data.get("stage", "awareness")
            interactions = data.get("interactions", 0)
            spin = data.get("spin_phase", "situation")
            lines.append(f"  • `{uid}` → {stage} | {interactions} msgs | SPIN: {spin}")
        msg = "💰 **All Users in Funnel:**\n\n" + "\n".join(lines[:20])
        await update.message.reply_text(msg, parse_mode="Markdown")

    else:
        # 查看特定用户的销售漏斗
        try:
            target_uid = int(sub_cmd)
        except ValueError:
            await update.message.reply_text("Usage: /sales [user_id|stats|funnel]")
            return

        stage = sales_engine.get_funnel_stage(target_uid)
        spin = sales_engine.get_spin_phase(target_uid)
        uid_data = sales_engine.funnel_data.get(str(target_uid), {})
        interactions = uid_data.get("interactions", 0)
        stage_since = uid_data.get("stage_since", 0)

        stage_info = SalesIntelligenceEngine.FUNNEL_STAGES.get(stage, {})
        from datetime import timezone as tz
        since_str = datetime.fromtimestamp(stage_since, tz=tz).strftime('%Y-%m-%d %H:%M') if stage_since else "N/A"

        msg = (
            f"💰 **Sales Profile**\n\n"
            f"🆔 User: `{target_uid}`\n"
            f"📊 Funnel Stage: {stage.upper()} ({stage_info.get('name_zh', '?')})\n"
            f"🎯 Sales Method: {stage_info.get('sales_approach', '?').upper()}\n"
            f"📝 CTA Style: {stage_info.get('cta_style', '?')}\n"
            f"🔄 SPIN Phase: {spin.upper()}\n"
            f"💬 Interactions: {interactions}\n"
            f"🕐 In stage since: {since_str}\n\n"
            f"💡 _Next stage: {stage_info.get('next', 'N/A')}_"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")


async def admin_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看用户记忆档案：/memory <user_id>"""
    if not ADMIN_CHAT_ID:
        return
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return

    if not memory_system:
        await update.message.reply_text("❌ Memory system not initialized.")
        return

    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /memory <user_id>\n\nAlso try /memory stats for overview.")
        return

    if parts[1].lower() == "stats":
        total_users = len(memory_system.user_preferences)
        total_with_mem = sum(1 for p in memory_system.user_preferences.values() 
                            if p.get("investment_interests") or p.get("personal_details_mentioned"))
        avg_intimacy = (sum(memory_system.intimacy_scores.values()) / 
                       len(memory_system.intimacy_scores)) if memory_system.intimacy_scores else 0
        await update.message.reply_text(
            f"🧠 **Memory System Stats**\n\n"
            f"📊 Total users known: {total_users}\n"
            f"📝 Users with rich profiles: {total_with_mem}\n"
            f"❤️ Avg intimacy score: {avg_intimacy:.1f}/100\n"
            f"📚 IMA KB connected: {'✅ Yes' if memory_system.ima_available else '❌ No'}"
        )
        return

    try:
        target_uid = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return

    profile = memory_system.get_user_profile(target_uid)
    intimacy = memory_system.get_intimacy(target_uid)
    
    report = (
        f"🧠 **User Memory Profile**\n\n"
        f"🆔 ID: `{target_uid}`\n"
        f"👤 Name: {profile['name'] or 'Unknown'}\n"
        f"🌐 Language: {profile['language'].upper()}\n"
        f"❤️ Intimacy: {intimacy}/100\n"
        f"💬 Total chats: {profile['conversation_count']}\n"
        f"📅 First contact: {profile['first_contact'] or 'N/A'}\n"
        f"🕐 Last contact: {profile['last_contact'] or 'N/A'}\n\n"
        f"**Investment Interests:**\n{chr(10).join(['  • '+i for i in profile['investment_interests']]) or '  (none detected yet)'}\n\n"
        f"**Risk Tolerance:** {profile['risk_tolerance'].upper()}\n"
        f"**Experience Level:** {profile['experience_level'].upper()}\n\n"
        f"**Personal Details Mentioned:**\n{chr(10).join(['  • '+d for d in profile['personal_details_mentioned']]) or '  (none yet)'}\n\n"
        f"**Topics Discussed:**\n{chr(10).join(['  • '+t for t in profile['topics_discussed']]) or '  (none yet)'}"
    )

    await update.message.reply_text(report, parse_mode="Markdown")


# ============================================================
# 启动 Bot
# ============================================================

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN required")

    # 初始化记忆系统
    global memory_system
    memory_dir = os.path.join(os.path.dirname(__file__), ".bot_memory")
    memory_system = MemorySystem(memory_dir)
    
    # 初始化情绪系统
    annoyance_file = os.path.join(memory_dir, "annoyance_scores.json")
    EmotionalIntelligence.load_annoyance(annoyance_file)

    # 🆕 初始化销售智能引擎
    global sales_engine
    sales_engine = SalesIntelligenceEngine()

    # 代理配置（V2rayN / Clash 等本地代理）
    _proxy = os.environ.get("TELEGRAM_PROXY", "http://127.0.0.1:10808")
    # 验证代理是否可用（不强制，连不上也尝试直连）
    try:
        import urllib.request
        _test = urllib.request.ProxyHandler({"https": _proxy, "http": _proxy})
        _opener = urllib.request.build_opener(_test)
        _opener.open("https://api.telegram.org", timeout=3)
        logger.info(f"🌐 Proxy {_proxy} — OK")
    except Exception:
        logger.info(f"🌐 Proxy unavailable — trying direct connection")
        _proxy = None

    if _proxy:
        app = (
            Application.builder()
            .token(token)
            .proxy(_proxy)
            .get_updates_proxy(_proxy)
            .build()
        )
    else:
        app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    if ADMIN_CHAT_ID:
        app.add_handler(CommandHandler("reply", admin_reply))
        app.add_handler(CommandHandler("endchat", admin_end_chat))
        app.add_handler(CommandHandler("accept", admin_accept))
        app.add_handler(CommandHandler("chats", admin_chats))
        app.add_handler(CommandHandler("memory", admin_memory))
        app.add_handler(CommandHandler("sales", admin_sales))

    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 BroadFSC Telegram Bot v3 (SOUL + Sales Intelligence) started successfully!")
    logger.info(f"   🧠 Memory system: {memory_dir}")
    logger.info(f"   📚 IMA Knowledge Base: {'Connected ✅' if memory_system.ima_available else 'Not available ❌'}")
    logger.info(f"   🌍 Cultural profiles loaded: {len(CULTURAL_PROFILES)} languages")
    logger.info(f"   💰 Sales Engine: {'Active ✅' if sales_engine else 'Disabled ❌'} | Methodologies: SPIN/Challenger/Sandler/Gap/Value/Consultative")
    if ADMIN_CHAT_ID:
        logger.info(f"   👤 Admin: {ADMIN_CHAT_ID} — Live chat enabled")
    else:
        logger.info("   👤 No admin — WhatsApp-only mode")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
