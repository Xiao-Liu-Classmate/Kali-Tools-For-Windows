@echo off
REM =============================================================================
REM SecTools_Uninstall.bat - Kali Tools Uninstall Script
REM =============================================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 请以管理员身份运行此脚本。
    pause
    exit /b 1
)

echo ============================================================
echo    Kali Tools Uninstall Script
echo ============================================================
echo.
echo  此操作将删除以下内容:
echo    - C:\SecTools 目录及所有工具
echo    - 从系统 PATH 中移除工具路径
echo.
echo ============================================================
pause

REM --- 删除工具目录 ---
if exist "C:\SecTools" (
    echo [INFO] 删除 C:\SecTools ...
    rmdir /s /q "C:\SecTools"
    echo [INFO] 已删除
) else (
    echo [INFO] C:\SecTools 不存在，跳过
)

REM --- 从 PATH 中移除 ---
echo [INFO] 清理系统 PATH...
powershell -NoProfile -Command "$p=[Environment]::GetEnvironmentVariable('PATH','Machine');$parts=@($p.Split(';') | Where-Object { $_ -and $_ -notlike '*C:\SecTools*' });[Environment]::SetEnvironmentVariable('PATH',($parts -join ';'),'Machine')"
echo [INFO] PATH 已清理

echo.
echo ============================================================
echo  卸载完成!
echo ============================================================
pause
exit /b 0
