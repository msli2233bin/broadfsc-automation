"""
BroadFSC Telegram 智能客服机器人
功能：自动回答投资咨询问题，引导用户访问官网注册
部署：Railway 免费版 / Render 免费版（永久在线运行）

依赖安装：
    pip install python-telegram-bot groq

环境变量：
    TELEGRAM_BOT_TOKEN    - 从 @BotFather 获取
    GROQ_API_KEY          - 从 console.groq.com 获取（免费）
"""

import os
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
- Offer to connect with a licensed human advisor for complex queries
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

⚠️ _Investment involves risk. Past performance is not indicative of future results._""",

    "zh": """👋 欢迎来到 **Broad Investment Securities**！

我是 Alex，您的 AI 投资顾问助手。我可以帮您了解：

📊 投资咨询服务详情
💼 资产管理方案
🌍 全球市场洞察
📋 开户注册指引

请用您习惯的语言提问！

🔗 官方网站：https://www.broadfsc.com/different

⚠️ _投资有风险，过往业绩不代表未来收益。_""",

    "es": """👋 ¡Bienvenido a **Broad Investment Securities**!

Soy Alex, tu asistente de inversión con IA. Puedo ayudarte con:

📊 Información sobre servicios de inversión
💼 Consultas sobre gestión de activos
🌍 Perspectivas del mercado global
📋 Guía de registro de cuenta

🔗 Visítenos: https://www.broadfsc.com/different

⚠️ _La inversión conlleva riesgos. El rendimiento pasado no es indicativo de resultados futuros._"""
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
            InlineKeyboardButton("🔗 Visit Website", url="https://www.broadfsc.com/different")
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
    else:
        msg = WELCOME_MESSAGES["en"]

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
        "Or visit: https://www.broadfsc.com/different",
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
        "🔗 For full details: https://www.broadfsc.com/different\n\n"
        "⚠️ _Investment involves risk._"
    ),
    "about": (
        "🏛️ **About Broad Investment Securities**\n\n"
        "Broad Investment Securities (BroadFSC) is a licensed investment advisory "
        "and asset management firm operating in multiple international markets.\n\n"
        "✅ Multiple regulatory licenses (global markets)\n"
        "✅ Serving all types of investors worldwide\n"
        "✅ Professional, regulated, transparent\n\n"
        "🔗 Learn more: https://www.broadfsc.com/different"
    ),
    "register": (
        "📋 **How to Get Started**\n\n"
        "1️⃣ Visit https://www.broadfsc.com/different\n"
        "2️⃣ Click the registration/sign-up button\n"
        "3️⃣ Complete identity verification (KYC)\n"
        "4️⃣ Choose your service package\n"
        "5️⃣ Connect with your dedicated advisor\n\n"
        "Need help? Just ask me or request a human advisor below!\n\n"
        "⚠️ _Investment involves risk. Please ensure you understand the risks involved._"
    ),
    "advisor": (
        "💬 **Connect with a Human Advisor**\n\n"
        "For complex investment queries or personalized advice, "
        "our licensed advisors are available.\n\n"
        "📧 Please visit our website to submit a consultation request:\n"
        "🔗 https://www.broadfsc.com/different\n\n"
        "Our team will respond within 1 business day."
    )
}


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理内联按钮点击"""
    query = update.callback_query
    await query.answer()

    answer = QUICK_ANSWERS.get(query.data, "Please visit our website for more information.")
    await query.message.reply_text(answer, parse_mode="Markdown")


# ============================================================
# 消息处理器（核心 AI 对话）
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息，调用 Groq AI 生成回复"""
    if update.message is None or update.message.text is None:
        return
    user_message = update.message.text
    user_name = update.effective_user.first_name or "there"

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
            reply += "\n\n🔗 _Explore our services: https://www.broadfsc.com/different_"

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"AI response error: {e}")
        await update.message.reply_text(
            "I'm having a momentary issue. Please visit https://www.broadfsc.com/different "
            "for immediate assistance, or try again in a moment! 😊"
        )


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
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 BroadFSC Telegram Bot started successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
