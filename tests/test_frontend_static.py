"""Static validation tests for Phase 4 frontend assets, CSS constraints, and contrast."""

import re
from pathlib import Path
import pytest

FRONTEND_DIR = Path("frontend")


def test_required_files_exist():
    required_files = [
        FRONTEND_DIR / "index.html",
        FRONTEND_DIR / "css" / "tokens.css",
        FRONTEND_DIR / "css" / "base.css",
        FRONTEND_DIR / "css" / "header.css",
        FRONTEND_DIR / "css" / "eye.css",
        FRONTEND_DIR / "css" / "tape.css",
        FRONTEND_DIR / "css" / "why.css",
        FRONTEND_DIR / "css" / "awaaz.css",
        FRONTEND_DIR / "js" / "strings.js",
        FRONTEND_DIR / "js" / "app.js",
        FRONTEND_DIR / "js" / "eye.js",
        FRONTEND_DIR / "js" / "tape.js",
        FRONTEND_DIR / "js" / "why.js",
        FRONTEND_DIR / "js" / "waveform.js",
        FRONTEND_DIR / "js" / "devfeed.js",
        FRONTEND_DIR / "assets" / "sample_run.jsonl",
    ]
    for p in required_files:
        assert p.exists(), f"Missing required file: {p}"


def test_file_line_limits():
    css_files = list((FRONTEND_DIR / "css").glob("*.css"))
    for f in css_files:
        lines = f.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 300, f"CSS file {f.name} exceeds 300 lines ({len(lines)})"

    js_files = list((FRONTEND_DIR / "js").glob("*.js"))
    for f in js_files:
        lines = f.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 200, f"JS file {f.name} exceeds 200 lines ({len(lines)})"


def test_external_urls_restricted_to_google_fonts():
    url_pattern = re.compile(r'https?://[^\s"\'<>)]+')
    allowed_domains = {"fonts.googleapis.com", "fonts.gstatic.com"}

    all_files = list(FRONTEND_DIR.glob("**/*"))
    for f in all_files:
        if f.is_dir() or f.suffix in (".jsonl", ".png", ".jpg", ".wav"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for url in url_pattern.findall(text):
            # Exclude XML namespace URLs like http://www.w3.org/2000/svg
            if "www.w3.org" in url:
                continue
            assert any(allowed in url for allowed in allowed_domains), (
                f"Unauthorized external URL in {f}: {url}"
            )


def test_no_banned_css_effects():
    banned_keywords = [
        "backdrop-filter",
        "filter: blur",
        "filter:blur",
        "linear-gradient(",
        "radial-gradient(",
    ]
    css_files = list((FRONTEND_DIR / "css").glob("*.css"))
    for f in css_files:
        content = f.read_text(encoding="utf-8")
        for kw in banned_keywords:
            assert kw not in content, f"Banned effect '{kw}' found in {f.name}"


def test_tokens_defines_spec_tokens():
    tokens_text = (FRONTEND_DIR / "css" / "tokens.css").read_text(encoding="utf-8")
    required_tokens = [
        "--night",
        "--night-2",
        "--night-3",
        "--line",
        "--text",
        "--muted",
        "--paper",
        "--paper-2",
        "--ink",
        "--nazar-deep",
        "--nazar-white",
        "--nazar-light",
        "--pupil",
        "--calm",
        "--calm-text",
        "--careful",
        "--danger",
        "--danger-text",
        "--danger-deep",
        "--focus",
    ]
    for token in required_tokens:
        assert f"{token}:" in tokens_text, f"Token {token} not defined in tokens.css"


def test_index_html_structure():
    content = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    assert '<html lang="' in content
    assert "<main" in content
    assert 'id="live-polite"' in content
    assert 'aria-live="polite"' in content
    assert 'id="live-assertive"' in content
    assert 'aria-live="assertive"' in content
    assert 'data-level="calm"' in content

    # All scripts must be type="module"
    script_tags = re.findall(r"<script\b[^>]*>", content)
    assert len(script_tags) > 0
    for tag in script_tags:
        assert 'type="module"' in tag, f"Script tag missing type='module': {tag}"


def test_strings_have_hi_and_en():
    strings_text = (FRONTEND_DIR / "js" / "strings.js").read_text(encoding="utf-8")
    # Parse key blocks inside STRINGS
    keys = re.findall(r"(\w+):\s*\{\s*hi:\s*\"([^\"]+)\",\s*en:\s*\"([^\"]+)\"", strings_text)
    assert len(keys) >= 15, "Expected at least 15 localized string entries"
    for k, hi, en in keys:
        assert hi.strip(), f"Empty hi string for key {k}"
        assert en.strip(), f"Empty en string for key {k}"


def _luminance(hex_str: str) -> float:
    hex_str = hex_str.strip().lstrip("#")
    rgb = [int(hex_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    rgb = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _contrast_ratio(c1: str, c2: str) -> float:
    l1, l2 = _luminance(c1), _luminance(c2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def test_contrast_ratios_from_tokens():
    tokens_text = (FRONTEND_DIR / "css" / "tokens.css").read_text(encoding="utf-8")
    color_map = {}
    for match in re.finditer(r"(--[\w-]+):\s*(#[0-9a-fA-F]{6});", tokens_text):
        color_map[match.group(1)] = match.group(2)

    required_pairs = [
        ("--text", "--night", 4.5),
        ("--muted", "--night-2", 4.5),
        ("--ink", "--paper", 4.5),
        ("--ink", "--careful", 4.5),
        ("--danger-text", "--night-2", 4.5),
        ("--calm-text", "--night-2", 4.5),
        ("--careful", "--night-2", 4.5),
        ("--paper", "--danger-deep", 4.5),
        ("--danger", "--night", 3.0),
    ]

    for fg_token, bg_token, min_ratio in required_pairs:
        assert fg_token in color_map, f"Token {fg_token} not found"
        assert bg_token in color_map, f"Token {bg_token} not found"
        ratio = _contrast_ratio(color_map[fg_token], color_map[bg_token])
        assert ratio >= min_ratio, (
            f"Contrast {fg_token} ({color_map[fg_token]}) on {bg_token} ({color_map[bg_token]}) "
            f"is {ratio:.2f}, expected >= {min_ratio}"
        )
