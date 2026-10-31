"""Rewrites the evaluation table in README.md from data/eval/results.json."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "data" / "eval" / "results.json"
README_FILE = ROOT / "README.md"

START_MARKER = "<!-- RESULTS:START -->"
END_MARKER = "<!-- RESULTS:END -->"


def format_ci(ci):
    if not ci or ci[0] is None or ci[1] is None:
        return ""
    return f"`[{ci[0]:.4f}, {ci[1]:.4f}]`"


def build_markdown_table(results: dict) -> str:
    splits = results.get("splits", {})
    dev_split = splits.get("dev", {})
    test_split = splits.get("test", {})

    dev_ceil = dev_split.get("ceiling", {})
    test_ceil = test_split.get("ceiling", {})

    # Dev ceiling
    dev_recall = f"**{dev_ceil.get('recall', 0.0) * 100:.1f}% ({dev_ceil.get('tp', 0)} of {dev_ceil.get('tp', 0) + dev_ceil.get('fn', 0)})** {format_ci(dev_ceil.get('recall_ci95'))}"
    dev_far = f"**{dev_ceil.get('false_alarm_rate', 0.0) * 100:.1f}% ({dev_ceil.get('fp', 0)} of {dev_ceil.get('fp', 0) + dev_ceil.get('tn', 0)})** {format_ci(dev_ceil.get('false_alarm_ci95'))}"
    dev_f1 = f"**{dev_ceil.get('f1', 0.0):.4f}**"

    # Test ceiling
    test_recall = f"**{test_ceil.get('recall', 0.0) * 100:.1f}% ({test_ceil.get('tp', 0)} of {test_ceil.get('tp', 0) + test_ceil.get('fn', 0)})** {format_ci(test_ceil.get('recall_ci95'))}"
    test_far = f"**{test_ceil.get('false_alarm_rate', 0.0) * 100:.1f}% ({test_ceil.get('fp', 0)} of {test_ceil.get('fp', 0) + test_ceil.get('tn', 0)})** {format_ci(test_ceil.get('false_alarm_ci95'))}"
    test_f1 = f"**{test_ceil.get('f1', 0.0):.4f}**"

    # Blind split
    blind_split = splits.get("blind", {})
    blind_ceil = blind_split.get("ceiling", {})
    if blind_split and blind_split.get("tp") is not None:
        b_rec = f"**{blind_split.get('recall', 0.0) * 100:.1f}% ({blind_split.get('tp', 0)} of {blind_split.get('tp', 0) + blind_split.get('fn', 0)})** {format_ci(blind_split.get('recall_ci95'))}"
        b_far = f"**{blind_split.get('false_alarm_rate', 0.0) * 100:.1f}% ({blind_split.get('fp', 0)} of {blind_split.get('fp', 0) + blind_split.get('tn', 0)})** {format_ci(blind_split.get('false_alarm_ci95'))}"
        b_f1 = f"**{blind_split.get('f1', 0.0):.4f}**"
        blind_real_row = f"| **Blind Set** (written by someone else) | Real Prisma (`phone_noise`) | {b_rec} | {b_far} | {b_f1} |"
    else:
        blind_real_row = "| **Blind Set** (written by someone else) | Real Prisma (`phone_noise`) | not measured yet (`python scripts/run_eval.py score --split blind --ceiling`) | - | - |"

    if blind_ceil and blind_ceil.get("tp") is not None:
        bc_rec = f"**{blind_ceil.get('recall', 0.0) * 100:.1f}% ({blind_ceil.get('tp', 0)} of {blind_ceil.get('tp', 0) + blind_ceil.get('fn', 0)})** {format_ci(blind_ceil.get('recall_ci95'))}"
        bc_far = f"**{blind_ceil.get('false_alarm_rate', 0.0) * 100:.1f}% ({blind_ceil.get('fp', 0)} of {blind_ceil.get('fp', 0) + blind_ceil.get('tn', 0)})** {format_ci(blind_ceil.get('false_alarm_ci95'))}"
        bc_f1 = f"**{blind_ceil.get('f1', 0.0):.4f}**"
        blind_ceil_row = f"| **Blind Set** (written by someone else) | Perfect Transcript (Ceiling) | {bc_rec} | {bc_far} | {bc_f1} |"
    else:
        blind_ceil_row = "| **Blind Set** (written by someone else) | Perfect Transcript (Ceiling) | not measured yet (`python scripts/run_eval.py score --split blind --ceiling`) | - | - |"

    rows = [
        START_MARKER,
        "| Evaluation Split | Mode | Scam Recall (95% CI) | False Alarm Rate (95% CI) | F1 Score |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Dev Split** (5 scam + 5 legit calls) | Perfect Transcript (Ceiling) | {dev_recall} | {dev_far} | {dev_f1} |",
        "| **Dev Split** (5 scam + 5 legit calls) | Real Prisma (`phone_noise`) | not measured yet (`python scripts/run_eval.py record --split dev --go`) | - | - |",
        f"| **Test Split** (5 scam + 5 legit calls, frozen) | Perfect Transcript (Ceiling) | {test_recall} | {test_far} | {test_f1} |",
        "| **Test Split** (5 scam + 5 legit calls, frozen) | Real Prisma (`phone_noise`) | not measured yet (`python scripts/run_eval.py record --split test --go`) | - | - |",
        blind_ceil_row,
        blind_real_row,
        END_MARKER,
    ]
    return "\n".join(rows)


def update_readme():
    if not RESULTS_FILE.exists():
        print(f"Error: {RESULTS_FILE} does not exist.")
        return False
    if not README_FILE.exists():
        print(f"Error: {README_FILE} does not exist.")
        return False

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    readme_text = README_FILE.read_text(encoding="utf-8")
    table_str = build_markdown_table(results)

    if START_MARKER in readme_text and END_MARKER in readme_text:
        pattern = re.compile(rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
        new_text = pattern.sub(table_str, readme_text)
    else:
        # Replace the existing table
        pattern = re.compile(r"\| Evaluation Split \| Mode \|.*?\n\n", re.DOTALL)
        if pattern.search(readme_text):
            new_text = pattern.sub(table_str + "\n\n", readme_text)
        else:
            print("Could not find table or markers in README.md")
            return False

    README_FILE.write_text(new_text, encoding="utf-8")
    print("README.md numbers updated successfully.")
    return True


if __name__ == "__main__":
    update_readme()
