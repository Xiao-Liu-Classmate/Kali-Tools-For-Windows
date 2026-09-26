@echo off
chcp 936 >nul
REM =============================================================================
REM SecTools_Deploy.bat - Kali Tools Deployment Script
REM 仅允许个人学习、完全授权的实验环境使用
REM 严禁扫描、渗透任何没有获得书面授权的设备、系统
REM =============================================================================

REM --- 管理员权限检查 ---
fltmc >nul 2>&1
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
    echo [INFO] Git 未安装，正在下载安装...
    powershell -Command "$o='%TEMP%\Git-Install.exe';if(Test-Path $o){Remove-Item $o -Force -EA SilentlyContinue};try{$u='https://registry.npmmirror.com/-/binary/git-for-windows/v2.55.0.windows.3/Git-2.55.0.3-64-bit.exe';(New-Object Net.WebClient).DownloadFile($u,$o)}catch{$u2='https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.3/Git-2.55.0.3-64-bit.exe';(New-Object Net.WebClient).DownloadFile($u2,$o)};if(Test-Path $o){Start-Process $o '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES' -Wait}else{exit 1}"
    if exist "C:\Program Files\Git\cmd" set "PATH=%PATH%;C:\Program Files\Git\cmd"
    git --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Git 安装失败，源码类工具(3/7/18/19/20/21)将无法部署
        echo [ERROR] 请手动安装 Git: https://git-scm.com/download/win
    ) else (
        echo [INFO] Git 安装完成
    )
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
echo   2  Masscan       高速端口扫描器(源码需编译)
echo   3  Sqlmap        SQL注入检测利用工具
echo   4  Hydra         多协议暴力破解工具(源码需编译)
echo   5  Hashcat       哈希密码破解工具
echo   6  FFUF          Web模糊测试/目录爆破
echo   7  Dirsearch     Web网站目录扫描工具
echo   8  Gobuster      目录/文件/DNS暴力枚举
echo   9  Whois         域名信息查询工具
echo  10  Xray          Web漏洞扫描器(闭源,需手动下载)
echo  11  Wireshark     网络协议分析器
echo  12  Nuclei        模板化漏洞扫描器
echo  13  Subfinder     子域名发现工具
echo  14  Httpx         HTTP探测工具
echo  15  RustScan      Rust高速端口扫描器
echo  16  John          密码哈希破解工具(源码需编译)
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

REM 全角逗号替换为半角逗号
set "INPUT=%INPUT:，=,%"

REM 初始化日志
echo [%date% %time%] 部署开始 >> "%LOG_FILE%"

REM --- 处理输入 ---
if /i "%INPUT%"=="A" (
    call :deploy_all
    goto :done
)

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
REM Hashcat 专用子过程（独立于 IF 块，避免 % 变量延迟展开问题）
REM ============================================================
:deploy_hashcat
echo [INFO] 部署 Hashcat...
echo [%date% %time%] Hashcat >> "%LOG_FILE%"
if not exist "%TOOLS_ROOT%\hashcat" mkdir "%TOOLS_ROOT%\hashcat"
set "SEVENZ=C:\Program Files\7-Zip\7z.exe"
if not exist "%SEVENZ%" set "SEVENZ=C:\Program Files (x86)\7-Zip\7z.exe"
if not exist "%SEVENZ%" (
    echo [ERROR] Hashcat 为 7z 格式，请先安装 7-Zip 后重试
    goto :eof
)
powershell -Command "$o='%TEMP%\hashcat.7z';$u='https://hashcat.net/files/hashcat-6.2.6.7z';if(Test-Path $o){Remove-Item $o -Force};(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){exit 0}else{exit 1}" >nul
if errorlevel 1 (
    echo [ERROR] Hashcat 下载失败
    goto :eof
)
"%SEVENZ%" x "%TEMP%\hashcat.7z" -o"%TOOLS_ROOT%\hashcat" -y >nul
echo [INFO] Hashcat 完成
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
    powershell -Command "$o='%TEMP%\nmap-setup.exe';$u='https://nmap.org/dist/nmap-7.95-setup.exe';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Start-Process $o '/S' -Wait}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Nmap 下载或安装失败) else (echo [INFO] Nmap 完成)
    if exist "C:\Program Files (x86)\Nmap" set "PATH=%PATH%;C:\Program Files (x86)\Nmap"
    goto :eof
)

if "%NUM%"=="2" (
    echo [INFO] 部署 Masscan...
    echo [%date% %time%] Masscan >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\masscan" mkdir "%TOOLS_ROOT%\masscan"
    powershell -Command "$o='%TEMP%\masscan.zip';$u='https://github.com/robertdavidgraham/masscan/archive/refs/heads/master.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\masscan' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Masscan 下载失败) else (echo [HINT] Masscan 源码已下载，需 Visual Studio 编译后使用)
    echo [INFO] Masscan 完成
    goto :eof
)

if "%NUM%"=="3" (
    echo [INFO] 部署 Sqlmap...
    echo [%date% %time%] Sqlmap >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\sqlmap" mkdir "%TOOLS_ROOT%\sqlmap"
    if exist "%TOOLS_ROOT%\sqlmap\.git" (
        echo [INFO] Sqlmap 已存在，跳过
    ) else (
        git clone https://github.com/sqlmapproject/sqlmap.git "%TOOLS_ROOT%\sqlmap" >nul 2>&1
        if errorlevel 1 (echo [ERROR] Sqlmap 克隆失败，请检查 Git 网络) else (echo [INFO] Sqlmap 完成)
    )
    goto :eof
)

if "%NUM%"=="4" (
    echo [INFO] 部署 Hydra...
    echo [%date% %time%] Hydra >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\hydra" mkdir "%TOOLS_ROOT%\hydra"
    powershell -Command "$o='%TEMP%\hydra.zip';$u='https://github.com/vanhauser-thc/thc-hydra/archive/refs/heads/master.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\hydra' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Hydra 下载失败) else (echo [HINT] Hydra 源码已下载，官方无 Windows 二进制，需编译后使用)
    echo [INFO] Hydra 完成
    goto :eof
)

if "%NUM%"=="5" (
    call :deploy_hashcat
    goto :eof
)

if "%NUM%"=="6" (
    echo [INFO] 部署 FFUF...
    echo [%date% %time%] FFUF >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\ffuf" mkdir "%TOOLS_ROOT%\ffuf"
    powershell -Command "$o='%TEMP%\ffuf.zip';$u='https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_windows_amd64.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\ffuf' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] FFUF 下载失败) else (echo [INFO] FFUF 完成)
    goto :eof
)

if "%NUM%"=="7" (
    echo [INFO] 部署 Dirsearch...
    echo [%date% %time%] Dirsearch >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\dirsearch" mkdir "%TOOLS_ROOT%\dirsearch"
    if exist "%TOOLS_ROOT%\dirsearch\.git" (
        echo [INFO] Dirsearch 已存在，跳过
    ) else (
        git clone https://github.com/maurosoria/dirsearch.git "%TOOLS_ROOT%\dirsearch" >nul 2>&1
        if errorlevel 1 (echo [ERROR] Dirsearch 克隆失败，请检查 Git 网络) else (echo [INFO] Dirsearch 完成)
    )
    goto :eof
)

if "%NUM%"=="8" (
    echo [INFO] 部署 Gobuster...
    echo [%date% %time%] Gobuster >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\gobuster" mkdir "%TOOLS_ROOT%\gobuster"
    powershell -Command "$o='%TEMP%\gobuster.zip';$u='https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_Windows_x86_64.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\gobuster' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Gobuster 下载失败) else (echo [INFO] Gobuster 完成)
    goto :eof
)

if "%NUM%"=="9" (
    echo [INFO] 部署 Whois...
    echo [%date% %time%] Whois >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\whois" mkdir "%TOOLS_ROOT%\whois"
    powershell -Command "$o='%TEMP%\whois.zip';$u='https://download.sysinternals.com/files/WhoIs.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\whois' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Whois 下载失败) else (echo [INFO] Whois 完成)
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
    powershell -Command "$o='%TEMP%\wireshark-setup.exe';$u='https://2.na.dl.wireshark.org/win64/Wireshark-4.6.9-x64.exe';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Start-Process $o '/S' -Wait}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Wireshark 下载或安装失败) else (echo [INFO] Wireshark 完成)
    if exist "C:\Program Files\Wireshark" set "PATH=%PATH%;C:\Program Files\Wireshark"
    goto :eof
)

if "%NUM%"=="12" (
    echo [INFO] 部署 Nuclei...
    echo [%date% %time%] Nuclei >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\nuclei" mkdir "%TOOLS_ROOT%\nuclei"
    powershell -Command "$o='%TEMP%\nuclei.zip';$u='https://github.com/projectdiscovery/nuclei/releases/download/v3.3.8/nuclei_3.3.8_windows_amd64.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\nuclei' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Nuclei 下载失败) else (echo [INFO] Nuclei 完成)
    goto :eof
)

if "%NUM%"=="13" (
    echo [INFO] 部署 Subfinder...
    echo [%date% %time%] Subfinder >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\subfinder" mkdir "%TOOLS_ROOT%\subfinder"
    powershell -Command "$o='%TEMP%\subfinder.zip';$u='https://github.com/projectdiscovery/subfinder/releases/download/v2.6.7/subfinder_2.6.7_windows_amd64.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\subfinder' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Subfinder 下载失败) else (echo [INFO] Subfinder 完成)
    goto :eof
)

if "%NUM%"=="14" (
    echo [INFO] 部署 Httpx...
    echo [%date% %time%] Httpx >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\httpx" mkdir "%TOOLS_ROOT%\httpx"
    powershell -Command "$o='%TEMP%\httpx.zip';$u='https://github.com/projectdiscovery/httpx/releases/download/v1.6.10/httpx_1.6.10_windows_amd64.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\httpx' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Httpx 下载失败) else (echo [INFO] Httpx 完成)
    goto :eof
)

if "%NUM%"=="15" (
    echo [INFO] 部署 RustScan...
    echo [%date% %time%] RustScan >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\rustscan" mkdir "%TOOLS_ROOT%\rustscan"
    powershell -Command "$o='%TEMP%\rustscan.zip';$u='https://github.com/bee-san/RustScan/releases/download/2.4.1/x86_64-windows-rustscan.exe.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\rustscan' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] RustScan 下载失败) else (echo [INFO] RustScan 完成)
    goto :eof
)

if "%NUM%"=="16" (
    echo [INFO] 部署 John...
    echo [%date% %time%] John >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\john" mkdir "%TOOLS_ROOT%\john"
    powershell -Command "$o='%TEMP%\john.zip';$u='https://github.com/openwall/john/archive/refs/heads/bleeding-jumbo.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\john' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] John 源码下载失败) else (echo [HINT] John 源码已下载，需编译后使用)
    echo [INFO] John 完成
    goto :eof
)

if "%NUM%"=="17" (
    echo [INFO] 部署 Mimikatz...
    echo [%date% %time%] Mimikatz >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\mimikatz" mkdir "%TOOLS_ROOT%\mimikatz"
    powershell -Command "$o='%TEMP%\mimikatz.zip';$u='https://github.com/gentilkiwi/mimikatz/releases/download/2.2.0-20220919/mimikatz_trunk.zip';(New-Object Net.WebClient).DownloadFile($u,$o);if(Test-Path $o){Expand-Archive -Path $o -DestinationPath '%TOOLS_ROOT%\mimikatz' -Force}else{exit 1}" >nul
    if errorlevel 1 (echo [ERROR] Mimikatz 下载失败) else (echo [INFO] Mimikatz 完成)
    goto :eof
)

if "%NUM%"=="18" (
    echo [INFO] 部署 Responder...
    echo [%date% %time%] Responder >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\responder" mkdir "%TOOLS_ROOT%\responder"
    if exist "%TOOLS_ROOT%\responder\.git" (
        echo [INFO] Responder 已存在，跳过
    ) else (
        git clone https://github.com/lgandx/Responder.git "%TOOLS_ROOT%\responder" >nul 2>&1
        if errorlevel 1 (echo [ERROR] Responder 克隆失败，请检查 Git 网络) else (echo [INFO] Responder 完成)
    )
    goto :eof
)

if "%NUM%"=="19" (
    echo [INFO] 部署 Evil-WinRM...
    echo [%date% %time%] Evil-WinRM >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\evil-winrm" mkdir "%TOOLS_ROOT%\evil-winrm"
    if exist "%TOOLS_ROOT%\evil-winrm\.git" (
        echo [INFO] Evil-WinRM 已存在，跳过
    ) else (
        git clone https://github.com/Hackplayers/evil-winrm.git "%TOOLS_ROOT%\evil-winrm" >nul 2>&1
        if errorlevel 1 (echo [ERROR] Evil-WinRM 克隆失败，请检查 Git 网络) else (echo [INFO] Evil-WinRM 完成)
    )
    goto :eof
)

if "%NUM%"=="20" (
    echo [INFO] 部署 Impacket...
    echo [%date% %time%] Impacket >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\impacket" mkdir "%TOOLS_ROOT%\impacket"
    if exist "%TOOLS_ROOT%\impacket\.git" (
        echo [INFO] Impacket 已存在，跳过
    ) else (
        git clone https://github.com/fortra/impacket.git "%TOOLS_ROOT%\impacket" >nul 2>&1
        if errorlevel 1 (echo [ERROR] Impacket 克隆失败，请检查 Git 网络) else (echo [INFO] Impacket 完成)
    )
    goto :eof
)

if "%NUM%"=="21" (
    echo [INFO] 部署 CrackMapExec...
    echo [%date% %time%] CrackMapExec >> "%LOG_FILE%"
    if not exist "%TOOLS_ROOT%\crackmapexec" mkdir "%TOOLS_ROOT%\crackmapexec"
    if exist "%TOOLS_ROOT%\crackmapexec\.git" (
        echo [INFO] CrackMapExec 已存在，跳过
    ) else (
        git clone https://github.com/Porchetta-Industries/CrackMapExec.git "%TOOLS_ROOT%\crackmapexec" >nul 2>&1
        if errorlevel 1 (echo [ERROR] CrackMapExec 克隆失败，请检查 Git 网络) else (echo [HINT] CrackMapExec 需在源码目录执行 pip install 后使用)
    )
    echo [INFO] CrackMapExec 完成
    goto :eof
)

echo [ERROR] 无效编号: %NUM%
goto :eof

REM ============================================================
REM 配置系统 PATH
REM ============================================================
:done
echo [INFO] 正在配置系统 PATH...
powershell -NoProfile -Command "$all=@();Get-ChildItem -Path 'C:\SecTools' -Directory -ErrorAction SilentlyContinue | ForEach-Object {$all+=$_.FullName;foreach($s in @('bin','x64','run','hashcat','Bundled')){$sd=Join-Path $_.FullName $s;if(Test-Path $sd){$all+=$sd}}};$all=$all|Select-Object -Unique;$p=[Environment]::GetEnvironmentVariable('PATH','Machine');if($null -eq $p){$p=''};try{$parts=@($p.Split(';')|Where-Object{$_});$newDirs=@($all|Where-Object{$parts -notcontains $_});if($newDirs.Count -gt 0){$new=$parts+$newDirs;[Environment]::SetEnvironmentVariable('PATH',($new -join ';'),'Machine');Write-Host ('  [OK] 新增 '+$newDirs.Count+' 个目录到系统 PATH')}else{Write-Host '  [i] PATH 已包含全部工具目录，无需变更'}}catch{exit 1}"
if errorlevel 1 (echo [WARN] 系统 PATH 配置失败) else (echo [%date% %time%] PATH 配置完成 >> "%LOG_FILE%")

echo.
echo ============================================================
echo  部署完成!
echo ============================================================
echo.
echo [INFO] 工具目录: %TOOLS_ROOT%
echo [INFO] 日志文件: %LOG_FILE%
echo [INFO] 新开的 CMD/PowerShell 窗口即可全局调用工具
echo.
echo [%date% %time%] 部署完成 >> "%LOG_FILE%"
pause
exit /b 0
