# -*- coding: utf-8 -*-
"""检查仓库内所有下载 URL 的连通性（HEAD 请求，失败回退 GET）。

URL 来源：
  1. deploy_config.json 的 tools[].url 与 helper_files[].url（权威配置）
  2. SecTools_Deploy.bat 中硬编码的 https URL（GBK 编码）
  3. Kali-Tools-Deployer.ps1 中硬编码的 https URL

用法：
  python scripts/check_urls.py            # 检查全部 URL
  python scripts/check_urls.py --config   # 仅检查 deploy_config.json
  python scripts/check_urls.py --timeout 30 --json report.json

退出码：0 = 全部可用；1 = 存在失效 URL（CI 据此标红）。
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
# RFC3986 允许字符白名单，避免把 URL 后紧跟的中文/全角标点吞进 URL
URL_RE = re.compile(r"https://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def collect_urls(include_scripts=True):
    """返回 {url: [来源标签]}，去重但保留来源。"""
    found = {}

    def add(url, src):
        url = url.rstrip(",;")
        srcs = found.setdefault(url, [])
        if src not in srcs:  # 同文件内重复 URL 只记一次来源
            srcs.append(src)

    cfg_path = os.path.join(BASE, "deploy_config.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    for t in cfg.get("tools", []) or []:
        if isinstance(t, dict) and t.get("url"):
            add(t["url"], "json:id=%s(%s)" % (t.get("id"), t.get("name")))
    for h in cfg.get("helper_files", []) or []:
        if isinstance(h, dict) and h.get("url"):
            add(h["url"], "json:helper(%s)" % h.get("name"))

    if include_scripts:
        with open(os.path.join(BASE, "SecTools_Deploy.bat"),
                  encoding="gbk", newline="") as f:
            bat = f.read()
        for u in URL_RE.findall(bat):
            add(u, "bat")
        with open(os.path.join(BASE, "Kali-Tools-Deployer.ps1"),
                  encoding="utf-8-sig") as f:
            ps1 = f.read()
        for u in URL_RE.findall(ps1):
            add(u, "ps1")
    return found


def check_one(url, timeout):
    """返回 (url, ok, detail)。HEAD 优先；失败回退 GET（Range 取首字节，
    服务器不支持 Range 返回 416 时再回退为不带 Range 的 GET 且不读 body）。"""
    ctx = ssl.create_default_context()

    def attempt(method, use_range):
        """返回 (code, err)。code=None 表示网络层失败。"""
        headers = {"User-Agent": UA}
        if use_range:
            headers["Range"] = "bytes=0-0"
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=ctx) as r:
                return r.getcode(), None
        except urllib.error.HTTPError as e:
            return e.code, e
        except Exception as e:  # 超时/SSL/DNS
            return None, e

    ok_codes = (200, 206, 301, 302, 303, 307, 308)

    code, err = attempt("HEAD", False)
    if code in ok_codes:
        return url, True, "HTTP %d (HEAD)" % code

    code, err = attempt("GET", True)
    if code == 416:  # 服务器不支持 Range，避免把可用链接误判为失效
        code, err = attempt("GET", False)
    if code in ok_codes:
        return url, True, "HTTP %d (GET)" % code
    if code is None:
        return url, False, "%s: %s" % (type(err).__name__, err)
    return url, False, "HTTP %d" % code


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check download URL health")
    ap.add_argument("--config", action="store_true",
                    help="only check URLs from deploy_config.json")
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--json", metavar="FILE", help="write JSON report")
    args = ap.parse_args(argv)

    urls = collect_urls(include_scripts=not args.config)
    print("checking %d unique URLs ..." % len(urls))

    results = []
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(check_one, u, args.timeout) for u in urls]
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    results.sort()
    bad = []
    for url, ok, detail in results:
        tag = ",".join(urls[url])
        mark = "OK  " if ok else "FAIL"
        print("%s %-70s %s  [%s]" % (mark, url[:70], detail, tag))
        if not ok:
            bad.append({"url": url, "detail": detail, "sources": urls[url]})

    print("\n%d/%d ok, %d failed" % (len(results) - len(bad),
                                     len(results), len(bad)))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"total": len(results), "failed": bad},
                      f, ensure_ascii=False, indent=2)
        print("report -> %s" % args.json)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
