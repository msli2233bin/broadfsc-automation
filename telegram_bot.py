"""
BroadFSC Telegram 智能客服机器人
功能：自动回答投资咨询问题，引导用户访问官网注册
      WhatsApp 一键联系 + 客服消息转发（真人对话）

依赖安装：
    pip install python-telegram-bot groq

环境变量：
    TELEGRAM_BOT_TOKEN    - 从 @BotFather 获取
    GROQ_API_KEY          - 从 console.groq.com 获取（免费）
    ADMIN_CHAT_ID         - 管理员 Telegram chat_id（用于接收客户转接消息）
"""

import os
import re
import logging
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

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
WHATSAPP_NUMBER = "18032150144"  # 美国 WhatsApp 号码
WHATSAPP_LINK = f"https://wa.me/1{WHATSAPP_NUMBER}"
WEBSITE_URL = "https://www.broadfsc.com/different"

# 管理员 Chat ID（用于接收客户转接消息）
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

# 客服模式：正在和真人对话的用户集合
LIVE_CHAT_USERS = set()

# ============================================================
# AI 客户端
# ============================================================
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ============================================================
# 系统提示词（公司知识库）
# ============================================================
SYSTEM_PROMPT = """You are a professional investment advisor assistant for Broad Investment Securities (BroadFSC).

Company: Broad Investment Securities
Website: https://www.broadfsc.com/different
Business: Investment advisory and asset management services
Licenses: Multiple mainstream market regulatory licenses globally

Your persona:
- Name: Alex (BroadFSC Advisor)
- Professional, friendly, knowledgeable
- Speaks the user's language automatically (multilingual)

What you can help with:
1. Explain our investment advisory services
2. Answer general investment and finance questions
3. Guide users to register on the website
4. Provide market education (NOT specific investment advice)
5. Explain account types, fees (direct to website for specifics)

Rules you MUST follow:
- NEVER guarantee specific returns or profits
- ALWAYS include risk disclaimer when discussing investments
- NEVER provide specific stock picks or trading signals
- For account/fee specifics, direct users to website or human advisor
- Standard disclaimer: "Investment involves risk. Past performance is not indicative of future results."
- If asked about illegal activities, decline politely

Call-to-action:
- Guide interested users to: https://www.broadfsc.com/different
- For personal consultation, offer WhatsApp contact: https://wa.me/118032150144
- Offer to connect with a licensed human advisor for complex queries
- When user wants to talk to a real person, suggest WhatsApp or the "Talk to Advisor" button
"""

# ============================================================
# 多语言欢迎消息
# ============================================================
WELCOME_MESSAGES = {
    "en": """👋 Welcome to **Broad Investment Securities**!

I'm Alex, your AI investment assistant. I can help you with:

📊 Investment services information
💼 Portfolio & asset management queries
🌍 Global market insights  
📋 Account registration guidance

Feel free to ask anything in your language!

🔗 Visit us: https://www.broadfsc.com/different
💬 WhatsApp: Direct line to our advisors

⚠️ _Investment involves risk. Past performance is not indicative of future results._""",

    "zh": """👋 欢迎来到 **Broad Investment Securities**！

我是 Alex，您的 AI 投资顾问助手。我可以帮您了解：

📊 投资咨询服务详情
💼 资产管理方案
🌍 全球市场洞察
📋 开户注册指引

请用您习惯的语言提问！

🔗 官方网站：https://www.broadfsc.com/different
💬 WhatsApp：直接联系我们的顾问

⚠️ _投资有风险，过往业绩不代表未来收益。_""",

    "es": """👋 ¡Bienvenido a **Broad Investment Securities**!

Soy Alex, tu asistente de inversión con IA. Puedo ayudarte con:

📊 Información sobre servicios de inversión
💼 Consultas sobre gestión de activos
🌍 Perspectivas del mercado global
📋 Guía de registro de cuenta

🔗 Visítenos: https://www.broadfsc.com/different
💬 WhatsApp: Línea directa con nuestros asesores

⚠️ _La inversión conlleva riesgos. El rendimiento pasado no es indicativo de resultados futuros._""",

    "ar": """👋 مرحباً بك في **Broad Investment Securities**!

أنا أليكس، مساعدك الاستثماري الذكي. يمكنني مساعدتك في:

📊 معلومات عن خدمات الاستثمار
💼 استفسارات إدارة الأصول
🌍 رؤى السوق العالمية
📋 إرشادات التسجيل

🔗 زيارة الموقع: https://www.broadfsc.com/different
💬 واتساب: خط مباشر مع مستشارينا

⚠️ _الاستثمار ينطوي على مخاطر. الأداء السابق لا يشير إلى نتائج مستقبلية._"""
}

# ============================================================
# 快捷按钮
# ============================================================
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Our Services", callback_data="services"),
            InlineKeyboardButton("🌍 About Us", callback_data="about")
        ],
        [
            InlineKeyboardButton("📋 How to Register", callback_data="register"),
            InlineKeyboardButton("💬 Talk to Advisor", callback_data="advisor")
        ],
        [
            InlineKeyboardButton("📱 WhatsApp Us", url=WHATSAPP_LINK),
            InlineKeyboardButton("🔗 Visit Website", url=WEBSITE_URL)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_contact_keyboard():
    """联系方式专用键盘"""
    keyboard = [
        [
            InlineKeyboardButton("📱 WhatsApp — Chat Now", url=WHATSAPP_LINK),
        ],
        [
            InlineKeyboardButton("🔗 Visit Website", url=WEBSITE_URL),
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
# 命令处理器
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    # 根据用户语言选择欢迎消息（默认英文）
    lang = update.effective_user.language_code or "en"
    if lang.startswith("zh"):
        msg = WELCOME_MESSAGES["zh"]
    elif lang.startswith("es"):
        msg = WELCOME_MESSAGES["es"]
    elif lang.startswith("ar"):
        msg = WELCOME_MESSAGES["ar"]
    else:
        msg = WELCOME_MESSAGES["en"]

    # 移出客服模式
    user_id = update.effective_user.id
    LIVE_CHAT_USERS.discard(user_id)

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    await update.message.reply_text(
        "Just ask me anything about investment services, markets, or how to get started! "
        "I speak English, Chinese, Spanish, Arabic, Japanese, and more. 🌍\n\n"
        "📱 Need a real person? Chat us on WhatsApp anytime!\n"
        "🔗 Or visit: https://www.broadfsc.com/different",
        reply_markup=get_main_keyboard()
    )


# ============================================================
# 按钮回调处理
# ============================================================
QUICK_ANSWERS = {
    "services": (
        "📊 **Our Investment Services**\n\n"
        "• **Investment Advisory** — Personalized investment strategy and portfolio guidance\n"
        "• **Asset Management** — Professional management of your investment portfolio\n"
        "• **Wealth Planning** — Long-term financial planning and wealth preservation\n"
        "• **Market Research** — In-depth analysis of global markets and opportunities\n\n"
        "Our advisors are licensed across multiple major markets globally.\n\n"
        "🔗 For full details: https://www.broadfsc.com/different\n"
        "📱 Chat an advisor: WhatsApp\n\n"
        "⚠️ _Investment involves risk._"
    ),
    "about": (
        "🏛️ **About Broad Investment Securities**\n\n"
        "Broad Investment Securities (BroadFSC) is a licensed investment advisory "
        "and asset management firm operating in multiple international markets.\n\n"
        "✅ Multiple regulatory licenses (global markets)\n"
        "✅ Serving all types of investors worldwide\n"
        "✅ Professional, regulated, transparent\n\n"
        "🔗 Learn more: https://www.broadfsc.com/different\n"
        "📱 Reach us: WhatsApp"
    ),
    "register": (
        "📋 **How to Get Started**\n\n"
        "1️⃣ Visit https://www.broadfsc.com/different\n"
        "2️⃣ Click the registration/sign-up button\n"
        "3️⃣ Complete identity verification (KYC)\n"
        "4️⃣ Choose your service package\n"
        "5️⃣ Connect with your dedicated advisor\n\n"
        "Need help? Chat us on WhatsApp for step-by-step guidance!\n\n"
        "⚠️ _Investment involves risk. Please ensure you understand the risks involved._"
    ),
    "advisor": (
        "💬 **Connect with a Human Advisor**\n\n"
        "Our licensed advisors are ready to help you with:\n\n"
        "• Personalized investment strategy\n"
        "• Portfolio review & recommendations\n"
        "• Account setup assistance\n"
        "• Complex financial questions\n\n"
        "📱 **WhatsApp** — Fastest way to reach us\n"
        "Tap the button below to start a chat!\n\n"
        "⏰ We typically respond within minutes during business hours.\n\n"
        "⚠️ _Investment involves risk. Past performance is not indicative of future results._"
    ),
    "back_menu": "back_menu"  # 特殊标记，返回主菜单
}


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理内联按钮点击"""
    query = update.callback_query
    await query.answer()

    data = query.data
    answer = QUICK_ANSWERS.get(data)

    if answer is None:
        await query.message.reply_text(
            "Please visit our website for more information.",
            reply_markup=get_main_keyboard()
        )
        return

    if answer == "back_menu":
        # 返回主菜单
        lang = query.from_user.language_code or "en"
        if lang.startswith("zh"):
            msg = "👋 有什么可以帮您的？"
        elif lang.startswith("es"):
            msg = "👋 ¿En qué puedo ayudarte?"
        elif lang.startswith("ar"):
            msg = "👋 كيف يمكنني مساعدتك؟"
        else:
            msg = "👋 How can I help you?"

        await query.message.reply_text(
            msg,
            reply_markup=get_main_keyboard()
        )
        return

    # advisor 按钮显示联系方式键盘
    if data == "advisor":
        await query.message.reply_text(
            answer,
            parse_mode="Markdown",
            reply_markup=get_contact_keyboard()
        )
        return

    await query.message.reply_text(answer, parse_mode="Markdown")


# ============================================================
# 消息处理器（核心 AI 对话）
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息"""
    if update.message is None or update.message.text is None:
        return

    user_message = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "there"

    # 检查是否在客服模式（和真人对话中）
    if user_id in LIVE_CHAT_USERS and ADMIN_CHAT_ID:
        # 转发客户消息给管理员
        try:
            forward_text = (
                f"📩 **Customer Message**\n\n"
                f"👤 {user_name} (ID: {user_id})\n"
                f"💬 {user_message}\n\n"
                f"_Reply format: /reply {user_id} your message_"
            )
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=forward_text,
                parse_mode="Markdown"
            )
            await update.message.reply_text("✅ Message sent to our advisor. They'll reply shortly!")
        except Exception as e:
            logger.error(f"Failed to forward message to admin: {e}")
            # 转发失败，回退到 AI 模式
            LIVE_CHAT_USERS.discard(user_id)
        return

    # 检测用户是否想联系真人
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
            f"You can reach our team directly on WhatsApp — "
            f"we usually respond within minutes!\n\n"
            f"📱 Tap below to start a chat:"
        )
        await update.message.reply_text(
            contact_msg,
            reply_markup=get_contact_keyboard()
        )
        return

    # 显示"正在输入"状态
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        # 调用 Groq 免费 API
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content

        # 添加网站链接（每5条消息追加一次）
        msg_count = context.user_data.get("msg_count", 0) + 1
        context.user_data["msg_count"] = msg_count
        if msg_count % 5 == 0:
            reply += f"\n\n🔗 _Explore our services: {WEBSITE_URL}_\n📱 _WhatsApp: Direct line to advisors_"

        # 清理 Markdown 避免解析错误
        reply = re.sub(r'(?<!\*)\*(?!\*)', '', reply)
        reply = re.sub(r'_{1,2}(?![\w])', '', reply)
        try:
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"AI response error: {e}")
        await update.message.reply_text(
            "I'm having a momentary issue. You can reach us directly on WhatsApp for immediate help! 😊",
            reply_markup=get_contact_keyboard()
        )


# ============================================================
# 管理员命令（客服转接）
# ============================================================
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员回复客户：/reply <user_id> <message>"""
    if not ADMIN_CHAT_ID:
        return

    admin_id = str(update.effective_user.id)
    if admin_id != ADMIN_CHAT_ID:
        return  # 只有管理员能用

    text = update.message.text
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Usage: /reply <user_id> <message>")
        return

    target_user_id = int(parts[1])
    reply_text = parts[2]

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"💬 **Advisor Reply:**\n\n{reply_text}\n\n_— BroadFSC Advisor_",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Message sent to customer.")
    except Exception as e:
        logger.error(f"Failed to send admin reply: {e}")
        await update.message.reply_text(f"❌ Failed to send: {e}")


async def admin_end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员结束客服对话：/endchat <user_id>"""
    if not ADMIN_CHAT_ID:
        return

    admin_id = str(update.effective_user.id)
    if admin_id != ADMIN_CHAT_ID:
        return

    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /endchat <user_id>")
        return

    target_user_id = int(parts[1])
    LIVE_CHAT_USERS.discard(target_user_id)

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text="💬 Our advisor has ended this chat. Feel free to ask me anything, or reach out on WhatsApp anytime!",
            reply_markup=get_main_keyboard()
        )
    except Exception:
        pass

    await update.message.reply_text(f"✅ Chat with user {target_user_id} ended.")


async def admin_start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员主动开启客服对话：/livechat <user_id>"""
    if not ADMIN_CHAT_ID:
        return

    admin_id = str(update.effective_user.id)
    if admin_id != ADMIN_CHAT_ID:
        return

    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /livechat <user_id>")
        return

    target_user_id = int(parts[1])
    LIVE_CHAT_USERS.add(target_user_id)

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text="💬 You're now connected with a live advisor! Type your message and they'll reply directly.",
        )
    except Exception:
        pass

    await update.message.reply_text(f"✅ Live chat with user {target_user_id} started. Their messages will be forwarded to you.")


# ============================================================
# 启动 Bot
# ============================================================
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

    app = Application.builder().token(token).build()

    # 注册处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # 管理员命令（仅 ADMIN_CHAT_ID 用户可用）
    if ADMIN_CHAT_ID:
        app.add_handler(CommandHandler("reply", admin_reply))
        app.add_handler(CommandHandler("endchat", admin_end_chat))
        app.add_handler(CommandHandler("livechat", admin_start_chat))

    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 BroadFSC Telegram Bot started successfully!")
    if ADMIN_CHAT_ID:
        logger.info(f"📢 Admin chat ID: {ADMIN_CHAT_ID} — Live chat forwarding enabled")
    else:
        logger.info("📢 No ADMIN_CHAT_ID set — WhatsApp contact only mode")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
