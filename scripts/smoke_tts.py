"""Smoke test script for Gnani Timbre TTS."""

import argparse
import asyncio
import io
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import soundfile as sf
from backend.gnani_tts import synthesize


def parse_args():
    parser = argparse.ArgumentParser(description="Smoke test for Gnani Timbre Text-to-Speech")
    parser.add_argument(
        "--text",
        default="नमस्ते, यह सावधान का एक छोटा परीक्षण है।",
        help="Text to synthesize",
    )
    parser.add_argument("--voice", default="Shivani", help="Voice name (default: Shivani)")
    parser.add_argument("--model", default="timbre-v3.0", help="Model name (default: timbre-v3.0)")
    parser.add_argument("--lang", default="hi-IN", help="Language code (default: hi-IN)")
    parser.add_argument(
        "--out",
        default="data/cache/smoke_tts.wav",
        help="Output audio path (default: data/cache/smoke_tts.wav)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned request without sending")
    return parser.parse_args()


async def main():
    args = parse_args()
    chars_sent = len(args.text)

    if args.dry_run:
        result = await synthesize(
            text=args.text,
            voice=args.voice,
            model=args.model,
            language=args.lang,
            dry_run=True,
        )
        print("=== DRY RUN MODE: Gnani Timbre TTS ===")
        print(f"Characters: {result.chars}")
        print("Planned Request:")
        print(json.dumps(result.audio, indent=2))
        return

    result = await synthesize(
        text=args.text,
        voice=args.voice,
        model=args.model,
        language=args.lang,
        dry_run=False,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(result.audio)

    bytes_recv = len(result.audio)
    try:
        with sf.SoundFile(io.BytesIO(result.audio)) as f:
            duration_s = round(len(f) / f.samplerate, 2)
    except Exception:
        duration_s = 0.0

    print("=== GNANI TIMBRE TTS SUCCESS ===")
    print(f"Characters sent: {chars_sent}")
    print(f"Bytes received: {bytes_recv}")
    print(f"Audio duration: {duration_s} s")
    print(f"Elapsed: {result.elapsed_ms} ms")
    print(f"Cached: {result.cached}")
    print(f"Output path: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
