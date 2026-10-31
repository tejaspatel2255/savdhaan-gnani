import json
from pathlib import Path
from scripts.credit_plan import analyze_split_needs, build_credit_plan, format_plan_markdown


def test_analyze_split_needs_with_cached(tmp_path: Path):
    scripts_dir = tmp_path / "data" / "scripts"
    calls_dir = tmp_path / "data" / "calls"
    cache_dir = tmp_path / "data" / "cache"
    scripts_dir.mkdir(parents=True)
    calls_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)

    fake_calls = {
        "calls": [
            {"id": "C01", "turns": [{"text": "Hello world"}, {"text": "How are you"}]},
            {"id": "C02", "turns": [{"text": "Second call text"}]},
        ]
    }
    with open(scripts_dir / "dev_calls.json", "w", encoding="utf-8") as f:
        json.dump(fake_calls, f)

    # Neither is cached
    tot, uncached, chars, sec = analyze_split_needs("dev", calls_dir, cache_dir, scripts_dir)
    assert tot == 2
    assert uncached == 2
    assert chars == len("Hello world") + len("How are you") + len("Second call text")

    # Now simulate C01 existing
    (calls_dir / "C01.wav").write_bytes(b"RIFFdummywav")
    tot2, uncached2, chars2, sec2 = analyze_split_needs("dev", calls_dir, cache_dir, scripts_dir)
    assert tot2 == 2
    assert uncached2 == 1
    assert chars2 == len("Second call text")


def test_build_credit_plan_unknown_cost(tmp_path: Path):
    plan = build_credit_plan(balance=3000.0, base_dir=tmp_path)
    assert plan["balance"] == 3000.0
    assert plan["one_third_balance"] == 1000.0
    assert plan["tts_cost_per_1k"] is None
    md = format_plan_markdown(plan)
    assert "Cost per unit unknown" in md
    assert "one third" in md


def test_build_credit_plan_known_cost_one_third_rule(tmp_path: Path):
    # Balance 300, 1/3 is 100
    # Step 1 pilot has 861 chars, 60s
    # TTS cost = 100 per 1k chars -> ~86 credits
    # STT cost = 50 per min -> 50 credits -> Total 136 credits > 100
    plan = build_credit_plan(balance=300.0, tts_cost_per_1k=100.0, stt_cost_per_min=50.0, base_dir=tmp_path)
    assert plan["one_third_balance"] == 100.0
    pilot_step = plan["steps"][0]
    assert pilot_step["est_credits"] == 136.1
    assert pilot_step["exceeds_one_third"] is True
    md = format_plan_markdown(plan)
    assert "WARNING" in md
