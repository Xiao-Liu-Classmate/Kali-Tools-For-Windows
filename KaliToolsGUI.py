import os
import sys
import time
import queue
import threading
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import urllib.request
import zipfile
import subprocess
import shutil
import ctypes
import py7zr

TOOLS_ROOT = r"C:\SecTools"
LOG_FILE = os.path.join(TOOLS_ROOT, "deploy_log.txt")
GH_PROXY = "https://gh-proxy.com/"
APP_DIRS = ("bin", "x64", "run", "hashcat", "Bundled")

TOOLS = [
    {"id": 1, "name": "Nmap", "desc": "端口扫描器", "method": "exe",
     "url": "https://nmap.org/dist/nmap-7.95-setup.exe", "dir": "nmap",
     "args": ["/S"], "program_files": "Nmap"},
    {"id": 2, "name": "Masscan", "desc": "高速端口扫描器", "method": "source",
     "url": GH_PROXY + "https://github.com/robertdavidgraham/masscan/archive/refs/heads/master.zip", "dir": "masscan",
     "hint": "源码已下载，需 Visual Studio 编译后使用"},
    {"id": 3, "name": "Sqlmap", "desc": "SQL 注入检测工具", "method": "source",
     "url": GH_PROXY + "https://github.com/sqlmapproject/sqlmap/archive/refs/heads/master.zip", "py": True, "dir": "sqlmap"},
    {"id": 4, "name": "Hydra", "desc": "多协议暴力破解", "method": "source",
     "url": GH_PROXY + "https://github.com/vanhauser-thc/thc-hydra/archive/refs/heads/master.zip", "dir": "hydra",
     "hint": "源码已下载，需编译后使用"},
    {"id": 5, "name": "Hashcat", "desc": "哈希密码破解", "method": "7z",
     "url": GH_PROXY + "https://github.com/hashcat/hashcat/releases/download/v6.2.6/hashcat-6.2.6.7z", "dir": "hashcat"},
    {"id": 6, "name": "FFUF", "desc": "Web 模糊测试", "method": "zip",
     "url": GH_PROXY + "https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_windows_amd64.zip", "dir": "ffuf"},
    {"id": 7, "name": "Dirsearch", "desc": "Web 目录扫描", "method": "source",
     "url": GH_PROXY + "https://github.com/maurosoria/dirsearch/archive/refs/heads/master.zip", "py": True, "dir": "dirsearch"},
    {"id": 8, "name": "CrackMapExec", "desc": "内网 SMB / 域渗透", "method": "source",
     "url": GH_PROXY + "https://github.com/Porchetta-Industries/CrackMapExec/archive/refs/heads/master.zip", "py": True, "dir": "crackmapexec"},
    {"id": 9, "name": "Whois", "desc": "域名信息查询", "method": "zip",
     "url": "https://download.sysinternals.com/files/WhoIs.zip", "dir": "whois"},
    {"id": 10, "name": "Xray", "desc": "Web 漏洞扫描(闭源)", "method": "empty", "url": "", "dir": "xray"},
    {"id": 11, "name": "Wireshark", "desc": "网络抓包分析", "method": "exe",
     "url": "https://www.wireshark.org/download/win64/Wireshark-latest-x64.exe", "dir": "wireshark",
     "args": ["/S"], "program_files": "Wireshark"},
    {"id": 12, "name": "Gobuster", "desc": "目录/子域名爆破", "method": "zip",
     "url": GH_PROXY + "https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_Windows_x86_64.zip", "dir": "gobuster"},
    {"id": 13, "name": "Nuclei", "desc": "漏洞扫描器", "method": "zip",
     "url": GH_PROXY + "https://github.com/projectdiscovery/nuclei/releases/download/v3.3.8/nuclei_3.3.8_windows_amd64.zip", "dir": "nuclei"},
    {"id": 14, "name": "Subfinder", "desc": "子域名发现", "method": "zip",
     "url": GH_PROXY + "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.7/subfinder_2.6.7_windows_amd64.zip", "dir": "subfinder"},
    {"id": 15, "name": "Httpx", "desc": "HTTP 存活探测", "method": "zip",
     "url": GH_PROXY + "https://github.com/projectdiscovery/httpx/releases/download/v1.6.10/httpx_1.6.10_windows_amd64.zip", "dir": "httpx"},
    {"id": 16, "name": "RustScan", "desc": "快速端口扫描", "method": "zip",
     "url": GH_PROXY + "https://github.com/bee-san/RustScan/releases/download/2.3.0/rustscan-2.3.0-x86_64-windows.zip", "dir": "rustscan"},
    {"id": 17, "name": "John the Ripper", "desc": "密码破解", "method": "source",
     "url": GH_PROXY + "https://github.com/openwall/john/archive/refs/heads/bleeding-jumbo.zip", "dir": "john",
     "hint": "源码已下载，需编译后使用（Windows 无官方二进制）"},
    {"id": 18, "name": "Mimikatz", "desc": "Windows 凭据提取", "method": "zip",
     "url": GH_PROXY + "https://github.com/gentilkiwi/mimikatz/releases/download/2.2.0-20220919/mimikatz_trunk.zip", "dir": "mimikatz"},
    {"id": 19, "name": "Responder", "desc": "LLMNR/NBT 投毒", "method": "source",
     "url": GH_PROXY + "https://github.com/lgandx/Responder/archive/refs/heads/master.zip", "py": True, "dir": "responder"},
    {"id": 20, "name": "Evil-WinRM", "desc": "Windows 远程管理", "method": "source",
     "url": GH_PROXY + "https://github.com/Hackplayers/evil-winrm/archive/refs/heads/master.zip", "py": True, "dir": "evil-winrm"},
    {"id": 21, "name": "Impacket", "desc": "网络协议工具集", "method": "source",
     "url": GH_PROXY + "https://github.com/fortra/impacket/archive/refs/heads/master.zip", "py": True, "pip": True, "dir": "impacket"},
]

VERSION = "1.1.0"


def log_line(msg, fh=None):
    line = "[%s] %s" % (time_now(), msg)
    if fh:
        fh.write(line + "\n")
        fh.flush()
    return line


def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def download(url, dest, progress=None):
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "*/*",
            })
            with urllib.request.urlopen(req, timeout=300) as r:
                total = int(r.headers.get("Content-Length", 0))
                done = 0
                with open(dest, "wb") as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if progress and total:
                            progress(int(done * 100 / total))
            return dest
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise last_err


class DeployerGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Kali Tools For Windows - 图形化部署工具 v%s" % VERSION)
        self.root.geometry("860x680")
        self.root.minsize(760, 600)
        self.vars = {}
        self.busy = False
        self.closing = False
        self._msg_queue = queue.Queue()
        self._build_widgets()
        self._show_disclaimer()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll_queue)
        threading.Thread(target=self._detect_installed, daemon=True).start()

    def _on_close(self):
        if self.busy and not messagebox.askyesno("确认退出",
                "部署正在进行中，强制退出可能导致安装不完整。\n确定要退出吗？"):
            return
        self.closing = True
        self.root.destroy()

    def _poll_queue(self):
        if self.closing:
            return
        try:
            while True:
                kind, payload = self._msg_queue.get_nowait()
                if kind == "log":
                    self._append_log_ui(payload)
                elif kind == "status":
                    self._status_ui(payload)
                elif kind == "progress":
                    self._progress_ui(payload)
                elif kind == "done":
                    self._done_ui()
                elif kind == "installed":
                    self._installed_ui(payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _build_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text="Kali Tools For Windows - 安全工具一键部署",
                          font=("Microsoft YaHei UI", 14, "bold"))
        title.pack(anchor=tk.W)

        sub = ttk.Label(main, text="工具部署目录: %s    日志: %s" % (TOOLS_ROOT, LOG_FILE),
                        foreground="#666")
        sub.pack(anchor=tk.W, pady=(2, 8))

        box = ttk.LabelFrame(main, text="选择要部署的工具")
        box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        canvas = tk.Canvas(box, highlightthickness=0)
        vsb = ttk.Scrollbar(box, orient=tk.VERTICAL, command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>",
                    lambda ev: canvas.yview_scroll(int(-ev.delta / 120), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._tool_canvas = canvas

        self._desc_labels = {}
        for i, tool in enumerate(TOOLS):
            var = tk.BooleanVar(value=False)
            self.vars[tool["id"]] = var
            cb = ttk.Checkbutton(
                inner,
                text="%d. %s" % (tool["id"], tool["name"]),
                variable=var,
            )
            cb.grid(row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=(8, 8), pady=2)
            desc = ttk.Label(inner, text=tool["desc"], foreground="#888")
            desc.grid(row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, pady=2)
            self._desc_labels[tool["id"]] = desc

        btns = ttk.Frame(main)
        btns.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btns, text="全选", command=self.select_all).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="清空", command=self.clear_all).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="开始部署", command=self.start_deploy).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="卸载工具", command=self.start_uninstall).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="打开工具目录", command=self.open_dir).pack(side=tk.LEFT, padx=(0, 6))

        pbar = ttk.LabelFrame(main, text="进度")
        pbar.pack(fill=tk.X, pady=(0, 8))
        self.progress = ttk.Progressbar(pbar, maximum=100, value=0)
        self.progress.pack(fill=tk.X, padx=6, pady=6)
        self.progress_lbl = ttk.Label(pbar, text="", foreground="#666")
        self.progress_lbl.pack(anchor=tk.W, padx=6, pady=(0, 6))

        logbox = ttk.LabelFrame(main, text="部署日志")
        logbox.pack(fill=tk.BOTH, expand=True)
        self.log = scrolledtext.ScrolledText(logbox, height=12, state=tk.DISABLED,
                                             font=("Consolas", 9))
        self.log.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.status = ttk.Label(main, text="就绪", anchor=tk.W, foreground="#008")
        self.status.pack(fill=tk.X, pady=(6, 0))

    def _show_disclaimer(self):
        ok = messagebox.askyesno(
            "免责声明",
            "本工具仅允许用于个人学习、完全授权的实验环境。\n\n"
            "严禁扫描、渗透任何未获得书面授权的设备或系统。\n"
            "非法使用产生的全部法律责任由操作者本人承担。\n\n"
            "是否同意并继续？")
        if not ok:
            self.root.destroy()
            return

    def append_log(self, msg):
        self._msg_queue.put(("log", msg))

    def set_status(self, text):
        self._msg_queue.put(("status", text))

    def _append_log_ui(self, msg):
        if self.closing:
            return
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _status_ui(self, text):
        if self.closing:
            return
        self.status.config(text=text)

    def _progress_ui(self, value):
        if self.closing:
            return
        self.progress["value"] = value

    def _installed_ui(self, ids):
        if self.closing:
            return
        for tid in ids:
            label = self._desc_labels.get(tid)
            if label:
                label.config(text="已安装", foreground="#080")
            self.vars[tid].set(True)
        if ids:
            self.status.config(text="检测到 %d 个工具已安装（已自动勾选）" % len(ids))

    def _done_ui(self):
        if self.closing:
            return
        self.busy = False
        self.status.config(text="部署完成")
        self.append_log("==========================================")
        self.append_log("Deploy Complete!")

    def _detect_installed(self):
        installed = []
        for tool in TOOLS:
            d = os.path.join(TOOLS_ROOT, tool["dir"])
            if os.path.isdir(d) and os.listdir(d):
                installed.append(tool["id"])
        if installed:
            self._msg_queue.put(("installed", installed))

    def select_all(self):
        for var in self.vars.values():
            var.set(True)

    def clear_all(self):
        for var in self.vars.values():
            var.set(False)

    def open_dir(self):
        os.makedirs(TOOLS_ROOT, exist_ok=True)
        os.startfile(TOOLS_ROOT)

    def selected_tools(self):
        return [t for t in TOOLS if self.vars[t["id"]].get()]

    def start_deploy(self):
        if self.busy:
            return
        sel = self.selected_tools()
        if not sel:
            messagebox.showwarning("提示", "请先选择要部署的工具")
            return
        if not is_admin():
            messagebox.showerror("权限不足", "请以管理员身份运行本程序后再部署。")
            return
        needs_py = [t["name"] for t in sel if t.get("py")]
        if needs_py and not self._check_python():
            messagebox.showerror("缺少 Python",
                "以下工具依赖 Python 环境：%s\n\n"
                "请先安装 Python 3 并加入 PATH 后重试。" % ", ".join(needs_py))
            return
        self.busy = True
        threading.Thread(target=self._run_deploy, args=(sel,), daemon=True).start()

    def _check_python(self):
        try:
            r = subprocess.run(["python", "--version"], capture_output=True,
                               timeout=15, text=True)
            return r.returncode == 0 and "Python 3" in (r.stdout + r.stderr)
        except Exception:
            return False

    def start_uninstall(self):
        if self.busy:
            return
        if not is_admin():
            messagebox.showerror("权限不足", "请以管理员身份运行本程序后再卸载。")
            return
        if not messagebox.askyesno("卸载确认", "将删除 %s 目录并还原系统 PATH，是否继续？" % TOOLS_ROOT):
            return
        self.busy = True
        threading.Thread(target=self._run_uninstall, daemon=True).start()

    def _run_deploy(self, sel):
        self.append_log("========== 部署开始 %s ==========" % time_now())
        self.append_log("部署目录: %s" % TOOLS_ROOT)
        self._path_extra = []
        os.makedirs(TOOLS_ROOT, exist_ok=True)
        fh = None
        try:
            fh = open(LOG_FILE, "a", encoding="utf-8")
        except Exception:
            pass
        total = len(sel)
        for idx, tool in enumerate(sel, 1):
            self.set_status("正在部署 %s ... (%d/%d)" % (tool["name"], idx, total))
            self.append_log("---- 工具 %d: %s (%s) ----" % (tool["id"], tool["name"], tool["desc"]))
            try:
                self._deploy_one(tool, fh)
                msg = "完成: %s" % tool["name"]
                self.append_log("[INFO] %s" % msg)
                if tool.get("hint"):
                    self.append_log("[HINT] %s" % tool["hint"])
            except Exception as e:
                msg = "%s 部署失败: %s" % (tool["name"], e)
                self.append_log("[ERROR] %s" % msg)
            if fh:
                fh.write("%s\n" % log_line(msg))
        self._configure_path(fh)
        if fh:
            fh.write("%s\n" % log_line("部署结束"))
            fh.close()
        self._msg_queue.put(("progress", 100))
        self._msg_queue.put(("done", None))

    def _deploy_one(self, tool, fh):
        dest_dir = os.path.join(TOOLS_ROOT, tool["dir"])
        os.makedirs(dest_dir, exist_ok=True)
        if tool["method"] == "empty":
            with open(os.path.join(dest_dir, "README.txt"), "w", encoding="utf-8") as f:
                f.write("Xray 为闭源商业软件，无法自动下载。\n")
                f.write("请前往 https://github.com/chaitin/xray 手动下载后放入本目录。\n")
            self.append_log("[INFO] Xray 需手动下载，已创建占位目录")
            return
        if not tool["url"]:
            raise RuntimeError("缺少下载地址")
        fname = os.path.basename(tool["url"].split("?")[0]) or "download.bin"
        tmp = os.path.join(TOOLS_ROOT, ".tmp_" + tool["dir"] + "_" + fname)
        try:
            self.append_log("[INFO] 下载 %s ..." % tool["url"])
            download(tool["url"], tmp, progress=lambda p: self._msg_queue.put(
                ("progress", p)))
            if tool["method"] == "exe":
                args = tool.get("args") or ["/S"]
                self.append_log("[INFO] 正在静默安装 %s ..." % tool["name"])
                subprocess.run([tmp] + args, check=True)
                self._register_program_files(tool)
            elif tool["method"] == "7z":
                self.append_log("[INFO] 正在解压 %s ..." % tool["name"])
                sevenz = self._get_7zr()
                if sevenz:
                    subprocess.run([sevenz, "x", tmp, "-o" + dest_dir, "-y"],
                                   check=False, capture_output=True)
                else:
                    with py7zr.SevenZipFile(tmp) as z:
                        for info in z.list():
                            target = os.path.abspath(os.path.join(dest_dir, info.filename))
                            if not target.startswith(os.path.abspath(dest_dir)):
                                self.append_log("[SECURITY] 跳过路径遍历文件: %s" % info.filename)
                                continue
                        z.extractall(dest_dir)
                self._flatten(dest_dir)
            elif tool["method"] in ("zip", "source"):
                self.append_log("[INFO] 正在解压 %s ..." % tool["name"])
                with zipfile.ZipFile(tmp) as z:
                    for info in z.infolist():
                        target = os.path.abspath(os.path.join(dest_dir, info.filename))
                        if not target.startswith(os.path.abspath(dest_dir)):
                            self.append_log("[SECURITY] 跳过路径遍历文件: %s" % info.filename)
                            continue
                        z.extract(info, dest_dir)
                self._flatten(dest_dir)
            if tool.get("pip"):
                self._pip_install(tool, dest_dir)
        finally:
            if os.path.isfile(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

    def _pip_install(self, tool, dest_dir):
        self.append_log("[INFO] 正在安装 %s 的 Python 依赖 ..." % tool["name"])
        req = os.path.join(dest_dir, "requirements.txt")
        if not os.path.isfile(req):
            self.append_log("[WARN] 未找到 requirements.txt，跳过依赖安装")
            return
        r = subprocess.run(["python", "-m", "pip", "install", "-r", req,
                            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
                           capture_output=True, text=True, timeout=600)
        if r.returncode == 0:
            self.append_log("[INFO] %s 依赖安装完成" % tool["name"])
        else:
            self.append_log("[WARN] %s 依赖安装失败: %s" % (tool["name"], r.stderr[-300:]))

    def _get_7zr(self):
        exe = os.path.join(TOOLS_ROOT, "7zr.exe")
        if not os.path.isfile(exe):
            self.append_log("[INFO] 下载 7-Zip 解压器 ...")
            try:
                download("https://www.7-zip.org/a/7zr.exe", exe)
            except Exception:
                try:
                    download(GH_PROXY + "https://github.com/ip7z/7zip/releases/download/24.09/7zr.exe", exe)
                except Exception as e:
                    self.append_log("[WARN] 7zr.exe 下载失败: %s" % e)
                    return None
        return exe

    def _register_program_files(self, tool):
        pf = tool.get("program_files")
        if not pf:
            return
        base = os.environ.get("ProgramFiles", r"C:\Program Files")
        d = os.path.join(base, pf)
        if os.path.isdir(d):
            self._path_extra.append(d)

    def _flatten(self, dest_dir):
        items = [os.path.join(dest_dir, x) for x in os.listdir(dest_dir)]
        dirs = [p for p in items if os.path.isdir(p)]
        if len(dirs) == 1 and not [p for p in items if os.path.isfile(p)]:
            inner = dirs[0]
            for sub in os.listdir(inner):
                shutil.move(os.path.join(inner, sub), os.path.join(dest_dir, sub))
            os.rmdir(inner)

    def _configure_path(self, fh):
        self.append_log("[INFO] 正在配置系统 PATH ...")
        dirs = []
        for tool in TOOLS:
            d = os.path.join(TOOLS_ROOT, tool["dir"])
            for sub in APP_DIRS:
                sd = os.path.join(d, sub)
                if os.path.isdir(sd):
                    dirs.append(sd)
            if os.path.isdir(d):
                dirs.append(d)
        dirs += self._path_extra
        seen = set()
        unique = []
        for d in dirs:
            if d not in seen:
                seen.add(d)
                unique.append(d)
        extra = ";".join(unique)
        if extra:
            ps = (
                "$base=[Environment]::GetEnvironmentVariable('PATH','Machine');"
                "$parts=@($base.Split(';') | Where-Object { $_ });"
                "$newParts=$parts + @($env:EXTRA.Split(';') | Where-Object { "
                "$_ -and ($parts -notcontains $_) });"
                "[Environment]::SetEnvironmentVariable('PATH',($newParts -join ';'),'Machine')"
            )
            env = dict(os.environ)
            env["EXTRA"] = extra
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], env=env, check=False)
            self.append_log("[INFO] 已添加 %d 个工具目录到系统 PATH（重复项已跳过）" % len(unique))
        else:
            self.append_log("[INFO] 无可用工具目录，跳过 PATH 配置")

    def _run_uninstall(self):
        self.append_log("========== 卸载开始 %s ==========" % time_now())
        ps = (
            "$p=[Environment]::GetEnvironmentVariable('PATH','Machine');"
            "$parts=@($p.Split(';') | Where-Object { $_ -and $_ -notlike '*%s*' -and $_ -notlike '*%s*' });"
            "[Environment]::SetEnvironmentVariable('PATH',($parts -join ';'),'Machine')" % (TOOLS_ROOT, "\\SecTools")
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
            self.append_log("[INFO] 已从 PATH 中移除 %s 及工具安装路径" % TOOLS_ROOT)
        except Exception as e:
            self.append_log("[ERROR] PATH 还原失败: %s" % e)
        try:
            shutil.rmtree(TOOLS_ROOT, ignore_errors=True)
            self.append_log("[INFO] 已删除 %s" % TOOLS_ROOT)
        except Exception as e:
            self.append_log("[ERROR] 删除目录失败: %s" % e)
        self.append_log("Uninstall Complete!")
        self._msg_queue.put(("status", "卸载完成"))
        self._msg_queue.put(("done", None))


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except Exception:
        pass
    app = DeployerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
