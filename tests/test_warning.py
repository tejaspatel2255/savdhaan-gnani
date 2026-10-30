"""Tests for backend/warning.py — especially the committed-audio fallback."""
import asyncio
import io
import struct
import wave
from pathlib import Path

import pytest


def _make_tiny_wav() -> bytes:
    """Create a minimal valid WAV file in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x00\x00" * 80)  # 10 ms of silence
    return buf.getvalue()


def test_committed_audio_returns_cached_no_tts(tmp_path, monkeypatch):
    """When frontend/assets/audio/{name}.wav exists, get_warning must return
    cached=True and must NOT invoke the TTS synthesizer."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    cache_dir = tmp_path / "cache" / "warnings"
    cache_dir.mkdir(parents=True)

    # Write a valid wav file at the committed path
    wav_bytes = _make_tiny_wav()
    # The name format is warn_{lang}_{key}_{voice}.wav
    name = "warn_hi_in_generic_testvoice"
    (audio_dir / f"{name}.wav").write_bytes(wav_bytes)

    from backend import warning as w_mod

    monkeypatch.setattr(w_mod, "COMMITTED_AUDIO_DIR", audio_dir)
    monkeypatch.setattr(w_mod, "CACHE_DIR", cache_dir)

    tts_called = []

    async def fake_tts(**kwargs):
        tts_called.append(True)
        raise AssertionError("TTS should not be called when committed audio exists")

    result = asyncio.run(
        w_mod.get_warning(
            lang="hi-IN",
            key="generic",
            voice="testvoice",
            model="timbre",
            tts_func=fake_tts,
        )
    )

    assert result.cached is True, "cached must be True when committed audio file exists"
    assert len(tts_called) == 0, "TTS synthesizer must not be called"
    assert result.name == name


def test_cache_dir_audio_returns_cached_no_tts(tmp_path, monkeypatch):
    """When data/cache/warnings/{name}.wav exists, get_warning returns cached=True
    without calling TTS."""
    audio_dir = tmp_path / "audio_empty"
    audio_dir.mkdir()
    cache_dir = tmp_path / "cache" / "warnings"
    cache_dir.mkdir(parents=True)

    wav_bytes = _make_tiny_wav()
    name = "warn_hi_in_generic_testvoice"
    (cache_dir / f"{name}.wav").write_bytes(wav_bytes)

    from backend import warning as w_mod

    monkeypatch.setattr(w_mod, "COMMITTED_AUDIO_DIR", audio_dir)
    monkeypatch.setattr(w_mod, "CACHE_DIR", cache_dir)

    tts_called = []

    async def fake_tts(**kwargs):
        tts_called.append(True)
        raise AssertionError("TTS should not be called when cache file exists")

    result = asyncio.run(
        w_mod.get_warning(
            lang="hi-IN",
            key="generic",
            voice="testvoice",
            model="timbre",
            tts_func=fake_tts,
        )
    )

    assert result.cached is True
    assert len(tts_called) == 0


def test_no_cache_calls_tts(tmp_path, monkeypatch):
    """When no committed or cached audio exists, get_warning invokes tts_func."""
    audio_dir = tmp_path / "audio_empty"
    audio_dir.mkdir()
    cache_dir = tmp_path / "cache" / "warnings"
    cache_dir.mkdir(parents=True)

    from backend import warning as w_mod

    monkeypatch.setattr(w_mod, "COMMITTED_AUDIO_DIR", audio_dir)
    monkeypatch.setattr(w_mod, "CACHE_DIR", cache_dir)

    class FakeTTSResult:
        audio = _make_tiny_wav()

    tts_called = []

    async def fake_tts(**kwargs):
        tts_called.append(True)
        return FakeTTSResult()

    result = asyncio.run(
        w_mod.get_warning(
            lang="hi-IN",
            key="generic",
            voice="testvoice",
            model="timbre",
            tts_func=fake_tts,
        )
    )

    assert len(tts_called) == 1, "TTS must be called when no audio exists"
    assert result.cached is False


def test_dry_run_skips_tts_write(tmp_path, monkeypatch):
    """dry_run=True returns WarningAudio(cached=False) without writing files."""
    audio_dir = tmp_path / "audio_empty"
    audio_dir.mkdir()
    cache_dir = tmp_path / "cache" / "warnings"
    cache_dir.mkdir(parents=True)

    from backend import warning as w_mod

    monkeypatch.setattr(w_mod, "COMMITTED_AUDIO_DIR", audio_dir)
    monkeypatch.setattr(w_mod, "CACHE_DIR", cache_dir)

    class FakeTTSResult:
        audio = b""

    async def fake_tts(**kwargs):
        return FakeTTSResult()

    result = asyncio.run(
        w_mod.get_warning(
            lang="hi-IN",
            key="generic",
            voice="testvoice",
            model="timbre",
            dry_run=True,
            tts_func=fake_tts,
        )
    )

    assert result.cached is False
    written = list(cache_dir.glob("*.wav"))
    assert len(written) == 0, "dry_run must not write any file"
