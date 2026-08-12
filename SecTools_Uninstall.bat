@echo off
REM =============================================================================
REM SecTools_Uninstall.bat - Kali Tools Uninstall Script
REM 卸载 Kali Tools 部署工具
REM =============================================================================

echo =============================================================================
echo    Kali Tools Uninstall Script
echo =============================================================================
echo.
echo  [INFO] 正在卸载 Kali Tools...
echo.

REM --- 检查是否以管理员权限运行 ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 警告：请以管理员身份运行此脚本。
    pause
    exit /b 1
)

REM --- 卸载工具 ---
REM 1. 移除工具目录
echo [INFO] 移除工具目录...
if exist "C:\SecTools" (
    rmdir /s /q "C:\SecTools"
    echo [INFO] 工具目录 C:\SecTools 已删除
) else (
    echo [INFO] 工具目录 C:\SecTools 不存在
)

REM 2. 移除工具清单
if exist "C:\Users\成成\Documents\GitHub\Kali-Tools-For-Windows\tools.txt" (
    del "C:\Users\成成\Documents\GitHub\Kali-Tools-For-Windows\tools.txt"
    echo [INFO] 工具清单已删除
)

REM 3. 移除快捷方式
if exist "%USERPROFILE%\Desktop\KaliTools" (
    rmdir /s /q "%USERPROFILE%\Desktop\KaliTools"
    echo [INFO] 桌面快捷方式已删除
) else (
    echo [INFO] 桌面快捷方式不存在
)

REM 4. 恢复系统 PATH
echo [INFO] 恢复系统 PATH 环境变量...
REM 调用系统 PATH 恢复命令
setx PATH "%PATH%" 2>nul
echo [INFO] PATH 环境变量已恢复

REM --- 确认 ---
echo.
echo ============================================================
echo  卸载完成！
echo ============================================================
echo.
echo [INFO] 卸载完成！
echo [INFO] 工具目录: C:\SecTools
echo [INFO] 工具清单: Kali-Tools-For-Windows\tools.txt
echo [INFO] 桌面快捷方式: %USERPROFILE%\Desktop\KaliTools
echo.

REM 等待用户按键
pause
exit /b 0