@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   ClipForge Studio - Dependency Setup
echo ==========================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher was not found. Install Python 3 from python.org first.
  pause
  exit /b 1
)
echo Installing or updating yt-dlp for this Python installation...
py -3 -m pip install --upgrade yt-dlp
if errorlevel 1 (
  echo.
  echo Could not install yt-dlp. Check your internet connection and Python installation.
  pause
  exit /b 1
)
echo.
echo Checking FFmpeg...
where ffmpeg
if errorlevel 1 (
  echo FFmpeg was not found on PATH.
  echo Put ffmpeg.exe and ffprobe.exe beside this app, or add their folder to PATH.
) else (
  where ffprobe
)
echo.
echo Setup finished. Keep editor_engine.py beside clipforge_studio.py.
echo Double-click START_APP.bat to open ClipForge Studio.
pause
