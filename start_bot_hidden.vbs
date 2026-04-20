Set objShell = CreateObject("WScript.Shell")
objShell.Environment("User").Item("TELEGRAM_BOT_TOKEN") = "8292422033:AAHrPUfSaUAcmpvQXcV4nsd-NakZH3SIwPU"
objShell.Environment("User").Item("GROQ_API_KEY") = objShell.Environment("User").Item("USER_GROQ_API_KEY")
objShell.Environment("User").Item("ADMIN_CHAT_ID") = "8639358750"

' 启动机器人（隐藏窗口）
objShell.Run "cmd /c cd /d c:\Users\Administrator\WorkBuddy\20260414140743\broadfsc-automation && python telegram_bot.py", 0, False
