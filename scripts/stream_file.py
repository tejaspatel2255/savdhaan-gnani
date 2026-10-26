"""Stream an audio file through Gnani Realtime STT and record events."""

import argparse
import asyncio
import json
import logging
import math
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.audio_utils import file_to_pcm, frames
from backend.config import settings
from backend.gnani_stream import (
    Connected,
    Processing,
    StreamError,
    Transcript,
    build_headers,
    stream_call,
)
from backend import usage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stream_file")


def format_t(seconds: float) -> str:
    """Format seconds into [mm:ss.s]."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"[{mins:02d}:{secs:04.1f}]"


def parse_args():
    parser = argparse.ArgumentParser(description="Stream audio file to Gnani Realtime STT")
    parser.add_argument("--file", required=True, help="Path to input audio file")
    parser.add_argument("--lang", default="hi-IN", help="Language code (default: hi-IN)")
    parser.add_argument("--rate", type=int, choices=[8000, 16000], default=8000, help="Sample rate (8000 or 16000)")
    parser.add_argument("--name", default=None, help="Name for recorded transcript (default: file stem)")
    parser.add_argument("--dry-run", action="store_true", help="Print streaming plan and headers without sending")
    return parser.parse_args()


def main():
    args = parse_args()
    input_file = Path(args.file)
    if not input_file.exists():
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    name = args.name if args.name else input_file.stem

    # Convert audio to raw PCM at specified rate
    try:
        pcm = file_to_pcm(input_file, args.rate)
    except Exception as exc:
        print(f"Audio conversion failed: {exc}", file=sys.stderr)
        sys.exit(1)

    frame_list = list(frames(pcm))
    frame_count = len(frame_list)
    audio_seconds = round(len(pcm) / (2.0 * float(args.rate)), 2)

    headers = build_headers(
        api_key=settings.api_key,
        lang=args.lang,
        rate=args.rate,
        fmt="verbatim",
    )
    # Mask key for dry-run/preview
    masked_headers = dict(headers)
    masked_headers["x-api-key-id"] = "***MASKED***" if settings.key_present else "EMPTY"

    print("=== STREAMING PLAN ===")
    print(f"File: {input_file}")
    print(f"Duration: {audio_seconds:.2f} s")
    print(f"Sample Rate: {args.rate} Hz")
    print(f"Frame Count: {frame_count} frames (1024 bytes each)")
    print(f"Estimated Charged Audio: {audio_seconds:.2f} s")
    print("Planned Upgrade Headers:")
    print(json.dumps(masked_headers, indent=2))

    if args.dry_run:
        print("Dry run complete: no network calls made.")
        return

    asyncio.run(run_stream(args, pcm, name))


async def run_stream(args, pcm: bytes, name: str):
    # Real streaming
    out_dir = Path("data/transcripts")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{name}.jsonl"

    latencies = []
    recorded_segments = []
    t_start = time.perf_counter()

    def on_event(ev):
        if isinstance(ev, Processing):
            print(f"{format_t(ev.t)} processing")
        elif isinstance(ev, Transcript):
            lat_str = f"({ev.latency} ms)" if ev.latency is not None else "(latency n/a)"
            print(f"{format_t(ev.t)} #{ev.segment_index} {lat_str} {ev.text}")
            if ev.latency is not None:
                latencies.append(ev.latency)

            # Record in docs/EVENTS.md format
            record = {
                "t": ev.t,
                "segment_index": ev.segment_index,
                "segment_id": ev.segment_id,
                "text": ev.text,
                "audio_duration_ms": ev.audio_duration_ms,
                "latency": ev.latency,
            }
            recorded_segments.append(record)
        elif isinstance(ev, StreamError):
            print(f"{format_t(ev.t)} error: {ev.message}")

    print(f"\n--- Streaming audio to wss://api.vachana.ai/stt/v3/stream ---")
    try:
        await stream_call(
            pcm,
            lang=args.lang,
            rate=args.rate,
            settings=settings,
            on_event=on_event,
        )
    except Exception as exc:
        print(f"Streaming error: {exc}", file=sys.stderr)
        sys.exit(1)

    wall_clock = time.perf_counter() - t_start

    # Write recorded transcript lines
    with open(out_file, "w", encoding="utf-8") as f:
        for r in recorded_segments:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Compute p50 and p95 latency
    p50 = None
    p95 = None
    if latencies:
        sorted_lat = sorted(latencies)
        idx_50 = int(len(sorted_lat) * 0.50)
        idx_95 = min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)
        p50 = sorted_lat[idx_50]
        p95 = sorted_lat[idx_95]

    ledger_data = usage.read()

    print("\n=== STREAM SUMMARY ===")
    print(f"Segments received: {len(recorded_segments)}")
    print(f"STT Latency (ms): p50={p50}, p95={p95}")
    print(f"Wall-clock elapsed: {wall_clock:.2f} s")
    print(f"Transcript saved: {out_file}")
    print(f"Usage ledger totals: {ledger_data.get('lifetime', {})}")


if __name__ == "__main__":
    main()
