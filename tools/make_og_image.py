#!/usr/bin/env python3
"""Build the 1200x630 social preview card used by og:image / twitter:image.

    python3 tools/make_og_image.py

Social platforms crop or letterbox a tall screenshot, so the card pastes the hero onto a correctly
sized canvas in the site's own background colour. Safe to re-run (output is deterministic).
"""
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "assets"
OUT = REPO / "og-image.png"
BG = (33, 30, 30)  # matches --bg in css/style.css
W, H, PAD = 1200, 630, 60


def main() -> int:
    hero = ASSETS / "screenshot.webp"
    if not hero.exists():
        hero = ASSETS / "screenshot-1200.png"
    if not hero.exists():
        print(f"ERROR: no hero image in {ASSETS}; run tools/optimize_images.py first")
        return 1

    card = Image.new("RGB", (W, H), BG)
    shot = Image.open(hero).convert("RGBA")
    scale = min((W - PAD * 2) / shot.width, (H - PAD * 2) / shot.height)
    shot = shot.resize((round(shot.width * scale), round(shot.height * scale)),
                       getattr(getattr(Image, "Resampling", Image), "LANCZOS"))
    card.paste(shot, ((W - shot.width) // 2, (H - shot.height) // 2), shot)

    card.save(OUT, "PNG", optimize=True)
    print(f"{OUT.name}: {W}x{H} {OUT.stat().st_size / 1024:.0f} KB (aspect {W / H:.2f}:1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
