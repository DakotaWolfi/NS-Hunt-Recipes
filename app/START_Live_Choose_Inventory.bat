@echo off
cd /d "%~dp0"
echo NS Hunt Workshop v0.8 - select avatar and EXISTING inventory file
py -3 live_server.py --mode live --log-dir auto --inventory ask --port 8765
if errorlevel 1 pause
