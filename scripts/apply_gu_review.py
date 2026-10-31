"""Apply reviewed Gujarati strings from CSV to frontend/js/strings.js (dry-run default).

Never edits rules/*.json directly; rule changes are written to docs/GUJARATI_RULE_LABEL_FIXES.md.
"""

import argparse
import csv
import difflib
import re
import sys
from pathlib import Path

STRINGS_JS = Path("frontend/js/strings.js")
DOCS_RULE_FIXES = Path("docs/GUJARATI_RULE_LABEL_FIXES.md")


def load_reviewed_csv(csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Review CSV {csv_path} not found.")
    strings_fixes = {}
    rule_fixes = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fixed = (row.get("gujarati_fixed") or "").strip()
            if not fixed:
                continue
            key = row.get("key", "").strip()
            en = row.get("english", "").strip()
            curr = row.get("gujarati_current", "").strip()
            notes = row.get("notes", "").strip()
            if key.startswith("strings."):
                str_key = key.split(".", 1)[1]
                strings_fixes[str_key] = fixed
            else:
                rule_fixes.append({"key": key, "english": en, "current": curr, "fixed": fixed, "notes": notes})
    return strings_fixes, rule_fixes


def update_strings_content(content: str, fixes: dict) -> str:
    """Update gu entry in strings.js without touching hi or en."""
    new_content = content
    for key, new_gu in fixes.items():
        # Match pattern: key: { hi: "...", en: "...", gu: "..." }
        pattern = re.compile(
            rf'(^\s*{re.escape(key)}\s*:\s*\{{\s*hi\s*:\s*"[^"]*",\s*en\s*:\s*"[^"]*",\s*gu\s*:\s*")[^"]*("\s*\}})',
            re.MULTILINE,
        )
        new_content = pattern.sub(rf"\g<1>{new_gu}\g<2>", new_content)
    return new_content


def apply_review(csv_path: Path, go: bool = False, strings_path: Path = STRINGS_JS, fixes_doc: Path = DOCS_RULE_FIXES):
    strings_fixes, rule_fixes = load_reviewed_csv(csv_path)
    print(f"Loaded {len(strings_fixes)} string fix(es) and {len(rule_fixes)} rule fix(es).")

    if not strings_fixes and not rule_fixes:
        print("No rows with non-empty 'gujarati_fixed' found. Nothing to apply.")
        return

    # Process strings.js
    orig_content = strings_path.read_text(encoding="utf-8")
    new_content = update_strings_content(orig_content, strings_fixes)

    diff = list(difflib.unified_diff(
        orig_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=str(strings_path),
        tofile=str(strings_path) + " (proposed)",
    ))

    if diff:
        print("\n--- Diff for frontend/js/strings.js ---")
        sys.stdout.writelines(diff)
    else:
        print("\nNo diff for strings.js.")

    if rule_fixes:
        print(f"\nFound {len(rule_fixes)} rule/warning fixes. Rules are FROZEN.")
        lines = [
            "# Proposed Gujarati Rule Label & Warning Fixes",
            "",
            "The following fixes were proposed by Gujarati review. Apply only if unfreezing rules.",
            "",
            "| Key | English | Current Gujarati | Proposed Fix | Notes |",
            "| --- | --- | --- | --- | --- |",
        ]
        for rf in rule_fixes:
            lines.append(f"| {rf['key']} | {rf['english']} | {rf['current']} | {rf['fixed']} | {rf['notes']} |")
        doc_text = "\n".join(lines) + "\n"
        if go:
            fixes_doc.write_text(doc_text, encoding="utf-8")
            print(f"Wrote rule proposals to {fixes_doc}")
        else:
            print(f"Dry run: Would write {len(rule_fixes)} proposals to {fixes_doc}")

    if not go:
        print("\n[DRY RUN] No files modified. Use --go to apply changes.")
    else:
        if strings_fixes:
            strings_path.write_text(new_content, encoding="utf-8")
            print(f"Applied {len(strings_fixes)} fix(es) to {strings_path}")


def main():
    parser = argparse.ArgumentParser(description="Apply reviewed Gujarati strings from CSV")
    parser.add_argument("csv_path", type=Path, help="Path to reviewed CSV file")
    parser.add_argument("--go", action="store_true", help="Apply fixes to strings.js (default is dry-run)")
    args = parser.parse_args()
    apply_review(args.csv_path, go=args.go)


if __name__ == "__main__":
    main()
