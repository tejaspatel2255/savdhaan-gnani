# Savdhaan (सावधान)

**Savdhaan** is a real-time scam-call shield built for the **Great Indian AI Internship Challenge** by **Gnani AI** (submission deadline: Nov 10, 2026, 11:59 PM IST).

It streams incoming call audio to **Gnani Prisma v2.5** (real-time speech-to-text via WebSocket), evaluates rolling bilingual transcripts against rule packs for scam indicators (digital arrest, OTP theft, fake authority, screen sharing coercion), and plays protective spoken warnings using **Gnani Timbre v3.0** (text-to-speech) in the listener's language.

> **Honest Demo Notice**: All test calls, transcripts, scripts, and phone numbers in this repository are **SYNTHETIC** test data based on public cybercrime and RBI advisories. Mock and replay modes are explicitly labeled in the UI and never presented as live calls.

---

## Architecture & Tech Stack

- **Speech-to-Text**: [Gnani Prisma v2.5](https://docs.gnani.ai) (`wss://api.vachana.ai/stt/v3/stream`)
- **Text-to-Speech**: [Gnani Timbre v3.0](https://docs.gnani.ai) (`https://api.vachana.ai/api/v1/tts/inference`)
- **Backend**: Python 3.10+, FastAPI, Uvicorn, WebSockets, HTTPX, SoundFile, NumPy, PyYAML
- **Frontend**: Plain HTML5, CSS custom properties, vanilla ES modules (No frameworks, bundlers, icon libraries, or CDN scripts)
- **Design System**: "Nazar" (guardian evil-eye charm) control room with real-time SVG eye tracking, torn paper receipt tape, evidence why-list, and full-width mirrored audio waveform.

---

## Quickstart

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/<your-username>/savdhaan.git
cd savdhaan

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Copy `.env.example` to `.env` and set your Gnani API key:

```bash
cp .env.example .env
```

```ini
GNANI_API_KEY=your_gnani_api_key_here
MAX_TTS_CHARS_PER_RUN=600
MAX_STT_SECONDS_PER_RUN=180
```

*(Note: `.env` is strictly gitignored and will never be committed or logged).*

---

## Running the Application

### Start Backend Server

```bash
uvicorn backend.main:app --reload --port 8000
```
Then visit **http://localhost:8000** in your browser.

### Visual Testing & Dev Feed (Phase 4)

Inspect the Nazar control room with recorded mock event playback:
- **Listening state ($t = 0.5$s)**: [http://localhost:8000/?dev=1&at=0.5](http://localhost:8000/?dev=1&at=0.5)
- **Careful state ($t = 17.6$s)**: [http://localhost:8000/?dev=1&at=17.6](http://localhost:8000/?dev=1&at=17.6)
- **Danger state ($t = 24.7$s)**: [http://localhost:8000/?dev=1&at=24.7](http://localhost:8000/?dev=1&at=24.7)
- **Ended state ($t = 50.0$s)**: [http://localhost:8000/?dev=1&at=50](http://localhost:8000/?dev=1&at=50)
- **Continuous 2x playback**: [http://localhost:8000/?dev=1&speed=2](http://localhost:8000/?dev=1&speed=2)

---

## CLI Tools & Testing

```bash
# Run complete test suite (91 automated unit and integration tests)
pytest -q

# Test warning synthesis character limits and templates without network usage
python scripts/make_warnings.py --lang hi-IN --dry-run

# Run a synthetic mock session in the terminal
python scripts/run_session.py --mode mock --speed 20 --no-speak

# Stream a local WAV file to Gnani Prisma v2.5 live STT
python scripts/stream_file.py --file data/cache/smoke_tts.wav --lang hi-IN --rate 16000 --name smoke_hi
```

---

## Project Roadmap

- [x] **Phase 0**: Project scaffold, usage ledger, configuration, and API smoke tests
- [x] **Phase 1**: Streaming speech-to-text WebSocket client, audio pacer, & transcript recorder
- [x] **Phase 2**: Scam scoring engine, token normalizer, rule pack loader, & fixture tests
- [x] **Phase 3**: Session orchestrator, event bus, mock mode, and warning synthesizer
- [x] **Phase 4**: Nazar control room UI, animated Eye, paper Tape slips, Why list, and dev feed
- [ ] **Phase 5**: Real WebSocket UI connection, live call controls, and call picker
- [ ] **Phase 6**: Audio source modes (Live Mic, Audio File, Replay, and Mock)
- [ ] **Phase 7**: Evaluation Khata page, benchmark runner, and accuracy reports
- [ ] **Phase 8**: System hardening, audio degradation tests, and error recovery
- [ ] **Phase 9**: Final packaging, synthetic demo scripts, and 60-second public demo video
