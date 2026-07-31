@echo off
setlocal
cd /d "%~dp0"

fltmc >nul 2>&1
if errorlevel 1 (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

title TAKlite Windows Docker Desktop Reinstall
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Reinstall-TAKliteWindows.ps1"
set "TAKLITE_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %TAKLITE_EXIT%
