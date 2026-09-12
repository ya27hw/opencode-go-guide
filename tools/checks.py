"""Content contract for the site — shared by the CLI checker and the pytest suite.

`problems()` returns human-readable violations; an empty list means the source is sound.
Keeping one implementation stops `make verify-local` and the tests from drifting apart.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES = ("index.html", "go/index.html")
BASE = "https://ya27hw.github.io/opencode-go-guide"
REF_URL = "https://opencode.ai/go?ref=APMP0ZVD7S"
REF_FRAGMENT = "opencode.ai/go?ref="
TITLE_RANGE = (40, 65)
DESC_RANGE = (120, 165)

_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
_REFS = re.compile(r'(?:src|srcset|href)="([^"]+)"')
_PREFIX = "/opencode-go-guide/"  # root-absolute refs are relative to the Pages project root


def local_refs(html: str, page_dir: Path) -> list[tuple[str, Path]]:
    """Local asset/style references in a page, resolved to real paths.

    On a GitHub Pages *project* site a leading slash means the repo root, not the filesystem
    root, so `/opencode-go-guide/css/x.css` must map inside the repo. References we cannot map
    (other absolute paths) are skipped rather than reported as broken.
    """
    out = []
    for raw in _REFS.findall(html):
        if raw.startswith(("http", "#", "mailto:", "data:", "//")):
            continue
        for candidate in raw.split(","):  # srcset may list several
            path = candidate.strip().split(" ")[0]
            if not path:
                continue
            if path.startswith("/"):
                if not path.startswith(_PREFIX):
                    continue
                resolved = (REPO / path[len(_PREFIX):]).resolve()
            else:
                resolved = (page_dir / path).resolve()
            out.append((path, resolved))
    return out


def _page_problems(page: str, want_ref_url: bool = True) -> list[str]:
    path = REPO / page
    if not path.exists():
        return [f"{page}: missing"]
    html = path.read_text(encoding="utf-8")
    bad: list[str] = []

    def want(cond: bool, msg: str) -> None:
        if not cond:
            bad.append(f"{page}: {msg}")

    want("YOUR-USERNAME" not in html, "placeholder host present")
    want(REF_FRAGMENT in html, "referral link missing")
    if want_ref_url:
        want(REF_URL in html, "referral URL not intact")
    want("aggregateRating" not in html, "fabricated review markup present")
    want("not affiliated" in html, "non-affiliation not stated")
    want('rel="sponsored' in html, "referral link not marked rel=sponsored")
    want('rel="stylesheet"' in html, "shared stylesheet not linked")
    want(re.search(rf'rel="canonical" href="{re.escape(BASE)}', html) is not None,
         "canonical missing or wrong")

    t = re.search(r"<title>(.*?)</title>", html, re.S)
    title = t.group(1).strip() if t else ""
    want(TITLE_RANGE[0] <= len(title) <= TITLE_RANGE[1],
         f"title length {len(title)} outside {TITLE_RANGE}")

    d = re.search(r'<meta name="description" content="(.*?)"', html)
    desc = d.group(1) if d else ""
    want(DESC_RANGE[0] <= len(desc) <= DESC_RANGE[1],
         f"description length {len(desc)} outside {DESC_RANGE}")

    want(len(re.findall(r"<h1", html)) == 1, "not exactly one h1")
    want(all(re.search(r'alt="[^"]+"', tag) for tag in re.findall(r"<img\b[^>]*>", html)),
         "an <img> is missing alt text")

    for block in _LD.findall(html):
        try:
            json.loads(block)
        except ValueError as e:
            want(False, f"JSON-LD invalid ({e})")

    for ref, resolved in local_refs(html, path.parent):
        want(resolved.exists(), f"broken reference {ref!r} -> {resolved}")

    return bad


def _sitemap_problems() -> list[str]:
    path = REPO / "sitemap.xml"
    if not path.exists():
        return ["sitemap.xml: missing"]
    try:
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [e.text or "" for e in ET.parse(path).getroot().findall(".//s:loc", ns)]
    except ET.ParseError as e:
        return [f"sitemap.xml: not valid XML ({e})"]
    bad = []
    if len(locs) != 2:
        bad.append(f"sitemap.xml: expected 2 urls, found {len(locs)}")
    if any(not loc.startswith(BASE) for loc in locs):
        bad.append(f"sitemap.xml: url outside {BASE}")
    if f"{BASE}/go/" not in locs:
        bad.append("sitemap.xml: guide url missing")
    return bad


def problems() -> list[str]:
    """All contract violations across the site source."""
    bad: list[str] = []
    for page in PAGES:
        bad += _page_problems(page)
    bad += _sitemap_problems()

    home = (REPO / "index.html").read_text(encoding="utf-8")
    guide = (REPO / "go/index.html").read_text(encoding="utf-8")
    if "/opencode-go-guide/go/" not in home:
        bad.append("index.html: does not link to the guide (internal linking)")
    if "/opencode-go-guide/" not in guide:
        bad.append("go/index.html: does not link back home (internal linking)")
    if "FAQPage" not in guide:
        bad.append("go/index.html: FAQ structured data missing")
    for anchor in ('id="limits"', 'id="pricing"'):
        if anchor not in guide:
            bad.append(f"go/index.html: missing anchor {anchor}")
    return bad
