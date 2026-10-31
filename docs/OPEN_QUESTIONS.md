# Open Questions

## Credit cost per unit (fill after the first calls)

### Instructions on Reading Unit Costs from Dashboard:
1. Log in to https://app.gnani.ai/voice/usage and record your starting credit balance.
2. Run the pilot step: `python scripts/gen_corpus.py --split dev --pilot --go` (861 TTS characters).
3. Check the dashboard balance again:
   - `TTS cost per 1,000 characters = (Credits Deducted / 861) * 1,000`
   - Set in `.env`: `TTS_CREDITS_PER_1K_CHARS=<value>`
4. Run `python scripts/run_eval.py record --split dev --limit 1 --go` (~15 STT seconds).
5. Check the dashboard balance again:
   - `STT cost per minute = (Credits Deducted / Seconds) * 60`
   - Set in `.env`: `STT_CREDITS_PER_MINUTE=<value>`
6. Run `python scripts/credit_plan.py --balance <Current Balance>` to see the exact credit-safe breakdown.

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
- Phase 3 TTS Warning pack character count:
  - 5 Hindi warnings total 437 characters (generic: 97, arrest: 91, otp: 83, money: 95, remote: 71), safely below the MAX_TTS_CHARS_PER_RUN cap of 600 chars.
- Future option: calls read aloud by a volunteer instead of synthetic voices; would need consent and a README change.
