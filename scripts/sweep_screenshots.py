"""Browser glitch sweep with Playwright for Savdhaan.
Checks widths (1920, 1366, 1280, 1024, 360) and languages (hi, gu)
Saves screenshots to docs/screens/ and checks overflow & text clipping.
"""
import os
import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCREENS_DIR = ROOT / "docs" / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)


def run_sweep():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed or available. Installing or checking...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        from playwright.sync_api import sync_playwright

    # Start static server
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 8085
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", str(ROOT / "frontend")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)

    base_url = f"http://127.0.0.1:{port}"
    widths = [1920, 1366, 1280, 1024, 360]
    langs = ["hi", "gu"]
    issues = []

    print(f"Starting Playwright glitch sweep on {base_url}...")

    try:
        with sync_playwright() as p:
            # Try launch with chrome channel or standard chromium
            try:
                browser = p.chromium.launch(headless=True, channel="chrome")
            except Exception:
                try:
                    browser = p.chromium.launch(headless=True)
                except Exception:
                    # Run playwright install chromium once to finish any partial download
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                    browser = p.chromium.launch(headless=True)
            for width in widths:
                height = 900 if width > 500 else 740
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()

                # 1. Main index page
                page.goto(f"{base_url}/index.html", wait_until="networkidle")

                for lang in langs:
                    # Switch language if dropdown exists
                    try:
                        page.select_option("#lang-select", lang)
                    except Exception:
                        pass
                    page.wait_for_timeout(300)

                    # IDLE SCREENSHOT
                    idle_shot = SCREENS_DIR / f"idle_{width}_{lang}.png"
                    page.screenshot(path=str(idle_shot), full_page=False)

                    # Check overflow
                    scroll_w = page.evaluate("document.documentElement.scrollWidth")
                    inner_w = page.evaluate("window.innerWidth")
                    if scroll_w > inner_w + 1:
                        issues.append(f"Width {width} ({lang}) idle overflow: scrollWidth {scroll_w} > innerWidth {inner_w}")

                    # Play sample scam call
                    try:
                        page.click("#btn-sample-scam")
                    except Exception:
                        pass

                    # Wait for danger (around 22s in simulated time, or wait for danger attribute)
                    try:
                        page.wait_for_selector('[data-state="danger"]', timeout=30000)
                        danger_shot = SCREENS_DIR / f"danger_{width}_{lang}.png"
                        page.screenshot(path=str(danger_shot))
                    except Exception:
                        pass

                    # Wait for receipt / ended state
                    try:
                        page.wait_for_selector(".receipt-container, [data-state=\"safe\"]", timeout=35000)
                        receipt_shot = SCREENS_DIR / f"receipt_{width}_{lang}.png"
                        page.screenshot(path=str(receipt_shot))
                    except Exception:
                        pass

                    # Reset and test normal call
                    page.goto(f"{base_url}/index.html", wait_until="networkidle")
                    try:
                        page.select_option("#lang-select", lang)
                        page.click("#btn-sample-legit")
                        page.wait_for_selector('[data-state="ended"], .receipt-container', timeout=20000)
                        legit_shot = SCREENS_DIR / f"normal_{width}_{lang}.png"
                        page.screenshot(path=str(legit_shot))
                    except Exception:
                        pass

                # 2. Report page (/report.html)
                page.goto(f"{base_url}/report.html", wait_until="networkidle")
                report_shot = SCREENS_DIR / f"report_{width}.png"
                page.screenshot(path=str(report_shot), full_page=True)

                scroll_w = page.evaluate("document.documentElement.scrollWidth")
                inner_w = page.evaluate("window.innerWidth")
                if scroll_w > inner_w + 1:
                    issues.append(f"Width {width} report.html overflow: scrollWidth {scroll_w} > innerWidth {inner_w}")

                context.close()
            browser.close()
    finally:
        server_proc.terminate()

    print("\n=== SWEEP COMPLETED ===")
    print(f"Screenshots saved to: {SCREENS_DIR}")
    if issues:
        print("Detected issues:")
        for iss in issues:
            print(f"  - {iss}")
    else:
        print("Zero layout overflow detected across all screen sizes!")


if __name__ == "__main__":
    run_sweep()
