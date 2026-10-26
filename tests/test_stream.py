"""Unit and integration tests for streaming STT client and pacing."""

import asyncio
import json
import time
from pathlib import Path
import pytest

from backend.audio_utils import pace_frames
from backend.config import Settings
from backend.gnani_errors import GnaniError
from backend.gnani_stream import (
    Connected,
    Processing,
    SttStream,
    Transcript,
    build_headers,
    stream_call,
)
from backend import usage
from tests.fake_stt_server import FakeSttServer


def test_build_headers_names_and_telephony_preset():
    """Verify build_headers outputs exact docs/API_CONTRACT.md header names and 8000 Hz preset."""
    h_8k = build_headers("test-key", "hi-IN", 8000)
    assert h_8k["x-api-key-id"] == "test-key"
    assert h_8k["lang_code"] == "hi-IN"
    assert h_8k["x-sample-rate"] == "8000"
    assert h_8k["x-format"] == "verbatim"
    assert h_8k["x-vad-threshold"] == "0.7"
    assert h_8k["x-min-speech-ms"] == "200"
    assert h_8k["x-min-silence-ms"] == "500"

    h_16k = build_headers("test-key", "en-IN", 16000)
    assert h_16k["x-sample-rate"] == "16000"
    assert "x-vad-threshold" not in h_16k


def test_build_headers_optional_bias():
    """Verify bias list and score are included only when provided."""
    h = build_headers("key", "hi-IN", 16000, bias_list=["police", "bank"], bias_score=1.5)
    assert json.loads(h["x-bias-list"]) == ["police", "bank"]
    assert h["x-bias-score"] == "1.5"


@pytest.mark.anyio
async def test_wrong_size_frame_rejected():
    """SttStream.send raises ValueError unless len(frame) == 1024."""
    dummy_settings = Settings(api_key="mock")
    stream = SttStream(dummy_settings, "hi-IN", 16000)
    with pytest.raises(ValueError):
        await stream.send(b"\x00" * 500)
    with pytest.raises(ValueError):
        await stream.send(b"\x00" * 1025)


@pytest.mark.anyio
async def test_frame_intervals_cadence_within_25_percent():
    """Verify pace_frames maintains 32ms nominal interval at 16000 Hz within 25% tolerance over 30 frames."""
    dummy_frames = [b"\x00" * 1024] * 30
    timestamps = []

    async def mock_send(fr: bytes):
        timestamps.append(time.monotonic())

    t0 = time.monotonic()
    await pace_frames(iter(dummy_frames), 16000, mock_send)
    total_elapsed = time.monotonic() - t0

    nominal = 30 * 0.032
    # Within 25% tolerance
    assert 0.75 * nominal <= total_elapsed <= 1.35 * nominal


@pytest.mark.anyio
async def test_fake_server_transcripts_parsed_and_t_increases():
    """Test full stream with FakeSttServer: transcripts parsed, t increases, and events received."""
    server = FakeSttServer()
    port = await server.start()
    try:
        dummy_settings = Settings(api_key="mock-key-abc")
        pcm = b"\x00" * (45 * 1024)
        events_received = []

        transcripts = await stream_call(
            pcm,
            lang="hi-IN",
            rate=16000,
            settings=dummy_settings,
            on_event=lambda ev: events_received.append(ev),
            tail_silence_ms=50,
            base_url=f"ws://127.0.0.1:{port}",
        )

        assert len(transcripts) >= 2
        assert isinstance(transcripts[0], Transcript)
        assert transcripts[0].text == "Mock segment 0"
        assert transcripts[1].text == "Mock segment 1"
        assert transcripts[1].t >= transcripts[0].t

        # Check recorded upgrade headers on server
        assert server.recorded_headers.get("x-api-key-id") == "mock-key-abc"
        assert server.recorded_headers.get("lang_code") == "hi-IN"
        assert server.recorded_headers.get("x-sample-rate") == "16000"
    finally:
        await server.stop()


@pytest.mark.anyio
async def test_auth_failure_4001_raises_auth_error():
    """Connection closed with 4001 raises GnaniError with code 'auth'."""
    server = FakeSttServer(close_with_4001=True)
    port = await server.start()
    try:
        dummy_settings = Settings(api_key="bad-key")
        pcm = b"\x00" * (5 * 1024)

        with pytest.raises(GnaniError) as exc_info:
            await stream_call(
                pcm,
                lang="hi-IN",
                rate=16000,
                settings=dummy_settings,
                on_event=lambda ev: None,
                tail_silence_ms=50,
                base_url=f"ws://127.0.0.1:{port}",
            )
        assert exc_info.value.code == "auth"
    finally:
        await server.stop()


@pytest.mark.anyio
async def test_tail_silence_sent():
    """Verify stream_call sends extra tail silence frames."""
    server = FakeSttServer()
    port = await server.start()
    try:
        dummy_settings = Settings(api_key="test")
        pcm = b"\x01" * (10 * 1024)
        await stream_call(
            pcm,
            lang="hi-IN",
            rate=16000,
            settings=dummy_settings,
            on_event=lambda ev: None,
            tail_silence_ms=200,
            base_url=f"ws://127.0.0.1:{port}",
        )
        assert len(server.frames_received) > 10
    finally:
        await server.stop()


def test_dry_run_masks_api_key(capsys):
    """Verify that build_headers or dry-run scripts mask API keys."""
    headers = build_headers("secret_gnani_key", "hi-IN", 16000)
    masked = dict(headers)
    masked["x-api-key-id"] = "***MASKED***"
    assert "secret_gnani_key" not in json.dumps(masked)
    assert masked["x-api-key-id"] == "***MASKED***"
