"""Unit tests for configuration, error handling, and usage ledger."""

import json
from pathlib import Path
import sys
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import Settings
from backend.gnani_errors import GnaniError
from backend import usage


def test_settings_repr_masks_api_key():
    """Verify that api_key is excluded from repr(Settings)."""
    s = Settings(api_key="secret-gnani-api-key-12345")
    repr_str = repr(s)
    assert "secret-gnani-api-key-12345" not in repr_str
    assert s.key_present is True


def test_settings_key_present_false_when_empty():
    """Verify key_present is False when api_key is empty or whitespace."""
    s = Settings(api_key="")
    assert s.key_present is False
    s2 = Settings(api_key="   ")
    assert s2.key_present is False


def test_gnani_error_from_http_400():
    """Status 400 maps to code 'bad_request'."""
    err = GnaniError.from_http(400, {"error": {"message": "Invalid audio encoding"}})
    assert err.code == "bad_request"
    assert err.status == 400
    assert err.recoverable is False
    assert "Invalid audio encoding" in err.message


def test_gnani_error_from_http_403():
    """Status 403 maps to code 'credits' with specified warning message."""
    err = GnaniError.from_http(403, {"error": {"message": "Forbidden"}})
    assert err.code == "credits"
    assert err.status == 403
    assert err.recoverable is False
    assert err.message == "Forbidden: the API key, organisation status or credits may be the problem"


def test_gnani_error_from_http_429():
    """Status 429 maps to code 'rate_limited' and is recoverable."""
    err = GnaniError.from_http(429, {"message": "Too many requests"})
    assert err.code == "rate_limited"
    assert err.status == 429
    assert err.recoverable is True


def test_gnani_error_from_http_500_and_503():
    """Statuses 500 and 503 map to code 'network' and are recoverable."""
    err500 = GnaniError.from_http(500, "Internal error")
    assert err500.code == "network"
    assert err500.status == 500
    assert err500.recoverable is True

    err503 = GnaniError.from_http(503, "Service unavailable")
    assert err503.code == "network"
    assert err503.status == 503
    assert err503.recoverable is True


def test_gnani_error_from_http_other_status():
    """Any other status code maps to code 'internal'."""
    err = GnaniError.from_http(418, "I'm a teapot")
    assert err.code == "internal"
    assert err.status == 418
    assert err.recoverable is False


def test_tts_cap_exceeded_raises_cap_reached(monkeypatch):
    """Exceeding MAX_TTS_CHARS_PER_RUN raises GnaniError(code='cap_reached')."""
    usage.reset_process_totals()
    custom_settings = Settings(max_tts_chars_per_run=50)
    monkeypatch.setattr(usage, "settings", custom_settings)

    # Within cap
    usage.check_tts_cap(40)
    # Exceeding cap
    with pytest.raises(GnaniError) as exc_info:
        usage.check_tts_cap(51)
    assert exc_info.value.code == "cap_reached"


def test_stt_cap_exceeded_raises_cap_reached(monkeypatch):
    """Exceeding MAX_STT_SECONDS_PER_RUN raises GnaniError(code='cap_reached')."""
    usage.reset_process_totals()
    custom_settings = Settings(max_stt_seconds_per_run=10)
    monkeypatch.setattr(usage, "settings", custom_settings)

    # Within cap
    usage.check_stt_cap(5.0)
    # Exceeding cap
    with pytest.raises(GnaniError) as exc_info:
        usage.check_stt_cap(15.0)
    assert exc_info.value.code == "cap_reached"


def test_usage_ledger_written_atomically(tmp_path, monkeypatch):
    """Verify ledger updates are written atomically and accurately."""
    test_ledger = tmp_path / "usage_ledger.json"
    monkeypatch.setattr(usage, "LEDGER_PATH", test_ledger)
    usage.reset_process_totals()

    usage.add_tts_chars(120)
    usage.add_stt_seconds(15.5)

    data = usage.read()
    assert data["lifetime"]["tts_chars"] == 120
    assert data["lifetime"]["stt_seconds"] == 15.5

    process_totals = usage.get_process_totals()
    assert process_totals["tts_chars"] == 120
    assert process_totals["stt_seconds"] == 15.5
