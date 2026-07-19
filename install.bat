@echo off
title Bio Wingman installer
echo ==================================================
echo   Bio Wingman  -  one-click installer (from Gitee)
echo ==================================================
echo.

if exist "setup\install.ps1" ( echo Detected app folder, installing dependencies... & goto deps )

where git >nul 2>nul
if errorlevel 1 goto zip

echo [1/2] Cloning Bio Wingman from Gitee (git) ...
git clone https://gitee.com/fsy2004/bio-wingman.git
if errorlevel 1 goto zip
goto entered

:zip
echo [1/2] Downloading Bio Wingman zip from Gitee ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try{ Invoke-WebRequest 'https://gitee.com/fsy2004/bio-wingman/repository/archive/master.zip' -OutFile 'bw.zip' -UseBasicParsing; Expand-Archive -Force 'bw.zip' 'bw_tmp'; $d=@(Get-ChildItem 'bw_tmp' -Directory)[0]; if(Test-Path 'bio-wingman'){Remove-Item 'bio-wingman' -Recurse -Force}; Move-Item $d.FullName 'bio-wingman'; Remove-Item 'bw.zip','bw_tmp' -Recurse -Force }catch{ Write-Host $_; exit 1 }"
if errorlevel 1 ( echo Download failed. Check your network, or download manually from https://gitee.com/fsy2004/bio-wingman & pause & exit /b 1 )

:entered
cd bio-wingman

:deps
echo.
echo [2/2] Installing R / Python dependencies (Tsinghua mirror by default) ...
powershell -NoProfile -ExecutionPolicy Bypass -File "setup\install.ps1"
echo.
echo ==================================================
echo   Done!  Double-click  start.bat  to launch Bio Wingman.
echo ==================================================
pause
