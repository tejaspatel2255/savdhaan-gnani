"""Gnani Prisma Speech-to-Text REST client."""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx
import soundfile as sf

from backend.config import settings
from backend.gnani_errors import GnaniError
from backend import usage

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/cache/stt")
STT_URL = "https://api.vachana.ai/stt/v3"


@dataclass
class SttResult:
    """Result of an STT transcription request."""

    transcript: str
    request_id: str
    cached: bool
    seconds: float
    elapsed_ms: int


def _cache_key(file_bytes: bytes, params: Dict[str, Any]) -> str:
    """Compute sha256 hex digest for file bytes plus query parameters."""
    h = hashlib.sha256(file_bytes)
    serialized = json.dumps(params, sort_keys=True, ensure_ascii=True).encode("utf-8")
    h.update(serialized)
    return h.hexdigest()


async def transcribe_file(
    path: Union[str, Path],
    *,
    language_code: str,
    fmt: str = "verbatim",
    dry_run: bool = False,
) -> SttResult:
    """Transcribe an audio file using Gnani Prisma REST endpoint.

    Refuses audio longer than 60 s before sending. Caches by sha256 of file bytes plus parameters.
    """
    if settings.demo:
        raise GnaniError("Gnani API calls disabled in demo mode", code="demo_mode")
    audio_path = Path(path)
    if not audio_path.exists():
        raise GnaniError(f"Audio file not found: {audio_path}", code="bad_request")

    try:
        info = sf.info(str(audio_path))
        seconds = float(info.duration)
    except Exception as exc:
        raise GnaniError(f"Could not read audio file metadata: {exc}", code="bad_request")

    if seconds > 60.0:
        raise GnaniError(
            f"Audio duration {seconds:.1f}s exceeds max limit of 60s for REST STT",
            code="bad_request",
        )

    file_bytes = audio_path.read_bytes()
    params = {"language_code": language_code, "format": fmt}

    if dry_run:
        masked_request = {
            "url": STT_URL,
            "headers": {"X-API-Key-ID": "***MASKED***" if settings.key_present else "EMPTY"},
            "fields": params,
            "file": str(audio_path),
            "audio_seconds": round(seconds, 2),
        }
        return SttResult(
            transcript=json.dumps(masked_request),
            request_id="dry-run",
            cached=False,
            seconds=round(seconds, 2),
            elapsed_ms=0,
        )

    key = _cache_key(file_bytes, params)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"

    if cache_file.exists():
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return SttResult(
            transcript=data.get("transcript", ""),
            request_id=data.get("request_id", ""),
            cached=True,
            seconds=data.get("seconds", round(seconds, 2)),
            elapsed_ms=0,
        )

    # Check cap before spending credits
    usage.check_stt_cap(seconds)

    if not settings.key_present:
        raise GnaniError("GNANI_API_KEY is not configured", code="no_key", status=None, recoverable=False)

    headers = {"X-API-Key-ID": settings.api_key}
    data_fields = {"language_code": language_code, "format": fmt}
    files = {"audio_file": (audio_path.name, file_bytes, "audio/wav")}

    t0 = time.perf_counter()
    retries = 0
    backoffs = [1.0, 2.0]

    async with httpx.AsyncClient(timeout=45.0) as client:
        while True:
            try:
                response = await client.post(STT_URL, headers=headers, data=data_fields, files=files)
            except httpx.RequestError as exc:
                raise GnaniError(f"Network error connecting to Gnani STT: {exc}", code="network", recoverable=True)

            if response.status_code == 200:
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                body = response.json()
                transcript = body.get("transcript", "")
                request_id = str(body.get("request_id", ""))

                cache_payload = {
                    "transcript": transcript,
                    "request_id": request_id,
                    "seconds": round(seconds, 2),
                }
                cache_file.write_text(json.dumps(cache_payload, ensure_ascii=False), encoding="utf-8")
                usage.add_stt_seconds(seconds)
                return SttResult(
                    transcript=transcript,
                    request_id=request_id,
                    cached=False,
                    seconds=round(seconds, 2),
                    elapsed_ms=elapsed_ms,
                )

            # Error handling
            if response.status_code == 429 and retries < 2:
                await asyncio.sleep(backoffs[retries])
                retries += 1
                continue

            try:
                err_body = response.json()
            except Exception:
                err_body = response.text

            raise GnaniError.from_http(response.status_code, err_body)
