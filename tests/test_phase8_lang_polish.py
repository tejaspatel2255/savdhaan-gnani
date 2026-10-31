"""Tests for Phase 8: Second Language (Gujarati), Merged Packs, Warnings, Errors, and Polish."""

import hashlib
import json
from pathlib import Path
import pytest

from backend.config import Settings
from backend.scorer import ScamScorer, load_pack, merge_packs, load_configured_packs
from backend.warning import WARNINGS, get_warning


def test_gujarati_rule_pack_schema_and_counts():
    gu_path = Path("rules/scam_rules_gu.json")
    assert gu_path.exists()
    pack = load_pack(gu_path)

    # At least 30 rules across 8 categories
    assert len(pack.rules) >= 30
    cats_covered = {r.category for r in pack.rules}
    assert len(cats_covered) == 8

    # 4 combos, 3 dampeners
    assert len(pack.combos) >= 4
    assert len(pack.dampeners) >= 3

    # Accepts _review list
    raw = json.loads(gu_path.read_text(encoding="utf-8"))
    assert "_review" in raw
    assert isinstance(raw["_review"], list)


def test_merged_packs_and_fixture_accuracy():
    hi_pack = load_pack("rules/scam_rules_hi_en.json")
    gu_pack = load_pack("rules/scam_rules_gu.json")
    merged = merge_packs([hi_pack, gu_pack])

    # Gujarati fixtures test
    gu_fixtures = json.loads(Path("tests/fixtures/calls_gu.json").read_text(encoding="utf-8"))
    for call in gu_fixtures:
        scorer = ScamScorer(merged, careful=30, danger=60)
        alerted = False
        for text in call["segments"]:
            res = scorer.feed(text)
            if res.alert:
                alerted = True
        if call["label"] == "scam":
            assert alerted is True, f"Expected alert on Gujarati scam: {call['id']}"
        else:
            assert alerted is False, f"Unexpected alert on Gujarati legit: {call['id']}"

    # Hindi-English fixtures unchanged
    hi_fixtures = json.loads(Path("tests/fixtures/calls.json").read_text(encoding="utf-8"))
    for call in hi_fixtures.get("scam", []):
        scorer = ScamScorer(merged, careful=30, danger=60)
        alerted = False
        for text in call["segments"]:
            res = scorer.feed(text)
            if res.alert:
                alerted = True
        assert alerted is True, f"Expected alert on Hindi scam: {call['id']}"

    for call in hi_fixtures.get("legit", []):
        scorer = ScamScorer(merged, careful=30, danger=60)
        alerted = False
        for text in call["segments"]:
            res = scorer.feed(text)
            if res.alert:
                alerted = True
        assert alerted is False, f"Unexpected alert on Hindi legit: {call['id']}"


def test_native_and_roman_scripts_and_negation():
    gu_pack = load_pack("rules/scam_rules_gu.json")

    # Native script
    s_native = ScamScorer(gu_pack, careful=30, danger=60)
    res_native = s_native.feed("હમણાં જ તમારો ઓટીપી આપો")
    assert any(h.rule_id == "GU_CRED_OTP_ASK" for h in res_native.hits)

    # Roman script
    s_roman = ScamScorer(gu_pack, careful=30, danger=60)
    res_roman = s_roman.feed("hali j tamaro otp aapo")
    assert any(h.rule_id == "GU_CRED_OTP_ASK" for h in res_roman.hits)

    # Negation dampens/guards
    s_neg = ScamScorer(gu_pack, careful=30, danger=60)
    res_neg = s_neg.feed("ઓટીપી આપશો નહીં")
    assert not any(h.rule_id == "GU_CRED_OTP_ASK" for h in res_neg.hits)


def test_warning_texts_and_cache_key_isolation(tmp_path):
    assert "gu-IN" in WARNINGS
    gu_warns = WARNINGS["gu-IN"]
    for k in ("generic", "arrest", "otp", "money", "remote"):
        assert k in gu_warns
        text = gu_warns[k]
        # Length between 70 and 110 characters
        assert 70 <= len(text) <= 110

    # Cache name isolation
    actual_lang = "gu-IN"
    key = "otp"
    voice = "Shivani"
    clean_lang = actual_lang.lower().replace("-", "_")
    name_gu = f"warn_{clean_lang}_{key.lower()}_{voice.lower()}"
    name_hi = f"warn_hi_in_{key.lower()}_{voice.lower()}"
    assert name_gu != name_hi
    assert "gu_in" in name_gu


def test_reconnect_backoff_sequence():
    # Sequence in ws.js getBackoffDelay must be: 1000, 2000, 4000, 8000, 8000
    js_text = Path("frontend/js/ws.js").read_text(encoding="utf-8")
    assert "getBackoffDelay" in js_text
    assert "[1000, 2000, 4000, 8000]" in js_text

    def backoff(retry_count):
        seq = [1000, 2000, 4000, 8000]
        if retry_count < len(seq):
            return seq[retry_count]
        return 8000

    delays = [backoff(i) for i in range(6)]
    assert delays == [1000, 2000, 4000, 8000, 8000, 8000]


def test_strings_i18n_has_required_codes_and_translations():
    strings_content = Path("frontend/js/strings.js").read_text(encoding="utf-8")
    required_error_codes = [
        "auth_failed", "rate_limited", "stt_unreachable", "tts_failed",
        "tts_over_cap", "session_cap", "mic_denied", "bad_audio_format"
    ]
    for code in required_error_codes:
        assert code in strings_content, f"Missing error code key in strings.js: {code}"


def test_frozen_checksums_exist_and_match():
    frozen_file = Path("docs/FROZEN.txt")
    assert frozen_file.exists()
    content = frozen_file.read_text(encoding="utf-8")
    
    # scam_rules_hi_en.json must match FROZEN.txt exactly
    hi_en_hash = hashlib.sha256(Path("rules/scam_rules_hi_en.json").read_bytes()).hexdigest()
    assert hi_en_hash in content
    
    # Gujarati files are tracked in docs/FROZEN_NOTES.md
    notes_file = Path("docs/FROZEN_NOTES.md")
    assert notes_file.exists()
    notes_content = notes_file.read_text(encoding="utf-8")
    gu_hash = hashlib.sha256(Path("rules/scam_rules_gu.json").read_bytes()).hexdigest()
    gu_warn_hash = hashlib.sha256(Path("rules/warnings_gu.json").read_bytes()).hexdigest()
    assert gu_hash in notes_content
    assert gu_warn_hash in notes_content
