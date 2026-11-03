@echo off
cd /d "%~dp0"
python rename_header.py
if errorlevel 1 pause
