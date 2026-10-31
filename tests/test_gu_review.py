import csv
from pathlib import Path
from scripts.apply_gu_review import apply_review, load_reviewed_csv, update_strings_content


def test_load_reviewed_csv(tmp_path: Path):
    csv_file = tmp_path / "review.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "english", "gujarati_current", "gujarati_fixed", "notes"])
        writer.writerow(["strings.app_title", "SAVDHAAN", "સાવધાન", "સાવધાન!", "added exclamation"])
        writer.writerow(["rule.R01.label_gu", "Police", "પોલીસ", "પોલીસ અધિકારી", "more formal"])
        writer.writerow(["strings.no_change", "Hello", "હેલો", "", "no change"])

    s_fixes, r_fixes = load_reviewed_csv(csv_file)
    assert len(s_fixes) == 1
    assert s_fixes["app_title"] == "સાવધાન!"
    assert len(r_fixes) == 1
    assert r_fixes[0]["key"] == "rule.R01.label_gu"


def test_update_strings_content_preserves_hi_and_en():
    original = """export const STRINGS = {
  app_title: { hi: "सावधान", en: "SAVDHAAN", gu: "સાવધાન" },
  start_call: { hi: "कॉल शुरू करें", en: "Start Call", gu: "કોલ શરૂ કરો" },
};
"""
    updated = update_strings_content(original, {"app_title": "સાવધાન!"})
    assert 'app_title: { hi: "सावधान", en: "SAVDHAAN", gu: "સાવધાન!" }' in updated
    assert 'start_call: { hi: "कॉल शुरू करें", en: "Start Call", gu: "કોલ શરૂ કરો" }' in updated


def test_apply_review_dry_run_and_go(tmp_path: Path):
    strings_file = tmp_path / "strings.js"
    fixes_doc = tmp_path / "rule_fixes.md"
    csv_file = tmp_path / "review.csv"

    strings_file.write_text(
        'export const STRINGS = {\n  test_key: { hi: "परीक्षण", en: "Test", gu: "જૂનું" },\n};\n',
        encoding="utf-8",
    )
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "english", "gujarati_current", "gujarati_fixed", "notes"])
        writer.writerow(["strings.test_key", "Test", "જૂનું", "નવું", "fixed typo"])
        writer.writerow(["rule.R02.label_gu", "Bank", "બેંક", "બેન્ક", "spelling"])

    # Dry run: files should not change
    apply_review(csv_file, go=False, strings_path=strings_file, fixes_doc=fixes_doc)
    assert "જૂનું" in strings_file.read_text(encoding="utf-8")
    assert not fixes_doc.exists()

    # Go run: strings updated and rule proposals written to markdown
    apply_review(csv_file, go=True, strings_path=strings_file, fixes_doc=fixes_doc)
    assert "નવું" in strings_file.read_text(encoding="utf-8")
    assert fixes_doc.exists()
    assert "બેન્ક" in fixes_doc.read_text(encoding="utf-8")
