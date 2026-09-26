# -*- coding: utf-8 -*-
"""scripts/check_urls.py 的离线单元测试（mock 网络层）。

覆盖：
  - collect_urls：JSON/BAT/PS1 三方收集、null 防御、来源去重
  - URL 正则：URL 后紧跟中文/全角标点不得吞入
  - check_one：HEAD 成功 / HEAD 败→GET 成功 / 416 回退 / 网络失败
  - main：退出码与 JSON 报告

运行：python -m unittest test_check_urls -v
"""
import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock as mock
import urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "scripts"))

import check_urls as cu  # noqa: E402


class _Resp(object):
    """urlopen 返回值替身。"""

    def __init__(self, code):
        self._code = code

    def getcode(self):
        return self._code

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestCollectUrls(unittest.TestCase):

    def test_config_only_has_21_tools_plus_helper(self):
        urls = cu.collect_urls(include_scripts=False)
        # 21 个工具中 Xray(id=10) 为手动下载无 URL -> 20 个 + helper 7zr
        self.assertGreaterEqual(len(urls), 21)
        json_srcs = [s for srcs in urls.values() for s in srcs]
        self.assertTrue(any(s.startswith("json:id=1(") for s in json_srcs))
        self.assertTrue(any(s.startswith("json:helper(") for s in json_srcs))

    def test_scripts_add_urls_deduped(self):
        all_urls = cu.collect_urls(include_scripts=True)
        cfg_urls = cu.collect_urls(include_scripts=False)
        # BAT/PS1 引入了 JSON 之外的 URL（如 git clone 源）
        self.assertGreater(len(all_urls), len(cfg_urls))
        for srcs in all_urls.values():
            self.assertEqual(len(srcs), len(set(srcs)),
                             "duplicate source labels: %s" % srcs)

    def test_null_tools_and_helper_do_not_crash(self):
        cfg = {"tools": None, "helper_files": None}
        with mock.patch.object(cu, "BASE", tempfile.mkdtemp()) as base, \
                mock.patch("builtins.open",
                           mock.mock_open(read_data=json.dumps(cfg))):
            found = cu.collect_urls(include_scripts=False)
        self.assertEqual(found, {})

    def test_regex_stops_at_chinese_and_fullwidth(self):
        text = "https://a.example/x.zip\uff0c\u4e0b\u8f7d\u5b8c\u6210 " \
               "https://b.example/y.zip\u3002ok"
        urls = cu.URL_RE.findall(text)
        self.assertEqual(urls, ["https://a.example/x.zip",
                                "https://b.example/y.zip"])

    def test_regex_stops_at_shell_code(self):
        # 回归：BAT/PS1 中 URL 后紧跟的引号与代码不得吞入（否则 404 假阳性）
        text = (
            "$u='https://a.example/x.zip';(New-Object Net.WebClient)"
            ".DownloadFile($u,$d)\r\n"
            "set \"URL=https://b.example/y.exe\"\r\n"
            "curl -o f https://c.example/z.7z & echo done"
        )
        urls = cu.URL_RE.findall(text)
        self.assertEqual(urls, ["https://a.example/x.zip",
                                "https://b.example/y.exe",
                                "https://c.example/z.7z"])

    def test_regex_keeps_hyphen_in_path(self):
        # 回归：'-' 是字符类范围语法，漏掉会导致 URL 在连字符处截断
        text = "https://nmap.org/dist/nmap-7.95-setup.exe end"
        self.assertEqual(cu.URL_RE.findall(text),
                         ["https://nmap.org/dist/nmap-7.95-setup.exe"])

    def test_regex_keeps_query_fragment(self):
        text = "https://c.example/dl?a=1&b=2#frag end"
        self.assertEqual(cu.URL_RE.findall(text),
                         ["https://c.example/dl?a=1&b=2#frag"])


class TestCheckOne(unittest.TestCase):

    URL = "https://example.com/tool.zip"

    def _run(self, side_effect):
        with mock.patch.object(cu.urllib.request, "urlopen",
                               side_effect=side_effect) as m:
            result = cu.check_one(self.URL, timeout=5)
        return result, m

    def test_head_ok(self):
        (url, ok, detail), m = self._run(lambda req, **kw: _Resp(200))
        self.assertTrue(ok)
        self.assertIn("HEAD", detail)
        self.assertEqual(m.call_count, 1)
        # HEAD 不得携带 Range 头
        first_req = m.call_args[0][0]
        self.assertNotIn("Range", first_req.header_items() and dict(
            first_req.header_items()) or {})

    def test_head_405_falls_back_to_get(self):
        def side_effect(req, **kw):
            if req.get_method() == "HEAD":
                raise urllib.error.HTTPError(
                    self.URL, 405, "Method Not Allowed", {}, io.BytesIO())
            return _Resp(200)
        (url, ok, detail), m = self._run(side_effect)
        self.assertTrue(ok)
        self.assertIn("GET", detail)
        self.assertEqual(m.call_count, 2)

    def test_416_falls_back_to_plain_get(self):
        calls = []

        def side_effect(req, **kw):
            calls.append(req)
            method = req.get_method()
            if method == "HEAD":
                raise urllib.error.HTTPError(
                    self.URL, 403, "Forbidden", {}, io.BytesIO())
            has_range = dict(req.header_items()).get("Range")
            if has_range:
                raise urllib.error.HTTPError(
                    self.URL, 416, "Range Not Satisfiable", {}, io.BytesIO())
            return _Resp(200)
        (url, ok, detail), _ = self._run(side_effect)
        self.assertTrue(ok)
        self.assertEqual(len(calls), 3)  # HEAD + GET(Range) + GET(plain)

    def test_all_network_errors_fail(self):
        def side_effect(req, **kw):
            raise TimeoutError("timed out")
        (url, ok, detail), _ = self._run(side_effect)
        self.assertFalse(ok)
        self.assertIn("TimeoutError", detail)

    def test_404_fail(self):
        def side_effect(req, **kw):
            raise urllib.error.HTTPError(
                self.URL, 404, "Not Found", {}, io.BytesIO())
        (url, ok, detail), _ = self._run(side_effect)
        self.assertFalse(ok)
        self.assertIn("HTTP 404", detail)


class TestMain(unittest.TestCase):

    def test_exit_code_and_report(self):
        urls = {"https://ok.example/a.zip": ["json:id=1(X)"],
                "https://bad.example/b.zip": ["bat"]}

        def fake_check(url, timeout):
            ok = url.startswith("https://ok")
            return url, ok, "HTTP 200" if ok else "HTTP 404"

        out = tempfile.mktemp(suffix=".json")
        try:
            with mock.patch.object(cu, "collect_urls",
                                   return_value=urls), \
                    mock.patch.object(cu, "check_one", side_effect=fake_check), \
                    mock.patch("sys.stdout", new=io.StringIO()):
                rc = cu.main(["--timeout", "1", "--json", out])
            self.assertEqual(rc, 1)  # 有失效 URL -> 1
            with open(out, encoding="utf-8") as f:
                report = json.load(f)
            self.assertEqual(report["total"], 2)
            self.assertEqual(len(report["failed"]), 1)
        finally:
            if os.path.exists(out):
                os.remove(out)

    def test_exit_zero_all_ok(self):
        def fake_check(url, timeout):
            return url, True, "HTTP 200"

        with mock.patch.object(cu, "collect_urls",
                               return_value={"https://a/x": ["bat"]}), \
                mock.patch.object(cu, "check_one", side_effect=fake_check), \
                mock.patch("sys.stdout", new=io.StringIO()):
            self.assertEqual(cu.main(["--config"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
