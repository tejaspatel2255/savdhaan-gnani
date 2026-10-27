"""Session lifecycle, concurrency, event dispatching, and source orchestration."""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from backend.config import Settings
from backend.events import (
    Emitter,
    build_alert_event,
    build_audio_level_event,
    build_error_event,
    build_family_alert_event,
    build_risk_event,
    build_segment_processing_event,
    build_session_event,
    build_summary_event,
    build_transcript_event,
    build_warning_audio_event,
)
from backend.gnani_errors import GnaniError
from backend.gnani_tts import synthesize as default_tts
from backend.metrics import build_summary
from backend.scorer import ScamScorer, load_pack, load_configured_packs
from backend.mic import MicSource
from backend.sources import FileSource, MockSource, ReplaySource, SourceEvent
from backend.warning import family_message, get_warning, pick_key
from backend import usage

logger = logging.getLogger(__name__)


class SessionBusy(Exception):
    """Raised when starting a new session while one is active."""
    pass


@dataclass
class StartSessionRequest:
    mode: str  # "mock", "replay", "file", "mic"
    call_id: Optional[str] = None
    lang: str = "hi-IN"
    sample_rate: int = 8000
    danger: int = 60
    careful: int = 30
    speak_warning: bool = True
    speed: float = 1.0


class SessionManager:
    """Manages active call session, event routing, rule scoring, and background tasks."""

    def __init__(
        self,
        settings: Settings,
        data_dir: str = "data",
        stt_base_url: str = "wss://api.vachana.ai",
        tts: Callable = default_tts,
    ) -> None:
        self.settings = settings
        self.data_dir = Path(data_dir)
        self.stt_base_url = stt_base_url
        self.tts = tts

        self._active_session_id: Optional[str] = None
        self._active_task: Optional[asyncio.Task] = None
        self._active_stop: Optional[asyncio.Event] = None
        self._active_emitter: Optional[Emitter] = None
        self._last_emitter: Optional[Emitter] = None

        # Active mic source reference for attach_mic()
        self._active_mic_source: Optional[MicSource] = None
        self._rule_packs: Dict[str, Any] = {}
        self._pack_routes = {
            "hi-IN": Path("rules/scam_rules_hi_en.json"),
            "en-IN": Path("rules/scam_rules_hi_en.json"),
            "gu-IN": Path("rules/scam_rules_gu.json"),
        }

    def _get_pack(self, lang: str):
        if lang not in self._rule_packs:
            # Check configured packs first
            if getattr(self.settings, "scorer_packs", None) and "," in self.settings.scorer_packs:
                self._rule_packs[lang] = load_configured_packs(self.settings.scorer_packs)
            elif lang == "gu-IN" and Path("rules/scam_rules_gu.json").exists():
                self._rule_packs[lang] = load_configured_packs("hi_en,gu")
            else:
                pack_path = self._pack_routes.get(lang, Path("rules/scam_rules_hi_en.json"))
                self._rule_packs[lang] = load_pack(pack_path)
        return self._rule_packs[lang]

    def is_busy(self) -> bool:
        return self._active_session_id is not None and self._active_task is not None and not self._active_task.done()

    def subscribe(self) -> asyncio.Queue:
        if self._active_emitter:
            return self._active_emitter.subscribe()
        if self._last_emitter:
            return self._last_emitter.subscribe()
        # Fallback dummy emitter
        dummy = Emitter("none")
        return dummy.subscribe()

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if self._active_emitter:
            self._active_emitter.unsubscribe(q)
        if self._last_emitter:
            self._last_emitter.unsubscribe(q)

    def history(self) -> List[Dict[str, Any]]:
        if self._active_emitter:
            return self._active_emitter.history()
        if self._last_emitter:
            return self._last_emitter.history()
        return []

    async def start(self, req: StartSessionRequest) -> str:
        """Start a new session. Validates parameters and raises SessionBusy if one runs."""
        if self.is_busy():
            raise SessionBusy("Another session is already active")

        # Validate thresholds
        if not (0 < req.careful < req.danger <= 100):
            raise ValueError(f"Invalid thresholds: careful={req.careful}, danger={req.danger}")

        if req.mode not in ("mock", "replay", "file", "mic"):
            raise ValueError(f"Unknown mode: {req.mode}")

        if req.mode == "mic" and not self.settings.key_present:
            raise ValueError("GNANI_API_KEY is required for mic mode")

        if req.mode == "replay":
            if not req.call_id:
                raise ValueError("call_id required for replay")
            rep_path = self.data_dir / "transcripts" / f"{req.call_id}.jsonl"
            if not rep_path.exists():
                raise ValueError(f"Unknown call_id for replay: {req.call_id}")

        if req.mode == "file":
            if not req.call_id:
                raise ValueError("call_id required for file mode")

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self._active_session_id = session_id
        self._active_stop = asyncio.Event()

        # Determine logging path
        if req.mode == "mic" and not self.settings.save_live_runs:
            log_path = None
        else:
            log_path = self.data_dir / "runs" / f"{session_id}.jsonl"

        emitter = Emitter(session_id, log_path=log_path)
        self._active_emitter = emitter
        self._last_emitter = emitter

        task = asyncio.create_task(self._run_session(req, emitter, self._active_stop))
        self._active_task = task
        return session_id

    async def stop(self, session_id: str) -> bool:
        """Stop active session cleanly."""
        if self._active_session_id != session_id or self._active_task is None:
            return False

        if self._active_stop:
            self._active_stop.set()

        try:
            await asyncio.wait_for(asyncio.shield(self._active_task), timeout=5.0)
        except asyncio.TimeoutError:
            self._active_task.cancel()
            try:
                await self._active_task
            except asyncio.CancelledError:
                pass
        return True

    async def _run_session(self, req: StartSessionRequest, emitter: Emitter, stop_event: asyncio.Event) -> None:
        mode_labels = {"mock": "MOCK", "replay": "REPLAY", "file": "FILE", "mic": "LIVE MIC"}
        mode_label = mode_labels.get(req.mode, req.mode.upper())
        synthetic = req.mode in ("mock", "replay", "file")
        thresholds = {"careful": req.careful, "danger": req.danger}

        # Track credits used during run
        ledger_before = usage.get_process_totals()

        # Step 1: session(starting)
        build_session_event(
            emitter,
            state="starting",
            mode=req.mode,
            mode_label=mode_label,
            call_title="",
            synthetic=synthetic,
            lang=req.lang,
            thresholds=thresholds,
            t=0.0,
        )

        # Build Source and call title
        call_title = ""
        source = None
        try:
            if req.mode == "mock":
                mock_path = self.data_dir / "mock" / "mock_call.json"
                if not mock_path.exists():
                    raise GnaniError("Mock call file missing", code="bad_request")
                try:
                    with open(mock_path, "r", encoding="utf-8") as f:
                        call_title = json.load(f).get("title", "Digital arrest call")
                except Exception:
                    call_title = "Digital arrest call"
                source = MockSource(mock_path, speed=req.speed)

            elif req.mode == "replay":
                if not req.call_id:
                    raise GnaniError("call_id required for replay", code="bad_request")
                rep_path = self.data_dir / "transcripts" / f"{req.call_id}.jsonl"
                if not rep_path.exists():
                    raise GnaniError(f"Transcript not found for replay: {req.call_id}", code="bad_request")
                call_title = req.call_id
                source = ReplaySource(rep_path, speed=req.speed)

            elif req.mode == "file":
                if not self.settings.key_present:
                    raise GnaniError("GNANI_API_KEY is not configured", code="no_key", recoverable=False)
                if not req.call_id:
                    raise GnaniError("call_id required for file mode", code="bad_request")

                # Try audio file directly or manifest
                wav_path = self.data_dir / "calls" / f"{req.call_id}.wav"
                if not wav_path.exists():
                    # check manifest
                    manifest_path = self.data_dir / "calls" / "manifest.json"
                    found = False
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, "r", encoding="utf-8") as f:
                                manifest = json.load(f)
                            for entry in manifest:
                                if entry.get("id") == req.call_id:
                                    wav_path = Path(entry.get("audio_path", ""))
                                    call_title = entry.get("title", req.call_id)
                                    found = True
                                    break
                        except Exception:
                            pass
                    if not found and not wav_path.exists():
                        raise GnaniError(f"Audio file not found: {req.call_id}", code="bad_request")
                else:
                    call_title = req.call_id

                source = FileSource(
                    audio_path=wav_path,
                    lang=req.lang,
                    rate=req.sample_rate,
                    settings=self.settings,
                    base_url=self.stt_base_url,
                )

            elif req.mode == "mic":
                mic_source = MicSource(self.settings, req.lang, base_url=self.stt_base_url)
                self._active_mic_source = mic_source
                call_title = "Live microphone"
                source = mic_source

        except GnaniError as ge:
            build_error_event(emitter, code=ge.code, message=ge.message, recoverable=ge.recoverable)
            build_session_event(emitter, state="error", mode=req.mode, mode_label=mode_label,
                                call_title=call_title, synthetic=synthetic, lang=req.lang, thresholds=thresholds)
            self._emit_final_summary(emitter, req, synthetic, ledger_before, 0.0, 0, None, 0, "calm", {}, [])
            self._cleanup()
            return
        except Exception as exc:
            logger.exception("Unexpected error initializing source")
            build_error_event(emitter, code="internal", message="Internal initialization error", recoverable=False)
            build_session_event(emitter, state="error", mode=req.mode, mode_label=mode_label,
                                call_title=call_title, synthetic=synthetic, lang=req.lang, thresholds=thresholds)
            self._emit_final_summary(emitter, req, synthetic, ledger_before, 0.0, 0, None, 0, "calm", {}, [])
            self._cleanup()
            return

        # Step 2: session(listening)
        build_session_event(
            emitter,
            state="listening",
            mode=req.mode,
            mode_label=mode_label,
            call_title=call_title,
            synthetic=synthetic,
            lang=req.lang,
            thresholds=thresholds,
            t=0.0,
        )

        pack = self._get_pack(req.lang)
        scorer = ScamScorer(pack, careful=req.careful, danger=req.danger)

        warning_task: Optional[asyncio.Task] = None
        alert_t: Optional[float] = None
        stt_latencies: List[int] = []
        segments_count = 0
        overall_categories: Dict[str, int] = {}
        largest_t = 0.0
        final_level = "calm"

        async def source_sink(ev: SourceEvent) -> None:
            nonlocal alert_t, segments_count, largest_t, final_level, warning_task
            largest_t = max(largest_t, ev.t)

            if ev.kind == "level":
                build_audio_level_event(emitter, rms=ev.data.get("rms", 0.0), t=ev.t)

            elif ev.kind == "processing":
                build_segment_processing_event(emitter, t=ev.t)

            elif ev.kind == "transcript":
                segments_count += 1
                lat = ev.data.get("stt_latency_ms")
                if lat is not None:
                    stt_latencies.append(lat)

                build_transcript_event(
                    emitter,
                    segment_index=ev.data["segment_index"],
                    segment_id=ev.data["segment_id"],
                    text=ev.data["text"],
                    audio_duration_ms=ev.data["audio_duration_ms"],
                    stt_latency_ms=lat,
                    t=ev.t,
                )

                # Feed into scorer
                up = scorer.feed(ev.data["text"], segment_index=ev.data["segment_index"])
                final_level = up.level

                # Update cumulative categories
                for h in up.hits:
                    if h.polarity == "raise":
                        overall_categories[h.category] = overall_categories.get(h.category, 0) + 1

                build_risk_event(
                    emitter,
                    segment_index=up.segment_index,
                    score=up.score,
                    level=up.level,
                    delta=up.delta,
                    hits=[h.to_event() for h in up.hits],
                    categories=up.categories,
                    t=ev.t,
                )

                # Danger trigger
                if up.alert and alert_t is None:
                    alert_t = ev.t
                    key = pick_key(up.reasons)
                    warn_status = "generating" if (req.speak_warning and self.settings.key_present) else "skipped"

                    # (1) alert
                    build_alert_event(
                        emitter,
                        score=up.score,
                        level="danger",
                        reasons=[h.to_event() for h in up.reasons],
                        warning={
                            "text": "",  # filled in warning_audio
                            "lang": req.lang,
                            "voice": self.settings.warning_voice,
                            "status": warn_status,
                        },
                        t=ev.t,
                    )

                    # (2) family_alert
                    fam_msg = family_message(req.lang, up.reasons)
                    build_family_alert_event(emitter, message=fam_msg, t=ev.t)

                    # (3) launch get_warning background task
                    warning_task = asyncio.create_task(
                        self._handle_warning_audio(emitter, req, key, up.reasons, ev.t)
                    )

            elif ev.kind == "error":
                code = ev.data.get("code", "internal")
                msg = ev.data.get("message", "Stream error")
                rec = ev.data.get("recoverable", False)
                build_error_event(emitter, code=code, message=msg, recoverable=rec, t=ev.t)

        try:
            await source.run(source_sink, stop_event)
        except GnaniError as ge:
            build_error_event(emitter, code=ge.code, message=ge.message, recoverable=ge.recoverable, t=largest_t)
            if not ge.recoverable:
                build_session_event(emitter, state="error", mode=req.mode, mode_label=mode_label,
                                    call_title=call_title, synthetic=synthetic, lang=req.lang, thresholds=thresholds, t=largest_t)
                self._emit_final_summary(emitter, req, synthetic, ledger_before, largest_t, segments_count,
                                         alert_t, scorer.max_score, final_level, overall_categories, stt_latencies)
                self._cleanup()
                return
        except Exception as exc:
            logger.exception("Unexpected error during session stream")
            build_error_event(emitter, code="internal", message="Stream processing error", recoverable=False, t=largest_t)
            build_session_event(emitter, state="error", mode=req.mode, mode_label=mode_label,
                                call_title=call_title, synthetic=synthetic, lang=req.lang, thresholds=thresholds, t=largest_t)
            self._emit_final_summary(emitter, req, synthetic, ledger_before, largest_t, segments_count,
                                     alert_t, scorer.max_score, final_level, overall_categories, stt_latencies)
            self._cleanup()
            return

        # Await warning audio task if active (up to 12s)
        if warning_task is not None:
            try:
                await asyncio.wait_for(warning_task, timeout=12.0)
            except Exception:
                pass

        # Normal ending
        build_session_event(
            emitter,
            state="ended",
            mode=req.mode,
            mode_label=mode_label,
            call_title=call_title,
            synthetic=synthetic,
            lang=req.lang,
            thresholds=thresholds,
            t=largest_t,
        )

        self._emit_final_summary(
            emitter,
            req=req,
            synthetic=synthetic,
            ledger_before=ledger_before,
            duration_s=largest_t,
            segments=segments_count,
            time_to_alert_s=alert_t,
            max_score=scorer.max_score,
            final_level=final_level,
            categories=overall_categories,
            latencies=stt_latencies,
            t=largest_t,
        )
        self._cleanup()

    async def _handle_warning_audio(
        self,
        emitter: Emitter,
        req: StartSessionRequest,
        key: str,
        reasons: List[Any],
        event_t: float,
    ) -> None:
        if not req.speak_warning:
            build_warning_audio_event(emitter, audio_url=None, duration_s=None, text="", cached=False, reason="speaking_off", t=event_t)
            return

        if not self.settings.key_present:
            build_warning_audio_event(emitter, audio_url=None, duration_s=None, text="", cached=False, reason="no_key", t=event_t)
            return

        try:
            w_res = await get_warning(
                lang=req.lang,
                key=key,
                voice=self.settings.warning_voice,
                model=self.settings.warning_model,
                dry_run=False,
                tts_func=self.tts,
            )
            build_warning_audio_event(
                emitter,
                audio_url=w_res.url,
                duration_s=w_res.duration_s,
                text=w_res.text,
                cached=w_res.cached,
                reason=None,
                t=event_t,
            )
            # Mute mic for warning duration so speaker audio is not transcribed
            if req.mode == "mic" and self._active_mic_source and w_res.duration_s:
                await self._active_mic_source.mute(w_res.duration_s + 0.7)
        except GnaniError as ge:
            reason = "cap_reached" if ge.code == "cap_reached" else "tts_failed"
            build_warning_audio_event(emitter, audio_url=None, duration_s=None, text="", cached=False, reason=reason, t=event_t)
            build_error_event(emitter, code=ge.code, message=ge.message, recoverable=True, t=event_t)
        except Exception as exc:
            logger.exception("Warning audio generation error")
            build_warning_audio_event(emitter, audio_url=None, duration_s=None, text="", cached=False, reason="tts_failed", t=event_t)
            build_error_event(emitter, code="tts_failed", message=str(exc), recoverable=True, t=event_t)

    def _emit_final_summary(
        self,
        emitter: Emitter,
        req: StartSessionRequest,
        synthetic: bool,
        ledger_before: Dict[str, Any],
        duration_s: float,
        segments: int,
        time_to_alert_s: Optional[float],
        max_score: int,
        final_level: str,
        categories: Dict[str, int],
        latencies: List[int],
        t: Optional[float] = None,
    ) -> None:
        ledger_after = usage.get_process_totals()
        credits_used = {
            "stt_seconds": round(ledger_after["stt_seconds"] - ledger_before["stt_seconds"], 2),
            "tts_chars": ledger_after["tts_chars"] - ledger_before["tts_chars"],
        }
        summary_payload = build_summary(
            duration_s=duration_s,
            segments=segments,
            time_to_alert_s=time_to_alert_s,
            max_score=max_score,
            final_level=final_level,
            categories=categories,
            latencies=latencies,
            credits_used=credits_used,
            mode=req.mode,
            synthetic=synthetic,
        )
        build_summary_event(
            emitter,
            t=t,
            **summary_payload,
        )

    def _cleanup(self) -> None:
        self._active_session_id = None
        self._active_task = None
        self._active_stop = None
        self._active_emitter = None
        self._active_mic_source = None

    def attach_mic(self, session_id: str, websocket: Any) -> bool:
        """Signal mic attach for the given session. Returns False if not applicable."""
        if self._active_session_id != session_id or self._active_mic_source is None:
            return False
        self._active_mic_source.attach(websocket)
        return True

    async def push_mic(self, session_id: str, data: bytes) -> None:
        """Forward a binary chunk from /ws/mic to the active MicSource queue."""
        if self._active_session_id == session_id and self._active_mic_source:
            await self._active_mic_source.push(data)

    async def stop_mic(self, session_id: str) -> None:
        """Signal end-of-stream from the browser to the active MicSource."""
        if self._active_session_id == session_id and self._active_mic_source:
            await self._active_mic_source.stop_push()
