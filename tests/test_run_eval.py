"""Unit tests for Phase 7 scripts/run_eval.py."""

import argparse
import hashlib
import json
import pytest
from pathlib import Path

from scripts.run_eval import handle_record, handle_score, handle_wer, score_calls_data
from backend.scorer import load_pack
from backend.config import Settings


def test_score_calls_data_with_fake_transcripts(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.run_eval.TRANSCRIPTS_DIR", tmp_path)

    # Write 2 scam and 2 legit fake transcripts
    # D01: alert on second line
    t_d01 = [
        {"t": 1.0, "segment_index": 0, "text": "नमस्ते मैं साइबर सेल से बोल रहा हूँ", "latency": 150},
        {"t": 3.5, "segment_index": 1, "text": "आपके खिलाफ अरेस्ट वारंट निकला है अपना ओटीपी बताइए", "latency": 160},
    ]
    with open(tmp_path / "D01_digital_arrest.jsonl", "w", encoding="utf-8") as f:
        for r in t_d01:
            f.write(json.dumps(r) + "\n")

    # D02: no alert
    t_d02 = [
        {"t": 1.0, "segment_index": 0, "text": "नमस्ते कहिए", "latency": 120},
    ]
    with open(tmp_path / "D02_otp_kyc.jsonl", "w", encoding="utf-8") as f:
        for r in t_d02:
            f.write(json.dumps(r) + "\n")

    # D06: legit clean
    t_d06 = [
        {"t": 1.0, "segment_index": 0, "text": "नमस्ते आपकी ईएमआई बाकी है", "latency": 110},
    ]
    with open(tmp_path / "D06_emi_reminder.jsonl", "w", encoding="utf-8") as f:
        for r in t_d06:
            f.write(json.dumps(r) + "\n")

    # D07: legit clean
    t_d07 = [
        {"t": 1.0, "segment_index": 0, "text": "नमस्ते आपका पार्सल आ गया है", "latency": 130},
    ]
    with open(tmp_path / "D07_delivery.jsonl", "w", encoding="utf-8") as f:
        for r in t_d07:
            f.write(json.dumps(r) + "\n")

    calls = [
        {"id": "D01_digital_arrest", "split": "dev", "label": "scam", "first_cue_s": 1.0},
        {"id": "D02_otp_kyc", "split": "dev", "label": "scam", "first_cue_s": 1.0},
        {"id": "D06_emi_reminder", "split": "dev", "label": "legit"},
        {"id": "D07_delivery", "split": "dev", "label": "legit"},
    ]

    pack = load_pack("rules/scam_rules_hi_en.json")
    rows, lats = score_calls_data(calls, pack, careful=30, danger=60, cond="phone_noise", from_script=False)

    assert len(rows) == 4
    d01_row = next(r for r in rows if r["id"] == "D01_digital_arrest")
    assert d01_row["alerted"] is True
    # alert_t should be 3.5, the t of the line that raised the alert
    assert d01_row["alert_t"] == 3.5
    assert len(lats) == 5


def test_split_with_no_transcripts_yields_null_real_fields(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.run_eval.TRANSCRIPTS_DIR", tmp_path / "nonexistent")
    monkeypatch.setattr("scripts.run_eval.EVAL_DIR", tmp_path)
    monkeypatch.setattr("scripts.run_eval.RESULTS_PATH", tmp_path / "results.json")
    monkeypatch.setattr("scripts.run_eval.TEST_RUNS_PATH", tmp_path / "test_runs.jsonl")

    args = argparse.Namespace(split="dev", cond="phone_noise", careful=30, danger=60, sweep=False, ceiling=False)
    handle_score(args)

    results = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    dev_split = results["splits"]["dev"]
    assert dev_split["recall"] is None
    assert dev_split["tp"] is None


def test_test_split_scoring_increments_and_tracks_hash(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.run_eval.TRANSCRIPTS_DIR", tmp_path)
    monkeypatch.setattr("scripts.run_eval.EVAL_DIR", tmp_path)
    monkeypatch.setattr("scripts.run_eval.RESULTS_PATH", tmp_path / "results.json")
    test_runs_file = tmp_path / "test_runs.jsonl"
    monkeypatch.setattr("scripts.run_eval.TEST_RUNS_PATH", test_runs_file)

    args = argparse.Namespace(split="test", cond="phone_noise", careful=30, danger=60, sweep=False, ceiling=False)

    # Run 1
    handle_score(args)
    res1 = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert res1["test_scoring"]["times_scored"] == 1
    assert res1["test_scoring"]["rules_changed_since_first"] is False

    # Run 2
    handle_score(args)
    res2 = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert res2["test_scoring"]["times_scored"] == 2
    assert res2["test_scoring"]["rules_changed_since_first"] is False

    # Simulate modifying rules hash in a 3rd run
    with open(test_runs_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": "2026-10-27T00:00:00Z", "rules_sha256": "different_hash_12345"}) + "\n")

    handle_score(args)
    res3 = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert res3["test_scoring"]["times_scored"] == 4
    assert res3["test_scoring"]["rules_changed_since_first"] is True


def test_sweep_refuses_on_test_split():
    args = argparse.Namespace(split="test", cond="phone_noise", careful=30, danger=60, sweep=True, ceiling=False)
    with pytest.raises(SystemExit) as exc:
        handle_score(args)
    assert exc.value.code != 0


def test_record_without_go_streams_nothing(monkeypatch, capsys):
    called = []
    async def mock_record(*a, **kw):
        called.append(True)
    monkeypatch.setattr("scripts.run_eval.record_call", mock_record)

    args = argparse.Namespace(split="dev", ids=None, cond="phone_noise", force=False, go=False)
    handle_record(args)
    assert len(called) == 0
    captured = capsys.readouterr().out
    assert "Dry run complete" in captured


def test_record_over_cap_prints_exact_refusal(monkeypatch, capsys):
    from backend.config import settings
    # Settings is a frozen dataclass, replace the instance with an updated one
    new_settings = Settings(
        api_key=settings.api_key,
        max_tts_chars_per_run=settings.max_tts_chars_per_run,
        max_stt_seconds_per_run=5,
        thresh_careful=settings.thresh_careful,
        thresh_danger=settings.thresh_danger,
        save_live_runs=settings.save_live_runs,
        warning_voice=settings.warning_voice,
        warning_model=settings.warning_model,
        tts_credits_per_1k_chars=settings.tts_credits_per_1k_chars,
        stt_credits_per_minute=settings.stt_credits_per_minute,
    )
    monkeypatch.setattr("scripts.run_eval.settings", new_settings)

    args = argparse.Namespace(split="dev", ids=None, cond="phone_noise", force=False, go=False)
    with pytest.raises(SystemExit):
        handle_record(args)
    captured = capsys.readouterr().out
    assert "This run needs about" in captured
    assert "MAX_STT_SECONDS_PER_RUN" in captured


def test_wer_without_go_makes_no_http_calls(monkeypatch, capsys):
    from backend.config import settings
    # Raise cap for dry run test
    new_settings = Settings(
        api_key=settings.api_key,
        max_tts_chars_per_run=settings.max_tts_chars_per_run,
        max_stt_seconds_per_run=1000,
        thresh_careful=settings.thresh_careful,
        thresh_danger=settings.thresh_danger,
        save_live_runs=settings.save_live_runs,
        warning_voice=settings.warning_voice,
        warning_model=settings.warning_model,
        tts_credits_per_1k_chars=settings.tts_credits_per_1k_chars,
        stt_credits_per_minute=settings.stt_credits_per_minute,
    )
    monkeypatch.setattr("scripts.run_eval.settings", new_settings)

    called = []
    async def fail_transcribe(*a, **kw):
        called.append(True)
        raise RuntimeError("HTTP should not be called in dry run")
    monkeypatch.setattr("scripts.run_eval.transcribe_file", fail_transcribe)

    args = argparse.Namespace(ids="D01_digital_arrest", conds="clean", go=False)
    handle_wer(args)
    assert len(called) == 0
    captured = capsys.readouterr().out
    assert "Dry run complete" in captured


def test_results_merge_keeps_other_split(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.run_eval.TRANSCRIPTS_DIR", tmp_path)
    monkeypatch.setattr("scripts.run_eval.EVAL_DIR", tmp_path)
    res_path = tmp_path / "results.json"
    monkeypatch.setattr("scripts.run_eval.RESULTS_PATH", res_path)
    monkeypatch.setattr("scripts.run_eval.TEST_RUNS_PATH", tmp_path / "test_runs.jsonl")

    # Initial results with dev
    initial = {
        "splits": {
            "test": {"recall": 0.8, "tp": 4, "fn": 1, "n": 5}
        },
        "calls": [{"id": "T01", "split": "test", "label": "scam"}]
    }
    res_path.write_text(json.dumps(initial), encoding="utf-8")

    # Score only dev
    args = argparse.Namespace(split="dev", cond="phone_noise", careful=30, danger=60, sweep=False, ceiling=True)
    handle_score(args)

    merged = json.loads(res_path.read_text(encoding="utf-8"))
    assert "dev" in merged["splits"]
    assert "test" in merged["splits"]
    assert merged["splits"]["test"]["recall"] == 0.8
