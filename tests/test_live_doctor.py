"""Tests for live_doctor diagnosis logic."""
import os
from pathlib import Path
from scripts.live_doctor import diagnose_live


def test_live_doctor_missing_env(tmp_path):
    env_file = tmp_path / ".env"
    rep = diagnose_live(env_path=env_file, port=59999)
    assert not rep["all_pass"]
    key_check = next(c for c in rep["checks"] if c["name"] == "GNANI_API_KEY")
    assert key_check["passed"] is False
    assert key_check["detail"] == "missing"


def test_live_doctor_empty_key(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GNANI_API_KEY=\n", encoding="utf-8")
    rep = diagnose_live(env_path=env_file, port=59999)
    assert not rep["all_pass"]
    key_check = next(c for c in rep["checks"] if c["name"] == "GNANI_API_KEY")
    assert key_check["passed"] is False
    assert "missing or empty" in key_check["detail"]


def test_live_doctor_key_present(tmp_path, monkeypatch):
    monkeypatch.delenv("DEMO", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("GNANI_API_KEY=real_or_fake_secret_key_12345\n", encoding="utf-8")
    rep = diagnose_live(env_path=env_file, port=59999)
    key_check = next(c for c in rep["checks"] if c["name"] == "GNANI_API_KEY")
    assert key_check["passed"] is True
    assert key_check["detail"] == "present"
    # Never leak the actual key in report
    assert "12345" not in str(rep)


def test_live_doctor_demo_mode_detection(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO", "1")
    env_file = tmp_path / ".env"
    env_file.write_text("GNANI_API_KEY=some_key\n", encoding="utf-8")
    rep = diagnose_live(env_path=env_file, port=59999)
    demo_check = next(c for c in rep["checks"] if c["name"] == "DEMO mode")
    assert demo_check["passed"] is False
