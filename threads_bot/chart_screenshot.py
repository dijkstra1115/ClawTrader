"""
Take H1 chart screenshot of BTC from Kiyotaka.ai with CVD + OI indicators.
Uses Playwright with ANGLE GPU backend for WebGL rendering.
"""
import os
import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "charts")
KIYOTAKA_BASE = "https://chart.kiyotaka.ai"

# Indicators to add via the Indicators panel search
INDICATORS = [
    "CVD Flow Dominance",
    "Open Interest Delta",
]

TIMEFRAME = "1h"


async def _dismiss_overlays(page):
    """Force-remove all dialog overlays and guest banners via JS."""
    try:
        removed = await page.evaluate("""() => {
            let count = 0;
            document.querySelectorAll(
                '.dialog-overlay, [class*="dialog-overlay"], [class*="notification"]'
            ).forEach(el => { el.remove(); count++; });
            return count;
        }""")
        if removed:
            print(f"[screenshot] Removed {removed} overlay(s)")
        await page.wait_for_timeout(500)
    except Exception as e:
        print(f"[screenshot] Overlay dismiss error: {e}")


async def _wait_for_chart(page):
    """Wait until WebGL chart canvas has rendered content."""
    try:
        await page.wait_for_selector("canvas", timeout=30000)
        for _ in range(15):
            has_content = await page.evaluate("""() => {
                const cs = document.querySelectorAll('canvas');
                for (const c of cs) {
                    if (c.width > 400 && c.height > 200) {
                        const gl = c.getContext('webgl') || c.getContext('webgl2');
                        if (gl) return true;
                    }
                }
                return false;
            }""")
            if has_content:
                await page.wait_for_timeout(2000)
                return
            await page.wait_for_timeout(2000)
        await page.wait_for_timeout(5000)
    except Exception:
        await page.wait_for_timeout(8000)


async def _add_indicators(page):
    """Open Indicators panel and add CVD + OI indicators."""
    try:
        ind_btn = await page.query_selector("button.indicators-button")
        if not ind_btn:
            print("[screenshot] Indicators button not found")
            return
        await ind_btn.click(force=True)
        await page.wait_for_timeout(2000)

        search = await page.query_selector('input[placeholder*="Search scripts"]')
        if not search:
            print("[screenshot] Indicator search input not found")
            await page.keyboard.press("Escape")
            return

        for indicator_name in INDICATORS:
            await search.fill(indicator_name)
            await page.wait_for_timeout(2000)
            first_row = await page.query_selector('[class*="script-row"]:first-child')
            if first_row and await first_row.is_visible():
                await first_row.click(force=True)
                await page.wait_for_timeout(1000)
                print(f"[screenshot] Added indicator: {indicator_name}")
            else:
                print(f"[screenshot] Indicator not found: {indicator_name}")

        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1000)
    except Exception as e:
        print(f"[screenshot] Add indicators error: {e}")
        await page.keyboard.press("Escape")


async def _set_timeframe(page):
    """Set chart to H1 timeframe."""
    try:
        await _dismiss_overlays(page)
        tf_btn = await page.query_selector(f'button:has-text("{TIMEFRAME}")')
        if tf_btn and await tf_btn.is_visible():
            await tf_btn.click(force=True)
            await page.wait_for_timeout(3000)
            print(f"[screenshot] Timeframe: {TIMEFRAME}")
    except Exception as e:
        print(f"[screenshot] Timeframe error: {e}")


async def _capture_largest_canvas(page, filename: str) -> Optional[str]:
    """Screenshot the largest canvas element (the main chart)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        await _dismiss_overlays(page)
        canvases = await page.query_selector_all("canvas")
        best = None
        max_area = 0
        for c in canvases:
            box = await c.bounding_box()
            if box and box["width"] > 400 and box["height"] > 200:
                area = box["width"] * box["height"]
                if area > max_area:
                    max_area = area
                    best = c

        if best:
            await best.screenshot(path=filepath)
            print(f"[screenshot] Chart captured: {filepath}")
        else:
            await page.screenshot(path=filepath)
            print(f"[screenshot] Viewport captured: {filepath}")
        return filepath
    except Exception as e:
        print(f"[screenshot] Capture failed: {e}")
        return None


async def capture_btc_chart() -> Optional[str]:
    """
    Full flow: launch browser -> load Kiyotaka -> add CVD + OI
    -> set H1 timeframe -> wait for render -> screenshot.

    Returns the filepath of the saved chart image.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--enable-webgl",
                "--use-angle=default",
                "--enable-gpu",
                "--ignore-gpu-blocklist",
                "--window-position=-10000,-10000",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        try:
            await page.goto(KIYOTAKA_BASE, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(8000)
            await _dismiss_overlays(page)

            # Handle error page
            error = await page.query_selector('text="something went wrong"')
            if error:
                btn = await page.query_selector('button:has-text("Create new workspace")')
                if btn:
                    await btn.click(force=True)
                    await page.wait_for_timeout(5000)
                else:
                    await page.reload(wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(5000)
                await _dismiss_overlays(page)

            # Default symbol is BTCUSDT on Binance Futures — perfect
            # Add CVD + OI indicators
            await _add_indicators(page)
            await _dismiss_overlays(page)

            # Set H1 timeframe
            await _set_timeframe(page)

            # Wait for chart render
            await _wait_for_chart(page)
            await _dismiss_overlays(page)

            # Capture
            filepath = await _capture_largest_canvas(page, "btc_h1.png")
            return filepath

        except Exception as e:
            print(f"[screenshot] Fatal error: {e}")
            return None
        finally:
            await browser.close()


def capture_btc_chart_sync() -> Optional[str]:
    """Synchronous wrapper."""
    return asyncio.run(capture_btc_chart())


if __name__ == "__main__":
    path = capture_btc_chart_sync()
    print(f"Chart: {path}")
