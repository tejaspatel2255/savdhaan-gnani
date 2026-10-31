"""Resumability and safety execution helpers for gen_corpus and run_eval."""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.gnani_errors import GnaniError
from backend import usage

logger = logging.getLogger(__name__)


def check_pre_flight_cap(needed_quantity: float, cap: float, kind: str = "TTS") -> None:
    """Check cap BEFORE sending requests, raising error or cleanly exiting."""
    if needed_quantity > cap:
        unit = "characters" if kind == "TTS" else "seconds"
        msg = f"Cap reached: {needed_quantity} {unit} needed but MAX_{kind}_PER_RUN is {cap}. Run again after raising the cap in .env"
        raise GnaniError(msg, code="cap_reached", status=None, recoverable=False)


def handle_gnani_status(status_code: int, detail: str = "") -> None:
    """Handle Gnani HTTP status codes with strict stopping on 403."""
    if status_code == 403:
        msg = f"The key or the credits may be exhausted: stop here (HTTP 403: {detail})"
        logger.error(msg)
        raise GnaniError(msg, code="auth", status=403, recoverable=False)
    if status_code == 429:
        raise GnaniError(f"Rate limited (HTTP 429: {detail})", code="rate_limit", status=429, recoverable=True)


def write_transcript_atomic(out_path: Path, records: List[Dict[str, Any]], force: bool = False) -> bool:
    """Write call transcripts to disk atomically. Never overwrite without force."""
    if out_path.exists() and not force:
        logger.info("Transcript %s already exists; skipping.", out_path)
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tf = tempfile.NamedTemporaryFile("w", dir=out_path.parent, delete=False, encoding="utf-8")
    try:
        for r in records:
            tf.write(json.dumps(r, ensure_ascii=False) + "\n")
        tf.flush()
        os.fsync(tf.fileno())
        tf.close()
        os.replace(tf.name, out_path)
        return True
    except Exception:
        if os.path.exists(tf.name):
            os.remove(tf.name)
        raise
