@echo off
setlocal
cd /d "%~dp0"
title TAKlite Bootstrap Token
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Show-TAKliteToken.ps1"
set "TAKLITE_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %TAKLITE_EXIT%
