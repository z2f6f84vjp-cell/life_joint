@echo off
REM ============================================================
REM  7_tool 综合工具集 - 统一启动入口
REM  可见控制台窗口, 便于崩溃时直接看到报错信息(不使用静默VBS方式)
REM ============================================================
setlocal EnableDelayedExpansion
chcp 936 >nul

set "TOOL_DIR=%~dp0"
set "TOOL_DIR=%TOOL_DIR:~0,-1%"
set "SCRIPT_NAME=comprehensive_hub.py"

cd /d "%TOOL_DIR%"
if errorlevel 1 (
    echo [ERROR] Cannot switch to script directory: %TOOL_DIR%
    pause
    exit /b 1
)

echo ============================================================
echo   7_tool Comprehensive Hub
echo   Working dir: %TOOL_DIR%
echo ============================================================

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3 and add it to PATH.
    pause
    exit /b 1
)

if not exist "%TOOL_DIR%\%SCRIPT_NAME%" (
    echo [ERROR] Script not found: %TOOL_DIR%\%SCRIPT_NAME%
    pause
    exit /b 1
)

echo [START] Launching hub, please wait...
python "%TOOL_DIR%\%SCRIPT_NAME%"
echo.
echo [EXIT] Hub closed with exit code %errorlevel%.
pause
endlocal
