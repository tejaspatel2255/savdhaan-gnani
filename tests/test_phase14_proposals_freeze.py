"""Unit tests for Phase 14 proposals application and rules freeze tools."""

import hashlib
import json
import shutil
from pathlib import Path
import pytest

from scripts.apply_rule_proposals import apply_proposals_to_dict
from scripts.freeze_rules import compute_rules_hashes


def test_apply_proposal_add_dampener_in_memory():
    sample_pack = {"rules": [], "dampeners": []}
    proposal = {
        "id": "P1",
        "type": "add_dampener",
        "fragment": {
            "id": "SAFE_COURIER_TEST",
            "patterns": ["कूरियर वाला"],
            "weight": -20
        }
    }
    apply_proposals_to_dict(sample_pack, proposal)
    assert len(sample_pack["dampeners"]) == 1
    assert sample_pack["dampeners"][0]["id"] == "SAFE_COURIER_TEST"


def test_apply_proposal_add_phrase_in_memory():
    sample_pack = {
        "rules": [
            {"id": "CRED_PIN_CVV", "patterns": ["पिन बताइए"]}
        ]
    }
    proposal = {
        "id": "P2",
        "type": "add_phrase",
        "target_rule_id": "CRED_PIN_CVV",
        "fragment": {
            "patterns_to_add": ["कलेक्ट रिक्वेस्ट", "पिन डालकर"]
        }
    }
    apply_proposals_to_dict(sample_pack, proposal)
    rule = sample_pack["rules"][0]
    assert "कलेक्ट रिक्वेस्ट" in rule["patterns"]
    assert "पिन डालकर" in rule["patterns"]
    assert len(rule["patterns"]) == 3


def test_freeze_rules_hash_computation(tmp_path, monkeypatch):
    test_rules_dir = tmp_path / "rules"
    test_rules_dir.mkdir()
    f1 = test_rules_dir / "r1.json"
    f1.write_text('{"rules": []}', encoding="utf-8")
    expected_h = hashlib.sha256(f1.read_bytes()).hexdigest()

    monkeypatch.setattr("scripts.freeze_rules.RULES_DIR", test_rules_dir)
    hashes = compute_rules_hashes()
    assert hashes["r1.json"] == expected_h
