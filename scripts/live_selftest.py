"""Self-test script for live listening mode and frontend components using Playwright."""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

BASE_URL = os.getenv("TEST_SERVER_URL", "http://127.0.0.1:8000")

async def test_live_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
        )
        context = await browser.new_context(permissions=["microphone"])
        page = await context.new_page()

        print(f"Navigating to {BASE_URL}...")
        try:
            await page.goto(BASE_URL, timeout=10000)
        except Exception as e:
            print(f"[FAIL] Could not load {BASE_URL}: {e}")
            await browser.close()
            return False

        # 1. Check Listen Live button exists
        btn_live = page.locator("#btn-listen-live")
        if not await btn_live.count():
            print("[FAIL] #btn-listen-live button not found in DOM.")
            await browser.close()
            return False
        print("[PASS] Found #btn-listen-live button.")

        # 2. Check Try your own words panel
        words_hdr = page.locator("#words-panel-header")
        if not await words_hdr.count():
            print("[FAIL] #words-panel-header not found.")
            await browser.close()
            return False
        print("[PASS] Found #words-panel-header.")

        # Expand words panel
        await words_hdr.click()
        btn_scam = page.locator("#words-btn-scam")
        await btn_scam.click()
        textarea = page.locator("#words-textarea")
        text_val = await textarea.input_value()
        if not text_val:
            print("[FAIL] Scam example did not populate textarea.")
            await browser.close()
            return False
        print("[PASS] Scam example populated into textarea.")

        # 3. Analyze button click (POST /api/analyze)
        btn_analyze = page.locator("#words-btn-analyze")
        await btn_analyze.click()
        await page.wait_for_timeout(1000)
        result_box = page.locator("#words-result")
        res_text = await result_box.inner_text()
        if "DANGER" not in res_text and "CAREFUL" not in res_text and "CALM" not in res_text:
            print(f"[FAIL] Analysis result badge not rendered as expected: {res_text}")
            await browser.close()
            return False
        print(f"[PASS] Analysis executed successfully with result: {res_text.strip()[:40]}...")

        # 4. Check Words we listen for panel
        rules_hdr = page.locator("#rules-panel-header")
        await rules_hdr.click()
        await page.wait_for_timeout(1000)
        rule_cards = page.locator(".rules-category-card")
        count = await rule_cards.count()
        if count == 0:
            print("[FAIL] No rule category cards loaded from /api/rules/summary.")
            await browser.close()
            return False
        print(f"[PASS] Successfully loaded {count} rule categories in summary panel.")

        await browser.close()
        print("\nAll Playwright live component tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_live_ui())
    sys.exit(0 if success else 1)
