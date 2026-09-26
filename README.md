# Kali-Tools-For-Windows

[![CI](https://github.com/Xiao-Liu-Classmate/Kali-Tools-For-Windows/actions/workflows/ci.yml/badge.svg)](https://github.com/Xiao-Liu-Classmate/Kali-Tools-For-Windows/actions/workflows/ci.yml)
[![URL health](https://github.com/Xiao-Liu-Classmate/Kali-Tools-For-Windows/actions/workflows/url-health.yml/badge.svg)](https://github.com/Xiao-Liu-Classmate/Kali-Tools-For-Windows/actions/workflows/url-health.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Xiao-Liu-Classmate/Kali-Tools-For-Windows)](../../releases/latest)

将 Kali Linux 常用安全工具一键部署到 Windows 系统。

## 简介

本工具支持通过图形化界面（GUI）、命令行（BAT）、PowerShell 脚本三种方式部署 21 个常用安全工具到 Windows。

## 工具列表（共 21 个）

| 编号 | 工具名 | 用途 | 部署方式 |
|------|--------|------|----------|
| 1 | Nmap | 端口扫描器 | exe 静默安装 |
| 2 | Masscan | 高速端口扫描器 | 源码压缩包解压（需编译） |
| 3 | Sqlmap | SQL注入检测利用工具 | 源码（Git/zip） |
| 4 | Hydra | 多协议暴力破解工具 | 源码压缩包解压（需编译） |
| 5 | Hashcat | 哈希密码破解工具 | 7z 解压 |
| 6 | FFUF | Web模糊测试/目录爆破 | zip 解压 |
| 7 | Dirsearch | Web网站目录扫描工具 | 源码（Git/zip） |
| 8 | Gobuster | 目录/文件/DNS暴力枚举 | zip 解压 |
| 9 | Whois | 域名信息查询工具 | zip 解压 |
| 10 | Xray | Web漏洞扫描器（闭源） | 需手动下载 |
| 11 | Wireshark | 网络协议分析器 | exe 静默安装 |
| 12 | Nuclei | 模板化漏洞扫描器 | zip 解压 |
| 13 | Subfinder | 子域名发现工具 | zip 解压 |
| 14 | Httpx | HTTP探测工具 | zip 解压 |
| 15 | RustScan | Rust高速端口扫描器 | zip 解压 |
| 16 | John | 密码哈希破解工具 | 源码压缩包解压（需编译） |
| 17 | Mimikatz | Windows凭据提取工具 | zip 解压 |
| 18 | Responder | LLMNR/NBT-NS投毒工具 | 源码（Git/zip） |
| 19 | Evil-WinRM | Windows远程管理工具 | 源码（Git/zip） |
| 20 | Impacket | 网络协议工具集 | 源码（Git/zip） |
| 21 | CrackMapExec | 内网SMB/域渗透工具 | 源码（Git/zip） |

> 注：上表"部署方式"描述 BAT 脚本的行为。三种方式获取源码的手段略有差异：
> BAT 对 Sqlmap/Dirsearch/Responder/Evil-WinRM/Impacket/CrackMapExec 使用 `git clone`，
> 而 GUI 与 PS1 下载源码 zip 包解压（不产生 `.git` 仓库）。工具最终形态一致。

## 使用方法

> **不想克隆仓库？** 直接前往 [Releases](../../releases/latest) 下载
> `KaliToolsGUI.exe`（展开 Assets 区域），下载后直接以管理员身份运行即可。
> 每个 Release 的说明中都附有 exe 的 SHA256 值，下载后可自行校验完整性。

### 方式一：图形化界面（推荐）

```
右键 dist\KaliToolsGUI.exe → 以管理员身份运行
```

若 dist 目录不存在，可重新构建：

```bat
build_exe.bat
```

### 方式二：命令行 BAT 脚本

```
右键 SecTools_Deploy.bat → 以管理员身份运行
输入编号（如 1,3,7）或 A 全部部署
```

### 方式三：PowerShell 脚本

```
右键 Kali-Tools-Deployer.ps1 → 使用 PowerShell 运行
选择部署模式
```

> `启动部署工具.bat` 是智能启动器：`dist\KaliToolsGUI.exe` 存在时启动 GUI，
> 缺失时回退到 PowerShell 脚本。

## 下载源验证

所有工具下载 URL 均经过实际连通性测试（HEAD 请求验证），失效链接已替换：

- GitHub Release 二进制：Gobuster、FFUF、Nuclei、Subfinder、Httpx、RustScan、Mimikatz
- 源码仓库：Masscan、Hydra、Sqlmap、Dirsearch、John、Responder、Evil-WinRM、Impacket、CrackMapExec
- 官方站点：Nmap、Hashcat、Wireshark、Whois (Sysinternals)

GUI 内置 SHA256 校验机制（工具配置含 `sha256` 字段时自动校验）。

以上 URL 由 [URL health 工作流](.github/workflows/url-health.yml) 每周自动检查
（覆盖 JSON / BAT / PS1 三处来源），失效时可
[提交链接失效 Issue](../../issues/new?template=broken-link.yml)反馈。

## 部署目录

- 工具安装目录：`C:\SecTools\`
- 日志文件：`C:\SecTools\deploy_log.txt`

## 系统要求

- Windows 10 / Windows 11
- 需要管理员权限
- 部分工具需要 Python 3 环境、Git（缺失时脚本会自动引导安装）

## 项目结构

```
├── KaliToolsGUI.py            图形界面（可打包为 exe）
├── SecTools_Deploy.bat        命令行部署脚本（GBK 编码）
├── SecTools_Uninstall.bat     卸载脚本
├── Kali-Tools-Deployer.ps1    PowerShell 部署脚本
├── 启动部署工具.bat            启动器（优先启动 GUI）
├── deploy_config.json         下载源权威配置（URL/目录/SHA256）
├── dist/KaliToolsGUI.exe      预编译图形界面
├── scripts/check_urls.py      下载源健康检查工具
├── check_all.bat              一键本地检查（测试+编译+下载源）
├── test_kalitools.py          离线回归测试（配置/BAT/PS1）
├── test_check_urls.py         URL 检查工具自身的测试
├── requirements.txt           Python 依赖（py7zr）
├── SECURITY.md                安全漏洞报告策略
├── LICENSE                    MIT 许可证
└── .github/
    ├── workflows/             CI（测试）、每周链接检查、tag 自动发布
    ├── ISSUE_TEMPLATE/        链接失效报告模板
    └── dependabot.yml         依赖自动更新
```

## 开发与测试

```bash
# 安装依赖（运行 GUI/测试所需）
pip install -r requirements.txt

# 离线回归测试（无需网络/管理员权限，覆盖配置一致性、SHA256、BAT 结构、PS1 语法）
python -m unittest test_kalitools test_check_urls -v

# 检查全部下载源是否可用（HEAD 请求，失效退出码 1）
python scripts/check_urls.py            # 全部来源：JSON + BAT + PS1
python scripts/check_urls.py --config   # 仅 deploy_config.json

# 重新打包 GUI
build_exe.bat

# 一键本地检查：单元测试 + 语法编译检查 + 下载源健康检查（失败返回非零退出码）
check_all.bat            # 全部检查
check_all.bat offline    # 跳过下载源检查（离线/内网环境）
```

> `check_all.bat` 不含 GUI 打包（打包见上方 `build_exe.bat`）；
> 无人值守调用时可加 `offline` 参数避免联网检查拖慢流程。

> **关于 exe 体积差异**：`dist/` 中的入库 exe 由本地环境打包，Release 资产由
> CI 打包，两者字节数可能不同（如 19MB vs 14MB）。这来自 UPX 是否可用、
> Python 补丁版本等环境差异，**不影响功能**；Release 资产每次发布都从
> 同一份源码重新构建，且 notes 中附 SHA256 可供校验。

推送到 `main` 时 CI 自动运行测试；每周一定时检查下载源健康状况。

**发布新版本**：推送 `V*` 形式 tag（如 `V26.10.1`）即自动跑测试、构建 exe 并创建/更新 Release 资产（见 [release.yml](.github/workflows/release.yml)），无需手动打包上传。

### 配置约定

`deploy_config.json` 是下载 URL、部署目录与 SHA256 哈希的**权威来源**，
GUI 启动时自动加载覆盖（编号/名称/目录/URL 由 `test_kalitools.py` 强制校验
GUI 与 JSON 一致）。BAT 与 PS1 内各自硬编码了下载源，修改时需三处同步；
`scripts/check_urls.py` 每周校验三处 URL 的连通性（但不校验彼此一致性）。

## 故障排查

| 现象 | 解决方案 |
|------|----------|
| 提示需要管理员权限 | 右键脚本/EXE → "以管理员身份运行" |
| GitHub 下载失败或很慢 | 挂代理，或手动下载后放入 `C:\SecTools` 对应目录 |
| Hashcat 提示缺少 7-Zip | 安装 [7-Zip](https://www.7-zip.org/) 后重试 |
| 工具装好但命令不识别 | 重新打开 CMD/PowerShell（PATH 变更需新会话生效） |
| 安全软件报毒/拦截 | 安全工具易被误报，添加信任或暂时关闭实时防护 |
| 源码类工具无法使用 | Masscan/Hydra/John 仅有源码，需自行编译；Git 类需安装 Git |

## 免责声明

本工具仅允许个人学习、完全授权的实验环境使用。严禁扫描、渗透任何没有获得书面授权的设备、系统。非法使用产生全部法律责任，全部由操作者本人承担。

## 许可证

[MIT](LICENSE)
