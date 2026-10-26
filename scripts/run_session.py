"""CLI terminal client for testing a running Savdhaan session."""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict

import httpx
import websockets

# Ensure utf-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Terminal client for Savdhaan server")
    parser.add_argument("--mode", default="mock", choices=["mock", "replay", "file", "mic"], help="Mode (default: mock)")
    parser.add_argument("--call-id", default=None, help="Call ID for replay/file mode")
    parser.add_argument("--lang", default="hi-IN", help="Language code (default: hi-IN)")
    parser.add_argument("--speed", type=float, default=1.0, help="Replay/mock speed multiplier")
    parser.add_argument("--no-speak", action="store_true", help="Disable warning audio generation")
    parser.add_argument("--host", default="http://localhost:8000", help="Backend host URL")
    return parser.parse_args()


async def main():
    args = parse_args()
    base_url = args.host.rstrip("/")

    # 1. POST /api/session/start
    start_payload = {
        "mode": args.mode,
        "call_id": args.call_id,
        "lang": args.lang,
        "speed": args.speed,
        "speak_warning": not args.no_speak,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(f"{base_url}/api/session/start", json=start_payload)
        except Exception as e:
            print(f"Failed to connect to server at {base_url}: {e}", file=sys.stderr)
            sys.exit(1)

        if resp.status_code != 200:
            print(f"Start session failed ({resp.status_code}): {resp.text}", file=sys.stderr)
            sys.exit(1)

        session_id = resp.json()["session_id"]
        print(f"Session started: {session_id} (mode={args.mode}, speed={args.speed})")

    # 2. Connect to WebSocket /ws/ui
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/ui"

    async with websockets.connect(ws_url) as ws:
        async for raw_msg in ws:
            data = json.loads(raw_msg)
            msg_type = data.get("type", "")
            t_val = data.get("t", 0.0)
            prefix = f"t={t_val:5.1f} {msg_type:<14s}"

            if msg_type == "session":
                state = data.get("state")
                print(f"{prefix} state={state} mode={data.get('mode_label')}")

            elif msg_type == "audio_level":
                # Print occasionally or skip to keep terminal readable
                pass

            elif msg_type == "segment_processing":
                print(f"{prefix} ...")

            elif msg_type == "transcript":
                idx = data.get("segment_index")
                print(f"{prefix} #{idx} {data.get('text')}")

            elif msg_type == "risk":
                idx = data.get("segment_index")
                score = data.get("score")
                level = data.get("level")
                hits_str = " ".join(f"{h['rule_id']}({h['matched']})" for h in data.get("hits", []))
                print(f"{prefix} #{idx} score={score:3d} level={level:<7s} {hits_str}")

            elif msg_type == "alert":
                score = data.get("score")
                print(f"{prefix} *** ALERT FIRED score={score} ***")

            elif msg_type == "family_alert":
                print(f"{prefix} [FAMILY] {data.get('message')}")

            elif msg_type == "warning_audio":
                url = data.get("audio_url")
                cached = data.get("cached")
                reason = data.get("reason")
                print(f"{prefix} url={url} cached={cached} reason={reason}")

            elif msg_type == "error":
                print(f"{prefix} [ERROR] {data.get('code')}: {data.get('message')}")

            elif msg_type == "summary":
                print(f"{prefix} Final Summary:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                break


if __name__ == "__main__":
    asyncio.run(main())
