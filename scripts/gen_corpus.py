"""Generate synthetic call audio corpus using Gnani Timbre and audio effects."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path so backend modules can be imported when running script directly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Dict, List, Optional

from backend.config import settings
from backend.gnani_tts import is_cached, synthesize
from scripts.audio_fx import apply_conditions
from scripts.corpus_lib import Call, build_call, load_scripts

SCRIPT_PATHS = [
    Path("data/scripts/dev_calls.json"),
    Path("data/scripts/test_calls.json"),
]
BLIND_SCRIPT_PATH = Path("data/scripts/blind_calls.json")


def load_manifest(manifest_path: Path) -> List[dict]:
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def save_manifest(manifest_path: Path, entries: List[dict]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    entries_sorted = sorted(entries, key=lambda x: x["id"])
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(entries_sorted, f, indent=2, ensure_ascii=False)


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic call audio corpus")
    parser.add_argument("--split", choices=["dev", "test", "blind", "all"], default="all")
    parser.add_argument("--ids", help="Comma-separated call IDs to process")
    parser.add_argument("--go", action="store_true", help="Execute real generation (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry-run mode (default)")
    parser.add_argument("--calls-dir", default="data/calls")
    args = parser.parse_args()

    if args.split == "blind":
        if not BLIND_SCRIPT_PATH.exists():
            print(f"Error: Blind script file {BLIND_SCRIPT_PATH} not found.")
            return
        calls = load_scripts([BLIND_SCRIPT_PATH])
    else:
        calls = load_scripts(SCRIPT_PATHS)
        if args.split != "all":
            calls = [c for c in calls if c.split == args.split]

    # Filter by ids
    if args.ids:
        selected_ids = {i.strip() for i in args.ids.split(",") if i.strip()}
        calls = [c for c in calls if c.id in selected_ids]

    if not calls:
        print("No calls selected.")
        return

    calls_dir = Path(args.calls_dir)
    calls_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = calls_dir / "manifest.json"

    # Compute character counts per call
    print(f"{'CALL ID':26s} {'SPLIT':5s} {'TOTAL CHARS':11s} {'CACHED':7s} {'NEW CHARS':9s}")
    print("-" * 65)

    tot_chars = 0
    tot_cached = 0
    tot_new = 0

    call_stats = []

    for call in calls:
        c_chars = 0
        c_cached = 0
        for speaker, text in call.turns:
            t_len = len(text)
            c_chars += t_len
            voice = call.caller_voice if speaker == "C" else call.listener_voice
            if is_cached(text, voice=voice, model=settings.warning_model, language=call.lang):
                c_cached += t_len
        c_new = c_chars - c_cached
        tot_chars += c_chars
        tot_cached += c_cached
        tot_new += c_new
        call_stats.append((call, c_chars, c_cached, c_new))
        print(f"{call.id:26s} {call.split:5s} {c_chars:11d} {c_cached:7d} {c_new:9d}")

    print("-" * 65)
    print(f"{'TOTALS':26s} {'':5s} {tot_chars:11d} {tot_cached:7d} {tot_new:9d}")

    if settings.tts_credits_per_1k_chars is not None:
        est_credits = (tot_new / 1000.0) * settings.tts_credits_per_1k_chars
        print(f"Estimated credit cost: {est_credits:.2f} credits (@ {settings.tts_credits_per_1k_chars}/1k chars)")

    if not args.go:
        print("\nDry run complete. Use --go to generate audio.")
        return

    # Check MAX_TTS_CHARS_PER_RUN cap
    cap = settings.max_tts_chars_per_run
    if tot_new > cap:
        print(f"This run needs {tot_new} new characters but MAX_TTS_CHARS_PER_RUN is {cap}. If you accept the cost, set MAX_TTS_CHARS_PER_RUN={tot_new} in .env and run again.")
        sys.exit(1)

    # Real generation
    print("\nGenerating calls...")
    existing_manifest = load_manifest(manifest_path)
    manifest_by_id = {item["id"]: item for item in existing_manifest}

    for call, _, _, _ in call_stats:
        print(f"Building {call.id}...")
        built = await build_call(
            call=call,
            tts=synthesize,
            out_dir=calls_dir,
            model=settings.warning_model,
            language=call.lang,
        )
        variants = apply_conditions(built.clean_path, calls_dir, call.id)

        manifest_by_id[call.id] = {
            "id": call.id,
            "title": call.title,
            "label": call.label,
            "lang": call.lang,
            "split": call.split,
            "script_path": call.script_path,
            "audio_path": variants["phone_noise"],
            "noise": "phone_noise snr 15 dB",
            "duration_s": built.duration_s,
            "first_cue_s": built.first_cue_s,
            "variants": variants,
            "voices": {
                "caller": call.caller_voice,
                "listener": call.listener_voice,
            },
            "chars": built.chars,
        }

    save_manifest(manifest_path, list(manifest_by_id.values()))
    print(f"Manifest saved with {len(manifest_by_id)} entries to {manifest_path}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
