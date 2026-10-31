"""Tests for Phase 13: The Blind Test Set infrastructure and guards."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.eval_blind import verify_blind_scoring_guards, record_blind_scoring_metadata
from scripts.import_blind import parse_blind_text, freeze_blind


SAMPLE_BLIND_VALID = """
ID: B01
LABEL: scam
TITLE: Fake tax refund call
LANG: hi-IN
CUE: 2
C: नमस्ते, मैं आयकर विभाग से बोल रहा हूँ।
L: जी कहिए।
C: आपका बीस हज़ार रुपये का रिफंड पेंडिंग है।
L: सच में?
C: तुरंत इस लिंक पर क्लिक करके ओटीपी शेयर करें।

ID: B02
LABEL: legit
TITLE: Clinic checkup reminder
LANG: hi-IN
C: नमस्ते, अस्पताल से डॉक्टर का सहायक बोल रहा हूँ।
L: नमस्ते जी।
C: आपकी कल सुबह ग्यारह बजे जांच तय है।
"""


def test_import_blind_valid_parse():
    calls = parse_blind_text(SAMPLE_BLIND_VALID)
    assert len(calls) == 2
    assert calls[0]["id"] == "B01"
    assert calls[0]["label"] == "scam"
    assert calls[0]["cue_turn"] == 1  # 0-based
    assert calls[1]["id"] == "B02"
    assert calls[1]["label"] == "legit"
    assert calls[1]["cue_turn"] is None


def test_import_blind_validation_duplicate_id():
    content = SAMPLE_BLIND_VALID + "\nID: B01\nLABEL: legit\nTITLE: Dupe\nC: एक\nL: दो\nC: तीन\n"
    with pytest.raises(ValueError, match="Duplicate ID"):
        parse_blind_text(content)


def test_import_blind_validation_invalid_id_prefix():
    content = "ID: D99\nLABEL: scam\nTITLE: Bad ID\nC: एक\nL: दो\nC: तीन\n"
    with pytest.raises(ValueError, match="must match 'B'"):
        parse_blind_text(content)


def test_import_blind_validation_invalid_label():
    content = "ID: B03\nLABEL: maybe\nTITLE: Bad label\nC: एक\nL: दो\nC: तीन\n"
    with pytest.raises(ValueError, match="LABEL must be 'scam' or 'legit'"):
        parse_blind_text(content)


def test_import_blind_validation_turn_count():
    content = "ID: B04\nLABEL: scam\nTITLE: Too short\nC: एक\nL: दो\n"
    with pytest.raises(ValueError, match="between 3 and 8 turns"):
        parse_blind_text(content)


def test_import_blind_validation_phone_digits():
    content = "ID: B05\nLABEL: scam\nTITLE: Real phone\nC: कॉल 987654321099 तुरंत\nL: जी\nC: ठीक है\n"
    with pytest.raises(ValueError, match="Run of 10\\+ digits"):
        parse_blind_text(content)


def test_import_blind_validation_url_rejection():
    content = "ID: B06\nLABEL: scam\nTITLE: URL\nC: http://evil.com देखें\nL: जी\nC: ठीक है\n"
    with pytest.raises(ValueError, match="Potential real URL"):
        parse_blind_text(content)


def test_freeze_blind_file_creation(tmp_path, monkeypatch):
    frozen_file = tmp_path / "docs" / "FROZEN_BLIND.txt"
    monkeypatch.setattr("scripts.import_blind.Path", lambda p: tmp_path / p if "docs" in str(p) else Path(p))

    raw_bytes = b'{"split": "blind", "calls": []}'
    h = freeze_blind(raw_bytes, 0, new_version=False)
    assert frozen_file.exists()
    assert h in frozen_file.read_text(encoding="utf-8")


def test_blind_scoring_guard_refuses_when_frozen_final_missing(tmp_path):
    ok, msg, _ = verify_blind_scoring_guards(
        confirm_blind_once=True,
        i_understand_this_is_a_rescore=False,
        results_path=tmp_path / "results.json",
        frozen_final_path=tmp_path / "docs" / "FROZEN_FINAL.txt",
    )
    assert not ok
    assert "Rules are not frozen yet: finish Phase 14 first." in msg


def test_blind_scoring_guard_refuses_without_confirm_blind_once(tmp_path):
    # Setup dummy frozen_final
    final_file = tmp_path / "FROZEN_FINAL.txt"
    final_file.write_text("dummy rules", encoding="utf-8")
    
    # Setup dummy frozen_blind and blind_calls
    blind_file = tmp_path / "blind_calls.json"
    content = b'{"calls": []}'
    blind_file.write_bytes(content)
    h = hashlib.sha256(content).hexdigest()
    blind_frozen = tmp_path / "FROZEN_BLIND.txt"
    blind_frozen.write_text(f"blind_calls.json: {h}", encoding="utf-8")

    # Empty rules dir for test
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    ok, msg, _ = verify_blind_scoring_guards(
        confirm_blind_once=False,
        i_understand_this_is_a_rescore=False,
        results_path=tmp_path / "results.json",
        frozen_final_path=final_file,
        frozen_blind_path=blind_frozen,
        blind_calls_path=blind_file,
        rules_dir=rules_dir,
    )
    assert not ok
    assert "--confirm-blind-once" in msg


def test_blind_scoring_guard_allows_with_all_flags(tmp_path):
    final_file = tmp_path / "FROZEN_FINAL.txt"
    final_file.write_text("rules", encoding="utf-8")
    
    blind_file = tmp_path / "blind_calls.json"
    content = b'{"calls": []}'
    blind_file.write_bytes(content)
    h = hashlib.sha256(content).hexdigest()
    blind_frozen = tmp_path / "FROZEN_BLIND.txt"
    blind_frozen.write_text(f"blind_calls.json: {h}", encoding="utf-8")

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    ok, msg, times = verify_blind_scoring_guards(
        confirm_blind_once=True,
        i_understand_this_is_a_rescore=False,
        results_path=tmp_path / "results.json",
        frozen_final_path=final_file,
        frozen_blind_path=blind_frozen,
        blind_calls_path=blind_file,
        rules_dir=rules_dir,
    )
    assert ok
    assert times == 0


def test_blind_scoring_guard_requires_rescore_flag_on_subsequent_runs(tmp_path):
    final_file = tmp_path / "FROZEN_FINAL.txt"
    final_file.write_text("rules", encoding="utf-8")
    
    blind_file = tmp_path / "blind_calls.json"
    content = b'{"calls": []}'
    blind_file.write_bytes(content)
    h = hashlib.sha256(content).hexdigest()
    blind_frozen = tmp_path / "FROZEN_BLIND.txt"
    blind_frozen.write_text(f"blind_calls.json: {h}", encoding="utf-8")

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    results_file = tmp_path / "results.json"
    results_file.write_text(json.dumps({"blind_scoring": {"times_scored": 1}}), encoding="utf-8")

    # Without rescore flag -> refuse
    ok, msg, times = verify_blind_scoring_guards(
        confirm_blind_once=True,
        i_understand_this_is_a_rescore=False,
        results_path=results_file,
        frozen_final_path=final_file,
        frozen_blind_path=blind_frozen,
        blind_calls_path=blind_file,
        rules_dir=rules_dir,
    )
    assert not ok
    assert "--i-understand-this-is-a-rescore" in msg
    assert times == 1

    # With rescore flag -> allowed
    ok, msg, times = verify_blind_scoring_guards(
        confirm_blind_once=True,
        i_understand_this_is_a_rescore=True,
        results_path=results_file,
        frozen_final_path=final_file,
        frozen_blind_path=blind_frozen,
        blind_calls_path=blind_file,
        rules_dir=rules_dir,
    )
    assert ok
