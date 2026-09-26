@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM check_all.bat - 一键本地检查（测试 / 语法编译 / 下载源）
REM 用法：
REM   check_all.bat            全部检查（含联网的下载源检查）
REM   check_all.bat offline    仅本地检查（跳过下载源，适合离线/内网）
REM ============================================================

chcp 936 >nul
cd /d "%~dp0"
if errorlevel 1 (
    echo [ERROR] 无法进入脚本所在目录
    exit /b 1
)

set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY (
    where py >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
    where python3 >nul 2>&1 && set "PY=python3"
)
if not defined PY (
    echo [ERROR] 未找到 Python 解释器，请先安装 Python 3 并加入 PATH
    exit /b 1
)

set "FAILED=0"
set "STEPS=2"
if /i not "%~1"=="offline" set "STEPS=3"

echo [1/!STEPS!] 离线回归测试...
%PY% -m unittest test_kalitools test_check_urls
if errorlevel 1 (
    echo [FAIL] 回归测试未通过
    set "FAILED=1"
)

echo.
echo [2/!STEPS!] Python 语法编译检查...
for %%f in (KaliToolsGUI.py scripts\check_urls.py test_kalitools.py test_check_urls.py) do (
    %PY% -m py_compile "%%f"
    if errorlevel 1 (
        echo [FAIL] 编译失败: %%f
        set "FAILED=1"
    )
)

if /i "%~1"=="offline" goto :summary

echo.
echo [3/3] 下载源健康检查（需要网络，可能较慢）...
%PY% scripts\check_urls.py
if errorlevel 1 (
    echo [WARN] 下载源检查未通过，可能是网络问题或确有链接失效
    set "FAILED=1"
)

:summary
echo.
if "%FAILED%"=="1" (
    echo [WARN] 检查完成，但存在失败项
    set "RC=1"
) else (
    echo [OK] 全部检查通过
    set "RC=0"
)

if "%~1"=="" pause
exit /b %RC%
