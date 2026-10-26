"""Replay a recorded transcript JSONL file at specified speed multiplier."""

import argparse
import json
import sys
import time
from pathlib import Path


def format_t(seconds: float) -> str:
    """Format seconds into [mm:ss.s]."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"[{mins:02d}:{secs:04.1f}]"


def parse_args():
    parser = argparse.ArgumentParser(description="Replay transcript file at scaled speed")
    parser.add_argument("path", help="Path to .jsonl transcript file")
    parser.add_argument("--speed", type=float, default=1.0, help="Replay speed multiplier (default: 1.0)")
    return parser.parse_args()


def main():
    args = parse_args()
    file_path = Path(args.path)
    if not file_path.exists():
        print(f"Error: Transcript file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if args.speed <= 0:
        print("Error: Speed must be greater than 0", file=sys.stderr)
        sys.exit(1)

    segments = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    segments.append(json.loads(line))
                except Exception:
                    pass

    if not segments:
        print(f"No transcript segments found in {file_path}")
        return

    print(f"=== Replaying {file_path.name} ({len(segments)} segments) at {args.speed}x speed ===")
    t_start = time.perf_counter()
    prev_t = 0.0

    for seg in segments:
        target_t = float(seg.get("t", 0.0))
        delay = (target_t - prev_t) / args.speed
        if delay > 0:
            time.sleep(delay)
        prev_t = target_t

        idx = seg.get("segment_index", 0)
        lat = seg.get("latency")
        lat_str = f"({lat} ms)" if lat is not None else ""
        text = seg.get("text", "")
        print(f"{format_t(target_t)} #{idx} {lat_str} {text}")

    print("=== Replay finished ===")


if __name__ == "__main__":
    main()
