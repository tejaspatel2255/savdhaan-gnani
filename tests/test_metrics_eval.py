"""Unit tests for Phase 7 metrics calculations and summary builder."""

import pytest
from backend.metrics import (
    compute_wer,
    detection_summary,
    latency_summary,
    wer_normalize,
    wilson_ci,
)


def test_wilson_ci_known_values():
    low, high = wilson_ci(4, 5)
    assert abs(low - 0.3755) < 0.005
    assert abs(high - 0.9638) < 0.005

    low_zero, high_zero = wilson_ci(0, 5)
    assert low_zero == 0.0
    assert abs(high_zero - 0.4345) < 0.005

    low_full, high_full = wilson_ci(5, 5)
    assert high_full == 1.0

    # n == 0
    assert wilson_ci(0, 0) == (None, None)


def test_detection_summary_metrics():
    # 5 scam calls (4 detected, 1 missed), 5 legit calls (1 false alarm, 4 safe)
    rows = [
        {"label": "scam", "alerted": True, "alert_t": 5.0, "first_cue_s": 2.0, "max_level": "danger"},
        {"label": "scam", "alerted": True, "alert_t": 8.0, "first_cue_s": 3.0, "max_level": "danger"},
        {"label": "scam", "alerted": True, "alert_t": 12.0, "first_cue_s": 4.0, "max_level": "danger"},
        {"label": "scam", "alerted": True, "alert_t": 15.0, "first_cue_s": 5.0, "max_level": "danger"},
        {"label": "scam", "alerted": False, "alert_t": None, "first_cue_s": 2.0, "max_level": "calm"},
        {"label": "legit", "alerted": True, "alert_t": 10.0, "first_cue_s": None, "max_level": "danger"},
        {"label": "legit", "alerted": False, "alert_t": None, "first_cue_s": None, "max_level": "careful"},
        {"label": "legit", "alerted": False, "alert_t": None, "first_cue_s": None, "max_level": "calm"},
        {"label": "legit", "alerted": False, "alert_t": None, "first_cue_s": None, "max_level": "calm"},
        {"label": "legit", "alerted": False, "alert_t": None, "first_cue_s": None, "max_level": "calm"},
    ]

    summary = detection_summary(rows)
    assert summary["tp"] == 4
    assert summary["fn"] == 1
    assert summary["fp"] == 1
    assert summary["tn"] == 4
    assert summary["precision"] == 0.8  # 4 / (4 + 1)
    assert summary["recall"] == 0.8     # 4 / (4 + 1)
    assert summary["f1"] == 0.8
    assert summary["false_alarm_rate"] == 0.2  # 1 / 5
    assert summary["careful_on_legit"] == 1    # only the non-alerted legit that reached careful

    # Time to alert median over [5.0, 8.0, 12.0, 15.0] -> (8.0 + 12.0)/2 = 10.0
    assert summary["time_to_alert_s"]["n"] == 4
    assert summary["time_to_alert_s"]["median"] == 10.0


def test_precision_none_with_zero_alerts():
    rows = [
        {"label": "scam", "alerted": False, "alert_t": None, "first_cue_s": 2.0, "max_level": "calm"},
        {"label": "legit", "alerted": False, "alert_t": None, "first_cue_s": None, "max_level": "calm"},
    ]
    summary = detection_summary(rows)
    assert summary["precision"] is None
    assert summary["f1"] is None


def test_wer_normalization_and_wer_computation():
    assert wer_normalize("Hello, World!") == "hello world"

    # Chandrabindu and nukta normalization
    s_chandrabindu = "हँसना"
    s_anusvara = "हंसना"
    assert wer_normalize(s_chandrabindu) == wer_normalize(s_anusvara)

    s_nukta = "साफ़"
    s_plain = "साफ"
    assert wer_normalize(s_nukta) == wer_normalize(s_plain)

    # Identical
    assert compute_wer("यह एक परीक्षण है", "यह एक परीक्षण है") == 0.0

    # 1 substitution in 4 words = 0.25
    assert compute_wer("one two three four", "one two three five") == 0.25

    # Empty reference
    with pytest.raises(ValueError):
        compute_wer("   ", "something")


def test_latency_summary():
    lats = [100, 200, 300, 400, 500]
    res = latency_summary(lats)
    assert res["n"] == 5
    assert res["p50"] == 300
