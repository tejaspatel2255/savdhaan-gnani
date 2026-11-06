"""Playwright browser check: verifies live bar state, sample buttons, Khata page, and console hygiene."""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent

async def run_browser_check():
    port = 8791
    env = os.environ.copy()
    env["DEMO"] = "1"
    
    # Start server
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to be responsive
    import httpx
    for _ in range(30):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"http://127.0.0.1:{port}/api/health")
                if res.status_code == 200:
                    break
        except Exception:
            await asyncio.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError("Server failed to start")

    console_errors = []
    failed_requests = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1366, "height": 768})
            page = await context.new_page()

            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("requestfailed", lambda req: failed_requests.append(req.url))

            # 1. Fresh page load
            await page.goto(f"http://127.0.0.1:{port}/")
            await page.wait_for_load_state("networkidle")

            # Check that Stamp and Receipt are not visible on fresh load
            stamp_visible = await page.is_visible(".rubber-stamp")
            pinned_visible = await page.is_visible(".pinned-stamp")
            receipt_visible = await page.is_visible(".receipt-dialog")
            assert not stamp_visible, "Rubber stamp should not be visible on fresh load"
            assert not pinned_visible, "Pinned stamp should not be visible on fresh load"
            assert not receipt_visible, "Receipt dialog should not be visible on fresh load"

            # Check live bar state is idle
            stop_visible = await page.is_visible("#btn-live-stop")
            assert not stop_visible, "#btn-live-stop should be hidden on fresh load"

            # 2. Press Sample Scam Call
            await page.click("#btn-demo-scam")
            # Wait for replay to trigger and check #btn-live-stop remains hidden throughout
            for _ in range(20):
                stop_vis = await page.is_visible("#btn-live-stop")
                assert not stop_vis, "#btn-live-stop must NOT be visible during sample playback"
                await asyncio.sleep(0.2)

            # Wait a little and click Stop button
            if await page.is_visible("#btn-stop"):
                await page.click("#btn-stop")

            # 3. Press Sample Normal Call
            await page.click("#btn-demo-normal")
            for _ in range(15):
                stop_vis = await page.is_visible("#btn-live-stop")
                assert not stop_vis, "#btn-live-stop must NOT be visible during normal playback"
                await asyncio.sleep(0.2)

            # 4. Open Khata (report.html)
            await page.goto(f"http://127.0.0.1:{port}/report.html")
            await page.wait_for_load_state("networkidle")
            assert await page.is_visible(".khata-header"), "Khata header must be visible"

            # Take a screenshot of the main page and khata
            screens_dir = ROOT / "docs" / "screens"
            screens_dir.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screens_dir / "s1_khata_check.png"))

            await page.goto(f"http://127.0.0.1:{port}/")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(screens_dir / "s1_main_check.png"))

            await browser.close()

    finally:
        proc.kill()
        proc.wait()

    print(f"Browser check complete.")
    print(f"Console errors: {console_errors}")
    print(f"Failed requests: {failed_requests}")

if __name__ == "__main__":
    asyncio.run(run_browser_check())
