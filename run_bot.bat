@echo off
chcp 65001 > nul
title AUREX PUBG TURNIR BOT & WEB APP
echo ===================================================
echo     AUREX PUBG MOBILE TOURNAMENT MANAGER BOT
echo ===================================================
echo.
echo 1. Web App Cloudflare HTTPS tunneli ishga tushirilmoqda...
start "AUREX CLOUDFLARE TUNNEL" cmd /c "cloudflared.exe tunnel --url http://localhost:8080"
echo 2. Bot va Web App server ishga tushirilmoqda...
py main.py
pause
