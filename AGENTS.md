# SAVDHAAN (सावधान): standing rules for every agent session

PROJECT
Savdhaan is a live scam-call shield for the Great Indian AI Internship Challenge by Gnani AI (deadline Nov 10, 2026, 11:59 PM IST). It streams call audio to Gnani Prisma v2.5 (speech to text), scores the rolling transcript for scam patterns, and speaks a warning with Gnani Timbre (text to speech) in the listener's language. The UI is a "Nazar" (evil-eye) control room. Built solo for a 60-second public demo video, so it must work reliably and honestly.

READ FIRST (every session, before editing anything)
AGENTS.md (this file), docs/API_CONTRACT.md, docs/EVENTS.md, docs/UI_SPEC.md. Do not edit those four files unless the prompt says so.

HARD RULES
1. Secrets. The API key comes only from the environment variable GNANI_API_KEY (loaded from .env with python-dotenv). Never print it, log it, hard-code it, commit it, or send it to the browser. .env must be in .gitignore. Browsers cannot set WebSocket headers, so the backend always holds the Gnani connection.
2. No guessing about the Gnani API. Use only endpoints, headers, fields and values written in docs/API_CONTRACT.md. If you need something that is not there, write TODO(verify) in the code, add a line to docs/OPEN_QUESTIONS.md, and continue with the safest option. Never invent a field name.
3. Synthetic data only. No real phone numbers, account numbers, Aadhaar, PAN, card numbers, OTPs, real people's names, or recorded calls. Use obviously fake values (98XXXXXXXX, 0000 0000 0000, "Test Customer"). Every demo call is labelled SYNTHETIC in the UI and README. Scam scripts are short, generic, based on public police and RBI advisories; they are detection test data, not persuasion material.
4. No voice cloning. Never call any voice-clone endpoint or imitate a real person's voice.
5. Credits are limited and the cost per unit is unknown. Never put a Gnani call in an unbounded loop. Every script or function that spends credits must: (a) support --dry-run, printing what it would send and an estimate in audio seconds or characters; (b) cache results on disk under data/cache/, keyed by sha256 of the request; (c) respect MAX_TTS_CHARS_PER_RUN (default 600) and MAX_STT_SECONDS_PER_RUN (default 180) from env and abort cleanly when exceeded; (d) add what it used to data/usage_ledger.json; (e) on HTTP 429 retry at most 2 times with exponential backoff; on 403 stop immediately and say the key or credits may be exhausted.
6. Honest demo. The UI and logs always show the audio source mode: LIVE MIC, FILE, REPLAY or MOCK. Mock and replay are never presented as live. Any number shown in the UI or README comes from data/eval/results.json or a run log, never typed by hand.
7. Challenge fit. The UI footer and README visibly name "Gnani Prisma v2.5" and "Gnani Timbre". Do not use Evon or the Agent Builder. One entry, solo.

FIXED TECH STACK (do not add, swap or upgrade anything unasked)
Backend: Python 3.10+, fastapi, uvicorn[standard], websockets (version 13 or newer; the header argument is additional_headers), httpx, python-dotenv, pydantic, numpy, soundfile, pyyaml, jiwer, pytest. System tool: ffmpeg.
Frontend: plain HTML, CSS and vanilla JavaScript (ES modules). No npm, no bundler, no framework, no CDN scripts, no icon libraries. The only external resource allowed is the Google Fonts stylesheet named in docs/UI_SPEC.md, and the page must still work if it fails to load. Charts are hand-written inline SVG.
Run command that must always work: uvicorn backend.main:app --reload --port 8000, then open http://localhost:8000

FOLDER LAYOUT (fixed; create only what the current phase needs)
backend/   config.py, usage.py, gnani_errors.py, gnani_stt.py (REST), gnani_stream.py (WebSocket), gnani_tts.py, audio_utils.py, events.py, sources.py, warning.py, orchestrator.py, metrics.py, main.py, scorer/ (normalize.py, matching.py, rules_loader.py, engine.py)
rules/     scam_rules_<lang>.json
frontend/  index.html, report.html, css/, js/, assets/
scripts/   smoke_stt.py, smoke_tts.py, stream_file.py, gen_corpus.py, degrade_audio.py, run_eval.py, demo.py
data/      scripts/ (call scripts), calls/ (audio), transcripts/, cache/, runs/, eval/, mock/ (mock_call.json)
tests/     test_*.py, fixtures/ (calls.json)
docs/      API_CONTRACT.md, EVENTS.md, UI_SPEC.md, OPEN_QUESTIONS.md, ARCHITECTURE.md

CODE RULES
- One responsibility per file; Python files under 200 lines, CSS files under 300. Split instead of growing.
- Complete files only. Never write "rest unchanged", "...", or a placeholder comment in place of code.
- Type hints on all Python functions; short docstrings; async for network I/O; use the logging module, not print, except for script output meant for the user.
- Network failures must never crash the server; send an error event to the UI instead (see docs/EVENTS.md).
- No global mutable state except config. No hidden sleeps to "make it work".
- Accessibility: contrast at least 4.5:1, prefers-reduced-motion respected, visible keyboard focus, an ARIA live region announces risk-level changes, colour is never the only signal.
- Privacy: live-microphone runs are not saved to disk unless SAVE_LIVE_RUNS=true.

HOW TO WORK
1. Do exactly what the phase prompt asks. No extra features, no refactors of earlier phases, no renames or moves of earlier files.
2. Start by listing the files you will create or change. If that list does not match the prompt, stop and ask.
3. Run the verification commands from the prompt. Never say something works unless you ran it and saw the output; otherwise write "not run" and why.
4. If a command fails, read the error, try at most 2 fixes, then stop and report the exact error. Do not loop.
5. If the key is missing from .env, skip the steps that need it, say so, and finish everything else.
6. End with a PHASE REPORT: files created or changed, commands run with results, anything not verified, open questions. Then stop. Do not start the next phase.
