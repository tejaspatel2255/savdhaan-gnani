# Blind Test Set Specification and Protocol

## 1. Provenance
- Written by: A friend / third party (did not view `rules/` or code).
- Purpose: Prevent author bias in evaluation by scoring calls written independently.

## 2. Ingestion & Validation
- Input file: `data/scripts/blind_input.txt` (or template `blind_input.EXAMPLE.txt`).
- Import command: `python scripts/import_blind.py`
- Validation checks: unique `B\d+` IDs, scam/legit labels, 3–8 turns, at least one caller (`C`) turn, ≤ 320 chars/call (`BLIND_MAX_CHARS`), no 10+ digit runs (except fake 0000/98XXXXXXXX), no real URLs/emails.

## 3. Freezing Rules
- Output file `data/scripts/blind_calls.json` is hashed on import into `docs/FROZEN_BLIND.txt`.
- Once frozen, `blind_calls.json` must never be edited manually.

## 4. One-Shot Scoring Guard
- Cannot score until:
  1. `docs/FROZEN_FINAL.txt` exists and matches `rules/*.json`.
  2. `docs/FROZEN_BLIND.txt` exists and matches `data/scripts/blind_calls.json`.
  3. Flag `--confirm-blind-once` is provided.
- Any rescoring requires `--i-understand-this-is-a-rescore` and is flagged in audit reports.
