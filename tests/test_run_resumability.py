import json
from pathlib import Path
import pytest
from backend.gnani_errors import GnaniError
from scripts.eval_safety import (
    check_pre_flight_cap,
    handle_gnani_status,
    write_transcript_atomic,
)


def test_check_pre_flight_cap_raises_cleanly():
    with pytest.raises(GnaniError) as exc_info:
        check_pre_flight_cap(needed_quantity=750, cap=600, kind="TTS")
    assert "Cap reached" in str(exc_info.value)
    assert "MAX_TTS_PER_RUN" in str(exc_info.value)


def test_handle_gnani_status_403_stops_immediately():
    with pytest.raises(GnaniError) as exc_info:
        handle_gnani_status(403, "Forbidden / Invalid key")
    assert "The key or the credits may be exhausted: stop here" in str(exc_info.value)
    assert exc_info.value.code == "auth"


def test_handle_gnani_status_429():
    with pytest.raises(GnaniError) as exc_info:
        handle_gnani_status(429, "Too many requests")
    assert exc_info.value.code == "rate_limit"


def test_write_transcript_atomic_resumable(tmp_path: Path):
    out = tmp_path / "transcripts" / "D01.jsonl"
    records = [{"t": 0.5, "text": "turn 1"}, {"t": 1.2, "text": "turn 2"}]

    # First write creates file
    res1 = write_transcript_atomic(out, records, force=False)
    assert res1 is True
    assert out.exists()

    # Second write skips without force
    res2 = write_transcript_atomic(out, [{"t": 3.0, "text": "new"}], force=False)
    assert res2 is False
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    # Force overwrites
    res3 = write_transcript_atomic(out, [{"t": 3.0, "text": "overwritten"}], force=True)
    assert res3 is True
    lines2 = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines2) == 1
    assert "overwritten" in lines2[0]
