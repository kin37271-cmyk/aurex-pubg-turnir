@echo off
chcp 65001 > nul
title AUREX PUBG MOBILE TURNIR BOT & WEB APP (24/7)
echo ===================================================
echo     AUREX PUBG MOBILE TOURNAMENT MANAGER BOT (24/7)
echo ===================================================

:loop
echo.
echo [%date% %time%] Bot, Web App server va Cloudflare HTTPS tunneli ishga tushirilmoqda...
py main.py
echo.
echo [%date% %time%] Bot to'xtadi yoki uzildi. 5 soniyadan so'ng avtomatik qayta ishga tushadi...
timeout /t 5 /nobreak > nul
goto loop
