"""Tests for the OpenCode Go guide site: source contract plus the tool scripts.

    python3 -m pytest -q        (or: make test)

Offline and deterministic. The deployed site is checked separately by `make verify`.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from tools.checks import PAGES, REPO, problems

TOOLS = REPO / "tools"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / script), *args],
                          capture_output=True, text=True, cwd=REPO)


def test_source_contract_is_satisfied():
    """The whole content contract: links, schema, meta lengths, assets, sitemap."""
    assert problems() == []


@pytest.mark.parametrize("page", PAGES)
def test_page_exists_and_has_content(page: str):
    body = (REPO / page).read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in body
    assert len(body) > 2000, f"{page} looks empty"


def test_sitemap_lists_both_pages():
    xml = (REPO / "sitemap.xml").read_text(encoding="utf-8")
    assert xml.count("<loc>") == 2
    assert "/go/" in xml


def test_check_local_cli_passes():
    r = _run("check_local.py")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout


def test_optimizer_builds_and_is_idempotent():
    """Rebuilding assets must not drift — otherwise every deploy looks dirty."""
    import hashlib

    def digest():
        names = ["assets/screenshot.webp", "assets/screenshot-1200.png", "og-image.png"]
        return [hashlib.sha256((REPO / n).read_bytes()).hexdigest() for n in names]

    first = digest()
    assert _run("optimize_images.py").returncode == 0
    assert _run("make_og_image.py").returncode == 0
    assert digest() == first, "assets changed on rebuild"


def test_optimizer_reports_a_missing_source_without_a_traceback():
    """The source lives outside the deployed site; moving it must not crash the build."""
    r = _run("optimize_images.py", "--src", "/tmp/hermes-verify-absent.png")
    assert r.returncode == 1
    assert "source not found" in r.stdout + r.stderr
    assert "Traceback" not in r.stderr


def test_og_image_has_social_card_dimensions():
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")
    with Image.open(REPO / "og-image.png") as im:
        assert im.size == (1200, 630), "social cards are cropped unless 1200x630"


def test_every_referenced_local_asset_exists():
    """Covered by the contract too, but asserted per page for a clearer failure."""
    from tools.checks import local_refs

    for page in PAGES:
        html = (REPO / page).read_text(encoding="utf-8")
        for ref, resolved in local_refs(html, (REPO / page).parent):
            assert resolved.exists(), f"{page} references missing {ref}"


def test_local_refs_maps_pages_paths_into_the_repo():
    """A Pages project site resolves '/opencode-go-guide/...' to the repo root, not '/'."""
    from tools.checks import local_refs

    refs = dict(local_refs(
        '<link href="/opencode-go-guide/css/style.css">'
        '<img src="assets/screenshot.webp">'
        '<link href="/somewhere/else.css">'
        '<a href="#anchor">',
        REPO))

    assert refs["/opencode-go-guide/css/style.css"] == REPO / "css" / "style.css"
    assert refs["assets/screenshot.webp"] == REPO / "assets" / "screenshot.webp"
    assert "/somewhere/else.css" not in refs, "unmappable refs must be skipped, not mangled"


def test_contract_detects_a_broken_reference(tmp_path, monkeypatch):
    """Non-vacuity guard: the contract must actually report a genuinely missing asset."""
    import tools.checks as checks

    (tmp_path / "go").mkdir()
    (tmp_path / "index.html").write_text(
        '<html><head><title>t</title></head><body><img src="assets/nope.webp"></body></html>',
        encoding="utf-8")
    (tmp_path / "go" / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "sitemap.xml").write_text("<urlset></urlset>", encoding="utf-8")

    monkeypatch.setattr(checks, "REPO", tmp_path)
    bad = checks.problems()
    assert any("assets/nope.webp" in b for b in bad), f"broken ref not detected: {bad}"
