import re
from pathlib import Path


def hex_to_rgb(hex_str: str):
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def relative_luminance(rgb):
    srgb = [x / 255.0 for x in rgb]
    lum = []
    for c in srgb:
        if c <= 0.03928:
            lum.append(c / 12.92)
        else:
            lum.append(((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lum[0] + 0.7152 * lum[1] + 0.0722 * lum[2]


def contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = relative_luminance(hex_to_rgb(hex1))
    l2 = relative_luminance(hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def test_theme_color_contrast_tokens():
    # Tokens defined in tokens.css
    night = "#070B18"
    night_2 = "#0D1326"
    text = "#FAF6ED"
    paper = "#F3E9D2"
    danger_deep = "#A82A14"
    muted = "#A4B3D6"

    # Text against backgrounds >= 4.5:1
    assert contrast_ratio(text, night) >= 4.5
    assert contrast_ratio(text, night_2) >= 4.5
    assert contrast_ratio(danger_deep, paper) >= 4.5
    assert contrast_ratio("#2B2116", paper) >= 4.5
    assert contrast_ratio(muted, night) >= 4.5


def test_reduced_motion_css_rules():
    base_css = Path("frontend/css/base.css").read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in base_css
    assert "animation-duration: 0.001s" in base_css
    assert "transition-duration: 0.001s" in base_css


def test_dialog_accessibility_roles():
    index_html = Path("frontend/index.html").read_text(encoding="utf-8")
    assert 'id="receipt-root"' in index_html
    assert 'role="dialog"' in index_html
    assert 'aria-modal="true"' in index_html
    assert 'id="live-notice-overlay"' in index_html


def test_how_it_works_diagram_exists_and_linked():
    svg_path = Path("docs/how_it_works.svg")
    assert svg_path.exists()
    svg_text = svg_path.read_text(encoding="utf-8")
    assert "Gnani Prisma v2.5" in svg_text
    assert "Gnani Timbre v3.0" in svg_text
    assert "Audio is sent to Gnani for transcription; Savdhaan does not save it" in svg_text

    readme_text = Path("README.md").read_text(encoding="utf-8")
    assert "docs/how_it_works.svg" in readme_text

    report_js = Path("frontend/js/report.js").read_text(encoding="utf-8")
    assert "docs/how_it_works.svg" in report_js
