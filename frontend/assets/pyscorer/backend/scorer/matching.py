"""Pattern compilation and phrase matching on token streams."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from backend.scorer.normalize import Token, normalize_token


@dataclass(frozen=True)
class CompiledPattern:
    """A compiled pattern consisting of parts with prefix wildcard flags."""
    parts: Tuple[str, ...]
    is_wildcard: Tuple[bool, ...]
    raw: str


def compile_pattern(p: str) -> CompiledPattern:
    """Split on whitespace. A part ending in * is a prefix wildcard (stem = normalize_token without *);
    any other part must equal the token. Empty pattern or empty stem raises ValueError.
    """
    if not p or not p.strip():
        raise ValueError("Pattern cannot be empty")

    raw_parts = p.strip().split()
    parts: List[str] = []
    is_wildcard: List[bool] = []

    for raw_part in raw_parts:
        if raw_part.endswith("*"):
            stem_raw = raw_part[:-1]
            stem = normalize_token(stem_raw)
            if not stem:
                raise ValueError(f"Empty wildcard stem in pattern: {p!r}")
            parts.append(stem)
            is_wildcard.append(True)
        else:
            norm = normalize_token(raw_part)
            if not norm:
                raise ValueError(f"Empty part in pattern: {p!r}")
            parts.append(norm)
            is_wildcard.append(False)

    return CompiledPattern(parts=tuple(parts), is_wildcard=tuple(is_wildcard), raw=p)


def find_spans(tokens: List[Token], pattern: CompiledPattern) -> List[Tuple[int, int]]:
    """Return (first, last) token indexes where ADJACENT tokens match (wildcard means startswith)."""
    matches: List[Tuple[int, int]] = []
    m = len(pattern.parts)
    n = len(tokens)
    if m == 0 or n < m:
        return matches

    for i in range(n - m + 1):
        matched = True
        for j in range(m):
            t_norm = tokens[i + j].norm
            p_part = pattern.parts[j]
            wildcard = pattern.is_wildcard[j]
            if wildcard:
                if not t_norm.startswith(p_part):
                    matched = False
                    break
            else:
                if t_norm != p_part:
                    matched = False
                    break
        if matched:
            matches.append((i, i + m - 1))
    return matches


@dataclass(frozen=True)
class Match:
    """A matched pattern span with token indexes and character slice in original text."""
    first: int
    last: int
    start: int
    end: int
    text: str


def best_match(tokens: List[Token], text: str, patterns: List[CompiledPattern]) -> Optional[Match]:
    """Over all patterns pick the match with the most tokens, ties to the smallest first index.
    Match.text is the slice of the ORIGINAL text.
    """
    best: Optional[Match] = None
    best_len = -1
    best_first = 9999999

    for pat in patterns:
        spans = find_spans(tokens, pat)
        pat_len = len(pat.parts)
        for first, last in spans:
            # Most tokens, ties to smallest first index
            if (pat_len > best_len) or (pat_len == best_len and first < best_first):
                start = tokens[first].start
                end = tokens[last].end
                matched_text = text[start:end]
                best = Match(first=first, last=last, start=start, end=end, text=matched_text)
                best_len = pat_len
                best_first = first

    return best
