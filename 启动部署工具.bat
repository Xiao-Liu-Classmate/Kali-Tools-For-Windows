@echo off
title Kali Tools Deployer
cd /d "%~dp0"

REM --- 管理员权限检查 ---
fltmc >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] 请以管理员身份运行本程序。
    echo.
    echo  右键点击本文件，选择 "以管理员身份运行"。
    echo.
    pause
    exit /b 1
)

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
