"""Telephone audio effects and degradation functions."""

import hashlib
import io
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Union
import numpy as np
import soundfile as sf

CONDITIONS: List[str] = ["clean", "phone", "phone_noise", "phone_noise_drops"]


def _make_seed(call_id: str, condition: str) -> int:
    """Deterministic integer seed from sha256 of call_id and condition."""
    h = hashlib.sha256(f"{call_id}_{condition}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def to_phone(in_wav: Union[str, Path], out_wav: Union[str, Path]) -> None:
    """Apply telephone bandpass filter and mu-law codec roundtrip via ffmpeg.

    Filter: highpass 300 Hz, lowpass 3400 Hz, mono, 8000 Hz, mu-law encode & decode, 16-bit PCM output.
    """
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found in PATH")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(in_wav),
        "-af", "highpass=f=300,lowpass=f=3400",
        "-ac", "1",
        "-ar", "8000",
        "-c:a", "pcm_mulaw",
        "-f", "wav",
        "pipe:1"
    ]
    p1 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    cmd2 = [
        ffmpeg_bin,
        "-y",
        "-i", "pipe:0",
        "-c:a", "pcm_s16le",
        "-ar", "8000",
        "-ac", "1",
        str(out_wav)
    ]
    subprocess.run(cmd2, input=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def add_noise(x: np.ndarray, rate: int, snr_db: float, seed: int) -> np.ndarray:
    """Add synthetic street noise (brown noise + 50 Hz hum) at specified SNR dB.

    Speech power is calculated over the louder half of 20 ms frames.
    """
    rng = np.random.default_rng(seed)
    n_samples = len(x)
    if n_samples == 0:
        return x.copy()

    # Brown noise: cumulative sum of white noise, normalized
    white = rng.standard_normal(n_samples)
    brown = np.cumsum(white)
    # Remove DC offset
    brown = brown - np.mean(brown)
    b_max = np.max(np.abs(brown))
    if b_max > 0:
        brown = brown / b_max

    # 50 Hz hum
    t = np.arange(n_samples) / float(rate)
    hum = 0.05 * np.sin(2.0 * np.pi * 50.0 * t)
    raw_noise = brown + hum

    # Measure speech power over the louder half of 20ms frames
    frame_len = max(1, int(rate * 0.020))
    n_frames = n_samples // frame_len
    if n_frames > 0:
        trimmed = x[:n_frames * frame_len]
        frames = trimmed.reshape((n_frames, frame_len))
        powers = np.mean(frames ** 2, axis=1)
        median_pow = np.median(powers)
        louder_powers = powers[powers >= median_pow]
        speech_power = float(np.mean(louder_powers)) if len(louder_powers) > 0 else float(np.mean(powers))
    else:
        speech_power = float(np.mean(x ** 2))

    if speech_power <= 1e-12:
        return x.copy()

    target_noise_power = speech_power / (10.0 ** (snr_db / 10.0))
    current_noise_power = float(np.mean(raw_noise ** 2))
    if current_noise_power > 0:
        scale = np.sqrt(target_noise_power / current_noise_power)
        scaled_noise = raw_noise * scale
    else:
        scaled_noise = raw_noise

    y = x + scaled_noise
    return y


def drop_packets(x: np.ndarray, rate: int, n: int, drop_ms: float, seed: int) -> np.ndarray:
    """Zero n windows of drop_ms at random positions, never in the first or last 0.5 s."""
    rng = np.random.default_rng(seed)
    y = x.copy()
    n_samples = len(y)
    margin = int(rate * 0.5)
    drop_len = int(rate * (drop_ms / 1000.0))

    if n_samples <= 2 * margin + drop_len:
        return y

    start_min = margin
    start_max = n_samples - margin - drop_len

    for _ in range(n):
        idx = int(rng.integers(start_min, start_max + 1))
        y[idx : idx + drop_len] = 0.0

    return y


def apply_conditions(
    clean_wav: Union[str, Path],
    out_dir: Union[str, Path],
    call_id: str,
) -> dict[str, str]:
    """Generate all 4 audio variants for a given call."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_dst = out_dir / f"{call_id}__clean.wav"
    if Path(clean_wav).resolve() != clean_dst.resolve():
        shutil.copyfile(clean_wav, clean_dst)

    phone_dst = out_dir / f"{call_id}__phone.wav"
    phone_noise_dst = out_dir / f"{call_id}__phone_noise.wav"
    phone_noise_drops_dst = out_dir / f"{call_id}__phone_noise_drops.wav"

    # Step 1: to_phone
    to_phone(clean_dst, phone_dst)

    # Step 2: phone_noise
    data_phone, rate = sf.read(str(phone_dst), dtype="float32")
    seed_noise = _make_seed(call_id, "phone_noise")
    data_noise = add_noise(data_phone, rate, snr_db=15.0, seed=seed_noise)
    sf.write(str(phone_noise_dst), data_noise, rate, subtype="PCM_16")

    # Step 3: phone_noise_drops
    seed_drops = _make_seed(call_id, "phone_noise_drops")
    data_drops = drop_packets(data_noise, rate, n=4, drop_ms=60.0, seed=seed_drops)
    sf.write(str(phone_noise_drops_dst), data_drops, rate, subtype="PCM_16")

    return {
        "clean": str(clean_dst),
        "phone": str(phone_dst),
        "phone_noise": str(phone_noise_dst),
        "phone_noise_drops": str(phone_noise_drops_dst),
    }
