@echo off
setlocal
cd /d "%~dp0"
title TAKlite Smoke Test
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\SmokeTest-TAKliteWindows.ps1"
set "TAKLITE_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %TAKLITE_EXIT%
