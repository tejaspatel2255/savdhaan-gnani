# Savdhaan Architecture

Savdhaan is a client-server live scam detection system that couples low-latency speech streaming with deterministic, explainable conversational reasoning.

## 1. Live Call Defense Pipeline

```mermaid
flowchart LR
    subgraph AudioSource ["Audio Ingestion"]
        A[Caller Audio / File / Mic] --> B[Browser Web Audio / Streamer]
    end

    subgraph Backend ["Savdhaan Backend (FastAPI + AsyncIO)"]
        B -->|PCM 8kHz / 16kHz| C["/ws/mic or /api/session"]
        C --> D["Gnani Prisma v2.5 STT (Realtime WS)"]
        D -->|VAD Transcript Segments| E["ScamScorer Engine"]
        E -->|Rolling Window + Combos + Negation| F["Risk & Score Events"]
        F --> G["/ws/ui Event Emitter"]
        
        E -.->|Danger Threshold Reached| H["Warning Coordinator"]
        H -->|Text & Lang| I["Gnani Timbre v3.0 TTS"]
        I -->|Warning Audio Cache| J["Warning Audio Dispatch"]
        H --> K["Simulated Family Alert"]
    end

    subgraph Frontend ["Nazar Control Room (Plain HTML / CSS / Vanilla JS)"]
        G --> L["The Eye Ring Gauge & Nazar Pupil"]
        G --> M["The Tape (Receipt Slip Log)"]
        G --> N["The Why Evidence List"]
        J --> O["Stamp Slam & Listener Phone Warning"]
        K --> P["Simulated Family Notification Card"]
    end
```

### Explanation of Live Flow
1. **Audio Ingestion**: Audio originates from a live microphone or audio file, is framed into standard 1024-byte PCM chunks, and forwarded over WebSocket to the FastAPI backend.
2. **Speech Recognition**: The backend proxies the PCM stream to Gnani Prisma v2.5 STT over a persistent WebSocket connection with Voice Activity Detection (VAD).
3. **Conversational Risk Scoring**: Each transcript segment is tokenized, normalized (stripping punctuation, normalising nukta and chandrabindu), and evaluated by `ScamScorer` using dual-language rule packs (Hindi, English, Gujarati). Evidence decays over a rolling window, combo rules add non-linear bonuses for dangerous category pairings, and negation guards suppress false positives.
4. **Protective Response**: When risk crosses the danger threshold (score ≥ 60), the backend triggers Gnani Timbre v3.0 TTS to speak a localized, calm intervention directly to the listener while an evil-eye rubber stamp slams onto the control tape and a simulated alert notifies trusted contacts.

---

## 2. Evaluation & Measurement Pipeline

```mermaid
flowchart LR
    M1["Call Manifest (manifest.json)"] --> R1["scripts/run_eval.py record"]
    R1 -->|Gnani Prisma Realtime WS| T1["Saved Transcripts (data/transcripts/*.jsonl)"]
    T1 --> S1["scripts/run_eval.py score"]
    M1 -.->|Ceiling Baseline| S1
    S1 -->|ScamScorer Offline| RES["data/eval/results.json"]
    RES --> K1["Khata Ledger Page (/report.html)"]
```

### Explanation of Evaluation Flow
1. **One-Time Recording**: `scripts/run_eval.py record` streams synthetic call recordings from the manifest through Gnani Prisma once to create persistent, real-world transcript logs (`.jsonl`).
2. **Offline Scoring**: `scripts/run_eval.py score` executes entirely offline without spending credits, feeding transcript lines through `ScamScorer` to measure Recall, False Alarm Rates, Time-to-Alert, and Wilson Score 95% Confidence Intervals.
3. **Honest Ledger**: All computed metrics are written to `results.json` and consumed directly by the Khata report page (`/report.html`) without any manually typed statistics.
