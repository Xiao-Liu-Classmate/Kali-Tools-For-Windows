@echo off
REM ============================================================
REM build_exe.bat - 用 PyInstaller 打包 KaliToolsGUI.py 为 exe
REM 需先安装: pip install pyinstaller py7zr -i https://pypi.tuna.tsinghua.edu.cn/simple
REM ============================================================
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3 并加入 PATH
    pause
    exit /b 1
)

python -c "import PyInstaller, sys; sys.exit(0 if PyInstaller.__version__=='6.22.2' else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 正在安装 PyInstaller...
    python -m pip install pyinstaller==6.22.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (echo [ERROR] PyInstaller install failed & pause & exit /b 1)
)

python -c "import py7zr" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 正在安装 py7zr...
    python -m pip install py7zr -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (echo [ERROR] py7zr install failed & pause & exit /b 1)
)

echo [INFO] 开始打包...
python -m PyInstaller --onefile --windowed --uac-admin --name KaliToolsGUI ^
    --distpath dist --workpath build --specpath build ^
    --noconfirm KaliToolsGUI.py

if exist "dist\KaliToolsGUI.exe" (
    echo.
    echo [OK] 打包完成: dist\KaliToolsGUI.exe
    for %%A in ("dist\KaliToolsGUI.exe") do echo [OK] 文件大小: %%~zA 字节
) else (
    echo [ERROR] 打包失败，请检查上方错误信息
)
pause
