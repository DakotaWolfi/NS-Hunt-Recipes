@echo off
cd /d "%~dp0"
echo Close any running NS Hunt Tracker first.
py -3 update_tracker.py
if errorlevel 1 pause
