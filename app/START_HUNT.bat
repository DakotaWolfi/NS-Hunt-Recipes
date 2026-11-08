@echo off
cd /d "%~dp0"
title NS Hunt Tracker - Live
py -3 live_server.py --mode live --log-dir auto --inventory auto --port 8765
if errorlevel 1 pause
