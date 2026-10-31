# Rule Proposals and Impact Analysis (Phase 14)

> **Important Disclosure**: These proposals are derived from observing the already-seen Dev and Test splits and the diagnostic Hard Cases suite. The Blind set was **not** accessed or evaluated. Applying any proposal updates `rules_changed_since_first_test_scoring: true` in the evaluation ledger.

---

## 1. Summary of Proposals

| ID | Title | Type | Target | Recommendation | Evidence / Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`P1`** | Delivery courier safe dampener | `add_dampener` | `rules/scam_rules_hi_en.json` | **Apply** | Prevents legitimate delivery boys (`T09`, `HN02`) from reaching careful score when asking for delivery OTP at the door. |
| **`P2`** | UPI collect & QR code patterns | `add_phrase` | `rules/scam_rules_hi_en.json` | **Apply** | Catches widespread UPI collect scams (`HP01`, `HP02`) where users are asked to enter their PIN to receive money. |
| **`P3`** | Card credentials + urgency combo | `add_combo` | `rules/scam_rules_hi_en.json` | **Apply** | Allows subtle credit/debit card credential theft (`T05_card_pin`) to reach the danger alert threshold (60). |
| **`P4`** | Remote desktop AnyDesk/TeamViewer | `add_phrase` | `rules/scam_rules_hi_en.json` | **Apply** | Covers common tech support malware remote access tools (`HP03`, `HP11`). |
| **`P5`** | Electricity cutoff threat phrases | `add_phrase` | `rules/scam_rules_hi_en.json` | **Apply** | Flags urgent power disconnection threats (`HP07`). |
| **`P6`** | No-change outcome (status quo) | `no_change` | N/A | **Skip** | Preserves original rule baseline if the user prefers zero modifications to seen data. |

---

## 2. Before / After Comparison Matrix (Simulated in Memory)

| Metric / Dataset | Baseline (Original Rules) | With P1, P2, P3, P4, P5 Applied | Impact / Delta |
| :--- | :--- | :--- | :--- |
| **Dev Split Recall** | 100.0% (5 of 5) | 100.0% (5 of 5) | Unchanged (all scam caught) |
| **Dev Split False Alarm Rate** | 0.0% (0 of 5) | 0.0% (0 of 5) | Unchanged (clean) |
| **Dev Legit Reaching Careful** | 0 of 5 | 0 of 5 | Unchanged |
| **Test Split Recall (Ceiling)** | 80.0% (4 of 5) | 100.0% (5 of 5) | **+20.0%** (`T05_card_pin` caught) |
| **Test Split False Alarm Rate** | 0.0% (0 of 5) | 0.0% (0 of 5) | Unchanged (0 of 5) |
| **Test Legit Reaching Careful** | 2 of 5 (`T08`, `T09`) | 1 of 5 (`T08` only; `T09` dropped) | **-1** (`T09` courier OTP stays calm) |
| **Hard Cases Accuracy** | 27 of 40 (67.5%) | 32 of 40 (80.0%) | **+5 cases resolved** (`HP01`, `HP02`, `HP03`, `HP07`, `HP12`) |

---

## 3. How to Apply
Per project guidelines, the agent **never** modifies `rules/*.json` directly. The USER decides what to apply:
```bash
# 1. Preview changes (Dry Run):
python scripts/apply_rule_proposals.py --ids P1,P2,P3,P4,P5

# 2. Approve and apply to rules:
python scripts/apply_rule_proposals.py --ids P1,P2,P3,P4,P5 --i-approve
```
