# Savdhaan (सावधान) · Live Scam-Call Shield

Savdhaan protects citizens from scam calls in real time using explainable speech intelligence.
It streams live phone audio, scores rolling bilingual transcripts with deterministic rules,
and speaks immediate warnings while simulating family alerts before money or credentials are lost.

Built for the **Great Indian AI Internship Challenge** by **Gnani AI** (Deadline: Nov 10, 2026, 11:59 PM IST).

## Run in Two Minutes (Offline Demo)

Zero configuration, zero API credits, and no secrets needed:

```bash
python -m venv .venv
# On Windows: .venv\Scripts\activate | On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/demo.py
```
Open [http://localhost:8000](http://localhost:8000). Click **Play a sample scam call** to watch real-time detection.

## Live Mode with Gnani AI

```bash
cp .env.example .env
# Edit .env and set your GNANI_API_KEY
python -m backend.main
```

## Where Gnani AI Is Used

| Capability | Gnani Engine | Endpoint | Calling Code |
| :--- | :--- | :--- | :--- |
| Live Speech Recognition | **Gnani Prisma v2.5** | `wss://api.vachana.ai/stt/v3/stream` | `backend/gnani_stream.py` |
| Benchmark Speech Recognition | **Gnani Prisma v2.5** (REST) | `https://api.vachana.ai/stt/v3` | `backend/gnani_stt.py` |
| Voice Warning Generation | **Gnani Timbre v3.0** | `https://api.vachana.ai/api/v1/tts/inference` | `backend/gnani_tts.py` |

## Measured Evaluation (Khata Ledger)

All figures come directly from `data/eval/results.json` (`/report.html`):

| Evaluation Split | Mode | Scam Recall (95% CI) | False Alarm Rate (95% CI) | F1 Score |
| :--- | :--- | :--- | :--- | :--- |
| **Dev Split** (10 calls) | Perfect Transcript (Ceiling) | **100.0% (5/5)** `[0.5655, 1.0]` | **0.0% (0/5)** `[0.0, 0.4345]` | **1.0000** |
| **Dev Split** (10 calls) | Real Prisma (`phone_noise`) | not measured yet (`python scripts/run_eval.py record --split dev --go`) | - | - |
| **Test Split** (10 calls, frozen) | Perfect Transcript (Ceiling) | **80.0% (4/5)** `[0.3755, 0.9638]` | **0.0% (0/5)** `[0.0, 0.4345]` | **0.8889** |
| **Test Split** (10 calls, frozen) | Real Prisma (`phone_noise`) | not measured yet (`python scripts/run_eval.py record --split test --go`) | - | - |

- **Limitations**: Synthetic TTS voices; small sample sizes (10 calls/split); frozen test split scored 1 time.
- Expected miss noted in test split: `T05_card_pin` (subtle conversational trap without threat keywords).

## Safety, Privacy & Honest Demo

- **100% Synthetic Data**: All test recordings, names, and numbers are artificial.
- **Zero Voice Cloning**: No voice imitation or speaker cloning APIs are ever called.
- **Privacy First**: Microphone audio is streamed directly to RAM buffers and never saved to disk.
- **Simulated Family Alerts**: All SMS and notification dispatches are strictly simulated.
- **Clear Demarcation**: UI displays `LIVE MIC`, `FILE`, `REPLAY`, or `DEMO · recorded` badges at all times.
- **Not a Helpline Replacement**: Intended as a personal safeguard, not a substitute for national cybercrime reporting (1930) or banking helplines.

## License

MIT License. See [LICENSE](LICENSE) for details.
