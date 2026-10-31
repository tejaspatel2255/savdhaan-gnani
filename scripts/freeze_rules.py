"""Freeze final rules and produce docs/FROZEN_FINAL.txt."""

import argparse
import datetime
import hashlib
import sys
from pathlib import Path

RULES_DIR = Path("rules")
FROZEN_FINAL_PATH = Path("docs/FROZEN_FINAL.txt")
CHANGELOG_PATH = Path("docs/RULES_CHANGELOG.md")


def compute_rules_hashes():
    hashes = {}
    for rf in sorted(RULES_DIR.glob("*.json")):
        hashes[rf.name] = hashlib.sha256(rf.read_bytes()).hexdigest()
    return hashes


def main():
    parser = argparse.ArgumentParser(description="Freeze final rules for evaluation")
    parser.add_argument("--go", action="store_true", help="Write docs/FROZEN_FINAL.txt (default dry-run)")
    parser.add_argument("--force", action="store_true", help="Force overwrite of existing frozen final")
    args = parser.parse_args()

    hashes = compute_rules_hashes()
    today = datetime.date.today().isoformat()

    print("=== Current Rules SHA-256 Hashes ===")
    for fname, h in hashes.items():
        print(f"  {fname:28}: {h}")

    # Note Gujarati mismatch per Phase 14 spec
    print("\nNote: Gujarati rule pack and warnings differ from initial docs/FROZEN.txt snapshot,")
    print("as documented in docs/FROZEN_NOTES.md. docs/FROZEN_FINAL.txt is the final authoritative record.")

    if not args.go:
        print("\n[DRY-RUN] Verification complete. Run with --go to write docs/FROZEN_FINAL.txt.")
        return

    if FROZEN_FINAL_PATH.exists() and not args.force:
        print(f"\nError: {FROZEN_FINAL_PATH} already exists. To overwrite, specify --force.")
        sys.exit(1)

    lines = [
        "# FROZEN FINAL RULES SHA256 DIGESTS",
        f"# Date: {today}",
        "# Authoritative frozen state prior to blind set scoring.",
        "",
    ]
    for fname, h in hashes.items():
        lines.append(f"rules/{fname}: {h}")

    FROZEN_FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    FROZEN_FINAL_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote authoritative freeze to {FROZEN_FINAL_PATH}")
    print("Rules frozen. The blind set may now be scored once.")

    if args.force:
        CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHANGELOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n- **Notice**: Final rules freeze was refreshed with --force on {today}.\n")


if __name__ == "__main__":
    main()
