"""Gnani Realtime Streaming STT client and connection orchestrator."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from backend.audio_utils import frames, pace_frames
from backend.config import Settings
from backend.gnani_errors import GnaniError
from backend import usage

logger = logging.getLogger(__name__)


def build_headers(
    api_key: str,
    lang: str,
    rate: int,
    fmt: str = "verbatim",
    vad: Optional[Dict[str, Any]] = None,
    bias_list: Optional[List[str]] = None,
    bias_score: Optional[float] = None,
) -> Dict[str, str]:
    """Build upgrade headers using exact header names in docs/API_CONTRACT.md.

    For rate 8000 uses the telephony VAD preset (threshold 0.7, min speech 200, min silence 500)
    unless custom vad passed; otherwise defaults. Include optional headers only when set.
    """
    headers: Dict[str, str] = {
        "x-api-key-id": api_key,
        "lang_code": lang,
        "x-sample-rate": str(rate),
        "x-format": fmt,
    }

    # VAD headers
    if vad is not None:
        if "threshold" in vad:
            headers["x-vad-threshold"] = str(vad["threshold"])
        if "min_silence_ms" in vad:
            headers["x-min-silence-ms"] = str(vad["min_silence_ms"])
        if "min_speech_ms" in vad:
            headers["x-min-speech-ms"] = str(vad["min_speech_ms"])
        if "min_segment_ms" in vad:
            headers["x-min-segment-ms"] = str(vad["min_segment_ms"])
        if "max_speech_s" in vad:
            headers["x-max-speech-s"] = str(vad["max_speech_s"])
    elif rate == 8000:
        # Telephony preset
        headers["x-vad-threshold"] = "0.7"
        headers["x-min-speech-ms"] = "200"
        headers["x-min-silence-ms"] = "500"

    # Bias list and score
    if bias_list:
        headers["x-bias-list"] = json.dumps(bias_list)
        if bias_score is not None:
            headers["x-bias-score"] = str(bias_score)

    return headers


@dataclass
class Connected:
    """Server connected event."""
    config: Dict[str, Any]
    t: float = 0.0


@dataclass
class Processing:
    """Speech end detected, segment is being processed."""
    t: float = 0.0


@dataclass
class Transcript:
    """Transcript event for a completed speech segment."""
    text: str
    segment_index: int
    segment_id: str
    audio_duration_ms: int
    latency: Optional[int]
    t: float


@dataclass
class StreamError:
    """Error reported by Gnani server."""
    message: str
    t: float = 0.0


@dataclass
class Closed:
    """WebSocket connection closed."""
    code: int
    reason: str
    t: float = 0.0


class SttStream:
    """Async context manager wrapper around Gnani STT WebSocket."""

    def __init__(
        self,
        settings: Settings,
        lang: str,
        rate: int,
        base_url: str = "wss://api.vachana.ai",
        **header_options: Any,
    ) -> None:
        self.settings = settings
        self.lang = lang
        self.rate = rate
        self.base_url = base_url.rstrip("/")
        self.header_options = header_options
        self.headers = build_headers(settings.api_key, lang, rate, **header_options)
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.first_frame_time: Optional[float] = None

    async def __aenter__(self) -> "SttStream":
        url = f"{self.base_url}/stt/v3/stream"
        try:
            self.ws = await websockets.connect(url, additional_headers=self.headers)
        except Exception as exc:
            logger.error("Failed to connect to STT stream: %s", exc)
            raise GnaniError(f"STT stream connection error: {exc}", code="network", recoverable=True)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def send(self, frame: bytes) -> None:
        """Send a single raw PCM frame. Raises ValueError unless len(frame) == 1024."""
        if len(frame) != 1024:
            raise ValueError(f"Frame must be exactly 1024 bytes, got {len(frame)}")

        if self.first_frame_time is None:
            self.first_frame_time = time.monotonic()

        if self.ws:
            await self.ws.send(frame)

    def _elapsed_t(self) -> float:
        if self.first_frame_time is None:
            return 0.0
        return round(time.monotonic() - self.first_frame_time, 3)

    async def events(self) -> AsyncGenerator[Any, None]:
        """Yield parsed event dataclasses from WebSocket stream."""
        if not self.ws:
            return

        try:
            async for raw_msg in self.ws:
                t = self._elapsed_t()
                if isinstance(raw_msg, bytes):
                    continue
                try:
                    data = json.loads(raw_msg)
                except Exception:
                    continue

                msg_type = data.get("type", "")
                if msg_type == "connected":
                    yield Connected(config=data.get("config", {}), t=t)
                elif msg_type == "processing":
                    yield Processing(t=t)
                elif msg_type == "transcript":
                    yield Transcript(
                        text=data.get("text", ""),
                        segment_index=int(data.get("segment_index", 0)),
                        segment_id=str(data.get("segment_id", "")),
                        audio_duration_ms=int(data.get("audio_duration_ms", 0)),
                        latency=data.get("latency"),
                        t=t,
                    )
                elif msg_type == "error":
                    yield StreamError(message=data.get("message", "Unknown error"), t=t)
        except ConnectionClosed as cc:
            t = self._elapsed_t()
            code = getattr(cc.rcvd, "code", None) or getattr(cc, "code", None)
            if code == 4001:
                raise GnaniError("Authentication failed on STT WebSocket (code 4001)", code="auth", recoverable=False)
            yield Closed(code=code or 1000, reason=getattr(cc.rcvd, "reason", "") or getattr(cc, "reason", "") or "", t=t)
        except Exception as exc:
            raise GnaniError(f"STT stream network failure: {exc}", code="network", recoverable=True)

    async def close(self) -> None:
        """Close WebSocket cleanly."""
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None


async def stream_call(
    pcm: bytes,
    *,
    lang: str,
    rate: int,
    settings: Settings,
    on_event: Callable[[Any], None],
    stop: Optional[asyncio.Event] = None,
    tail_silence_ms: int = 1500,
    max_reconnects: int = 2,
    base_url: str = "wss://api.vachana.ai",
    **header_options: Any,
) -> List[Transcript]:
    """Pace audio PCM through STT WebSocket and collect transcripts.

    Sends tail silence to ensure the last segment closes.
    Checks cap first and records actual audio seconds consumed.
    Reconnects on drop up to max_reconnects times.
    """
    total_audio_seconds = len(pcm) / (2.0 * float(rate))
    usage.check_stt_cap(total_audio_seconds)

    transcripts: List[Transcript] = []
    # Tail silence in bytes: rate * 2 bytes/sample * (ms / 1000)
    tail_silence_bytes = int(rate * 2 * (tail_silence_ms / 1000.0))
    full_pcm = pcm + b"\x00" * tail_silence_bytes
    all_frames = list(frames(full_pcm))

    reconnect_count = 0
    backoffs = [1.0, 2.0]
    frame_index = 0

    while frame_index < len(all_frames):
        try:
            async with SttStream(settings, lang, rate, base_url=base_url, **header_options) as stream:
                send_done = asyncio.Event()

                async def receiver() -> None:
                    async for event in stream.events():
                        on_event(event)
                        if isinstance(event, Transcript):
                            transcripts.append(event)
                        elif isinstance(event, Closed):
                            break
                        elif isinstance(event, StreamError):
                            logger.warning("Stream reported error: %s", event.message)
                    send_done.set()

                async def sender() -> None:
                    nonlocal frame_index
                    remaining = all_frames[frame_index:]

                    async def send_wrapper(fr: bytes) -> None:
                        nonlocal frame_index
                        await stream.send(fr)
                        frame_index += 1

                    await pace_frames(iter(remaining), rate, send_wrapper, stop=stop)
                    # Allow VAD and transcripts to arrive
                    await asyncio.sleep(tail_silence_ms / 1000.0 + 0.5)
                    await stream.close()
                    send_done.set()

                recv_task = asyncio.create_task(receiver())
                send_task = asyncio.create_task(sender())
                await asyncio.wait([recv_task, send_task], return_when=asyncio.FIRST_COMPLETED)
                results = await asyncio.gather(recv_task, send_task, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        raise res
                break  # Completed successfully
        except GnaniError as ge:
            if ge.code == "auth" or reconnect_count >= max_reconnects:
                raise
            await asyncio.sleep(backoffs[min(reconnect_count, len(backoffs) - 1)])
            reconnect_count += 1
            logger.info("Reconnecting STT stream (attempt %d)...", reconnect_count)
        except Exception as exc:
            if reconnect_count >= max_reconnects:
                raise GnaniError(f"Stream interrupted: {exc}", code="network", recoverable=True)
            await asyncio.sleep(backoffs[min(reconnect_count, len(backoffs) - 1)])
            reconnect_count += 1
            logger.info("Reconnecting STT stream after unexpected error (attempt %d)...", reconnect_count)

    # Record actual audio seconds to ledger (excluding extra padding)
    usage.add_stt_seconds(total_audio_seconds)
    return transcripts
