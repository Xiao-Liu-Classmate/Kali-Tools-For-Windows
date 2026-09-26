# -*- coding: utf-8 -*-
"""scripts/check_versions.py 的离线单元测试（不发起真实网络请求）。"""
import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock as mock

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "scripts"))

import check_versions as cv  # noqa: E402


class TestExtractVersion(unittest.TestCase):

    def test_release_tag_from_url(self):
        self.assertEqual(
            cv.extract_version(
                "https://github.com/ffuf/ffuf/releases/download/"
                "v2.1.0/ffuf_2.1.0_windows_amd64.zip"),
            "v2.1.0")

    def test_filename_version_drops_extension_digits(self):
        # hashcat-6.2.6.7z -> 6.2.6（末段 .7 属扩展名）
        self.assertEqual(
            cv.extract_version("https://hashcat.net/files/hashcat-6.2.6.7z"),
            "6.2.6")

    def test_branch_zip_has_no_version(self):
        self.assertIsNone(cv.extract_version(
            "https://github.com/sqlmapproject/sqlmap/archive/refs/heads/"
            "master.zip"))

    def test_none_url(self):
        self.assertIsNone(cv.extract_version(None))

    def test_normalize_strips_prefix(self):
        self.assertEqual(cv._normalize("v3.3.8"), "3.3.8")
        self.assertEqual(cv._normalize("V3.3.8"), "3.3.8")
        self.assertEqual(cv._normalize("3.3.8"), "3.3.8")
        self.assertEqual(cv._normalize(None), "")

    def test_version_key_compares_numerically(self):
        self.assertLess(cv._version_key("3.3.8"), cv._version_key("3.11.1"))
        self.assertLess(cv._version_key("v2.6.7"), cv._version_key("2.16.0"))
        self.assertGreater(cv._version_key("7.1.2"), cv._version_key("6.2.6"))
        # 无数字段时不应抛 TypeError
        self.assertEqual(cv._version_key("nightly"), (0,))


class TestCollectTargets(unittest.TestCase):

    def test_only_version_pinned_github_tools(self):
        names = {n for n, _v, _r in cv.collect_targets()}
        self.assertNotIn("Sqlmap", names)   # 跟随 master
        self.assertNotIn("Xray", names)     # 无 URL
        self.assertNotIn("Nmap", names)     # nmap.org 非 GitHub release
        self.assertIn("Nuclei", names)
        self.assertIn("7zr.exe", names)     # helper 文件

    def test_all_mapped_sources_collected(self):
        # 映射表里每一项都应被收集到（防止误删映射）
        names = {n for n, _v, _r in cv.collect_targets()}
        self.assertEqual(names, set(cv.GITHUB_SOURCES))

    def test_every_target_has_version_and_repo(self):
        for name, ver, repo in cv.collect_targets():
            self.assertTrue(ver, "%s missing version" % name)
            self.assertIn("/", repo, "%s bad repo slug" % name)

    def test_sorted_and_deduped(self):
        targets = cv.collect_targets()
        names = [n for n, _v, _r in targets]
        self.assertEqual(names, sorted(names))
        self.assertEqual(len(names), len(set(names)))


class TestCheckOne(unittest.TestCase):

    def test_same_version_is_current(self):
        with mock.patch.object(cv, "fetch_latest", return_value=("v3.3.8", None)):
            name, cur, latest, err = cv.check_one("Nuclei", "v3.3.8",
                                                  "projectdiscovery/nuclei", 5)
        self.assertEqual((name, cur, latest), ("Nuclei", "v3.3.8", "3.3.8"))
        self.assertIsNone(err)

    def test_newer_upstream_reported(self):
        with mock.patch.object(cv, "fetch_latest", return_value=("v9.9.9", None)):
            _n, _c, latest, err = cv.check_one("Nuclei", "v3.3.8",
                                               "projectdiscovery/nuclei", 5)
        self.assertEqual(latest, "9.9.9")
        self.assertIsNone(err)

    def test_error_surfaced_as_none_latest(self):
        with mock.patch.object(cv, "fetch_latest", return_value=(None, "HTTP 403")):
            _n, _c, latest, err = cv.check_one("Nuclei", "v3.3.8",
                                               "projectdiscovery/nuclei", 5)
        self.assertIsNone(latest)
        self.assertEqual(err, "HTTP 403")


class TestFetchLatest(unittest.TestCase):

    class _Resp(object):
        def __init__(self, payload):
            self.payload = payload

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def test_token_header_injected(self):
        captured = {}

        def fake_urlopen(req, timeout=None, context=None):
            captured["auth"] = req.get_header("Authorization")
            captured["ver"] = req.get_header("X-github-api-version")
            return self._Resp({"tag_name": "v1.0.0"})

        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t0k3n"}), \
             mock.patch.object(cv.urllib.request, "urlopen", fake_urlopen):
            tag, err = cv.fetch_latest("a/b", 5)
        self.assertEqual((tag, err), ("v1.0.0", None))
        self.assertEqual(captured["auth"], "Bearer t0k3n")
        self.assertTrue(captured["ver"])

    def test_no_token_header_when_unset(self):
        captured = {}

        def fake_urlopen(req, timeout=None, context=None):
            captured["auth"] = req.get_header("Authorization")
            return self._Resp({"tag_name": "v1.0.0"})

        env = dict(os.environ)
        env.pop("GITHUB_TOKEN", None)
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(cv.urllib.request, "urlopen", fake_urlopen):
            cv.fetch_latest("a/b", 5)
        self.assertIsNone(captured["auth"])

    def test_rate_limit_message(self):
        import urllib.error

        class _Hdrs(dict):
            def get(self, k, default=None):
                return dict.get(self, k, default)

        hdrs = _Hdrs({"X-RateLimit-Remaining": "0"})
        err = urllib.error.HTTPError("u", 403, "forbidden", hdrs, None)
        with mock.patch.object(cv.urllib.request, "urlopen",
                               mock.Mock(side_effect=err)):
            tag, reason = cv.fetch_latest("a/b", 5)
        self.assertIsNone(tag)
        self.assertIn("速率限制", reason)

    def test_403_without_rate_limit_header_is_plain(self):
        import urllib.error

        class _Hdrs(dict):
            def get(self, k, default=None):
                return dict.get(self, k, default)

        err = urllib.error.HTTPError("u", 403, "forbidden", _Hdrs(), None)
        with mock.patch.object(cv.urllib.request, "urlopen",
                               mock.Mock(side_effect=err)):
            _tag, reason = cv.fetch_latest("a/b", 5)
        self.assertEqual(reason, "HTTP 403")

    def test_plain_http_error(self):
        import urllib.error

        err = urllib.error.HTTPError("u", 404, "not found", {}, None)
        with mock.patch.object(cv.urllib.request, "urlopen",
                               mock.Mock(side_effect=err)):
            tag, reason = cv.fetch_latest("a/b", 5)
        self.assertIsNone(tag)
        self.assertEqual(reason, "HTTP 404")


class TestMain(unittest.TestCase):

    TARGETS = [("FFUF", "v2.1.0", "f/f"), ("Nuclei", "v3.3.8", "p/d")]

    def _run(self, latest_map, extra_args=(), targets=None):
        """latest_map: {repo: (tag, err)}，按 repo 判定，与并发顺序无关。"""
        def side_effect(repo, timeout):
            return latest_map[repo]
        argv = ["--timeout", "1"] + list(extra_args)
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            with mock.patch.object(cv, "collect_targets",
                                   return_value=list(targets or self.TARGETS)), \
                 mock.patch.object(cv, "fetch_latest", side_effect=side_effect):
                code = cv.main(argv)
        finally:
            sys.stdout = old
        return code, buf.getvalue()

    def test_exit_zero_when_up_to_date(self):
        code, out = self._run({"f/f": ("v2.1.0", None), "p/d": ("v3.3.8", None)})
        self.assertEqual(code, 0)
        self.assertIn("0 个有新版本", out)
        self.assertIn("OK", out)

    def test_exit_one_with_fail_on_update(self):
        code, out = self._run({"f/f": ("v2.1.0", None), "p/d": ("v9.9.9", None)},
                              ["--fail-on-update"])
        self.assertEqual(code, 1)
        self.assertIn("1 个有新版本", out)
        self.assertIn("NEW", out)

    def test_exit_zero_on_update_without_strict_flag(self):
        code, _out = self._run({"f/f": ("v2.1.0", None),
                                "p/d": ("v9.9.9", None)})
        self.assertEqual(code, 0)

    def test_exit_two_when_all_checks_fail(self):
        code, out = self._run({"f/f": (None, "HTTP 403"),
                               "p/d": (None, "timeout")})
        self.assertEqual(code, 2)
        self.assertIn("2 个需人工确认", out)
        self.assertIn("GITHUB_TOKEN", out)

    def test_partial_failure_is_not_exit_two(self):
        code, _out = self._run({"f/f": ("v2.1.0", None),
                                "p/d": (None, "HTTP 403")})
        self.assertEqual(code, 0)

    def test_config_newer_than_upstream_marked_diff(self):
        # 配置 pin 到 nightly（高于上游 latest）不应误报"有新版本"
        code, out = self._run({"f/f": ("v2.1.0", None), "p/d": ("v1.0.0", None)},
                              ["--fail-on-update"])
        self.assertEqual(code, 0)
        self.assertIn("DIFF", out)
        self.assertIn("请人工确认", out)

    def test_json_report_written(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "sub", "report.json")
        code, _out = self._run({"f/f": ("v2.1.0", None),
                                "p/d": ("v9.9.9", None)}, ["--json", path])
        self.assertEqual(code, 0)
        with open(path, encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["total"], 2)
        self.assertEqual(report["outdated"][0]["tool"], "Nuclei")
        self.assertEqual(report["outdated"][0]["repo"], "p/d")

    def test_json_write_failure_returns_two(self):
        # 目录路径作为 --json 目标 -> 写文件失败 -> 退出码 2
        code, out = self._run({"f/f": ("v2.1.0", None),
                               "p/d": ("v3.3.8", None)},
                              ["--json", os.path.dirname(__file__)])
        self.assertEqual(code, 2)
        self.assertIn("write report failed", out)

    def test_invalid_args_rejected(self):
        # argparse 的报错走 stderr，需一并吞掉避免污染测试输出
        for bad in (["--timeout", "0"], ["--workers", "-1"],
                    ["--workers", "abc"]):
            buf_out, buf_err = io.StringIO(), io.StringIO()
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = buf_out, buf_err
            try:
                with self.assertRaises(SystemExit):
                    cv.main(bad)
            finally:
                sys.stdout, sys.stderr = old_out, old_err
            self.assertIn("usage", buf_err.getvalue())

    def test_no_targets_returns_zero(self):
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            with mock.patch.object(cv, "collect_targets", return_value=[]):
                code = cv.main([])
        finally:
            sys.stdout = old
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
