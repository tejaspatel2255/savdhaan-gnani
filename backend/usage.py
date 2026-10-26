"""Usage tracking and ledger management for Gnani API consumption."""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from backend.config import settings
from backend.gnani_errors import GnaniError

logger = logging.getLogger(__name__)

LEDGER_PATH = Path("data/usage_ledger.json")

# Per-process counters
_process_tts_chars: int = 0
_process_stt_seconds: float = 0.0


def reset_process_totals() -> None:
    """Reset the current process's usage counters (mainly for testing)."""
    global _process_tts_chars, _process_stt_seconds
    _process_tts_chars = 0
    _process_stt_seconds = 0.0


def get_process_totals() -> Dict[str, Any]:
    """Return in-memory usage for this process."""
    return {
        "tts_chars": _process_tts_chars,
        "stt_seconds": _process_stt_seconds,
    }


def read() -> Dict[str, Any]:
    """Read the usage ledger from disk, returning default structure if missing or invalid."""
    if not LEDGER_PATH.exists():
        return {
            "lifetime": {"tts_chars": 0, "stt_seconds": 0.0},
            "history": [],
        }
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Ledger content is not a dict")
            data.setdefault("lifetime", {"tts_chars": 0, "stt_seconds": 0.0})
            data.setdefault("history", [])
            return data
    except Exception as exc:
        logger.warning("Failed to read usage ledger, creating fresh: %s", exc)
        return {
            "lifetime": {"tts_chars": 0, "stt_seconds": 0.0},
            "history": [],
        }


def _write_atomic(data: Dict[str, Any]) -> None:
    """Write data to the ledger file atomically using a temporary file and replace."""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    dir_path = LEDGER_PATH.parent
    temp_file = tempfile.NamedTemporaryFile("w", dir=dir_path, delete=False, encoding="utf-8")
    try:
        json.dump(data, temp_file, indent=2)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        os.replace(temp_file.name, LEDGER_PATH)
    except Exception:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise


def check_tts_cap(chars: int) -> None:
    """Raise GnaniError(code='cap_reached') if THIS PROCESS would exceed MAX_TTS_CHARS_PER_RUN."""
    cap = settings.max_tts_chars_per_run
    if _process_tts_chars + chars > cap:
        raise GnaniError(
            message=f"TTS cap exceeded for this run: {_process_tts_chars + chars} > {cap} chars",
            code="cap_reached",
            status=None,
            recoverable=False,
        )


def check_stt_cap(seconds: float) -> None:
    """Raise GnaniError(code='cap_reached') if THIS PROCESS would exceed MAX_STT_SECONDS_PER_RUN."""
    cap = settings.max_stt_seconds_per_run
    if _process_stt_seconds + seconds > cap:
        raise GnaniError(
            message=f"STT cap exceeded for this run: {_process_stt_seconds + seconds:.1f} > {cap} seconds",
            code="cap_reached",
            status=None,
            recoverable=False,
        )


def add_tts_chars(chars: int) -> None:
    """Record TTS character consumption in process memory and atomically to disk."""
    global _process_tts_chars
    _process_tts_chars += chars

    data = read()
    lifetime = data.setdefault("lifetime", {"tts_chars": 0, "stt_seconds": 0.0})
    lifetime["tts_chars"] = lifetime.get("tts_chars", 0) + chars
    _write_atomic(data)


def add_stt_seconds(seconds: float) -> None:
    """Record STT audio duration in process memory and atomically to disk."""
    global _process_stt_seconds
    _process_stt_seconds += seconds

    data = read()
    lifetime = data.setdefault("lifetime", {"tts_chars": 0, "stt_seconds": 0.0})
    lifetime["stt_seconds"] = round(lifetime.get("stt_seconds", 0.0) + seconds, 3)
    _write_atomic(data)
