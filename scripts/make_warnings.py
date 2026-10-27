"""Pre-generate and cache spoken warning audio files."""

import argparse
import asyncio
import io
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Ensure utf-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.config import settings
from backend.warning import WARNINGS, get_warning


def parse_args():
    parser = argparse.ArgumentParser(description="Generate and cache spoken warning audio")
    parser.add_argument(
        "--lang",
        default="hi-IN",
        choices=["hi-IN", "en-IN", "gu-IN", "all"],
        help="Language code or 'all' (default: hi-IN)"
    )
    parser.add_argument(
        "--only",
        choices=["generic", "arrest", "otp", "money", "remote"],
        default=None,
        help="Generate only one specific warning key"
    )
    parser.add_argument(
        "--go",
        action="store_true",
        help="Actually call TTS API to generate and cache audio (spends credits)"
    )
    return parser.parse_args()


def process_language(lang: str, only_key: str, go: bool):
    lang_dict = WARNINGS.get(lang, WARNINGS["hi-IN"])
    keys = [only_key] if only_key else list(lang_dict.keys())
    total_chars = sum(len(lang_dict[k]) for k in keys)

    print(f"\n=== Warning Audio Preparation ({lang}) ===")
    print(f"Target Voice: {settings.warning_voice}")
    print(f"Target Model: {settings.warning_model}")
    print(f"Total Warnings: {len(keys)}")
    print(f"Total Characters: {total_chars} (Cap: {settings.max_tts_chars_per_run})")
    print(f"Mode: {'LIVE GENERATION (--go)' if go else 'DRY RUN'}\n")

    if not go:
        print("Planned Warnings (Dry Run):")
        for k in keys:
            text = lang_dict[k]
            print(f"  [{k:<8s}] ({len(text)} chars): {text}")
        print("Dry run complete for this language. No credits spent.")
        return

    asyncio.run(generate_warnings(keys, lang_dict, lang))


async def generate_warnings(keys, lang_dict, lang):
    for k in keys:
        text = lang_dict[k]
        chars = len(text)
        try:
            res = await get_warning(
                lang=lang,
                key=k,
                voice=settings.warning_voice,
                model=settings.warning_model,
                dry_run=False,
            )
            status_str = "CACHED" if res.cached else "GENERATED"
            print(f"  [{k:<8s}] {status_str} ({chars} chars, {res.duration_s}s): {res.url}")
        except Exception as e:
            print(f"  [{k:<8s}] FAILED ({chars} chars): {e}")

    print(f"Warning audio preparation for {lang} complete.")


def main():
    args = parse_args()
    langs_to_process = ["hi-IN", "en-IN", "gu-IN"] if args.lang == "all" else [args.lang]

    for l in langs_to_process:
        process_language(l, args.only, args.go)


if __name__ == "__main__":
    main()
