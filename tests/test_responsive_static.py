"""Tests for responsive CSS static properties, link positions, and viewport meta tags."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_responsive_css_files_exist_and_within_limits():
    resp_css = ROOT / "frontend" / "css" / "responsive.css"
    rep_resp_css = ROOT / "frontend" / "css" / "report-responsive.css"

    assert resp_css.exists(), "frontend/css/responsive.css must exist"
    assert rep_resp_css.exists(), "frontend/css/report-responsive.css must exist"

    resp_lines = len(resp_css.read_text(encoding="utf-8").splitlines())
    rep_lines = len(rep_resp_css.read_text(encoding="utf-8").splitlines())

    assert resp_lines <= 300, f"responsive.css exceeds 300 lines ({resp_lines})"
    assert rep_lines <= 300, f"report-responsive.css exceeds 300 lines ({rep_lines})"


def test_html_link_tags_order():
    index_html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    report_html = (ROOT / "frontend" / "report.html").read_text(encoding="utf-8")

    # index.html: css/responsive.css must be the last <link rel="stylesheet">
    index_links = re.findall(r'<link\s+rel="stylesheet"\s+href="([^"]+)"', index_html)
    assert len(index_links) > 0
    assert index_links[-1] == "css/responsive.css", f"Last link in index.html is {index_links[-1]}"

    # report.html: css/report-responsive.css linked after css/khata.css
    report_links = re.findall(r'<link\s+rel="stylesheet"\s+href="([^"]+)"', report_html)
    assert "css/khata.css" in report_links
    assert "css/report-responsive.css" in report_links
    assert report_links.index("css/report-responsive.css") > report_links.index("css/khata.css")


def test_viewport_meta_tags():
    index_html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    report_html = (ROOT / "frontend" / "report.html").read_text(encoding="utf-8")

    meta_needle = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    assert meta_needle in index_html, "index.html missing standard viewport meta"
    assert meta_needle in report_html, "report.html missing standard viewport meta"


def test_responsive_css_required_rules():
    css = (ROOT / "frontend" / "css" / "responsive.css").read_text(encoding="utf-8")
    assert "(min-width: 600px)" in css
    assert "(min-width: 1000px)" in css
    assert "(min-width: 1000px) and (min-height: 800px)" in css
    assert "min-height: 44px" in css


def test_no_fixed_pixel_width_over_1800():
    css_dir = ROOT / "frontend" / "css"
    for css_file in css_dir.glob("*.css"):
        text = css_file.read_text(encoding="utf-8")
        matches = re.findall(r'(?:width|min-width)\s*:\s*(\d+)px', text)
        for w_val in matches:
            val = int(w_val)
            assert val <= 1800, f"{css_file.name} has fixed pixel width > 1800px: {val}px"
