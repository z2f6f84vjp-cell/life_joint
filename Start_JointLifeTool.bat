@echo off
REM ============================================================
REM  Joint Arm Fatigue Life Calculator - Desktop Launcher
REM  Local Tkinter desktop app. No browser, no network port.
REM  1. Locate script directory, switch working dir
REM  2. Check Python and required modules (numpy/matplotlib/tkinter)
REM  3. Clean up a stale single-instance lock left by a previous
REM     abnormal exit (handled inside the python script itself)
REM  4. Launch the app; auto-retry on crash (max 3 times)
REM  5. Log every run so failures are always diagnosable
REM ============================================================

setlocal EnableDelayedExpansion
chcp 936 >nul

set "TOOL_DIR=%~dp0"
set "TOOL_DIR=%TOOL_DIR:~0,-1%"
set "SCRIPT_NAME=joint_life_desktop.py"
set "LOG_DIR=%TOOL_DIR%\logs"
set "MAX_RETRY=3"

cd /d "%TOOL_DIR%"
if errorlevel 1 (
    echo [ERROR] Cannot switch to script directory: %TOOL_DIR%
    pause
    exit /b 1
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================================
echo   Joint Arm Fatigue Life Calculator - Desktop Edition
echo   Working dir: %TOOL_DIR%
echo ============================================================

REM ---------- 1. Check Python ----------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

if not exist "%TOOL_DIR%\%SCRIPT_NAME%" (
    echo [ERROR] Script not found: %TOOL_DIR%\%SCRIPT_NAME%
    pause
    exit /b 1
)

REM ---------- 2. Check required Python modules ----------
echo [CHECK] Verifying required Python modules ^(numpy / matplotlib / tkinter^)...
python -c "import numpy, matplotlib, tkinter" >nul 2>"%LOG_DIR%\deps_check.log"
if errorlevel 1 (
    echo [ERROR] Missing required Python module. Attempting to install numpy/matplotlib...
    python -m pip install --quiet numpy matplotlib
    python -c "import numpy, matplotlib, tkinter" >nul 2>"%LOG_DIR%\deps_check.log"
    if errorlevel 1 (
        echo [ERROR] Auto-install failed. See %LOG_DIR%\deps_check.log
        type "%LOG_DIR%\deps_check.log"
        pause
        exit /b 1
    )
)
echo [OK] Dependencies satisfied.

REM ---------- 3. Launch with auto-retry ----------
set "RETRY_COUNT=0"

:RETRY_LAUNCH
set /a RETRY_COUNT+=1
set "TS=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TS=%TS: =0%"
set "LOG_FILE=%LOG_DIR%\run_%TS%.log"

echo.
echo [START] Attempt !RETRY_COUNT!/%MAX_RETRY%, log: %LOG_FILE%
echo [START] Launching desktop app, please wait...

python "%TOOL_DIR%\%SCRIPT_NAME%" > "%LOG_FILE%" 2>&1
set "EXITCODE=!ERRORLEVEL!"

if "!EXITCODE!"=="0" (
    echo [OK] App closed normally.
    goto :END
) else (
    echo [FAIL] App exited with code !EXITCODE!. See log: %LOG_FILE%
    findstr /I "Traceback Error" "%LOG_FILE%" >nul 2>nul
    if not errorlevel 1 (
        echo [DIAG] Exception found in log, details:
        findstr /I "Traceback Error" "%LOG_FILE%"
    )
    if !RETRY_COUNT! LSS %MAX_RETRY% (
        if exist "%TOOL_DIR%\.instance.lock" del /f /q "%TOOL_DIR%\.instance.lock" >nul 2>nul
        echo [RETRY] Retrying in 2 seconds...
        timeout /t 2 /nobreak >nul
        goto :RETRY_LAUNCH
    ) else (
        echo [FAIL] Max retries %MAX_RETRY% reached. Please check the log above.
        pause
        exit /b 1
    )
)

:END
endlocal
