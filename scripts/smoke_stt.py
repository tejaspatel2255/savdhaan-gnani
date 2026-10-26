"""Smoke test script for Gnani Prisma STT."""

import argparse
import asyncio
import io
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import soundfile as sf
from backend.gnani_stt import transcribe_file


def parse_args():
    parser = argparse.ArgumentParser(description="Smoke test for Gnani Prisma Speech-to-Text")
    parser.add_argument(
        "--file",
        default="data/cache/smoke_tts.wav",
        help="Audio file path to transcribe (default: data/cache/smoke_tts.wav)",
    )
    parser.add_argument("--lang", default="hi-IN", help="Language code (default: hi-IN)")
    parser.add_argument("--fmt", default="verbatim", help="Format: verbatim or transcribe (default: verbatim)")
    parser.add_argument("--dry-run", action="store_true", help="Print planned request without sending")
    return parser.parse_args()


async def main():
    args = parse_args()
    audio_path = Path(args.file)

    if args.dry_run:
        # In dry run, check if file exists or provide mock duration for preview
        if not audio_path.exists():
            # Create a brief 1-second dummy wav file so soundfile can measure it in dry-run
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            import numpy as np
            sample_rate = 16000
            data = np.zeros(sample_rate, dtype=np.int16)
            sf.write(str(audio_path), data, sample_rate)

        result = await transcribe_file(
            path=audio_path,
            language_code=args.lang,
            fmt=args.fmt,
            dry_run=True,
        )
        print("=== DRY RUN MODE: Gnani Prisma STT ===")
        print(f"Audio duration: {result.seconds} s")
        print("Planned Request:")
        print(json.dumps(json.loads(result.transcript), indent=2))
        return

    result = await transcribe_file(
        path=audio_path,
        language_code=args.lang,
        fmt=args.fmt,
        dry_run=False,
    )

    print("=== GNANI PRISMA STT SUCCESS ===")
    print(f"Transcript: {result.transcript}")
    print(f"Request ID: {result.request_id}")
    print(f"Audio seconds: {result.seconds}")
    print(f"Elapsed: {result.elapsed_ms} ms")
    print(f"Cached: {result.cached}")


if __name__ == "__main__":
    asyncio.run(main())
