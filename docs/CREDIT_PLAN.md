# Savdhaan Credit Plan & Execution Steps

**Reported Dashboard Balance**: 4000.0 credits
**Safety Threshold (1/3 Balance Rule)**: 1333.3 credits

> [!WARNING]
> **Cost per unit unknown**: Run the pilot step first and fill `docs/OPEN_QUESTIONS.md`.
> Showing physical quantities (characters and seconds).

## Safety Rule (AGENTS.md Rule 5)
Never start a step whose estimate is more than **one third** of your remaining balance.
If the estimate is unknown and the quantity is large, stop and verify dashboard usage.

## Ordered Execution Steps

### Step 1: Pilot (4 dev calls: D01, D02, D07, D08)
- **Characters to synthesise**: 861 (cached calls cost 0)
- **Audio seconds to record**: 60s
- **Estimated credits**: Unknown (verify via pilot)
- **Set in `.env` before running**:
  ```env
  MAX_TTS_CHARS_PER_RUN=900
MAX_STT_SECONDS_PER_RUN=180
  ```
- **Command**:
  ```bash
  python scripts/gen_corpus.py --split dev --pilot --go
  ```
- **Note**: Write dashboard balance down before and after.

### Step 2: Full Corpus Generation (dev and test)
- **Characters to synthesise**: 4,183 (cached calls cost 0)
- **Audio seconds to record**: 0s
- **Estimated credits**: Unknown (verify via pilot)
- **Set in `.env` before running**:
  ```env
  MAX_TTS_CHARS_PER_RUN=4183
  ```
- **Command**:
  ```bash
  python scripts/gen_corpus.py --split dev --go && python scripts/gen_corpus.py --split test --go
  ```
- **Note**: Cached turns cost 0 credits. Write dashboard balance down before and after.

### Step 3: Record Real STT Transcripts (dev and test)
- **Characters to synthesise**: 0 (cached calls cost 0)
- **Audio seconds to record**: 298s
- **Estimated credits**: Unknown (verify via pilot)
- **Set in `.env` before running**:
  ```env
  MAX_STT_SECONDS_PER_RUN=300
  ```
- **Command**:
  ```bash
  python scripts/run_eval.py record --split dev --go && python scripts/run_eval.py record --split test --go
  ```
- **Note**: Writes raw transcripts to data/transcripts/. Write balance down before and after.

### Step 4: Word Error Rate on representative subset
- **Characters to synthesise**: 0 (cached calls cost 0)
- **Audio seconds to record**: 90s
- **Estimated credits**: Unknown (verify via pilot)
- **Set in `.env` before running**:
  ```env
  MAX_STT_SECONDS_PER_RUN=120
  ```
- **Command**:
  ```bash
  python scripts/run_eval.py wer --subset 6 --go
  ```
- **Note**: Write balance down before and after.

### Step 5: Offline Scoring (dev and test)
- **Characters to synthesise**: 0 (cached calls cost 0)
- **Audio seconds to record**: 0s
- **Estimated credits**: Unknown (verify via pilot)
- **Set in `.env` before running**:
  ```env
  # Offline: 0 credits used
  ```
- **Command**:
  ```bash
  python scripts/run_eval.py score --split dev && python scripts/run_eval.py score --split test
  ```
- **Note**: Free offline scoring. Zero Gnani API calls.

### Step 6: Blind Test Set (Single Shot Scoring)
- **Characters to synthesise**: 366 (cached calls cost 0)
- **Audio seconds to record**: 26s
- **Estimated credits**: Unknown (verify via pilot)
- **Set in `.env` before running**:
  ```env
  MAX_TTS_CHARS_PER_RUN=500
MAX_STT_SECONDS_PER_RUN=200
  ```
- **Command**:
  ```bash
  python scripts/gen_corpus.py --split blind --go && python scripts/run_eval.py record --split blind --go && python scripts/run_eval.py score --split blind --confirm-blind-once
  ```
- **Note**: Scored exactly ONCE after rules are frozen. Write balance down before and after.
