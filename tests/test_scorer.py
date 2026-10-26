"""Comprehensive test suite for the scam scoring engine."""

import json
import subprocess
import sys
from pathlib import Path
import pytest

from backend.scorer import Hit, RiskUpdate, ScamScorer, load_pack
from backend.scorer.matching import compile_pattern, find_spans, best_match
from backend.scorer.normalize import normalize_token, tokenize, Token

FIXTURES_PATH = Path("tests/fixtures/calls.json")
RULES_PATH = Path("rules/scam_rules_hi_en.json")


@pytest.fixture(scope="module")
def pack():
    return load_pack(RULES_PATH)


# --- 1. Fixture Parametrized Tests ---

def _load_fixtures():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

FIXTURE_DATA = _load_fixtures()

@pytest.mark.parametrize("call", FIXTURE_DATA["scam"], ids=lambda c: c["id"])
def test_scam_calls_alert_by_index(pack, call):
    scorer = ScamScorer(pack)
    alert_idx = None
    for idx, seg in enumerate(call["segments"]):
        up = scorer.feed(seg, segment_index=idx)
        if up.alert and alert_idx is None:
            alert_idx = idx
    assert alert_idx is not None, f"Scam call {call['id']} did not alert"
    assert alert_idx <= call["alert_by_index"], f"{call['id']} alerted at {alert_idx} > {call['alert_by_index']}"


@pytest.mark.parametrize("call", FIXTURE_DATA["legit"], ids=lambda c: c["id"])
def test_legit_calls_never_alert_and_stay_low(pack, call):
    scorer = ScamScorer(pack)
    max_score = 0
    max_allowed = call.get("max_score_below", 30)
    for idx, seg in enumerate(call["segments"]):
        up = scorer.feed(seg, segment_index=idx)
        assert not up.alert, f"Legit call {call['id']} triggered alert at {idx}"
        if up.score > max_score:
            max_score = up.score
    assert max_score < max_allowed, f"Legit call {call['id']} max_score {max_score} >= {max_allowed}"


@pytest.mark.parametrize("call", FIXTURE_DATA["gating"], ids=lambda c: c["id"])
def test_gating_calls_never_alert(pack, call):
    scorer = ScamScorer(pack)
    for idx, seg in enumerate(call["segments"]):
        up = scorer.feed(seg, segment_index=idx)
        assert not up.alert, f"Gating call {call['id']} alerted at {idx}"


# --- 2. Exact Specification Checks ---

def test_check_please_apna_otp_bataiye(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("Please Apna OTP bataiye")
    assert up.score == 30
    assert up.level == "careful"
    assert any(h.matched == "Apna OTP" for h in up.hits)


def test_check_apna_otp_kisi_ko_na_dein(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("apna otp kisi ko na dein")
    assert up.score == 0
    assert len(up.suppressed) == 1
    assert up.suppressed[0].category == "credentials"


def test_check_apna_otp_nahi_to_account_band(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("apna otp batao nahi to account band ho jayega")
    assert up.score == 52
    assert len(up.suppressed) == 0


def test_check_apna_otp_aur_kisi_ko_mat_batana(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("apna otp batao aur kisi ko mat batana")
    assert up.score == 52


def test_check_yeh_digital_arrest_hai(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("yeh digital arrest hai")
    assert up.score == 60
    assert up.level == "danger"
    assert up.alert is True


def test_check_aap_anydesk_download_karo(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("aap anydesk download karo")
    assert up.score == 45
    assert up.level == "careful"


def test_check_aadhaar_number_bataiye(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("aadhaar number bataiye")
    assert up.score == 15


def test_check_paisa_ko_transfer_karo_adjacent_only(pack):
    scorer = ScamScorer(pack)
    up1 = scorer.feed("paisa ko transfer karo")
    assert up1.score == 0
    scorer.reset()
    up2 = scorer.feed("train mein hoon")
    assert up2.score == 0


def test_check_gate_blocks_danger_single_category(pack):
    scorer = ScamScorer(pack, careful=10, danger=25)
    up = scorer.feed("apna otp bataiye")
    assert up.score == 30
    assert up.level == "careful"


def test_check_fixture_s1_scores_and_reasons(pack):
    scorer = ScamScorer(pack)
    s1_segs = FIXTURE_DATA["scam"][0]["segments"]
    scores = []
    levels = []
    alert_flags = []
    reason_lists = []

    for idx, seg in enumerate(s1_segs):
        up = scorer.feed(seg, segment_index=idx)
        scores.append(up.score)
        levels.append(up.level)
        alert_flags.append(up.alert)
        if up.alert:
            reason_lists.append(up.reasons)

    assert scores == [10, 9, 45, 79, 100]
    assert levels == ["calm", "calm", "careful", "danger", "danger"]
    assert alert_flags == [False, False, False, True, False]
    assert len(reason_lists) == 1
    reasons = reason_lists[0]
    assert len(reasons) == 3
    # 3 hits from 3 different categories
    assert len({r.category for r in reasons}) == 3
    # first is SECRET_KEEP
    assert reasons[0].rule_id == "SECRET_KEEP"


def test_check_decay_arrest_warrant_followed_by_7_dhanyavaad(pack):
    scorer = ScamScorer(pack)
    scores = [scorer.feed("aapke khilaf arrest warrant nikla hai").score]
    for _ in range(7):
        scores.append(scorer.feed("dhanyavaad").score)
    assert scores == [22, 20, 18, 16, 14, 13, 0, 0]


def test_check_s1_followed_by_8_dhanyavaad_hysteresis(pack):
    scorer = ScamScorer(pack)
    s1_segs = FIXTURE_DATA["scam"][0]["segments"]
    for seg in s1_segs:
        scorer.feed(seg)
    assert scorer.alerted is True

    levels = []
    scores = []
    for _ in range(8):
        up = scorer.feed("dhanyavaad")
        levels.append(up.level)
        scores.append(up.score)

    assert "calm" not in levels
    assert scores[-1] == 0
    assert levels[-1] == "careful"


# --- 3. Normalization and Tokenizing Tests ---

def test_tokenizing_devanagari_vowel_signs():
    tokens = tokenize("नमस्ते")
    assert len(tokens) == 1
    assert tokens[0].norm == "नमस्ते"
    assert tokens[0].start == 0
    assert tokens[0].end == 6


def test_normalize_chandrabindu_equals_anusvara():
    assert normalize_token("हूँ") == normalize_token("हूं")


def test_normalize_nukta_ignored():
    assert normalize_token("ज़रूरी") == normalize_token("जरूरी")


def test_normalize_apostrophe_and_token_offsets():
    text = "they don't understand"
    tokens = tokenize(text)
    assert len(tokens) == 3
    dont = tokens[1]
    assert dont.norm == "dont"
    assert text[dont.start:dont.end] == "don't"


# --- 4. Loader and Validation Tests ---

def test_loader_shipped_pack(pack):
    assert len(pack.rules) == 20
    assert len(pack.categories) == 8
    assert len(pack.combos) == 7
    assert len(pack.dampeners) == 3


def test_loader_unknown_category_raises(tmp_path):
    bad = {
        "pack": "test", "version": 1, "window_segments": 6, "decay": 0.9,
        "strong_rule_weight": 45, "min_categories_for_danger": 2,
        "negation_window_after": 6, "negation_window_before": 2,
        "negation_guard_categories": [], "negation_phrases": [], "negation_exceptions": [],
        "categories": {"cat1": {"weight": 10, "label_en": "C1", "label_hi": "C1"}},
        "rules": [{"id": "R1", "category": "non_existent_cat", "patterns": ["test"]}],
        "combos": [], "dampeners": [],
    }
    p = tmp_path / "bad_pack.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown category"):
        load_pack(p)


def test_loader_empty_pattern_raises(tmp_path):
    bad = {
        "pack": "test", "version": 1, "window_segments": 6, "decay": 0.9,
        "strong_rule_weight": 45, "min_categories_for_danger": 2,
        "negation_window_after": 6, "negation_window_before": 2,
        "negation_guard_categories": [], "negation_phrases": [], "negation_exceptions": [],
        "categories": {"cat1": {"weight": 10, "label_en": "C1", "label_hi": "C1"}},
        "rules": [{"id": "R1", "category": "cat1", "patterns": ["   "]}],
        "combos": [], "dampeners": [],
    }
    p = tmp_path / "bad_pat.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        load_pack(p)


# --- 5. Protocol Events & Bounds Tests ---

def test_to_event_keys_and_shape(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("apna otp bataiye", segment_index=0)
    ev = up.to_event()
    assert set(ev.keys()) == {"segment_index", "score", "level", "delta", "hits", "categories"}
    assert len(ev["hits"]) > 0
    hit_ev = ev["hits"][0]
    assert set(hit_ev.keys()) == {"rule_id", "category", "label_en", "label_hi", "matched", "weight", "polarity"}


def test_reset_clears_state(pack):
    scorer = ScamScorer(pack)
    scorer.feed("yeh digital arrest hai")
    assert scorer.alerted is True
    assert scorer.max_score == 60
    scorer.reset()
    assert scorer.alerted is False
    assert scorer.max_score == 0


def test_empty_string_segment(pack):
    scorer = ScamScorer(pack)
    up = scorer.feed("")
    assert up.score == 0
    assert up.level == "calm"
    assert up.hits == []


def test_scores_stay_within_bounds(pack):
    scorer = ScamScorer(pack)
    # Stack multiple massive threats
    for _ in range(5):
        up = scorer.feed("digital arrest warrant police safe account")
        assert 0 <= up.score <= 100


# --- 6. Subprocess CLI Test ---

def test_score_transcript_cli_subprocess():
    res = subprocess.run(
        [sys.executable, "scripts/score_transcript.py", "tests/fixtures/calls.json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Overall Result: ALL PASS" in res.stdout
