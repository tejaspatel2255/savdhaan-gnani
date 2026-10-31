"""Apply proposed rule changes to rules/*.json with strict audit trail and backups."""

import argparse
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

PROPOSALS_DIR = Path("rules/proposed")
BACKUP_DIR = Path("rules/backup")
RULES_DIR = Path("rules")
CHANGELOG_PATH = Path("docs/RULES_CHANGELOG.md")
RESULTS_PATH = Path("data/eval/results.json")


def load_proposals(ids: List[str]) -> List[Dict[str, Any]]:
    proposals = []
    for pid in ids:
        p_file = PROPOSALS_DIR / f"{pid}.json"
        if not p_file.exists():
            raise FileNotFoundError(f"Proposal file not found: {p_file}")
        proposals.append(json.loads(p_file.read_text(encoding="utf-8")))
    return proposals


def apply_proposals_to_dict(rule_pack: Dict[str, Any], proposal: Dict[str, Any]) -> None:
    p_type = proposal.get("type")
    frag = proposal.get("fragment", {})

    if p_type == "add_dampener":
        rule_pack.setdefault("dampeners", [])
        if not any(d.get("id") == frag.get("id") for d in rule_pack["dampeners"]):
            rule_pack["dampeners"].append(frag)

    elif p_type == "add_combo":
        rule_pack.setdefault("combos", [])
        if not any(c.get("id") == frag.get("id") for c in rule_pack["combos"]):
            rule_pack["combos"].append(frag)

    elif p_type == "add_phrase":
        target_rule_id = proposal.get("target_rule_id")
        to_add = frag.get("patterns_to_add", [])
        for rule in rule_pack.get("rules", []):
            if rule.get("id") == target_rule_id:
                curr_pats = set(rule.get("patterns", []))
                for p in to_add:
                    if p not in curr_pats:
                        rule["patterns"].append(p)
                        curr_pats.add(p)

    elif p_type == "no_change":
        pass


def main():
    parser = argparse.ArgumentParser(description="Apply proposed rule modifications")
    parser.add_argument("--ids", required=True, help="Comma-separated proposal IDs (e.g. P1,P2)")
    parser.add_argument("--i-approve", action="store_true", help="User approval flag to write changes")
    args = parser.parse_args()

    # Pre-condition: Refuse if blind set was already scored
    if RESULTS_PATH.exists():
        try:
            r_data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
            if "blind_scoring" in r_data and r_data["blind_scoring"].get("times_scored", 0) > 0:
                print("Error: Blind set has already been scored! Rules can never be changed after blind scoring.")
                sys.exit(1)
        except Exception:
            pass

    selected_ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    try:
        proposals = load_proposals(selected_ids)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Loaded {len(proposals)} proposal(s): {', '.join(selected_ids)}")
    for p in proposals:
        print(f"  [{p['id']}] {p['title']} ({p['type']}) -> {p['target_file']}")

    if not args.i_approve:
        print("\n[DRY-RUN] Previewing diff. No files were modified.")
        print("To apply these changes, rerun with --i-approve.")
        return

    # Backup existing rules
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup = BACKUP_DIR / timestamp
    target_backup.mkdir(parents=True, exist_ok=True)

    files_to_update: Dict[Path, Dict[str, Any]] = {}
    shas_before: Dict[str, str] = {}

    for r_file in RULES_DIR.glob("*.json"):
        shas_before[r_file.name] = hashlib.sha256(r_file.read_bytes()).hexdigest()
        shutil.copy2(r_file, target_backup / r_file.name)
        files_to_update[r_file] = json.loads(r_file.read_text(encoding="utf-8"))

    print(f"Created backup in {target_backup}")

    for p in proposals:
        t_path = Path(p["target_file"])
        if t_path in files_to_update:
            apply_proposals_to_dict(files_to_update[t_path], p)

    shas_after: Dict[str, str] = {}
    for r_file, updated_dict in files_to_update.items():
        data_bytes = json.dumps(updated_dict, indent=2, ensure_ascii=False).encode("utf-8")
        r_file.write_bytes(data_bytes)
        shas_after[r_file.name] = hashlib.sha256(data_bytes).hexdigest()

    # Append to RULES_CHANGELOG.md
    today = datetime.date.today().isoformat()
    changelog_entry = [
        f"\n## Applied Proposals: {', '.join(selected_ids)} ({today})",
        f"- **Timestamp**: {timestamp}",
        f"- **Proposals**: {', '.join(selected_ids)}",
        "- **Notes**: Blind set was NOT used to formulate these changes (dev/test/hardcases only).",
        "- **SHA-256 Changes**:",
    ]
    for fn, sha_b in shas_before.items():
        sha_a = shas_after.get(fn, sha_b)
        status = f"{sha_b} -> {sha_a}" if sha_b != sha_a else f"{sha_b} (unchanged)"
        changelog_entry.append(f"  - `{fn}`: {status}")

    CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHANGELOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(changelog_entry) + "\n")

    print(f"Successfully applied proposals and updated {CHANGELOG_PATH}")


if __name__ == "__main__":
    main()
