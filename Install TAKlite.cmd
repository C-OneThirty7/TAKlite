@echo off
setlocal
cd /d "%~dp0"

fltmc >nul 2>&1
if errorlevel 1 (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

title TAKlite Windows Docker Desktop Installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Install-TAKliteWindows.ps1"
set "TAKLITE_EXIT=%ERRORLEVEL%"
echo.
if not "%TAKLITE_EXIT%"=="0" (
  echo TAKlite installation paused or failed. Read the message above.
  echo It is safe to restart Windows, start Docker Desktop, and run Install TAKlite again.
) else (
  echo TAKlite installation completed successfully.
  echo.
  echo If you closed this window before saving the bootstrap token,
  echo double-click "Show Bootstrap Token.cmd" in this same folder.
)
echo.
pause
exit /b %TAKLITE_EXIT%
