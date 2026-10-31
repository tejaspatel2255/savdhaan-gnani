# Runbook: Spending Real Gnani Credits Safely

Follow these exact steps in order. Note dashboard balance before and after each step at https://app.gnani.ai/voice/usage. Stop immediately on HTTP 403.

## Step 0: Initial Balance Check
- Record your starting balance:
  `python scripts/ledger_reconcile.py --dashboard-balance <BALANCE> --note "Initial check"`

## Step 1: Pilot Run (861 Characters)
- Generate 4 dev calls:
  `python scripts/gen_corpus.py --split dev --ids D01_digital_arrest,D02_otp_kyc,D07_delivery,D08_doctor_appointment --go`

## Step 2: Calculate and Fill Unit Costs
- Calculate:
  - `TTS_CREDITS_PER_1K_CHARS = (Credits Deducted / 861) * 1000`
  - Record STT deduction during the next test.
- Set both in `.env` and fill `docs/OPEN_QUESTIONS.md`.

## Step 3: Run Credit Planner
- Confirm remaining steps satisfy the 1/3 balance safety rule:
  `python scripts/credit_plan.py --balance <BALANCE> --write`

## Step 4: Complete Dev and Test Corpus Generation
- Synthesize remaining calls (cached calls cost 0 credits):
  `python scripts/gen_corpus.py --split dev --go && python scripts/gen_corpus.py --split test --go`

## Step 5: Record Real Transcripts via Prisma STT
- Stream audio and record transcripts (skips existing transcripts automatically):
  `python scripts/run_eval.py record --split dev --go && python scripts/run_eval.py record --split test --go`

## Step 6: Word Error Rate on Small Subset
- Compute acoustic WER across audio conditions:
  `python scripts/run_eval.py wer --subset 6 --go`

## Step 7: Score Dev and Test Splits
- Offline scoring (zero credits used):
  `python scripts/run_eval.py score --split dev && python scripts/run_eval.py score --split test`

## Step 8: Blind Test Set (Run Exactly ONCE)
- Only after `docs/FROZEN_FINAL.txt` exists and rules are completely frozen:
  `python scripts/import_blind.py`
  `python scripts/gen_corpus.py --split blind --go`
  `python scripts/run_eval.py record --split blind --go`
  `python scripts/run_eval.py score --split blind --confirm-blind-once`

## Step 9: Final Release and Hygiene
- Export static assets, sync README figures, audit release, commit, and push:
  `python scripts/export_static.py`
  `python scripts/update_readme_numbers.py`
  `python scripts/check_release.py`
  `git commit -am "Complete real evaluation run" && git push origin main`
