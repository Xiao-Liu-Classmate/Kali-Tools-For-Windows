# -*- coding: utf-8 -*-
"""Kali-Tools-For-Windows 离线回归测试。

无需网络、无需管理员权限，覆盖：
  - GUI ↔ deploy_config.json 配置一致性（编号/名称/目录/URL/SHA256）
  - BAT 结构完整性（编号引用、工具名覆盖）
  - SHA256 校验机制（含真实语义）
  - deploy_config.json 覆盖加载的健壮性（结构异常不崩溃）
  - _get_7zr 下载校验流程（mock，五个分支）
  - BAT 结构完整性（编码、括号、标签、版本一致性）
  - PS1 语法解析（仅 Windows）
  - release.yml ↔ build_exe.bat 打包参数一致性（防漂移）

运行：python test_kalitools.py   （或 python -m unittest -v）
"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import KaliToolsGUI as g  # noqa: E402

ORIG_TOOLS = copy.deepcopy(g.TOOLS)
GBK = "gbk"


def read_text(name, encoding="utf-8"):
    # newline="" 保留原始行尾（BAT 必须是 CRLF，需按原样校验）
    with open(os.path.join(BASE, name), encoding=encoding, newline="") as f:
        return f.read()


class TestConsistency(unittest.TestCase):
    """GUI、deploy_config.json、BAT 三方编号/名称/目录/URL 必须一致。"""

    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(read_text("deploy_config.json"))
        cls.bat = read_text("SecTools_Deploy.bat", GBK)
        cls.gname = {t["id"]: t["name"] for t in g.TOOLS}
        cls.gdir = {t["id"]: t["dir"] for t in g.TOOLS}
        cls.gurl = {t["id"]: t["url"] for t in g.TOOLS}

    def test_gui_ids_continuous(self):
        self.assertEqual([t["id"] for t in g.TOOLS], list(range(1, 22)))

    def test_json_ids_continuous(self):
        self.assertEqual([t["id"] for t in self.cfg["tools"]], list(range(1, 22)))

    def test_name_matches_json(self):
        for jt in self.cfg["tools"]:
            self.assertEqual(self.gname[jt["id"]], jt["name"],
                             "id=%s name mismatch" % jt["id"])

    def test_dir_matches_json(self):
        for jt in self.cfg["tools"]:
            self.assertEqual(self.gdir[jt["id"]], jt["dir"],
                             "id=%s dir mismatch" % jt["id"])

    def test_url_matches_json_after_override(self):
        for jt in self.cfg["tools"]:
            expected = jt.get("url") or ""
            if expected.startswith("https://github.com/"):
                expected = g.GH_PROXY + expected
            self.assertEqual(self.gurl[jt["id"]], expected,
                             "id=%s url mismatch" % jt["id"])

    def test_bat_contains_all_tool_names(self):
        for t in g.TOOLS:
            self.assertIn(t["name"], self.bat, "BAT missing tool %s" % t["name"])

    def test_sha256_pinned_tools(self):
        pinned = sorted(t["id"] for t in g.TOOLS if t.get("sha256"))
        self.assertEqual(pinned, [5, 8, 11, 12, 15])
        for t in g.TOOLS:
            if t.get("sha256"):
                self.assertRegex(t["sha256"], r"^[0-9A-F]{64}$")

    def test_helper_hashes_loaded(self):
        self.assertGreaterEqual(len(g.HELPER_HASHES), 1)
        for url, h in g.HELPER_HASHES.items():
            self.assertTrue(url.startswith("https://"))
            self.assertRegex(h, r"^[0-9A-F]{64}$")


class TestSha256(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        os.write(fd, b"kali-tools-test-payload")
        os.close(fd)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_roundtrip(self):
        digest = g.sha256_of(self.path)
        self.assertTrue(g.verify_sha256(self.path, digest))
        self.assertTrue(g.verify_sha256(self.path, digest.lower()))

    def test_mismatch(self):
        self.assertFalse(g.verify_sha256(self.path, "0" * 64))

    def test_empty_expected_skips(self):
        self.assertTrue(g.verify_sha256(self.path, None))
        self.assertTrue(g.verify_sha256(self.path, ""))


class _FakeGUI(object):
    """仅提供 append_log 的 DeployerGUI 替身。"""

    def __init__(self):
        self.logs = []

    def append_log(self, msg):
        self.logs.append(str(msg))


class TestConfigOverride(unittest.TestCase):
    """load_config_overrides 的健壮性：任何结构异常都不得让 GUI 导入失败。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._tools = g.TOOLS
        self._hh = g.HELPER_HASHES
        g.TOOLS = copy.deepcopy(ORIG_TOOLS)
        g.HELPER_HASHES = dict(self._hh)  # 就地写入隔离，避免污染模块全局

    def tearDown(self):
        g.TOOLS = self._tools
        g.HELPER_HASHES = self._hh
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_cfg(self, data):
        if isinstance(data, str):
            with open(os.path.join(self.tmp, "deploy_config.json"), "w",
                      encoding="utf-8") as f:
                f.write(data)
        else:
            with open(os.path.join(self.tmp, "deploy_config.json"), "w",
                      encoding="utf-8") as f:
                json.dump(data, f)

    def _load(self):
        with mock.patch.object(g, "__file__",
                               os.path.join(self.tmp, "KaliToolsGUI.py")):
            return g.load_config_overrides()

    def test_malformed_json_returns_zero(self):
        self._write_cfg("{not json")
        self.assertEqual(self._load(), 0)

    def test_wrong_shape_returns_zero_without_raise(self):
        # tools 为 null / 元素非 dict / helper_files 为字符串 —— 均不得抛异常
        self._write_cfg({"tools": None, "helper_files": "oops"})
        self._load()
        self._write_cfg({"tools": ["bad", 42, None]})
        self._load()
        self._write_cfg({"tools": [{"id": "x"}, {"id": 5, "sha256": "AA"}],
                         "helper_files": [{"url": 1}]})
        self._load()

    def test_missing_file_returns_zero(self):
        self.assertEqual(self._load(), 0)

    def test_valid_override_applies(self):
        self._write_cfg({
            "tools": [{"id": 12, "url": "https://github.com/x/y.zip",
                       "dir": "nuclei", "sha256": "A" * 64}],
            "helper_files": [{"url": "https://h/f.exe", "sha256": "B" * 64}],
        })
        self.assertEqual(self._load(), 1)
        t12 = next(t for t in g.TOOLS if t["id"] == 12)
        self.assertTrue(t12["url"].startswith(g.GH_PROXY))
        self.assertEqual(t12["sha256"], "A" * 64)
        self.assertEqual(g.HELPER_HASHES["https://h/f.exe"], "B" * 64)

    def test_blank_url_does_not_wipe_builtin(self):
        builtin = next(t for t in g.TOOLS if t["id"] == 1)["url"]
        self._write_cfg({"tools": [{"id": 1, "url": "   "}]})
        self._load()
        self.assertEqual(next(t for t in g.TOOLS if t["id"] == 1)["url"],
                         builtin)


class TestGet7zr(unittest.TestCase):
    """_get_7zr 五分支：本地已存在 / 主源成功 / 主源败+备用成功 /
    备用校验失败（删除）/ 双源皆失败。"""

    GH_RAW = "https://github.com/ip7z/7zip/releases/download/24.09/7zr.exe"
    GOOD = "D2C0045523CF053A6B43F9315E9672FC2535F06AEADD4FFA53C729CD8B2B6DFE"

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fake = _FakeGUI()
        patcher_root = mock.patch.object(g, "TOOLS_ROOT", self.tmp)
        patcher_root.start()
        self.addCleanup(patcher_root.stop)
        self._orig_dl = g.download
        self._orig_hh = g.HELPER_HASHES
        g.HELPER_HASHES = dict(self._orig_hh)

    def tearDown(self):
        g.download = self._orig_dl
        g.HELPER_HASHES = self._orig_hh
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _call(self):
        return g.DeployerGUI._get_7zr(self.fake)

    def test_existing_file_returned_as_is(self):
        exe = os.path.join(self.tmp, "7zr.exe")
        with open(exe, "wb") as f:
            f.write(b"existing")
        self.assertEqual(self._call(), exe)

    def test_primary_success_no_hash_required(self):
        def dl(url, dest, progress=None):
            with open(dest, "wb") as f:
                f.write(b"primary")
            return dest
        g.download = dl
        exe = os.path.join(self.tmp, "7zr.exe")
        self.assertEqual(self._call(), exe)
        self.assertTrue(os.path.isfile(exe))

    def test_primary_fail_fallback_hash_ok(self):
        def dl(url, dest, progress=None):
            if "7-zip.org" in url:
                raise IOError("primary down")
            with open(dest, "wb") as f:
                f.write(b"fallback")
            return dest
        g.download = dl
        # 用与内容匹配的哈希
        import hashlib
        g.HELPER_HASHES = {self.GH_RAW: hashlib.sha256(b"fallback").hexdigest().upper()}
        exe = self._call()
        self.assertEqual(exe, os.path.join(self.tmp, "7zr.exe"))
        self.assertTrue(os.path.isfile(exe))

    def test_fallback_hash_mismatch_deleted(self):
        def dl(url, dest, progress=None):
            if "7-zip.org" in url:
                raise IOError("primary down")
            with open(dest, "wb") as f:
                f.write(b"tampered")
            return dest
        g.download = dl
        g.HELPER_HASHES = {self.GH_RAW: self.GOOD}
        self.assertIsNone(self._call())
        self.assertFalse(os.path.isfile(os.path.join(self.tmp, "7zr.exe")))

    def test_both_sources_fail(self):
        def dl(url, dest, progress=None):
            raise IOError("all down")
        g.download = dl
        self.assertIsNone(self._call())


class TestBatStructure(unittest.TestCase):
    """BAT 文件的编码与结构完整性（cmd 可解析性）。"""

    @classmethod
    def setUpClass(cls):
        cls.text = read_text("SecTools_Deploy.bat", GBK)
        cls.lines = cls.text.split("\r\n")

    def test_gbk_decodable_and_crlf(self):
        self.assertIn("\r\n", self.text)
        self.assertNotIn("\n", self.text.replace("\r\n", ""))  # 无混杂裸 LF

    def test_paren_balance(self):
        self.assertEqual(self.text.count("("), self.text.count(")"))

    def test_labels_defined_for_all_refs(self):
        labels = set(re.findall(r"(?m)^:(\w+)", self.text))
        refs = set(re.findall(r"(?m)(?:call|goto) :?(\w+)", self.text))
        missing = {r for r in refs if r != "eof" and r not in labels}
        self.assertFalse(missing, "missing labels: %s" % missing)

    def test_no_stale_nuclei(self):
        self.assertNotIn("3.3.7", self.text)
        self.assertIn("nuclei_3.3.8_windows_amd64.zip", self.text)

    def test_hashcat_subroutine_present(self):
        self.assertIn(":deploy_hashcat", self.text)
        self.assertIn("call :deploy_hashcat", self.text)

    def test_fullwidth_comma_replacement(self):
        self.assertIn("set \"INPUT=%INPUT:\uff0c=,%\"", self.text)

    def test_no_literal_question_runs(self):
        # GBK 中文被破坏成 ??? 的回归检测
        self.assertNotRegex(self.text, r"\?{4,}")

    def test_line_length_under_cmd_limit(self):
        # cmd.exe 的 8191 限制按字节（GBK 中文 1 字 = 2 字节）
        longest = max(len(x.encode(GBK, errors="replace")) for x in self.lines)
        self.assertLess(longest, 8191)


class TestPs1Syntax(unittest.TestCase):

    @unittest.skipUnless(sys.platform.startswith("win"), "needs Windows PowerShell")
    def test_parses_without_error(self):
        ps1 = os.path.join(BASE, "Kali-Tools-Deployer.ps1")
        script = (
            "$e=$null;[void][System.Management.Automation.Language.Parser]::ParseFile("
            "'%s',[ref]$null,[ref]$e);if($e.Count -gt 0){$e[0].Message;exit 1}else{exit 0}"
            % ps1.replace("'", "''"))
        r = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    @unittest.skipUnless(sys.platform.startswith("win"), "needs Windows PowerShell")
    def test_labeled_breaks_present(self):
        text = read_text("Kali-Tools-Deployer.ps1")
        self.assertIn(":mainLoop do {", text)
        self.assertIn("break :mainLoop", text)
        self.assertIn(":wslLoop do {", text)
        self.assertIn("break :wslLoop", text)


class TestReleaseBuildConsistency(unittest.TestCase):
    """release.yml 自动打包参数必须与 build_exe.bat 保持一致（防漂移）。

    两者各自演化会导致 CI 发布的 exe 与本地构建行为不一致，
    此测试按词级序列比对 PyInstaller 命令参数。
    """

    def _bat_pyinstaller_args(self):
        bat = read_text("build_exe.bat", encoding=GBK)
        # 提取逻辑按 CRLF 切行，先显式校验，避免行尾损坏时报错指向别处
        self.assertIn("\r\n", bat,
                      "build_exe.bat must keep CRLF line endings")
        self.assertNotIn("\n", bat.replace("\r\n", ""),
                         "build_exe.bat has bare-LF line endings")
        self.assertNotRegex(bat, r"\?{4,}",
                            "GBK chinese corrupted in build_exe.bat")
        marker = "python -m PyInstaller"
        start = bat.find(marker)
        self.assertNotEqual(start, -1,
                            "PyInstaller command not found in build_exe.bat")
        cmd_lines = []
        for line in bat[start:].split("\r\n"):
            cmd_lines.append(line.rstrip())
            if not cmd_lines[-1].endswith("^"):
                break
        else:
            self.fail("unterminated ^ continuation in build_exe.bat")
        flat = " ".join(l.rstrip("^").strip() for l in cmd_lines)
        return flat.split()

    def _yml_pyinstaller_args(self):
        yml = read_text(".github/workflows/release.yml")
        lines = yml.splitlines()
        for i, line in enumerate(lines):
            if line.strip() != "run: >-":
                continue
            # 块内容缩进 = run 行缩进 + 2，按实际排版推导而非硬编码
            run_indent = len(line) - len(line.lstrip())
            min_indent = run_indent + 2
            block = []
            for nxt in lines[i + 1:]:
                stripped = nxt.strip()
                indent = len(nxt) - len(nxt.lstrip())
                if stripped and indent < min_indent:
                    break
                if stripped:
                    block.append(stripped)
            if any("python -m PyInstaller" in l for l in block):
                return " ".join(block).split()
        self.fail("PyInstaller run block not found in release.yml")

    def test_pyinstaller_args_match(self):
        bat_args = self._bat_pyinstaller_args()
        yml_args = self._yml_pyinstaller_args()
        self.assertEqual(
            bat_args, yml_args,
            "PyInstaller args drifted between build_exe.bat "
            "and .github/workflows/release.yml")

    def test_pyinstaller_version_pinned_consistently(self):
        # 两侧都必须 pin 同一版本，否则 CI 发布与本地构建行为漂移
        bat = read_text("build_exe.bat", encoding=GBK)
        yml = read_text(".github/workflows/release.yml")
        pins = []
        for name, src in (("build_exe.bat", bat),
                          (".github/workflows/release.yml", yml)):
            m = re.search(r"pip install pyinstaller==([\w.]+)", src)
            self.assertIsNotNone(
                m, "%s must pin pyinstaller==x.y.z (supply-chain safety)" % name)
            pins.append(m.group(1))
        self.assertEqual(pins[0], pins[1],
                         "pyinstaller version pin drifted between "
                         "build_exe.bat and release.yml")
        # bat 的已装检查必须校验同一版本，否则装了旧版会跳过 pin 安装
        gate = re.search(r"PyInstaller\.__version__=='([\w.]+)'", bat)
        self.assertIsNotNone(
            gate, "build_exe.bat must gate install on exact pinned version")
        self.assertEqual(gate.group(1), pins[0],
                         "build_exe.bat version gate drifted from pin")


class TestCheckAllBat(unittest.TestCase):
    """check_all.bat：编码、cmd 可解析性与退出码语义。"""

    @classmethod
    def setUpClass(cls):
        cls.text = read_text("check_all.bat", GBK)
        cls.lines = cls.text.split("\r\n")

    def test_gbk_decodable_and_crlf(self):
        self.assertIn("\r\n", self.text)
        self.assertNotIn("\n", self.text.replace("\r\n", ""))

    def test_no_literal_question_runs(self):
        self.assertNotRegex(self.text, r"\?{4,}")

    def test_paren_balance(self):
        self.assertEqual(self.text.count("("), self.text.count(")"))

    def test_line_length_under_cmd_limit(self):
        longest = max(len(x.encode(GBK, errors="replace")) for x in self.lines)
        self.assertLess(longest, 8191)

    def test_label_summary_defined_and_referenced(self):
        labels = set(re.findall(r"(?m)^:(\w+)", self.text))
        refs = set(re.findall(r"(?m)goto :?(\w+)", self.text))
        missing = {r for r in refs if r not in labels}
        self.assertFalse(missing, "missing labels: %s" % missing)

    def test_offline_mode_skips_network_step(self):
        self.assertIn('if /i "%~1"=="offline" goto :summary', self.text)

    def test_exit_code_reflects_failure(self):
        # 失败标记必须在块外读取，退出码不能恒为 0
        self.assertIn('set "RC=1"', self.text)
        self.assertIn("exit /b %RC%", self.text)

    def test_setlocal_present(self):
        # 防止 FAILED 等变量泄漏到调用者环境
        self.assertRegex(self.text, r"(?m)^setlocal\b")

    def test_pause_only_without_args(self):
        # 双击运行时需停留查看结果，脚本化调用时不阻塞
        self.assertIn('if "%~1"=="" pause', self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
