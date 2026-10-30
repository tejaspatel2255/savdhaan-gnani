"""Tests for POST /api/analyze and GET /api/rules/summary endpoints.
No Gnani API calls are made in any of these tests.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# POST /api/analyze
# ---------------------------------------------------------------------------

HINDI_SCAM = (
    "आपके खाते को ब्लॉक कर दिया जाएगा। "
    "अभी OTP बताइए नहीं तो गिरफ्तारी होगी। "
    "पैसे सेफ अकाउंट में ट्रांसफर करें।"
)

BANK_REMINDER = "आपकी EMI का भुगतान अगले सोमवार तक करें। धन्यवाद।"

NEGATED_SCAM = "यह कोई स्कैम नहीं है और आपको OTP नहीं देना है।"


def post_analyze(text: str, pack: str = "hi_en"):
    return client.post("/api/analyze", json={"text": text, "pack": pack})


def test_hindi_scam_reaches_danger():
    res = post_analyze(HINDI_SCAM)
    assert res.status_code == 200
    data = res.json()
    # Must have a score and a level
    assert "score" in data
    assert "level" in data
    assert data["level"] in ("calm", "careful", "danger")
    # A proper scam text should score higher than calm
    assert data["score"] >= 0


def test_hindi_scam_high_score():
    """Full scam sentence covering multiple categories should score >= 30."""
    res = post_analyze(HINDI_SCAM)
    assert res.status_code == 200
    data = res.json()
    assert data["score"] >= 30, f"Expected high score for scam text, got {data['score']}"


def test_bank_reminder_low_score():
    """A benign reminder should score lower than the scam text."""
    res_scam = post_analyze(HINDI_SCAM)
    res_safe = post_analyze(BANK_REMINDER)
    assert res_scam.status_code == 200
    assert res_safe.status_code == 200
    assert res_scam.json()["score"] > res_safe.json()["score"]


def test_empty_text_returns_422():
    res = client.post("/api/analyze", json={"text": "", "pack": "hi_en"})
    assert res.status_code == 422


def test_whitespace_only_returns_422():
    res = client.post("/api/analyze", json={"text": "   \n  ", "pack": "hi_en"})
    assert res.status_code == 422


def test_too_long_text_returns_422():
    res = client.post("/api/analyze", json={"text": "x" * 2001, "pack": "hi_en"})
    assert res.status_code == 422


def test_too_many_segments_returns_422():
    """41 segments separated by punctuation should be rejected."""
    text = ". ".join(["scam text"] * 41)
    res = post_analyze(text)
    assert res.status_code == 422


def test_segments_returned():
    """Response must include a non-empty segments list."""
    res = post_analyze(HINDI_SCAM)
    assert res.status_code == 200
    data = res.json()
    assert "segments" in data
    assert isinstance(data["segments"], list)
    assert len(data["segments"]) >= 1


def test_segment_schema():
    """Each segment must have the required fields."""
    res = post_analyze(HINDI_SCAM)
    assert res.status_code == 200
    seg = res.json()["segments"][0]
    for field in ("segment_index", "text", "score", "level", "delta", "hits", "categories"):
        assert field in seg, f"Missing field: {field}"


def test_gujarati_pack():
    """gu pack should work without crashing."""
    res = client.post("/api/analyze", json={"text": "OTP આપો નહીં", "pack": "gu"})
    assert res.status_code == 200


def test_invalid_pack_falls_back_to_hi_en():
    """Unknown pack name falls back to hi_en gracefully."""
    res = client.post("/api/analyze", json={"text": BANK_REMINDER, "pack": "unknown_pack"})
    assert res.status_code == 200


def test_missing_text_field_422():
    """Request body without 'text' field should fail validation."""
    res = client.post("/api/analyze", json={"pack": "hi_en"})
    assert res.status_code == 422


def test_rate_limit_triggers_after_30():
    """After 30 rapid requests, the 31st should return 429."""
    # Use a fresh test client to avoid shared rate-limiter state from other tests
    from backend.analyze import _rate_limits
    # Clear the rate limit table first so this test is isolated
    _rate_limits.clear()

    ok_count = 0
    for _ in range(30):
        r = client.post("/api/analyze", json={"text": BANK_REMINDER, "pack": "hi_en"})
        if r.status_code == 200:
            ok_count += 1

    # 31st request should be rate-limited
    r = client.post("/api/analyze", json={"text": BANK_REMINDER, "pack": "hi_en"})
    assert r.status_code == 429, f"Expected 429 after 30 requests, got {r.status_code}"
    _rate_limits.clear()  # clean up


# ---------------------------------------------------------------------------
# GET /api/rules/summary
# ---------------------------------------------------------------------------

def test_rules_summary_returns_categories():
    res = client.get("/api/rules/summary")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_rules_summary_has_logic_en():
    res = client.get("/api/rules/summary")
    assert res.status_code == 200
    data = res.json()
    assert "logic_en" in data
    assert len(data["logic_en"]) > 10


def test_rules_summary_category_fields():
    """Each category must have id, label_en, label_hi, weight, examples."""
    res = client.get("/api/rules/summary")
    assert res.status_code == 200
    cats = res.json()["categories"]
    for cat in cats:
        for field in ("id", "label_en", "label_hi", "weight", "examples"):
            assert field in cat, f"Category missing field '{field}': {cat}"
        assert isinstance(cat["examples"], list)
        assert len(cat["examples"]) <= 6
