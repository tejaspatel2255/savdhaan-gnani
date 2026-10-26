"""Unit and integration tests for session orchestrator, sources, and warning audio."""

import asyncio
import io
import json
import wave
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
import soundfile as sf
import numpy as np

from backend.config import Settings
from backend.events import Emitter
from backend.gnani_errors import GnaniError
from backend.gnani_tts import TtsResult
from backend.metrics import percentile
from backend.orchestrator import SessionBusy, SessionManager, StartSessionRequest
from backend.warning import WARNINGS, family_message, get_warning, pick_key
from tests.fake_stt_server import FakeSttServer


def make_dummy_wav_bytes(duration_s: float = 1.0, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        frames_count = int(rate * duration_s)
        wf.writeframes(b"\x00\x00" * frames_count)
    return buf.getvalue()


# --- Metrics tests ---

def test_percentile_known_and_empty():
    assert percentile([], 50) is None
    assert percentile([100], 50) == 100
    # [10, 20, 30, 40, 50]
    vals = [10, 20, 30, 40, 50]
    assert percentile(vals, 50) == 30
    assert percentile(vals, 0) == 10
    assert percentile(vals, 100) == 50


# --- Warning unit tests ---

def test_warning_pick_key_priority():
    assert pick_key([{"category": "remote_app"}, {"category": "threat"}]) == "remote"
    assert pick_key([{"category": "payment"}, {"category": "threat"}]) == "money"
    assert pick_key([{"category": "credentials"}]) == "otp"
    assert pick_key([{"category": "threat"}]) == "arrest"
    assert pick_key([{"category": "urgency"}]) == "generic"


def test_warning_texts_and_character_counts():
    for lang in ("hi-IN", "en-IN"):
        assert set(WARNINGS[lang].keys()) == {"generic", "arrest", "otp", "money", "remote"}

    hi_chars = sum(len(t) for t in WARNINGS["hi-IN"].values())
    assert hi_chars <= 600


def test_warning_unknown_lang_fallback():
    msg = family_message("fr-FR", [{"label_en": "threat"}])
    assert "Savdhaan alert:" in msg


# --- Emitter tests ---

def test_emitter_queue_overflow_and_monotonic_t():
    emitter = Emitter("test_sess")
    q = emitter.subscribe()
    # emit 1005 items
    for i in range(1005):
        emitter.emit("audio_level", t=i * 0.1, rms=0.1)

    assert q.qsize() == 1000
    # Monotonic t check: passing a lower t should keep largest so far
    ev = emitter.emit("session", t=5.0)
    assert ev["t"] >= 100.4

    emitter.unsubscribe(q)
    assert q not in emitter._subscribers


# --- Orchestrator & Mock Session Tests ---

def test_mock_session_complete_flow_and_order():
    # Ensure cached warning audio doesn't bypass TTS call for this test
    cache_file = Path("data/cache/warnings/warn_hi_in_arrest_shivani.wav")
    if cache_file.exists():
        cache_file.unlink()

    dummy_settings = Settings(api_key="mock", max_tts_chars_per_run=600)
    tts_called = 0

    async def fake_tts(*args, **kwargs):
        nonlocal tts_called
        tts_called += 1
        return TtsResult(audio=make_dummy_wav_bytes(2.5), cached=False, chars=40, elapsed_ms=10)

    mgr = SessionManager(dummy_settings, data_dir="data", tts=fake_tts)

    async def run():
        req = StartSessionRequest(mode="mock", speed=200.0, speak_warning=True)
        sess_id = await mgr.start(req)

        while mgr.is_busy():
            await asyncio.sleep(0.01)

        history = mgr.history()
        types = [m["type"] for m in history]

        assert types[0] == "session"
        assert history[0]["state"] == "starting"
        assert types[1] == "session"
        assert history[1]["state"] == "listening"

        seqs = [m["seq"] for m in history]
        assert seqs == list(range(len(history)))

        ts = [m["t"] for m in history]
        assert all(ts[i] <= ts[i + 1] for i in range(len(ts) - 1))

        transcripts = [m for m in history if m["type"] == "transcript"]
        risks = [m for m in history if m["type"] == "risk"]
        assert len(transcripts) == 7
        assert len(risks) == 7

        alerts = [m for m in history if m["type"] == "alert"]
        assert len(alerts) == 1
        alert_msg = alerts[0]
        alert_seq = alert_msg["seq"]

        t3 = [m for m in history if m["type"] == "transcript" and m["segment_index"] == 3][0]
        r3 = [m for m in history if m["type"] == "risk" and m["segment_index"] == 3][0]
        assert t3["seq"] < r3["seq"] < alert_seq

        fam_alerts = [m for m in history if m["type"] == "family_alert"]
        assert len(fam_alerts) == 1
        assert fam_alerts[0]["seq"] == alert_seq + 1

        warn_audios = [m for m in history if m["type"] == "warning_audio"]
        assert len(warn_audios) == 1
        warn_audio = warn_audios[0]

        end_session_idx = [i for i, m in enumerate(history) if m["type"] == "session" and m["state"] == "ended"][0]
        warn_audio_idx = history.index(warn_audio)
        assert warn_audio_idx < end_session_idx

        assert types[-1] == "summary"
        summary = history[-1]
        assert summary["time_to_alert_s"] == 24.6
        assert summary["max_score"] == 100
        assert summary["final_level"] == "danger"
        assert summary["stt_latency_ms"]["p50"] is None
        assert summary["mode"] == "mock"
        assert summary["synthetic"] is True

        assert tts_called == 1
        assert "/api/audio/" in warn_audio["audio_url"]

    asyncio.run(run())


def test_speak_warning_false_skips_tts():
    dummy_settings = Settings(api_key="mock")
    tts_mock = AsyncMock()
    mgr = SessionManager(dummy_settings, data_dir="data", tts=tts_mock)

    async def run():
        req = StartSessionRequest(mode="mock", speed=200.0, speak_warning=False)
        await mgr.start(req)

        while mgr.is_busy():
            await asyncio.sleep(0.01)

        history = mgr.history()
        alert = [m for m in history if m["type"] == "alert"][0]
        assert alert["warning"]["status"] == "skipped"

        warn_audio = [m for m in history if m["type"] == "warning_audio"][0]
        assert warn_audio["audio_url"] is None
        assert warn_audio["reason"] == "speaking_off"
        assert tts_mock.call_count == 0

    asyncio.run(run())


def test_fake_tts_failure_emits_recoverable_error():
    # Ensure cached warning audio doesn't bypass broken_tts call
    cache_file = Path("data/cache/warnings/warn_hi_in_arrest_shivani.wav")
    if cache_file.exists():
        cache_file.unlink()

    dummy_settings = Settings(api_key="mock")

    async def broken_tts(*args, **kwargs):
        raise GnaniError("TTS server down", code="tts_failed", recoverable=True)

    mgr = SessionManager(dummy_settings, data_dir="data", tts=broken_tts)

    async def run():
        req = StartSessionRequest(mode="mock", speed=200.0, speak_warning=True)
        await mgr.start(req)

        while mgr.is_busy():
            await asyncio.sleep(0.01)

        history = mgr.history()
        warn_audio = [m for m in history if m["type"] == "warning_audio"][0]
        assert warn_audio["audio_url"] is None
        assert warn_audio["reason"] == "tts_failed"

        errors = [m for m in history if m["type"] == "error"]
        assert any(e["code"] == "tts_failed" and e["recoverable"] is True for e in errors)
        assert history[-1]["type"] == "summary"

    asyncio.run(run())


def test_session_busy_409_and_stop():
    dummy_settings = Settings(api_key="mock")
    mgr = SessionManager(dummy_settings, data_dir="data")

    async def run():
        req = StartSessionRequest(mode="mock", speed=0.5)
        sid = await mgr.start(req)

        with pytest.raises(SessionBusy):
            await mgr.start(req)

        stopped = await mgr.stop(sid)
        assert stopped is True

        history = mgr.history()
        types = [m["type"] for m in history]
        assert types[-2] == "session"
        assert history[-2]["state"] == "ended"
        assert types[-1] == "summary"

    asyncio.run(run())


def test_file_mode_no_key_error():
    dummy_settings = Settings(api_key="")
    mgr = SessionManager(dummy_settings, data_dir="data")

    async def run():
        req = StartSessionRequest(mode="file", call_id="test_call")
        await mgr.start(req)

        while mgr.is_busy():
            await asyncio.sleep(0.01)

        history = mgr.history()
        errors = [m for m in history if m["type"] == "error"]
        assert len(errors) == 1
        assert errors[0]["code"] == "no_key"
        assert history[-2]["state"] == "error"
        assert history[-1]["type"] == "summary"

    asyncio.run(run())


def test_replay_mode_stt_latency_from_file(tmp_path):
    rep_dir = tmp_path / "transcripts"
    rep_dir.mkdir(parents=True, exist_ok=True)
    rep_file = rep_dir / "test_rep.jsonl"
    line = {
        "t": 1.0,
        "segment_index": 0,
        "segment_id": "seg_0",
        "text": "नमस्ते",
        "audio_duration_ms": 1000,
        "latency": 345,
    }
    rep_file.write_text(json.dumps(line) + "\n", encoding="utf-8")

    dummy_settings = Settings(api_key="mock")
    mgr = SessionManager(dummy_settings, data_dir=str(tmp_path))

    async def run():
        req = StartSessionRequest(mode="replay", call_id="test_rep", speed=100.0)
        await mgr.start(req)

        while mgr.is_busy():
            await asyncio.sleep(0.01)

        history = mgr.history()
        transcripts = [m for m in history if m["type"] == "transcript"]
        assert len(transcripts) == 1
        assert transcripts[0]["stt_latency_ms"] == 345

    asyncio.run(run())


def test_file_mode_with_fake_stt_server(tmp_path):
    async def run():
        server = FakeSttServer()
        port = await server.start()
        try:
            calls_dir = tmp_path / "calls"
            calls_dir.mkdir(parents=True, exist_ok=True)
            wav_file = calls_dir / "short_call.wav"
            data = np.zeros(8000, dtype=np.int16)
            sf.write(str(wav_file), data, 8000)

            dummy_settings = Settings(api_key="valid-test-key", max_stt_seconds_per_run=100)
            mgr = SessionManager(
                dummy_settings,
                data_dir=str(tmp_path),
                stt_base_url=f"ws://127.0.0.1:{port}",
            )

            req = StartSessionRequest(mode="file", call_id="short_call", sample_rate=8000)
            await mgr.start(req)

            while mgr.is_busy():
                await asyncio.sleep(0.02)

            history = mgr.history()
            levels = [m for m in history if m["type"] == "audio_level"]
            assert 0 < len(levels) <= 30
            summary = history[-1]
            assert summary["credits_used"]["stt_seconds"] > 0
        finally:
            await server.stop()

    asyncio.run(run())
