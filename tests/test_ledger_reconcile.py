import json
from pathlib import Path
import pytest
from scripts.ledger_reconcile import (
    read_ledger,
    add_manual_usage,
    add_dashboard_observation,
)


def test_add_manual_usage(tmp_path: Path):
    ledger = tmp_path / "usage_ledger.json"
    add_manual_usage(ledger, tts_chars=500, stt_sec=25.5, reason="Reconciliation for warning files")
    data = read_ledger(ledger)
    assert data["lifetime"]["tts_chars"] == 500
    assert data["lifetime"]["stt_seconds"] == 25.5
    assert len(data["history"]) == 1
    assert data["history"][0]["type"] == "manual"
    assert data["history"][0]["reason"] == "Reconciliation for warning files"


def test_add_manual_usage_requires_reason(tmp_path: Path):
    ledger = tmp_path / "usage_ledger.json"
    with pytest.raises(ValueError):
        add_manual_usage(ledger, tts_chars=100, stt_sec=0, reason="")


def test_dashboard_observation_preserves_lifetime(tmp_path: Path):
    ledger = tmp_path / "usage_ledger.json"
    add_manual_usage(ledger, tts_chars=300, stt_sec=10.0, reason="Initial")
    add_dashboard_observation(ledger, balance=3750.0, note="Logged in at 11am")
    data = read_ledger(ledger)
    assert data["lifetime"]["tts_chars"] == 300
    assert data["lifetime"]["stt_seconds"] == 10.0
    assert len(data["history"]) == 2
    assert data["history"][1]["type"] == "dashboard_observation"
    assert data["history"][1]["balance"] == 3750.0
