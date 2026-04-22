' BroadFSC Telegram 客服机器人 - 开机自启脚本
' 请确保系统环境变量已设置:
'   TELEGRAM_BOT_TOKEN
'   GROQ_API_KEY
'   ADMIN_CHAT_ID

Set objShell = CreateObject("WScript.Shell")

' 启动机器人（隐藏窗口）
objShell.Run "cmd /c cd /d c:\Users\Administrator\WorkBuddy\20260414140743\broadfsc-automation && python telegram_bot.py", 0, False
