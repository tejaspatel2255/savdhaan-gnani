"""Audio utilities: format conversion, frame slicing, RMS measurement, and pacing."""

import asyncio
import math
import shutil
import subprocess
import time
from pathlib import Path
from typing import AsyncIterator, Callable, Iterator, Optional, Union
import numpy as np


def file_to_pcm(path: Union[str, Path], rate: int) -> bytes:
    """Run ffmpeg (-y -i path -ac 1 -ar rate -f s16le -) and return raw PCM bytes.

    Raises RuntimeError with a clear error if ffmpeg is missing or conversion fails.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed or not found on PATH")

    input_path = str(Path(path).resolve())
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-y",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        str(rate),
        "-f",
        "s16le",
        "-",
    ]
    res = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        err_msg = res.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg conversion failed: {err_msg}")
    return res.stdout


def frames(pcm: bytes) -> Iterator[bytes]:
    """Yield exactly 1024-byte frames; the last one is padded with zero bytes."""
    chunk_size = 1024
    if not pcm:
        return

    total_len = len(pcm)
    for i in range(0, total_len, chunk_size):
        chunk = pcm[i : i + chunk_size]
        if len(chunk) < chunk_size:
            chunk = chunk + b"\x00" * (chunk_size - len(chunk))
        yield chunk


def rms_int16(frame: bytes) -> float:
    """Compute RMS of a signed 16-bit little-endian frame, normalized to 0..1."""
    if not frame:
        return 0.0
    arr = np.frombuffer(frame, dtype=np.int16)
    if len(arr) == 0:
        return 0.0
    mean_sq = np.mean(arr.astype(np.float64) ** 2)
    rms_val = math.sqrt(mean_sq)
    # 32768 is max amplitude for signed 16-bit int
    norm = rms_val / 32768.0
    return min(1.0, max(0.0, float(norm)))


async def pace_frames(
    frames_iter: Iterator[bytes],
    rate: int,
    send: Callable[[bytes], asyncio.Future],
    on_level: Optional[Callable[[float], None]] = None,
    stop: Optional[asyncio.Event] = None,
) -> None:
    """Await send(frame) once per frame at real-time cadence (32ms at 16000Hz, 64ms at 8000Hz).

    Schedules against time.monotonic() deadlines (deadline += interval) so timing error
    does not accumulate. Stops early when stop asyncio.Event is set. Never sends faster than real time.
    """
    # 1024 bytes = 512 samples. interval = 512 / rate (e.g. 0.032s at 16000, 0.064s at 8000)
    interval = 512.0 / float(rate)
    deadline = time.monotonic()

    for frame in frames_iter:
        if stop is not None and stop.is_set():
            break

        if on_level is not None:
            lvl = rms_int16(frame)
            on_level(lvl)

        await send(frame)
        deadline += interval
        now = time.monotonic()
        sleep_dur = deadline - now
        if sleep_dur > 0:
            await asyncio.sleep(sleep_dur)
