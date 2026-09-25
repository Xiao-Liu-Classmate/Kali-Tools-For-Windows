# Kali-Tools-For-Windows

将 Kali Linux 常用安全工具一键部署到 Windows 系统。

## 简介

本工具支持通过命令行（BAT）、PowerShell 脚本、图形化界面（Python GUI）三种方式部署 21 个常用安全工具到 Windows。

## 工具列表（共 21 个）

| 编号 | 工具名 | 用途 | 部署方式 |
|------|--------|------|----------|
| 1 | Nmap | 端口扫描器 | exe 静默安装 |
| 2 | Masscan | 高速端口扫描器 | zip 解压 |
| 3 | Sqlmap | SQL注入检测利用工具 | 源码压缩包解压 |
| 4 | Hydra | 多协议暴力破解工具 | zip 解压 |
| 5 | Hashcat | 哈希密码破解工具 | 7z 解压 |
| 6 | FFUF | Web模糊测试/目录爆破 | zip 解压 |
| 7 | Dirsearch | Web网站目录扫描工具 | 源码压缩包解压 |
| 8 | Gobuster | 目录/文件/DNS暴力枚举 | zip 解压 |
| 9 | Whois | 域名信息查询工具 | zip 解压 |
| 10 | Xray | Web漏洞扫描器（闭源） | 需手动下载 |
| 11 | Wireshark | 网络协议分析器 | exe 静默安装 |
| 12 | Nuclei | 模板化漏洞扫描器 | zip 解压 |
| 13 | Subfinder | 子域名发现工具 | zip 解压 |
| 14 | Httpx | HTTP探测工具 | zip 解压 |
| 15 | RustScan | Rust高速端口扫描器 | zip 解压 |
| 16 | John | 密码哈希破解工具 | 源码压缩包解压 |
| 17 | Mimikatz | Windows凭据提取工具 | 7z 解压 |
| 18 | Responder | LLMNR/NBT-NS投毒工具 | 源码压缩包解压 |
| 19 | Evil-WinRM | Windows远程管理工具 | 源码压缩包解压 |
| 20 | Impacket | 网络协议工具集 | 源码压缩包解压 |
| 21 | CrackMapExec | 内网SMB/域渗透工具 | 源码压缩包解压 |

## 使用方法

### 方式一：图形化界面（推荐）

```
双击 KaliToolsGUI.exe（需管理员权限）
```

### 方式二：命令行 BAT 脚本

```
右键 SecTools_Deploy.bat → 以管理员身份运行
输入编号（如 1,3,7）或 A 全部部署
```

### 方式三：PowerShell 脚本

```
右键 启动部署工具.bat → 以管理员身份运行
选择部署模式
```

## 部署目录

- 工具安装目录：`C:\SecTools\`
- 日志文件：`C:\SecTools\deploy_log.txt`

## 系统要求

- Windows 10 / Windows 11
- 需要管理员权限
- 部分工具需要 Python 3 环境

## 免责声明

本工具仅允许个人学习、完全授权的实验环境使用。严禁扫描、渗透任何没有获得书面授权的设备、系统。非法使用产生全部法律责任，全部由操作者本人承担。
