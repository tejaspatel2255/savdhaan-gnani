"""CLI tool to degrade existing clean call audio files into telephone variants."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path so scripts / backend modules can be imported
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import soundfile as sf
import numpy as np

from scripts.audio_fx import apply_conditions


def measure_snr(signal: np.ndarray, noisy: np.ndarray) -> float:
    """Measure SNR in dB between clean/reference and noisy signals."""
    noise = noisy - signal
    p_sig = np.mean(signal ** 2)
    p_noise = np.mean(noise ** 2)
    if p_noise <= 1e-12:
        return 999.0
    return float(10.0 * np.log10(p_sig / p_noise))


def main() -> None:
    parser = argparse.ArgumentParser(description="Degrade clean call audio to phone conditions")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="Single call id to process")
    group.add_argument("--all", action="store_true", help="Process all clean calls in data/calls")
    parser.add_argument("--calls-dir", default="data/calls", help="Directory containing calls")
    args = parser.parse_args()

    calls_dir = Path(args.calls_dir)
    if not calls_dir.exists():
        print(f"Directory {calls_dir} does not exist.")
        sys.exit(1)

    if args.id:
        clean_files = list(calls_dir.glob(f"{args.id}__clean.wav"))
        if not clean_files:
            print(f"Error: {args.id}__clean.wav not found in {calls_dir}")
            sys.exit(1)
    else:
        clean_files = sorted(list(calls_dir.glob("*__clean.wav")))
        if not clean_files:
            print(f"No *__clean.wav files found in {calls_dir}")
            return

    for clean_path in clean_files:
        call_id = clean_path.name.replace("__clean.wav", "")
        variants = apply_conditions(clean_path, calls_dir, call_id)
        print(f"=== Call: {call_id} ===")
        for cond, path in variants.items():
            info = sf.info(path)
            extra = ""
            if cond == "phone_noise":
                phone_data, _ = sf.read(variants["phone"])
                noise_data, _ = sf.read(path)
                snr = measure_snr(phone_data, noise_data)
                extra = f" (measured SNR: {snr:.1f} dB)"
            print(f"  {cond:18s}: {info.duration:.2f}s, {info.samplerate}Hz, {info.channels}ch{extra}")


if __name__ == "__main__":
    main()
