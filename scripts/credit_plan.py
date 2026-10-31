"""Calculate audio seconds and characters needed for evaluation runs, enforce safety rules, and generate credit plans."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _count_call_chars(call: dict) -> int:
    """Return total character count for a call script."""
    turns = call.get("turns", [])
    total = 0
    for t in turns:
        if isinstance(t, list) and len(t) >= 2:
            total += len(t[1])
        elif isinstance(t, dict):
            total += len(t.get("text", ""))
    return total


def _load_calls(filepath: Path) -> List[dict]:
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("calls", [])
    except Exception:
        return []


def analyze_split_needs(
    split: str,
    calls_dir: Path,
    cache_dir: Path,
    scripts_dir: Path,
) -> Tuple[int, int, int, int]:
    """Return (total_calls, uncached_calls, uncached_chars, est_audio_seconds)."""
    script_path = scripts_dir / f"{split}_calls.json"
    calls = _load_calls(script_path)
    total_calls = len(calls)
    uncached_calls = 0
    uncached_chars = 0
    total_chars = 0

    for call in calls:
        call_id = call.get("id", "")
        call_chars = _count_call_chars(call)
        total_chars += call_chars
        # Check if call audio exists in data/calls/<call_id>.wav or cached
        audio_path = calls_dir / f"{call_id}.wav"
        if audio_path.exists():
            continue
        # Also check data/cache
        # In gen_corpus, turns are cached by sha256. If audio_path missing, it needs generation
        uncached_calls += 1
        uncached_chars += call_chars

    # Estimate audio seconds: ~15 characters per second of speech (~60-80 chars per 5-second turn)
    # Average speech rate in Hindi/Gujarati/English is approx 12-16 chars per second
    est_seconds = int(total_chars / 14) if total_chars > 0 else 0
    return total_calls, uncached_calls, uncached_chars, est_seconds


def build_credit_plan(
    balance: float,
    tts_cost_per_1k: Optional[float] = None,
    stt_cost_per_min: Optional[float] = None,
    base_dir: Optional[Path] = None,
) -> dict:
    """Build the ordered plan and calculate quantities/credits."""
    base = base_dir or Path(".")
    scripts_dir = base / "data" / "scripts"
    calls_dir = base / "data" / "calls"
    cache_dir = base / "data" / "cache"

    splits = ["dev", "test"]
    blind_path = scripts_dir / "blind_calls.json"
    if blind_path.exists():
        splits.append("blind")

    split_stats = {}
    for s in splits:
        split_stats[s] = analyze_split_needs(s, calls_dir, cache_dir, scripts_dir)

    steps = [
        {
            "id": "1_pilot",
            "name": "Pilot (4 dev calls: D01, D02, D07, D08)",
            "command": "python scripts/gen_corpus.py --split dev --pilot --go",
            "cap_env": "MAX_TTS_CHARS_PER_RUN=900\nMAX_STT_SECONDS_PER_RUN=180",
            "chars": 861,
            "seconds": 60,
            "note": "Write dashboard balance down before and after.",
        },
        {
            "id": "2_corpus_dev_test",
            "name": "Full Corpus Generation (dev and test)",
            "command": "python scripts/gen_corpus.py --split dev --go && python scripts/gen_corpus.py --split test --go",
            "cap_env": f"MAX_TTS_CHARS_PER_RUN={max(1000, split_stats['dev'][2] + split_stats['test'][2])}",
            "chars": split_stats["dev"][2] + split_stats["test"][2],
            "seconds": 0,
            "note": "Cached turns cost 0 credits. Write dashboard balance down before and after.",
        },
        {
            "id": "3_record_transcripts",
            "name": "Record Real STT Transcripts (dev and test)",
            "command": "python scripts/run_eval.py record --split dev --go && python scripts/run_eval.py record --split test --go",
            "cap_env": f"MAX_STT_SECONDS_PER_RUN={max(300, split_stats['dev'][3] + split_stats['test'][3])}",
            "chars": 0,
            "seconds": split_stats["dev"][3] + split_stats["test"][3],
            "note": "Writes raw transcripts to data/transcripts/. Write balance down before and after.",
        },
        {
            "id": "4_wer_subset",
            "name": "Word Error Rate on representative subset",
            "command": "python scripts/run_eval.py wer --subset 6 --go",
            "cap_env": "MAX_STT_SECONDS_PER_RUN=120",
            "chars": 0,
            "seconds": 90,
            "note": "Write balance down before and after.",
        },
        {
            "id": "5_score_offline",
            "name": "Offline Scoring (dev and test)",
            "command": "python scripts/run_eval.py score --split dev && python scripts/run_eval.py score --split test",
            "cap_env": "# Offline: 0 credits used",
            "chars": 0,
            "seconds": 0,
            "note": "Free offline scoring. Zero Gnani API calls.",
        },
    ]

    if "blind" in split_stats:
        steps.append({
            "id": "6_blind",
            "name": "Blind Test Set (Single Shot Scoring)",
            "command": "python scripts/gen_corpus.py --split blind --go && python scripts/run_eval.py record --split blind --go && python scripts/run_eval.py score --split blind --confirm-blind-once",
            "cap_env": f"MAX_TTS_CHARS_PER_RUN={max(500, split_stats['blind'][2])}\nMAX_STT_SECONDS_PER_RUN={max(200, split_stats['blind'][3])}",
            "chars": split_stats["blind"][2],
            "seconds": split_stats["blind"][3],
            "note": "Scored exactly ONCE after rules are frozen. Write balance down before and after.",
        })

    # Evaluate cost and one-third rule
    one_third_balance = balance / 3.0
    for st in steps:
        c_chars = st["chars"]
        c_sec = st["seconds"]
        est_cost = None
        if tts_cost_per_1k is not None and stt_cost_per_min is not None:
            est_cost = (c_chars / 1000.0 * tts_cost_per_1k) + (c_sec / 60.0 * stt_cost_per_min)
            st["est_credits"] = round(est_cost, 2)
            st["exceeds_one_third"] = est_cost > one_third_balance
        else:
            st["est_credits"] = None
            st["exceeds_one_third"] = (c_chars > 2000 or c_sec > 180)  # conservative flag

    return {
        "balance": balance,
        "one_third_balance": round(one_third_balance, 2),
        "tts_cost_per_1k": tts_cost_per_1k,
        "stt_cost_per_min": stt_cost_per_min,
        "split_stats": split_stats,
        "steps": steps,
    }


def format_plan_markdown(plan: dict) -> str:
    lines = [
        "# Savdhaan Credit Plan & Execution Steps",
        "",
        f"**Reported Dashboard Balance**: {plan['balance']:.1f} credits",
        f"**Safety Threshold (1/3 Balance Rule)**: {plan['one_third_balance']:.1f} credits",
        "",
    ]
    if plan["tts_cost_per_1k"] is None or plan["stt_cost_per_min"] is None:
        lines.append("> [!WARNING]")
        lines.append("> **Cost per unit unknown**: Run the pilot step first and fill `docs/OPEN_QUESTIONS.md`.")
        lines.append("> Showing physical quantities (characters and seconds).")
        lines.append("")
    else:
        lines.append(f"- TTS unit cost: {plan['tts_cost_per_1k']} credits / 1,000 characters")
        lines.append(f"- STT unit cost: {plan['stt_cost_per_min']} credits / minute")
        lines.append("")

    lines.append("## Safety Rule (AGENTS.md Rule 5)")
    lines.append("Never start a step whose estimate is more than **one third** of your remaining balance.")
    lines.append("If the estimate is unknown and the quantity is large, stop and verify dashboard usage.\n")

    lines.append("## Ordered Execution Steps\n")
    for i, s in enumerate(plan["steps"], 1):
        lines.append(f"### Step {i}: {s['name']}")
        lines.append(f"- **Characters to synthesise**: {s['chars']:,} (cached calls cost 0)")
        lines.append(f"- **Audio seconds to record**: {s['seconds']}s")
        if s["est_credits"] is not None:
            lines.append(f"- **Estimated credits**: {s['est_credits']:.1f} credits")
            if s["exceeds_one_third"]:
                lines.append(f"  **WARNING**: Exceeds 1/3 balance safety limit ({plan['one_third_balance']:.1f})!")
        else:
            lines.append("- **Estimated credits**: Unknown (verify via pilot)")

        lines.append(f"- **Set in `.env` before running**:\n  ```env\n  {s['cap_env']}\n  ```")
        lines.append(f"- **Command**:\n  ```bash\n  {s['command']}\n  ```")
        lines.append(f"- **Note**: {s['note']}\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Savdhaan Credit Planner")
    parser.add_argument("--balance", type=float, required=True, help="Current credit balance from dashboard")
    parser.add_argument("--tts-credits-per-1k-chars", type=float, default=None)
    parser.add_argument("--stt-credits-per-minute", type=float, default=None)
    parser.add_argument("--write", action="store_true", help="Write plan to docs/CREDIT_PLAN.md")
    args = parser.parse_args()

    tts_cost = args.tts_credits_per_1k_chars
    if tts_cost is None and os.environ.get("TTS_CREDITS_PER_1K_CHARS"):
        try:
            tts_cost = float(os.environ.get("TTS_CREDITS_PER_1K_CHARS"))
        except ValueError:
            pass

    stt_cost = args.stt_credits_per_minute
    if stt_cost is None and os.environ.get("STT_CREDITS_PER_MINUTE"):
        try:
            stt_cost = float(os.environ.get("STT_CREDITS_PER_MINUTE"))
        except ValueError:
            pass

    plan = build_credit_plan(args.balance, tts_cost, stt_cost)
    md_output = format_plan_markdown(plan)
    print(md_output)

    if args.write:
        out_path = Path("docs") / "CREDIT_PLAN.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_output)
        print(f"\nPlan successfully written to {out_path}")


if __name__ == "__main__":
    main()
