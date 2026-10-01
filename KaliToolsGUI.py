import os
import sys
import time
import queue
import json
import hashlib
import threading
import datetime
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame,
                               QGridLayout, QHBoxLayout, QLabel,
                               QMessageBox, QPlainTextEdit,
                               QProgressBar, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)
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
# UI 层 —— PySide6 (Qt 6) 原生控件
# 渲染、控件、布局、滚动条、对话框全部使用 Qt 原生 API 与 QSS 样式表，
# 不含任何自绘绘制代码。部署 / 下载 / 校验 / 解压等核心逻辑保持不变。
# =============================================================================

APP_TITLE = "Kali Tools For Windows"
CARDS_PER_ROW = 3          # 工具卡片每行列数
LOG_HEIGHT = 150           # 日志区固定高度

# 深色玻璃主题配色（与迁移前视觉一致，全部通过 QSS 表达）
C_BG = "#080B14"
C_HEADER_A = "#2A3358"
C_HEADER_B = "#4B3A7A"
C_CARD = "#171D2E"
C_CARD_HOVER = "#1F2740"
C_CARD_ON = "#1C2742"
C_STROKE = "#2C3550"
C_STROKE_HI = "#5C6B99"
C_TEXT = "#EAEDF7"
C_TEXT_DIM = "#8E99B8"
C_ACCENT = "#5B8CFF"
C_ACCENT2 = "#A96BFF"
C_SUCCESS = "#3DDC97"
C_LOG_BG = "#0C101C"
C_TRACK = "#232B44"

QSS = """\
QWidget {
    background: %(bg)s; color: %(text)s;
    font-family: "Microsoft YaHei UI"; font-size: 13px;
}
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 %(hdr_a)s, stop:1 %(hdr_b)s);
    border: none;
}
QFrame#panel {
    background: %(card)s; border: 1px solid %(stroke)s;
    border-radius: 14px;
}
QFrame#card {
    background: %(card)s; border: 1px solid %(stroke)s;
    border-radius: 14px;
}
QFrame#card:hover { background: %(card_hover)s; border-color: %(stroke_hi)s; }
QFrame#card[state="on"] { background: %(card_on)s; border-color: %(accent)s; }
QFrame#card[state="on"]:hover { background: %(card_hover)s; border-color: %(accent)s; }
QLabel { background: transparent; }
QLabel#title {
    color: #FFFFFF; font-size: 27px; font-weight: bold;
}
QLabel#subtitle { color: %(dim)s; font-size: 13px; }
QLabel#paths { color: %(dim)s; font-size: 12px; }
QLabel#section { color: %(text)s; font-size: 14px; font-weight: bold; }
QLabel#status { color: %(accent)s; font-size: 13px; }
QLabel#pct { color: %(accent)s; font-size: 13px; font-weight: bold; }
QLabel#badge {
    color: #FFFFFF; font-size: 14px; font-weight: bold;
    background: rgba(255,255,255,38);
    border: 1px solid rgba(255,255,255,110);
    border-radius: 14px; padding: 6px 18px;
}
QLabel#desc { color: %(dim)s; font-size: 12px; }
QLabel#desc[installed="1"] { color: %(success)s; }
QCheckBox { color: %(text)s; background: transparent; spacing: 10px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 9px;
    border: 1px solid %(stroke_hi)s; background: %(bg)s;
}
QCheckBox::indicator:hover { border-color: %(accent)s; }
QCheckBox::indicator:checked { background: %(accent)s; border: 1px solid #FFFFFF; }
QPushButton {
    background: %(card)s; border: 1px solid %(stroke)s;
    border-radius: 17px; padding: 9px 22px;
    color: %(text)s; font-size: 14px;
}
QPushButton:hover { background: %(card_hover)s; border-color: %(stroke_hi)s; }
QPushButton:pressed { background: %(bg)s; }
QPushButton:disabled { background: %(track)s; color: %(dim)s; }
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 %(accent)s, stop:1 %(accent2)s);
    border: none; color: #FFFFFF; font-weight: bold;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #7BA1FF, stop:1 #BE8BFF);
}
QPushButton#primary:disabled { background: %(track)s; color: %(dim)s; }
QProgressBar {
    background: %(track)s; border: none; border-radius: 6px;
    height: 12px; text-align: center;
}
QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 %(accent)s, stop:1 %(accent2)s);
}
QPlainTextEdit {
    background: %(log_bg)s; color: #C8D2E8;
    border: 1px solid %(stroke)s; border-radius: 12px;
    font-family: Consolas; font-size: 13px;
    selection-background-color: %(accent)s;
}
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget { background: transparent; }
QWidget#canvas { background: transparent; }
QScrollBar:vertical {
    background: transparent; width: 12px; margin: 2px; border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: %(stroke_hi)s; border-radius: 5px; min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: %(accent)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { height: 0; }
""" % {
    "bg": C_BG, "hdr_a": C_HEADER_A, "hdr_b": C_HEADER_B, "card": C_CARD,
    "card_hover": C_CARD_HOVER, "card_on": C_CARD_ON, "stroke": C_STROKE,
    "stroke_hi": C_STROKE_HI, "text": C_TEXT, "dim": C_TEXT_DIM,
    "accent": C_ACCENT, "accent2": C_ACCENT2, "success": C_SUCCESS,
    "log_bg": C_LOG_BG, "track": C_TRACK,
}

_CHECKED = int(Qt.CheckState.Checked.value)
_YES = int(QMessageBox.StandardButton.Yes.value)


# --- 对话框助手：语义与迁移前的 tkinter messagebox 完全一致 ---------------
def _ask_yes_no(title, text):
    """等价 messagebox.askyesno：是 -> True，否 -> False。

    注意：PySide6 的 QMessageBox 位置参数为 (icon, title, text, buttons, parent)，
    没有 defaultButton 参数，必须构造后调用 setDefaultButton()。默认按钮保持与
    tkinter messagebox 一致为「是」，不改变原有交互行为。
    """
    box = QMessageBox(QMessageBox.Icon.Question, title, text,
                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    box.setDefaultButton(QMessageBox.StandardButton.Yes)
    return int(box.exec()) == _YES


def _warn(title, text):
    """等价 messagebox.showwarning。"""
    QMessageBox(QMessageBox.Icon.Warning, title, text,
                QMessageBox.StandardButton.Ok).exec()


def _err(title, text):
    """等价 messagebox.showerror。"""
    QMessageBox(QMessageBox.Icon.Critical, title, text,
                QMessageBox.StandardButton.Ok).exec()


class ToolCard(QFrame):
    """工具选择卡片：QFrame + QCheckBox + QLabel，质感全部由 QSS 呈现。"""

    toggled = Signal(int, bool)

    def __init__(self, tool, parent=None):
        super().__init__(parent)
        self.tid = int(tool["id"])
        self._orig_desc = tool.get("desc", "")
        self.setObjectName("card")
        self.setProperty("state", "off")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(62)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 9, 12, 9)
        lay.setSpacing(2)
        self.cb = QCheckBox("%d. %s" % (self.tid, tool["name"]), self)
        self.cb.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Bold))
        self.desc = QLabel(self._orig_desc, self)
        self.desc.setObjectName("desc")
        self.desc.setProperty("installed", "0")
        lay.addWidget(self.cb)
        lay.addWidget(self.desc)
        self._pressed = False
        self.cb.stateChanged.connect(self._on_state_changed)

    def _on_state_changed(self, state):
        checked = int(state) == _CHECKED
        self.setProperty("state", "on" if checked else "off")
        self._repolish(self)
        self.toggled.emit(self.tid, checked)

    @staticmethod
    def _repolish(w):
        # 动态属性变化后必须重新抛光 + update，QSS 才会稳定生效
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()

    def mousePressEvent(self, event):
        # 只记录按下；在 release 时确认仍在本卡片内才切换，
        # 避免在 QScrollArea 里拖动列表时误勾选（与迁移前行为一致）
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if (getattr(self, "_pressed", False)
                and event.button() == Qt.MouseButton.LeftButton
                and self.rect().contains(event.position().toPoint())):
            self.cb.toggle()
        self._pressed = False
        super().mouseReleaseEvent(event)

    def is_checked(self):
        return self.cb.isChecked()

    def set_checked(self, value):
        self.cb.setChecked(bool(value))

    def set_installed(self, flag):
        self.desc.setText("已安装" if flag else self._orig_desc)
        self.desc.setProperty("installed", "1" if flag else "0")
        self._repolish(self.desc)


class _MainWindow(QWidget):
    """顶层窗口：把关闭事件接到 GUI 的确认逻辑。

    对应迁移前 tkinter 的 root.protocol("WM_DELETE_WINDOW", self._on_close)。
    没有它，部署过程中点右上角 X 会直接退出、把 daemon 工作线程砍在半路。
    """

    def __init__(self):
        super().__init__()
        self.gui = None

    def closeEvent(self, event):
        gui = self.gui
        if gui is not None and not gui.closing and not gui.confirm_close():
            event.ignore()          # 用户取消 -> 保持窗口打开
            return
        event.accept()


class DeployerGUI:
    """界面层。部署逻辑沿用迁移前的实现与调用方式。"""

    def __init__(self, root):
        self.root = root                      # 顶层 QWidget
        if hasattr(root, "gui"):
            root.gui = self                   # 让 closeEvent 能回调本对象
        self.vars = {tool["id"]: False for tool in TOOLS}
        self.busy = False
        self.closing = False
        self._msg_queue = queue.Queue()       # 保持不变：核心函数直接投递
        self._cards = {}                      # tool_id -> ToolCard
        self._build_widgets()
        if not self._show_disclaimer():
            self.closing = True
            return
        # 100ms 轮询队列：把工作线程消息搬到 UI 线程（替代 tkinter after）
        self._timer = QTimer(self.root)
        self._timer.timeout.connect(self._poll_queue)
        self._timer.start(100)
        threading.Thread(target=self._detect_installed, daemon=True).start()

    def confirm_close(self):
        """是否允许关闭。忙碌时弹确认框（与迁移前 messagebox 行为一致）。"""
        if self.busy and not _ask_yes_no("确认退出",
                "部署正在进行中，强制退出可能导致安装不完整。\n确定要退出吗？"):
            return False
        self.closing = True
        timer = getattr(self, "_timer", None)
        if timer is not None:
            timer.stop()
        return True

    def _on_close(self):
        if self.confirm_close():
            self.root.close()

    def _poll_queue(self):
        if self.closing:
            return
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

    # ---- 构建界面 ---------------------------------------------------------
    @staticmethod
    def _section_label(text, parent):
        lbl = QLabel(text, parent)
        lbl.setObjectName("section")
        return lbl

    def _build_widgets(self):
        root = self.root
        root.setWindowTitle("%s - 图形化部署工具 v%s" % (APP_TITLE, VERSION))
        root.resize(1120, 800)
        root.setMinimumSize(980, 680)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 14)
        outer.setSpacing(0)

        # ---------- 顶栏 ----------
        header = QFrame(root)
        header.setObjectName("header")
        header.setFixedHeight(104)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(22, 14, 22, 12)
        hbox = QVBoxLayout()
        hbox.setSpacing(2)
        title = QLabel(APP_TITLE, header)
        title.setObjectName("title")
        sub = QLabel("安全工具一键部署 · GUI", header)
        sub.setObjectName("subtitle")
        paths = QLabel("目录 %s    日志 %s" % (TOOLS_ROOT, LOG_FILE), header)
        paths.setObjectName("paths")
        for w in (title, sub, paths):
            hbox.addWidget(w)
        hl.addLayout(hbox, 1)
        badge = QLabel("v%s" % VERSION, header)
        badge.setObjectName("badge")
        hl.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addWidget(header)

        # ---------- 主体 ----------
        body = QWidget(root)
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 12, 16, 0)
        bl.setSpacing(12)
        bl.addWidget(self._section_label("选择要部署的工具", body))

        scroll = QScrollArea(body)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        canvas = QWidget()
        canvas.setObjectName("canvas")
        grid = QGridLayout(canvas)
        grid.setContentsMargins(0, 0, 8, 0)
        grid.setSpacing(10)
        for i, tool in enumerate(TOOLS):
            card = ToolCard(tool)
            card.toggled.connect(self._on_card_toggled)
            self._cards[tool["id"]] = card
            grid.addWidget(card, i // CARDS_PER_ROW, i % CARDS_PER_ROW)
        for col in range(CARDS_PER_ROW):
            grid.setColumnStretch(col, 1)
        scroll.setWidget(canvas)
        bl.addWidget(scroll, 1)

        # ---------- 按钮行 ----------
        bar = QHBoxLayout()
        bar.setSpacing(10)
        self._buttons = []
        for text, slot, primary in (("全选", self.select_all, False),
                                    ("清空", self.clear_all, False),
                                    ("开始部署", self.start_deploy, True),
                                    ("卸载工具", self.start_uninstall, False),
                                    ("打开工具目录", self.open_dir, False)):
            btn = QPushButton(text, body)
            if primary:
                btn.setObjectName("primary")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            bar.addWidget(btn)
            self._buttons.append(btn)
        bar.addStretch(1)
        bl.addLayout(bar)

        # ---------- 进度 ----------
        panel = QFrame(body)
        panel.setObjectName("panel")
        pl = QHBoxLayout(panel)
        pl.setContentsMargins(14, 8, 14, 10)
        cap = QLabel("进度", panel)
        cap.setObjectName("subtitle")
        self._pct = QLabel("0%", panel)
        self._pct.setObjectName("pct")
        self.progress = QProgressBar(panel)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(12)
        pl.addWidget(cap)
        pl.addWidget(self._pct)
        pl.addWidget(self.progress, 1)
        bl.addWidget(panel)

        # ---------- 日志 ----------
        bl.addWidget(self._section_label("部署日志", body))
        self.log = QPlainTextEdit(body)
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.setFixedHeight(LOG_HEIGHT)
        bl.addWidget(self.log)

        # ---------- 状态栏 ----------
        self.status = QLabel("就绪", body)
        self.status.setObjectName("status")
        bl.addWidget(self.status)

        outer.addWidget(body, 1)

    def _on_card_toggled(self, tid, checked):
        self.vars[tid] = bool(checked)

    def _set_tool_state(self, tid, value):
        card = self._cards.get(tid)
        if card is not None:
            card.set_checked(bool(value))
        self.vars[tid] = bool(value)

    def _show_disclaimer(self):
        ok = _ask_yes_no(
            "免责声明",
            "本工具仅允许用于个人学习、完全授权的实验环境。\n\n"
            "严禁扫描、渗透任何未获得书面授权的设备或系统。\n"
            "非法使用产生的全部法律责任由操作者本人承担。\n\n"
            "是否同意并继续？")
        if not ok:
            self.root.close()
        return ok

    def append_log(self, msg):
        self._msg_queue.put(("log", msg))

    def set_status(self, text):
        self._msg_queue.put(("status", text))

    def _append_log_ui(self, msg):
        if self.closing:
            return
        self.log.appendPlainText(msg)

    def _status_ui(self, text):
        if self.closing:
            return
        self.status.setText(text)

    def _progress_ui(self, value):
        if self.closing:
            return
        # 首次收到进度事件即进入忙碌态：禁用按钮，避免重复触发
        if self.busy:
            for btn in self._buttons:
                btn.setEnabled(False)
        self.progress.setValue(int(value))
        self._pct.setText("%d%%" % int(round(value)))

    def _installed_ui(self, ids):
        if self.closing:
            return
        for tid in ids:
            # 先置位再标记，否则卡片重绘时读到的仍是旧值
            self._set_tool_state(tid, True)
            card = self._cards.get(tid)
            if card is not None:
                card.set_installed(True)
        if ids:
            self.status.setText("检测到 %d 个工具已安装（已自动勾选）" % len(ids))

    def _done_ui(self):
        if self.closing:
            return
        self.busy = False
        for btn in self._buttons:
            btn.setEnabled(True)
        if self.status.text() == "卸载完成":
            # 卸载流程会先投递 status="卸载完成"，此处不能覆盖成"部署完成"；
            # 同时工具已从磁盘删除，需清除已安装标记、勾选与进度
            for card in self._cards.values():
                card.set_installed(False)
            self.clear_all()
            self.progress.setValue(0)
            self._pct.setText("0%")
            return
        self.status.setText("部署完成")
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
        for tid in self.vars:
            self._set_tool_state(tid, True)

    def clear_all(self):
        for tid in self.vars:
            self._set_tool_state(tid, False)

    def open_dir(self):
        os.makedirs(TOOLS_ROOT, exist_ok=True)
        os.startfile(TOOLS_ROOT)

    def selected_tools(self):
        return [t for t in TOOLS if self.vars[t["id"]]]

    def start_deploy(self):
        if self.busy:
            return
        sel = self.selected_tools()
        if not sel:
            _warn("提示", "请先选择要部署的工具")
            return
        if not is_admin():
            _err("权限不足", "请以管理员身份运行本程序后再部署。")
            return
        needs_py = [t["name"] for t in sel if t.get("py")]
        if needs_py and not self._check_python():
            _err("缺少 Python",
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
            _err("权限不足", "请以管理员身份运行本程序后再卸载。")
            return
        if not _ask_yes_no("卸载确认", "将删除 %s 目录并还原系统 PATH，是否继续？" % TOOLS_ROOT):
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
    """Qt 6 入口。Qt 自行处理高 DPI 缩放，无需再手动调用 SetProcessDpiAwareness。"""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 9))
    app.setStyleSheet(QSS)
    root = _MainWindow()
    gui = DeployerGUI(root)
    if gui.closing:            # 用户未同意免责声明
        return 0
    root.show()
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main() or 0)
