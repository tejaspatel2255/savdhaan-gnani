import sys, json
sys.path.insert(0, "/app")
from backend.scorer import ScamScorer, load_pack, merge_packs

_scorer = None

def start(pack_names, careful, danger):
    """pack_names: 'hi_en' or 'hi_en,gu'. Starts a fresh scoring session."""
    global _scorer
    packs = [load_pack("/app/rules/scam_rules_%s.json" % n.strip()) for n in pack_names.split(",") if n.strip()]
    _scorer = ScamScorer(merge_packs(packs), careful=int(careful), danger=int(danger))
    return "ok"

def feed(text, idx):
    """Score one finished sentence. Returns the risk event body as JSON plus whether the alert threshold was crossed."""
    was = _scorer.alerted
    up = _scorer.feed(text, segment_index=int(idx))
    body = up.to_event()
    body["alert"] = bool(up.alert)
    body["reasons"] = [h.to_event() for h in up.reasons][:3]
    body["max_score"] = _scorer.max_score
    return json.dumps(body, ensure_ascii=False)
