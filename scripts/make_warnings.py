"""Pre-generate and cache spoken warning audio files."""

import argparse
import asyncio
import io
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure utf-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.config import settings
from backend.warning import WARNINGS, get_warning


def parse_args():
    parser = argparse.ArgumentParser(description="Generate and cache spoken warning audio")
    parser.add_argument("--lang", default="hi-IN", choices=["hi-IN", "en-IN"], help="Language code (default: hi-IN)")
    parser.add_argument("--only", choices=["generic", "arrest", "otp", "money", "remote"], default=None, help="Generate only one specific warning key")
    parser.add_argument("--dry-run", action="store_true", help="Print plan and character counts without calling TTS API")
    return parser.parse_args()


def main():
    args = parse_args()
    lang = args.lang
    lang_dict = WARNINGS.get(lang, WARNINGS["hi-IN"])

    keys = [args.only] if args.only else list(lang_dict.keys())

    total_chars = sum(len(lang_dict[k]) for k in keys)

    print(f"=== Warning Audio Generation ({lang}) ===")
    print(f"Target Voice: {settings.warning_voice}")
    print(f"Target Model: {settings.warning_model}")
    print(f"Total Warnings: {len(keys)}")
    print(f"Total Characters: {total_chars}")
    print(f"Dry Run: {args.dry_run}\n")

    if args.dry_run:
        print("Planned Warnings:")
        for k in keys:
            text = lang_dict[k]
            print(f"  [{k:<8s}] ({len(text)} chars): {text}")
        print("\nDry run complete. No credits spent.")
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

    print("\nWarning audio preparation complete.")


if __name__ == "__main__":
    main()
