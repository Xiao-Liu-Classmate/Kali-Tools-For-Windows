# -*- coding: utf-8 -*-
"""检查 deploy_config.json 中固定版本的工具是否落后于上游最新 release。

只覆盖"URL 里带明确版本号"且上游是 GitHub Releases 的工具；
跟随 master / bleeding-jumbo 分支的源码类工具天然是最新版，无需检查。

用法：
  python scripts/check_versions.py                  # 报告上游版本差异
  python scripts/check_versions.py --fail-on-update  # 有新版时退出码 1（CI 提醒用）
  python scripts/check_versions.py --json out.json

环境变量：
  GITHUB_TOKEN   可选，提高 GitHub API 速率限制（60/h -> 5000/h）

退出码：0 = 无新版（或仅提示）；1 = --fail-on-update 且存在新版；
        2 = 全部检查失败（网络/鉴权问题）。
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import ssl
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com/repos/%s/releases/latest"
UA = "Kali-Tools-For-Windows version checker"

# 工具名/辅助文件名 -> 上游 GitHub 仓库（仅列可自动核对的）
GITHUB_SOURCES = {
    "Hashcat": "hashcat/hashcat",
    "FFUF": "ffuf/ffuf",
    "Gobuster": "OJ/gobuster",
    "Nuclei": "projectdiscovery/nuclei",
    "Subfinder": "projectdiscovery/subfinder",
    "Httpx": "projectdiscovery/httpx",
    "RustScan": "bee-san/RustScan",
    "Mimikatz": "gentilkiwi/mimikatz",
    "7zr.exe": "ip7z/7zip",
}

# 从 release 下载 URL 中提取版本：.../releases/download/<tag>/<asset>
TAG_RE = re.compile(r"/releases/download/([^/]+)/")
# 从文件名提取版本：hashcat-6.2.6.7z -> 6.2.6
# 末段数字可能是扩展名（.7z/.exe）的一部分，需回退一组
FILE_VER_RE = re.compile(r"(\d+(?:\.\d+)+)\.\w+$")
FILE_VER_RE_FALLBACK = re.compile(r"(\d+(?:\.\d+)+)")


def _normalize(v):
    """去掉版本号前缀 v / V，便于比较。"""
    return re.sub(r"^[vV]", "", (v or "").strip())


def _version_key(v):
    """把版本串拆成可比较的元组：数字段按 int 比较，非数字段（如日期后缀）
    退化为 0 以保证元组比较不抛 TypeError。用于判断上游是否真的更新。"""
    parts = re.findall(r"\d+", _normalize(v) or "")
    return tuple(int(p) for p in parts) or (0,)


def extract_version(url):
    """从下载 URL 推断配置的版本号；无法推断返回 None。

    优先取 release 下载路径中的 tag；无 tag（如 hashcat.net 直链）时
    退化为文件名中的数字版本，末段数字视为扩展名的一部分。
    """
    if not url:
        return None
    m = TAG_RE.search(url)
    if m:
        return m.group(1)
    fname = url.rsplit("/", 1)[-1]
    m = FILE_VER_RE.search(fname)          # hashcat-6.2.6.7z -> 6.2.6
    if m:
        return m.group(1)
    m = FILE_VER_RE_FALLBACK.search(fname)  # 兜底：不做末段回退
    return m.group(1) if m else None


def collect_targets():
    """返回 [(显示名, 配置版本, 上游仓库), ...]，跳过无法自动核对的项。

    按名称去重（tools 与 helper_files 理论上不会重名，但防御性处理可避免
    对同一仓库重复请求浪费 API 配额）。
    """
    with open(os.path.join(BASE, "deploy_config.json"), encoding="utf-8") as f:
        cfg = json.load(f)

    items = {}
    for t in cfg.get("tools", []) or []:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        repo = GITHUB_SOURCES.get(name)
        ver = extract_version(t.get("url"))
        if repo and ver:
            items[name] = (name, ver, repo)
    for h in cfg.get("helper_files", []) or []:
        if not isinstance(h, dict):
            continue
        name = h.get("name")
        repo = GITHUB_SOURCES.get(name)
        ver = extract_version(h.get("url"))
        if repo and ver and name not in items:
            items[name] = (name, ver, repo)
    return sorted(items.values(), key=lambda x: x[0])


def fetch_latest(repo, timeout):
    """返回 (tag, err)。tag=None 表示失败。"""
    ctx = ssl.create_default_context()
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer %s" % token
    req = urllib.request.Request(API % repo, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data.get("tag_name") or data.get("name") or None, None
    except urllib.error.HTTPError as e:
        if e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
            return None, ("HTTP %d 速率限制已用尽，请设置 GITHUB_TOKEN "
                           "或稍后重试" % e.code)
        return None, "HTTP %d" % e.code
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def check_one(name, current, repo, timeout):
    """返回 (name, current, latest, err)。err/latest 为 None 表示无法核对。"""
    latest, err = fetch_latest(repo, timeout)
    if err or not latest:
        return name, current, None, (err or "no tag")
    return name, current, _normalize(latest), None


def _positive_int(value):
    """argparse 校验：正整数。"""
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("需要整数：%s" % value)
    if n <= 0:
        raise argparse.ArgumentTypeError("需要正整数：%s" % value)
    return n


def main(argv=None):
    # 输出重定向到管道/文件时避免中文触发 UnicodeEncodeError
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Check pinned tool versions "
                                                 "against upstream releases")
    ap.add_argument("--timeout", type=_positive_int, default=20)
    ap.add_argument("--workers", type=_positive_int, default=6)
    ap.add_argument("--fail-on-update", action="store_true",
                    help="exit 1 when a newer upstream release exists")
    ap.add_argument("--json", metavar="FILE", help="write JSON report")
    args = ap.parse_args(argv)

    targets = collect_targets()
    if not targets:
        print("no version-pinned GitHub tools found")
        return 0
    print("checking %d version-pinned tools ..." % len(targets))

    results = []
    try:
        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            futures = [pool.submit(check_one, n, v, r, args.timeout)
                       for n, v, r in targets]
            for fut in concurrent.futures.as_completed(futures):
                results.append(fut.result())
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130
    results.sort(key=lambda r: r[0])  # 只按名字排，避免 None/str 异构比较

    repo_map = {n: r for n, _v, r in targets}
    outdated, unknown = [], []
    for name, current, latest, err in results:
        if err or not latest:
            mark, note = "SKIP", (err or "no tag")
            unknown.append({"tool": name, "current": current, "reason": note})
        elif _normalize(current) == latest:
            mark, note = "OK  ", "%s (最新)" % latest
        elif _version_key(latest) > _version_key(current):
            mark = "NEW "
            note = "配置 %s -> 上游 %s" % (current, latest)
            outdated.append({"tool": name, "current": current,
                             "latest": latest, "repo": repo_map.get(name)})
        else:
            # 配置版本不低于上游（pin 到 nightly / 上游回退等），需人工确认
            mark = "DIFF"
            note = "与上游不一致（配置 %s / 上游 %s），请人工确认" % (current, latest)
            unknown.append({"tool": name, "current": current,
                            "latest": latest, "reason": "version mismatch"})

        print("%s %-12s %s" % (mark, name, note))

    print("\n%d 个可核对，%d 个有新版本，%d 个需人工确认"
          % (len(results), len(outdated), len(unknown)))

    if args.json:
        report = {"total": len(results), "outdated": outdated,
                  "unchecked": unknown}
        try:
            parent = os.path.dirname(os.path.abspath(args.json))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print("write report failed: %s" % e)
            return 2
        print("report -> %s" % args.json)

    if unknown and len(unknown) == len(results):
        print("提示：全部无法核对通常是网络不可达或 GITHUB_TOKEN 失效，"
              "请检查后重试")
        return 2
    if outdated and args.fail_on_update:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
