"""Live microphone source: browser -> /ws/mic -> Gnani Prisma STT."""

import asyncio
import logging
import time
from typing import Any, Callable, Optional

from backend.audio_utils import rms_int16
from backend.config import Settings
from backend.gnani_errors import GnaniError
from backend.gnani_stream import Processing, SttStream, StreamError, Transcript
from backend.sources import SourceEvent
from backend import usage

logger = logging.getLogger(__name__)

FRAME_SIZE = 1024          # bytes — must match SttStream expectation
RATE = 16000               # Hz  — fixed for mic mode
MAX_SESSION_S = 14 * 60   # 14 minutes hard cap (Gnani session cap is 15)
CAP_CHECK_INTERVAL = 5.0  # seconds between credit checks
MAX_LEVELS_PER_S = 10      # throttle audio_level events


class MicSource:
    """Live microphone audio source.

    Call flow:
    1. orchestrator creates MicSource and calls source.run(sink, stop).
    2. /ws/mic route calls push(data) for each incoming binary message.
    3. run() drains the queue into SttStream until stop is set.
    """

    def __init__(self, settings: Settings, lang: str, base_url: str = "wss://api.vachana.ai") -> None:
        self.settings = settings
        self.lang = lang
        self.base_url = base_url
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._attached = asyncio.Event()
        self._mute_until: float = 0.0
        self.synthetic: bool = False
        self.mode_label: str = "LIVE MIC"
        self._connected = asyncio.Event()

    def attach(self, _: Any) -> None:
        """Signal that the browser WebSocket has connected."""
        self._attached.set()

    async def push(self, data: bytes) -> None:
        """Called by /ws/mic handler for each binary frame received."""
        try:
            self._queue.put_nowait(data)
        except asyncio.QueueFull:
            pass  # Drop; back-pressure — browser is faster than STT

    async def stop_push(self) -> None:
        """Signal end of stream from the browser side."""
        try:
            self._queue.put_nowait(None)  # sentinel
        except asyncio.QueueFull:
            pass

    async def mute(self, seconds: float) -> None:
        """Mute incoming audio for `seconds`; called by orchestrator on warning_audio."""
        self._mute_until = time.monotonic() + seconds

    async def run(self, sink: Callable[[SourceEvent], Any], stop: asyncio.Event) -> None:
        """Main source coroutine — runs until stop is set or stream ends."""
        try:
            await asyncio.wait_for(self._attached.wait(), timeout=15.0)
        except asyncio.TimeoutError:
            raise GnaniError(
                "microphone did not connect",
                code="bad_request",
                recoverable=False,
            )

        seconds_sent: float = 0.0
        buf = bytearray()

        async with SttStream(
            self.settings, self.lang, RATE, base_url=self.base_url
        ) as stream:
            self._connected.set()

            async def receiver() -> None:
                """Map SttStream events to SourceEvents."""
                async for ev in stream.events():
                    t = seconds_sent
                    if isinstance(ev, Processing):
                        await sink(SourceEvent(kind="processing", t=t, data={}))
                    elif isinstance(ev, Transcript):
                        await sink(SourceEvent(
                            kind="transcript",
                            t=t,
                            data={
                                "segment_index": ev.segment_index,
                                "segment_id": ev.segment_id,
                                "text": ev.text,
                                "audio_duration_ms": ev.audio_duration_ms,
                                "stt_latency_ms": ev.latency,
                            },
                        ))
                    elif isinstance(ev, StreamError):
                        await sink(SourceEvent(
                            kind="error",
                            t=t,
                            data={"code": "stt_closed", "message": ev.message, "recoverable": False},
                        ))
                        stop.set()
                        return

            async def sender() -> None:
                """Re-chunk queued binary chunks into 1024-byte frames."""
                nonlocal buf, seconds_sent
                last_level_t = 0.0
                last_cap_check_t = 0.0
                session_start = time.monotonic()

                while not stop.is_set():
                    try:
                        chunk = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue
                    if chunk is None:  # sentinel — browser disconnected
                        break

                    now = time.monotonic()
                    if now - session_start >= MAX_SESSION_S:
                        stop.set()
                        break
                    if now - last_cap_check_t >= CAP_CHECK_INTERVAL:
                        usage.check_stt_cap(seconds_sent)
                        last_cap_check_t = now
                        await sink(SourceEvent(
                            kind="usage_tick",
                            t=seconds_sent,
                            data={
                                "stt_seconds_used": seconds_sent,
                                "stt_seconds_cap": float(self.settings.max_stt_seconds_per_run),
                            },
                        ))

                    muted = now < self._mute_until
                    buf.extend(bytes(len(chunk)) if muted else chunk)

                    while len(buf) >= FRAME_SIZE:
                        frame = bytes(buf[:FRAME_SIZE])
                        del buf[:FRAME_SIZE]

                        if now - last_level_t >= 1.0 / MAX_LEVELS_PER_S:
                            await sink(SourceEvent(
                                kind="level",
                                t=seconds_sent,
                                data={"rms": rms_int16(frame)},
                            ))
                            last_level_t = now

                        await stream.send(frame)
                        seconds_sent += FRAME_SIZE / (RATE * 2.0)

                # Pad and send final partial frame
                if buf:
                    pad = bytes(FRAME_SIZE - len(buf))
                    await stream.send(bytes(buf) + pad)
                    seconds_sent += FRAME_SIZE / (RATE * 2.0)
                    buf.clear()

                stop.set()
                await stream.close()

            recv_task = asyncio.create_task(receiver())
            send_task = asyncio.create_task(sender())

            done, pending = await asyncio.wait(
                [recv_task, send_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            # Ensure sender and receiver are stopped and stream is closed
            stop.set()
            await stream.close()
            for task in pending:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
            for task in done:
                exc = task.exception()
                if exc and isinstance(exc, GnaniError):
                    raise exc

        # Record usage — audio never written to disk
        if seconds_sent > 0:
            usage.add_stt_seconds(seconds_sent)
