"""Unit and integration tests for Phase 6 synthetic call corpus."""

import asyncio
import io
import json
import shutil
from pathlib import Path
import pytest
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.gnani_tts import TtsResult, is_cached
from backend.scorer import ScamScorer, load_pack
from scripts.audio_fx import add_noise, drop_packets, to_phone, apply_conditions
from scripts.corpus_lib import assemble, build_call, load_scripts, Call

DEV_SCRIPT_PATH = Path("data/scripts/dev_calls.json")
TEST_SCRIPT_PATH = Path("data/scripts/test_calls.json")


def make_dummy_tts(rate: int = 24000):
    async def dummy_synthesize(text, voice, model, language, sample_rate=24000, **kwargs):
        duration_s = max(0.1, len(text) * 0.05)
        n_samples = int(duration_s * sample_rate)
        t = np.linspace(0, duration_s, n_samples, endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
        buf = io.BytesIO()
        sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16")
        return TtsResult(audio=buf.getvalue(), cached=False, chars=len(text), elapsed_ms=10)
    return dummy_synthesize


# 1. Script validation & character counts
def test_scripts_validation_and_turn_counts():
    calls = load_scripts([DEV_SCRIPT_PATH, TEST_SCRIPT_PATH])
    assert len(calls) == 20
    dev_calls = [c for c in calls if c.split == "dev"]
    test_calls = [c for c in calls if c.split == "test"]

    assert len(dev_calls) == 10
    assert len(test_calls) == 10

    assert sum(1 for c in dev_calls if c.label == "scam") == 5
    assert sum(1 for c in dev_calls if c.label == "legit") == 5
    assert sum(1 for c in test_calls if c.label == "scam") == 5
    assert sum(1 for c in test_calls if c.label == "legit") == 5

    for c in calls:
        assert 3 <= len(c.turns) <= 9
        chars = sum(len(t[1]) for t in c.turns)
        assert chars <= 400


def test_script_character_totals():
    dev_calls = load_scripts([DEV_SCRIPT_PATH])
    test_calls = load_scripts([TEST_SCRIPT_PATH])

    dev_chars = sum(sum(len(t[1]) for t in c.turns) for c in dev_calls)
    test_chars = sum(sum(len(t[1]) for t in c.turns) for c in test_calls)

    assert dev_chars == 2032
    assert test_chars == 2151
    assert dev_chars + test_chars == 4183


# 2. Text-level sanity
def test_text_level_sanity_dev_split():
    dev_calls = load_scripts([DEV_SCRIPT_PATH])
    pack = load_pack("rules/scam_rules_hi_en.json")

    for c in dev_calls:
        scorer = ScamScorer(pack, careful=30, danger=60)
        fired_alert = False
        for idx, (spk, text) in enumerate(c.turns):
            up = scorer.feed(text, segment_index=idx)
            if up.alert:
                fired_alert = True

        if c.label == "scam":
            assert fired_alert is True, f"Scam call {c.id} did not fire alert"
        else:
            assert fired_alert is False, f"Legit call {c.id} fired unexpected alert"


# 3. Audio assembly & build_call
def test_assemble_timelines_and_first_cue():
    rate = 16000
    a1 = np.ones(int(rate * 1.0), dtype=np.float32)  # 1.0s
    a2 = np.ones(int(rate * 2.0), dtype=np.float32)  # 2.0s
    assembled, timeline, first_cue_s = assemble([a1, a2], rate, cue_turn=1)

    # 0.4s + 1.0s + 0.7s + 2.0s + 1.0s = 5.1s
    assert len(assembled) == int(5.1 * rate)
    assert len(timeline) == 2
    # Turn 0: 0.4s to 1.4s
    assert timeline[0] == (0, 0.4, 1.4)
    # Turn 1: 0.4 + 1.0 + 0.7 = 2.1s to 4.1s
    assert timeline[1] == (1, 2.1, 4.1)
    assert first_cue_s == 2.1


def test_build_call_creates_24k_mono_file(tmp_path):
    async def run():
        call = Call(
            id="C_test",
            title="Test Call",
            label="scam",
            lang="hi-IN",
            split="dev",
            cue_turn=0,
            caller_voice="Avinash",
            listener_voice="Chetana",
            turns=[("C", "नमस्ते"), ("L", "हाँ कहिए")],
        )
        tts = make_dummy_tts(24000)
        built = await build_call(call, tts, tmp_path)

        clean_file = Path(built.clean_path)
        assert clean_file.exists()
        info = sf.info(str(clean_file))
        assert info.samplerate == 24000
        assert info.channels == 1
        assert built.duration_s > 0
        assert built.first_cue_s == 0.4
    asyncio.run(run())


# 4. Telephone effect and degradation
def test_to_phone_filter_frequency_response(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not found in PATH")

    rate = 24000
    n_samples = int(rate * 2.0)
    rng = np.random.default_rng(123)
    white_noise = rng.standard_normal(n_samples).astype(np.float32)
    in_wav = tmp_path / "white.wav"
    out_wav = tmp_path / "phone.wav"
    sf.write(str(in_wav), white_noise, rate, subtype="PCM_16")

    to_phone(in_wav, out_wav)
    assert out_wav.exists()
    filtered, f_rate = sf.read(str(out_wav))
    assert f_rate == 8000

    # FFT analysis
    fft_in = np.abs(np.fft.rfft(white_noise[:rate]))
    fft_out = np.abs(np.fft.rfft(filtered[:8000]))

    freqs_out = np.fft.rfftfreq(8000, 1.0 / 8000)
    passband = (freqs_out >= 500) & (freqs_out <= 3000)
    pb_level = np.mean(fft_out[passband] ** 2)

    # Below 250 Hz at least 10 dB lower
    lowband = (freqs_out < 250) & (freqs_out > 20)
    low_level = np.mean(fft_out[lowband] ** 2) if np.any(lowband) else 1e-12
    diff_low_db = 10.0 * np.log10(pb_level / max(1e-12, low_level))
    assert diff_low_db >= 10.0

    # Above 3.6 kHz at least 6 dB lower
    highband = (freqs_out >= 3600)
    high_level = np.mean(fft_out[highband] ** 2) if np.any(highband) else 1e-12
    diff_high_db = 10.0 * np.log10(pb_level / max(1e-12, high_level))
    assert diff_high_db >= 6.0


def test_add_noise_snr_accuracy_and_determinism():
    rate = 8000
    n = int(rate * 2.0)
    t = np.linspace(0, 2.0, n)
    signal = 0.5 * np.sin(2 * np.pi * 500.0 * t).astype(np.float32)

    noisy1 = add_noise(signal, rate, snr_db=15.0, seed=42)
    noisy2 = add_noise(signal, rate, snr_db=15.0, seed=42)
    noisy3 = add_noise(signal, rate, snr_db=15.0, seed=99)

    # Determinism
    np.testing.assert_array_equal(noisy1, noisy2)
    # Different seed produces different noise
    assert not np.array_equal(noisy1, noisy3)

    # SNR measurement within 2 dB
    noise = noisy1 - signal
    measured_snr = 10.0 * np.log10(np.mean(signal ** 2) / np.mean(noise ** 2))
    assert abs(measured_snr - 15.0) <= 2.0


def test_drop_packets_position_and_count():
    rate = 8000
    n_samples = int(rate * 3.0)  # 3 seconds
    signal = np.ones(n_samples, dtype=np.float32)

    dropped = drop_packets(signal, rate, n=4, drop_ms=60.0, seed=123)

    # Never inside first or last 0.5s
    margin = int(rate * 0.5)
    assert np.all(dropped[:margin] == 1.0)
    assert np.all(dropped[-margin:] == 1.0)

    # Exactly 4 drops of 60ms (480 samples each)
    zero_samples = np.sum(dropped == 0.0)
    expected_zero = 4 * int(rate * 0.060)
    assert zero_samples == expected_zero


def test_apply_conditions_generates_4_variants(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not found in PATH")

    rate = 24000
    clean_wav = tmp_path / "test__clean.wav"
    audio = np.ones(int(rate * 2.0), dtype=np.float32)
    sf.write(str(clean_wav), audio, rate, subtype="PCM_16")

    variants = apply_conditions(clean_wav, tmp_path, "test")
    assert len(variants) == 4
    for cond in ("clean", "phone", "phone_noise", "phone_noise_drops"):
        fpath = Path(variants[cond])
        assert fpath.exists()
        info = sf.info(str(fpath))
        if cond == "clean":
            assert info.samplerate == 24000
        else:
            assert info.samplerate == 8000
        # Duration within 50ms of clean
        assert abs(info.duration - 2.0) <= 0.05


# 5. Dry run, caching, and manifest integration
def test_is_cached_returns_false_when_absent():
    assert is_cached("Non existent text 123456", voice="Avinash", model="timbre-v3.0", language="hi-IN") is False


def test_manifest_merge_preserves_unselected_calls(tmp_path):
    from scripts.gen_corpus import load_manifest, save_manifest
    m_path = tmp_path / "manifest.json"
    initial_entries = [{"id": "D01", "title": "D01"}]
    save_manifest(m_path, initial_entries)

    loaded = load_manifest(m_path)
    loaded.append({"id": "D02", "title": "D02"})
    save_manifest(m_path, loaded)

    reloaded = load_manifest(m_path)
    assert len(reloaded) == 2
    assert reloaded[0]["id"] == "D01"
    assert reloaded[1]["id"] == "D02"


def test_api_calls_includes_manifest_calls_with_file_mode(tmp_path, monkeypatch):
    from backend.main import app
    calls_dir = tmp_path / "data" / "calls"
    calls_dir.mkdir(parents=True, exist_ok=True)
    mock_dir = tmp_path / "data" / "mock"
    mock_dir.mkdir(parents=True, exist_ok=True)
    (mock_dir / "mock_call.json").write_text('{"title":"test","lang":"hi-IN","segments":[]}', encoding="utf-8")

    m_path = calls_dir / "manifest.json"

    dummy_wav = calls_dir / "D01.wav"
    sf.write(str(dummy_wav), np.zeros(8000, dtype=np.int16), 8000)

    manifest_data = [{
        "id": "D01",
        "title": "Digital arrest test",
        "label": "scam",
        "lang": "hi-IN",
        "duration_s": 15.0,
        "audio_path": str(dummy_wav)
    }]
    with open(m_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/calls")
    assert resp.status_code == 200
    data = resp.json()
    c_entry = next((c for c in data["calls"] if c["id"] == "D01"), None)
    assert c_entry is not None
    assert "file" in c_entry["modes"]
