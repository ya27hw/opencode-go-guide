#!/usr/bin/env python3
"""Offline source checks for both pages — no network.

    python3 tools/check_local.py      (or: make verify-local)

Thin CLI over tools/checks.py, which the pytest suite also uses.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.checks import PAGES, problems  # noqa: E402


def main() -> int:
    for page in PAGES:
        print(f"  checking {page}")
    bad = problems()
    for label in bad:
        print(f"  FAIL {label}")
    print(f"\n{len(bad)} problem(s)")
    print("RESULT:", "PASS" if not bad else "FAIL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
