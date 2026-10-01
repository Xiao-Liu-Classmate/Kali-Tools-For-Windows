# -*- coding: utf-8 -*-
"""GUI 层测试（PySide6 / Qt 6）。

分两部分：
  1. 引擎无关的逻辑测试（不需要显示器）
  2. Qt 控件冒烟测试（离屏平台 QT_QPA_PLATFORM=offscreen，无需真实显示器）

同时守护两条硬性约束：
  - 核心业务逻辑函数签名与实现不被改动
  - UI 不含自绘代码（不使用 canvas/paintEvent 手绘）
"""
import ast
import inspect
import os
import re
import sys
import unittest
import unittest.mock as mock

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# 离屏平台：让控件测试不需要真实显示器（必须在 QApplication 创建前设置）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    import PySide6  # noqa: F401
except Exception:                                   # pragma: no cover
    raise SystemExit("PySide6 未安装：请先 pip install -r requirements.txt")

import KaliToolsGUI as g  # noqa: E402


# =============================================================================
# 1. 约束守护（纯文本/反射，无需 Qt 运行时）
# =============================================================================
class TestMigrationConstraints(unittest.TestCase):

    def test_no_tkinter_anywhere(self):
        """用 AST 检查真实代码里没有 tkinter（注释/文档字符串不计入）。"""
        tree = ast.parse(inspect.getsource(g))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
        for token in ("tkinter", "messagebox", "ttk", "scrolledtext",
                      "BooleanVar", "Tk"):
            self.assertNotIn(token, names, "残留 tkinter 代码符号: %s" % token)

    def test_qt_is_the_engine(self):
        for name in ("QApplication", "QPushButton", "QProgressBar",
                     "QPlainTextEdit", "QScrollArea", "QCheckBox", "QFrame"):
            self.assertTrue(hasattr(g, name), "缺少 Qt 组件 %s" % name)
        self.assertTrue(hasattr(g, "QSS") and len(g.QSS) > 500)

    def test_no_hand_drawn_rendering(self):
        """UI 不得回退到手写底层渲染（AST 检查，排除注释与字符串）。"""
        tree = ast.parse(inspect.getsource(g))
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                called.add(node.attr)
            elif isinstance(node, ast.ClassDef):
                called.add(node.name)
        for token in ("create_polygon", "create_rectangle", "create_oval",
                      "create_line", "create_text", "paintEvent",
                      "QPainter", "Canvas", "Turtle"):
            self.assertNotIn(token, called, "出现自绘渲染: %s" % token)

    def test_core_logic_signatures_unchanged(self):
        expected = {
            "download": ["url", "dest", "progress"],
            "sha256_of": ["path"],
            "verify_sha256": ["path", "expected"],
            "is_admin": [],
            "load_config_overrides": [],
            "time_now": [],
            "log_line": ["msg", "fh"],
        }
        for name, params in expected.items():
            self.assertTrue(callable(getattr(g, name, None)), name)
            got = list(inspect.signature(getattr(g, name)).parameters)
            self.assertEqual(got, params, "%s 签名被改动" % name)

    def test_core_methods_unchanged(self):
        for name in ("_deploy_one", "_pip_install", "_get_7zr",
                     "_register_program_files", "_flatten", "_configure_path",
                     "_run_deploy", "_run_uninstall", "_check_python",
                     "open_dir", "_detect_installed"):
            self.assertTrue(callable(getattr(g.DeployerGUI, name, None)), name)

    def test_message_queue_preserved(self):
        """核心函数依赖 self._msg_queue 投递消息，队列类型不得改变。"""
        import queue as _q
        self.assertIs(g.queue, _q)
        src = inspect.getsource(g.DeployerGUI._deploy_one)
        self.assertIn("self._msg_queue.put", src)
        self.assertIn('"progress"', src)

    def test_qss_uses_engine_features(self):
        for token in ("qlineargradient", "border-radius", ":hover", ":disabled",
                      "QProgressBar::chunk", "QScrollBar::handle"):
            self.assertIn(token, g.QSS, "QSS 缺少引擎特性 %s" % token)


# =============================================================================
# 2. 构建参数一致性（build_exe.bat 与 release.yml 必须保持同步）
# =============================================================================
def _fake_screen(size, stripes=True):
    """构造可控的假屏幕：返回一张高对比竖条纹图，用于确定性验证模糊。"""
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QColor, QImage, QPainter

    class _Shot:
        def __init__(self, img):
            self._img = img

        def toImage(self):
            return self._img

    class _Screen:
        def __init__(self, img):
            self._img = img
            self.calls = 0

        def grabWindow(self, *_args):
            self.calls += 1
            return _Shot(self._img)

    img = QImage(size, QImage.Format.Format_RGB32)
    painter = QPainter(img)
    painter.fillRect(img.rect(), QColor(255, 255, 255))
    if stripes:                      # 间距 16px 的黑条：模糊后方差显著下降
        x = 0
        while x < size.width():
            painter.fillRect(QRect(x, 0, 8, size.height()), QColor(0, 0, 0))
            x += 16
    painter.end()
    return _Screen(img)


def _variance(qimage):
    """灰度方差：模糊会让方差明显下降。"""
    img = qimage.convertToFormat(
        __import__("PySide6.QtGui", fromlist=["QImage"]).QImage.Format.Format_RGB32)
    total = n = 0
    w, h = img.width(), img.height()
    for y in range(0, h, max(1, h // 40)):
        for x in range(0, w, max(1, w // 40)):
            c = img.pixelColor(x, y)
            total += (c.red() + c.green() + c.blue()) / 3.0
            n += 1
    if n == 0:
        return 0.0
    mean = total / n
    acc = 0.0
    for y in range(0, h, max(1, h // 40)):
        for x in range(0, w, max(1, w // 40)):
            c = img.pixelColor(x, y)
            d = (c.red() + c.green() + c.blue()) / 3.0 - mean
            acc += d * d
    return acc / n


class TestGlassBackdrop(unittest.TestCase):
    """macOS 风格毛玻璃：无边框窗口 + 背景采样模糊。"""

    def _win(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        root = g._MainWindow()
        with mock.patch.object(g, "_ask_yes_no", return_value=True), \
             mock.patch.object(g, "threading"):
            gui = g.DeployerGUI(root)
            timer = getattr(gui, "_timer", None)
            if timer is not None:
                timer.stop()
        return gui, root

    def setUp(self):
        self._roots = []

    def tearDown(self):
        from PySide6.QtWidgets import QApplication, QWidget
        for r in self._roots:
            try:
                r.close()
                r.deleteLater()
            except Exception:
                pass
        QApplication.processEvents()

    def test_frameless_and_translucent(self):
        from PySide6.QtCore import Qt
        _gui, root = self._win()
        self._roots.append(root)
        self.assertTrue(root.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.assertTrue(
            root.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))

    def test_gui_is_wired_to_window(self):
        gui, root = self._win()
        self._roots.append(root)
        self.assertIs(root.gui, gui)

    # ---- 背景采样 ----
    def test_backdrop_is_blurred_not_pasted(self):
        """核心行为：输出必须比原图模糊（方差显著下降），而非直接贴原图。"""
        gui, root = self._win()
        self._roots.append(root)
        screen = _fake_screen(root.size())
        with mock.patch.object(type(root), "screen", return_value=screen):
            root.refresh_backdrop()
        self.assertIsNotNone(root._backdrop, "应产出背景图")
        self.assertEqual(root._backdrop.size(), root.size())
        before = _variance(screen._img)
        after = _variance(root._backdrop)
        self.assertGreater(before, 500.0, "测试图案本身应有明显对比")
        self.assertLess(after, before * 0.6,
                        "输出方差应显著低于原图，证明模糊已生效")

    def test_backdrop_falls_back_to_primary_screen(self):
        """取不到当前屏幕时应回退到主屏幕，而不是抛异常或留空。"""
        from PySide6.QtGui import QGuiApplication
        gui, root = self._win()
        self._roots.append(root)
        primary = _fake_screen(root.size())
        with mock.patch.object(type(root), "screen", return_value=None), \
             mock.patch.object(QGuiApplication, "primaryScreen",
                               staticmethod(lambda: primary)):
            root.refresh_backdrop()
        self.assertIsNotNone(root._backdrop, "应回退到主屏幕并产出背景图")

    def test_backdrop_null_grab_keeps_previous(self):
        """抓取失败时保留上一帧画面，而不是清成纯色（视觉更平滑）。"""
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QImage, QPixmap
        gui, root = self._win()
        self._roots.append(root)
        root._backdrop = QPixmap(root.size())
        root._backdrop.fill(Qt.GlobalColor.red)   # 代表"上一帧真实画面"

        class _Null:
            def grabWindow(self, *_a):
                class S:
                    def toImage(self):
                        return QImage()          # isNull() == True
                return S()
        with mock.patch.object(type(root), "screen", return_value=_Null()):
            root.refresh_backdrop()
        self.assertIsNotNone(root._backdrop, "抓取失败不应清空已有背景")
        kept = root._backdrop.toImage().pixelColor(5, 5)
        self.assertEqual((kept.red(), kept.green(), kept.blue()),
                         (255, 0, 0), "应保留的正是上一帧画面内容")

    def test_paint_falls_back_to_solid_glass_color(self):
        """_backdrop 为 None 时 paintEvent 仍要画出兜底底色+玻璃色（校验真实像素）。"""
        from PySide6.QtGui import QColor, QPixmap
        from PySide6.QtWidgets import QWidget
        gui, root = self._win()
        self._roots.append(root)
        hidden = [c for c in root.findChildren(QWidget)
                  if c is not root and c.isVisible()]
        for c in hidden:                    # 隐藏子控件，只留 paintEvent 的输出
            c.hide()
        root._backdrop = None
        try:
            pix = QPixmap(root.size())
            root.render(pix)
            got = pix.toImage().pixelColor(5, 5)
            base = QColor(g.C_BG)
            a = g.GLASS_TINT.alpha()
            want = QColor(
                (base.red() * a + g.GLASS_TINT.red() * (255 - a)) // 255,
                (base.green() * a + g.GLASS_TINT.green() * (255 - a)) // 255,
                (base.blue() * a + g.GLASS_TINT.blue() * (255 - a)) // 255)
            self.assertLessEqual(abs(got.red() - want.red()), 6)
            self.assertLessEqual(abs(got.green() - want.green()), 6)
            self.assertLessEqual(abs(got.blue() - want.blue()), 6)
        finally:
            for c in hidden:
                c.show()

    def test_minimized_skips_sampling(self):
        gui, root = self._win()
        self._roots.append(root)
        with mock.patch.object(type(root), "isMinimized", return_value=True), \
             mock.patch.object(type(root), "screen",
                               side_effect=AssertionError("最小化时不应采样")):
            root.refresh_backdrop()        # 最小化时直接返回

    # ---- 定时器合并（防回归：曾出现 5 次请求排 5 个定时器）----
    def test_schedule_backdrop_coalesces(self):
        gui, root = self._win()
        self._roots.append(root)
        with mock.patch.object(g.QTimer, "singleShot") as st:
            for _ in range(5):
                root._schedule_backdrop(10)
            self.assertEqual(st.call_count, 1, "5 次请求应只排 1 个定时器")
            with mock.patch.object(root, "refresh_backdrop"):
                root._do_resample()         # 真实实现，清 pending
        with mock.patch.object(g.QTimer, "singleShot") as st:
            for _ in range(5):
                root._schedule_backdrop(10)
            self.assertEqual(st.call_count, 1, "pending 清除后应能再排 1 个")

    def test_timer_carries_context_receiver(self):
        """定时器必须带 context，窗口析构后自动取消，避免打到已释放对象。"""
        gui, root = self._win()
        self._roots.append(root)
        with mock.patch.object(g.QTimer, "singleShot") as st:
            root._schedule_backdrop(10)
        args = st.call_args[0]
        self.assertIs(args[1], root, "应传 self 作为 context 参数")
        self.assertEqual(len(args), 3, "应为 singleShot(delay, context, slot)")

    # ---- 无边框窗口交互 ----
    def _press(self, root, x, y):
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent
        handle = mock.Mock()
        with mock.patch.object(type(root), "windowHandle",
                               return_value=handle):
            ev = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(x, y),
                             QPointF(x, y), Qt.MouseButton.LeftButton,
                             Qt.MouseButton.LeftButton,
                             Qt.KeyboardModifier.NoModifier)
            root.mousePressEvent(ev)
        return handle

    def test_titlebar_blank_starts_system_move(self):
        """回归：条件曾写反导致无边框窗口完全拖不动。"""
        gui, root = self._win()
        self._roots.append(root)
        handle = self._press(root, root.width() // 2, 20)
        handle.startSystemMove.assert_called_once()
        handle.startSystemResize.assert_not_called()

    def test_content_area_does_not_move_window(self):
        gui, root = self._win()
        self._roots.append(root)
        handle = self._press(root, root.width() // 2,
                             g.TITLEBAR_H + 80)
        handle.startSystemMove.assert_not_called()
        handle.startSystemResize.assert_not_called()

    def test_edges_start_system_resize(self):
        from PySide6.QtCore import Qt
        gui, root = self._win()
        self._roots.append(root)
        w, h = root.width(), root.height()
        checks = [
            (1, h // 2, Qt.Edge.LeftEdge),
            (w - 1, h // 2, Qt.Edge.RightEdge),
            (w // 2, 1, Qt.Edge.TopEdge),
            (w // 2, h - 1, Qt.Edge.BottomEdge),
            (1, 1, Qt.Edge.LeftEdge | Qt.Edge.TopEdge),
            (w // 2, h // 2, Qt.Edge(0)),
        ]
        for x, y, want in checks:
            with self.subTest(x=x, y=y):
                handle = self._press(root, x, y)
                if want == Qt.Edge(0):
                    handle.startSystemResize.assert_not_called()
                else:
                    handle.startSystemResize.assert_called_once_with(want)
                    handle.startSystemMove.assert_not_called()

    def test_escape_key_closes_window(self):
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtGui import QKeyEvent
        gui, root = self._win()
        self._roots.append(root)
        with mock.patch.object(root, "close") as c:
            root.keyPressEvent(QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                Qt.KeyboardModifier.NoModifier))
        c.assert_called_once()

    # ---- 标题栏按钮 ----
    def test_titlebar_has_window_buttons(self):
        from PySide6.QtWidgets import QPushButton
        gui, root = self._win()
        self._roots.append(root)
        names = ("tl_close", "tl_min", "tl_max")
        btns = [b for b in root.findChildren(QPushButton)
                if b.objectName() in names]
        # macOS 交通灯顺序：关闭 - 最小化 - 最大化（从左到右）
        self.assertEqual([b.objectName() for b in btns], list(names))
        self.assertEqual([b.toolTip() for b in btns],
                         ["关闭", "最小化", "最大化"])
        self.assertIsNotNone(root.findChild(g.QFrame, "titlebar"))
        for b in btns:                     # 交通灯应为小圆点，且三种颜色不同
            self.assertEqual(b.width(), 14)
            self.assertEqual(b.height(), 14)
        for n in names:                    # QSS 必须给每个交通灯上色
            self.assertIn("QPushButton#%s" % n, g.QSS)

    def test_window_buttons_delegate(self):
        gui, root = self._win()
        self._roots.append(root)
        with mock.patch.object(root, "showMinimized") as m:
            gui._win_minimize()
        m.assert_called_once()
        with mock.patch.object(root, "isMaximized", return_value=False), \
             mock.patch.object(root, "showMaximized") as mx:
            gui._win_toggle_maximize()
        mx.assert_called_once()
        with mock.patch.object(root, "isMaximized", return_value=True), \
             mock.patch.object(root, "showNormal") as mn:
            gui._win_toggle_maximize()
        mn.assert_called_once()

    def test_close_button_uses_confirm_path(self):
        gui, root = self._win()
        self._roots.append(root)
        gui.busy = True
        with mock.patch.object(g, "_ask_yes_no", return_value=False):
            gui._win_close()
        self.assertFalse(gui.closing)      # 取消 -> 不关闭
        with mock.patch.object(g, "_ask_yes_no", return_value=True):
            gui._win_close()
        self.assertTrue(gui.closing)

    def test_qss_uses_translucent_layers(self):
        for token in ("QFrame#titlebar", "QPushButton#tl_close",
                      "QPushButton#tl_min", "QPushButton#tl_max",
                      "background: transparent"):
            self.assertIn(token, g.QSS)
        # 控件层必须半透明，否则会盖住底层的毛玻璃
        for name in ("C_CARD", "C_LOG_BG", "C_CARD_HOVER"):
            self.assertTrue(getattr(g, name).startswith("rgba("),
                            "%s 应为半透明 rgba" % name)

    def test_qss_has_no_hash_comments(self):
        """回归：Qt QSS 不支持 '#' 行注释（# 是 ID 选择器前缀）。

        出现非法行会让解析中断，其后所有规则静默失效（曾导致交通灯不着色）。
        """
        for line in g.QSS.splitlines():
            self.assertFalse(line.strip().startswith("#"),
                             "QSS 中不能以 # 开头（会被当成 ID 选择器）: %s"
                             % line.strip())


class TestBuildConsistency(unittest.TestCase):
    """打包参数只在 build_exe.bat 与 release.yml 各写一份，用测试强制防漂移。"""

    GBK = "gbk"

    def _read(self, name, encoding="utf-8"):
        with open(os.path.join(BASE, name), encoding=encoding,
                  newline="") as f:
            return f.read()

    def _bat_pyinstaller_args(self):
        bat = self._read("build_exe.bat", self.GBK)
        self.assertIn("\r\n", bat, "build_exe.bat 必须保持 CRLF")
        self.assertNotIn("\n", bat.replace("\r\n", ""),
                         "build_exe.bat 出现裸 LF")
        self.assertNotRegex(bat, r"\?{4,}", "build_exe.bat 中文已损坏")
        marker = "python -m PyInstaller"
        start = bat.find(marker)
        self.assertNotEqual(start, -1,
                            "build_exe.bat 中未找到 PyInstaller 命令")
        collected = []
        for line in bat[start:].split("\r\n"):
            collected.append(line.rstrip())
            if not collected[-1].endswith("^"):
                break
        else:
            self.fail("build_exe.bat 中 ^ 续行未正常结束")
        flat = " ".join(l.rstrip("^").strip() for l in collected)
        return flat.split()

    def _yml_pyinstaller_args(self):
        yml = self._read(".github/workflows/release.yml")
        lines = yml.splitlines()
        for i, line in enumerate(lines):
            if line.strip() != "run: >-":
                continue
            indent = len(line) - len(line.lstrip())
            block = []
            for nxt in lines[i + 1:]:
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) < indent + 2:
                    break
                if nxt.strip():
                    block.append(nxt.strip())
            if any("python -m PyInstaller" in b for b in block):
                return " ".join(block).split()
        self.fail("release.yml 中未找到 PyInstaller 构建步骤")

    def test_pyinstaller_args_match(self):
        self.assertEqual(self._bat_pyinstaller_args(),
                         self._yml_pyinstaller_args(),
                         "打包参数在 build_exe.bat 与 release.yml 之间发生漂移")

    def test_pyinstaller_version_pinned_consistently(self):
        bat = self._read("build_exe.bat", self.GBK)
        yml = self._read(".github/workflows/release.yml")
        pins = []
        for name, src in (("build_exe.bat", bat),
                          ("release.yml", yml)):
            m = re.search(r"pyinstaller==([\w.]+)", src)
            self.assertIsNotNone(
                m, "%s 必须锁定 pyinstaller==x.y.z（供应链安全）" % name)
            pins.append(m.group(1))
        self.assertEqual(pins[0], pins[1], "pyinstaller 版本锁定值不一致")
        gate = re.search(r"PyInstaller\.__version__=='([\w.]+)'", bat)
        self.assertIsNotNone(
            gate, "build_exe.bat 的已安装检查必须校验精确版本")
        self.assertEqual(gate.group(1), pins[0],
                         "build_exe.bat 版本门槛与 pin 不一致")

    def test_qt_modules_excluded_from_bundle(self):
        """未使用的 Qt 模块必须在打包时裁掉（全量白名单，控制 exe 体积）。"""
        bat = self._read("build_exe.bat", self.GBK)
        yml = self._read(".github/workflows/release.yml")
        expected = [
            "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
            "PySide6.Qt3DCore", "PySide6.Qt3DRender",
            "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
            "PySide6.QtWebChannel", "PySide6.QtWebSockets",
            "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
            "PySide6.QtDesigner", "PySide6.QtUiTools", "PySide6.QtHelp",
            "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning",
            "PySide6.QtSensors", "PySide6.QtSerialPort",
            "PySide6.QtTextToSpeech",
        ]
        for mod in expected:
            self.assertIn("--exclude-module %s" % mod, bat,
                          "build_exe.bat 缺少裁剪项 %s" % mod)
            self.assertIn("--exclude-module %s" % mod, yml,
                          "release.yml 缺少裁剪项 %s" % mod)


# =============================================================================
# 3. 引擎无关逻辑
# =============================================================================
class TestSelectionLogic(unittest.TestCase):

    def _gui(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.closing = False
        gui.vars = {t["id"]: False for t in g.TOOLS}
        gui._cards = {}
        return gui

    def test_selected_tools_only_checked(self):
        gui = self._gui()
        gui.vars[3] = True
        gui.vars[7] = True
        names = [t["name"] for t in gui.selected_tools()]
        self.assertEqual([g.TOOLS[2]["name"], g.TOOLS[6]["name"]], names)

    def test_selected_tools_empty(self):
        self.assertEqual([], self._gui().selected_tools())

    def test_set_tool_state_updates_vars(self):
        gui = self._gui()
        gui._set_tool_state(5, True)
        self.assertTrue(gui.vars[5])
        gui._set_tool_state(5, False)
        self.assertFalse(gui.vars[5])

    def test_set_tool_state_tolerates_unknown_id(self):
        gui = self._gui()
        gui._set_tool_state(999, True)      # 不应抛异常
        self.assertTrue(gui.vars[999])


class TestPollQueueResilience(unittest.TestCase):
    """队列抽水：单条消息异常不得丢弃后续消息。"""

    class _Q(object):
        def __init__(self, items):
            self.items = list(items)

        def get_nowait(self):
            import queue as _q
            if not self.items:
                raise _q.Empty
            return self.items.pop(0)

    def _gui(self, items):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.closing = False
        gui._msg_queue = self._Q(items)
        return gui

    def test_exception_isolated(self):
        gui = self._gui([("progress", 1), ("status", "ok"), ("log", "hi")])
        seen = []
        gui._progress_ui = lambda v: (_ for _ in ()).throw(RuntimeError("boom"))
        gui._status_ui = lambda v: seen.append(("status", v))
        gui._append_log_ui = lambda m: seen.append(("log", m))
        gui._done_ui = lambda: seen.append(("done", None))
        gui._installed_ui = lambda v: seen.append(("installed", v))
        gui.append_log = lambda m: seen.append(("error", m))
        gui._poll_queue()
        self.assertIn(("status", "ok"), seen)
        self.assertIn(("log", "hi"), seen)
        self.assertTrue(any(k == "error" for k, _ in seen))

    def test_empty_queue_is_noop(self):
        gui = self._gui([])
        gui._poll_queue()          # 不应抛异常

    def test_closing_stops_processing(self):
        gui = self._gui([("log", "x")])
        gui.closing = True
        called = []
        gui._append_log_ui = lambda m: called.append(m)
        gui._poll_queue()
        self.assertEqual([], called)


class TestDialogHelpers(unittest.TestCase):
    """对话框语义与默认按钮必须与迁移前的 tkinter messagebox 一致。"""

    def test_dialog_helpers_preserve_behaviour(self):
        from PySide6.QtWidgets import QMessageBox
        captured = {}

        class _Box(object):
            """与 _ask_yes_no 的调用形态一致：4 个位置参数 + setDefaultButton。"""

            # 让桩对象保留 Icon / StandardButton 枚举访问
            Icon = QMessageBox.Icon
            StandardButton = QMessageBox.StandardButton

            def __init__(self, icon, title, text, buttons):
                captured.update(icon=icon, title=title, text=text,
                                buttons=buttons, default=None)

            def setDefaultButton(self, button):
                captured["default"] = button

            def exec(self):
                return int((captured["default"] or
                            captured["buttons"]).value)

        # 默认按钮为「是」-> 返回 True
        with mock.patch.object(g, "QMessageBox", _Box):
            self.assertTrue(g._ask_yes_no("t", "m"))
        self.assertEqual(captured["default"], QMessageBox.StandardButton.Yes)
        buttons = int(captured["buttons"])
        # 按钮集合是位掩码，用按位与判断
        self.assertTrue(int(QMessageBox.StandardButton.Yes.value) & buttons)
        self.assertTrue(int(QMessageBox.StandardButton.No.value) & buttons)

        # 点击「否」-> 返回 False
        with mock.patch.object(g, "QMessageBox", _Box), \
             mock.patch.object(g, "_YES",
                               int(QMessageBox.StandardButton.No.value)):
            self.assertFalse(g._ask_yes_no("t", "m"))

        # _warn / _err：只提供 Ok 按钮，图标分别为 Warning / Critical
        for helper, icon in ((g._warn, QMessageBox.Icon.Warning),
                             (g._err, QMessageBox.Icon.Critical)):
            captured.clear()
            with mock.patch.object(g, "QMessageBox", _Box):
                helper("t", "m")
            self.assertEqual(captured["icon"], icon)
            self.assertEqual(int(captured["buttons"]),
                             int(QMessageBox.StandardButton.Ok.value))


class TestDisclaimerContract(unittest.TestCase):

    def test_accept_keeps_running(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.root = mock.Mock()
        gui.closing = False
        with mock.patch.object(g, "_ask_yes_no", return_value=True):
            self.assertTrue(gui._show_disclaimer())
        gui.root.close.assert_not_called()

    def test_decline_closes_window(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.root = mock.Mock()
        gui.closing = False
        with mock.patch.object(g, "_ask_yes_no", return_value=False):
            self.assertFalse(gui._show_disclaimer())
        gui.root.close.assert_called_once()


# =============================================================================
# 3. Qt 控件冒烟（离屏）
# =============================================================================
class TestQtWidgets(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._roots = []

    def tearDown(self):
        # 必须显式销毁窗口：QCloseEvent 不删除顶层控件，
        # 否则离屏插件会累积窗口并最终阻塞整个测试进程
        for root in self._roots:
            try:
                root.close()
                root.deleteLater()
            except Exception:
                pass
        self._roots = []
        self.app.processEvents()

    def _build(self):
        """构造被测窗口：屏蔽模态框与后台线程，并登记以便销毁。"""
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget
        root = QWidget()
        root.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        with mock.patch.object(g, "_ask_yes_no", return_value=True), \
             mock.patch.object(g, "threading"):
            gui = g.DeployerGUI(root)
        # 测试中手动调用 _poll_queue，不需要定时器持续触发
        timer = getattr(gui, "_timer", None)
        if timer is not None:
            timer.stop()
        self._roots.append(root)
        return gui, root

    def test_dialog_construction_signature_is_valid(self):
        """真实构造 QMessageBox（不 exec），防止参数签名错误只在打包后暴露。

        历史教训：曾把「默认按钮」当作第 5 个位置参数传入（该位置实为 parent），
        源码运行与 mock 测试都不报错，打包后的 exe 启动即崩溃。
        """
        from PySide6.QtWidgets import QMessageBox
        box = QMessageBox(QMessageBox.Icon.Question, "t", "m",
                          QMessageBox.StandardButton.Yes
                          | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.Yes)
        # defaultButton() 返回按钮控件，需与 Yes 对应的按钮比对
        self.assertEqual(box.defaultButton(),
                         box.button(QMessageBox.StandardButton.Yes))
        self.assertIsNone(box.parent())
        box.deleteLater()
        for icon in (QMessageBox.Icon.Warning, QMessageBox.Icon.Critical):
            b = QMessageBox(icon, "t", "m", QMessageBox.StandardButton.Ok)
            b.deleteLater()

    def test_close_event_is_wired_to_confirm_close(self):
        """HIGH 回归守护：关闭事件必须经过 confirm_close（部署中点 X 要确认）。

        迁移到 Qt 时曾只定义了 _on_close 却没接到窗口，部署中点 X 会直接
        退出并把 daemon 工作线程砍在半路。
        """
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QCloseEvent
        root = g._MainWindow()
        gui, _ = None, None
        with mock.patch.object(g, "_ask_yes_no", return_value=True), \
             mock.patch.object(g, "threading"):
            gui = g.DeployerGUI(root)
            timer = getattr(gui, "_timer", None)
            if timer is not None:
                timer.stop()
        self._roots.append(root)
        self.assertIs(root.gui, gui, "root.gui 必须回指 GUI 对象")

        # 空闲时直接放行
        gui.busy = False
        ev = QCloseEvent()
        root.closeEvent(ev)
        self.assertTrue(ev.isAccepted())
        self.assertTrue(gui.closing)

        # 忙碌且用户取消 -> 拒绝关闭，窗口保持
        gui.closing = False
        gui.busy = True
        with mock.patch.object(g, "_ask_yes_no", return_value=False):
            ev2 = QCloseEvent()
            root.closeEvent(ev2)
        self.assertFalse(ev2.isAccepted())
        self.assertFalse(gui.closing)
        gui.busy = False
        root.close()

    def test_confirm_close_stops_timer(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.root = mock.Mock()
        gui.busy = False
        gui.closing = False
        gui._timer = mock.Mock()
        self.assertTrue(gui.confirm_close())
        gui._timer.stop.assert_called_once()

    def test_done_ui_clears_state_after_uninstall(self):
        gui, root = self._build()
        gui.busy = True                       # 真实流程中部署/卸载期间 busy 为真
        gui._set_tool_state(1, True)
        gui._cards[1].set_installed(True)
        gui._progress_ui(100)
        self.assertFalse(gui._buttons[2].isEnabled())   # 忙碌时按钮禁用
        gui._status_ui("卸载完成")
        gui._done_ui()
        # 卸载完成后不得显示"部署完成"，且要清除已安装标记/勾选/进度
        self.assertEqual(gui.status.text(), "卸载完成")
        self.assertEqual(gui._cards[1].desc.text(), g.TOOLS[0]["desc"])
        self.assertFalse(gui.vars[1])
        self.assertEqual(gui.progress.value(), 0)
        self.assertTrue(gui._buttons[2].isEnabled())
        gui.closing = True
        root.close()

    def test_construction_builds_all_widgets(self):
        gui, root = self._build()
        self.assertEqual(len(gui._cards), len(g.TOOLS))
        self.assertEqual(len(gui._buttons), 5)
        self.assertIsNotNone(gui.log)
        self.assertIsNotNone(gui.status)
        self.assertIsNotNone(gui.progress)
        self.assertTrue(gui.log.isReadOnly())
        self.assertEqual(gui.status.text(), "就绪")
        self.assertEqual(gui.progress.value(), 0)
        self.assertEqual([b.text() for b in gui._buttons],
                         ["全选", "清空", "开始部署", "卸载工具", "打开工具目录"])
        self.assertEqual(gui._buttons[2].objectName(), "primary")
        gui.closing = True
        root.close()

    def test_card_toggle_updates_state(self):
        gui, root = self._build()
        card = gui._cards[3]
        self.assertFalse(card.is_checked())
        card.set_checked(True)
        self.assertTrue(gui.vars[3])
        self.assertEqual(card.property("state"), "on")
        card.set_checked(False)
        self.assertFalse(gui.vars[3])
        self.assertEqual(card.property("state"), "off")
        gui.closing = True
        root.close()

    def test_card_click_toggles_checkbox(self):
        """点击卡片空白处（按下+释放）应切换勾选。"""
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent
        gui, root = self._build()
        card = gui._cards[2]
        before = card.is_checked()
        pos = QPointF(card.width() / 2.0, card.height() / 2.0)
        card.mousePressEvent(QMouseEvent(
            QEvent.Type.MouseButtonPress, pos, pos,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier))
        card.mouseReleaseEvent(QMouseEvent(
            QEvent.Type.MouseButtonRelease, pos, pos,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier))
        self.assertNotEqual(card.is_checked(), before)
        self.assertTrue(gui.vars[2])
        gui.closing = True
        root.close()

    def test_card_drag_out_does_not_toggle(self):
        """按下后拖出卡片再释放，不应切换（避免滚动列表时误勾选）。"""
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent
        gui, root = self._build()
        card = gui._cards[4]
        before = card.is_checked()
        inside = QPointF(4.0, 4.0)
        outside = QPointF(card.width() + 60.0, card.height() + 60.0)
        card.mousePressEvent(QMouseEvent(
            QEvent.Type.MouseButtonPress, inside, inside,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier))
        card.mouseReleaseEvent(QMouseEvent(
            QEvent.Type.MouseButtonRelease, outside, outside,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier))
        self.assertEqual(card.is_checked(), before)
        gui.closing = True
        root.close()

    def test_select_all_and_clear_all(self):
        gui, root = self._build()
        gui.select_all()
        self.assertTrue(all(gui.vars.values()))
        self.assertEqual(len(gui.selected_tools()), len(g.TOOLS))
        gui.clear_all()
        self.assertFalse(any(gui.vars.values()))
        self.assertEqual([], gui.selected_tools())
        gui.closing = True
        root.close()

    def test_installed_marks_and_checks(self):
        gui, root = self._build()
        gui._installed_ui([1, 5])
        self.assertTrue(gui.vars[1] and gui.vars[5])
        self.assertEqual(gui._cards[1].desc.text(), "已安装")
        self.assertEqual(gui._cards[1].desc.property("installed"), "1")
        self.assertEqual(gui._cards[3].desc.text(), g.TOOLS[2]["desc"])
        self.assertIn("自动勾选", gui.status.text())
        gui.closing = True
        root.close()

    def test_progress_log_status_updates(self):
        gui, root = self._build()
        gui._progress_ui(42)
        self.assertEqual(gui.progress.value(), 42)
        self.assertEqual(gui._pct.text(), "42%")
        gui._status_ui("正在部署 Nmap")
        self.assertEqual(gui.status.text(), "正在部署 Nmap")
        gui._append_log_ui("第一行")
        gui._append_log_ui("第二行")
        txt = gui.log.toPlainText()
        self.assertIn("第一行", txt)
        self.assertIn("第二行", txt)
        self.assertTrue(txt.index("第一行") < txt.index("第二行"))
        gui.closing = True
        root.close()

    def test_done_resets_busy(self):
        gui, root = self._build()
        gui.busy = True
        gui._done_ui()
        self.assertFalse(gui.busy)
        self.assertEqual(gui.status.text(), "部署完成")
        gui.closing = True
        root.close()

    def test_queue_pump_updates_widgets(self):
        """append_log/set_status 经队列 -> QTimer 轮询 -> 控件刷新。"""
        gui, root = self._build()
        gui.append_log("来自队列的日志")
        gui.set_status("队列状态")
        gui._poll_queue()
        self.assertIn("来自队列的日志", gui.log.toPlainText())
        self.assertEqual(gui.status.text(), "队列状态")
        gui.closing = True
        root.close()

    def test_start_deploy_warns_when_nothing_selected(self):
        gui, root = self._build()
        with mock.patch.object(g, "_warn") as w:
            gui.start_deploy()
        w.assert_called_once()
        self.assertIn("请先选择", w.call_args[0][1])
        self.assertFalse(gui.busy)
        gui.closing = True
        root.close()

    def test_start_deploy_requires_admin(self):
        gui, root = self._build()
        gui.vars[1] = True
        with mock.patch.object(g, "is_admin", return_value=False), \
             mock.patch.object(g, "_err") as e:
            gui.start_deploy()
        e.assert_called_once()
        self.assertIn("管理员", e.call_args[0][1])
        gui.closing = True
        root.close()

    def test_start_deploy_requires_python_for_py_tools(self):
        gui, root = self._build()
        py_tool = next(t for t in g.TOOLS if t.get("py"))
        gui.vars[py_tool["id"]] = True
        with mock.patch.object(g, "is_admin", return_value=True), \
             mock.patch.object(g.DeployerGUI, "_check_python", return_value=False), \
             mock.patch.object(g, "_err") as e, \
             mock.patch.object(g, "threading") as th:
            gui.start_deploy()
        e.assert_called_once()
        self.assertIn("Python", e.call_args[0][1])
        th.Thread.assert_not_called()
        gui.closing = True
        root.close()

    def test_start_deploy_launches_thread(self):
        gui, root = self._build()
        gui.vars[1] = True
        with mock.patch.object(g, "is_admin", return_value=True), \
             mock.patch.object(g, "threading") as th:
            gui.start_deploy()
        self.assertTrue(gui.busy)
        th.Thread.assert_called_once()
        args = th.Thread.call_args[1]["args"][0]
        self.assertEqual([t["id"] for t in args], [1])
        gui.closing = True
        root.close()

    def test_start_uninstall_requires_admin(self):
        gui, root = self._build()
        with mock.patch.object(g, "is_admin", return_value=False), \
             mock.patch.object(g, "_err") as e:
            gui.start_uninstall()
        e.assert_called_once()
        gui.closing = True
        root.close()

    def test_start_uninstall_confirm_declined(self):
        gui, root = self._build()
        with mock.patch.object(g, "is_admin", return_value=True), \
             mock.patch.object(g, "_ask_yes_no", return_value=False), \
             mock.patch.object(g, "threading") as th:
            gui.start_uninstall()
        th.Thread.assert_not_called()
        self.assertFalse(gui.busy)
        gui.closing = True
        root.close()

    def test_start_uninstall_confirmed(self):
        gui, root = self._build()
        with mock.patch.object(g, "is_admin", return_value=True), \
             mock.patch.object(g, "_ask_yes_no", return_value=True), \
             mock.patch.object(g, "threading") as th:
            gui.start_uninstall()
        self.assertTrue(gui.busy)
        th.Thread.assert_called_once()
        gui.closing = True
        root.close()

    def test_on_close_blocks_while_busy(self):
        # 用 Mock 作为 root，才能断言 close 是否被调用
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.root = mock.Mock()
        gui.busy = True
        gui.closing = False
        with mock.patch.object(g, "_ask_yes_no", return_value=False):
            gui._on_close()
        self.assertFalse(gui.closing)
        gui.root.close.assert_not_called()
        # 空闲时可直接关闭
        gui.busy = False
        gui._on_close()
        self.assertTrue(gui.closing)
        gui.root.close.assert_called_once()

    def test_decline_disclaimer_stops_startup(self):
        from PySide6.QtWidgets import QWidget
        root = QWidget()
        with mock.patch.object(g, "_ask_yes_no", return_value=False):
            gui = g.DeployerGUI(root)
        self.assertTrue(gui.closing)
        self.assertIsNone(getattr(gui, "_timer", None))

    def test_qss_applies_to_widgets(self):
        gui, root = self._build()
        gui.root.setStyleSheet(g.QSS)
        self.assertEqual(gui.root.styleSheet(), g.QSS)
        gui.closing = True
        root.close()

    def test_secondary_text_untouched_by_install(self):
        gui, root = self._build()
        tool = g.TOOLS[5]
        gui._installed_ui([tool["id"]])
        self.assertEqual(gui._cards[tool["id"]].desc.text(), "已安装")
        gui._installed_ui([])
        self.assertEqual(gui._cards[tool["id"]].desc.text(), "已安装")
        gui.closing = True
        root.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
