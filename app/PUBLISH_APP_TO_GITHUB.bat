@echo off
cd /d "%~dp0"
echo Publishes ONLY tracker source to DakotaWolfi/NS-Hunt-Recipes/app
py -3 publish_app.py
if errorlevel 1 pause
