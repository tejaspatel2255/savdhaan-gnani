import json
from pathlib import Path
from scripts.verify_static_site import check_vercel_config, check_frontend_tokens_and_size


def test_check_vercel_config_valid(tmp_path: Path):
    cfg = tmp_path / "vercel.json"
    cfg.write_text(json.dumps({
        "framework": None,
        "outputDirectory": "frontend",
        "headers": [
            {
                "source": "/assets/(.*)",
                "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]
            }
        ]
    }), encoding="utf-8")
    ok, issues = check_vercel_config(cfg)
    assert ok is True
    assert len(issues) == 0


def test_check_vercel_config_invalid(tmp_path: Path):
    cfg = tmp_path / "vercel.json"
    cfg.write_text(json.dumps({
        "framework": "nextjs",
        "buildCommand": "npm run build"
    }), encoding="utf-8")
    ok, issues = check_vercel_config(cfg)
    assert ok is False
    assert any("framework" in i for i in issues)
    assert any("buildCommand" in i for i in issues)


def test_check_frontend_tokens_and_size(tmp_path: Path):
    f_dir = tmp_path / "frontend"
    f_dir.mkdir()
    (f_dir / "index.html").write_text("<html>Clean content</html>", encoding="utf-8")
    ok, issues = check_frontend_tokens_and_size(f_dir)
    assert ok is True

    # Inject secret token
    (f_dir / "leak.js").write_text("const key = 'GNANI_API_KEY';", encoding="utf-8")
    ok2, issues2 = check_frontend_tokens_and_size(f_dir)
    assert ok2 is False
    assert any("GNANI_API_KEY" in i for i in issues2)
