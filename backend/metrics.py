"""Metrics calculations and summary builder."""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import jiwer

from backend.scorer.normalize import tokenize


def percentile(values: List[Union[int, float]], p: float) -> Optional[int]:
    """Compute p-th percentile (0 <= p <= 100) with linear interpolation.

    Returns None for an empty list. Output is rounded to nearest int.
    """
    if not values:
        return None
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return int(round(sorted_vals[0]))

    # Rank between 0 and n - 1
    rank = (p / 100.0) * (n - 1)
    lower_idx = int(rank)
    upper_idx = min(lower_idx + 1, n - 1)
    weight = rank - lower_idx

    val = sorted_vals[lower_idx] * (1.0 - weight) + sorted_vals[upper_idx] * weight
    return int(round(val))


def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[Optional[float], Optional[float]]:
    """Compute Wilson score interval (low, high) clamped to [0, 1].

    Returns (None, None) when n is 0.
    """
    if n == 0:
        return (None, None)
    p = float(k) / float(n)
    denom = 1.0 + (z ** 2) / float(n)
    center = (p + (z ** 2) / (2.0 * float(n))) / denom
    variance = (p * (1.0 - p) / float(n)) + ((z ** 2) / (4.0 * (float(n) ** 2)))
    spread = (z / denom) * math.sqrt(max(0.0, variance))
    low = max(0.0, center - spread)
    high = min(1.0, center + spread)
    return (round(low, 4), round(high, 4))


def _dist_summary(vals: List[float]) -> Optional[Dict[str, Any]]:
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    median_val = s[mid] if (n % 2 == 1) else (s[mid - 1] + s[mid]) / 2.0
    return {
        "n": n,
        "median": round(median_val, 2),
        "mean": round(sum(vals) / float(n), 2),
        "max": round(max(vals), 2),
    }


def detection_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute detection performance and latency metrics over evaluated call rows."""
    tp = sum(1 for r in rows if r.get("label") == "scam" and r.get("alerted") is True)
    fn = sum(1 for r in rows if r.get("label") == "scam" and not r.get("alerted"))
    fp = sum(1 for r in rows if r.get("label") == "legit" and r.get("alerted") is True)
    tn = sum(1 for r in rows if r.get("label") == "legit" and not r.get("alerted"))

    scam_count = tp + fn
    legit_count = fp + tn
    total_alerts = tp + fp

    precision = round(tp / float(total_alerts), 4) if total_alerts > 0 else None
    recall = round(tp / float(scam_count), 4) if scam_count > 0 else None

    if precision is None or recall is None or (precision + recall == 0):
        f1 = None
    else:
        f1 = round(2.0 * (precision * recall) / (precision + recall), 4)

    false_alarm_rate = round(fp / float(legit_count), 4) if legit_count > 0 else None
    recall_ci95 = wilson_ci(tp, scam_count) if scam_count > 0 else (None, None)
    false_alarm_ci95 = wilson_ci(fp, legit_count) if legit_count > 0 else (None, None)

    careful_on_legit = sum(
        1 for r in rows
        if r.get("label") == "legit"
        and not r.get("alerted")
        and r.get("max_level") in ("careful", "danger")
    )

    tta_vals = [
        float(r["alert_t"]) for r in rows
        if r.get("label") == "scam" and r.get("alerted") is True and r.get("alert_t") is not None
    ]
    tfc_vals = [
        float(r["alert_t"]) - float(r["first_cue_s"]) for r in rows
        if r.get("label") == "scam"
        and r.get("alerted") is True
        and r.get("alert_t") is not None
        and r.get("first_cue_s") is not None
    ]

    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alarm_rate": false_alarm_rate,
        "recall_ci95": recall_ci95,
        "false_alarm_ci95": false_alarm_ci95,
        "careful_on_legit": careful_on_legit,
        "time_to_alert_s": _dist_summary(tta_vals),
        "time_from_cue_s": _dist_summary(tfc_vals),
    }


def wer_normalize(text: str) -> str:
    """Tokenize with scorer's tokenizer (removing punct, normalizing nukta & chandrabindu)."""
    tokens = tokenize(text)
    return " ".join(t.norm.lower() for t in tokens)


def compute_wer(ref: str, hyp: str) -> float:
    """Compute Word Error Rate using jiwer on normalized strings. Raises ValueError on empty ref."""
    norm_ref = wer_normalize(ref)
    norm_hyp = wer_normalize(hyp)
    if not norm_ref.strip():
        raise ValueError("Reference text cannot be empty for WER calculation.")
    return round(float(jiwer.wer(norm_ref, norm_hyp)), 4)


def latency_summary(values_ms: List[int]) -> Dict[str, Any]:
    """Compute {n, p50, p95} for latency values."""
    if not values_ms:
        return {"n": 0, "p50": None, "p95": None}
    return {
        "n": len(values_ms),
        "p50": percentile(values_ms, 50.0),
        "p95": percentile(values_ms, 95.0),
    }


def build_summary(
    duration_s: float,
    segments: int,
    time_to_alert_s: Optional[float],
    max_score: int,
    final_level: str,
    categories: Dict[str, int],
    latencies: List[int],
    credits_used: Dict[str, Union[float, int]],
    mode: str,
    synthetic: bool,
) -> Dict[str, Any]:
    """Build summary dictionary matching docs/EVENTS.md."""
    p50 = percentile(latencies, 50.0)
    p95 = percentile(latencies, 95.0)

    return {
        "duration_s": round(float(duration_s), 2),
        "segments": segments,
        "time_to_alert_s": round(float(time_to_alert_s), 2) if time_to_alert_s is not None else None,
        "max_score": max_score,
        "final_level": final_level,
        "categories": categories,
        "stt_latency_ms": {"p50": p50, "p95": p95},
        "credits_used": credits_used,
        "mode": mode,
        "synthetic": synthetic,
    }
