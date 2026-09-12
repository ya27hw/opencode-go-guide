#!/usr/bin/env python3
"""Offline sanity check on the source files — no network. Run before committing or deploying.

    python3 tools/check_local.py      (or: make verify-local)
"""
import json
import re
import sys

html = open("index.html", encoding="utf-8").read()

EXPECTATIONS = [
    ("no placeholder host in HTML", "YOUR-USERNAME" not in html),
    ("referral link present", "opencode.ai/go?ref=" in html),
    ("no fabricated aggregateRating", "aggregateRating" not in html),
    ("Go plan section present", 'id="go"' in html),
    ("real price stated", "$10/month" in html),
    ("non-affiliation stated", "not affiliated" in html),
]

bad = [label for label, ok in EXPECTATIONS if not ok]
for label, ok in EXPECTATIONS:
    print(f"  {'OK  ' if ok else 'FAIL'} {label}")

# JSON-LD must parse, and must not carry review markup we cannot source
m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
if not m:
    print("  FAIL no JSON-LD block found")
    bad.append("JSON-LD block missing")
else:
    try:
        data = json.loads(m.group(1))
        print(f"  OK   JSON-LD parses (keys: {', '.join(sorted(data))})")
    except Exception as e:
        print(f"  FAIL JSON-LD invalid: {e}")
        bad.append("JSON-LD invalid")

print("\nRESULT:", "PASS" if not bad else f"FAIL -> {bad}")
sys.exit(1 if bad else 0)
