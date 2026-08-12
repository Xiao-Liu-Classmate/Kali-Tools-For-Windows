@echo off
title Kali Tools Deployer

cd /d "%~dp0"

echo.
echo  ========================================
echo   Kali Tools Deployer
echo  ========================================
echo.

powershell -ExecutionPolicy Bypass -NoExit -File "Kali-Tools-Deployer.ps1"

echo.
echo  Please wait...
pause >nul