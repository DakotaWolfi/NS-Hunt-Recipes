@echo off
cd /d "%~dp0"
title NS Hunt Tracker - Historical Restore
py -3 live_server.py --mode restore --log-dir auto --inventory auto --port 8766
if errorlevel 1 pause
