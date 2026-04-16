@echo off
chcp 65001 >nul
title BroadFSC Telegram Bot

REM ============================================================
REM BroadFSC Telegram 客服机器人 - 本地启动脚本
REM 使用前请填入你的 GROQ_API_KEY
REM ============================================================

set TELEGRAM_BOT_TOKEN=8292422033:AAFir8sg7io6reQY5eYSmdiI8lftwyr3dFg
set GROQ_API_KEY=%USER_GROQ_API_KEY%

echo ============================================
echo   BroadFSC Telegram Bot 启动中...
echo ============================================
echo.
echo Bot Token: 已配置
echo Groq Key:  %GROQ_API_KEY:~0,8%...
echo.

cd /d "%~dp0"
python telegram_bot.py

echo.
echo 机器人已停止运行。
pause
