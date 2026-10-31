"""Reconcile usage ledger with disk warnings, manual additions, and dashboard balance."""

import argparse
import datetime
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

DEFAULT_LEDGER = Path("data/usage_ledger.json")


def read_ledger(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "lifetime": {"tts_chars": 0, "stt_seconds": 0.0},
            "history": [],
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("lifetime", {"tts_chars": 0, "stt_seconds": 0.0})
            data.setdefault("history", [])
            return data
    except Exception:
        return {
            "lifetime": {"tts_chars": 0, "stt_seconds": 0.0},
            "history": [],
        }


def write_ledger(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tf = tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8")
    try:
        json.dump(data, tf, indent=2)
        tf.flush()
        os.fsync(tf.fileno())
        tf.close()
        os.replace(tf.name, path)
    except Exception:
        if os.path.exists(tf.name):
            os.remove(tf.name)
        raise


def add_manual_usage(path: Path, tts_chars: int = 0, stt_sec: float = 0.0, reason: str = "") -> Dict[str, Any]:
    if not reason:
        raise ValueError("A --reason is required for manual usage additions.")
    data = read_ledger(path)
    entry = {
        "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "type": "manual",
        "tts_chars": tts_chars,
        "stt_seconds": round(stt_sec, 2),
        "reason": reason,
    }
    data["history"].append(entry)
    data["lifetime"]["tts_chars"] = data["lifetime"].get("tts_chars", 0) + tts_chars
    data["lifetime"]["stt_seconds"] = round(data["lifetime"].get("stt_seconds", 0.0) + stt_sec, 2)
    write_ledger(path, data)
    return data


def add_dashboard_observation(path: Path, balance: float, note: str = "") -> Dict[str, Any]:
    data = read_ledger(path)
    entry = {
        "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "type": "dashboard_observation",
        "balance": balance,
        "note": note,
    }
    data["history"].append(entry)
    # Does not change lifetime totals
    write_ledger(path, data)
    return data


def show_summary(path: Path) -> None:
    data = read_ledger(path)
    life = data.get("lifetime", {})
    hist = data.get("history", [])
    print("=" * 60)
    print("SAVDHAAN USAGE LEDGER RECONCILIATION")
    print("=" * 60)
    print(f"Ledger file: {path}")
    print(f"Lifetime TTS characters: {life.get('tts_chars', 0):,}")
    print(f"Lifetime STT seconds:    {life.get('stt_seconds', 0.0):.2f}s")
    print(f"History entries:         {len(hist)}")
    print("-" * 60)
    for i, h in enumerate(hist[-10:], 1):
        htype = h.get("type", "run")
        dt = h.get("date", "")[:19]
        if htype == "manual":
            print(f"[{dt}] MANUAL: +{h.get('tts_chars', 0)} chars, +{h.get('stt_seconds', 0.0)}s | Reason: {h.get('reason')}")
        elif htype == "dashboard_observation":
            print(f"[{dt}] DASHBOARD BALANCE: {h.get('balance')} credits | Note: {h.get('note')}")
        else:
            print(f"[{dt}] {htype}: {h.get('tts_chars', 0)} chars, {h.get('stt_seconds', 0.0)}s")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Reconcile and manage Savdhaan usage ledger")
    parser.add_argument("--show", action="store_true", help="Print lifetime totals and recent history")
    parser.add_argument("--add-tts-chars", type=int, default=0, help="Manual TTS characters to add")
    parser.add_argument("--add-stt-seconds", type=float, default=0.0, help="Manual STT seconds to add")
    parser.add_argument("--reason", type=str, default="", help="Required reason for manual adjustment")
    parser.add_argument("--dashboard-balance", type=float, default=None, help="Record dashboard balance observation")
    parser.add_argument("--note", type=str, default="", help="Note for dashboard balance observation")
    parser.add_argument("--ledger", type=str, default=str(DEFAULT_LEDGER), help="Path to usage_ledger.json")
    args = parser.parse_args()

    ledger_path = Path(args.ledger)

    if args.add_tts_chars > 0 or args.add_stt_seconds > 0:
        if not args.reason:
            print("Error: --reason is required when adding manual TTS characters or STT seconds.", file=sys.stderr)
            sys.exit(1)
        add_manual_usage(ledger_path, args.add_tts_chars, args.add_stt_seconds, args.reason)
        print(f"Added manual usage (+{args.add_tts_chars} chars, +{args.add_stt_seconds}s).")

    if args.dashboard_balance is not None:
        add_dashboard_observation(ledger_path, args.dashboard_balance, args.note)
        print(f"Recorded dashboard balance observation ({args.dashboard_balance} credits).")

    if args.show or (not args.add_tts_chars and not args.add_stt_seconds and args.dashboard_balance is None):
        show_summary(ledger_path)


if __name__ == "__main__":
    main()
