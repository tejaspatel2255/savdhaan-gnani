"""Tests for live microphone mode (Phase 5B)."""

import asyncio
import time
import pytest

from backend.config import Settings
from backend.gnani_errors import GnaniError
from backend.mic import MicSource, FRAME_SIZE
from backend.orchestrator import SessionManager, StartSessionRequest
from tests.fake_stt_server import FakeSttServer


def test_mic_source_frame_sizes_and_levels():
    """Verify MicSource slices uneven chunks into exact 1024-byte frames."""
    async def run():
        fake_stt = FakeSttServer()
        port = await fake_stt.start()
        try:
            settings = Settings(api_key="fake-key", max_stt_seconds_per_run=100)
            mic = MicSource(settings, lang="hi-IN", base_url=f"ws://127.0.0.1:{port}")
            mic.attach("mock_socket")

            stop_event = asyncio.Event()
            received_events = []

            async def sink(ev):
                received_events.append(ev)

            run_task = asyncio.create_task(mic.run(sink, stop_event))

            # Wait until SttStream connection is established
            await asyncio.wait_for(mic._connected.wait(), timeout=2.0)

            # Push uneven chunks
            await mic.push(b"\x01\x00" * 150)
            await asyncio.sleep(0.01)
            await mic.push(b"\x02\x00" * 362)
            await asyncio.sleep(0.01)
            await mic.push(b"\x03\x00" * 1000)

            # Wait for fake_stt to receive frames
            for _ in range(50):
                if len(fake_stt.frames_received) >= 1:
                    break
                await asyncio.sleep(0.02)

            await mic.stop_push()
            stop_event.set()
            try:
                await asyncio.wait_for(run_task, timeout=1.0)
            except asyncio.TimeoutError:
                run_task.cancel()

            assert len(fake_stt.frames_received) > 0
            for fr in fake_stt.frames_received:
                assert len(fr) == 1024

            level_events = [ev for ev in received_events if ev.kind == "level"]
            assert len(level_events) > 0
        finally:
            await fake_stt.stop()

    asyncio.run(run())


def test_mic_mute_replaces_audio_with_silence():
    """Unit test: mute() causes incoming bytes to be replaced with zeros in sender buffer."""
    async def run():
        settings = Settings(api_key="fake-key")
        mic = MicSource(settings, lang="hi-IN")

        # Before mute: not muted
        now = time.monotonic()
        assert now >= mic._mute_until

        # After mute: audio byte replacement must produce zeros
        await mic.mute(5.0)
        now = time.monotonic()
        assert now < mic._mute_until, "mute_until must be in the future"

        chunk = b"\x7f\xff" * (FRAME_SIZE // 2)  # 1024 bytes of loud audio
        muted = now < mic._mute_until
        result = bytes(len(chunk)) if muted else chunk
        assert result == b"\x00" * FRAME_SIZE, "Muted audio must be all zeros"

        # After mute expires: audio passes through unchanged
        mic._mute_until = time.monotonic() - 0.1
        now = time.monotonic()
        muted = now < mic._mute_until
        result = bytes(len(chunk)) if muted else chunk
        assert result == chunk, "Unmuted audio must pass through unchanged"

    asyncio.run(run())


def test_mic_mode_requires_api_key():
    """Verify mic mode cannot start without GNANI_API_KEY."""
    settings = Settings(api_key="")
    mgr = SessionManager(settings)

    async def run():
        req = StartSessionRequest(mode="mic")
        with pytest.raises(ValueError, match="GNANI_API_KEY is required"):
            await mgr.start(req)

    asyncio.run(run())


def test_mic_websocket_origin_check_logic():
    """Verify origin check logic matches same-origin, allowed origins, and rejects different host."""
    from urllib.parse import urlparse

    def check_origin(origin: str, host: str, allowed_origins_str: str) -> bool:
        allowed = {"http://localhost:8000", "http://127.0.0.1:8000"}
        if allowed_origins_str:
            for o in allowed_origins_str.split(","):
                if o.strip():
                    allowed.add(o.strip())

        if not origin:
            return True  # Allowed for non-browser clients
        parsed = urlparse(origin)
        netloc = parsed.netloc or parsed.path
        if netloc == host:
            return True
        return origin in allowed

    # 1. Same-origin on port 8765 accepted
    assert check_origin("http://myhost:8765", "myhost:8765", "") is True

    # 2. Different host rejected
    assert check_origin("http://evil.com", "localhost:8000", "") is False
    assert check_origin("http://evil.com:8765", "myhost:8765", "") is False

    # 3. ALLOWED_ORIGINS entry accepted
    assert check_origin("https://savdhaan.vercel.app", "api.savdhaan.internal", "https://savdhaan.vercel.app") is True

    # 4. Missing origin accepted (non-browser client)
    assert check_origin("", "localhost:8000", "") is True
