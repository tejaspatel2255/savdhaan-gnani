import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def capture():
    screens_dir = Path("docs/screens")
    screens_dir.mkdir(parents=True, exist_ok=True)
    
    # Path to local html file
    html_url = "file:///" + str(Path("frontend/report.html").resolve()).replace("\\", "/") + "?fixture=1"
    
    viewports = [
        ("1920", 1920, 1080),
        ("1366", 1366, 768),
        ("360", 360, 800),
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for label, width, height in viewports:
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(html_url, wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Check horizontal overflow
            scroll_width = await page.evaluate("() => document.documentElement.scrollWidth")
            client_width = await page.evaluate("() => document.documentElement.clientWidth")
            print(f"Viewport {label}: clientWidth={client_width}, scrollWidth={scroll_width}")
            
            shot_path = screens_dir / f"khata_{label}.png"
            await page.screenshot(path=str(shot_path), full_page=True)
            print(f"Captured {shot_path}")
            await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())
