"""Print authoritative facts and numbers directly from results.json for posts and reports."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    results_path = ROOT / "data" / "eval" / "results.json"
    if not results_path.exists():
        print("data/eval/results.json does not exist.")
        return

    data = json.loads(results_path.read_text(encoding="utf-8"))
    splits = data.get("splits", {})

    print("=" * 60)
    print("SAVDHAAN POST FACTS & VERIFIED METRICS")
    print("=" * 60)

    for s_name in ["dev", "test", "blind"]:
        s_data = splits.get(s_name)
        if not s_data:
            continue
        print(f"\nSplit: {s_name.upper()}")
        ceiling = s_data.get("ceiling", {})
        if ceiling:
            c_tp = ceiling.get("tp", 0)
            c_pos = c_tp + ceiling.get("fn", 0)
            c_fp = ceiling.get("fp", 0)
            c_neg = c_fp + ceiling.get("tn", 0)
            c_rec = ceiling.get("recall", 0.0) * 100
            c_far = ceiling.get("false_alarm_rate", 0.0) * 100
            print(f"  Ceiling Recall : {c_rec:.1f}% ({c_tp} of {c_pos})")
            print(f"  Ceiling FAR    : {c_far:.1f}% ({c_fp} of {c_neg})")
            print(f"  Ceiling F1     : {ceiling.get('f1', 0.0):.4f}")

        # Real speech recognition metrics if measured
        rec = s_data.get("recall")
        if rec is not None:
            tp = s_data.get("tp", 0)
            pos = tp + s_data.get("fn", 0)
            fp = s_data.get("fp", 0)
            neg = fp + s_data.get("tn", 0)
            far = s_data.get("false_alarm_rate", 0.0) * 100
            print(f"  Prisma Recall  : {rec * 100:.1f}% ({tp} of {pos})")
            print(f"  Prisma FAR     : {far:.1f}% ({fp} of {neg})")
            print(f"  Prisma F1      : {s_data.get('f1', 0.0):.4f}")
        else:
            print("  Prisma Audio   : not measured yet")

    print("\n" + "=" * 60)
    print("Core Capabilities:")
    print("  - Real-time live audio streaming with Gnani Prisma v2.5 WebSocket STT")
    print("  - Zero-latency deterministic regex and token gating scam scoring")
    print("  - Protective voice interrupt synthesis with Gnani Timbre v3.0 TTS")
    print("  - Trilingual warning voice pack (Hindi, Gujarati, English)")
    print("  - 'Nazar' guardian eye interface with transparent evidence receipt tape")
    print("=" * 60)


if __name__ == "__main__":
    main()
