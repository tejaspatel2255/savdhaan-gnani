"""Unit tests for audio utilities."""

import math
import shutil
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf

from backend.audio_utils import file_to_pcm, frames, rms_int16, pace_frames


def test_frames_padding_and_exact_size():
    """Verify that frames slices input into 1024-byte chunks and pads the last frame."""
    # 2500 bytes -> 1024, 1024, 452 (padded with 572 zeros to 1024)
    pcm = b"\x01" * 2500
    chunks = list(frames(pcm))
    assert len(chunks) == 3
    assert len(chunks[0]) == 1024
    assert len(chunks[1]) == 1024
    assert len(chunks[2]) == 1024
    assert chunks[2][:452] == b"\x01" * 452
    assert chunks[2][452:] == b"\x00" * (1024 - 452)


def test_frames_empty_input():
    """Empty pcm yields no frames."""
    assert list(frames(b"")) == []


def test_rms_int16_range_and_values():
    """Verify rms_int16 returns values in 0..1 for silence, half scale, and full scale."""
    # Silence
    silence = b"\x00" * 1024
    assert rms_int16(silence) == 0.0

    # Max constant amplitude: 32767 as int16
    arr_max = np.full(512, 32767, dtype=np.int16)
    rms_max = rms_int16(arr_max.tobytes())
    assert 0.99 <= rms_max <= 1.0

    # Half scale
    arr_half = np.full(512, 16384, dtype=np.int16)
    rms_half = rms_int16(arr_half.tobytes())
    assert 0.49 <= rms_half <= 0.51


def test_file_to_pcm_with_soundfile(tmp_path):
    """Create a short wav file with soundfile, then run file_to_pcm if ffmpeg is available."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")

    wav_path = tmp_path / "test_sine.wav"
    sample_rate = 16000
    # 0.2 seconds of silence/tone
    data = np.zeros(int(sample_rate * 0.2), dtype=np.int16)
    sf.write(str(wav_path), data, sample_rate)

    pcm_8k = file_to_pcm(wav_path, 8000)
    # 0.2s * 8000 samples/s * 2 bytes/sample = 3200 bytes
    assert len(pcm_8k) == 3200

    pcm_16k = file_to_pcm(wav_path, 16000)
    # 0.2s * 16000 samples/s * 2 bytes/sample = 6400 bytes
    assert len(pcm_16k) == 6400
