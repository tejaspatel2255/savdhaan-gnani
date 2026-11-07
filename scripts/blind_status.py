"""Pure helper for checking blind set evaluation status."""
from typing import Any, Dict


def blind_status(results: Dict[str, Any]) -> str:
    """Return 'not_scored', 'placeholder', or 'scored'.
    
    Rule:
    - If blind split does not exist or has no scoring info: 'not_scored'
    - If blind split exists and n < 10: 'placeholder'
    - If blind split exists and n >= 10: 'scored'
    """
    if not results or not isinstance(results, dict):
        return "not_scored"

    splits = results.get("splits") or {}
    blind = splits.get("blind")
    if not blind or not isinstance(blind, dict):
        return "not_scored"

    # Check n in ceiling or top-level blind dict
    n = blind.get("n")
    if n is None and "ceiling" in blind and isinstance(blind["ceiling"], dict):
        n = blind["ceiling"].get("n")

    if n is None:
        return "not_scored"

    try:
        n_val = int(n)
        if n_val < 10:
            return "placeholder"
        return "scored"
    except (ValueError, TypeError):
        return "not_scored"
