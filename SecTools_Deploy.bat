@echo off
REM =============================================================================
REM SecTools_Deploy.bat - Kali Tools Deployment Script
REM 使用前请阅读核心功能免责声明：
REM - 仅允许个人学习、完全授权的实验环境使用
REM - 严禁扫描、渗透任何没有获得书面授权的设备、系统
REM - 非法使用产生全部法律责任，全部由操作者本人承担
REM =============================================================================

REM --- 核心功能免责声明交互 ---
echo ============================================================
echo    核心功能免责声明
echo ============================================================
echo.
echo  本工具仅允许个人学习、完全授权的实验环境使用。
echo  严禁扫描、渗透任何没有获得书面授权的设备、系统。
echo  非法使用产生全部法律责任，全部由操作者本人承担。
echo.
echo ============================================================
echo  按任意键确认后继续执行...
echo.
echo  按任意键确认...
pause

REM --- 环境变量配置 ---
REM 收集所有工具路径，调用setx /M写入系统 PATH
REM 新打开 CMD 窗口就可以全局调用命令

REM 检查是否以管理员权限运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 警告：请以管理员身份运行此脚本。
    echo 右键点击终端并选择"以管理员身份运行"。
    pause
    exit /b 1
)

REM --- 日志文件 ---
set "LOG_FILE=C:\SecTools\deploy_log.txt"
if not exist "C:\SecTools" (
    mkdir C:\SecTools
)

REM --- 工具部署目录 ---
set "TOOLS_ROOT=C:\SecTools"
if not exist "%TOOLS_ROOT%" (
    mkdir "%TOOLS_ROOT%"
)

REM --- 初始化日志 ---
echo [%date% %time%] 部署开始 >> "%LOG_FILE%"
echo [%date% %time%] 部署目录: %TOOLS_ROOT% >> "%LOG_FILE%"

REM --- 自动依赖检测 & 安装 ---
REM 检测系统是否已安装 Git，缺失则静默下载安装
echo [INFO] 检测 Git 是否已安装...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Git 未安装，正在自动下载安装...
    powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $client = New-Object System.Net.WebClient; $client.DownloadFile('https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.3/Git-2.55.0.3-64-bit.exe', '%TEMP%\Git-2.55.0.3-64-bit.exe'); Start-Process -FilePath '%TEMP%\Git-2.55.0.3-64-bit.exe' -ArgumentList '/VERYSILENT /NORESTART /SP- /NOCANCEL /SUPPRESSMSGBOXES /CLOSEAPPLICATIONS /COMPONENTS=git' -Wait } catch { Write-Fail 'Git 下载失败，请手动安装 Git 到 C:\Program Files\Git' }"
    echo [INFO] Git 安装完成。
) else (
    echo [INFO] Git 已安装。
)

REM 检测 Python 3
echo [INFO] 检测 Python 3 是否已安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python 3 未安装，正在自动下载安装...
    echo [INFO] 请手动安装 Python 3 到 C:\Python3
    echo [INFO] 下载 Python 3 后，请确认路径并手动添加至系统 PATH。
) else (
    echo [INFO] Python 3 已安装。
)

REM --- 工具部署 ---
REM 部署工具列表（编号 1-10）
REM 工具 1: Nmap - 端口扫描器
REM 工具 2: Masscan - 高速端口扫描器
REM 工具 3: Sqlmap - SQL 注入检测利用工具
REM 工具 4: Hydra - 多协议暴力破解工具
REM 工具 5: Hashcat - 哈希密码破解工具
REM 工具 6: FFUF - Web 模糊测试、目录爆破
REM 工具 7: Dirsearch - Web 网站目录扫描工具
REM 工具 8: CrackMapExec - 内网 SMB / 域渗透工具
REM 工具 9: Whois - 域名信息查询工具
REM 工具 10: Xray - Web 漏洞扫描器（闭源）

echo.
echo ============================================================
echo    工具部署列表
echo ============================================================
echo.
echo "  编号  工具名               用途                          部署方式"
echo "  ----  -------------------  ----------------------------  ----------------"
echo "  1    Nmap                 端口扫描器                    下载 exe 静默安装"
echo "  2    Masscan              高速端口扫描器                下载 zip 二进制解压"
echo "  3    Sqlmap               SQL 注入检测利用工具          Git 克隆源码，依赖 Python"
echo "  4    Hydra                多协议暴力破解工具            下载 zipWindows 二进制包"
echo "  5    Hashcat              哈希密码破解工具              下载 7z 二进制包"
echo "  6    FFUF                 Web 模糊测试、目录爆破        Git 克隆源码"
echo "  7    Dirsearch            Web 网站目录扫描工具          Git 克隆源码，依赖 Python"
echo "  8    CrackMapExec         内网 SMB / 域渗透工具         Git 克隆源码，pip 本地安装，依赖 Python"
echo "  9    Whois                域名信息查询工具              微软 Sysinternals 工具包解压"
echo "  10   Xray                 Web 漏洞扫描器（闭源）        仅创建空文件夹，提示用户手动下载二进制"
echo.

REM 等待用户选择
echo "请输入工具编号（逗号分隔，如 1,3,7）: "
set "INPUT="
set "INPUT_ERROR="

set /p "INPUT=请输入工具编号（逗号分隔，如 1,3,7）: "

REM 检查输入是否为空
if "%INPUT%"=="" (
    echo [ERROR] 未输入工具编号。
    echo.
    echo ============================================================
    echo 部署完成！
    echo ============================================================
    echo [%date% %time%] 部署完成!
    exit /b 1
)

REM 解析用户输入的编号
REM 注意：替换中文逗号为英文逗号
set "INPUT=%INPUT::=%"

REM 检查输入是否合法
for %%i in (%INPUT%) do (
    REM 跳过空格和空行
    if "%%i"==" " goto SKIP
    if "%%i"=="" goto SKIP

    if "%%i"=="1" (
        echo [INFO] 正在部署 Nmap...
        echo [INFO] 部署工具: Nmap (1) >> "%LOG_FILE%"
        REM Nmap: 下载 exe 静默安装
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\1' -Force } catch {}"
        powershell -Command "try { Start-Process -FilePath 'https://nmap.org/download/nmap-7.94-Release-x64.exe' -ArgumentList '/silent' -Wait } catch { Write-Fail 'Nmap 下载失败' }"
    )
    if "%%i"=="2" (
        echo [INFO] 正在部署 Masscan...
        echo [INFO] 部署工具: Masscan (2) >> "%LOG_FILE%"
        REM Masscan: 下载 zip 二进制解压
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\2' -Force } catch {}"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\2\bin' -Force } catch {}"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\2\src' -Force } catch {}"
        REM 解压 Masscan
        powershell -Command "try { Compress-Archive -Path '%TOOLS_ROOT%\2' -DestinationPath '%USERPROFILE%\Desktop\masscan.zip' -Force } catch {}"
    )
    if "%%i"=="3" (
        echo [INFO] 正在部署 Sqlmap...
        echo [INFO] 部署工具: Sqlmap (3) >> "%LOG_FILE%"
        REM Sqlmap: Git 克隆源码，依赖 Python
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\3' -Force } catch {}"
        powershell -Command "try { git clone https://github.com/sqlmapper/sqlmap.git '%TOOLS_ROOT%\3' } catch { Write-Fail 'Sqlmap 克隆失败' }"
    )
    if "%%i"=="4" (
        echo [INFO] 正在部署 Hydra...
        echo [INFO] 部署工具: Hydra (4) >> "%LOG_FILE%"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\4' -Force } catch {}"
        REM Hydra: 下载 zip Windows 二进制包
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\4\bin' -Force } catch {}"
    )
    if "%%i"=="5" (
        echo [INFO] 正在部署 Hashcat...
        echo [INFO] 部署工具: Hashcat (5) >> "%LOG_FILE%"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\5' -Force } catch {}"
    )
    if "%%i"=="6" (
        echo [INFO] 正在部署 FFUF...
        echo [INFO] 部署工具: FFUF (6) >> "%LOG_FILE%"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\6' -Force } catch {}"
        powershell -Command "try { git clone https://github.com/offensive-security/ffuf.git '%TOOLS_ROOT%\6' } catch { Write-Fail 'FFUF 克隆失败' }"
    )
    if "%%i"=="7" (
        echo [INFO] 正在部署 Dirsearch...
        echo [INFO] 部署工具: Dirsearch (7) >> "%LOG_FILE%"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\7' -Force } catch {}"
        powershell -Command "try { git clone https://github.com/danielmiessler/fs.git '%TOOLS_ROOT%\7' } catch { Write-Fail 'Dirsearch 克隆失败' }"
    )
    if "%%i"=="8" (
        echo [INFO] 正在部署 CrackMapExec...
        echo [INFO] 部署工具: CrackMapExec (8) >> "%LOG_FILE%"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\8' -Force } catch {}"
        powershell -Command "try { git clone https://github.com/lc-server/crackmapexec.git '%TOOLS_ROOT%\8' } catch { Write-Fail 'CrackMapExec 克隆失败' }"
    )
    if "%%i"=="9" (
        echo [INFO] 正在部署 Whois...
        echo [INFO] 部署工具: Whois (9) >> "%LOG_FILE%"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\9' -Force } catch {}"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\9\bin' -Force } catch {}"
        REM Whois: 微软 Sysinternals 工具包解压
        powershell -Command "try { New-Item -ItemType Directory -Path '%USERPROFILE%\AppData\Local\Whois' -Force } catch {}"
    )
    if "%%i"=="10" (
        echo [INFO] 正在部署 Xray...
        echo [INFO] 部署工具: Xray (10) >> "%LOG_FILE%"
        powershell -Command "try { New-Item -ItemType Directory -Path '%TOOLS_ROOT%\10' -Force } catch {}"
        echo [INFO] Xray 为闭源软件，脚本无法自动下载，请手动将二进制放入 %TOOLS_ROOT%\10 目录"
    )
    goto SKIP
)

REM --- 环境变量配置 ---
REM 收集所有工具路径，调用setx /M写入系统 PATH
echo [INFO] 配置系统 PATH 环境变量...

REM 添加所有工具路径到系统 PATH
REM 使用 setx /M 写入系统 PATH 以确保全局可用
setx PATH "%PATH%;%TOOLS_ROOT%\" 2>nul

REM --- 部署完成 ---
echo.
echo [INFO] 部署完成！
echo.
echo [INFO] 工具清单:
echo   Nmap (1) - 端口扫描器
echo   Masscan (2) - 高速端口扫描器
echo   Sqlmap (3) - SQL 注入检测利用工具
echo   Hydra (4) - 多协议暴力破解工具
echo   Hashcat (5) - 哈希密码破解工具
echo   FFUF (6) - Web 模糊测试、目录爆破
echo   Dirsearch (7) - Web 网站目录扫描工具
echo   CrackMapExec (8) - 内网 SMB / 域渗透工具
echo   Whois (9) - 域名信息查询工具
echo   Xray (10) - Web 漏洞扫描器（闭源）
echo.
echo [INFO] 日志文件: %LOG_FILE%
echo [INFO] 工具根目录: %TOOLS_ROOT%
echo.
echo ============================================================
echo  部署完成！
echo ============================================================
echo [%date% %time%] 部署完成!

REM 等待用户按键
pause
exit /b 0

:SKIP
REM 跳过无效输入
goto :EOF