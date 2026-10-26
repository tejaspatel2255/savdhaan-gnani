"""Audio and transcript data sources for sessions."""

import asyncio
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from backend.audio_utils import file_to_pcm
from backend.config import Settings
from backend.gnani_stream import (
    Connected,
    Processing,
    StreamError,
    Transcript,
    stream_call,
)


@dataclass
class SourceEvent:
    kind: str  # 'level', 'processing', 'transcript', 'error'
    t: float
    data: Dict[str, Any]


class MockSource:
    """Mock call data source with simulated speech and audio levels."""

    def __init__(self, path: Union[str, Path], speed: float = 1.0) -> None:
        self.path = Path(path)
        self.speed = max(0.1, float(speed))

    async def run(self, sink: Callable[[SourceEvent], Any], stop: asyncio.Event) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("segments", [])
        if not segments:
            return

        total_call_time = segments[-1]["t"] + (segments[-1].get("audio_duration_ms", 3000) / 1000.0)
        t_call = 0.0
        seg_idx = 0
        t0 = time.monotonic()

        # Emit audio levels every 0.1s of call time
        while t_call <= total_call_time:
            if stop.is_set():
                break

            # Check if any segment is due
            while seg_idx < len(segments):
                seg = segments[seg_idx]
                seg_t = float(seg["t"])
                proc_t = max(seg_t - 0.3, 0.0)

                # Emit processing
                if not seg.get("_proc_emitted") and t_call >= proc_t:
                    await sink(SourceEvent(kind="processing", t=proc_t, data={}))
                    seg["_proc_emitted"] = True

                # Emit transcript
                if t_call >= seg_t:
                    await sink(SourceEvent(
                        kind="transcript",
                        t=seg_t,
                        data={
                            "segment_index": seg_idx,
                            "segment_id": f"mock_seg_{seg_idx}",
                            "text": seg["text"],
                            "audio_duration_ms": seg.get("audio_duration_ms", 3000),
                            "stt_latency_ms": None,
                        },
                    ))
                    seg_idx += 1
                else:
                    break

            # Determine RMS inside speech window vs silence
            # Speech window for current or recent segment: [t - audio_duration_ms/1000, t]
            in_speech = False
            for s in segments:
                dur_s = s.get("audio_duration_ms", 3000) / 1000.0
                st = float(s["t"])
                if (st - dur_s) <= t_call <= st:
                    in_speech = True
                    break

            if in_speech:
                rms = 0.30 + 0.25 * abs(math.sin(3.1 * t_call))
            else:
                rms = 0.02

            await sink(SourceEvent(kind="level", t=t_call, data={"rms": rms}))

            t_call += 0.1
            wall_deadline = t0 + (t_call / self.speed)
            sleep_s = wall_deadline - time.monotonic()
            if sleep_s > 0:
                await asyncio.sleep(sleep_s)


class ReplaySource:
    """Replay data source from pre-recorded JSONL transcript file."""

    def __init__(self, path: Union[str, Path], speed: float = 1.0) -> None:
        self.path = Path(path)
        self.speed = max(0.1, float(speed))

    async def run(self, sink: Callable[[SourceEvent], Any], stop: asyncio.Event) -> None:
        lines: List[Dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(json.loads(line))

        if not lines:
            return

        total_call_time = lines[-1]["t"] + (lines[-1].get("audio_duration_ms", 3000) / 1000.0)
        t_call = 0.0
        line_idx = 0
        t0 = time.monotonic()

        while t_call <= total_call_time:
            if stop.is_set():
                break

            while line_idx < len(lines):
                item = lines[line_idx]
                target_t = float(item["t"])
                proc_t = max(target_t - 0.3, 0.0)

                if not item.get("_proc_emitted") and t_call >= proc_t:
                    await sink(SourceEvent(kind="processing", t=proc_t, data={}))
                    item["_proc_emitted"] = True

                if t_call >= target_t:
                    await sink(SourceEvent(
                        kind="transcript",
                        t=target_t,
                        data={
                            "segment_index": item.get("segment_index", line_idx),
                            "segment_id": str(item.get("segment_id", f"rep_{line_idx}")),
                            "text": item.get("text", ""),
                            "audio_duration_ms": item.get("audio_duration_ms", 3000),
                            "stt_latency_ms": item.get("latency"),
                        },
                    ))
                    line_idx += 1
                else:
                    break

            # Simulated RMS
            in_speech = False
            for s in lines:
                dur_s = s.get("audio_duration_ms", 3000) / 1000.0
                st = float(s["t"])
                if (st - dur_s) <= t_call <= st:
                    in_speech = True
                    break

            rms = 0.30 + 0.25 * abs(math.sin(3.1 * t_call)) if in_speech else 0.02
            await sink(SourceEvent(kind="level", t=t_call, data={"rms": rms}))

            t_call += 0.1
            wall_deadline = t0 + (t_call / self.speed)
            sleep_s = wall_deadline - time.monotonic()
            if sleep_s > 0:
                await asyncio.sleep(sleep_s)


class FileSource:
    """Audio file data source streaming real audio frames to Gnani STT WebSocket."""

    def __init__(
        self,
        audio_path: Union[str, Path],
        lang: str,
        rate: int,
        settings: Settings,
        base_url: str = "wss://api.vachana.ai",
    ) -> None:
        self.audio_path = Path(audio_path)
        self.lang = lang
        self.rate = rate
        self.settings = settings
        self.base_url = base_url

    async def run(self, sink: Callable[[SourceEvent], Any], stop: asyncio.Event) -> None:
        pcm = file_to_pcm(self.audio_path, self.rate)
        frames_sent = 0
        last_level_emit_time = -1.0

        def on_stt_event(ev: Any) -> None:
            if isinstance(ev, Processing):
                asyncio.create_task(sink(SourceEvent(kind="processing", t=ev.t, data={})))
            elif isinstance(ev, Transcript):
                asyncio.create_task(sink(SourceEvent(
                    kind="transcript",
                    t=ev.t,
                    data={
                        "segment_index": ev.segment_index,
                        "segment_id": ev.segment_id,
                        "text": ev.text,
                        "audio_duration_ms": ev.audio_duration_ms,
                        "stt_latency_ms": ev.latency,
                    },
                )))
            elif isinstance(ev, StreamError):
                asyncio.create_task(sink(SourceEvent(
                    kind="error",
                    t=ev.t,
                    data={"code": "network", "message": ev.message, "recoverable": True},
                )))

        def on_level(rms: float) -> None:
            nonlocal frames_sent, last_level_emit_time
            frames_sent += 1
            call_t = (frames_sent * 512.0) / float(self.rate)
            # Throttle to at most 10 per second (every 0.1s)
            if call_t - last_level_emit_time >= 0.095:
                last_level_emit_time = call_t
                asyncio.create_task(sink(SourceEvent(
                    kind="level",
                    t=round(call_t, 3),
                    data={"rms": rms},
                )))

        await stream_call(
            pcm,
            lang=self.lang,
            rate=self.rate,
            settings=self.settings,
            on_event=on_stt_event,
            on_level=on_level,
            stop=stop,
            base_url=self.base_url,
        )
