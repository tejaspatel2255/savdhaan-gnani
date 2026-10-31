"""Exports evaluation ledger and warning audios for static site deployment."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_RESULTS = ROOT / "data" / "eval" / "results.json"
CACHE_WARNINGS = ROOT / "data" / "cache" / "warnings"

ASSETS_DIR = ROOT / "frontend" / "assets"
TARGET_RESULTS = ASSETS_DIR / "results.json"
TARGET_AUDIO_DIR = ASSETS_DIR / "audio"


def export_static():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Export results.json
    if EVAL_RESULTS.exists():
        shutil.copy2(EVAL_RESULTS, TARGET_RESULTS)
        print(f"Copied {EVAL_RESULTS} -> {TARGET_RESULTS}")
    else:
        print(f"Notice: {EVAL_RESULTS} not found. Skipping results export.")

    # 2. Export warning audio files
    copied_audio = 0
    if CACHE_WARNINGS.exists():
        for wav_path in CACHE_WARNINGS.glob("*.wav"):
            target_path = TARGET_AUDIO_DIR / wav_path.name
            shutil.copy2(wav_path, target_path)
            copied_audio += 1
            print(f"Copied audio: {wav_path.name} -> {target_path}")

    if copied_audio == 0:
        print("Notice: No warning audios in data/cache/warnings/ to export (skipping audio copy).")
    else:
        print(f"Exported {copied_audio} warning audio files to {TARGET_AUDIO_DIR}.")

    # 3. Export audio manifest
    manifest_data = {"languages": {}}
    for lang_code, prefix in [("hi-IN", "warn_hi_in_"), ("gu-IN", "warn_gu_in_"), ("en-IN", "warn_en_in_")]:
        files = [p.name for p in TARGET_AUDIO_DIR.glob(f"{prefix}*.wav")]
        manifest_data["languages"][lang_code] = {
            "has_voice": len(files) > 0,
            "files": sorted(files),
        }
    manifest_path = TARGET_AUDIO_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"Generated audio manifest at {manifest_path}")

    print("Static export complete.")


if __name__ == "__main__":
    export_static()
