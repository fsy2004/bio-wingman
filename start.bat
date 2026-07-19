@echo off
cd /d "%~dp0"
where python >nul 2>nul || ( echo [ERROR] Python not found. Run install.bat first, or install Python 3.9+. & pause & exit /b 1 )
python -m biowingman
if errorlevel 1 pause
