@echo off
cd /d "%~dp0"
set "LOG_DIR=%APPDATA%\Firestorm_x64\dakotawolf1994"
py -3 live_server.py --mode live --avatar "Jenna" --log-dir "%LOG_DIR%" --inventory ask --port 8765
if errorlevel 1 pause
