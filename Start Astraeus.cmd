@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
if errorlevel 1 (
  echo Astraeus could not start. Run Install Astraeus.cmd first, or inspect the error above.
  pause
)
