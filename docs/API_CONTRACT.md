# GNANI API CONTRACT (verified from docs.gnani.ai; do not guess beyond this)

HOST: api.vachana.ai. Auth header on every call: X-API-Key-ID (REST) or x-api-key-id (WebSocket upgrade). Error body shape: {"success": false, "error": {"type": "...", "message": "..."}}. Codes: 400 INVALID_REQUEST_ERROR, 403 FORBIDDEN (check key, org status or credits), 429 RATE_LIMIT_ERROR, 500 API_ERROR, 503 SERVICE_UNAVAILABLE. Max text length and rate limits are NOT documented.

== STT REALTIME (WebSocket) - used for live and file calls ==
URL: wss://api.vachana.ai/stt/v3/stream
Headers set at connect (fixed for the connection): x-api-key-id (required), lang_code (required, BCP-47), x-sample-rate (8000, 16000, 44100 or 48000; default 16000; must match the audio), x-format (verbatim default, or transcribe for inverse text normalisation), itn_native_numerals (false default), x-bias-list (up to 100 single words, letters only, JSON array or comma separated; use ASCII-safe JSON escapes for Indic words; needs x-bias-score; use with x-format verbatim), x-bias-score (0.0, 0.5, 1.0, 1.5 or 2.0; start at 1.0).
VAD headers: x-vad-threshold (default 0.7, range 0-1), x-min-silence-ms (default 500, range 100-2000), x-min-speech-ms (default 100, 200 at 8 kHz, range 50-2000), x-min-segment-ms (default 120, range 100-1000), x-max-speech-s (disabled by default, range 5-120). Docs' telephony preset: 8000 Hz, x-vad-threshold 0.7, x-min-speech-ms 200, x-min-silence-ms 500.
Audio: binary frames only. Raw PCM signed 16-bit little-endian, mono. EVERY frame is exactly 1024 bytes (512 samples). Send at real-time cadence: one frame every 32 ms at 16 kHz, every 64 ms at 8 kHz. Never burst. Pad a final partial frame with zero bytes.
Server JSON messages: connected {type, message, timestamp, config{sample_rate, chunk_size}}; processing {type, timestamp} (speech end detected); transcript {type, timestamp, text, audio_duration_ms, segment_id, segment_index, latency}; error {type, timestamp, message}; settings_updated {type, timestamp, config}. One transcript per VAD segment, so a transcript only arrives after the speaker pauses. latency = ms from end of speech to delivery. Session hard cap: 15 minutes. Auth failure closes the socket (close code 4001).
Python: websockets.connect(url, additional_headers={...}) on websockets 13+.
UNVERIFIED, do not use: partial transcripts (x-partials, partial_transcript), the /stt/v4/stream route, multi_lang_codes.

== STT REST - used for smoke tests and evaluation ==
POST https://api.vachana.ai/stt/v3 (multipart/form-data), header X-API-Key-ID. Fields: audio_file (WAV, MP3, OGG, FLAC, AAC or M4A; max 60 s, ideal 30 s or less; auto-converted to 16 kHz mono), language_code (required), format (verbatim or transcribe), itn_native_numerals, bias_list, bias_score. 200 response: {success, request_id, timestamp, transcript}.
Language codes: bn-IN, en-IN, gu-IN, hi-IN, kn-IN, ml-IN, mr-IN, pa-IN, ta-IN, te-IN. en-IN accepts English-Hindi mixed audio and writes Latin script; hi-IN writes Devanagari. There is no separate Hinglish code for STT. Which script code-mixed speech comes out in must be measured in Phase 1, not assumed.

== TTS REST - used for warnings and test calls ==
POST https://api.vachana.ai/api/v1/tts/inference, headers X-API-Key-ID and Content-Type: application/json. Response 200 is the audio as binary bytes.
Body: text (required), model (required: timbre-v3.0 or timbre-v2.5; ALWAYS pass it, never rely on a default), voice (required, must belong to that model), language (required: auto, hi-IN, en-IN, ta-IN, te-IN, kn-IN, ml-IN, mr-IN, pa-IN, bn-IN, gu-IN, hi-en), speed (optional, 0.85 to 1.15, default 1.0), audio_config (required): sample_rate (8000, 16000, 22050, 24000, 44100 or 48000; default 48000), num_channels (1), sample_width (2), container (wav, raw, mp3, ogg, mulaw, alaw; mulaw and alaw force 8000 Hz), encoding (linear_pcm default), bitrate (mp3 only).
Default call for this project: model timbre-v3.0, container wav, encoding linear_pcm, sample_rate 24000, num_channels 1, sample_width 2.
Timbre v3.0 voices (all speak all 10 languages): female Shivani (warm, empathetic), Tarika (warm, reassuring), Kalpana (composed), Chetana (gentle), Lakshmi (expressive), Vasudha (expressive), Riyaa (confident); male Avinash (professional, firm), Prakash (deliberate), Harshad (professional), Shubham (energetic), Devansh (young, conversational), Yashraj (warm narrator).
Project voice choices (ours, not Gnani's): warning voice Shivani; test-call caller Avinash; test-call listener Chetana.
Audio tags (timbre-v3.0 only, case-sensitive, applies from its position to the end or the next tag, unknown tags are stripped, tags are billed as characters): <coughs> <excited> <exhales> <giggle> <laugh> <pauses> <shouting> <sigh> <slow> <sniffles> <whispers> <yawns> <clears throat>. For warnings use at most <pauses> and <slow>. Never <laugh>, <giggle> or <shouting>.
Text normalisation is automatic: write numbers, rupees and dates naturally. OTP and PIN digits are read one by one. Include the year in dates. Mixed Devanagari plus Latin text is detected as Hinglish under language auto. Latin-only text is normalised as English under auto, so set language explicitly for another language. Pass language mr explicitly for Marathi.
TTS streaming (SSE POST /api/v1/tts/sse, WebSocket wss://api.vachana.ai/api/v1/tts) exists, but this project uses REST for short warnings. SSE events: start, chunk {chunk_index, audio base64, is_final}, complete, error. Whether the WAV header is only in the first chunk is undocumented.

== CREDITS AND NAMING ==
5,000 programme credits per registration. Cost per audio second or character is NOT documented; read the usage on the dashboard at app.gnani.ai/voice after the first calls. A marketing page mentions free TTS minutes: unverified.
The marketing page shows model vachana-voice-v3 and voice Karan; the docs say timbre-v3.0 and the voices above. Use the docs. If the API returns 400, print the error message (it lists supported values), do not guess, and note it in docs/OPEN_QUESTIONS.md.
Do not use the gnani-vachana SDK (its TTS default model timbre-v2.0 is no longer served). Use httpx and websockets directly.
Display names in the UI: Gnani Prisma v2.5 (speech to text), Gnani Timbre v3.0 (text to speech).

== AUDIO CONVERSION ==
To raw frames: ffmpeg -y -i in.wav -ac 1 -ar 8000 -f s16le out.pcm (use -ar 16000 for 16 kHz).
