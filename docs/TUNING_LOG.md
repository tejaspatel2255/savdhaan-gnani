# TUNING LOG: Dev-Only Rule Adjustments

Initial pack baseline saved at: `data/eval/pack_before_tuning.json`.

## Dev Split Evaluation Baseline (Before Tuning)
- **Dev Recall**: 5 of 5 (100.0%)
- **Dev False Alarm Rate (FAR)**: 0 of 5 (0.0%)
- **Dev F1**: 1.00

### Rule Changes
*No rule modifications needed.* The existing general rule patterns already correctly achieve 100% recall (5/5 scam detected) and 0% false alarms (0/5 legit flagged) on the dev ceiling sweep without overfitting or narrow rule additions.

## Known issues after freezing
- `T05_card_pin` (Test split): scam alert is false in text ceiling test. Expected per Phase 6 frozen benchmark notes. Per AGENTS.md rules, rules are frozen and NOT tuned against the test split.
