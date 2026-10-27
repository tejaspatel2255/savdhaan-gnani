"""Tests for /api/eval endpoint (Phase 7)."""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_eval_404_when_absent(tmp_path, monkeypatch):
    eval_file = tmp_path / "nonexistent_results.json"
    monkeypatch.setattr("backend.main.Path", lambda p: eval_file if "results.json" in str(p) else Path(p))

    resp = client.get("/api/eval")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "no_results"


def test_api_eval_serves_json_when_present(tmp_path, monkeypatch):
    eval_file = tmp_path / "results.json"
    test_data = {"test_metric": 42, "status": "ok"}
    eval_file.write_text(json.dumps(test_data), encoding="utf-8")

    monkeypatch.setattr("backend.main.Path", lambda p: eval_file if "results.json" in str(p) else Path(p))

    resp = client.get("/api/eval")
    assert resp.status_code == 200
    assert resp.json() == test_data
