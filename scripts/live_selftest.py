"""Live mode end-to-end selftest script using Playwright and Fake STT server.
Runs fully offline with mock backend and fake audio devices.
"""

import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

SCREENS_DIR = Path("docs/screens")
SCREENS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.getenv("TEST_SERVER_URL", "http://127.0.0.1:8000")


async def run_live_selftest():
    print(f"Starting Live Mode Self-Test against {BASE_URL}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
            ],
        )

        # Desktop context
        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            permissions=["microphone"],
        )
        page = await ctx.new_page()

        print(f"Loading {BASE_URL}...")
        try:
            await page.goto(BASE_URL, timeout=10000)
            await page.wait_for_selector("#btn-listen-live", timeout=5000)
        except Exception as e:
            print(f"[FAIL] Could not connect to {BASE_URL}: {e}")
            await browser.close()
            return False

        # Capture live idle screenshot
        await page.screenshot(path=str(SCREENS_DIR / "live_idle.png"))
        print("[PASS] Captured live_idle.png")

        # 1. Test 'Try your own words' panel
        print("Testing 'Try your own words' panel...")
        words_hdr = page.locator("#words-panel-header")
        await words_hdr.click()
        await page.wait_for_timeout(300)

        # Scam example
        await page.locator("#words-btn-scam").click()
        val = await page.locator("#words-textarea").input_value()
        assert len(val) > 0, "Scam example text missing"
        await page.locator("#words-btn-analyze").click()
        await page.wait_for_timeout(500)
        res_text = await page.locator("#words-result").inner_text()
        assert "DANGER" in res_text or "CAREFUL" in res_text, "Expected scam danger/careful badge"
        print("[PASS] Try your own words: Scam analysis verified.")

        # Safe example
        await page.locator("#words-btn-safe").click()
        await page.locator("#words-btn-analyze").click()
        await page.wait_for_timeout(500)
        safe_res = await page.locator("#words-result").inner_text()
        assert "CALM" in safe_res, "Expected calm safe badge"
        print("[PASS] Try your own words: Safe analysis verified.")

        # 2. Test 'Words we listen for' panel
        print("Testing 'Words we listen for' panel...")
        rules_hdr = page.locator("#rules-panel-header")
        await rules_hdr.click()
        await page.wait_for_timeout(1000)
        cards = await page.locator(".rules-category-card").count()
        assert cards >= 8, f"Expected 8 category cards, found {cards}"
        print(f"[PASS] Words we listen for: {cards} categories rendered.")

        # 3. Test Play Sample Scam Call and Receipt Dialog interactions
        print("Testing Sample Scam Call & Receipt Dialog...")
        await page.locator("#btn-demo-scam").click()
        await page.wait_for_selector(".receipt-dialog", timeout=8000)
        await page.screenshot(path=str(SCREENS_DIR / "live_receipt.png"))
        print("[PASS] Captured live_receipt.png")

        # Test Close button on Receipt Dialog
        close_btn = page.locator(".btn-receipt-close")
        assert await close_btn.is_visible(), "Receipt close button not visible"
        await close_btn.click()
        await page.wait_for_timeout(300)
        receipt_root = page.locator("#receipt-root")
        is_hidden = await receipt_root.evaluate("el => el.classList.contains('hidden')")
        assert is_hidden, "Receipt dialog did not close after clicking Close"
        print("[PASS] Receipt Close button closes dialog.")

        # 4. Mobile viewport capture
        mobile_ctx = await browser.new_context(
            viewport={"width": 360, "height": 740},
            permissions=["microphone"],
        )
        mobile_page = await mobile_ctx.new_page()
        await mobile_page.goto(BASE_URL, timeout=10000)
        await mobile_page.screenshot(path=str(SCREENS_DIR / "live_mobile.png"))
        print("[PASS] Captured live_mobile.png")

        await browser.close()
        print("\n[SUCCESS] All live selftest steps completed successfully!")
        return True


if __name__ == "__main__":
    ok = asyncio.run(run_live_selftest())
    sys.exit(0 if ok else 1)
