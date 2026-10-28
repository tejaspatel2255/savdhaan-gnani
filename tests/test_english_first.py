"""English-first UI: English is the primary text, Hindi/Gujarati only secondary."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONT = ROOT / "frontend"
INDIC = re.compile(r"[\u0900-\u097F\u0A80-\u0AFF]")


def test_en_strings_contain_no_indic_script():
    text = (FRONT / "js" / "strings.js").read_text(encoding="utf-8")
    for key, en in re.findall(r'(\w+):\s*\{[^}]*?\ben:\s*"([^"]*)"', text):
        assert not INDIC.search(en), f"English text for {key} contains Indic script: {en}"


def test_index_and_report_primary_text_is_english():
    for name in ["index.html", "report.html"]:
        html = (FRONT / name).read_text(encoding="utf-8")
        for line in html.splitlines():
            if INDIC.search(line):
                assert (
                    "brand-hi" in line
                    or "t-loc" in line
                    or 'lang="hi"' in line
                    or 'lang="gu"' in line
                ), f"Indic text outside secondary element in {name}: {line.strip()}"


def test_gloss_covers_all_sample_transcripts():
    gloss_file = FRONT / "assets" / "gloss.json"
    assert gloss_file.exists(), "gloss.json must exist"
    gloss = json.loads(gloss_file.read_text(encoding="utf-8"))

    for sample_name in ["sample_run.jsonl", "sample_legit.jsonl"]:
        sample_path = FRONT / "assets" / sample_name
        assert sample_path.exists(), f"{sample_name} must exist"
        lines = [
            json.loads(line)
            for line in sample_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for event in lines:
            if event.get("type") == "transcript":
                text = event.get("text", "").strip()
                if text:
                    assert text in gloss, f"Missing gloss entry for transcript '{text}' in {sample_name}"
                    en_trans = gloss[text]
                    assert en_trans and not INDIC.search(en_trans), f"Gloss for '{text}' has missing/invalid English: {en_trans}"


def test_events_reaching_phone_or_tape_have_english():
    for sample_name in ["sample_run.jsonl", "sample_legit.jsonl"]:
        lines = [
            json.loads(line)
            for line in (FRONT / "assets" / sample_name).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for event in lines:
            ev_type = event.get("type")
            if ev_type == "family_alert":
                assert "message_en" in event, f"family_alert missing message_en in {sample_name}"
                assert not INDIC.search(event["message_en"])
            elif ev_type == "alert":
                reasons = event.get("reasons", [])
                for r in reasons:
                    assert "label_en" in r, f"Reason missing label_en in {sample_name}"
                    assert not INDIC.search(r["label_en"])


def test_readme_first_screen_is_english_first():
    readme_lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()[:40]
    for line in readme_lines:
        if INDIC.search(line):
            # Hindi allowed only in parenthetical secondary markup like (सावधान)
            assert "(" in line and ")" in line, f"Standalone Indic text in README first screen: {line}"


def test_i18n_helpers_exist():
    assert (FRONT / "js" / "i18n.js").exists()
    assert (FRONT / "css" / "i18n.css").exists()


def test_file_size_limits():
    for f in (FRONT / "js").glob("*.js"):
        assert len(f.read_text(encoding="utf-8").splitlines()) <= 200, f.name
    for f in (FRONT / "css").glob("*.css"):
        assert len(f.read_text(encoding="utf-8").splitlines()) <= 300, f.name
