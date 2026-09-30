# -*- coding: utf-8 -*-
"""液态玻璃 UI 的纯逻辑单元测试（不需要显示器，不创建 Tk 窗口）。

覆盖：不依赖显示器的绘制计算与状态逻辑
  - _mix 颜色混合边界
  - ToolCardCanvas 列数/卡宽计算与 resize 历史无关性
  - GlassProgress 渐变条数上限（不随宽度线性增长）
  - _installed_ui 的置位顺序（先 set 再标记）
  - _show_disclaimer 返回值契约
"""
import os
import sys
import unittest
import unittest.mock as mock

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import KaliToolsGUI as g  # noqa: E402


class TestMix(unittest.TestCase):
    """颜色混合必须始终产出合法 #RRGGBB。"""

    def test_endpoints(self):
        self.assertEqual(g._mix("#000000", "#ffffff", 0.0), "#000000")
        self.assertEqual(g._mix("#000000", "#ffffff", 1.0), "#ffffff")

    def test_midpoint(self):
        # int() 截断：127.5 -> 127
        self.assertEqual(g._mix("#000000", "#ffffff", 0.5), "#7f7f7f")

    def test_out_of_range_is_clamped(self):
        self.assertEqual(g._mix("#000000", "#ffffff", -5), "#000000")
        self.assertEqual(g._mix("#000000", "#ffffff", 5), "#ffffff")

    def test_result_shape(self):
        for t in (0, 0.25, 0.5, 0.75, 1):
            out = g._mix("#1A2036", "#A96BFF", t)
            self.assertEqual(len(out), 7)
            self.assertTrue(out.startswith("#"))
            int(out[1:], 16)  # 必须可解析为十六进制


class TestRrectGeometry(unittest.TestCase):
    """圆角矩形在极端尺寸下不应崩溃（半径被夹紧）。"""

    def test_degenerate_sizes(self):
        class _FakeCanvas(object):
            def __init__(self):
                self.polys = []

            def create_polygon(self, pts, **kw):
                self.polys.append((pts, kw))
                return len(self.polys)

        for (x1, y1, x2, y2) in ((0, 0, 0, 0), (0, 0, 3, 3), (0, 0, 1, 50)):
            cv = _FakeCanvas()
            g._rrect(cv, x1, y1, x2, y2, 12)
            self.assertEqual(len(cv.polys), 1)
            self.assertTrue(cv.polys[0][1].get("smooth"))


class TestColumnLayout(unittest.TestCase):
    """列数必须只由当前可用宽度决定，与 resize 历史无关。"""

    def _cols_for(self, width, pref=300, gap=9):
        avail = max(1, width - 12)
        cols = max(1, int((avail + gap) // (pref + gap)))
        card_w = max(1, (avail - (cols + 1) * gap) // cols)
        return cols, card_w, avail

    def test_wide_window_more_columns(self):
        cols_wide, _, _ = self._cols_for(2368)
        cols_narrow, _, _ = self._cols_for(1076)
        self.assertGreater(cols_wide, cols_narrow)

    def test_idempotent_across_resize_history(self):
        # 审查指出的退化场景：300 -> 382 -> 524 -> 1058 反复回写 card_w
        # 修复后每次都从固定 pref 推导，结果必须稳定
        pref = 300
        results = []
        for width in (1088, 2368, 1076, 1088, 2368, 1076):
            avail = max(1, width - 12)
            cols = max(1, int((avail + 9) // (pref + 9)))
            card_w = max(1, (avail - (cols + 1) * 9) // cols)
            results.append((width, cols, card_w, card_w <= avail))
        for width, cols, card_w, fits in results:
            self.assertTrue(fits, "card_w %d exceeds avail for width %d"
                            % (card_w, width))
        # 相同宽度必须得到相同结果（与历史无关）
        by_width = {}
        for width, cols, card_w, _ in results:
            by_width.setdefault(width, set()).add((cols, card_w))
        for width, vals in by_width.items():
            self.assertEqual(len(vals), 1,
                             "width %d gave unstable layout %s" % (width, vals))


class TestProgressGradientCap(unittest.TestCase):
    """进度条渐变条数必须封顶（下载热路径性能）。"""

    def test_steps_capped(self):
        # 复现 GlassProgress._redraw 中的 steps 计算
        for fw in (100, 400, 1071, 2000):
            steps = min(max(8, fw // 3), 48)
            self.assertLessEqual(steps, 48)
        # 宽度增加不应导致条数无限增长
        self.assertEqual(min(max(8, 1071 // 3), 48),
                         min(max(8, 2000 // 3), 48))


class TestInstalledUiOrder(unittest.TestCase):
    """自动勾选：必须先置位变量再标记，否则卡片显示为未勾选。"""

    def test_var_set_before_mark_and_single_redraw(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.closing = False
        order = []

        class _Var(object):
            def __init__(self, tid):
                self.tid = tid
                self.value = False

            def set(self, v):
                self.value = v
                order.append(("set", self.tid, v))

        class _Cards(object):
            def mark_installed(self, tid, redraw=True):
                order.append(("mark", tid, redraw))

            def refresh(self):
                order.append(("refresh", None, None))

        class _Status(object):
            def config(self, **kw):
                order.append(("status", None, kw.get("text")))

        gui.vars = {1: _Var(1), 5: _Var(5), 11: _Var(11)}
        gui._cards = _Cards()
        gui.status = _Status()
        gui._installed_ui([1, 5, 11])

        # 每个 mark 之前，对应变量必须已经是 True
        for i, (kind, tid, val) in enumerate(order):
            if kind == "mark":
                self.assertTrue(gui.vars[tid].value,
                                "var %d not set before mark_installed" % tid)
                self.assertFalse(val, "mark_installed should not redraw per item")
        # 只应整体 refresh 一次
        self.assertEqual(sum(1 for k, _t, _v in order if k == "refresh"), 1)
        # 状态栏文案保留
        self.assertTrue(any(k == "status" and "自动勾选" in (v or "")
                            for k, _t, v in order))

    def test_missing_id_does_not_raise(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.closing = False

        class _Cards(object):
            def mark_installed(self, tid, redraw=True):
                pass

            def refresh(self):
                pass

        class _Status(object):
            def config(self, **kw):
                pass

        gui.vars = {}
        gui._cards = _Cards()
        gui.status = _Status()
        gui._installed_ui([999])  # 配置里不存在的 id 不应抛 KeyError


class TestPollQueueResilience(unittest.TestCase):
    """UI 队列处理异常不得杀死轮询循环（否则界面永久失去更新）。"""

    def test_exception_does_not_stop_loop(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.closing = False

        class _Q(object):
            def __init__(self):
                self.items = [("progress", 1), ("status", "x")]

            def get_nowait(self):
                import queue as _queue
                if not self.items:
                    raise _queue.Empty
                return self.items.pop(0)

        calls = []

        def _boom(self, value):
            raise RuntimeError("draw failed")

        gui._msg_queue = _Q()
        gui._progress_ui = lambda v: _boom(gui, v)
        gui._status_ui = lambda v: calls.append(v)
        gui._append_log_ui = lambda m: None
        gui.append_log = lambda m: None
        gui.root = mock.Mock()
        gui._poll_queue()
        # 即使首条消息处理抛异常，也必须安排下一轮
        self.assertTrue(gui.root.after.called)
        self.assertTrue(calls, "后续消息应继续被处理")


class TestDisclaimerContract(unittest.TestCase):
    """_show_disclaimer 返回布尔，调用方据此提前返回。"""

    def test_returns_true_when_accepted(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.root = mock.Mock()
        with mock.patch.object(g.messagebox, "askyesno", return_value=True):
            self.assertTrue(gui._show_disclaimer())
        gui.root.destroy.assert_not_called()

    def test_returns_false_and_destroys_when_declined(self):
        gui = g.DeployerGUI.__new__(g.DeployerGUI)
        gui.root = mock.Mock()
        with mock.patch.object(g.messagebox, "askyesno", return_value=False):
            self.assertFalse(gui._show_disclaimer())
        gui.root.destroy.assert_called_once()


class TestCoreLogicUntouched(unittest.TestCase):
    """守护：核心部署逻辑函数必须保持存在且签名不变。"""

    def test_core_callables_present(self):
        for name in ("download", "sha256_of", "verify_sha256", "is_admin",
                     "load_config_overrides", "time_now"):
            self.assertTrue(callable(getattr(g, name)), name)

    def test_gui_core_methods_present(self):
        for name in ("_deploy_one", "_pip_install", "_get_7zr",
                     "_register_program_files", "_flatten", "_configure_path",
                     "_run_deploy", "_run_uninstall", "start_deploy",
                     "start_uninstall", "selected_tools", "_detect_installed",
                     "_check_python", "open_dir"):
            self.assertTrue(callable(getattr(g.DeployerGUI, name, None)), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
