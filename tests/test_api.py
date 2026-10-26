"""Integration tests for FastAPI REST routes and WebSocket UI endpoint."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings

client = TestClient(app)


def test_api_calls_shape_and_defaults():
    resp = client.get("/api/calls")
    assert resp.status_code == 200
    data = resp.json()
    assert "calls" in data
    assert any(c["id"] == "mock" for c in data["calls"])


def test_api_usage_shape():
    resp = client.get("/api/usage")
    assert resp.status_code == 200
    data = resp.json()
    assert "lifetime" in data
    assert "caps" in data


def test_api_eval_404_when_absent():
    eval_file = Path("data/eval/results.json")
    if not eval_file.exists():
        resp = client.get("/api/eval")
        assert resp.status_code == 404


def test_api_audio_path_traversal_rejection():
    # slashes or dots: rejected with 400 or 404
    assert client.get("/api/audio/../secret.wav").status_code in (400, 404)
    assert client.get("/api/audio/sub/secret.wav").status_code in (400, 404)
    assert client.get("/api/audio/secret.test.wav").status_code == 400


def test_api_start_validation():
    # Bad thresholds -> 422
    resp_thresh = client.post("/api/session/start", json={"mode": "mock", "careful": 80, "danger": 50})
    assert resp_thresh.status_code == 422

    # Mode mic -> 400
    resp_mic = client.post("/api/session/start", json={"mode": "mic"})
    assert resp_mic.status_code == 400

    # Unknown call_id for replay -> 400
    resp_unknown = client.post("/api/session/start", json={"mode": "replay", "call_id": "non_existent_12345"})
    assert resp_unknown.status_code == 400


def test_ws_ui_delivers_history_of_finished_session():
    from backend.events import Emitter, build_session_event, build_summary_event
    from backend.main import session_manager

    emitter = Emitter("test_ws_history")
    session_manager._last_emitter = emitter
    build_session_event(
        emitter,
        state="ended",
        mode="mock",
        mode_label="MOCK",
        call_title="Mock digital arrest",
        synthetic=True,
        lang="hi-IN",
        thresholds={"careful": 30, "danger": 60},
        t=0.0,
    )
    build_summary_event(
        emitter,
        duration_s=10.0,
        segments=1,
        time_to_alert_s=None,
        max_score=0,
        final_level="calm",
        categories={},
        stt_latency_ms={"p50": None, "p95": None},
        credits_used={"stt_seconds": 0.0, "tts_chars": 0},
        mode="mock",
        synthetic=True,
        t=10.0,
    )

    # Connect WebSocket via TestClient
    with client.websocket_connect("/ws/ui") as websocket:
        # History messages arrive
        received = []
        while True:
            try:
                data = websocket.receive_text()
                msg = json.loads(data)
                received.append(msg)
                if msg.get("type") == "summary":
                    break
            except Exception:
                break
        assert len(received) == 2
        assert received[0]["type"] == "session"
        assert received[-1]["type"] == "summary"
        assert received[0]["type"] == "session"
        assert received[-1]["type"] == "summary"
