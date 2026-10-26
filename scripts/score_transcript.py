"""Script to score transcripts or fixtures against the scam detection engine."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.scorer import ScamScorer, load_pack


def parse_args():
    parser = argparse.ArgumentParser(description="Score audio transcript or calls fixture")
    parser.add_argument("path", help="Path to .jsonl transcript, .json mock call, or fixtures calls.json")
    parser.add_argument("--pack", default="rules/scam_rules_hi_en.json", help="Rule pack path")
    parser.add_argument("--careful", type=int, default=30, help="Careful threshold (default: 30)")
    parser.add_argument("--danger", type=int, default=60, help="Danger threshold (default: 60)")
    parser.add_argument("--json", action="store_true", help="Print updates as JSON")
    return parser.parse_args()


def score_single_call(segments: List[str], scorer: ScamScorer, print_rows: bool = True) -> List[Dict[str, Any]]:
    scorer.reset()
    events = []
    alert_printed = False

    for idx, seg in enumerate(segments):
        update = scorer.feed(seg, segment_index=idx)
        events.append(update.to_event())

        if print_rows:
            matched_rules = ", ".join(f"{h.rule_id}('{h.matched}')" for h in update.hits)
            sign = f"+{update.delta}" if update.delta > 0 else str(update.delta)
            print(f"[{idx}] score: {update.score:3d} ({sign:>3s})  level: {update.level:<7s}  hits: [{matched_rules}]")
            if update.alert and not alert_printed:
                print(f"  *** ALERT at segment {idx} ***")
                alert_printed = True

    return events


def run_fixtures(fixtures_path: Path, pack_path: str, careful: int, danger: int) -> bool:
    with open(fixtures_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pack = load_pack(pack_path)
    scorer = ScamScorer(pack, careful=careful, danger=danger)

    all_passed = True
    print(f"\n=== Evaluating Fixtures: {fixtures_path} ===\n")
    print(f"{'Category':<10s} {'Call ID':<26s} {'Status':<6s} {'Details'}")
    print("-" * 75)

    # 1. Scam calls
    for call in data.get("scam", []):
        cid = call["id"]
        expected_alert_by = call["alert_by_index"]
        segments = call["segments"]

        scorer.reset()
        alert_index = None
        for idx, seg in enumerate(segments):
            up = scorer.feed(seg, segment_index=idx)
            if up.alert and alert_index is None:
                alert_index = idx

        if alert_index is not None and alert_index <= expected_alert_by:
            status = "PASS"
            details = f"alerted at idx {alert_index} (expected <= {expected_alert_by})"
        else:
            status = "FAIL"
            all_passed = False
            details = f"alerted at {alert_index} (expected <= {expected_alert_by})"

        print(f"{'SCAM':<10s} {cid:<26s} {status:<6s} {details}")

    # 2. Legit calls
    for call in data.get("legit", []):
        cid = call["id"]
        max_below = call.get("max_score_below", 30)
        segments = call["segments"]

        scorer.reset()
        alert_fired = False
        max_score = 0
        for idx, seg in enumerate(segments):
            up = scorer.feed(seg, segment_index=idx)
            if up.alert:
                alert_fired = True
            if up.score > max_score:
                max_score = up.score

        if not alert_fired and max_score < max_below:
            status = "PASS"
            details = f"no alert, max_score {max_score} < {max_below}"
        else:
            status = "FAIL"
            all_passed = False
            details = f"alert={alert_fired}, max_score {max_score} (must be < {max_below})"

        print(f"{'LEGIT':<10s} {cid:<26s} {status:<6s} {details}")

    # 3. Gating calls
    for call in data.get("gating", []):
        cid = call["id"]
        segments = call["segments"]

        scorer.reset()
        alert_fired = False
        for idx, seg in enumerate(segments):
            up = scorer.feed(seg, segment_index=idx)
            if up.alert:
                alert_fired = True

        if not alert_fired:
            status = "PASS"
            details = "gated successfully (no alert)"
        else:
            status = "FAIL"
            all_passed = False
            details = "FAILED: alert fired on gated call"

        print(f"{'GATING':<10s} {cid:<26s} {status:<6s} {details}")

    print("-" * 75)
    print(f"Overall Result: {'ALL PASS' if all_passed else 'SOME FAILED'}\n")
    return all_passed


def main():
    args = parse_args()
    input_path = Path(args.path)
    if not input_path.exists():
        print(f"Error: Path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Check if this is the fixtures calls.json
    if input_path.name == "calls.json" or "fixtures" in str(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                peek = json.load(f)
            if isinstance(peek, dict) and ("scam" in peek or "legit" in peek or "gating" in peek):
                success = run_fixtures(input_path, args.pack, args.careful, args.danger)
                sys.exit(0 if success else 1)
        except Exception:
            pass

    # Single call scoring
    pack = load_pack(args.pack)
    scorer = ScamScorer(pack, careful=args.careful, danger=args.danger)

    segments: List[str] = []
    if input_path.suffix == ".jsonl":
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    segments.append(data.get("text", ""))
    elif input_path.suffix == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            segments = [s if isinstance(s, str) else s.get("text", "") for s in data]
        elif isinstance(data, dict):
            segs = data.get("segments", [])
            segments = [s if isinstance(s, str) else s.get("text", "") for s in segs]
    else:
        print(f"Unsupported file extension: {input_path.suffix}", file=sys.stderr)
        sys.exit(1)

    events = score_single_call(segments, scorer, print_rows=not args.json)
    if args.json:
        print(json.dumps(events, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
