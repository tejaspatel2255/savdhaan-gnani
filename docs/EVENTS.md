# SAVDHAAN INTERNAL PROTOCOL (backend <-> browser)

SERVING: FastAPI serves frontend/ at / (index.html), /report.html, /css, /js, /assets. Browser opens ONE WebSocket: ws://localhost:8000/ws/ui . The server pushes JSON text frames; the browser sends nothing except {"type":"hello"} on open. Control uses REST.

REST
GET  /api/health -> {"ok":true,"gnani_key_present":bool,"version":"0.1"}
GET  /api/calls -> {"calls":[{"id","title","label":"scam"|"legit","lang","duration_s","modes":["mock","replay","file"]}]} built from data/mock, data/transcripts and data/calls/manifest.json
POST /api/session/start  body {"mode":"mock"|"replay"|"file"|"mic","call_id":str|null,"lang":"hi-IN","sample_rate":8000,"danger":60,"careful":30,"speak_warning":true} -> {"session_id":str}. Only one session at a time; a second start returns 409.
POST /api/session/stop  body {"session_id":str} -> {"ok":true}. Must end the session cleanly and still emit session(ended) and summary.
GET  /api/audio/{name}.wav -> cached warning audio.
GET  /api/usage -> contents of data/usage_ledger.json plus caps.
GET  /api/eval -> data/eval/results.json (404 if absent).
Mic audio (Phase 5B only): ws://localhost:8000/ws/mic?session_id=ID, browser sends binary PCM signed 16-bit little-endian mono at 16000 Hz.

EVERY WS MESSAGE has: type (string), session_id (string), seq (int, increases by 1), t (float, seconds of CALL AUDIO elapsed when the event happened; 0.0 at audio start). Fields below are in addition.

TYPES (server to browser)
session: {state:"starting"|"listening"|"alerting"|"ended"|"error", mode:"mock"|"replay"|"file"|"mic", mode_label:"MOCK"|"REPLAY"|"FILE"|"LIVE MIC", call_title:str, synthetic:bool, lang:str, models:{stt:"Gnani Prisma v2.5",tts:"Gnani Timbre v3.0"}, thresholds:{careful:30,danger:60}}
audio_level: {rms:float 0..1} about 10 per second while audio flows, computed from the PCM actually being sent (zero in mock mode unless simulated)
segment_processing: {} sent when Gnani says speech ended and the transcript is being produced (UI blinks)
transcript: {segment_index:int, segment_id:str, text:str, audio_duration_ms:int, stt_latency_ms:int|null}
risk: {segment_index:int, score:int 0..100, level:"calm"|"careful"|"danger", delta:int, hits:[{rule_id:str, category:str, label_en:str, label_hi:str, matched:str, weight:int, polarity:"raise"|"dampen"}], categories:{category:count}}
alert: {score:int, level:"danger", reasons:[up to 3 hits], warning:{text:str, lang:str, voice:str, status:"generating"|"ready"|"skipped"|"failed"}} sent exactly once per session, the moment score first reaches the danger threshold
warning_audio: {audio_url:str|null, duration_s:float|null, text:str, cached:bool, reason:str|null} sent once after alert; audio_url is null when speaking is off, mocked without a cached file, or failed (reason says why)
family_alert: {contact_label:"Trusted contact (simulated)", message:str, simulated:true} sent once, right after alert. Nothing is ever sent to a real phone.
error: {code:"no_key"|"auth"|"rate_limited"|"credits"|"network"|"stt_closed"|"tts_failed"|"cap_reached"|"bad_request"|"internal", message:str, recoverable:bool}
summary: {duration_s:float, segments:int, time_to_alert_s:float|null, max_score:int, final_level:str, categories:{category:count}, stt_latency_ms:{p50:int|null,p95:int|null}, credits_used:{stt_seconds:float, tts_chars:int}, mode:str, synthetic:bool}

ORDER: session(starting) -> session(listening) -> any number of [audio_level, segment_processing, transcript, risk] -> at most one [alert, warning_audio, family_alert] -> session(ended) -> summary. After a fatal error: error -> session(error) -> summary with partial data. summary is always last.

LEVELS: calm = score below careful (30); careful = 30 up to below danger; danger = at or above danger (60). Hysteresis: once alert has fired, level may not drop below careful for the rest of the session.

FILE FORMATS
data/transcripts/<name>.jsonl, one line per segment: {"t":float,"segment_index":int,"segment_id":str,"text":str,"audio_duration_ms":int,"latency":int|null}. t is call-audio seconds when the transcript arrived. Recorded from real Gnani output; used by REPLAY and by evaluation.
data/mock/mock_call.json: {"title":str,"lang":"hi-IN","segments":[{"t":float,"text":str,"audio_duration_ms":int}]}. Hand-written, synthetic, labelled MOCK everywhere. Runs through the real scorer.
data/calls/manifest.json: list of {"id","title","label":"scam"|"legit","lang","script_path","audio_path","noise":str,"duration_s":float,"first_cue_s":float|null}
data/runs/<session_id>.jsonl: every WS message sent, one per line.
