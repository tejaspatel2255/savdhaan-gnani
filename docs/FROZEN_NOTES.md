# FROZEN CHECKSUM AUDIT NOTES
# Reference for rule file SHA-256 digests and audit trace

## 1. Hindi/English Rule Pack
- `rules/scam_rules_hi_en.json`: `477cca5dd0ad163cab2ca14a55c0f32d810d3c614686def2ae2f7b1ecb2ed8c3`
- Status: **Matches `docs/FROZEN.txt` exactly**.
- Note: This is the primary corpus used by the automated evaluation pipeline (`data/eval/results.json`).

## 2. Gujarati Rule Pack and Warnings
- `rules/scam_rules_gu.json`: `3b83872e94fa6d594139250318e57ef4acf6b6b6769465238ea098f34c3fba47`
- `rules/warnings_gu.json`: `5209f1680cc0bbc1b35690dbf163d5c24cdedda5c72123c5878a814a9961c421`
- Note: `docs/FROZEN.txt` preserves the initial Phase 8 snapshot hash (`3c5a1762...` / `8f192b67...`). Following the standard standing rules (FROZEN.txt is immutable), the current active Gujarati rule pack and translated warnings are tracked here. Evaluation metrics in `data/eval/results.json` rely strictly on the Hindi/English pack and are unaffected.
