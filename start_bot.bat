@echo off
chcp 65001 >nul
cd /d C:\kwork-projects\pricepulse
py -3.11 -m bot.main
pause