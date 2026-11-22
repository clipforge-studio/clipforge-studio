@echo off
cd /d "%~dp0"
py -3 clipforge_studio.py
if errorlevel 1 pause
