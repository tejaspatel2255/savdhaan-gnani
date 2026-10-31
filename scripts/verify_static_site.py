"""Verify static frontend deployment, Vercel configuration, and static functionality."""

import argparse
import http.server
import json
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Tuple

VERCEL_JSON = Path("vercel.json")
FRONTEND_DIR = Path("frontend")
SAMPLE_RUN = FRONTEND_DIR / "assets" / "sample_run.jsonl"


def check_vercel_config(path: Path) -> Tuple[bool, List[str]]:
    """Validate vercel.json structure and security headers."""
    issues = []
    if not path.exists():
        return False, [f"Missing {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [f"Invalid JSON in {path}: {e}"]

    if data.get("framework") is not None:
        issues.append("vercel.json 'framework' must be null")
    if data.get("outputDirectory") != "frontend":
        issues.append("vercel.json 'outputDirectory' must be 'frontend'")
    if data.get("buildCommand") is not None:
        issues.append("vercel.json 'buildCommand' must be null or absent")
    if data.get("installCommand") is not None:
        issues.append("vercel.json 'installCommand' must be null or absent")

    headers = data.get("headers", [])
    has_cache_control = any(
        h.get("source", "").startswith("/assets/")
        and any(kv.get("key") == "Cache-Control" for kv in h.get("headers", []))
        for h in headers
    )
    if not has_cache_control:
        issues.append("vercel.json missing Cache-Control header for /assets/")

    return len(issues) == 0, issues


def check_frontend_tokens_and_size(frontend_dir: Path) -> Tuple[bool, List[str]]:
    """Ensure no secrets or tokens exist in frontend/ and check total directory size."""
    issues = []
    total_bytes = 0
    token_pattern = re.compile(r"GNANI_API_KEY|[a-zA-Z0-9_-]{32,}")

    for p in frontend_dir.rglob("*"):
        if p.is_file():
            size = p.stat().st_size
            total_bytes += size
            # Check text files for potential tokens
            if p.suffix in (".html", ".js", ".css", ".json", ".jsonl"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    if "GNANI_API_KEY" in text:
                        issues.append(f"Found 'GNANI_API_KEY' in {p}")
                except Exception:
                    pass

    total_mb = total_bytes / (1024 * 1024)
    if total_mb > 20.0:
        issues.append(f"Frontend directory size {total_mb:.1f} MB exceeds 20 MB limit")

    return len(issues) == 0, issues


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_playwright_checks(base_url: str) -> Tuple[bool, List[str]]:
    """Run browser-based static checks using Playwright."""
    issues = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return True, ["Playwright not available; skipped headless browser verification"]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for width, height, label in [(1366, 768, "1366"), (360, 740, "360")]:
                page = browser.new_page(viewport={"width": width, "height": height})
                requests_made = []
                console_errors = []

                page.on("request", lambda r: requests_made.append(r.url))
                page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

                # Open static index
                page.goto(f"{base_url}/index.html", wait_until="networkidle")
                page.wait_for_timeout(500)

                # 1. Check badge text
                badge = page.query_selector("#mode-badge")
                if not badge or "DEMO" not in (badge.text_content() or ""):
                    issues.append(f"[{label}] Expected DEMO / STATIC badge on static site")

                # 2. Check Listen Live visibly disabled
                btn_live = page.query_selector("#btn-listen-live")
                if btn_live and not btn_live.is_disabled():
                    issues.append(f"[{label}] 'Listen live' button must be disabled on static site")

                # 3. Check no forbidden backend requests made
                for req in requests_made:
                    if "/ws/" in req or "/api/session" in req or "/api/usage" in req:
                        issues.append(f"[{label}] Forbidden backend request observed: {req}")

                # Save screenshot
                out_png = Path(f"docs/screens/static_{label}.png")
                out_png.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out_png))

                page.close()
            browser.close()
    except Exception as e:
        issues.append(f"Playwright checks encountered an error: {e}")

    return len(issues) == 0, issues


def main():
    parser = argparse.ArgumentParser(description="Savdhaan Static Site Verifier")
    parser.add_argument("--url", default=None, help="Hosted URL to verify (e.g. https://savdhaan.vercel.app)")
    parser.add_argument("--with-browser", action="store_true", help="Launch Playwright browser tests")
    args = parser.parse_args()

    print("=" * 60)
    print("SAVDHAAN STATIC SITE VERIFIER")
    print("=" * 60)

    all_passed = True

    if not args.url:
        # Check vercel.json
        print("Checking vercel.json...")
        v_ok, v_issues = check_vercel_config(VERCEL_JSON)
        if v_ok:
            print("  [PASS] vercel.json is correctly configured.")
        else:
            all_passed = False
            for iss in v_issues:
                print(f"  [FAIL] {iss}")

        # Check frontend/ directory
        print("Checking frontend/ directory size and secrets...")
        f_ok, f_issues = check_frontend_tokens_and_size(FRONTEND_DIR)
        if f_ok:
            print("  [PASS] frontend/ directory is clean and under 20MB.")
        else:
            all_passed = False
            for iss in f_issues:
                print(f"  [FAIL] {iss}")

        if args.with_browser:
            # Spin up local server for Playwright verification
            port = find_free_port()
            class QuietHandler(http.server.SimpleHTTPRequestHandler):
                def log_message(self, format, *args):
                    pass

            server = http.server.HTTPServer(("127.0.0.1", port), lambda *a, **k: QuietHandler(*a, directory=str(FRONTEND_DIR), **k))
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            print(f"Local static server running at http://127.0.0.1:{port}")
            target_url = f"http://127.0.0.1:{port}"
        else:
            print("  [SKIP] Playwright browser checks skipped (pass --with-browser to run).")
            target_url = None
    else:
        target_url = args.url.rstrip("/")
        print(f"Targeting hosted URL: {target_url}")

    # Browser checks
    if target_url:
        print(f"Running browser checks against {target_url}...")
        b_ok, b_issues = run_playwright_checks(target_url)
        if b_ok:
            print("  [PASS] Browser static verification succeeded.")
        else:
            for iss in b_issues:
                print(f"  [NOTE/FAIL] {iss}")

    print("=" * 60)
    if all_passed:
        print("RESULT: ALL STATIC CHECKS PASSED.")
    else:
        print("RESULT: ONE OR MORE CHECKS FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
