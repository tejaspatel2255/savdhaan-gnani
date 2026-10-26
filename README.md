# Savdhaan (सावधान)

Savdhaan is a live scam-call shield for the Great Indian AI Internship Challenge by Gnani AI (deadline Nov 10, 2026, 11:59 PM IST). It streams call audio to Gnani Prisma v2.5 (speech to text), scores rolling transcripts for scam patterns, and speaks warnings with Gnani Timbre v3.0 (text to speech) in the listener's language.

All demo calls and scripts are SYNTHETIC detection test data based on public police and RBI advisories.

## Setup

```bash
# 1. Create and activate Python virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and supply your GNANI_API_KEY
```

## Running

```bash
uvicorn backend.main:app --reload --port 8000
```
Then open http://localhost:8000 in your browser.

## Streaming Audio & Replay Scripts

```bash
# 1. Stream an audio file to Gnani Prisma v2.5 live WebSocket:
python scripts/stream_file.py --file data/cache/smoke_tts.wav --lang hi-IN --rate 16000 --name smoke_hi

# 2. Replay recorded transcript locally without hitting the network:
python scripts/replay_transcript.py data/transcripts/smoke_hi.jsonl --speed 4
```

## Roadmap & Checklist

- [x] **Phase 0**: Project scaffold, usage ledger, configuration, and API smoke tests
- [x] **Phase 1**: Streaming speech-to-text client, audio pacer, & transcript recorder
- [x] **Phase 2**: Scam scoring engine, rule pack loader, & fixture evaluator
- [ ] **Phase 3**: Warning generation & Timbre TTS synthesis
- [ ] **Phase 4**: Realtime streaming orchestrator & WebSocket server
- [ ] **Phase 5**: Nazar control room UI & visual alerts
- [ ] **Phase 6**: Audio source modes (Live Mic, File, Replay, Mock)
- [ ] **Phase 7**: End-to-end evaluation suite & benchmark metrics
- [ ] **Phase 8**: System hardening, error recovery, & test coverage
- [ ] **Phase 9**: Final packaging, synthetic demo scripts, & video recording
