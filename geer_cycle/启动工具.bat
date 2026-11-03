@echo off
chcp 65001 >nul
cd /d "%~dp0"
python "%~dp0gear_fatigue_tool.py"
echo.
echo 程序已退出，退出码：%errorlevel%
pause
