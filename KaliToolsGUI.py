import os
import sys
import time
import queue
import json
import hashlib
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
    {"id": 2, "name": "Masscan", "desc": "高速端口扫描", "method": "source",
     "url": GH_PROXY + "https://github.com/robertdavidgraham/masscan/archive/refs/heads/master.zip", "dir": "masscan",
     "hint": "源码已下载，需 Visual Studio 编译后使用"},
    {"id": 3, "name": "Sqlmap", "desc": "SQL 注入检测", "method": "source",
     "url": GH_PROXY + "https://github.com/sqlmapproject/sqlmap/archive/refs/heads/master.zip", "py": True, "dir": "sqlmap"},
    {"id": 4, "name": "Hydra", "desc": "多协议暴力破解", "method": "source",
     "url": GH_PROXY + "https://github.com/vanhauser-thc/thc-hydra/archive/refs/heads/master.zip", "dir": "hydra",
     "hint": "源码已下载，需编译后使用（官方无 Windows 二进制）"},
    {"id": 5, "name": "Hashcat", "desc": "哈希密码破解", "method": "7z",
     "url": "https://hashcat.net/files/hashcat-6.2.6.7z", "dir": "hashcat"},
    {"id": 6, "name": "FFUF", "desc": "Web 模糊测试", "method": "zip",
     "url": GH_PROXY + "https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_windows_amd64.zip", "dir": "ffuf"},
    {"id": 7, "name": "Dirsearch", "desc": "Web 目录扫描", "method": "source",
     "url": GH_PROXY + "https://github.com/maurosoria/dirsearch/archive/refs/heads/master.zip", "py": True, "dir": "dirsearch"},
    {"id": 8, "name": "Gobuster", "desc": "目录/子域名爆破", "method": "zip",
     "url": GH_PROXY + "https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_Windows_x86_64.zip", "dir": "gobuster"},
    {"id": 9, "name": "Whois", "desc": "域名信息查询", "method": "zip",
     "url": "https://download.sysinternals.com/files/WhoIs.zip", "dir": "whois"},
    {"id": 10, "name": "Xray", "desc": "Web 漏洞扫描(闭源)", "method": "empty", "url": "", "dir": "xray"},
    {"id": 11, "name": "Wireshark", "desc": "网络抓包分析", "method": "exe",
     "url": "https://2.na.dl.wireshark.org/win64/Wireshark-4.6.9-x64.exe", "dir": "wireshark",
     "args": ["/S"], "program_files": "Wireshark"},
    {"id": 12, "name": "Nuclei", "desc": "漏洞扫描器", "method": "zip",
     "url": GH_PROXY + "https://github.com/projectdiscovery/nuclei/releases/download/v3.3.8/nuclei_3.3.8_windows_amd64.zip", "dir": "nuclei"},
    {"id": 13, "name": "Subfinder", "desc": "子域名发现", "method": "zip",
     "url": GH_PROXY + "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.7/subfinder_2.6.7_windows_amd64.zip", "dir": "subfinder"},
    {"id": 14, "name": "Httpx", "desc": "HTTP 存活探测", "method": "zip",
     "url": GH_PROXY + "https://github.com/projectdiscovery/httpx/releases/download/v1.6.10/httpx_1.6.10_windows_amd64.zip", "dir": "httpx"},
    {"id": 15, "name": "RustScan", "desc": "快速端口扫描", "method": "zip",
     "url": GH_PROXY + "https://github.com/bee-san/RustScan/releases/download/2.4.1/x86_64-windows-rustscan.exe.zip", "dir": "rustscan"},
    {"id": 16, "name": "John", "desc": "密码哈希破解", "method": "source",
     "url": GH_PROXY + "https://github.com/openwall/john/archive/refs/heads/bleeding-jumbo.zip", "dir": "john",
     "hint": "源码已下载，需编译后使用（Windows 无官方二进制）"},
    {"id": 17, "name": "Mimikatz", "desc": "Windows 凭据提取", "method": "zip",
     "url": GH_PROXY + "https://github.com/gentilkiwi/mimikatz/releases/download/2.2.0-20220919/mimikatz_trunk.zip", "dir": "mimikatz"},
    {"id": 18, "name": "Responder", "desc": "LLMNR/NBT 投毒", "method": "source",
     "url": GH_PROXY + "https://github.com/lgandx/Responder/archive/refs/heads/master.zip", "py": True, "dir": "responder"},
    {"id": 19, "name": "Evil-WinRM", "desc": "Windows 远程管理", "method": "source",
     "url": GH_PROXY + "https://github.com/Hackplayers/evil-winrm/archive/refs/heads/master.zip", "py": True, "dir": "evil-winrm"},
    {"id": 20, "name": "Impacket", "desc": "网络协议工具集", "method": "source",
     "url": GH_PROXY + "https://github.com/fortra/impacket/archive/refs/heads/master.zip", "py": True, "pip": True, "dir": "impacket"},
    {"id": 21, "name": "CrackMapExec", "desc": "内网 SMB/域渗透", "method": "source",
     "url": GH_PROXY + "https://github.com/Porchetta-Industries/CrackMapExec/archive/refs/heads/master.zip",
     "py": True, "dir": "crackmapexec",
     "hint": "源码已下载，需 pip install 后使用"},
]

VERSION = "1.1.0"

# 辅助文件（如 7zr.exe）的 SHA256，键为原始 URL；由 deploy_config.json 填充
HELPER_HASHES = {}


def load_config_overrides():
    """从 deploy_config.json 覆盖 TOOLS 的 url/method/dir/sha256 字段。

    deploy_config.json 是下载 URL、下载方法、目录与哈希的权威配置，
    GUI/BAT/PS1 三方引用同一套下载源。JSON 中的 github.com URL
    自动加 GH_PROXY 前缀。结构异常时静默跳过，不影响 GUI 启动。
    """
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "deploy_config.json")
    if not os.path.isfile(cfg_path):
        return 0
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        by_id = {}
        for item in cfg.get("tools", []) or []:
            if not isinstance(item, dict):
                continue
            try:
                by_id[int(item.get("id"))] = item
            except (TypeError, ValueError):
                continue
        n = 0
        for tool in TOOLS:
            item = by_id.get(tool.get("id"))
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if isinstance(url, str) and url.strip():
                if url.startswith("https://github.com/") and not url.startswith(GH_PROXY):
                    url = GH_PROXY + url
                tool["url"] = url
            for key in ("method", "dir", "sha256"):
                val = item.get(key)
                if val:
                    tool[key] = val
            n += 1
        for helper in cfg.get("helper_files", []) or []:
            if isinstance(helper, dict) and helper.get("url") and helper.get("sha256"):
                HELPER_HASHES[helper["url"]] = helper["sha256"]
        return n
    except Exception:
        return 0


CONFIG_OVERRIDE_COUNT = load_config_overrides()


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


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def verify_sha256(path, expected):
    """校验文件 SHA256；expected 为空时跳过校验并返回 True。"""
    if not expected:
        return True
    actual = sha256_of(path)
    return actual == expected.upper()


# =============================================================================
# 液态玻璃风格 UI —— 纯表现层
# 部署 / 下载 / 校验 / 解压等核心逻辑不受本节任何改动影响
# =============================================================================

HEADER_PAD = 20       # 顶栏左右留白
HEADER_H = 104        # 顶栏高度
LOG_H = 132           # 日志区固定高度（其余空间留给工具卡片）

class GlassTheme(object):
    """深色玻璃主题配色（液态玻璃观感：高光边缘 + 半透明色层 + 柔和渐变）。"""
    bg_top = "#1A2036"        # 背景渐变（上）
    bg_bottom = "#080B14"     # 背景渐变（下）
    header_a = "#2A3358"      # 标题条渐变
    header_b = "#4B3A7A"
    card = "#171D2E"          # 卡片底色
    card_hover = "#1F2740"    # 卡片悬停
    card_on = "#1C2742"       # 卡片选中
    stroke = "#2C3550"        # 卡片描边
    stroke_hi = "#5C6B99"     # 悬停/选中描边（高光）
    text = "#EAEDF7"          # 主文字
    text_dim = "#8E99B8"      # 次要文字
    accent = "#5B8CFF"        # 主题强调色
    accent2 = "#A96BFF"       # 强调色渐变端
    success = "#3DDC97"
    danger = "#FF6B6B"
    warn = "#FFC24B"
    log_bg = "#0C101C"
    track = "#232B44"         # 进度条轨道

    # 圆角/间距/尺寸
    radius = 12
    card_radius = 14
    pad = 16


def _mix(c1, c2, t):
    """两个 #RRGGBB 颜色按 t(0..1) 线性混合，返回 #RRGGBB。"""
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rrect(cv, x1, y1, x2, y2, r, **kw):
    """圆角矩形（Tk 无原生圆角，用平滑多边形逼近）。"""
    r = max(1, min(r, int((x2 - x1) / 2), int((y2 - y1) / 2)))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return cv.create_polygon(pts, smooth=True, splinesteps=18, **kw)


def _vgrad(cv, x1, y1, x2, y2, c_from, c_to, tags=(), steps=72):
    """竖直线性渐变：用若干无边框矩形条带模拟（深色下视觉平滑）。"""
    h = float(y2 - y1)
    if h <= 0:
        return []
    steps = max(2, min(int(steps), int(h)))
    items = []
    for i in range(steps):
        t = i / float(steps - 1)
        ya = y1 + h * i / steps
        yb = y1 + h * (i + 1) / steps + 1
        items.append(cv.create_rectangle(x1, ya, x2, yb,
                                        fill=_mix(c_from, c_to, t),
                                        outline="", tags=tags))
    return items


def _hgrad(cv, x1, y1, x2, y2, c_from, c_to, tags=(), steps=48):
    """水平线性渐变。"""
    w = float(x2 - x1)
    if w <= 0:
        return []
    steps = max(2, min(int(steps), int(w)))
    items = []
    for i in range(steps):
        t = i / float(steps - 1)
        xa = x1 + w * i / steps
        xb = x1 + w * (i + 1) / steps + 1
        items.append(cv.create_rectangle(xa, y1, xb, y2,
                                        fill=_mix(c_from, c_to, t),
                                        outline="", tags=tags))
    return items


class GlassButton(tk.Canvas):
    """圆角玻璃按钮：渐变填充 + 顶部高光 + 悬停/按下反馈。"""

    def __init__(self, parent, text, command, theme=None, accent=False,
                 width=112, height=36, font=None):
        t = theme or GlassTheme
        tk.Canvas.__init__(self, parent, width=width, height=height,
                           highlightthickness=0, bd=0, bg=t.bg_bottom,
                           cursor="hand2")
        self._t = t
        self._text = text
        self._cmd = command
        self._accent = accent
        # 注意：不可用 self._w / self._h —— 它们是 tkinter 内部 widget 路径属性
        self._bw = width
        self._bh = height
        self._font = font or ("Microsoft YaHei UI", 10)
        self._state = "normal"
        self._enabled = True
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._redraw()

    # -- 状态 ---------------------------------------------------------------
    def _on_enter(self, _e):
        if self._enabled and self._state == "normal":
            self._state = "hover"
            self._redraw()

    def _on_leave(self, _e):
        self._state = "normal"
        self._redraw()

    def _on_press(self, _e):
        if self._enabled:
            self._state = "press"
            self._redraw()

    def _on_release(self, _e):
        was = self._state
        self._state = "hover" if self._enabled else "normal"
        self._redraw()
        if was == "press" and self._enabled and self._cmd:
            self._cmd()

    def set_enabled(self, flag):
        self._enabled = bool(flag)
        self.configure(cursor="hand2" if flag else "arrow")
        self._state = "normal"
        self._redraw()

    # -- 绘制 ---------------------------------------------------------------
    def _redraw(self):
        self.delete("all")
        t = self._t
        w, h = self._bw, self._bh
        if not self._enabled:
            fill_a, fill_b, fg, stroke = t.track, t.track, t.text_dim, t.stroke
        elif self._accent:
            fill_a = t.accent if self._state != "press" else t.accent2
            fill_b = t.accent2 if self._state != "press" else t.accent
            fg = "#FFFFFF"
            stroke = _mix(t.accent, "#FFFFFF", 0.35)
            if self._state == "hover":
                fill_a = _mix(t.accent, "#FFFFFF", 0.12)
                fill_b = _mix(t.accent2, "#FFFFFF", 0.12)
        else:
            base_a = t.card_hover if self._state == "hover" else t.card
            if self._state == "press":
                base_a = t.bg_bottom
            fill_a, fill_b = base_a, _mix(base_a, t.bg_top, 0.6)
            fg = t.text
            stroke = t.stroke_hi if self._state != "normal" else t.stroke

        r = h // 2 - 1  # 胶囊圆角
        _hgrad(self, 0, 0, w, h, fill_a, fill_b, steps=10)
        # 顶部高光：上半部分再叠一层白（玻璃反光）
        if self._enabled:
            _hgrad(self, 1, 1, w - 1, h * 0.5,
                   _mix(fill_a, "#FFFFFF", 0.16 if self._state != "press" else 0.04),
                   fill_a, steps=5)
        _rrect(self, 0.5, 0.5, w - 0.5, h - 0.5, r, fill="", outline=stroke,
               width=1)
        self.create_text(w / 2, h / 2, text=self._text, fill=fg,
                         font=self._font)


class GlassProgress(tk.Canvas):
    """圆角玻璃进度条：轨道 + 渐变填充 + 高光。"""

    def __init__(self, parent, theme=None, height=14, bg=None):
        t = theme or GlassTheme
        tk.Canvas.__init__(self, parent, height=height,
                           highlightthickness=0, bd=0,
                           bg=bg or t.bg_bottom)
        self._t = t
        # 不可用 self._h（避免与 tkinter 内部属性混淆）
        self._ph = height
        self._value = 0.0
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def set(self, percent):
        self._value = max(0.0, min(100.0, float(percent)))
        self._redraw()

    def get(self):
        return self._value

    def _redraw(self):
        self.delete("all")
        t = self._t
        w = max(4, self.winfo_width())
        h = self._ph
        r = h // 2
        _rrect(self, 0, 0, w, h, r, fill=t.track, outline=_mix(t.track, "#FFFFFF", 0.12))
        fw = int(w * self._value / 100.0)
        if fw >= h:
            # 条数设上限：进度回调在下载热路径上高频触发，
            # 渐变条数若随宽度线性增长会导致每次重绘重建大量 item 而卡顿
            _hgrad(self, 0, 0, fw, h, t.accent, t.accent2,
                   steps=min(max(8, fw // 3), 48))
            # 填充条顶部高光
            self.create_line(3, 3, max(4, fw - 3), 3,
                             fill=_mix(t.accent, "#FFFFFF", 0.45))
            _rrect(self, 0, 0, fw, h, r, fill="", outline="")


class ToolCardCanvas(tk.Canvas):
    """工具选择卡片区：圆角玻璃卡片网格，支持点击选中与悬停高光。"""

    def __init__(self, parent, tools, on_toggle, theme=None, columns=2,
                 card_h=62, gap=10, state_getter=None):
        t = theme or GlassTheme
        tk.Canvas.__init__(self, parent, highlightthickness=0, bd=0,
                           bg=t.bg_bottom)
        self._t = t
        self._tools = tools
        self._on_toggle = on_toggle
        self._state = state_getter or (lambda tid: False)
        self._cols = max(1, columns)
        self._card_h = card_h
        self._gap = gap
        self._card_w_pref = 300   # 期望卡宽（只读基准，不随布局回写）
        self._card_w = 300        # 本次布局实际算出的卡宽
        self._installed = set()
        self._hover = None
        self._pressed = None
        self._cards = {}          # tool_id -> item id 元组
        self._geom = []           # (x1, y1, x2, y2, tool_id) 命中区域

        self.bind("<Configure>", lambda e: self._layout())
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Button-4>", lambda e: self._scroll(-2))
        self.bind("<Button-5>", lambda e: self._scroll(2))
        self._layout()

    # -- 布局 ---------------------------------------------------------------
    def _layout(self):
        # 保留滚动位置：delete("all") 会重置视图，hover 重绘时必须还原
        try:
            keep_top = self.yview()[0]
        except Exception:
            keep_top = 0.0
        # 期望卡宽只读：由当前可用宽度一次性推出列数与卡宽，
        # 不可用上一次的 card_w 反推（否则列数会随 resize 历史漂移）
        avail = max(1, self.winfo_width() - 12)
        cols = max(1, int((avail + self._gap) // (self._card_w_pref + self._gap)))
        self._cols = cols
        w = avail
        self._card_w = max(1, (w - (cols + 1) * self._gap) // cols)
        self.delete("all")
        self._cards = {}
        self._geom = []

        rows = (len(self._tools) + cols - 1) // cols
        total_h = rows * self._card_h + (rows + 1) * self._gap
        for idx, tool in enumerate(self._tools):
            r, c = divmod(idx, cols)
            x1 = self._gap + c * (self._card_w + self._gap)
            y1 = self._gap + r * (self._card_h + self._gap)
            x2 = x1 + self._card_w
            y2 = y1 + self._card_h
            self._geom.append((x1, y1, x2, y2, tool["id"]))
            self._draw_card(tool, x1, y1, x2, y2)
        self.configure(scrollregion=(0, 0, w, max(total_h, 1)))
        self._total_h = total_h
        self._view_w = w
        self._draw_scrollbar()
        if keep_top:
            self.yview_moveto(keep_top)

    def _draw_scrollbar(self):
        """右侧细滚动条（内容超出可视高度时出现，滚动时同步位置）。"""
        self.delete("sb")
        view_h = self.winfo_height()
        total = getattr(self, "_total_h", 0)
        if view_h <= 1 or total <= view_h:
            return
        t = self._t
        sw = 6
        sx = self.winfo_width() - sw - 3
        first = self.yview()[0]
        thumb_h = max(28, int(view_h * (view_h / float(total))))
        # 可视滚动距离 = total - view_h；thumb 可移动距离 = view_h - thumb_h
        ty = int((view_h - thumb_h) * max(0.0, min(1.0, first)))
        _rrect(self, sx, 2, sx + sw, view_h - 2, sw // 2,
               fill=_mix(t.bg_bottom, "#FFFFFF", 0.06), outline="", tags="sb")
        _rrect(self, sx, ty + 2, sx + sw, ty + thumb_h - 2, sw // 2,
               fill=t.stroke_hi, outline="", tags="sb")
        self.tag_raise("sb")

    def _draw_card(self, tool, x1, y1, x2, y2):
        t = self._t
        tid = tool["id"]
        selected = bool(self._on_toggle_state(tid))
        hovered = (self._hover == tid)
        if selected:
            base = t.card_on
        elif hovered:
            base = t.card_hover
        else:
            base = t.card
        r = t.card_radius
        # 卡片内部竖向渐变：条数刻意压低（卡片小、色差小，8 条即平滑），
        # 避免 item 数量膨胀拖慢 hover 时的整体重绘
        grad = _vgrad(self, x1, y1, x2, y2, _mix(base, "#FFFFFF", 0.07), base,
                      tags=("card", tid), steps=8)
        # 顶部高光条（玻璃反光）
        _hgrad(self, x1 + 2, y1 + 1.5, x2 - 2, y1 + 4,
               _mix(base, "#FFFFFF", 0.22), _mix(base, "#FFFFFF", 0.02),
               tags=("card", tid), steps=8)
        stroke = t.stroke_hi if (hovered or selected) else t.stroke
        _rrect(self, x1 + 0.5, y1 + 0.5, x2 - 0.5, y2 - 0.5, r, fill="",
               outline=stroke, width=1, tags=("card", tid))
        # 选中态左侧强调条
        if selected:
            _rrect(self, x1 + 2, y1 + r * 0.6, x1 + 5, y2 - r * 0.6, 2,
                   fill=t.accent, outline="", tags=("card", tid))
        # 勾选指示器
        cx, cy = x1 + 26, (y1 + y2) / 2
        if selected:
            self.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill=t.accent,
                             outline=_mix(t.accent, "#FFFFFF", 0.4),
                             tags=("card", tid))
            self.create_line(cx - 4, cy, cx - 1, cy + 3.5, cx + 4.5, cy - 3.5,
                             fill="#FFFFFF", width=2, capstyle=tk.ROUND,
                             joinstyle=tk.ROUND, tags=("card", tid))
        else:
            self.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill=t.bg_bottom,
                             outline=t.stroke_hi, width=1, tags=("card", tid))
        # 文字（两行：名称 + 状态/说明）
        self.create_text(x1 + 44, y1 + 19, anchor=tk.W,
                         text="%d. %s" % (tid, tool["name"]),
                         fill=t.text, font=("Microsoft YaHei UI", 10, "bold"),
                         tags=("card", tid))
        state = tool.get("state_text", "")
        if tid in self._installed and not state:
            state = "已安装"
        color = t.success if state == "已安装" else (
            t.warn if "编译" in (state or "") else t.text_dim)
        self.create_text(x1 + 44, y1 + 38, anchor=tk.W,
                         text=state or tool["desc"],
                         fill=color, font=("Microsoft YaHei UI", 8),
                         tags=("card", tid))
        self._cards[tid] = (grad,)

    # -- 交互 ---------------------------------------------------------------
    def _on_toggle_state(self, tid):
        return bool(self._state(tid))

    def _on_wheel(self, e):
        self._scroll(-1 if e.delta > 0 else 1)

    def _scroll(self, units):
        self.yview_scroll(units * 3, "units")
        self._draw_scrollbar()

    def _hit(self, x, y):
        # 事件坐标是视口坐标，需换算回画布坐标（考虑滚动偏移）
        cy = self.canvasy(y)
        for x1, y1, x2, y2, tid in self._geom:
            if x1 <= x <= x2 and y1 <= cy <= y2:
                return tid
        return None

    def _on_motion(self, e):
        self._set_hover(self._hit(e.x, e.y))

    def _set_hover(self, tid):
        if tid != self._hover:
            self._hover = tid
            self._layout()

    def _on_press(self, e):
        self._pressed = self._hit(e.x, e.y)
        if self._pressed is not None:
            self.focus_set()

    def _on_release(self, e):
        tid = self._hit(e.x, e.y)
        if tid is not None and tid == self._pressed:
            self._on_toggle(tid)
        self._pressed = None
        self._layout()

    def mark_installed(self, tid, redraw=True):
        self._installed.add(tid)
        if redraw:
            self._layout()

    def refresh(self):
        self._layout()


class DeployerGUI:

    def __init__(self, root):
        self.root = root
        self.theme = GlassTheme()
        t = self.theme
        self.root.title("Kali Tools For Windows - 图形化部署工具 v%s" % VERSION)
        self.root.geometry("1120x800")
        self.root.minsize(980, 680)
        self.root.configure(bg=t.bg_bottom)
        self._apply_window_backdrop()
        self.vars = {tool["id"]: tk.BooleanVar(value=False) for tool in TOOLS}
        self.busy = False
        self.closing = False
        self._msg_queue = queue.Queue()
        self._build_widgets()
        self._draw_header()
        if not self._show_disclaimer():
            return
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll_queue)
        threading.Thread(target=self._detect_installed, daemon=True).start()

    def _apply_window_backdrop(self):
        """尝试启用 Windows 11 的系统背景材质（Mica/Acrylic）。
        失败或旧版系统上静默跳过——纯视觉增强，不影响任何功能。"""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            DWMSBT_TRANSIENTWINDOW = 3   # 类 Acrylic
            val = ctypes.c_int(DWMSBT_TRANSIENTWINDOW)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd), ctypes.c_int(DWMWA_SYSTEMBACKDROP_TYPE),
                ctypes.byref(val), ctypes.sizeof(val))
        except Exception:
            pass

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
                try:
                    kind, payload = self._msg_queue.get_nowait()
                except queue.Empty:
                    break
                # 单条消息处理异常不得中断整轮排空，否则后续消息会丢失
                try:
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
                except Exception as e:
                    try:
                        self.append_log("[ERROR] UI 消息处理异常: %r" % (e,))
                    except Exception:
                        pass
        finally:
            if not self.closing:
                self.root.after(100, self._poll_queue)

    def _build_widgets(self):
        t = self.theme
        P = t.pad

        # ---------- 顶栏：渐变玻璃标题条 ----------
        header = tk.Canvas(self.root, height=HEADER_H, highlightthickness=0,
                           bd=0, bg=t.header_b)
        header.pack(fill=tk.X, side=tk.TOP)
        self._header = header

        # ---------- 主体 ----------
        main = tk.Frame(self.root, bg=t.bg_bottom)
        main.pack(fill=tk.BOTH, expand=True, padx=P, pady=(10, P))

        # 工具卡片区
        cards_wrap = tk.Frame(main, bg=t.bg_bottom)
        cards_wrap.pack(fill=tk.BOTH, expand=True)
        lbl = tk.Label(cards_wrap, text="选择要部署的工具", bg=t.bg_bottom,
                       fg=t.text, font=("Microsoft YaHei UI", 10, "bold"),
                       anchor=tk.W)
        lbl.pack(fill=tk.X, pady=(0, 6))
        self._cards = ToolCardCanvas(cards_wrap, TOOLS, self._toggle_tool,
                                     theme=t, columns=2, card_h=56, gap=9,
                                     state_getter=self._tool_state)
        self._cards.pack(fill=tk.BOTH, expand=True)

        # 操作按钮行
        bar = tk.Frame(main, bg=t.bg_bottom)
        bar.pack(fill=tk.X, pady=(12, 0))
        self._buttons = []
        specs = [
            ("全选", self.select_all, False),
            ("清空", self.clear_all, False),
            ("开始部署", self.start_deploy, True),
            ("卸载工具", self.start_uninstall, False),
            ("打开工具目录", self.open_dir, False),
        ]
        for text, cmd, accent in specs:
            b = GlassButton(bar, text, cmd, theme=t, accent=accent,
                            width=124 if accent else 104)
            b.pack(side=tk.LEFT, padx=(0, 10))
            self._buttons.append(b)

        # 进度区（玻璃卡片容器，宽度随窗口自适应）
        prog_wrap = tk.Canvas(main, height=62, highlightthickness=0, bd=0,
                              bg=t.bg_bottom)
        prog_wrap.pack(fill=tk.X, pady=(12, 0))
        card_id = _rrect(prog_wrap, 0, 0, 10, 62, t.radius,
                         fill=t.card, outline=t.stroke)

        def _fit_prog_card(event, cv=prog_wrap, cid=card_id):
            cv.coords(cid, 0, 0, max(10, int(event.width)), 62)
            cv.tag_lower(cid)

        prog_wrap.bind("<Configure>", _fit_prog_card)
        tk.Label(prog_wrap, text="进度", bg=t.card, fg=t.text_dim,
                 font=("Microsoft YaHei UI", 8)).place(x=14, y=8)
        self._pct_lbl = tk.Label(prog_wrap, text="0%", bg=t.card, fg=t.accent,
                                 font=("Segoe UI", 10, "bold"))
        self._pct_lbl.place(x=58, y=6)
        self.progress = GlassProgress(prog_wrap, theme=t, height=10, bg=t.card)
        self.progress.place(x=14, y=34, relwidth=0.985, height=10)
        self._progress_sink = prog_wrap

        # 日志区（固定高度，把空间尽量留给工具卡片）
        log_wrap = tk.Frame(main, bg=t.bg_bottom)
        log_wrap.pack(fill=tk.X, pady=(12, 0))
        self._log_wrap = log_wrap
        tk.Label(log_wrap, text="部署日志", bg=t.bg_bottom, fg=t.text,
                 font=("Microsoft YaHei UI", 10, "bold"),
                 anchor=tk.W).pack(fill=tk.X, pady=(0, 6))
        shell = tk.Frame(log_wrap, bg=t.card, height=LOG_H)
        shell.pack(fill=tk.X)
        shell.pack_propagate(False)
        self._log_shell = shell
        self.log = scrolledtext.ScrolledText(
            shell, height=1, state=tk.DISABLED, font=("Consolas", 9),
            bg=t.log_bg, fg="#C8D2E8", insertbackground=t.accent,
            relief=tk.FLAT, bd=0, highlightthickness=0,
            selectbackground=_mix(t.accent, t.bg_bottom, 0.55),
            selectforeground="#FFFFFF", padx=10, pady=6)
        self.log.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # 状态栏
        self.status = tk.Label(main, text="就绪", anchor=tk.W, bg=t.bg_bottom,
                               fg=t.accent,
                               font=("Microsoft YaHei UI", 9))
        self.status.pack(fill=tk.X, pady=(10, 0))
        self.root.bind("<Configure>", self._on_resize, add="+")

    # ---------- UI 辅助（表现层） ----------
    def _tool_state(self, tid):
        var = self.vars.get(tid)
        return bool(var.get()) if var is not None else False

    def _toggle_tool(self, tid):
        var = self.vars.get(tid)
        if var is not None:
            var.set(not var.get())

    def _on_resize(self, event):
        # 顶栏渐变需随窗口宽度重绘；用事件宽度避免读到布局前的旧值。
        # 宽度未变化时不重绘（拖拽/最大化时避免高频抖动）
        if event.widget is self.root:
            w = int(event.width)
            if w != getattr(self, "_hdr_w", None):
                self._hdr_w = w
                self._draw_header(w)

    def _draw_header(self, width=None):
        h = self._header
        h.delete("all")
        w = int(width) if width else max(400, h.winfo_width())
        t = self.theme
        _hgrad(h, 0, 0, w, HEADER_H, t.header_a, t.header_b, steps=96)
        # 玻璃高光斜带
        _hgrad(h, 0, 0, w, 46, _mix(t.header_a, "#FFFFFF", 0.10),
               t.header_a, steps=32)
        # 底部渐隐分隔线
        _vgrad(h, 0, HEADER_H - 2, w, HEADER_H, t.header_b, t.bg_bottom,
               steps=2)
        h.create_text(HEADER_PAD, 34, anchor=tk.W, text="Kali Tools For Windows",
                      fill="#FFFFFF", font=("Microsoft YaHei UI", 19, "bold"))
        h.create_text(HEADER_PAD, 62, anchor=tk.W,
                      text="安全工具一键部署 · GUI",
                      fill=_mix(t.header_b, "#FFFFFF", 0.72),
                      font=("Microsoft YaHei UI", 9))
        h.create_text(HEADER_PAD, 82, anchor=tk.W,
                      text="目录 %s    日志 %s" % (TOOLS_ROOT, LOG_FILE),
                      fill=_mix(t.header_b, "#FFFFFF", 0.45),
                      font=("Microsoft YaHei UI", 8))
        # 右侧版本徽章
        bw, bh = 96, 30
        bx, by = w - bw - HEADER_PAD, 34
        _rrect(h, bx, by, bx + bw, by + bh, bh // 2,
               fill=_mix(t.header_a, "#FFFFFF", 0.14),
               outline=_mix(t.header_a, "#FFFFFF", 0.34))
        h.create_text(bx + bw / 2, by + bh / 2, text="v%s" % VERSION,
                      fill="#FFFFFF", font=("Segoe UI", 10, "bold"))

    def _show_disclaimer(self):
        ok = messagebox.askyesno(
            "免责声明",
            "本工具仅允许用于个人学习、完全授权的实验环境。\n\n"
            "严禁扫描、渗透任何未获得书面授权的设备或系统。\n"
            "非法使用产生的全部法律责任由操作者本人承担。\n\n"
            "是否同意并继续？")
        if not ok:
            self.root.destroy()
        return ok

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
        self.progress.set(value)
        try:
            self._pct_lbl.config(text="%d%%" % int(round(value)))
        except Exception:
            pass

    def _installed_ui(self, ids):
        if self.closing:
            return
        # 先置位再标记：否则 mark_installed 的重绘读到的仍是旧值，
        # 卡片不会显示为已勾选。全部处理完统一重绘一次（避免 N 次全量重绘）
        for tid in ids:
            var = self.vars.get(tid)
            if var is not None:
                var.set(True)
            self._cards.mark_installed(tid, redraw=False)
        if ids:
            self._cards.refresh()
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
        self._cards.refresh()

    def clear_all(self):
        for var in self.vars.values():
            var.set(False)
        self._cards.refresh()

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
            if tool.get("sha256"):
                if verify_sha256(tmp, tool["sha256"]):
                    self.append_log("[INFO] SHA256 校验通过")
                else:
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
                    raise RuntimeError("SHA256 校验失败，文件已删除（可能被篡改）")
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
        """获取 7zr.exe。

        主源 7-zip.org/a/7zr.exe 是滚动版本 URL，无法固定哈希（同 Nmap 策略，
        官方 HTTPS 直接信任）；备用源为固定版本 24.09，下载后强制 SHA256 校验。
        """
        exe = os.path.join(TOOLS_ROOT, "7zr.exe")
        if os.path.isfile(exe):
            return exe
        self.append_log("[INFO] 下载 7-Zip 解压器 ...")
        try:
            download("https://www.7-zip.org/a/7zr.exe", exe)
            return exe
        except Exception as e:
            self.append_log("[WARN] 7zr.exe 主源下载失败: %s，尝试备用源" % e)
            try:
                os.remove(exe)
            except OSError:
                pass
        gh_raw = "https://github.com/ip7z/7zip/releases/download/24.09/7zr.exe"
        expected = HELPER_HASHES.get(gh_raw)
        try:
            download(GH_PROXY + gh_raw, exe)
        except Exception as e:
            self.append_log("[WARN] 7zr.exe 下载失败: %s" % e)
            return None
        if expected and not verify_sha256(exe, expected):
            self.append_log("[WARN] 7zr.exe SHA256 校验失败，已删除")
            try:
                os.remove(exe)
            except OSError:
                pass
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
