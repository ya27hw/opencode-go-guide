#!/usr/bin/env python3
"""Verify the deployed OpenCode Go guide landing page.

    python3 tools/check_live_site.py [--base URL] [--wait SECONDS]

Checks the LIVE site, not the local files — the failure modes that matter here (a placeholder
host left in the served HTML, a fabricated structured-data block, a broken og:image) only show
up once deployed. Exits non-zero on the first failed expectation set.

Run after every edit + deploy:  make verify
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time

REF = "opencode.ai/go?ref="
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"

fails: list[str] = []


def check(ok: bool, label: str) -> None:
    print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    if not ok:
        fails.append(label)


def get(url: str) -> tuple[str, str]:
    """Return (status_code, body). Bytes-safe: /assets/screenshot.png is a PNG."""
    raw = subprocess.run(
        ["curl", "-sL", "-A", UA, "--max-time", "30", "-w", "\n__CODE__%{http_code}", url],
        capture_output=True,
    ).stdout
    text = raw.decode("utf-8", errors="ignore")
    m = re.search(r"__CODE__(\d+)$", text)
    return (m.group(1) if m else "000"), (text[: m.start()] if m else text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://ya27hw.github.io/opencode-go-guide")
    ap.add_argument("--wait", type=int, default=0,
                    help="seconds to poll for a 200 before checking (first build 404s briefly)")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    code, body = "000", ""
    deadline = time.time() + args.wait
    while True:
        code, body = get(f"{base}/?cb={time.time()}")
        if code == "200" and "OpenCode" in body:
            break
        if time.time() >= deadline:
            break
        time.sleep(10)

    print(f"homepage: http={code} bytes={len(body)}")
    check(code == "200", "homepage returns 200")
    check("YOUR-USERNAME" not in body, "no placeholder host in the served HTML")
    check(body.count(REF) >= 2, f"referral link present ({body.count(REF)} occurrences)")
    check("aggregateRating" not in body, "no fabricated review markup served")
    check('id="go"' in body and 'href="#go"' in body, "Go plan section present and linked")
    check("$10/month" in body, "states the real $10/month price")
    check("not affiliated" in body, "non-affiliation stated")
    check(f'href="{base}/"' in body, "canonical points at the live URL")

    t = re.search(r"<title>(.*?)</title>", body, re.S)
    print(f"title: {(t.group(1).strip() if t else '')[:88]}")

    print("supporting files:")
    for path, needle in [("/robots.txt", "Sitemap:"), ("/sitemap.xml", "<loc>"),
                         ("/assets/screenshot.png", None), ("/.nojekyll", None)]:
        c, file_body = get(base + path)
        ok = c == "200" and (needle is None or needle in file_body)
        check(ok, f"{path} -> {c}")

    print("sitemap:")
    _, sm = get(base + "/sitemap.xml")
    check("YOUR-USERNAME" not in sm, "no placeholder host in sitemap")
    check(base in sm, "sitemap loc matches the live URL")

    print("social preview:")
    m = re.search(r'property="og:image" content="([^"]+)"', body)
    if m:
        c, _ = get(m.group(1))
        check(c == "200", f"og:image resolves -> {c}")
    else:
        check(False, "og:image tag present")

    print("\nRESULT:", "PASS" if not fails else f"FAIL -> {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
