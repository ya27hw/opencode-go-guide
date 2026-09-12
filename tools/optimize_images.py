#!/usr/bin/env python3
"""Build the site's hero image: resize and emit WebP (primary) plus a leaner PNG fallback.

    python3 tools/optimize_images.py [--src PATH] [--max-width 1200]

The master original is deliberately kept OUTSIDE the deployed site (a 460 KB PNG that nothing
links to should not ship), so --src defaults to the sibling originals directory. Safe to re-run.
"""
import argparse
import os
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "assets"
DEFAULT_SRC = REPO.parent / "opencode-ref" / "originals" / "screenshot-original-1824x1488.png"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC),
                    help="master screenshot (kept outside the deployed site)")
    ap.add_argument("--max-width", type=int, default=1200,
                    help="displayed at ~493 CSS px, so 1200 covers 2x DPR")
    a = ap.parse_args()

    src = Path(a.src)
    if not src.exists():
        print(f"ERROR: source not found: {src}\n"
              f"Pass --src explicitly, or restore the original screenshot there.", flush=True)
        return 1

    before = src.stat().st_size
    im = Image.open(src)
    print(f"original: {im.width}x{im.height} {im.mode} {before / 1024:.0f} KB")

    if im.width > a.max_width:
        h = round(im.height * a.max_width / im.width)
        im = im.resize((a.max_width, h), getattr(getattr(Image, "Resampling", Image), "LANCZOS"))
        print(f"resized -> {im.width}x{im.height}")

    webp, png = ASSETS / "screenshot.webp", ASSETS / "screenshot-1200.png"
    im.save(webp, "WEBP", quality=86, method=6)
    im.convert("RGBA").save(png, "PNG", optimize=True)

    saved = before - webp.stat().st_size
    print(f"webp:     {webp.stat().st_size / 1024:.0f} KB")
    print(f"fallback: {png.stat().st_size / 1024:.0f} KB")
    print(f"\nmodern browsers get {before / 1024:.0f} KB -> {webp.stat().st_size / 1024:.0f} KB "
          f"({saved / 1024:.0f} KB saved, {100 * saved / before:.0f}% smaller)")
    print(f'img dimensions for HTML: width="{im.width}" height="{im.height}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
