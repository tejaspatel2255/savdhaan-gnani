"""Export Gujarati strings from strings.js, rules, and warnings into docs/GUJARATI_REVIEW.csv."""

import csv
import json
import re
import sys
from pathlib import Path

STRINGS_JS = Path("frontend/js/strings.js")
SCAM_RULES_GU = Path("rules/scam_rules_gu.json")
WARNINGS_GU = Path("rules/warnings_gu.json")
OUT_CSV = Path("docs/GUJARATI_REVIEW.csv")


def extract_strings_entries(js_path: Path):
    """Extract (key, english, gujarati) from frontend/js/strings.js."""
    if not js_path.exists():
        return []
    content = js_path.read_text(encoding="utf-8")
    # Matches patterns like: key: { hi: "...", en: "...", gu: "..." }
    pattern = re.compile(
        r'^\s*([a-zA-Z0-9_]+)\s*:\s*\{\s*hi\s*:\s*"([^"]*)",\s*en\s*:\s*"([^"]*)",\s*gu\s*:\s*"([^"]*)"\s*\}',
        re.MULTILINE,
    )
    rows = []
    for match in pattern.finditer(content):
        key = match.group(1)
        en = match.group(3)
        gu = match.group(4)
        rows.append(("strings." + key, en, gu))
    return rows


def extract_rule_labels(rules_path: Path):
    """Extract label_gu entries from scam_rules_gu.json."""
    if not rules_path.exists():
        return []
    try:
        data = json.loads(rules_path.read_text(encoding="utf-8"))
        rows = []
        for rule in data.get("rules", []):
            rid = rule.get("id", "")
            en_desc = rule.get("description", "")
            label_gu = rule.get("label_gu", "")
            if label_gu:
                rows.append((f"rule.{rid}.label_gu", en_desc, label_gu))
        return rows
    except Exception:
        return []


def extract_warning_texts(warnings_path: Path):
    """Extract warning texts from warnings_gu.json."""
    if not warnings_path.exists():
        return []
    try:
        data = json.loads(warnings_path.read_text(encoding="utf-8"))
        rows = []
        for w_type, w_obj in data.get("warnings", {}).items():
            en_desc = f"Warning spoken for category: {w_type}"
            gu_text = w_obj.get("text", "") if isinstance(w_obj, dict) else str(w_obj)
            rows.append((f"warning.{w_type}.text", en_desc, gu_text))
        return rows
    except Exception:
        return []


def export_csv(out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_rows = []
    all_rows.extend(extract_strings_entries(STRINGS_JS))
    all_rows.extend(extract_rule_labels(SCAM_RULES_GU))
    all_rows.extend(extract_warning_texts(WARNINGS_GU))

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "english", "gujarati_current", "gujarati_fixed", "notes"])
        for key, en, gu in all_rows:
            writer.writerow([key, en, gu, "", ""])

    print(f"Exported {len(all_rows)} entries to {out_path}")
    return len(all_rows)


if __name__ == "__main__":
    export_csv(OUT_CSV)
