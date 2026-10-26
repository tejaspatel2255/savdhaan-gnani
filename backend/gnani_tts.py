"""Gnani Timbre Text-to-Speech REST client."""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx

from backend.config import settings
from backend.gnani_errors import GnaniError
from backend import usage

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/cache/tts")
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"


@dataclass
class TtsResult:
    """Result of a TTS synthesis request."""

    audio: Union[bytes, Dict[str, Any]]
    cached: bool
    chars: int
    elapsed_ms: int


def _cache_key(payload: Dict[str, Any]) -> str:
    """Compute sha256 hex digest for request JSON payload."""
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


async def synthesize(
    text: str,
    *,
    voice: str,
    model: str,
    language: str,
    sample_rate: int = 24000,
    dry_run: bool = False,
) -> TtsResult:
    """Synthesize text into speech using Gnani Timbre REST endpoint.

    Uses httpx POST to docs/API_CONTRACT.md specs with audio_config container wav,
    encoding linear_pcm, num_channels 1, sample_width 2.
    """
    chars = len(text)
    payload = {
        "text": text,
        "model": model,
        "voice": voice,
        "language": language,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": sample_rate,
            "num_channels": 1,
            "sample_width": 2,
            "container": "wav",
            "encoding": "linear_pcm",
        },
    }

    if dry_run:
        masked_request = {
            "url": TTS_URL,
            "headers": {"X-API-Key-ID": "***MASKED***" if settings.key_present else "EMPTY", "Content-Type": "application/json"},
            "payload": payload,
            "estimated_chars": chars,
        }
        return TtsResult(audio=masked_request, cached=False, chars=chars, elapsed_ms=0)

    key = _cache_key(payload)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.wav"

    if cache_file.exists():
        audio_bytes = cache_file.read_bytes()
        return TtsResult(audio=audio_bytes, cached=True, chars=chars, elapsed_ms=0)

    # Check cap before spending credits
    usage.check_tts_cap(chars)

    if not settings.key_present:
        raise GnaniError("GNANI_API_KEY is not configured", code="no_key", status=None, recoverable=False)

    headers = {
        "X-API-Key-ID": settings.api_key,
        "Content-Type": "application/json",
    }

    t0 = time.perf_counter()
    retries = 0
    backoffs = [1.0, 2.0]

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                response = await client.post(TTS_URL, headers=headers, json=payload)
            except httpx.RequestError as exc:
                raise GnaniError(f"Network error connecting to Gnani TTS: {exc}", code="network", recoverable=True)

            if response.status_code == 200:
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                audio_bytes = response.content
                cache_file.write_bytes(audio_bytes)
                usage.add_tts_chars(chars)
                return TtsResult(audio=audio_bytes, cached=False, chars=chars, elapsed_ms=elapsed_ms)

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
