@echo off
cd /d "%~dp0"
echo Historical restore; no inventory file will be loaded.
py -3 live_server.py --mode restore --log-dir auto --inventory none --port 8766
if errorlevel 1 pause
