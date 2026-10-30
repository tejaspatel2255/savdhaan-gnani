# Live Mode Guide (Savdhaan)

Savdhaan provides real-time microphone listening and analysis via **Gnani Prisma v2.5** and **Gnani Timbre**.

## How It Works
1. Click **Listen live** in the web header.
2. Select your listening language (`Hindi · हिंदी`, `Gujarati · ગુજરાતી`, or `English · Hinglish`).
3. Speak or hold your phone on speakerphone near your computer microphone.
4. Audio frames (16-bit PCM, 8kHz/16kHz) stream through WebSocket to backend `MicSource`, which relays chunks to Gnani Prisma.
5. Transcribed text segments are scored immediately by the Chowkidar rule engine.
6. If cumulative risk crosses the threshold, the **Nazar Eye** turns danger red, an authoritative voice warning plays, and a call receipt is prepared.

## Security & Privacy
- **Local-Only by Default**: Live listening is restricted to loopback connections (`127.0.0.1`, `localhost`). External clients receive HTTP 403 / WS 4003 unless `ALLOW_REMOTE_LIVE=1` is explicitly set.
- **Credit Guards**: Capped at `MAX_STT_SECONDS_PER_RUN` (default 180s) to strictly prevent runaway credit usage.
- **Zero Disk Recording**: Audio buffers live purely in memory and are discarded when the session ends unless `SAVE_LIVE_RUNS=true` is enabled.
