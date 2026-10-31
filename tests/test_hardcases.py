"""Test hardcases suite and write docs/HARDCASES.md summary.
Note: Per Phase 14 spec, individual prediction misses do NOT fail the build;
this test validates schema, structure, and records the pass/fail census to docs/HARDCASES.md.
"""

import json
from pathlib import Path
import pytest

from backend.scorer import ScamScorer, load_pack, merge_packs

HARDCASES_PATH = Path("tests/hardcases.json")
REPORT_PATH = Path("docs/HARDCASES.md")


def test_hardcases_schema_and_execution():
    assert HARDCASES_PATH.exists(), f"Missing {HARDCASES_PATH}"
    cases = json.loads(HARDCASES_PATH.read_text(encoding="utf-8"))

    assert len(cases) == 40, f"Expected exactly 40 hard cases, found {len(cases)}"
    negatives = [c for c in cases if c["group"] == "hard_negative"]
    positives = [c for c in cases if c["group"] == "hard_positive"]
    assert len(negatives) == 20, f"Expected 20 hard negatives, found {len(negatives)}"
    assert len(positives) == 20, f"Expected 20 hard positives, found {len(positives)}"

    hi_pack = load_pack("rules/scam_rules_hi_en.json")
    gu_pack = load_pack("rules/scam_rules_gu.json")
    merged_pack = merge_packs([hi_pack, gu_pack])

    passed_count = 0
    results_rows = []

    for c in cases:
        scorer = ScamScorer(merged_pack, careful=30, danger=60)
        max_score = 0
        max_level = "calm"
        for idx, (spk, txt) in enumerate(c["turns"]):
            up = scorer.feed(txt, segment_index=idx)
            if up.score > max_score:
                max_score = up.score
            if up.level in ("careful", "danger") and max_level != "danger":
                max_level = up.level

        expected = c["expected_level"]
        passed = (max_level == expected) or (expected == "danger" and scorer.alerted)
        if passed:
            passed_count += 1

        results_rows.append({
            "id": c["id"],
            "group": c["group"],
            "scenario": c["scenario"],
            "expected": expected,
            "actual_level": max_level,
            "max_score": max_score,
            "status": "PASS" if passed else "FAIL",
        })

    # Generate docs/HARDCASES.md
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# Hard Cases Evaluation Census",
        "",
        "> **Notice**: These 40 diagnostic test cases evaluate boundary behaviors (negations, customer service,",
        "> delivery OTPs, UPI collects, QR codes, remote apps). They represent known-behavior regression checks,",
        "> **NOT** an official benchmark accuracy figure. These counts are not added to `data/eval/results.json`.",
        "",
        f"**Summary**: {passed_count} of {len(cases)} behave as expected.",
        "",
        "| Case ID | Group | Expected | Actual Level | Max Score | Status | Scenario |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in results_rows:
        report_lines.append(
            f"| `{r['id']}` | {r['group']} | **{r['expected'].upper()}** | {r['actual_level'].upper()} | {r['max_score']} | **{r['status']}** | {r['scenario']} |"
        )

    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    assert REPORT_PATH.exists()
