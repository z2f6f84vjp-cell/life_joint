@echo off
REM ============================================================
REM  Joint Arm Fatigue Life Calculator - Quick Launch
REM  Double-click to open the tool instantly.
REM  Runs via a tiny VBScript wrapper so no black console window
REM  flashes up (python.exe itself stays whitelisted by any
REM  endpoint security / DLP software already trusting it, unlike
REM  pythonw.exe which this machine's Esafenet DLP does not decrypt
REM  files for).
REM ============================================================
setlocal
set "TOOL_DIR=%~dp0"
wscript.exe "%TOOL_DIR%QuickOpen.vbs"
endlocal
