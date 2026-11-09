"""Scoring package for Savdhaan scam detection."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import unicodedata

# Internal representations
@dataclass(frozen=True)
class Token:
    """A token with normalized form and character spans in original text."""
    norm: str
    start: int
    end: int


def normalize_token(raw: str) -> str:
    """Normalize raw token: NFKC, lowercase, map U+0901 to U+0902,
    delete U+093C (nukta), delete apostrophes (' and U+2019) and U+200C/U+200D.
    """
    if not raw:
        return ""
    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", raw).lower()

    out = []
    for ch in text:
        if ch == "\u0901":  # chandrabindu -> anusvara
            out.append("\u0902")
        elif ch in ("\u093c", "'", "\u2019", "\u200c", "\u200d"):  # nukta, apostrophes, ZWNJ/ZWJ
            continue
        else:
            out.append(ch)
    return "".join(out)


def _is_token_char(ch: str) -> bool:
    """Return True if character's unicodedata category starts with L, N or M."""
    cat = unicodedata.category(ch)
    return bool(cat and cat[0] in ("L", "N", "M"))


def tokenize(text: str) -> List[Token]:
    """Tokenize text into a sequence of Token objects.

    A token is a maximal run of characters whose unicodedata.category starts with L, N or M.
    An apostrophe (' or U+2019) or U+200C/U+200D between two such characters stays inside the token.
    start and end are offsets in the ORIGINAL text. Drop tokens whose norm is empty.
    """
    tokens: List[Token] = []
    if not text:
        return tokens

    n = len(text)
    i = 0
    while i < n:
        if _is_token_char(text[i]):
            start = i
            end = i + 1
            while end < n:
                ch = text[end]
                if _is_token_char(ch):
                    end += 1
                elif ch in ("'", "\u2019", "\u200c", "\u200d") and (end + 1 < n) and _is_token_char(text[end + 1]):
                    # apostrophe or ZWNJ/ZWJ between two token characters
                    end += 1
                else:
                    break
            raw_token = text[start:end]
            norm = normalize_token(raw_token)
            if norm:
                tokens.append(Token(norm=norm, start=start, end=end))
            i = end
        else:
            i += 1
    return tokens
