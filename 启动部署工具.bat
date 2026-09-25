@echo off
title Kali Tools Deployer
cd /d "%~dp0"

echo.
echo ========================================
echo  Kali Tools Deployer - 启动中...
echo ========================================
echo.

if exist "dist\KaliToolsGUI.exe" (
    echo [INFO] 启动图形化界面...
    start "" "dist\KaliToolsGUI.exe"
) else (
    echo [INFO] 图形化界面不存在，启动命令行部署...
    powershell -ExecutionPolicy Bypass -NoExit -File "Kali-Tools-Deployer.ps1"
)
