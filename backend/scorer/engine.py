"""Scam detection scoring engine implementation."""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from backend.scorer.matching import Match, best_match, find_spans
from backend.scorer.normalize import Token, tokenize
from backend.scorer.rules_loader import Combo, Dampener, Rule, RulePack


@dataclass(frozen=True)
class Hit:
    rule_id: str
    category: str
    label_en: str
    label_hi: str
    matched: str
    weight: int
    polarity: str
    segment_index: int
    match: Optional[Match] = None
    rule_order: int = 0

    def to_event(self) -> Dict[str, Any]:
        """Hit shape strictly matching docs/EVENTS.md:
        {rule_id:str, category:str, label_en:str, label_hi:str, matched:str, weight:int, polarity:"raise"|"dampen"}
        """
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "label_en": self.label_en,
            "label_hi": self.label_hi,
            "matched": self.matched,
            "weight": self.weight,
            "polarity": self.polarity,
        }


@dataclass
class RiskUpdate:
    segment_index: int
    score: int
    level: str
    delta: int
    hits: List[Hit]
    categories: Dict[str, int]
    alert: bool
    reasons: List[Hit]
    combos: List[str]
    suppressed: List[Hit]

    def to_event(self) -> Dict[str, Any]:
        """Return exactly the keys of the risk message in docs/EVENTS.md except type, session_id, seq, t."""
        return {
            "segment_index": self.segment_index,
            "score": self.score,
            "level": self.level,
            "delta": self.delta,
            "hits": [h.to_event() for h in self.hits],
            "categories": self.categories,
        }


class ScamScorer:
    """Live scam scoring engine tracking rolling window evidence and risk levels."""

    def __init__(self, pack: RulePack, careful: int = 30, danger: int = 60) -> None:
        self.pack = pack
        self.careful = careful
        self.danger = danger
        self.reset()

    def reset(self) -> None:
        """Reset state for a new session."""
        self._current_index = -1
        self._previous_score = 0
        self._alerted = False
        self._max_score = 0
        # window stores history of (segment_index, raise_hits, dampener_hits)
        self._window: List[Tuple[int, List[Hit], List[Hit]]] = []

    @property
    def alerted(self) -> bool:
        return self._alerted

    @property
    def max_score(self) -> int:
        return self._max_score

    def feed(self, text: str, segment_index: Optional[int] = None) -> RiskUpdate:
        """Process one speech segment and compute updated risk state."""
        if segment_index is None:
            self._current_index += 1
            idx = self._current_index
        else:
            self._current_index = segment_index
            idx = segment_index

        # a. Tokenize
        tokens = tokenize(text)

        # Find best match for each rule (at most one hit per rule)
        raw_raise_hits: List[Hit] = []
        for rule_order, rule in enumerate(self.pack.rules):
            m = best_match(tokens, text, rule.patterns)
            if m is not None:
                cat_info = self.pack.categories[rule.category]
                raw_raise_hits.append(Hit(
                    rule_id=rule.id,
                    category=rule.category,
                    label_en=cat_info["label_en"],
                    label_hi=cat_info["label_hi"],
                    matched=m.text,
                    weight=rule.weight,
                    polarity="raise",
                    segment_index=idx,
                    match=m,
                    rule_order=rule_order,
                ))

        # Find best match for each dampener (at most one hit per dampener)
        dampener_hits: List[Hit] = []
        for d_order, dampener in enumerate(self.pack.dampeners):
            m = best_match(tokens, text, dampener.patterns)
            if m is not None:
                dampener_hits.append(Hit(
                    rule_id=dampener.id,
                    category="safe",
                    label_en=dampener.label_en,
                    label_hi=dampener.label_hi,
                    matched=m.text,
                    weight=dampener.weight,  # negative
                    polarity="dampen",
                    segment_index=idx,
                    match=m,
                    rule_order=d_order,
                ))

        # b. Negation guard
        # Find token spans of secrecy hits in this segment
        secrecy_spans = [
            (h.match.first, h.match.last)
            for h in raw_raise_hits
            if h.category == "secrecy" and h.match is not None
        ]

        # Find all negation phrase occurrences
        candidate_negations: List[Tuple[int, int]] = []
        for neg_pat in self.pack.negation_phrases:
            spans = find_spans(tokens, neg_pat)
            for f, l in spans:
                # skip (i): occurrence lying completely inside the token span of a hit from category 'secrecy'
                in_secrecy = any(sf <= f and l <= sl for sf, sl in secrecy_spans)
                if in_secrecy:
                    continue

                # skip (ii): occurrence whose first token is also the first token of a negation_exceptions phrase
                is_exception = False
                for exc_pat in self.pack.negation_exceptions:
                    exc_spans = find_spans(tokens, exc_pat)
                    if any(ef == f for ef, _ in exc_spans):
                        is_exception = True
                        break
                if is_exception:
                    continue

                candidate_negations.append((f, l))

        # Check suppression for hits in negation_guard_categories
        active_raise_hits: List[Hit] = []
        suppressed_hits: List[Hit] = []

        w_before = self.pack.negation_window_before
        w_after = self.pack.negation_window_after

        for h in raw_raise_hits:
            if h.category in self.pack.negation_guard_categories and h.match is not None:
                f, l = h.match.first, h.match.last
                is_suppressed = False
                for a, b in candidate_negations:
                    # occurrence [a, b] does not overlap [f, l]
                    no_overlap = (b < f) or (a > l)
                    # and lies inside [f - negation_window_before, l + negation_window_after]
                    in_window = (a >= f - w_before) and (b <= l + w_after)
                    if no_overlap and in_window:
                        is_suppressed = True
                        break
                if is_suppressed:
                    suppressed_hits.append(h)
                else:
                    active_raise_hits.append(h)
            else:
                active_raise_hits.append(h)

        # c. Append this segment to rolling window
        self._window.append((idx, active_raise_hits, dampener_hits))
        if len(self._window) > self.pack.window_segments:
            self._window.pop(0)

        # d. Per category, evidence = largest weight * factor among its raise hits in the window
        # Ties: newer hit, then rule listed first in pack
        category_best_hit: Dict[str, Hit] = {}
        category_evidence: Dict[str, float] = {}

        for item_idx, (seg_idx, seg_raise, _) in enumerate(self._window):
            age = (len(self._window) - 1) - item_idx
            factor = self.pack.decay ** age
            for hit in seg_raise:
                cat = hit.category
                val = hit.weight * factor
                if cat not in category_evidence:
                    category_evidence[cat] = val
                    category_best_hit[cat] = hit
                else:
                    cur_val = category_evidence[cat]
                    if val > cur_val + 1e-9:
                        category_evidence[cat] = val
                        category_best_hit[cat] = hit
                    elif abs(val - cur_val) <= 1e-9:
                        # Tie break: newer hit (larger seg_idx), then smaller rule_order
                        cur_hit = category_best_hit[cat]
                        if hit.segment_index > cur_hit.segment_index:
                            category_evidence[cat] = val
                            category_best_hit[cat] = hit
                        elif hit.segment_index == cur_hit.segment_index and hit.rule_order < cur_hit.rule_order:
                            category_evidence[cat] = val
                            category_best_hit[cat] = hit

        # e. Active combos
        active_combos: List[str] = []
        combo_bonus_total = 0
        for combo in self.pack.combos:
            has_all = all(cat in category_evidence for cat in combo.requires_all)
            if has_all:
                if combo.requires_any:
                    has_any = any(cat in category_evidence for cat in combo.requires_any)
                else:
                    has_any = True
                if has_any:
                    active_combos.append(combo.id)
                    combo_bonus_total += combo.bonus

        # f. Distinct dampeners in the window
        # Each distinct dampener id in window adds weight * factor of its most recent occurrence
        dampener_most_recent: Dict[str, Tuple[int, Hit]] = {}  # id -> (age, hit)
        for item_idx, (_, _, seg_damp) in enumerate(self._window):
            age = (len(self._window) - 1) - item_idx
            for d_hit in seg_damp:
                # most recent has the smallest age
                if d_hit.rule_id not in dampener_most_recent or age < dampener_most_recent[d_hit.rule_id][0]:
                    dampener_most_recent[d_hit.rule_id] = (age, d_hit)

        dampener_total = 0.0
        for _, (age, d_hit) in dampener_most_recent.items():
            factor = self.pack.decay ** age
            dampener_total += d_hit.weight * factor  # weight is negative

        # g. raw and score
        sum_evidence = sum(category_evidence.values())
        raw = sum_evidence + combo_bonus_total + dampener_total
        score = min(100, max(0, math.floor(raw + 0.5)))
        delta = score - self._previous_score if idx > 0 else 0
        self._previous_score = score
        if score > self._max_score:
            self._max_score = score

        # h. Gate and level
        # Gate: at least min_categories_for_danger categories have evidence,
        # OR a raise hit in the window has weight >= strong_rule_weight
        has_min_categories = len(category_evidence) >= self.pack.min_categories_for_danger
        has_strong_rule = any(
            h.weight >= self.pack.strong_rule_weight
            for _, seg_raise, _ in self._window
            for h in seg_raise
        )
        gate_holds = has_min_categories or has_strong_rule

        if score >= self.danger and gate_holds:
            computed_level = "danger"
        elif score >= self.careful:
            computed_level = "careful"
        else:
            computed_level = "calm"

        # Hysteresis: once alert fired, computed calm is reported as careful
        if self._alerted and computed_level == "calm":
            level = "careful"
        else:
            level = computed_level

        # i. Alert and reasons
        alert = False
        reasons: List[Hit] = []
        if level == "danger" and not self._alerted:
            alert = True
            self._alerted = True
            # up to 3 categories, highest evidence first (ties: newer first)
            sorted_cats = sorted(
                category_evidence.keys(),
                key=lambda c: (category_evidence[c], category_best_hit[c].segment_index),
                reverse=True,
            )
            top_3 = sorted_cats[:3]
            reasons = [category_best_hit[c] for c in top_3]

        # j. categories = {category: number of raise hits in the window}
        cat_counts: Dict[str, int] = {}
        for _, seg_raise, _ in self._window:
            for h in seg_raise:
                cat_counts[h.category] = cat_counts.get(h.category, 0) + 1

        all_segment_hits = active_raise_hits + dampener_hits

        return RiskUpdate(
            segment_index=idx,
            score=score,
            level=level,
            delta=delta,
            hits=all_segment_hits,
            categories=cat_counts,
            alert=alert,
            reasons=reasons,
            combos=active_combos,
            suppressed=suppressed_hits,
        )
