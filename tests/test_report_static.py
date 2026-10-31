"""Static asset and security tests for the Khata report page."""

from pathlib import Path


def test_report_static_files_exist():
    assert Path("frontend/report.html").exists()
    assert Path("frontend/css/khata.css").exists()
    assert Path("frontend/js/report.js").exists()
    assert Path("frontend/assets/results.fixture.json").exists()


def test_report_js_security_and_dom_practices():
    js_content = Path("frontend/js/report.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js_content, "report.js must not use innerHTML; use textContent"
    assert "eval(" not in js_content, "report.js must not use eval()"
    assert "card" in js_content, "?card=1 handling must exist in report.js"
    assert "fixture" in js_content, "?fixture=1 handling must exist in report.js"


def test_report_sections_separates_real_and_ceiling():
    sec_content = Path("frontend/js/report-sections.js").read_text(encoding="utf-8")
    assert "Real Prisma speech recognition" in sec_content
    assert "Upper bound with perfect transcripts (not real speech recognition)" in sec_content
    assert "not measured yet" in sec_content
    assert "n = " in sec_content or "intervals are wide" in sec_content


def test_report_audit_what_changed_section():
    changed_content = Path("frontend/js/report-changed.js").read_text(encoding="utf-8")
    assert "What real speech recognition changed" in changed_content
    assert "Side-by-side transcript comparison" in changed_content

    audit_content = Path("frontend/js/report-audit.js").read_text(encoding="utf-8")
    assert "Word Error Rate (WER)" in audit_content
    assert "FIXTURE DATA - NOT MEASURED" in audit_content


def test_khata_css_text_color_safety():
    css_content = Path("frontend/css/khata.css").read_text(encoding="utf-8")
    # Verify that #E5391F is not used as a text color (small danger text should use --danger-deep)
    for line in css_content.splitlines():
        clean_line = line.strip().lower()
        if clean_line.startswith("color:") and "#e5391f" in clean_line:
            raise AssertionError(f"Forbidden #E5391F used as text color in line: {line}")
