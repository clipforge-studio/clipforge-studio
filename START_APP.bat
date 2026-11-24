@echo off
setlocal
cd /d "%~dp0"
if not exist "clipforge_studio.py" (
  echo clipforge_studio.py was not found. Extract the complete ZIP first.
  pause
  exit /b 1
)
if not exist "editor_engine.py" (
  echo editor_engine.py is missing. Extract all files from the ZIP into one folder.
  pause
  exit /b 1
)
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher was not found. Install Python 3 first.
  pause
  exit /b 1
)
py -3 clipforge_studio.py
if errorlevel 1 pause
