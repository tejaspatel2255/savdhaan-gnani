"""Unit tests for responsive audit overlap and rule logic."""
from scripts.responsive_audit_lib import check_overlap, check_responsive_rules


def test_check_overlap_detects_collision():
    elems = [
        {"label": "#btn1", "rect": {"top": 10, "bottom": 50, "left": 10, "right": 60}},
        {"label": "#btn2", "rect": {"top": 20, "bottom": 60, "left": 50, "right": 100}},
    ]
    ov = check_overlap(elems)
    assert len(ov) == 1
    assert "#btn1 overlaps #btn2" in ov[0]


def test_check_overlap_ignores_sub_2px():
    elems = [
        {"label": "#btn1", "rect": {"top": 10, "bottom": 50, "left": 10, "right": 51}},
        {"label": "#btn2", "rect": {"top": 10, "bottom": 50, "left": 50, "right": 100}},
    ]
    ov = check_overlap(elems)
    assert len(ov) == 0


def test_check_responsive_rules_short_wide_fold():
    d = {
        "W": 1366,
        "H": 625,
        "scrollW": 1366,
        "scrollH": 625,
        "bad": {"outside": [], "small": [], "clipped": [], "tiny": [], "contrast": []},
        "score": {"bottom": 500, "top": 100},
        "phone": {"bottom": 700, "top": 300},
    }
    p = check_responsive_rules(1366, 625, "danger", d)
    assert any("phone is below the fold" in item for item in p)
