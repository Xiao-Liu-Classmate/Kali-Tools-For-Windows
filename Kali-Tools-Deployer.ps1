# ============================================
# Kali Tools Deployer v1.1
# Kali Linux 工具 Windows 一键部署工具
# ============================================

# 编码设置
[Console]::OutputEncoding = [System.Text.Encoding]::Default
$OutputEncoding = [System.Text.Encoding]::Default
$ErrorActionPreference = "Continue"

# ============================================
# 全局配置
# ============================================
$Script:Config = @{
    ToolsDir      = "C:\SecTools"
    DownloadDir   = "C:\SecTools\Downloads"
    BinDir        = "C:\SecTools\bin"
    ShortcutsDir  = "$env:PUBLIC\Desktop\KaliTools"
    DownloadRetry = 2
    TimeoutSec    = 600
    MinFileSizeKB = 50
}

# ============================================
# 工具列表（21 个）
# ============================================
$Script:ToolList = @(
    @{ Cat="信息收集"; Name="Nmap";         Desc="端口扫描器";              Type="installer"; Url="https://nmap.org/dist/nmap-7.95-setup.exe";                        Args="/S";                                          BinPath="C:\Program Files (x86)\Nmap\nmap.exe";              Status="stable" },
    @{ Cat="信息收集"; Name="Masscan";      Desc="高速端口扫描器";          Type="portable";  Url="https://github.com/L7-GO/Masscan/releases/download/v1.0.0/Masscan-windows-64bit.zip";       Extract=$true; BinPath="";                                      Status="stable" },
    @{ Cat="信息收集"; Name="Whois";        Desc="域名信息查询工具";        Type="portable";  Url="https://downloads.sourceforge.net/project/whois/whois/whois-20190719-win32.zip";              Extract=$true; BinPath="";                                      Status="stable" },
    @{ Cat="信息收集"; Name="Subfinder";    Desc="子域名发现工具";          Type="portable";  Url="https://github.com/projectdiscovery/subfinder/releases/download/v2.6.7/subfinder_2.6.7_windows_amd64.zip"; Extract=$true; BinPath=""; Status="stable" },
    @{ Cat="信息收集"; Name="Httpx";        Desc="HTTP探测工具";            Type="portable";  Url="https://github.com/projectdiscovery/httpx/releases/download/v1.6.10/httpx_1.6.10_windows_amd64.zip"; Extract=$true; BinPath=""; Status="stable" },
    @{ Cat="漏洞扫描"; Name="Sqlmap";       Desc="SQL注入检测利用工具";    Type="portable";  Url="https://github.com/sqlmapproject/sqlmap/archive/refs/heads/master.zip";                       Extract=$true; BinPath=""; Note="需要 Python 环境";                       Status="stable" },
    @{ Cat="漏洞扫描"; Name="Nuclei";       Desc="模板化漏洞扫描器";        Type="portable";  Url="https://github.com/projectdiscovery/nuclei/releases/download/v3.3.7/nuclei_3.3.7_windows_amd64.zip"; Extract=$true; BinPath=""; Status="stable" },
    @{ Cat="漏洞扫描"; Name="Xray";         Desc="Web漏洞扫描器（闭源）";   Type="empty";     Url="";                                                                                           Note="请手动下载二进制放入 C:\SecTools\xray";                 Status="warning" },
    @{ Cat="密码攻击"; Name="Hashcat";      Desc="哈希密码破解工具";        Type="portable";  Url="https://hashcat.net/files/hashcat-6.2.6.7z";                                                 Extract=$true; BinPath=""; Note="需要 7-Zip 解压";                        Status="stable" },
    @{ Cat="密码攻击"; Name="Hydra";        Desc="多协议暴力破解工具";      Type="portable";  Url="https://github.com/vanhauser-thc/thc-hydra/releases/download/v9.6/hydra-9.6-windows.zip";    Extract=$true; BinPath="";                                      Status="stable" },
    @{ Cat="密码攻击"; Name="John";         Desc="密码哈希破解工具";        Type="portable";  Url="https://github.com/openwall/john/archive/refs/heads/bleeding-jumbo.zip";                       Extract=$true; BinPath=""; Note="需要编译或下载预编译包";                   Status="stable" },
    @{ Cat="密码攻击"; Name="Mimikatz";     Desc="Windows凭据提取工具";     Type="portable";  Url="https://github.com/gentilkiwi/mimikatz/releases/download/2.2.0-20240918/mimikatz_trunk.7z";  Extract=$true; BinPath=""; Note="需要 7-Zip 解压";                        Status="stable" },
    @{ Cat="Web测试"; Name="FFUF";         Desc="Web模糊测试/目录爆破";     Type="portable";  Url="https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_windows_amd64.zip";         Extract=$true; BinPath="";                                      Status="stable" },
    @{ Cat="Web测试"; Name="Gobuster";     Desc="目录/文件/DNS暴力枚举";   Type="portable";  Url="https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_3.6.0_windows_amd64.zip";  Extract=$true; BinPath="";                                      Status="stable" },
    @{ Cat="Web测试"; Name="Dirsearch";    Desc="Web网站目录扫描工具";      Type="portable";  Url="https://github.com/maurosoria/dirsearch/archive/refs/heads/master.zip";                       Extract=$true; BinPath=""; Note="需要 Python 环境";                       Status="stable" },
    @{ Cat="Web测试"; Name="RustScan";     Desc="Rust高速端口扫描器";       Type="portable";  Url="https://github.com/RustScan/RustScan/releases/download/2.3.0/rustscan-2.3.0-windows.zip";   Extract=$true; BinPath="";                                      Status="stable" },
    @{ Cat="网络分析"; Name="Wireshark";    Desc="网络协议分析器";           Type="installer"; Url="https://2.na.dl.wireshark.org/win64/WiresharkPortable64-4.4.8.paf.exe";                       Args="/S";                                          BinPath="C:\SecTools\WiresharkPortable\Wireshark.exe";     Status="stable" },
    @{ Cat="网络分析"; Name="Responder";    Desc="LLMNR/NBT-NS投毒工具";   Type="portable";  Url="https://github.com/lgandx/Responder/archive/refs/heads/master.zip";                           Extract=$true; BinPath=""; Note="需要 Python 环境";                       Status="stable" },
    @{ Cat="漏洞利用"; Name="Evil-WinRM";   Desc="Windows远程管理工具";      Type="portable";  Url="https://github.com/Hackplayers/evil-winrm/archive/refs/heads/master.zip";                     Extract=$true; BinPath=""; Note="需要 Python 环境";                       Status="stable" },
    @{ Cat="漏洞利用"; Name="Impacket";     Desc="网络协议工具集";           Type="portable";  Url="https://github.com/fortra/impacket/archive/refs/heads/master.zip";                            Extract=$true; BinPath=""; Note="需要 Python 环境 + pip install impacket", Status="stable" },
    @{ Cat="内网渗透"; Name="CrackMapExec"; Desc="内网SMB/域渗透工具";       Type="portable";  Url="https://github.com/Penntest-docker/CrackMapExec/archive/refs/heads/master.zip";               Extract=$true; BinPath=""; Note="需要 Python 环境",                        Status="stable" }
)

# ============================================
# 工具函数
# ============================================

function Write-Title($text) {
    Write-Host ""
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "  $("-" * $text.Length)" -ForegroundColor Gray
    Write-Host ""
}

function Write-Ok($text) {
    Write-Host "  [OK] " -NoNewline -ForegroundColor Green
    Write-Host $text -ForegroundColor White
}

function Write-Fail($text) {
    Write-Host "  [X] " -NoNewline -ForegroundColor Red
    Write-Host $text -ForegroundColor White
}

function Write-Info($text) {
    Write-Host "  [i] " -NoNewline -ForegroundColor Cyan
    Write-Host $text -ForegroundColor White
}

function Write-Warn($text) {
    Write-Host "  [!] " -NoNewline -ForegroundColor Yellow
    Write-Host $text -ForegroundColor White
}

function Write-Item($num, $text) {
    Write-Host "  [" -NoNewline -ForegroundColor Gray
    Write-Host $num -NoNewline -ForegroundColor Yellow
    Write-Host "] " -NoNewline -ForegroundColor Gray
    Write-Host $text -ForegroundColor White
}

function Test-AdminPrivilege {
    try {
        $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Ensure-Directory($path) {
    try {
        if (!(Test-Path -Path $path -PathType Container)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
        return $true
    } catch {
        Write-Fail "无法创建目录: $path - $($_.Exception.Message)"
        return $false
    }
}

function Test-7Zip {
    $paths = @(
        "C:\Program Files\7-Zip\7z.exe",
        "C:\Program Files (x86)\7-Zip\7z.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

# ============================================
# 核心功能：下载
# ============================================

function Start-Download($url, $outputPath) {
    $fileName = Split-Path $outputPath -Leaf
    $retry = 0
    $maxRetry = $Script:Config.DownloadRetry

    while ($retry -le $maxRetry) {
        if ($retry -gt 0) {
            Write-Info "重试第 $retry 次..."
        }

        try {
            Write-Info "下载中: $fileName"
            $ProgressPreference = 'SilentlyContinue'

            Invoke-WebRequest -Uri $url -OutFile $outputPath -UseBasicParsing -TimeoutSec $Script:Config.TimeoutSec

            # 验证文件
            if (!(Test-Path $outputPath)) {
                Write-Fail "下载失败：文件未生成"
                $retry++
                continue
            }

            $fileSize = (Get-Item $outputPath).Length
            $sizeMB = [math]::Round($fileSize / 1MB, 2)

            # 检查文件大小
            if ($fileSize -lt ($Script:Config.MinFileSizeKB * 1024)) {
                Write-Fail "下载失败：文件太小 ($fileSize 字节)，可能是错误页面"
                Remove-Item $outputPath -Force -ErrorAction SilentlyContinue
                $retry++
                continue
            }

            Write-Ok "下载完成 ($sizeMB MB)"
            return $true

        } catch {
            $errMsg = $_.Exception.Message
            if ($errMsg.Length -gt 80) { $errMsg = $errMsg.Substring(0, 80) + "..." }
            Write-Fail "下载失败: $errMsg"

            # 清理损坏文件
            if (Test-Path $outputPath) {
                Remove-Item $outputPath -Force -ErrorAction SilentlyContinue
            }

            $retry++
        }
    }

    Write-Fail "下载失败，已重试 $maxRetry 次"
    return $false
}

# ============================================
# 核心功能：解压
# ============================================

function Expand-ArchiveFile($archivePath, $destPath) {
    $fileName = Split-Path $archivePath -Leaf
    Write-Info "解压中: $fileName"

    try {
        # 7z 格式
        if ($archivePath -match '\.7z$') {
            $7zPath = Test-7Zip
            if ($7zPath) {
                & $7zPath x $archivePath -o"$destPath" -y | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Ok "解压完成"
                    return $true
                } else {
                    Write-Fail "7z 解压失败，退出码: $LASTEXITCODE"
                    return $false
                }
            } else {
                Write-Warn "检测到 7z 格式，但系统未安装 7-Zip"
                Write-Info "请手动解压到: $destPath"
                Write-Info "或安装 7-Zip 后重试"
                return $false
            }
        }

        # zip 格式
        if ($archivePath -match '\.zip$') {
            Expand-Archive -Path $archivePath -DestinationPath $destPath -Force -ErrorAction Stop
            Write-Ok "解压完成"
            return $true
        }

        Write-Warn "不支持的压缩格式: $fileName"
        return $false

    } catch {
        Write-Fail "解压失败: $($_.Exception.Message)"
        return $false
    }
}

# ============================================
# 核心功能：安装
# ============================================

function Start-Install($installerPath, $installArgs) {
    $fileName = Split-Path $installerPath -Leaf
    Write-Info "安装中: $fileName"

    try {
        # 验证文件
        if (!(Test-Path $installerPath)) {
            Write-Fail "安装文件不存在"
            return $false
        }

        $fileSize = (Get-Item $installerPath).Length
        if ($fileSize -lt 100KB) {
            Write-Fail "安装文件太小 ($fileSize 字节)，可能已损坏"
            return $false
        }

        # MSI 安装包
        if ($installerPath -match '\.msi$') {
            $msiArgs = "/i `"$installerPath`" $installArgs"
            $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
        }
        # EXE 安装包
        else {
            if ([string]::IsNullOrEmpty($installArgs)) {
                $process = Start-Process -FilePath $installerPath -Wait -PassThru -NoNewWindow
            } else {
                $process = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
            }
        }

        if ($process.ExitCode -eq 0) {
            Write-Ok "安装完成"
            return $true
        } else {
            Write-Warn "安装程序退出码: $($process.ExitCode)（可能已安装成功）"
            return $true
        }

    } catch {
        Write-Fail "安装失败: $($_.Exception.Message)"
        return $false
    }
}

# ============================================
# 核心功能：创建快捷方式
# ============================================

function New-AppShortcut($targetPath, $shortcutName) {
    try {
        if ([string]::IsNullOrEmpty($targetPath)) { return }
        if (!(Test-Path $targetPath)) { return }

        Ensure-Directory $Script:Config.ShortcutsDir

        $shortcutPath = Join-Path $Script:Config.ShortcutsDir "$shortcutName.lnk"
        $wshShell = New-Object -ComObject WScript.Shell
        $shortcut = $wshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $targetPath
        $shortcut.Save()

        Write-Ok "快捷方式: $shortcutName"
    } catch {
        # 静默失败，不影响主流程
    }
}

# ============================================
# 核心功能：安装单个工具
# ============================================

function Install-SingleTool($tool) {
    Write-Host ""
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host "  工具: $($tool.Name)" -ForegroundColor Cyan
    Write-Host "  描述: $($tool.Desc)" -ForegroundColor Gray
    if ($tool.Note) {
        Write-Host "  注意: $($tool.Note)" -ForegroundColor Yellow
    }
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host ""

    # 获取文件名
    try {
        $uri = [System.Uri]$tool.Url
        $fileName = [System.IO.Path]::GetFileName($uri.LocalPath)
    } catch {
        $fileName = "download"
    }

    if ([string]::IsNullOrEmpty($fileName)) { $fileName = "download" }

    $downloadPath = Join-Path $Script:Config.DownloadDir $fileName

    # 检查是否已下载
    $downloaded = $false
    if (Test-Path $downloadPath) {
        $size = (Get-Item $downloadPath).Length
        if ($size -gt ($Script:Config.MinFileSizeKB * 1024)) {
            Write-Info "已下载，跳过下载步骤"
            $downloaded = $true
        } else {
            Write-Warn "已下载的文件太小，重新下载"
            Remove-Item $downloadPath -Force -ErrorAction SilentlyContinue
        }
    }

    # 下载
    if (!$downloaded) {
        if (!(Start-Download $tool.Url $downloadPath)) {
            Write-Fail "$($tool.Name) 安装失败（下载失败）"
            return $false
        }
    }

    # 安装/解压
    $success = $false

    switch ($tool.Type) {
        "installer" {
            $success = Start-Install $downloadPath $tool.Args
        }
        "portable" {
            if ($tool.Extract) {
                $success = Expand-ArchiveFile $downloadPath $Script:Config.ToolsDir
            } else {
                Ensure-Directory $Script:Config.BinDir
                Copy-Item $downloadPath $Script:Config.BinDir -Force
                $success = $true
            }
        }
        default {
            Write-Warn "未知的工具类型: $($tool.Type)"
            $success = $true
        }
    }

    # 创建快捷方式
    if ($success -and $tool.BinPath) {
        if ($tool.BinPath -match '\.(exe|bat|py)$') {
            New-AppShortcut $tool.BinPath $tool.Name
        }
    }

    # 结果
    if ($success) {
        Write-Ok "$($tool.Name) 部署完成"
    } else {
        Write-Fail "$($tool.Name) 部署失败"
    }

    return $success
}

# ============================================
# 菜单：分类列表
# ============================================

function Show-CategoryMenu {
    Clear-Host
    Write-Host ""
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host "       原生 Windows 工具包" -ForegroundColor Cyan
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host ""

    $categories = $Script:ToolList | ForEach-Object { $_.Cat } | Sort-Object -Unique
    $index = 1

    foreach ($cat in $categories) {
        $count = ($Script:ToolList | Where-Object { $_.Cat -eq $cat }).Count
        Write-Item $index "$cat ($count 个工具)"
        $index++
    }

    Write-Host ""
    Write-Item "A" "安装全部工具"
    Write-Item "0" "返回主菜单"
    Write-Host ""
}

# ============================================
# 菜单：工具列表
# ============================================

function Show-ToolMenu($category) {
    Clear-Host
    Write-Host ""
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host "       $category" -ForegroundColor Cyan
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host ""

    $tools = $Script:ToolList | Where-Object { $_.Cat -eq $category }
    $index = 1

    foreach ($tool in $tools) {
        $statusColor = "White"
        $statusTag = ""
        if ($tool.Status -eq "warning") {
            $statusTag = " [可能下载慢]"
            $statusColor = "Yellow"
        }

        Write-Host "  [" -NoNewline -ForegroundColor Gray
        Write-Host $index -NoNewline -ForegroundColor Yellow
        Write-Host "] " -NoNewline -ForegroundColor Gray
        Write-Host "$($tool.Name)" -NoNewline -ForegroundColor White
        Write-Host $statusTag -ForegroundColor $statusColor
        Write-Host " - $($tool.Desc)" -ForegroundColor Gray

        $index++
    }

    Write-Host ""
    Write-Item "A" "安装本类全部"
    Write-Item "0" "返回分类列表"
    Write-Host ""
}

# ============================================
# 菜单：原生工具主逻辑
# ============================================

function NativeTools-Main {
    do {
        Show-CategoryMenu
        $choice = Read-Host "  请选择分类"

        $categories = $Script:ToolList | ForEach-Object { $_.Cat } | Sort-Object -Unique

        if ($choice -eq "0") { break }

        if ($choice -eq "A" -or $choice -eq "a") {
            Write-Title "安装全部工具"
            $total = $Script:ToolList.Count
            $okCount = 0

            foreach ($tool in $Script:ToolList) {
                if (Install-SingleTool $tool) { $okCount++ }
            }

            Write-Host ""
            Write-Ok "全部完成: $okCount / $total 个工具成功"
            Write-Host ""
            Read-Host "  按回车键返回"
            continue
        }

        if ($choice -match '^\d+$') {
            $num = [int]$choice
            if ($num -ge 1 -and $num -le $categories.Count) {
                $catName = $categories[$num - 1]

                do {
                    Show-ToolMenu $catName
                    $toolChoice = Read-Host "  请选择工具"

                    $tools = $Script:ToolList | Where-Object { $_.Cat -eq $catName }

                    if ($toolChoice -eq "0") { break }

                    if ($toolChoice -eq "A" -or $toolChoice -eq "a") {
                        Write-Title "安装 $catName 全部工具"
                        $okCount = 0
                        foreach ($t in $tools) {
                            if (Install-SingleTool $t) { $okCount++ }
                        }
                        Write-Host ""
                        Write-Ok "完成: $okCount / $($tools.Count) 个工具成功"
                        Write-Host ""
                        Read-Host "  按回车键返回"
                        continue
                    }

                    if ($toolChoice -match '^\d+$') {
                        $toolNum = [int]$toolChoice
                        if ($toolNum -ge 1 -and $toolNum -le $tools.Count) {
                            $tool = $tools[$toolNum - 1]
                            Install-SingleTool $tool
                            Write-Host ""
                            Read-Host "  按回车键继续"
                        }
                    }
                } while ($true)
            }
        }
    } while ($true)
}

# ============================================
# 菜单：WSL 模式
# ============================================

function WSL-Menu {
    do {
        Clear-Host
        Write-Host ""
        Write-Host "  =========================================" -ForegroundColor Cyan
        Write-Host "       WSL 完整 Kali Linux 环境" -ForegroundColor Cyan
        Write-Host "  =========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Info "推荐方案：兼容性最好，工具最全"
        Write-Host ""

        Write-Item "1" "检查 WSL 状态"
        Write-Item "2" "启用 WSL 功能（需要重启电脑）"
        Write-Item "3" "安装 Kali Linux"
        Write-Item "4" "安装常用工具集 (kali-linux-default)"
        Write-Item "5" "安装全部工具集 (kali-linux-everything)"
        Write-Item "6" "启动 Kali Linux 终端"
        Write-Item "7" "安装图形界面 (Win-KeX)"
        Write-Item "0" "返回主菜单"
        Write-Host ""

        $choice = Read-Host "  请选择操作"

        switch ($choice) {
            "1" {
                Clear-Host
                Write-Title "WSL 状态检查"
                try {
                    wsl --status
                } catch {
                    Write-Warn "WSL 可能未安装"
                }
                Write-Host ""
                try {
                    Write-Host "已安装的发行版:"
                    wsl --list --verbose
                } catch {
                    Write-Warn "无法获取发行版列表"
                }
                Write-Host ""
                Read-Host "  按回车键返回"
            }
            "2" {
                Clear-Host
                Write-Title "启用 WSL 功能"
                Write-Warn "操作完成后必须重启电脑才能生效"
                Write-Host ""
                $confirm = Read-Host "  确认继续? (Y/N)"

                if ($confirm -match '^[Yy]') {
                    Write-Info "启用 Windows 子系统..."
                    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

                    Write-Info "启用虚拟机平台..."
                    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

                    Write-Info "设置 WSL 2 为默认版本..."
                    wsl --set-default-version 2

                    Write-Host ""
                    Write-Ok "功能已启用，请重启电脑后继续"
                }
                Write-Host ""
                Read-Host "  按回车键返回"
            }
            "3" {
                Clear-Host
                Write-Title "安装 Kali Linux"
                Write-Host ""
                try {
                    wsl --install -d Kali-Linux
                    Write-Ok "Kali Linux 安装完成"
                } catch {
                    Write-Fail "自动安装失败: $($_.Exception.Message)"
                    Write-Info "请从 Microsoft Store 搜索 'Kali Linux' 手动安装"
                }
                Write-Host ""
                Read-Host "  按回车键返回"
            }
            "4" {
                Clear-Host
                Write-Title "安装常用工具集"
                Write-Info "约 2GB，包含大部分常用工具"
                Write-Host ""
                wsl -d Kali-Linux -- sudo apt update
                wsl -d Kali-Linux -- sudo apt install -y kali-linux-default
                Write-Host ""
                Write-Ok "安装完成"
                Write-Host ""
                Read-Host "  按回车键返回"
            }
            "5" {
                Clear-Host
                Write-Title "安装全部工具集"
                Write-Warn "约 10GB+，包含所有 Kali 工具"
                Write-Host ""
                $confirm = Read-Host "  确认继续? (Y/N)"
                if ($confirm -match '^[Yy]') {
                    wsl -d Kali-Linux -- sudo apt update
                    wsl -d Kali-Linux -- sudo apt install -y kali-linux-everything
                    Write-Host ""
                    Write-Ok "安装完成"
                }
                Write-Host ""
                Read-Host "  按回车键返回"
            }
            "6" {
                Write-Info "启动 Kali Linux..."
                wsl -d Kali-Linux
            }
            "7" {
                Clear-Host
                Write-Title "安装 Win-KeX 图形界面"
                Write-Host ""
                wsl -d Kali-Linux -- sudo apt update
                wsl -d Kali-Linux -- sudo apt install -y kali-win-kex
                Write-Host ""
                Write-Ok "Win-KeX 安装完成"
                Write-Info "使用方法:"
                Write-Host "    kex        - 窗口模式"
                Write-Host "    kex --sl   - 无缝模式"
                Write-Host "    kex --esm  - 增强会话模式"
                Write-Host ""
                Read-Host "  按回车键返回"
            }
            "0" { break }
        }
    } while ($true)
}

# ============================================
# 关于页面
# ============================================

function Show-About {
    Clear-Host
    Write-Host ""
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host "       关于 Kali Tools Deployer" -ForegroundColor Cyan
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  版本: v1.1" -ForegroundColor White
    Write-Host ""
    Write-Host "  功能: 将 Kali Linux 常用安全工具一键部署到 Windows"
    Write-Host ""
    Write-Host "  两种部署模式:"
    Write-Host "    1. 原生 Windows 工具包 - 各工具独立的 Windows 版本"
    Write-Host "    2. WSL 完整环境 - 通过 WSL 运行完整 Kali Linux"
    Write-Host ""
    Write-Warn "免责声明"
    Write-Host "  本工具仅供学习和授权的安全测试使用。"
    Write-Host "  请勿用于任何非法用途，使用者自行承担责任。"
    Write-Host ""
    Write-Info "工具目录: $($Script:Config.ToolsDir)"
    Write-Info "下载目录: $($Script:Config.DownloadDir)"
    Write-Info "快捷方式: $($Script:Config.ShortcutsDir)"
    Write-Host ""
    Write-Host "  提示: 国内网络建议使用 WSL 模式，更稳定" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  按回车键返回"
}

# ============================================
# 主菜单
# ============================================

function Main-Menu {
    do {
        Clear-Host
        Write-Host ""
        Write-Host "  =========================================" -ForegroundColor Cyan
        Write-Host "     Kali Tools Deployer v1.1" -ForegroundColor Cyan
        Write-Host "     Kali 工具 Windows 部署工具" -ForegroundColor Cyan
        Write-Host "  =========================================" -ForegroundColor Cyan
        Write-Host ""

        # 管理员权限提示
        if (!(Test-AdminPrivilege)) {
            Write-Warn "当前不是管理员权限，部分工具可能无法安装"
            Write-Info "建议右键选择 '以管理员身份运行'"
            Write-Host ""
        }

        Write-Item "1" "原生 Windows 工具包（独立安装）"
        Write-Item "2" "WSL 完整 Kali 环境（推荐）"
        Write-Item "3" "关于 / 使用说明"
        Write-Item "0" "退出"
        Write-Host ""
        Write-Host "  推荐使用 WSL 模式，兼容性更好，工具更全" -ForegroundColor Gray
        Write-Host ""

        $choice = Read-Host "  请选择模式"

        switch ($choice) {
            "1" { NativeTools-Main }
            "2" { WSL-Menu }
            "3" { Show-About }
            "0" {
                Clear-Host
                Write-Host ""
                Write-Ok "感谢使用 Kali Tools Deployer！"
                Write-Host ""
                break
            }
            default {
                Write-Warn "无效选项，请重新选择"
                Start-Sleep -Seconds 1
            }
        }
    } while ($true)
}

# ============================================
# 初始化
# ============================================

function Initialize-Environment {
    # 创建必要目录
    $dirs = @(
        $Script:Config.ToolsDir,
        $Script:Config.DownloadDir,
        $Script:Config.BinDir,
        $Script:Config.ShortcutsDir
    )

    foreach ($dir in $dirs) {
        Ensure-Directory $dir | Out-Null
    }
}

# ============================================
# 启动
# ============================================

Initialize-Environment
Main-Menu