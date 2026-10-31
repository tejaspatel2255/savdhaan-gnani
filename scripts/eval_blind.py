"""Blind split validation, one-shot scoring guard, and results.json helpers."""

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FROZEN_FINAL_PATH = Path("docs/FROZEN_FINAL.txt")
FROZEN_BLIND_PATH = Path("docs/FROZEN_BLIND.txt")
BLIND_CALLS_PATH = Path("data/scripts/blind_calls.json")
RULES_DIR = Path("rules")


def verify_blind_scoring_guards(
    confirm_blind_once: bool,
    i_understand_this_is_a_rescore: bool,
    results_path: Path,
    frozen_final_path: Path = FROZEN_FINAL_PATH,
    frozen_blind_path: Path = FROZEN_BLIND_PATH,
    blind_calls_path: Path = BLIND_CALLS_PATH,
    rules_dir: Path = RULES_DIR,
) -> Tuple[bool, str, int]:
    """Verify that all guard conditions are met before scoring the blind set.
    Returns (ok, message, times_scored).
    """
    # 1. Rules must be frozen in FROZEN_FINAL.txt
    if not frozen_final_path.exists():
        return False, "Rules are not frozen yet: finish Phase 14 first.", 0

    frozen_final_content = frozen_final_path.read_text(encoding="utf-8")
    for r_file in rules_dir.glob("*.json"):
        curr_hash = hashlib.sha256(r_file.read_bytes()).hexdigest()
        if curr_hash not in frozen_final_content:
            return False, f"Rule file {r_file.name} hash does not match {frozen_final_path}.", 0

    # 2. Blind calls must match FROZEN_BLIND.txt
    if not frozen_blind_path.exists():
        return False, f"Blind test set is not frozen: {frozen_blind_path} is missing.", 0
    if not blind_calls_path.exists():
        return False, f"Blind calls file {blind_calls_path} does not exist.", 0

    blind_bytes = blind_calls_path.read_bytes()
    blind_hash = hashlib.sha256(blind_bytes).hexdigest()
    frozen_blind_content = frozen_blind_path.read_text(encoding="utf-8")
    if blind_hash not in frozen_blind_content:
        return False, f"Blind set hash does not match {frozen_blind_path}.", 0

    # Check times already scored
    times_scored = 0
    if results_path.exists():
        try:
            res_data = json.loads(results_path.read_text(encoding="utf-8"))
            times_scored = res_data.get("blind_scoring", {}).get("times_scored", 0)
        except Exception:
            pass

    if times_scored > 0:
        if not i_understand_this_is_a_rescore:
            return (
                False,
                f"Blind set was already scored {times_scored} time(s). "
                "Rescoring requires --i-understand-this-is-a-rescore.",
                times_scored,
            )
    else:
        if not confirm_blind_once:
            return (
                False,
                "Scoring the blind set requires explicit flag --confirm-blind-once.",
                times_scored,
            )

    return True, "Guard check passed", times_scored


def record_blind_scoring_metadata(
    results_data: Dict[str, Any],
    blind_calls_path: Path = BLIND_CALLS_PATH,
    rules_dir: Path = RULES_DIR,
) -> None:
    """Record blind scoring metadata into results_data dict."""
    blind_hash = hashlib.sha256(blind_calls_path.read_bytes()).hexdigest()
    rules_hashes = {
        rf.name: hashlib.sha256(rf.read_bytes()).hexdigest()
        for rf in rules_dir.glob("*.json")
    }

    scoring_meta = results_data.get("blind_scoring", {})
    prev_times = scoring_meta.get("times_scored", 0)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    scoring_meta["times_scored"] = prev_times + 1
    if "first_scored_at" not in scoring_meta:
        scoring_meta["first_scored_at"] = now_iso
    scoring_meta["last_scored_at"] = now_iso
    scoring_meta["rules_sha256"] = rules_hashes
    scoring_meta["blind_sha256"] = blind_hash

    results_data["blind_scoring"] = scoring_meta
