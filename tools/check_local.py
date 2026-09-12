#!/usr/bin/env python3
"""Offline source checks for the landing page and the guide page — no network.

    python3 tools/check_local.py      (or: make verify-local)

Covers both pages, plus the on-page SEO constraints we committed to: title/description lengths,
exactly one h1, alt text on images, valid JSON-LD, and no fabricated review markup.
"""
import json
import re
import sys

PAGES = ["index.html", "go/index.html"]
REF = "opencode.ai/go?ref="
fails: list[str] = []


def check(ok: bool, label: str) -> None:
    print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    if not ok:
        fails.append(label)


for page in PAGES:
    print(f"\n--- {page} ---")
    try:
        html = open(page, encoding="utf-8").read()
    except OSError as e:
        check(False, f"{page} readable ({e})")
        continue

    check("YOUR-USERNAME" not in html, "no placeholder host")
    check(REF in html, "referral link present")
    check("aggregateRating" not in html, "no fabricated review markup")
    check("not affiliated" in html, "non-affiliation stated")
    check("sponsored noopener" in html, "referral link marked rel=sponsored")
    check('rel="stylesheet"' in html, "uses the shared stylesheet")

    t = re.search(r"<title>(.*?)</title>", html, re.S)
    title = t.group(1).strip() if t else ""
    check(40 <= len(title) <= 65, f"title length {len(title)} (40-65)")
    d = re.search(r'<meta name="description" content="(.*?)"', html)
    desc = d.group(1) if d else ""
    check(120 <= len(desc) <= 165, f"description length {len(desc)} (120-165)")
    check(len(re.findall(r"<h1", html)) == 1, "exactly one h1")
    check(bool(re.search(r'rel="canonical" href="https://ya27hw\.github\.io/opencode-go-guide',
                         html)), "canonical present and correct")

    imgs = re.findall(r"<img\b[^>]*>", html)
    bad_alt = [i for i in imgs if not re.search(r'alt="[^"]+"', i)]
    check(not bad_alt, f"all {len(imgs)} img tag(s) have alt text")

    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(m.group(1))
            check(True, "JSON-LD parses")
        except Exception as e:
            check(False, f"JSON-LD parses ({e})")

    check("https://opencode.ai/go?ref=APMP0ZVD7S" in html, "referral URL intact")

print("\n--- cross-page ---")
home = open("index.html", encoding="utf-8").read()
guide = open("go/index.html", encoding="utf-8").read()
check('/opencode-go-guide/go/' in home, "home links to the guide (internal linking)")
check('/opencode-go-guide/' in guide, "guide links back home (internal linking)")
check("FAQPage" in guide, "guide has FAQ structured data")
check("id=\"limits\"" in guide and "id=\"pricing\"" in guide,
      "guide has anchor sections for deep links")

sm = open("sitemap.xml", encoding="utf-8").read()
check(sm.count("<loc>") == 2, "sitemap lists both pages")
check("/go/" in sm, "sitemap includes the guide URL")

print("\nRESULT:", "PASS" if not fails else f"FAIL -> {fails}")
sys.exit(1 if fails else 0)
