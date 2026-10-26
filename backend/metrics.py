"""Metrics calculations and summary builder."""

from typing import Any, Dict, List, Optional, Union


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
