"""Evaluation runner: record transcripts, score detection metrics, and evaluate WER."""

import argparse
import asyncio
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
import soundfile as sf

from backend.config import settings
from backend.gnani_stt import transcribe_file
from backend.metrics import (
    compute_wer,
    detection_summary,
    latency_summary,
    wer_normalize,
)
from backend.scorer import ScamScorer, load_pack
from scripts.corpus_lib import Call, load_scripts
from scripts.stream_file import record_call

MANIFEST_PATH = Path("data/calls/manifest.json")
DEV_SCRIPTS_PATH = Path("data/scripts/dev_calls.json")
TEST_SCRIPTS_PATH = Path("data/scripts/test_calls.json")
RULES_PATH = Path("rules/scam_rules_hi_en.json")
TRANSCRIPTS_DIR = Path("data/transcripts")
EVAL_DIR = Path("data/eval")
RESULTS_PATH = EVAL_DIR / "results.json"
TEST_RUNS_PATH = EVAL_DIR / "test_runs.jsonl"
WER_PATH = EVAL_DIR / "wer.json"


def get_rules_sha256() -> str:
    if RULES_PATH.exists():
        return hashlib.sha256(RULES_PATH.read_bytes()).hexdigest()
    return ""


def get_manifest_entries(split: Optional[str] = None, ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    entries = []
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception:
            entries = []
    if not entries:
        # Fallback to loading scripts as synthetic call descriptors
        calls = load_scripts([DEV_SCRIPTS_PATH, TEST_SCRIPTS_PATH])
        for c in calls:
            entries.append({
                "id": c.id,
                "title": c.title,
                "label": c.label,
                "lang": c.lang,
                "split": c.split,
                "cue_turn": c.cue_turn,
                "duration_s": 15.0,
                "first_cue_s": 0.4 if c.cue_turn is not None else None,
                "audio_path": f"data/calls/{c.id}__phone_noise.wav",
                "variants": {
                    "clean": f"data/calls/{c.id}__clean.wav",
                    "phone": f"data/calls/{c.id}__phone.wav",
                    "phone_noise": f"data/calls/{c.id}__phone_noise.wav",
                    "phone_noise_drops": f"data/calls/{c.id}__phone_noise_drops.wav",
                },
                "expect": "T05 is an expected miss" if c.id == "T05_card_pin" else None,
            })

    if split and split != "all":
        entries = [e for e in entries if e.get("split") == split]
    if ids:
        id_set = set(ids)
        entries = [e for e in entries if e.get("id") in id_set]
    return sorted(entries, key=lambda x: x.get("id", ""))


# =========================================================================
# 1. RECORD SUBCOMMAND
# =========================================================================
def handle_record(args: argparse.Namespace) -> None:
    calls = get_manifest_entries(args.split, args.ids.split(",") if args.ids else None)
    cond = args.cond or "phone_noise"

    total_seconds = 0.0
    call_audio_files: List[Tuple[Dict[str, Any], Path, Path, float]] = []

    for c in calls:
        cid = c["id"]
        # Find audio file for condition
        variants = c.get("variants") or {}
        wav_path_str = variants.get(cond) or c.get("audio_path") or f"data/calls/{cid}__{cond}.wav"
        wav_path = Path(wav_path_str)

        dur = float(c.get("duration_s", 0.0))
        if dur <= 0.0 and wav_path.exists():
            try:
                dur = float(sf.info(str(wav_path)).duration)
            except Exception:
                dur = 15.0
        elif dur <= 0.0:
            dur = 15.0

        out_name = f"{cid}.jsonl" if cond == "phone_noise" else f"{cid}__{cond}.jsonl"
        out_path = TRANSCRIPTS_DIR / out_name
        call_audio_files.append((c, wav_path, out_path, dur))
        total_seconds += dur

    total_seconds = round(total_seconds, 1)
    cap = float(settings.max_stt_seconds_per_run)

    print(f"=== RECORDING PLAN ({len(calls)} calls, condition: {cond}) ===")
    for c, wav, out, dur in call_audio_files:
        status_str = "[EXISTS - SKIP]" if out.exists() and not args.force else "[READY]"
        print(f"  {c['id']:25} {dur:5.1f}s -> {out.name} {status_str}")

    print(f"\nTotal audio seconds: {total_seconds:.1f} s")
    mins = total_seconds / 60.0
    print(f"Estimated wall-clock ETA: {total_seconds:.1f} s (~{mins:.1f} min streaming in real-time)")

    if settings.stt_credits_per_minute:
        cost = mins * float(settings.stt_credits_per_minute)
        print(f"Estimated credit cost: {cost:.2f} credits (at {settings.stt_credits_per_minute}/min)")
    else:
        print("Estimated credit cost: unknown (STT_CREDITS_PER_MINUTE not set)")

    if total_seconds > cap:
        print(
            f"\nThis run needs about {int(math.ceil(total_seconds))} seconds of audio but "
            f"MAX_STT_SECONDS_PER_RUN is {int(cap)}. If you accept the cost, set "
            f"MAX_STT_SECONDS_PER_RUN={int(math.ceil(total_seconds))} in .env and run again."
        )
        sys.exit(1)

    if not args.go:
        print("\nDry run complete. Use --go to stream audio to Gnani Realtime STT.")
        return

    # Real streaming
    finished_count = 0
    for c, wav, out, dur in call_audio_files:
        if out.exists() and not args.force:
            print(f"Skipping {c['id']}: transcript exists at {out}")
            continue

        if not wav.exists():
            print(f"Error: audio file {wav} does not exist. Run Phase 6 corpus generation first.", file=sys.stderr)
            print(f"Finished {finished_count} calls before stopping.")
            sys.exit(1)

        print(f"\nStreaming {c['id']} ({wav})...")
        try:
            asyncio.run(record_call(wav, out, lang=c.get("lang", "hi-IN"), rate=8000))
            finished_count += 1
        except Exception as exc:
            print(f"Error while recording {c['id']}: {exc}", file=sys.stderr)
            print(f"Finished {finished_count} calls before stopping.")
            sys.exit(1)

    print(f"\nSuccessfully finished recording {finished_count} calls.")


# =========================================================================
# 2. SCORE SUBCOMMAND
# =========================================================================
def score_calls_data(
    calls: List[Dict[str, Any]],
    pack: Any,
    careful: int,
    danger: int,
    cond: str,
    from_script: bool = False,
) -> Tuple[List[Dict[str, Any]], List[int]]:
    evaluated_rows: List[Dict[str, Any]] = []
    collected_latencies: List[int] = []

    # Map scripts if from_script is True
    script_map: Dict[str, Call] = {}
    if from_script:
        all_scripts = load_scripts([DEV_SCRIPTS_PATH, TEST_SCRIPTS_PATH])
        script_map = {c.id: c for c in all_scripts}

    for c in calls:
        cid = c["id"]
        label = c.get("label", "scam")
        cue_turn = c.get("cue_turn")
        first_cue_s = c.get("first_cue_s")

        scorer = ScamScorer(pack, careful=careful, danger=danger)
        alerted = False
        alert_t: Optional[float] = None
        max_score = 0
        max_level = "calm"
        segments_data: List[Dict[str, Any]] = []

        if from_script:
            script_call = script_map.get(cid)
            if not script_call:
                continue
            for idx, (spk, text) in enumerate(script_call.turns):
                t_val = 0.4 + idx * 1.5
                res = scorer.feed(text, segment_index=idx)
                if res.score > max_score:
                    max_score = res.score
                if res.level in ("careful", "danger") and max_level != "danger":
                    max_level = res.level
                if res.alert and not alerted:
                    alerted = True
                    alert_t = t_val
                segments_data.append({"t": round(t_val, 2), "text": text})
        else:
            t_file = TRANSCRIPTS_DIR / (f"{cid}.jsonl" if cond == "phone_noise" else f"{cid}__{cond}.jsonl")
            if not t_file.exists():
                continue
            with open(t_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    t_val = float(rec.get("t", 0.0))
                    text = rec.get("text", "")
                    lat = rec.get("latency")
                    if lat is not None:
                        try:
                            collected_latencies.append(int(lat))
                        except (ValueError, TypeError):
                            pass
                    res = scorer.feed(text, segment_index=rec.get("segment_index"))
                    if res.score > max_score:
                        max_score = res.score
                    if res.level in ("careful", "danger") and max_level != "danger":
                        max_level = res.level
                    if res.alert and not alerted:
                        alerted = True
                        alert_t = t_val
                    segments_data.append({"t": round(t_val, 2), "text": text})

        evaluated_rows.append({
            "id": cid,
            "split": c.get("split", "dev"),
            "label": label,
            "alerted": alerted,
            "alert_t": round(alert_t, 2) if alert_t is not None else None,
            "first_cue_s": round(float(first_cue_s), 2) if first_cue_s is not None else None,
            "max_score": max_score,
            "max_level": max_level,
            "segments": segments_data,
        })

    return evaluated_rows, collected_latencies


def handle_score(args: argparse.Namespace) -> None:
    split = args.split or "dev"
    cond = args.cond or "phone_noise"
    careful = int(args.careful)
    danger = int(args.danger)

    # Sweep mode check: dev only!
    if args.sweep:
        if split in ("test", "all"):
            print("Error: --sweep is only permitted on the dev split. Never sweep or tune on the test split.", file=sys.stderr)
            sys.exit(1)

        print(f"=== THRESHOLD SWEEP (split: dev, careful: {careful}, condition: {cond}) ===")
        print("DANGER  RECALL (TP/P)   FAR (FP/N)")
        print("-----------------------------------")
        pack = load_pack(str(RULES_PATH))
        dev_calls = get_manifest_entries("dev")
        for d_thresh in range(40, 95, 5):
            rows, _ = score_calls_data(dev_calls, pack, careful=careful, danger=d_thresh, cond=cond, from_script=False)
            if not rows:
                rows, _ = score_calls_data(dev_calls, pack, careful=careful, danger=d_thresh, cond=cond, from_script=True)
            summary = detection_summary(rows)
            rec = f"{summary['recall'] * 100:.1f}% ({summary['tp']}/{summary['tp'] + summary['fn']})" if summary['recall'] is not None else "N/A"
            far = f"{summary['false_alarm_rate'] * 100:.1f}% ({summary['fp']}/{summary['fp'] + summary['tn']})" if summary['false_alarm_rate'] is not None else "N/A"
            print(f"  {d_thresh:2d}     {rec:15} {far:10}")
        return

    # Test split guard
    rules_sha = get_rules_sha256()
    test_scoring_info = {"times_scored": 0, "rules_changed_since_first": False}

    if split in ("test", "all") or args.ceiling:
        if split in ("test", "all"):
            print("\n" + "=" * 70)
            print("TEST SPLIT: these numbers are final; do not change the rules because of them")
            print("=" * 70 + "\n")
            EVAL_DIR.mkdir(parents=True, exist_ok=True)
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with open(TEST_RUNS_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"time": now_iso, "rules_sha256": rules_sha}) + "\n")

    # Compute test_scoring stats
    if TEST_RUNS_PATH.exists():
        run_lines = [json.loads(line) for line in TEST_RUNS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        if run_lines:
            test_scoring_info["times_scored"] = len(run_lines)
            first_sha = run_lines[0].get("rules_sha256")
            test_scoring_info["rules_changed_since_first"] = any(r.get("rules_sha256") != first_sha for r in run_lines)

    pack = load_pack(str(RULES_PATH))
    existing_results: Dict[str, Any] = {}
    if RESULTS_PATH.exists():
        try:
            existing_results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing_results = {}

    splits_to_process = ["dev", "test"] if split == "all" else [split]
    splits_dict = existing_results.get("splits", {})
    all_calls_list = existing_results.get("calls", [])
    calls_by_id = {c["id"]: c for c in all_calls_list}
    all_latencies: List[int] = []

    for sp in splits_to_process:
        sp_calls = get_manifest_entries(sp)
        # Score real transcripts
        real_rows, lats = score_calls_data(sp_calls, pack, careful, danger, cond, from_script=False)
        all_latencies.extend(lats)

        # Ceiling
        ceiling_summary = None
        if args.ceiling or True:  # Always compute ceiling if possible or requested
            ceiling_rows, _ = score_calls_data(sp_calls, pack, careful, danger, cond, from_script=True)
            if ceiling_rows:
                ceiling_summary = detection_summary(ceiling_rows)
                ceiling_summary["n"] = len(ceiling_rows)

        if real_rows:
            summary = detection_summary(real_rows)
            summary["n"] = len(real_rows)
            summary["ceiling"] = ceiling_summary
            splits_dict[sp] = summary
            for r in real_rows:
                calls_by_id[r["id"]] = r
        else:
            # No transcripts yet: real fields null, ceiling populated
            splits_dict[sp] = {
                "tp": None, "fn": None, "fp": None, "tn": None,
                "precision": None, "recall": None, "f1": None,
                "false_alarm_rate": None, "recall_ci95": [None, None],
                "false_alarm_ci95": [None, None], "careful_on_legit": None,
                "time_to_alert_s": None, "time_from_cue_s": None,
                "n": len(sp_calls),
                "ceiling": ceiling_summary,
            }
            if ceiling_rows:
                for r in ceiling_rows:
                    calls_by_id[r["id"]] = r

    # Table printing
    print(f"\n=== EVALUATION SCORING ({split.upper()} SPLIT) ===")
    print("CALL ID                   SPLIT LABEL  ALERT TTA(s) MAX_SCORE MAX_LEVEL")
    print("-----------------------------------------------------------------------")
    active_calls = [c for c in calls_by_id.values() if split == "all" or c.get("split") == split]
    for c in sorted(active_calls, key=lambda x: x["id"]):
        tta_str = f"{c['alert_t']:.1f}" if c.get("alert_t") is not None else "-"
        print(f"  {c['id']:24} {c['split']:5} {c['label']:6} {str(c['alerted']):5} {tta_str:6} {c['max_score']:3d}       {c['max_level']}")

    for sp in splits_to_process:
        s_data = splits_dict.get(sp, {})
        ceil = s_data.get("ceiling") or {}
        print(f"\nSummary for {sp.upper()}:")
        if s_data.get("recall") is not None:
            print(f"  Real STT : Recall={s_data['recall']*100:.1f}%, FAR={s_data['false_alarm_rate']*100:.1f}%, F1={s_data.get('f1')}")
        else:
            print("  Real STT : No transcripts available yet (fields null)")
        if ceil:
            print(f"  Ceiling  : Recall={ceil.get('recall', 0)*100:.1f}%, FAR={ceil.get('false_alarm_rate', 0)*100:.1f}%, F1={ceil.get('f1')}")

    # Build limitations list
    n_per_split = 10
    limitations = [
        "The same author wrote the rules and the evaluation call scripts.",
        "The calls use synthetic TTS voices rather than real-world human phone recordings.",
        f"The evaluation sets are small ({n_per_split} calls per split), so confidence intervals are wide.",
        f"The frozen test split was scored {test_scoring_info['times_scored']} time(s).",
        "WER comparison: digits vs spelled-out words and Devanagari vs Roman spelling count as errors, making WER an upper bound.",
    ]
    # Check for manifest expect misses
    for c in get_manifest_entries():
        if c.get("expect"):
            limitations.append(c["expect"])

    # Load wer if present
    wer_payload = existing_results.get("wer", {
        "conditions": {
            "clean": None,
            "phone": None,
            "phone_noise": None,
            "phone_noise_drops": None,
        },
        "note": "Digits vs spelled-out numbers and Roman vs Devanagari spellings count as errors; WER values are an upper bound.",
    })
    if WER_PATH.exists():
        try:
            w_data = json.loads(WER_PATH.read_text(encoding="utf-8"))
            wer_payload["conditions"] = w_data.get("conditions", wer_payload["conditions"])
            wer_payload["note"] = w_data.get("note", wer_payload["note"])
        except Exception:
            pass

    results_data = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rules_sha256": rules_sha,
        "rules_pack": pack.pack,
        "thresholds": {"careful": careful, "danger": danger},
        "n_calls": len(calls_by_id),
        "splits": splits_dict,
        "latency_ms": latency_summary(all_latencies) if all_latencies else None,
        "wer": wer_payload,
        "calls": sorted(calls_by_id.values(), key=lambda x: x["id"]),
        "test_scoring": test_scoring_info,
        "limitations": limitations,
    }

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    print(f"\nMerged results written to {RESULTS_PATH}")


# =========================================================================
# 3. WER SUBCOMMAND
# =========================================================================
DEFAULT_WER_IDS = [
    "D01_digital_arrest",
    "D02_otp_kyc",
    "D06_emi_reminder",
    "D07_delivery",
    "D04_lottery",
    "D10_bank_awareness",
]
DEFAULT_CONDS = ["clean", "phone", "phone_noise", "phone_noise_drops"]


def handle_wer(args: argparse.Namespace) -> None:
    ids = args.ids.split(",") if args.ids else DEFAULT_WER_IDS
    conds = args.conds.split(",") if args.conds else DEFAULT_CONDS
    calls = get_manifest_entries(ids=ids)

    # Prepare files
    audio_tasks = []
    total_seconds = 0.0

    all_scripts = load_scripts([DEV_SCRIPTS_PATH, TEST_SCRIPTS_PATH])
    script_map = {c.id: " ".join(t[1] for t in c.turns) for c in all_scripts}

    for c in calls:
        cid = c["id"]
        ref_text = script_map.get(cid, "")
        variants = c.get("variants") or {}
        for cond in conds:
            w_path = variants.get(cond) or f"data/calls/{cid}__{cond}.wav"
            p = Path(w_path)
            dur = float(c.get("duration_s", 0.0))
            if dur <= 0.0 and p.exists():
                try:
                    dur = float(sf.info(str(p)).duration)
                except Exception:
                    dur = 15.0
            elif dur <= 0.0:
                dur = 15.0
            audio_tasks.append((cid, cond, p, ref_text, dur, c.get("lang", "hi-IN")))
            total_seconds += dur

    cap = float(settings.max_stt_seconds_per_run)
    print(f"=== WER EVALUATION PLAN ({len(audio_tasks)} audio clips) ===")
    for cid, cond, path, _, dur, _ in audio_tasks:
        print(f"  {cid:22} {cond:18} {dur:5.1f}s -> {path}")

    print(f"\nTotal audio seconds: {total_seconds:.1f} s")
    if total_seconds > cap:
        print(
            f"This run needs about {int(math.ceil(total_seconds))} seconds of audio but "
            f"MAX_STT_SECONDS_PER_RUN is {int(cap)}. If you accept the cost, set "
            f"MAX_STT_SECONDS_PER_RUN={int(math.ceil(total_seconds))} in .env and run again."
        )
        sys.exit(1)

    if not args.go:
        print("\nDry run complete. Use --go to transcribe files via Gnani REST STT.")
        return

    # Real transcription via REST STT
    cond_results: Dict[str, Dict[str, Any]] = {c: {"wers": [], "per_call": {}} for c in conds}
    for cid, cond, path, ref_text, dur, lang in audio_tasks:
        if dur > 60.0:
            print(f"Skipping {cid} ({cond}): duration {dur:.1f}s > 60s")
            continue
        if not path.exists():
            print(f"Audio file missing: {path}, skipping...")
            continue

        try:
            res = asyncio.run(transcribe_file(path, language_code=lang, fmt="verbatim"))
            hyp_text = res.transcript
            wer_val = compute_wer(ref_text, hyp_text)
            cond_results[cond]["wers"].append(wer_val)
            cond_results[cond]["per_call"][cid] = wer_val
            print(f"  {cid} [{cond}]: WER={wer_val*100:.1f}%")
        except Exception as exc:
            print(f"Error evaluating WER for {cid} [{cond}]: {exc}", file=sys.stderr)

    wer_out: Dict[str, Any] = {
        "conditions": {},
        "note": "Digits versus spelled-out numbers and Devanagari versus Roman spelling count as errors here, so these WERs are an upper bound; they are not an official Gnani benchmark.",
    }
    for cond, data in cond_results.items():
        w_list = data["wers"]
        avg_wer = round(sum(w_list) / float(len(w_list)), 4) if w_list else None
        wer_out["conditions"][cond] = {
            "wer": avg_wer,
            "n": len(w_list),
            "per_call": data["per_call"],
        }

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(WER_PATH, "w", encoding="utf-8") as f:
        json.dump(wer_out, f, indent=2, ensure_ascii=False)
    print(f"\nWER evaluation saved to {WER_PATH}")


# =========================================================================
# MAIN ENTRYPOINT
# =========================================================================
def main() -> None:
    parser = argparse.ArgumentParser(description="Savdhaan Evaluation Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. record
    p_rec = subparsers.add_parser("record", help="Record real Prisma transcripts of synthetic calls")
    p_rec.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    p_rec.add_argument("--ids", help="Comma-separated call IDs")
    p_rec.add_argument("--cond", default="phone_noise")
    p_rec.add_argument("--force", action="store_true", help="Overwrite existing transcripts")
    p_rec.add_argument("--go", action="store_true", help="Execute real recording")

    # 2. score
    p_score = subparsers.add_parser("score", help="Score saved transcripts or script text ceiling")
    p_score.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    p_score.add_argument("--cond", default="phone_noise")
    p_score.add_argument("--careful", type=int, default=30)
    p_score.add_argument("--danger", type=int, default=60)
    p_score.add_argument("--sweep", action="store_true", help="Run danger threshold sweep (dev only)")
    p_score.add_argument("--ceiling", action="store_true", help="Score ceiling from scripts")

    # 3. wer
    p_wer = subparsers.add_parser("wer", help="Evaluate WER across audio conditions")
    p_wer.add_argument("--ids", help="Comma-separated call IDs")
    p_wer.add_argument("--conds", help="Comma-separated conditions")
    p_wer.add_argument("--go", action="store_true", help="Execute real WER transcription")

    args = parser.parse_args()
    if args.command == "record":
        handle_record(args)
    elif args.command == "score":
        handle_score(args)
    elif args.command == "wer":
        handle_wer(args)


if __name__ == "__main__":
    main()
