"""Event emitter, message builders, and subscription queues."""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


class Emitter:
    """Session event emitter maintaining sequence numbers, monotonic timestamps,
    subscriber queues, history, and optional JSONL file logging.
    """

    def __init__(self, session_id: str, log_path: Optional[Union[str, Path]] = None) -> None:
        self.session_id = session_id
        self.log_path = Path(log_path) if log_path else None
        self._seq = 0
        self._last_t: float = 0.0
        self._history: List[Dict[str, Any]] = []
        self._subscribers: Set[asyncio.Queue] = set()

        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def subscribe(self) -> asyncio.Queue:
        """Return a subscriber queue (maxsize=1000). Drops oldest on overflow."""
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """Remove a subscriber queue."""
        self._subscribers.discard(q)

    def history(self) -> List[Dict[str, Any]]:
        """Return a copy of the emitted message history."""
        return list(self._history)

    def emit(self, type: str, t: Optional[float] = None, **fields: Any) -> Dict[str, Any]:
        """Build and emit an event. seq increments by 1; t is monotonic."""
        if t is None:
            event_t = self._last_t
        else:
            # t never decreases
            event_t = max(round(float(t), 3), self._last_t)
        self._last_t = event_t

        msg: Dict[str, Any] = {
            "type": type,
            "session_id": self.session_id,
            "seq": self._seq,
            "t": event_t,
        }
        msg.update(fields)
        self._seq += 1

        # Keep history up to 5000 items
        if len(self._history) >= 5000:
            self._history.pop(0)
        self._history.append(msg)

        # Log to disk if configured
        if self.log_path:
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            except Exception:
                pass

        # Push to subscribers
        for q in list(self._subscribers):
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass

        return msg


# --- Message Builders matching docs/EVENTS.md exactly ---

def build_session_event(
    emitter: Emitter,
    state: str,
    mode: str,
    mode_label: str,
    call_title: str,
    synthetic: bool,
    lang: str,
    thresholds: Dict[str, int],
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "session",
        t=t,
        state=state,
        mode=mode,
        mode_label=mode_label,
        call_title=call_title,
        synthetic=synthetic,
        lang=lang,
        models={"stt": "Gnani Prisma v2.5", "tts": "Gnani Timbre v3.0"},
        thresholds=thresholds,
    )


def build_audio_level_event(emitter: Emitter, rms: float, t: Optional[float] = None) -> Dict[str, Any]:
    return emitter.emit("audio_level", t=t, rms=round(float(rms), 3))


def build_segment_processing_event(emitter: Emitter, t: Optional[float] = None) -> Dict[str, Any]:
    return emitter.emit("segment_processing", t=t)


def build_transcript_event(
    emitter: Emitter,
    segment_index: int,
    segment_id: str,
    text: str,
    audio_duration_ms: int,
    stt_latency_ms: Optional[int],
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "transcript",
        t=t,
        segment_index=segment_index,
        segment_id=segment_id,
        text=text,
        audio_duration_ms=audio_duration_ms,
        stt_latency_ms=stt_latency_ms,
    )


def build_risk_event(
    emitter: Emitter,
    segment_index: int,
    score: int,
    level: str,
    delta: int,
    hits: List[Dict[str, Any]],
    categories: Dict[str, int],
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "risk",
        t=t,
        segment_index=segment_index,
        score=score,
        level=level,
        delta=delta,
        hits=hits,
        categories=categories,
    )


def build_alert_event(
    emitter: Emitter,
    score: int,
    level: str,
    reasons: List[Dict[str, Any]],
    warning: Dict[str, Any],
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "alert",
        t=t,
        score=score,
        level=level,
        reasons=reasons,
        warning=warning,
    )


def build_warning_audio_event(
    emitter: Emitter,
    audio_url: Optional[str],
    duration_s: Optional[float],
    text: str,
    cached: bool,
    reason: Optional[str],
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "warning_audio",
        t=t,
        audio_url=audio_url,
        duration_s=duration_s,
        text=text,
        cached=cached,
        reason=reason,
    )


def build_family_alert_event(
    emitter: Emitter,
    message: str,
    t: Optional[float] = None,
    message_en: Optional[str] = None,
) -> Dict[str, Any]:
    """`message` is in the listener's language; `message_en` is the English version shown first in the UI."""
    return emitter.emit(
        "family_alert",
        t=t,
        contact_label="Trusted contact (simulated)",
        message=message,
        message_en=message_en or message,
        simulated=True,
    )


def build_error_event(
    emitter: Emitter,
    code: str,
    message: str,
    recoverable: bool,
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "error",
        t=t,
        code=code,
        message=message,
        recoverable=recoverable,
    )


def build_usage_tick_event(
    emitter: Emitter,
    stt_seconds_used: float,
    stt_seconds_cap: float,
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "usage_tick",
        t=t,
        stt_seconds_used=round(stt_seconds_used, 1),
        stt_seconds_cap=round(stt_seconds_cap, 1),
    )


def build_summary_event(
    emitter: Emitter,
    duration_s: float,
    segments: int,
    time_to_alert_s: Optional[float],
    max_score: int,
    final_level: str,
    categories: Dict[str, int],
    stt_latency_ms: Dict[str, Optional[int]],
    credits_used: Dict[str, Union[float, int]],
    mode: str,
    synthetic: bool,
    t: Optional[float] = None,
) -> Dict[str, Any]:
    return emitter.emit(
        "summary",
        t=t,
        duration_s=round(duration_s, 2),
        segments=segments,
        time_to_alert_s=round(time_to_alert_s, 2) if time_to_alert_s is not None else None,
        max_score=max_score,
        final_level=final_level,
        categories=categories,
        stt_latency_ms=stt_latency_ms,
        credits_used=credits_used,
        mode=mode,
        synthetic=synthetic,
    )
