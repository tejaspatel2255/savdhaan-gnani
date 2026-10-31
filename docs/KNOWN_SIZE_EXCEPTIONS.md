# Known File Size Exceptions

This document registers source and script files that exceed the default project size thresholds (Python/JS <= 200 lines, CSS <= 300 lines) and are intentionally preserved as-is to avoid last-minute refactor regressions prior to the competition freeze.

| File Path | Lines | Default Limit | Justification |
| :--- | :--- | :--- | :--- |
| `backend/orchestrator.py` | 497 | 200 | Central session management, timing loops, audio dispatching, and fallback logic; splitting risks subtle concurrency races. |
| `scripts/run_eval.py` | 532 | 200 | Comprehensive evaluation harness across CLI subcommands (`eval`, `wer`, `record`, `manifest`); keeping single CLI entry point preserves evaluation reproducibility. |
| `backend/scorer/engine.py` | 287 | 200 | Core multi-category scam scoring engine, hysteresis decay, and category gating state transitions. |
| `backend/gnani_stream.py` | 248 | 200 | Gnani Prisma v2.5 streaming WebSocket client with binary audio pacer, keep-alive heartbeat, and reconnection handling. |
| `backend/scorer/rules_loader.py` | 247 | 200 | Robust schema validation, transliteration normalizer, and pattern compiler for Hindi/English/Gujarati rule packs. |
| `backend/events.py` | 237 | 200 | Pydantic event bus schemas, typed telemetry models, and JSON serialization contracts for the Nazar UI. |
| `scripts/check_release.py` | 215 | 200 | Comprehensive submission verification harness with CLI options and reporting tables. |
| `scripts/credit_plan.py` | 216 | 200 | Credit simulation, quota verification, dry-run estimates, and cache lookup planner for Gnani API consumption. |
| `scripts/verify_static_site.py` | 201 | 200 | Multi-point static distribution validator (Vercel routing, token security, bundle sizes, audio manifest). |
| `backend/sources.py` | 205 | 200 | Multi-source audio feeder supporting live microphone streaming, file playback, replay simulation, and mock feeds. |

All frontend JavaScript files strictly conform to `<= 200` lines.
All frontend CSS stylesheets strictly conform to `<= 300` lines.
