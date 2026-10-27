"""Builds recorded event streams for frontend demo mode offline."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.events import (
    Emitter,
    build_session_event,
    build_transcript_event,
    build_risk_event,
    build_summary_event,
    build_audio_level_event,
)
from backend.scorer import ScamScorer, load_pack

ASSETS_DIR = ROOT / "frontend" / "assets"
CACHE_WARNINGS = ROOT / "data" / "cache" / "warnings"


def build_legit_sample():
    """Build frontend/assets/sample_legit.jsonl with bank EMI reminder."""
    pack = load_pack("rules/scam_rules_hi_en.json")
    scorer = ScamScorer(pack, careful=30, danger=60)

    segments = [
        "namaste main aapke bank ki taraf se automated reminder bol raha hoon",
        "aapki emi 5 tareekh ko due hai",
        "kripya samay par bhugtaan karein",
        "kisi bhi sahayata ke liye branch mein sampark karein",
        "dhanyavaad",
    ]

    session_id = "sess_demo_legit"
    out_file = ASSETS_DIR / "sample_legit.jsonl"
    if out_file.exists():
        out_file.unlink()

    emitter = Emitter(session_id=session_id, log_path=out_file)
    t = 0.0

    # 1. Starting session
    build_session_event(
        emitter=emitter, state="starting", mode="mock", mode_label="DEMO · recorded",
        call_title="", synthetic=True, lang="hi-IN",
        thresholds={"careful": 30, "danger": 60}, t=t
    )

    # 2. Listening session
    build_session_event(
        emitter=emitter, state="listening", mode="mock", mode_label="DEMO · recorded",
        call_title="Bank EMI reminder (synthetic, normal call)", synthetic=True, lang="hi-IN",
        thresholds={"careful": 30, "danger": 60}, t=t
    )

    # Audio levels
    for _ in range(5):
        t += 0.2
        build_audio_level_event(emitter=emitter, rms=0.03, t=round(t, 2))

    max_score = 0

    for idx, text in enumerate(segments):
        t += 1.2
        update = scorer.feed(text, segment_index=idx)
        if update.score > max_score:
            max_score = update.score

        # Transcript event
        build_transcript_event(
            emitter=emitter, segment_index=idx, segment_id=f"seg_{idx}", text=text,
            audio_duration_ms=1200, stt_latency_ms=150, t=round(t, 2)
        )

        # Risk event
        build_risk_event(
            emitter=emitter, segment_index=idx, score=update.score, level=update.level,
            delta=update.delta, hits=[h.to_dict() if hasattr(h, "to_dict") else h for h in update.hits],
            categories=update.categories, t=round(t, 2)
        )

        for _ in range(3):
            t += 0.3
            build_audio_level_event(emitter=emitter, rms=0.25, t=round(t, 2))

    # Summary event
    t += 0.5
    build_summary_event(
        emitter=emitter, duration_s=round(t, 2), segments=len(segments),
        time_to_alert_s=None, max_score=max_score, final_level="calm",
        categories=update.categories,
        stt_latency_ms={"median": 150, "p95": 180},
        credits_used={"tts_chars": 0, "stt_seconds": round(t, 1)},
        mode="mock", synthetic=True, t=round(t, 2)
    )

    print(f"Generated {out_file} (max_score={max_score}).")


def check_and_report_scam_warning_audio():
    """Checks whether warning audio file exists in data/cache/warnings for scam sample."""
    sample_scam_file = ASSETS_DIR / "sample_run.jsonl"
    if not sample_scam_file.exists():
        return

    warning_file = CACHE_WARNINGS / "warning_cyber_arrest_hi.wav"
    if not warning_file.exists():
        print(
            "Note: Warning audio for scam sample does not exist yet.\n"
            "Run: python scripts/make_warnings.py --lang hi-IN --go, then python scripts/export_static.py, then python scripts/build_sample_runs.py"
        )


def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    build_legit_sample()
    check_and_report_scam_warning_audio()


if __name__ == "__main__":
    main()
