@echo off
chcp 65001 >nul
title BroadFSC Telegram Bot

REM ============================================================
REM BroadFSC Telegram 客服机器人 - 本地启动脚本
REM 请确保系统环境变量已设置:
REM   TELEGRAM_BOT_TOKEN
REM   GROQ_API_KEY
REM   ADMIN_CHAT_ID
REM ============================================================

echo ============================================
echo   BroadFSC Telegram Bot 启动中...
echo ============================================
echo.
echo Bot Token: %TELEGRAM_BOT_TOKEN:~0,8%...
echo Groq Key:  %GROQ_API_KEY:~0,8%...
echo.

cd /d "%~dp0"
python telegram_bot.py

echo.
echo 机器人已停止运行。
pause
