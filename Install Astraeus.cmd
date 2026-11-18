@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -ChooseProfile
if errorlevel 1 echo Setup failed. Read the error above and rerun this file to retry.
pause
