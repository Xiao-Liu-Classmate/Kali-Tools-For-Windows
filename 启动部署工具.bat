@echo off
chcp 936 >nul
title Kali Tools Deployer

echo.
echo  ========================================
echo   Kali Tools Deployer - 启动器
echo  ========================================
echo.

cd /d "%~dp0"

echo  正在启动 PowerShell 脚本...
echo.

powershell -ExecutionPolicy Bypass -NoExit -File "Kali-Tools-Deployer.ps1"

echo.
echo  脚本已退出，按任意键关闭...
pause >nul
