@echo off
cd /d "%~dp0"
python rename_joints.py
if errorlevel 1 pause
