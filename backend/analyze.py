"""Text analysis and rule summary endpoints for Savdhaan (no Gnani credits)."""
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.config import settings
from backend.scorer import ScamScorer, load_pack

router = APIRouter()

# In-memory rate limiter: 30 requests per minute per client
_rate_limits: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_MAX = 30
RATE_LIMIT_WINDOW = 60.0

PUNCT_SPLIT = re.compile(r"[.?!।\n\r]+")


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    pack: Optional[str] = "hi_en"


def _check_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    calls = _rate_limits[client_ip]
    # Prune old calls
    _rate_limits[client_ip] = [t for t in calls if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (max 30 requests per minute)",
        )
    _rate_limits[client_ip].append(now)


@router.post("/api/analyze")
async def analyze_text(body: AnalyzeRequest, request: Request):
    """Stateless text scoring with deterministic rules. Zero Gnani calls."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    _check_rate_limit(client_ip)

    text = body.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text must not be empty",
        )
    if len(text) > 2000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text exceeds maximum length of 2000 characters",
        )

    raw_segments = [s.strip() for s in PUNCT_SPLIT.split(text) if s.strip()]
    if not raw_segments:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid text segments found",
        )
    if len(raw_segments) > 40:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Exceeds maximum of 40 segments",
        )

    pack_name = body.pack if body.pack in ("hi_en", "gu") else "hi_en"
    rule_file = Path("rules/scam_rules_gu.json") if pack_name == "gu" else Path("rules/scam_rules_hi_en.json")
    if not rule_file.exists():
        rule_file = Path("rules/scam_rules_hi_en.json")

    pack = load_pack(rule_file)
    scorer = ScamScorer(pack, careful=settings.thresh_careful, danger=settings.thresh_danger)

    segments_res = []
    overall_categories: Dict[str, int] = {}
    last_update = None

    for idx, seg_text in enumerate(raw_segments):
        up = scorer.feed(seg_text, segment_index=idx)
        last_update = up
        for h in up.hits:
            if h.polarity == "raise":
                overall_categories[h.category] = overall_categories.get(h.category, 0) + 1

        segments_res.append({
            "segment_index": idx,
            "text": seg_text,
            "score": up.score,
            "level": up.level,
            "delta": up.delta,
            "hits": [h.to_event() for h in up.hits],
            "categories": up.categories,
        })

    return {
        "score": last_update.score if last_update else 0,
        "level": last_update.level if last_update else "calm",
        "max_score": scorer.max_score,
        "categories": overall_categories,
        "segments": segments_res,
    }


@router.get("/api/rules/summary")
async def get_rules_summary():
    """Return summary of rule categories, weights, and sample phrases."""
    rule_file = Path("rules/scam_rules_hi_en.json")
    if not rule_file.exists():
        return {"categories": []}

    import json
    with open(rule_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories_meta = data.get("categories", {})
    rules = data.get("rules", [])

    cat_examples = defaultdict(list)
    for r in rules:
        cat = r.get("category")
        patterns = r.get("patterns", [])
        for p in patterns:
            # Clean wildcard
            clean = p.rstrip("*").strip()
            if clean and clean not in cat_examples[cat] and len(cat_examples[cat]) < 6:
                cat_examples[cat].append(clean)

    summary = []
    for cat_id, meta in categories_meta.items():
        summary.append({
            "id": cat_id,
            "label_en": meta.get("label_en", cat_id),
            "label_hi": meta.get("label_hi", cat_id),
            "weight": meta.get("weight", 0),
            "examples": cat_examples.get(cat_id, [])[:6],
        })

    return {
        "categories": summary,
        "logic_en": (
            "One cue alone rarely means a scam. Danger needs several different kinds of cue "
            "close together, for example an arrest threat plus a demand for money plus 'tell no one'."
        ),
    }
