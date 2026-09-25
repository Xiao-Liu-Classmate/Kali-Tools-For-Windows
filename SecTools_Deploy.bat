@echo off
REM =============================================================================
REM SecTools_Deploy.bat - Kali Tools Deployment Script
REM 仅允许个人学习、完全授权的实验环境使用
REM 严禁扫描、渗透任何没有获得书面授权的设备、系统
REM =============================================================================

REM --- 管理员权限检查 ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 请以管理员身份运行此脚本。
    pause
    exit /b 1
)

REM --- 免责声明 ---
echo ============================================================
echo    Kali Tools Deployer - 安全工具一键部署
echo ============================================================
echo.
echo  本工具仅允许个人学习、完全授权的实验环境使用。
echo  严禁扫描、渗透任何没有获得书面授权的设备、系统。
echo  非法使用产生全部法律责任，全部由操作者本人承担。
echo.
echo ============================================================
pause

REM --- 环境变量 ---
set "TOOLS_ROOT=C:\SecTools"
set "LOG_FILE=%TOOLS_ROOT%\deploy_log.txt"
if not exist "%TOOLS_ROOT%" mkdir "%TOOLS_ROOT%"

REM --- 自动依赖检测 ---
echo [INFO] 检测 Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Git 未安装，正在下载...
    powershell -Command "$u='https://mirrors.tuna.tsinghua.edu.cn/github-release/git-for-windows/git/2.55.0.windows.3/Git-2.55.0.3-64-bit.exe';$o='%TEMP%\Git-Install.exe';(New-Object Net.WebClient).DownloadFile($u,$o);Start-Process $o '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES' -Wait" 2>nul
    echo [INFO] Git 安装完成
) else (
    echo [INFO] Git 已安装
)

REM --- 工具列表 ---
echo.
echo ============================================================
echo    工具部署列表
echo ============================================================
echo.
echo   1  Nmap          端口扫描器
echo   2  Masscan       高速端口扫描器
echo   3  Sqlmap        SQL注入检测利用工具
echo   4  Hydra         多协议暴力破解工具
echo   5  Hashcat       哈希密码破解工具
echo   6  FFUF          Web模糊测试/目录爆破
echo   7  Dirsearch     Web网站目录扫描工具
echo   8  Gobuster      目录/文件/DNS暴力枚举
echo   9  Whois         域名信息查询工具
echo  10  Xray          Web漏洞扫描器(闭源)
echo  11  Wireshark     网络协议分析器
echo  12  Nuclei        模板化漏洞扫描器
echo  13  Subfinder     子域名发现工具
echo  14  Httpx         HTTP探测工具
echo  15  RustScan      Rust高速端口扫描器
echo  16  John          密码哈希破解工具
echo  17  Mimikatz      Windows凭据提取工具
echo  18  Responder     LLMNR/NBT-NS投毒工具
echo  19  Evil-WinRM    Windows远程管理工具
echo  20  Impacket      网络协议工具集
echo  21  CrackMapExec  内网SMB/域渗透工具
echo.
echo   A  全部部署
echo.
echo ============================================================

REM --- 用户输入 ---
set "INPUT="
set /p "INPUT=请输入编号(逗号分隔，如 1,3,7 或 A 全部): "

if "%INPUT%"=="" (
    echo [ERROR] 未输入任何编号
    pause
    exit /b 1
)

REM 中文逗号替换为英文逗号
set "INPUT=%INPUT:，=%"

REM 初始化日志
echo [%date% %time%] 部署开始 >> "%LOG_FILE%"

REM --- 处理输入 ---
REM 支持 A/a 部署全部
if /i "%INPUT%"=="A" (
    call :deploy_all
    goto :done
)

REM 逐个处理编号
for %%i in (%INPUT%) do (
    call :deploy_one %%i
)

goto :done

REM ============================================================
REM 部署全部
REM ============================================================
:deploy_all
call :deploy_one 1
call :deploy_one 2
call :deploy_one 3
call :deploy_one 4
call :deploy_one 5
call :deploy_one 6
call :deploy_one 7
call :deploy_one 8
call :deploy_one 9
call :deploy_one 10
call :deploy_one 11
call :deploy_one 12
call :deploy_one 13
call :deploy_one 14
call :deploy_one 15
call :deploy_one 16
call :deploy_one 17
call :deploy_one 18
call :deploy_one 19
call :deploy_one 20
call :deploy_one 21
goto :eof

REM ============================================================
REM 部署单个工具
REM ============================================================
:deploy_one
set "NUM=%~1"
if "%NUM%"=="" goto :eof

if "%NUM%"=="1" (
    echo [INFO] 部署 Nmap...
    echo [%date% %time%] Nmap >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\nmap" mkdir "%TOOLS_ROOT%\nmap"
    powershell -Command "$u='https://nmap.org/dist/nmap-7.95-setup.exe';$o='%TEMP%\nmap-setup.exe';(New-Object Net.WebClient).DownloadFile($u,$o);Start-Process $o '/S' -Wait" 2>nul
    if exist "C:\Program Files (x86)\Nmap" (
        set "PATH=%PATH%;C:\Program Files (x86)\Nmap"
        echo [INFO] Nmap 已注册到 PATH
    )
    echo [INFO] Nmap 完成
    goto :eof
)

if "%NUM%"=="2" (
    echo [INFO] 部署 Masscan...
    echo [%date% %time%] Masscan >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\masscan" mkdir "%TOOLS_ROOT%\masscan"
    powershell -Command "$u='https://github.com/L7-GO/Masscan/releases/download/v1.0.0/Masscan-windows-64bit.zip';$o='%TEMP%\masscan.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\masscan' -Force" 2>nul
    echo [INFO] Masscan 完成
    goto :eof
)

if "%NUM%"=="3" (
    echo [INFO] 部署 Sqlmap...
    echo [%date% %time%] Sqlmap >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\sqlmap" mkdir "%TOOLS_ROOT%\sqlmap"
    powershell -Command "git clone https://github.com/sqlmapproject/sqlmap.git '%TOOLS_ROOT%\sqlmap'" 2>nul
    echo [INFO] Sqlmap 完成
    goto :eof
)

if "%NUM%"=="4" (
    echo [INFO] 部署 Hydra...
    echo [%date% %time%] Hydra >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\hydra" mkdir "%TOOLS_ROOT%\hydra"
    powershell -Command "$u='https://github.com/vanhauser-thc/thc-hydra/releases/download/v9.6/hydra-9.6-windows.zip';$o='%TEMP%\hydra.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\hydra' -Force" 2>nul
    echo [INFO] Hydra 完成
    goto :eof
)

if "%NUM%"=="5" (
    echo [INFO] 部署 Hashcat...
    echo [%date% %time%] Hashcat >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\hashcat" mkdir "%TOOLS_ROOT%\hashcat"
    powershell -Command "$u='https://hashcat.net/files/hashcat-6.2.6.7z';$o='%TEMP%\hashcat.7z';(New-Object Net.WebClient).DownloadFile($u,$o);& 'C:\Program Files\7-Zip\7z.exe' x $o -o'%TOOLS_ROOT%\hashcat' -y" 2>nul
    echo [INFO] Hashcat 完成
    goto :eof
)

if "%NUM%"=="6" (
    echo [INFO] 部署 FFUF...
    echo [%date% %time%] FFUF >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\ffuf" mkdir "%TOOLS_ROOT%\ffuf"
    powershell -Command "$u='https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_windows_amd64.zip';$o='%TEMP%\ffuf.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\ffuf' -Force" 2>nul
    echo [INFO] FFUF 完成
    goto :eof
)

if "%NUM%"=="7" (
    echo [INFO] 部署 Dirsearch...
    echo [%date% %time%] Dirsearch >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\dirsearch" mkdir "%TOOLS_ROOT%\dirsearch"
    powershell -Command "git clone https://github.com/maurosoria/dirsearch.git '%TOOLS_ROOT%\dirsearch'" 2>nul
    echo [INFO] Dirsearch 完成
    goto :eof
)

if "%NUM%"=="8" (
    echo [INFO] 部署 Gobuster...
    echo [%date% %time%] Gobuster >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\gobuster" mkdir "%TOOLS_ROOT%\gobuster"
    powershell -Command "$u='https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_3.6.0_windows_amd64.zip';$o='%TEMP%\gobuster.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\gobuster' -Force" 2>nul
    echo [INFO] Gobuster 完成
    goto :eof
)

if "%NUM%"=="9" (
    echo [INFO] 部署 Whois...
    echo [%date% %time%] Whois >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\whois" mkdir "%TOOLS_ROOT%\whois"
    powershell -Command "$u='https://downloads.sourceforge.net/project/whois/whois/whois-20190719-win32.zip';$o='%TEMP%\whois.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\whois' -Force" 2>nul
    echo [INFO] Whois 完成
    goto :eof
)

if "%NUM%"=="10" (
    echo [INFO] Xray 为闭源软件，请手动下载放入 %TOOLS_ROOT%\xray
    if not exist "%TOOLS_ROOT%\xray" mkdir "%TOOLS_ROOT%\xray"
    echo [%date% %time%] Xray - 手动下载 >> "%LOG_FILE%"
    echo [INFO] Xray 完成
    goto :eof
)

if "%NUM%"=="11" (
    echo [INFO] 部署 Wireshark...
    echo [%date% %time%] Wireshark >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\wireshark" mkdir "%TOOLS_ROOT%\wireshark"
    powershell -Command "$u='https://2.na.dl.wireshark.org/win64/WiresharkPortable64-4.4.8.paf.exe';$o='%TEMP%\wireshark.exe';(New-Object Net.WebClient).DownloadFile($u,$o);Start-Process $o '/S /D=%TOOLS_ROOT%\wireshark' -Wait" 2>nul
    echo [INFO] Wireshark 完成
    goto :eof
)

if "%NUM%"=="12" (
    echo [INFO] 部署 Nuclei...
    echo [%date% %time%] Nuclei >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\nuclei" mkdir "%TOOLS_ROOT%\nuclei"
    powershell -Command "$u='https://github.com/projectdiscovery/nuclei/releases/download/v3.3.7/nuclei_3.3.7_windows_amd64.zip';$o='%TEMP%\nuclei.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\nuclei' -Force" 2>nul
    echo [INFO] Nuclei 完成
    goto :eof
)

if "%NUM%"=="13" (
    echo [INFO] 部署 Subfinder...
    echo [%date% %time%] Subfinder >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\subfinder" mkdir "%TOOLS_ROOT%\subfinder"
    powershell -Command "$u='https://github.com/projectdiscovery/subfinder/releases/download/v2.6.7/subfinder_2.6.7_windows_amd64.zip';$o='%TEMP%\subfinder.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\subfinder' -Force" 2>nul
    echo [INFO] Subfinder 完成
    goto :eof
)

if "%NUM%"=="14" (
    echo [INFO] 部署 Httpx...
    echo [%date% %time%] Httpx >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\httpx" mkdir "%TOOLS_ROOT%\httpx"
    powershell -Command "$u='https://github.com/projectdiscovery/httpx/releases/download/v1.6.10/httpx_1.6.10_windows_amd64.zip';$o='%TEMP%\httpx.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\httpx' -Force" 2>nul
    echo [INFO] Httpx 完成
    goto :eof
)

if "%NUM%"=="15" (
    echo [INFO] 部署 RustScan...
    echo [%date% %time%] RustScan >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\rustscan" mkdir "%TOOLS_ROOT%\rustscan"
    powershell -Command "$u='https://github.com/RustScan/RustScan/releases/download/2.3.0/rustscan-2.3.0-windows.zip';$o='%TEMP%\rustscan.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\rustscan' -Force" 2>nul
    echo [INFO] RustScan 完成
    goto :eof
)

if "%NUM%"=="16" (
    echo [INFO] 部署 John the Ripper...
    echo [%date% %time%] John >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\john" mkdir "%TOOLS_ROOT%\john"
    echo [INFO] 需要从 https://github.com/openwall/john/archive/refs/heads/bleeding-jumbo.zip 下载源码
    echo [INFO] 或下载预编译包: https://github.com/openwall/john/releases
    powershell -Command "$u='https://github.com/openwall/john/archive/refs/heads/bleeding-jumbo.zip';$o='%TEMP%\john.zip';(New-Object Net.WebClient).DownloadFile($u,$o);Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\john' -Force" 2>nul
    echo [INFO] John 完成
    goto :eof
)

if "%NUM%"=="17" (
    echo [INFO] 部署 Mimikatz...
    echo [%date% %time%] Mimikatz >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\mimikatz" mkdir "%TOOLS_ROOT%\mimikatz"
    powershell -Command "$u='https://github.com/gentilkiwi/mimikatz/releases/download/2.2.0-20240918/mimikatz_trunk.7z';$o='%TEMP%\mimikatz.7z';(New-Object Net.WebClient).DownloadFile($u,$o);& 'C:\Program Files\7-Zip\7z.exe' x $o -o'%TOOLS_ROOT%\mimikatz' -y" 2>nul
    echo [INFO] Mimikatz 完成
    goto :eof
)

if "%NUM%"=="18" (
    echo [INFO] 部署 Responder...
    echo [%date% %time%] Responder >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\responder" mkdir "%TOOLS_ROOT%\responder"
    powershell -Command "git clone https://github.com/lgandx/Responder.git '%TOOLS_ROOT%\responder'" 2>nul
    echo [INFO] Responder 完成
    goto :eof
)

if "%NUM%"=="19" (
    echo [INFO] 部署 Evil-WinRM...
    echo [%date% %time%] Evil-WinRM >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\evil-winrm" mkdir "%TOOLS_ROOT%\evil-winrm"
    powershell -Command "git clone https://github.com/Hackplayers/evil-winrm.git '%TOOLS_ROOT%\evil-winrm'" 2>nul
    echo [INFO] Evil-WinRM 完成
    goto :eof
)

if "%NUM%"=="20" (
    echo [INFO] 部署 Impacket...
    echo [%date% %time%] Impacket >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\impacket" mkdir "%TOOLS_ROOT%\impacket"
    powershell -Command "git clone https://github.com/fortra/impacket.git '%TOOLS_ROOT%\impacket'" 2>nul
    echo [INFO] Impacket 完成
    goto :eof
)

if "%NUM%"=="21" (
    echo [INFO] 部署 CrackMapExec...
    echo [%date% %time%] CrackMapExec >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\crackmapexec" mkdir "%TOOLS_ROOT%\crackmapexec"
    powershell -Command "git clone https://github.com/Penntest-docker/CrackMapExec.git '%TOOLS_ROOT%\crackmapexec'" 2>nul
    echo [INFO] CrackMapExec 完成
    goto :eof
)

echo [ERROR] 无效编号: %NUM%
goto :eof

REM ============================================================
REM 完成
REM ============================================================
:done
echo.
echo ============================================================
echo  部署完成!
echo ============================================================
echo.
echo [INFO] 工具目录: %TOOLS_ROOT%
echo [INFO] 日志文件: %LOG_FILE%
echo.
echo [%date% %time%] 部署完成 >> "%LOG_FILE%"
pause
exit /b 0
