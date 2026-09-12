#!/usr/bin/env python3
"""Verify the deployed OpenCode Go guide site (both pages).

    python3 tools/check_live_site.py [--base URL] [--wait SECONDS]

Checks the LIVE site, not the local files — the failure modes that matter (a placeholder host in
the served HTML, fabricated structured data, a broken og:image, a stylesheet that 404s because of
the project path) only appear once deployed.  Run after every edit + deploy:  make verify
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
    """Return (status_code, body). Bytes-safe: images are binary."""
    raw = subprocess.run(
        ["curl", "-sL", "-A", UA, "--max-time", "30", "-w", "\n__CODE__%{http_code}", url],
        capture_output=True,
    ).stdout
    text = raw.decode("utf-8", errors="ignore")
    m = re.search(r"__CODE__(\d+)$", text)
    return (m.group(1) if m else "000"), (text[: m.start()] if m else text)


def page(base: str, path: str, required: list[tuple[str, bool]],
         label: str) -> str:
    code, body = get(f"{base}{path}?cb={time.time()}")
    print(f"\n--- {label}: {base}{path} -> http={code} bytes={len(body)} ---")
    check(code == "200", f"{label} returns 200")
    check("YOUR-USERNAME" not in body, f"{label}: no placeholder host")
    check(body.count(REF) >= 1, f"{label}: referral link present")
    check("aggregateRating" not in body, f"{label}: no fabricated review markup")
    check("not affiliated" in body, f"{label}: non-affiliation stated")
    for needle, want in required:
        check((needle in body) == want, f"{label}: contains {needle!r}")
    t = re.search(r"<title>(.*?)</title>", body, re.S)
    print(f"    title: {(t.group(1).strip() if t else '')[:88]}")
    return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://ya27hw.github.io/opencode-go-guide")
    ap.add_argument("--wait", type=int, default=0,
                    help="seconds to poll for a 200 before checking (first build 404s briefly)")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    deadline = time.time() + args.wait
    while True:
        code, body = get(f"{base}/?cb={time.time()}")
        if code == "200" and "OpenCode" in body:
            break
        if time.time() >= deadline:
            break
        time.sleep(10)

    body = page(base, "/", [("$10/month", True), ('id="go"', True)], "home")
    page(base, "/go/", [('id="limits"', True), ('id="pricing"', True),
                        ('id="faq"', True), ("$10/month", True)], "guide")

    print("\n--- supporting files ---")
    for path, needle in [("/robots.txt", "Sitemap:"), ("/sitemap.xml", "<loc>"),
                         ("/css/style.css", ".wrap"), ("/css/guide.css", ".table-wrap"),
                         ("/og-image.png", None), ("/assets/screenshot.webp", None),
                         ("/.nojekyll", None)]:
        c, file_body = get(base + path)
        ok = c == "200" and (needle is None or needle in file_body)
        check(ok, f"{path} -> {c}")

    print("\n--- sitemap ---")
    _, sm = get(base + "/sitemap.xml")
    check("YOUR-USERNAME" not in sm, "no placeholder host in sitemap")
    check(sm.count("<loc>") == 2, "sitemap lists both pages")
    check(base + "/go/" in sm, "sitemap includes the guide")

    print("\n--- social preview ---")
    for prop in ["og:image", "og:url"]:
        m = re.search(rf'property="{prop}" content="([^"]+)"', body)
        if not m:
            check(False, f"{prop} tag present")
            continue
        if prop == "og:image":
            c, _ = get(m.group(1))
            check(c == "200", f"og:image resolves -> {c}")

    print("\n--- performance ---")
    c, webp = get(base + "/assets/screenshot.webp")
    check("image/webp" in webp, "hero is served as WebP")
    check(len(webp) < 150_000, f"hero under 150 KB ({len(webp)//1024} KB)")

    print("\nRESULT:", "PASS" if not fails else f"FAIL -> {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
