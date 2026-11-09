"""check_browser_live.py — End-to-end verification of 'Speak yourself' mode with mocked SpeechRecognition."""
import http.server
import socketserver
import threading
import time
import sys
from playwright.sync_api import sync_playwright

PORT = 8089

def run_server():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory="frontend", **kwargs)
        def log_message(self, format, *args):
            pass
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()

def main():
    srv = threading.Thread(target=run_server, daemon=True)
    srv.start()
    time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1523, "height": 720})
        
        # Inject Mock SpeechRecognition before page loads
        context.add_init_script("""
        window.MockSpeechRecognition = class {
            constructor() {
                this.continuous = true;
                this.interimResults = true;
                this.lang = 'hi-IN';
                this.onresult = null;
                this.onerror = null;
                this.onend = null;
                window._activeMockRec = this;
            }
            start() {}
            stop() {}
        };
        window.SpeechRecognition = window.MockSpeechRecognition;
        window.webkitSpeechRecognition = window.MockSpeechRecognition;
        """)

        page = context.new_page()
        page.goto(f"http://127.0.0.1:{PORT}/index.html")
        page.wait_for_load_state("networkidle")

        print("Testing Speak yourself button presence...")
        btn = page.locator("#btn-browser-mic")
        assert btn.is_visible(), "Speak yourself button not visible"
        btn.click()

        # Wait for Pyodide to finish loading and button to become active
        print("Waiting for Pyodide to initialize...")
        page.wait_for_selector("#btn-browser-mic.active-live", timeout=30000)
        print("Pyodide loaded & listening active!")

        # 1. Interim phrase
        print("Testing interim speech recognition...")
        page.evaluate("""() => {
            const rec = window._activeMockRec;
            rec.onresult({
                resultIndex: 0,
                results: [[{ transcript: 'Namaste sir main CBI se bol raha hoon' }]]
            });
        }""")
        time.sleep(0.5)
        caption = page.locator("#live-caption").text_content()
        assert "CBI" in caption, f"Interim text not in caption: {caption}"
        print(f"Interim caption verified: '{caption}'")

        # 2. Final scam phrase 1: Digital Arrest
        print("Sending scam sentence 1 (digital arrest)...")
        page.evaluate("""() => {
            const rec = window._activeMockRec;
            const res = [{ transcript: 'Aap digital arrest mein hain, video call disconnect mat kijiye.' }];
            res.isFinal = true;
            rec.onresult({ resultIndex: 0, results: [res] });
        }""")
        time.sleep(1)

        # 3. Final scam phrase 2: Bank transfer
        print("Sending scam sentence 2 (bank transfer)...")
        page.evaluate("""() => {
            const rec = window._activeMockRec;
            const res = [{ transcript: 'Turant paise verify karne ke liye RBI account mein transfer karein.' }];
            res.isFinal = true;
            rec.onresult({ resultIndex: 0, results: [res] });
        }""")
        time.sleep(1.5)

        # Assertions
        badge = page.locator("#mode-badge").text_content()
        assert "BROWSER MIC" in badge, f"Badge mismatch: {badge}"

        slips = page.locator(".tape-slip").count()
        assert slips >= 2, f"Expected at least 2 tape slips, got {slips}"
        print(f"Verified {slips} tape slips rendered.")

        level = page.locator(".level-text").text_content()
        score = page.locator(".score-num").text_content()
        print(f"Risk state: Level={level}, Score={score}")
        assert int(score) >= 60, f"Expected score >= 60, got {score}"

        # Check phone card STOP warning
        phone_warn = page.locator("#phone-slot")
        assert phone_warn.is_visible()

        # Take screenshots across viewports
        page.screenshot(path="docs/screens/d1_desktop_1523.png")
        print("Saved docs/screens/d1_desktop_1523.png")

        # Stop listening
        btn.click()
        time.sleep(1)

        browser.close()
        print("ALL BROWSER LIVE CHECKS PASSED!")

if __name__ == "__main__":
    main()
