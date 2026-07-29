@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_windows_fast.ps1"
if errorlevel 1 (
  echo.
  echo Launch failed. Check the error output above.
  pause
)
endlocal
