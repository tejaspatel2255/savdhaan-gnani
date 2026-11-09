"""Rule pack loader and schema validation."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from backend.scorer.matching import CompiledPattern, compile_pattern


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    weight: int
    patterns: List[CompiledPattern]


@dataclass(frozen=True)
class Combo:
    id: str
    requires_all: List[str]
    bonus: int
    label_en: str
    label_hi: str
    requires_any: List[str]


@dataclass(frozen=True)
class Dampener:
    id: str
    weight: int
    label_en: str
    label_hi: str
    patterns: List[CompiledPattern]


@dataclass(frozen=True)
class RulePack:
    pack: str
    version: int
    window_segments: int
    decay: float
    strong_rule_weight: int
    min_categories_for_danger: int
    negation_window_after: int
    negation_window_before: int
    negation_guard_categories: Set[str]
    negation_phrases: List[CompiledPattern]
    negation_exceptions: List[CompiledPattern]
    categories: Dict[str, Dict[str, Any]]
    rules: List[Rule]
    combos: List[Combo]
    dampeners: List[Dampener]


def load_pack(path: Union[str, Path]) -> RulePack:
    """Load, validate, and compile a rule pack JSON file.

    Raises ValueError with a clear message for:
    - rule or combo naming an unknown category
    - missing keys
    - empty pattern lists
    - non-integer weights
    """
    file_path = Path(path)
    if not file_path.exists():
        raise ValueError(f"Rule pack file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check required top-level keys
    req_keys = [
        "pack", "version", "window_segments", "decay", "strong_rule_weight",
        "min_categories_for_danger", "negation_window_after", "negation_window_before",
        "negation_guard_categories", "negation_phrases", "negation_exceptions",
        "categories", "rules", "combos", "dampeners",
    ]
    for k in req_keys:
        if k not in data:
            raise ValueError(f"Missing required key in rule pack: {k}")

    # Allow and ignore unknown keys beginning with underscore (e.g. '_review')
    for k in data.keys():
        if k not in req_keys and not k.startswith("_"):
            pass

    categories = data["categories"]
    if not isinstance(categories, dict) or not categories:
        raise ValueError("categories must be a non-empty dictionary")

    for cat_name, cat_info in categories.items():
        if "weight" not in cat_info or not isinstance(cat_info["weight"], int):
            raise ValueError(f"Category {cat_name} must have integer weight")

    compiled_neg_phrases = [compile_pattern(p) for p in data["negation_phrases"]]
    compiled_neg_exceptions = [compile_pattern(p) for p in data["negation_exceptions"]]

    # Validate rules
    rules: List[Rule] = []
    for r in data["rules"]:
        for fld in ("id", "category", "patterns"):
            if fld not in r:
                raise ValueError(f"Rule missing required field {fld}: {r}")

        cat = r["category"]
        if cat not in categories:
            raise ValueError(f"Rule {r['id']} names unknown category {cat}")

        patterns = r["patterns"]
        if not patterns or not isinstance(patterns, list):
            raise ValueError(f"Rule {r['id']} has empty patterns list")

        compiled_pats = [compile_pattern(p) for p in patterns]

        if "weight" in r:
            if not isinstance(r["weight"], int):
                raise ValueError(f"Rule {r['id']} weight must be an integer")
            weight = r["weight"]
        else:
            weight = categories[cat]["weight"]

        rules.append(Rule(
            id=r["id"],
            category=cat,
            weight=weight,
            patterns=compiled_pats,
        ))

    # Validate combos
    combos: List[Combo] = []
    for c in data["combos"]:
        for fld in ("id", "requires_all", "bonus"):
            if fld not in c:
                raise ValueError(f"Combo missing required field {fld}: {c}")

        if not isinstance(c["bonus"], int):
            raise ValueError(f"Combo {c['id']} bonus must be an integer")

        for cat in c["requires_all"]:
            if cat not in categories:
                raise ValueError(f"Combo {c['id']} requires unknown category {cat}")

        req_any = c.get("requires_any", [])
        for cat in req_any:
            if cat not in categories:
                raise ValueError(f"Combo {c['id']} requires_any unknown category {cat}")

        combos.append(Combo(
            id=c["id"],
            requires_all=list(c["requires_all"]),
            bonus=c["bonus"],
            label_en=c.get("label_en", ""),
            label_hi=c.get("label_hi", ""),
            requires_any=list(req_any),
        ))

    # Validate dampeners
    dampeners: List[Dampener] = []
    for d in data["dampeners"]:
        for fld in ("id", "weight", "patterns"):
            if fld not in d:
                raise ValueError(f"Dampener missing required field {fld}: {d}")

        if not isinstance(d["weight"], int):
            raise ValueError(f"Dampener {d['id']} weight must be an integer")

        patterns = d["patterns"]
        if not patterns or not isinstance(patterns, list):
            raise ValueError(f"Dampener {d['id']} has empty patterns list")

        compiled_pats = [compile_pattern(p) for p in patterns]
        dampeners.append(Dampener(
            id=d["id"],
            weight=d["weight"],
            label_en=d.get("label_en", ""),
            label_hi=d.get("label_hi", ""),
            patterns=compiled_pats,
        ))

    return RulePack(
        pack=data["pack"],
        version=int(data["version"]),
        window_segments=int(data["window_segments"]),
        decay=float(data["decay"]),
        strong_rule_weight=int(data["strong_rule_weight"]),
        min_categories_for_danger=int(data["min_categories_for_danger"]),
        negation_window_after=int(data["negation_window_after"]),
        negation_window_before=int(data["negation_window_before"]),
        negation_guard_categories=set(data["negation_guard_categories"]),
        negation_phrases=compiled_neg_phrases,
        negation_exceptions=compiled_neg_exceptions,
        categories=categories,
        rules=rules,
        combos=combos,
        dampeners=dampeners,
    )


def merge_packs(packs: List[RulePack]) -> RulePack:
    """Merge multiple RulePacks into a single unified RulePack.

    Rules, combos, dampeners, and negation phrases from all packs are merged.
    Categories are shared by ID (later packs can augment category labels/weights).
    """
    if not packs:
        raise ValueError("Cannot merge empty list of packs")
    if len(packs) == 1:
        return packs[0]

    primary = packs[0]
    combined_name = "+".join(p.pack for p in packs)

    merged_categories: Dict[str, Dict[str, Any]] = {}
    for p in packs:
        for cat_id, cat_info in p.categories.items():
            if cat_id not in merged_categories:
                merged_categories[cat_id] = dict(cat_info)
            else:
                merged_categories[cat_id].update(cat_info)

    seen_rule_ids: Set[str] = set()
    merged_rules: List[Rule] = []
    for p in packs:
        for r in p.rules:
            if r.id not in seen_rule_ids:
                seen_rule_ids.add(r.id)
                merged_rules.append(r)

    seen_combo_ids: Set[str] = set()
    merged_combos: List[Combo] = []
    for p in packs:
        for c in p.combos:
            if c.id not in seen_combo_ids:
                seen_combo_ids.add(c.id)
                merged_combos.append(c)

    seen_dampener_ids: Set[str] = set()
    merged_dampeners: List[Dampener] = []
    for p in packs:
        for d in p.dampeners:
            if d.id not in seen_dampener_ids:
                seen_dampener_ids.add(d.id)
                merged_dampeners.append(d)

    merged_neg_phrases: List[CompiledPattern] = []
    seen_negs: Set[str] = set()
    for p in packs:
        for np in p.negation_phrases:
            key = np.raw
            if key not in seen_negs:
                seen_negs.add(key)
                merged_neg_phrases.append(np)

    merged_neg_exceptions: List[CompiledPattern] = []
    seen_ex: Set[str] = set()
    for p in packs:
        for ne in p.negation_exceptions:
            key = ne.raw
            if key not in seen_ex:
                seen_ex.add(key)
                merged_neg_exceptions.append(ne)

    merged_guard_cats = set().union(*(p.negation_guard_categories for p in packs))

    return RulePack(
        pack=combined_name,
        version=primary.version,
        window_segments=primary.window_segments,
        decay=primary.decay,
        strong_rule_weight=primary.strong_rule_weight,
        min_categories_for_danger=primary.min_categories_for_danger,
        negation_window_after=primary.negation_window_after,
        negation_window_before=primary.negation_window_before,
        negation_guard_categories=merged_guard_cats,
        negation_phrases=merged_neg_phrases,
        negation_exceptions=merged_neg_exceptions,
        categories=merged_categories,
        rules=merged_rules,
        combos=merged_combos,
        dampeners=merged_dampeners,
    )


def load_configured_packs(pack_names: Optional[str] = None, rules_dir: Union[str, Path] = "rules") -> RulePack:
    """Load packs specified by comma-separated string (e.g. 'hi_en,gu') and merge them."""
    rules_dir = Path(rules_dir)
    if not pack_names:
        pack_names = "hi_en"
    names = [n.strip() for n in pack_names.split(",") if n.strip()]
    loaded = []
    for name in names:
        p_path = rules_dir / f"scam_rules_{name}.json"
        loaded.append(load_pack(p_path))
    return merge_packs(loaded)
