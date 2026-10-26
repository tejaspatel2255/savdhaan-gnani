# Open Questions

## Credit cost per unit (fill after the first calls)

- STT REST cost per audio second or minute: 3.28 s consumed in smoke test (check dashboard app.gnani.ai/voice/usage to note deducted credits)
- STT WebSocket streaming cost per minute:
- TTS REST cost per character: 40 chars consumed in smoke test (check dashboard app.gnani.ai/voice/usage to note deducted credits)
- Free tier / programme credit allowance details: 5,000 credits allocated on signup

## Other

- Exact latency breakdown for live streaming over wss://api.vachana.ai/stt/v3/stream.
- Best language code behavior for Hinglish code-mixed audio (en-IN vs hi-IN) to be measured in Phase 1:
  - `hi-IN` transcript: "नमस्ते, यह सावधान का एक छोटा परीक्षण है।" (Devanagari script, latency 75 ms)
  - `en-IN` transcript: "namaste ye savdhan ka ek chhota parikshan hai" (Latin script / Hinglish, latency 130 ms)
  - Both modes achieved ultra-low latency (<150 ms) on the live WebSocket stream.
